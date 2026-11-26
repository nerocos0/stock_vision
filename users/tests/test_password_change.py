from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth.models import User
from rest_framework_simplejwt.tokens import RefreshToken


class PasswordChangeTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser', password='oldpass123', email='test@example.com'
        )
        self.client.force_authenticate(user=self.user)

    def test_change_password_success(self):
        url = '/api/auth/profile/change-password/'
        data = {
            'oldpassword': 'oldpass123',
            'new_password': 'newpass456',
            'new_password2': 'newpass456'
        }
        
        response = self.client.post(url, data)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'access' in response.data
        assert 'refresh' in response.data
        self.user.refresh_from_db()
        assert self.user.check_password('newpass456')

    def test_change_password_wrong_old(self):
        url = '/api/auth/profile/change-password/'
        data = {
            'oldpassword': 'wrongpass',
            'new_password': 'newpass456',
            'new_password2': 'newpass456'
        }
        
        response = self.client.post(url, data)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        self.user.refresh_from_db()
        assert self.user.check_password('oldpass123')

    def test_change_password_mismatch(self):
        url = '/api/auth/profile/change-password/'
        data = {
            'oldpassword': 'oldpass123',
            'new_password': 'newpass456',
            'new_password2': 'different789'
        }
        
        response = self.client.post(url, data)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        self.user.refresh_from_db()
        assert self.user.check_password('oldpass123')

    def test_old_tokens_blacklisted(self):
        refresh = RefreshToken.for_user(self.user)
        old_refresh = str(refresh)
        
        url = '/api/auth/profile/change-password/'
        data = {
            'oldpassword': 'oldpass123',
            'new_password': 'newpass456',
            'new_password2': 'newpass456'
        }
        self.client.post(url, data)
        
        from rest_framework_simplejwt.tokens import RefreshToken as RT
        from rest_framework_simplejwt.exceptions import TokenError
        try:
            RT(old_refresh)
            assert False, "Старый токен должен быть в blacklist"
        except TokenError:
            pass