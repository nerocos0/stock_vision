from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth.models import User

class AuthAPITests(APITestCase):
    """Тесты регистрации и логина (JWT)"""

    def setUp(self):
        self.register_url = '/api/auth/register/'
        self.login_url = '/api/auth/token/'

    def test_register_user_success(self):
        data = {
            "username": "testuser_new",
            "password": "strongpassword123",
            "password2": "strongpassword123"
        }
        response = self.client.post(self.register_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('username', response.data)
        self.assertNotIn('password', response.data)
        
        user = User.objects.get(username="testuser_new")
        self.assertTrue(user.check_password("strongpassword123"))

    def test_register_passwords_do_not_match(self):
        data = {
            "username": "testuser_bad",
            "password": "password123",
            "password2": "differentpassword"
        }
        response = self.client.post(self.register_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', response.data)

    def test_login_success(self):
        User.objects.create_user(username="loginuser", password="password123")
        
        data = {
            "username": "loginuser",
            "password": "password123"
        }
        response = self.client.post(self.login_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_login_wrong_password(self):
        User.objects.create_user(username="loginuser", password="password123")
        
        data = {
            "username": "loginuser",
            "password": "wrongpassword"
        }
        response = self.client.post(self.login_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)