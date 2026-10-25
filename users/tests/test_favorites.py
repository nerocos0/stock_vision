from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth.models import User
from users.models import FavoriteInstrument
from data.models import Instrument

class FavoriteAPITests(APITestCase):
    """Тесты API избранного"""

    def setUp(self):
        self.url = '/api/auth/favorites/'
        
        self.user1 = User.objects.create_user(username="user1", password="pass123")
        self.user2 = User.objects.create_user(username="user2", password="pass123")
        
        self.instrument1 = Instrument.objects.create(code="EURUSD", name="Euro", instrument_type="forex")
        self.instrument2 = Instrument.objects.create(code="XAUUSD", name="Gold", instrument_type="forex")

    def test_anonymous_cannot_add_favorite(self):
        data = {"instrument": "EURUSD"}
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_user_can_add_favorite(self):
        self.client.force_authenticate(user=self.user1)
        
        data = {"instrument": "EURUSD"}
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(FavoriteInstrument.objects.count(), 1)
        
        fav = FavoriteInstrument.objects.first()
        self.assertEqual(fav.user, self.user1)
        self.assertEqual(fav.instrument.code, "EURUSD")

    def test_duplicate_favorite_does_not_crash(self):
        self.client.force_authenticate(user=self.user1)
        data = {"instrument": "EURUSD"}
        
        self.client.post(self.url, data, format='json')
        
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(FavoriteInstrument.objects.count(), 1)

    def test_user_sees_only_own_favorites(self):
        FavoriteInstrument.objects.create(user=self.user1, instrument=self.instrument1)
        FavoriteInstrument.objects.create(user=self.user2, instrument=self.instrument2)
        
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.data.get('results', response.data)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['instrument_code'], "EURUSD")

    def test_user_cannot_delete_others_favorite(self):
        fav = FavoriteInstrument.objects.create(user=self.user2, instrument=self.instrument1)
        
        self.client.force_authenticate(user=self.user1)
        url = f'{self.url}{fav.id}/'
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
        self.assertTrue(FavoriteInstrument.objects.filter(id=fav.id).exists())