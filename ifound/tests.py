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
		header_response = self.client.get(reverse('meus_itens'))
		self.assertContains(header_response, 'class="navbar-profile-avatar"')
		self.assertContains(header_response, f'src="{self.profile.foto.url}"')

	def test_shared_header_uses_default_icon_without_profile_photo(self):
		response = self.client.get(reverse('index'))

		self.assertContains(response, 'id="navbarProfileIcon"')
		self.assertContains(response, 'class="bi bi-person-circle"')
		self.assertNotContains(response, 'navbar-profile-avatar')

	def test_profile_page_uses_saved_photo_in_profile_card_and_header(self):
		self.profile.foto.save('existing-profile.jpg', self._jpeg_upload(), save=True)

		response = self.client.get(reverse('perfil'))

		self.assertContains(response, 'id="profileAvatarImage"')
		self.assertContains(response, 'id="navbarProfileAvatar"')
		self.assertContains(response, f'src="{self.profile.foto.url}"')

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


class PasswordChangeTests(TestCase):
	def setUp(self):
		self.user = User.objects.create_user(username='password-user', password='Current-pass-88')
		self.client.force_login(self.user)
		self.url = reverse('alterar_senha')

	def _post_passwords(self, **passwords):
		return self.client.post(
			self.url,
			passwords,
			HTTP_X_REQUESTED_WITH='XMLHttpRequest',
		)

	def test_password_page_has_active_navigation_and_required_fields(self):
		response = self.client.get(self.url)

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, f'class="profile-menu-item active" href="{self.url}"')
		self.assertContains(response, 'name="current_password"')
		self.assertContains(response, 'name="new_password"')
		self.assertContains(response, 'name="confirm_password"')

	def test_password_change_requires_authentication(self):
		self.client.logout()

		response = self.client.get(self.url)

		self.assertEqual(response.status_code, 302)

	def test_empty_password_fields_are_rejected(self):
		response = self._post_passwords()

		self.assertEqual(response.status_code, 400)
		self.assertEqual(set(response.json()['errors']), {'current_password', 'new_password', 'confirm_password'})

	def test_incorrect_current_password_does_not_change_password(self):
		response = self._post_passwords(
			current_password='wrong-password',
			new_password='New-safe-pass-99',
			confirm_password='New-safe-pass-99',
		)

		self.assertEqual(response.status_code, 400)
		self.assertIn('current_password', response.json()['errors'])
		self.user.refresh_from_db()
		self.assertTrue(self.user.check_password('Current-pass-88'))

	def test_mismatched_confirmation_is_rejected(self):
		response = self._post_passwords(
			current_password='Current-pass-88',
			new_password='New-safe-pass-99',
			confirm_password='Different-pass-99',
		)

		self.assertEqual(response.status_code, 400)
		self.assertIn('confirm_password', response.json()['errors'])
		self.user.refresh_from_db()
		self.assertTrue(self.user.check_password('Current-pass-88'))

	def test_django_password_validators_are_applied(self):
		response = self._post_passwords(
			current_password='Current-pass-88',
			new_password='12345678',
			confirm_password='12345678',
		)

		self.assertEqual(response.status_code, 400)
		self.assertIn('new_password', response.json()['errors'])

	def test_success_changes_password_and_keeps_session_authenticated(self):
		response = self._post_passwords(
			current_password='Current-pass-88',
			new_password='New-safe-pass-99',
			confirm_password='New-safe-pass-99',
		)

		self.assertEqual(response.status_code, 200)
		self.assertTrue(response.json()['success'])
		self.user.refresh_from_db()
		self.assertTrue(self.user.check_password('New-safe-pass-99'))
		self.assertEqual(self.client.session['_auth_user_id'], str(self.user.pk))
		self.assertEqual(self.client.get(reverse('perfil')).status_code, 200)


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

		request = RequestFactory().get('/admin-dashboard/indicadores/')
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
			response = views.admin_indicadores(request)

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


