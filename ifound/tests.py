from io import BytesIO
from datetime import date, datetime, timedelta
import tempfile
from unittest.mock import patch

from PIL import Image
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.http import HttpResponse
from django.test import RequestFactory, SimpleTestCase, TestCase, override_settings
from django.urls import reverse

from .models import Perfil, Item, Solicitacao
from .prazos import calcular_prazo_retirada


class ProfilePhotoUploadTests(TestCase):
	def setUp(self):
		self.media_directory = tempfile.TemporaryDirectory()
		self.addCleanup(self.media_directory.cleanup)
		media_settings = override_settings(MEDIA_ROOT=self.media_directory.name)
		media_settings.enable()
		self.addCleanup(media_settings.disable)

		self.user = User.objects.create_user(username='12345', password='test-password')
		self.profile, _ = Perfil.objects.get_or_create(user=self.user)
		self.client.force_login(self.user)

	def _jpeg_upload(self, name='profile.jpg'):
		content = BytesIO()
		Image.new('RGB', (2, 2), color='green').save(content, format='JPEG')
		return SimpleUploadedFile(name, content.getvalue(), content_type='image/jpeg')

	def test_valid_image_is_saved_to_authenticated_profile(self):
		response = self.client.post(
			reverse('perfil'),
			{'foto': self._jpeg_upload()},
			HTTP_X_REQUESTED_WITH='XMLHttpRequest',
		)

		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.json()['message'], 'Foto de perfil atualizada com sucesso!')
		self.profile.refresh_from_db()
		self.assertTrue(self.profile.foto.name.startswith('perfis/'))
		self.assertEqual(response.json()['url'], self.profile.foto.url)

	def test_invalid_image_is_rejected(self):
		upload = SimpleUploadedFile('profile.jpg', b'not an image', content_type='image/jpeg')
		response = self.client.post(
			reverse('perfil'),
			{'foto': upload},
			HTTP_X_REQUESTED_WITH='XMLHttpRequest',
		)

		self.assertEqual(response.status_code, 400)
		self.assertEqual(response.json()['message'], 'Não foi possível atualizar sua foto de perfil.')
		self.profile.refresh_from_db()
		self.assertFalse(self.profile.foto)

	def test_upload_requires_authentication(self):
		self.client.logout()
		response = self.client.post(reverse('perfil'), {'foto': self._jpeg_upload()})

		self.assertEqual(response.status_code, 302)


class SolicitationFlowTests(TestCase):
	def setUp(self):
		self.media_directory = tempfile.TemporaryDirectory()
		self.addCleanup(self.media_directory.cleanup)
		media_settings = override_settings(MEDIA_ROOT=self.media_directory.name)
		media_settings.enable()
		self.addCleanup(media_settings.disable)

		self.user = User.objects.create_user(username='12345', password='test-password')
		self.client.force_login(self.user)
		self.item = Item.objects.create(
			nome='Celular',
			descricao='Celular quebrado',
			local='Sala A107',
			data_registro='2026-10-08',
			status='perdi',
			usuario=self.user,
		)

	def _image_upload(self, name='comprovante.jpg'):
		content = BytesIO()
		Image.new('RGB', (2, 2), color='blue').save(content, format='JPEG')
		return SimpleUploadedFile(name, content.getvalue(), content_type='image/jpeg')

	def test_user_can_view_their_solicitations_page(self):
		response = self.client.get(reverse('minhas_solicitacoes'))
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'Minhas Solicitações')
		self.assertContains(response, 'Acompanhe as solicitações que você enviou para recuperar os itens.')

	def test_duplicate_solicitation_is_detected_for_the_same_item(self):
		Solicitacao.objects.create(
			item=self.item,
			solicitante=self.user,
			foto_comprovante=self._image_upload(),
			status='em_analise',
		)

		response = self.client.get(
			reverse('verificar_solicitacao_item', args=[self.item.id]),
			HTTP_X_REQUESTED_WITH='XMLHttpRequest',
		)
		self.assertEqual(response.status_code, 200)
		self.assertTrue(response.json()['exists'])
		self.assertEqual(response.json()['message'], 'Você já possui uma solicitação para este item.')

	def test_confirmation_page_renders_item_and_cancel_destination(self):
		response = self.client.get(reverse('confirmar_solicitacao', args=[self.item.id]))

		self.assertEqual(response.status_code, 200)
		self.assertTemplateUsed(response, 'confirmar_solicitacao.html')
		self.assertContains(response, self.item.nome)
		self.assertContains(response, self.item.local)
		self.assertContains(response, 'name="foto_comprovante"')
		self.assertContains(response, reverse('detalhar_item', args=[self.item.id]))

	def test_item_verification_points_to_confirmation_when_request_is_new(self):
		response = self.client.get(reverse('verificar_solicitacao_item', args=[self.item.id]))

		self.assertEqual(response.status_code, 200)
		self.assertFalse(response.json()['exists'])
		self.assertEqual(
			response.json()['redirect_url'],
			reverse('confirmar_solicitacao', args=[self.item.id]),
		)

	def test_valid_solicitation_submission_creates_request_and_sets_initial_status_to_analysis(self):
		response = self.client.post(
			reverse('confirmar_solicitacao', args=[self.item.id]),
			{'foto_comprovante': self._image_upload()},
			HTTP_X_REQUESTED_WITH='XMLHttpRequest',
		)

		self.assertEqual(response.status_code, 200)
		self.assertTrue(response.json()['success'])
		self.assertEqual(Solicitacao.objects.filter(item=self.item, solicitante=self.user).count(), 1)
		self.assertEqual(Solicitacao.objects.get(item=self.item, solicitante=self.user).status, 'em_analise')

		list_response = self.client.get(reverse('minhas_solicitacoes'))
		solicitacao = Solicitacao.objects.get(item=self.item, solicitante=self.user)
		self.assertContains(list_response, self.item.nome)
		self.assertContains(list_response, self.item.local)
		self.assertContains(list_response, reverse('detalhar_solicitacao', args=[solicitacao.id]))


