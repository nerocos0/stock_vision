from datetime import timedelta
from django.utils import timezone
from django.contrib.auth.models import User
from rest_framework.test import APITestCase
from rest_framework import status
from unittest.mock import patch
from users.models import EmailChangeRequest


class EmailChangeTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser', password='oldpass123', email='old@example.com'
        )
        self.client.force_authenticate(user=self.user)

    @patch('users.views.send_email_change_task.delay')
    def test_change_email_request(self, mock_task):
        url = '/api/auth/profile/change-email/'
        data = {'new_email': 'new@example.com', 'password': 'oldpass123'}
        
        response = self.client.post(url, data)
        
        assert response.status_code == status.HTTP_200_OK
        assert EmailChangeRequest.objects.filter(user=self.user, status='pending').exists()
        mock_task.assert_called_once()
        self.user.refresh_from_db()
        assert self.user.email == 'old@example.com'

    def test_change_email_wrong_password(self):
        url = '/api/auth/profile/change-email/'
        data = {'new_email': 'new@example.com', 'password': 'wrongpass'}
        
        response = self.client.post(url, data)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert not EmailChangeRequest.objects.filter(user=self.user).exists()

    def test_change_email_taken(self):
        User.objects.create_user(username='other', password='pass', email='taken@example.com')
        url = '/api/auth/profile/change-email/'
        data = {'new_email': 'taken@example.com', 'password': 'oldpass123'}
        
        response = self.client.post(url, data)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_confirm_email_change(self):
        change_request = EmailChangeRequest.objects.create(
            user=self.user, old_email='old@example.com', new_email='new@example.com'
        )
        url = f'/api/auth/confirm-email-change/{self.user.id}/{change_request.token}/'
        
        response = self.client.get(url)
        
        assert response.status_code == 302
        self.user.refresh_from_db()
        assert self.user.email == 'new@example.com'
        change_request.refresh_from_db()
        assert change_request.status == 'confirmed'

    def test_confirm_email_expired(self):
        change_request = EmailChangeRequest.objects.create(
            user=self.user, old_email='old@example.com', new_email='new@example.com'
        )
        change_request.created_at = timezone.now() - timedelta(hours=25)
        change_request.save()
        
        url = f'/api/auth/confirm-email-change/{self.user.id}/{change_request.token}/'
        response = self.client.get(url)
        
        assert response.status_code == 302
        self.user.refresh_from_db()
        assert self.user.email == 'old@example.com'
        change_request.refresh_from_db()
        assert change_request.status == 'expired'

    def test_confirm_email_invalid_token(self):
        url = f'/api/auth/confirm-email-change/{self.user.id}/invalid-token/'
        response = self.client.get(url)
        assert response.status_code == 302
        assert 'email_error=invalid' in response.url