class AdminDashboardPagesTests(TestCase):
	def setUp(self):
		self.admin = User.objects.create_superuser(
			username='admin-dashboard-test',
			email='admin-dashboard-test@example.com',
			password='test-password',
		)
		self.client.force_login(self.admin)

	def test_admin_navigation_opens_independent_pages_with_active_link(self):
		pages = (
			('admin_dashboard', 'Total de itens cadastrados', 'ifAdminMonthlyChart'),
			('admin_indicadores', 'ifAdminMonthlyChart', 'adminDeadlinesTitle'),
			('admin_prazos', 'Situação do prazo', 'ifAdminMonthlyChart'),
			('admin_solicitacoes', 'Solicitações recebidas', 'adminDeadlinesTitle'),
		)

		for url_name, included_content, excluded_content in pages:
			with self.subTest(page=url_name):
				response = self.client.get(reverse(url_name))

				self.assertEqual(response.status_code, 200)
				self.assertContains(response, included_content)
				self.assertNotContains(response, excluded_content)
				self.assertContains(
					response,
					f'class="if-admin-nav-link is-active" href="{reverse(url_name)}"',
				)
				self.assertNotContains(response, 'Categorias')

	def test_admin_categories_page_is_no_longer_routed(self):
		response = self.client.get('/admin-dashboard/categorias/')

		self.assertEqual(response.status_code, 404)

	def test_overview_displays_summary_cards_without_attention_or_quick_links(self):
		today = date(2026, 10, 15)
		item_com_prazo = Item.objects.create(
			nome='Item próximo do prazo',
			descricao='Teste',
			local='Campus',
			data_registro=today,
			data_encontrado=today - timedelta(days=12),
			status='achei',
			usuario=self.admin,
		)
		Item.objects.create(
			nome='Item vencido',
			descricao='Teste',
			local='Campus',
			data_registro=today,
			data_encontrado=today - timedelta(days=16),
			status='achei',
			usuario=self.admin,
		)
		Item.objects.create(
			nome='Item devolvido',
			descricao='Teste',
			local='Campus',
			data_registro=today,
			status='devolvido',
			usuario=self.admin,
		)
		Solicitacao.objects.create(
			item=item_com_prazo,
			solicitante=self.admin,
			foto_comprovante='comprovantes/teste.jpg',
			status='em_analise',
		)

		with patch('ifound.views.timezone.localdate', return_value=today):
			response = self.client.get(reverse('admin_dashboard'))

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'Total de itens cadastrados')
		self.assertContains(response, 'Itens devolvidos')
		self.assertNotContains(response, 'Atenção administrativa')
		self.assertNotContains(response, 'Acessos rápidos')
		self.assertNotContains(response, 'admin_solicitacoes')
		self.assertNotContains(response, 'admin_prazos')
		self.assertNotContains(response, 'admin_indicadores')
		self.assertNotContains(response, 'ifAdminMonthlyChart')
		self.assertNotContains(response, 'ifAdminRequestChart')
		self.assertEqual(response.context['resumo'], {
			'total_itens': 3,
			'solicitacoes_em_analise': 1,
			'itens_devolvidos': 1,
			'proximos_vencimento': 1,
			'itens_vencidos': 1,
		})

	def test_admin_requests_list_and_detail_use_real_request_records(self):
		item = Item.objects.create(
			nome='Mochila azul',
			descricao='Com distintivo',
			local='Biblioteca',
			data_registro=date(2026, 10, 10),
			status='achei',
			usuario=self.admin,
		)
		solicitante = User.objects.create_user(
			username='solicitante',
			first_name='Ana',
			last_name='Silva',
			password='test-password',
		)
		solicitacao = Solicitacao.objects.create(
			item=item,
			solicitante=solicitante,
			foto_comprovante='comprovantes/prova.jpg',
			status='em_analise',
		)

		list_response = self.client.get(reverse('admin_solicitacoes'))
		detail_response = self.client.get(
			reverse('admin_detalhar_solicitacao', args=[solicitacao.id])
		)

		self.assertContains(list_response, 'Ana Silva')
		self.assertContains(list_response, 'Mochila azul')
		self.assertContains(list_response, 'Em análise')
		self.assertContains(list_response, 'Visualizar comprovante')
		self.assertContains(list_response, reverse('admin_detalhar_solicitacao', args=[solicitacao.id]))
		self.assertContains(detail_response, 'Biblioteca')
		self.assertContains(detail_response, 'Comprovante enviado')
		self.assertContains(detail_response, 'comprovantes/prova.jpg')
		self.assertContains(detail_response, 'Em análise')
		self.assertContains(
			detail_response,
			f'class="if-admin-nav-link is-active" href="{reverse("admin_solicitacoes")}"',
		)

	def test_admin_deadlines_show_real_dates_and_existing_classifications(self):
		today = date(2026, 10, 15)
		near_due_item = Item.objects.create(
			nome='Chaves',
			descricao='Chaves encontradas',
			local='Recepção',
			data_registro=today,
			data_encontrado=today - timedelta(days=12),
			status='achei',
			categoria='acessorios',
			usuario=self.admin,
		)
		expired_item = Item.objects.create(
			nome='Caderno',
			descricao='Caderno encontrado',
			local='Sala 1',
			data_registro=today,
			data_encontrado=today - timedelta(days=16),
			status='achei',
			usuario=self.admin,
		)
		missing_date_item = Item.objects.create(
			nome='Guarda-chuva',
			descricao='Sem data de achado',
			local='Pátio',
			data_registro=today,
			status='achei',
			usuario=self.admin,
		)

		with patch('ifound.views.timezone.localdate', return_value=today):
			response = self.client.get(reverse('admin_prazos'))

		self.assertContains(response, 'Chaves')
		self.assertContains(response, 'Acessórios')
		self.assertContains(response, '18/10/2026')
		self.assertContains(response, 'Próximo do vencimento')
		self.assertContains(response, 'Caderno')
		self.assertContains(response, 'Vencido')
		self.assertContains(response, 'Guarda-chuva')
		self.assertContains(response, 'Data não informada')
		prazos_por_item = {prazo['item'].id: prazo for prazo in response.context['prazos']}
		self.assertEqual(prazos_por_item[near_due_item.id]['data_limite'], today + timedelta(days=3))
		self.assertEqual(prazos_por_item[near_due_item.id]['classificacao'], 'proximo_vencimento')
		self.assertEqual(prazos_por_item[expired_item.id]['classificacao'], 'vencido')
		self.assertIsNone(prazos_por_item[missing_date_item.id]['data_limite'])
		self.assertEqual(prazos_por_item[missing_date_item.id]['classificacao'], 'data_nao_informada')

	def test_each_admin_page_keeps_the_existing_permission_requirement(self):
		user = User.objects.create_user(username='regular-user', password='test-password')
		self.client.force_login(user)

		for url_name in (
			'admin_dashboard',
			'admin_indicadores',
			'admin_prazos',
			'admin_solicitacoes',
			'admin_detalhar_solicitacao',
		):
			with self.subTest(page=url_name):
				if url_name == 'admin_detalhar_solicitacao':
					response = self.client.get(reverse(url_name, args=[1]))
				else:
					response = self.client.get(reverse(url_name))
				self.assertEqual(response.status_code, 403)