class EditProfileTests(TestCase):
	def setUp(self):
		self.user = User.objects.create_user(
			username='12345',
			email='aluno@example.com',
			password='test-password'
		)
		self.profile, _ = Perfil.objects.get_or_create(user=self.user)
		self.profile.nome_completo = 'Nome Atual'
		self.profile.curso = 'Curso Atual'
		self.profile.turma = 'Turma Atual'
		self.profile.save()
		self.client.force_login(self.user)

	def test_get_shows_current_profile_data(self):
		response = self.client.get(reverse('editar_perfil'))

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'value="Nome Atual"')
		self.assertContains(response, 'value="aluno@example.com"')
		self.assertContains(response, 'value="Curso Atual"')
		self.assertContains(response, 'value="Turma Atual"')

	def test_post_updates_own_user_and_profile_then_redirects(self):
		response = self.client.post(reverse('editar_perfil'), {
			'nome_completo': 'Nome Atualizado',
			'email': 'novo@example.com',
			'curso': 'Novo Curso',
			'turma': 'Nova Turma',
		})

		self.assertRedirects(response, reverse('perfil'))
		self.user.refresh_from_db()
		self.profile.refresh_from_db()
		self.assertEqual(self.user.email, 'novo@example.com')
		self.assertEqual(self.user.username, '12345')
		self.assertEqual(self.profile.nome_completo, 'Nome Atualizado')
		self.assertEqual(self.profile.curso, 'Novo Curso')
		self.assertEqual(self.profile.turma, 'Nova Turma')
		self.assertContains(self.client.get(reverse('perfil')), 'Dados atualizados com sucesso!')

	def test_ajax_post_returns_updated_profile_as_json(self):
		response = self.client.post(
			reverse('editar_perfil'),
			{
				'nome_completo': 'Nome via AJAX',
				'email': 'ajax@example.com',
				'curso': 'Curso AJAX',
				'turma': 'Turma AJAX',
			},
			HTTP_X_REQUESTED_WITH='XMLHttpRequest',
		)

		self.assertEqual(response.status_code, 200)
		self.assertTrue(response.json()['success'])
		self.assertEqual(response.json()['profile']['nome_completo'], 'Nome via AJAX')
		self.user.refresh_from_db()
		self.profile.refresh_from_db()
		self.assertEqual(self.user.email, 'ajax@example.com')
		self.assertEqual(self.profile.curso, 'Curso AJAX')

	def test_ajax_validation_errors_are_returned_as_json(self):
		response = self.client.post(
			reverse('editar_perfil'),
			{
				'nome_completo': '',
				'email': 'invalido',
				'curso': '',
				'turma': '',
			},
			HTTP_X_REQUESTED_WITH='XMLHttpRequest',
		)

		self.assertEqual(response.status_code, 400)
		self.assertFalse(response.json()['success'])
		self.assertIn('Informe seu nome completo.', response.json()['errors'])

	def test_invalid_fields_are_reported_without_saving(self):
		response = self.client.post(reverse('editar_perfil'), {
			'nome_completo': '',
			'email': 'email-invalido',
			'curso': '',
			'turma': '',
		})

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'Informe seu nome completo.')
		self.assertContains(response, 'Informe um e-mail válido.')
		self.user.refresh_from_db()
		self.profile.refresh_from_db()
		self.assertEqual(self.user.email, 'aluno@example.com')
		self.assertEqual(self.profile.nome_completo, 'Nome Atual')

	def test_email_used_by_another_user_is_rejected(self):
		User.objects.create_user(username='67890', email='outro@example.com', password='test-password')
		response = self.client.post(reverse('editar_perfil'), {
			'nome_completo': 'Nome Atual',
			'email': 'outro@example.com',
			'curso': 'Curso Atual',
			'turma': 'Turma Atual',
		})

		self.assertContains(response, 'Este e-mail já está sendo utilizado por outra conta.')
		self.user.refresh_from_db()
		self.assertEqual(self.user.email, 'aluno@example.com')

	def test_edit_requires_authentication(self):
		self.client.logout()
		response = self.client.get(reverse('editar_perfil'))

		self.assertEqual(response.status_code, 302)


