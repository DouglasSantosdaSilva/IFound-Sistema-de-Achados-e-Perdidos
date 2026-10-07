from io import BytesIO
import tempfile

from PIL import Image
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse


class ProfilePhotoUploadTests(TestCase):
	def setUp(self):
		self.media_directory = tempfile.TemporaryDirectory()
		self.addCleanup(self.media_directory.cleanup)
		media_settings = override_settings(MEDIA_ROOT=self.media_directory.name)
		media_settings.enable()
		self.addCleanup(media_settings.disable)

		self.user = User.objects.create_user(username='12345', password='test-password')
		self.profile = self.user.perfil
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