class AdminRequestLifecycleTests(TestCase):
	def setUp(self):
		self.admin = User.objects.create_superuser(
			username='request-admin',
			email='request-admin@example.com',
			password='test-password',
		)
		self.requester = User.objects.create_user(
			username='requester',
			password='test-password',
		)
		self.item = Item.objects.create(
			nome='Carteira preta',
			descricao='Carteira com documentos',
			local='Biblioteca',
			data_registro=date(2026, 11, 1),
			data_encontrado=date(2026, 11, 1),
			categoria='documentos',
			status='achei',
			usuario=self.admin,
		)
		self.solicitacao = Solicitacao.objects.create(
			item=self.item,
			solicitante=self.requester,
			foto_comprovante='comprovantes/prova.jpg',
		)
		self.client.force_login(self.admin)
		self.action_url = reverse(
			'admin_atualizar_solicitacao',
			args=[self.solicitacao.id],
		)

	def _post_action(self, action, **data):
		return self.client.post(
			self.action_url,
			{'action': action, **data},
			HTTP_X_REQUESTED_WITH='XMLHttpRequest',
		)

	def test_admin_lists_and_can_inspect_analysis_request_and_proof(self):
		list_response = self.client.get(reverse('admin_solicitacoes'))
		detail_response = self.client.get(
			reverse('admin_detalhar_solicitacao', args=[self.solicitacao.id])
		)

		self.assertContains(list_response, 'Em análise')
		self.assertContains(list_response, 'Todas (1)')
		self.assertContains(detail_response, 'comprovantes/prova.jpg')
		self.assertContains(detail_response, 'Documentos')
		self.assertContains(detail_response, '01/11/2026')
		self.assertContains(detail_response, 'Aprovar solicitação')

	def test_approval_allows_pickup_without_marking_item_delivered(self):
		response = self._post_action('aprovar')

		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.json()['status'], 'aprovada')
		self.solicitacao.refresh_from_db()
		self.item.refresh_from_db()
		self.assertEqual(self.solicitacao.status, 'aprovada')
		self.assertIsNone(self.solicitacao.data_entrega)
		self.assertEqual(self.item.status, 'achei')

		user_client = self.client_class()
		user_client.force_login(self.requester)
		list_response = user_client.get(reverse('minhas_solicitacoes'))
		detail_response = user_client.get(
			reverse('detalhar_solicitacao', args=[self.solicitacao.id])
		)
		self.assertContains(list_response, 'Aprovada')
		self.assertContains(list_response, 'a entrega ainda aguarda confirmação presencial')
		self.assertContains(detail_response, 'Você pode comparecer para retirar o objeto.')

	def test_delivery_is_explicit_and_updates_request_and_item(self):
		self._post_action('aprovar')

		response = self._post_action('confirmar_entrega')

		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.json()['status'], 'entregue')
		self.solicitacao.refresh_from_db()
		self.item.refresh_from_db()
		self.assertEqual(self.solicitacao.status, 'entregue')
		self.assertIsNotNone(self.solicitacao.data_entrega)
		self.assertEqual(self.item.status, 'devolvido')

		user_client = self.client_class()
		user_client.force_login(self.requester)
		self.assertContains(
			user_client.get(reverse('detalhar_solicitacao', args=[self.solicitacao.id])),
			'Objeto entregue',
		)
		self.assertContains(
			user_client.get(reverse('minhas_solicitacoes')),
			'Entrega confirmada presencialmente.',
		)

	def test_rejection_requires_and_exposes_a_reason_to_requester(self):
		empty_reason_response = self._post_action('recusar', motivo_recusa='  ')
		self.assertEqual(empty_reason_response.status_code, 400)
		self.assertEqual(self.solicitacao.status, 'em_analise')

		response = self._post_action(
			'recusar',
			motivo_recusa='O comprovante não identifica o item.',
		)

		self.assertEqual(response.status_code, 200)
		self.solicitacao.refresh_from_db()
		self.assertEqual(self.solicitacao.status, 'recusada')
		self.assertEqual(self.solicitacao.motivo_recusa, 'O comprovante não identifica o item.')
		user_client = self.client_class()
		user_client.force_login(self.requester)
		self.assertContains(
			user_client.get(reverse('detalhar_solicitacao', args=[self.solicitacao.id])),
			'O comprovante não identifica o item.',
		)
		self.assertContains(
			user_client.get(reverse('minhas_solicitacoes')),
			'Motivo: O comprovante não identifica o item.',
		)

	def test_incompatible_actions_and_second_approval_are_rejected(self):
		self.assertEqual(self._post_action('confirmar_entrega').status_code, 409)
		self.assertEqual(self._post_action('aprovar').status_code, 200)
		self.assertEqual(self._post_action('aprovar').status_code, 409)
		self.assertEqual(self._post_action('recusar', motivo_recusa='Tarde demais.').status_code, 409)
		self.solicitacao.refresh_from_db()
		self.assertEqual(self.solicitacao.status, 'aprovada')
		self.item.refresh_from_db()
		self.assertEqual(self.item.status, 'achei')

		self.assertEqual(self._post_action('confirmar_entrega').status_code, 200)
		self.assertEqual(self._post_action('confirmar_entrega').status_code, 409)
		self.assertEqual(self._post_action('aprovar').status_code, 409)

	def test_another_approval_for_same_item_and_unavailable_item_are_blocked(self):
		other_request = Solicitacao.objects.create(
			item=self.item,
			solicitante=User.objects.create_user(username='other-requester'),
			foto_comprovante='comprovantes/outra-prova.jpg',
		)
		self.assertEqual(self._post_action('aprovar').status_code, 200)
		other_response = self.client.post(
			reverse('admin_atualizar_solicitacao', args=[other_request.id]),
			{'action': 'aprovar'},
		)
		self.assertEqual(other_response.status_code, 409)
		other_request.refresh_from_db()
		self.assertEqual(other_request.status, 'em_analise')

		unavailable_request = Solicitacao.objects.create(
			item=Item.objects.create(
				nome='Item já devolvido',
				descricao='Indisponível',
				local='Campus',
				data_registro=date(2026, 11, 1),
				status='devolvido',
				usuario=self.admin,
			),
			solicitante=self.requester,
			foto_comprovante='comprovantes/indisponivel.jpg',
		)
		unavailable_response = self.client.post(
			reverse('admin_atualizar_solicitacao', args=[unavailable_request.id]),
			{'action': 'aprovar'},
		)
		self.assertEqual(unavailable_response.status_code, 409)
		unavailable_request.refresh_from_db()
		self.assertEqual(unavailable_request.status, 'em_analise')

	def test_user_without_admin_permission_cannot_change_request(self):
		self.client.force_login(self.requester)

		response = self._post_action('aprovar')

		self.assertEqual(response.status_code, 403)
		self.solicitacao.refresh_from_db()
		self.assertEqual(self.solicitacao.status, 'em_analise')

	def test_admin_action_requires_csrf_token(self):
		csrf_client = self.client_class(enforce_csrf_checks=True)
		csrf_client.force_login(self.admin)

		response = csrf_client.post(self.action_url, {'action': 'aprovar'})

		self.assertEqual(response.status_code, 403)
		self.solicitacao.refresh_from_db()
		self.assertEqual(self.solicitacao.status, 'em_analise')


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
		self.assertEqual(requests['values'], [3, 2] + [0] * (len(Solicitacao.STATUS_CHOICES) - 2))