class ItemDeadlineTests(SimpleTestCase):
	def item(self, status='achei', data_encontrado=None):
		return Item(status=status, data_encontrado=data_encontrado)

	def test_found_item_with_distant_deadline_is_awaiting_pickup(self):
		today = date(2026, 10, 15)
		result = calcular_prazo_retirada(
			self.item(data_encontrado=today - timedelta(days=4)),
			hoje=today,
		)
		self.assertEqual(result.data_limite, today + timedelta(days=11))
		self.assertEqual(result.classificacao, 'aguardando_retirada')
		self.assertEqual(result.dias_restantes, 11)

	def test_found_item_due_in_exactly_three_days_is_approaching_deadline(self):
		today = date(2026, 10, 15)
		result = calcular_prazo_retirada(
			self.item(data_encontrado=today - timedelta(days=12)),
			hoje=today,
		)
		self.assertEqual(result.classificacao, 'proximo_vencimento')
		self.assertEqual(result.dias_restantes, 3)

	def test_found_item_due_today_is_still_within_deadline(self):
		today = date(2026, 10, 15)
		result = calcular_prazo_retirada(
			self.item(data_encontrado=today - timedelta(days=15)),
			hoje=today,
		)
		self.assertEqual(result.data_limite, today)
		self.assertEqual(result.classificacao, 'proximo_vencimento')
		self.assertEqual(result.dias_restantes, 0)

	def test_found_item_expired_yesterday_is_overdue(self):
		today = date(2026, 10, 15)
		result = calcular_prazo_retirada(
			self.item(data_encontrado=today - timedelta(days=16)),
			hoje=today,
		)
		self.assertEqual(result.data_limite, today - timedelta(days=1))
		self.assertEqual(result.classificacao, 'vencido')
		self.assertEqual(result.dias_restantes, -1)

	def test_found_item_without_found_date_has_no_deadline_status(self):
		result = calcular_prazo_retirada(self.item(data_encontrado=None), hoje=date(2026, 10, 15))
		self.assertEqual(result.data_limite, None)
		self.assertEqual(result.classificacao, 'data_nao_informada')
		self.assertEqual(result.dias_restantes, None)

	def test_lost_item_is_excluded_even_when_found_date_is_set(self):
		result = calcular_prazo_retirada(
			self.item(status='perdi', data_encontrado=date(2026, 10, 1)),
			hoje=date(2026, 10, 15),
		)
		self.assertEqual(result.data_limite, None)
		self.assertEqual(result.classificacao, 'nao_aplicavel')
		self.assertEqual(result.dias_restantes, None)

	def test_deadline_is_exactly_fifteen_calendar_days_after_found_date(self):
		found_date = date(2026, 10, 1)
		result = calcular_prazo_retirada(
			self.item(data_encontrado=found_date),
			hoje=date(2026, 10, 1),
		)
		self.assertEqual(result.data_limite, date(2026, 10, 16))
		self.assertEqual(result.data_limite - found_date, timedelta(days=15))

	def test_default_today_uses_django_local_date(self):
		local_today = date(2026, 10, 15)
		with patch('ifound.prazos.timezone.localdate', return_value=local_today) as localdate:
			result = calcular_prazo_retirada(
				self.item(data_encontrado=local_today - timedelta(days=12))
			)
		localdate.assert_called_once_with()
		self.assertEqual(result.classificacao, 'proximo_vencimento')


class AdminDashboardIndicatorsTests(SimpleTestCase):
	class MemoryQuerySet(list):
		def only(self, *fields):
			self.selected_fields = fields
			return self

		def count(self):
			return len(self)

	def test_authorized_dashboard_counts_indicators_using_sample_records(self):
		today = date(2026, 10, 15)
		found_items = self.MemoryQuerySet([
			Item(status='achei', data_encontrado=today - timedelta(days=12)),
			Item(status='achei', data_encontrado=today - timedelta(days=16)),
			Item(status='achei', data_encontrado=None),
			Item(status='achei', data_encontrado=today - timedelta(days=4)),
		])
		lost_items = self.MemoryQuerySet([
			Item(status='perdi', data_encontrado=today - timedelta(days=16)),
		])
		analysis_requests = self.MemoryQuerySet(['requester-a', 'requester-b'])

		def filter_items(**filters):
			if filters == {'status': 'achei'}:
				return found_items
			if filters == {'status': 'perdi'}:
				return lost_items
			self.fail(f'Filtro inesperado para Item: {filters}')

		request = RequestFactory().get('/admin-dashboard/')
		request.user = type('AuthorizedUser', (), {
			'is_authenticated': True,
			'is_superuser': False,
			'has_perm': lambda self, permission: permission == 'ifound.access_ifound_admin_area',
		})()

		from . import views
		with patch.object(views.Item.objects, 'filter', side_effect=filter_items) as item_filter, \
				patch.object(views.Solicitacao.objects, 'filter', return_value=analysis_requests) as request_filter, \
				patch('ifound.views.timezone.localdate', return_value=today), \
				patch('ifound.views._get_dashboard_chart_data', return_value={'sample': True}) as chart_data, \
				patch('ifound.views.render', return_value=HttpResponse('dashboard')) as render:
			response = views.admin_dashboard(request)

		self.assertEqual(response.status_code, 200)
		self.assertEqual(item_filter.call_count, 2)
		self.assertEqual(request_filter.call_args.kwargs, {'status': 'em_analise'})
		chart_data.assert_called_once_with(today)
		self.assertEqual(found_items.selected_fields, ('status', 'data_encontrado'))
		context = render.call_args.args[2]
		self.assertEqual(context['indicadores'], {
			'itens_encontrados': 4,
			'itens_perdidos': 1,
			'proximos_vencimento': 1,
			'itens_vencidos': 1,
			'solicitacoes_em_analise': 2,
		})
		self.assertEqual(context['graficos'], {'sample': True})
		self.assertNotIn('requester-a', repr(context))
		self.assertNotIn('requester-b', repr(context))

	def test_user_without_dashboard_permission_receives_forbidden(self):
		request = RequestFactory().get('/admin-dashboard/')
		request.user = type('UnauthorizedUser', (), {
			'is_authenticated': True,
			'is_superuser': False,
			'has_perm': lambda self, permission: False,
		})()

		from . import views
		with patch('ifound.views.render') as render:
			response = views.admin_dashboard(request)

		self.assertEqual(response.status_code, 403)
		render.assert_not_called()


class AdminDashboardChartDataTests(SimpleTestCase):
	def test_monthly_chart_has_six_months_and_zeroes_for_missing_months(self):
		from .views import _format_dashboard_chart_data

		chart_data = _format_dashboard_chart_data(
			[
				{'mes': datetime(2026, 10, 1), 'status': 'achei', 'total': 2},
				{'mes': datetime(2026, 8, 1), 'status': 'perdi', 'total': 1},
			],
			[],
			date(2026, 10, 15),
		)

		monthly = chart_data['itens_por_mes']
		self.assertEqual(monthly['labels'], ['Mai/26', 'Jun/26', 'Jul/26', 'Ago/26', 'Set/26', 'Out/26'])
		self.assertEqual(monthly['encontrados'], [0, 0, 0, 0, 0, 2])
		self.assertEqual(monthly['perdidos'], [0, 0, 0, 1, 0, 0])

	def test_solicitation_chart_uses_all_model_choices_and_zeroes_missing_statuses(self):
		from .views import _format_dashboard_chart_data

		chart_data = _format_dashboard_chart_data(
			[],
			[
				{'status': 'em_analise', 'total': 3},
				{'status': 'aprovada', 'total': 2},
			],
			date(2026, 10, 15),
		)

		requests = chart_data['solicitacoes_por_situacao']
		self.assertEqual(requests['keys'], [status for status, _label in Solicitacao.STATUS_CHOICES])
		self.assertEqual(requests['labels'], [label for _status, label in Solicitacao.STATUS_CHOICES])
		self.assertEqual(requests['values'], [3, 2, 0])
