from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch
from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework import status
from data.models import EconomicEvent
from data.tasks import sync_economic_calendar


class EconomicEventAPITests(APITestCase):
    def setUp(self):
        now = timezone.now() + timedelta(hours=1)
        EconomicEvent.objects.create(
            event_id='1', time=now, country='US', currency='USD',
            name='CPI', importance='high',
            actual=Decimal('2.5'), forecast=Decimal('2.3'), previous=Decimal('2.1')
        )
        EconomicEvent.objects.create(
            event_id='2', time=now, country='EU', currency='EUR',
            name='GDP', importance='medium',
            actual=None, forecast=Decimal('1.5'), previous=Decimal('1.4')
        )

    def test_calendar_list(self):
        response = self.client.get('/api/calendar/')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2

    def test_currencies_distinct(self):
        response = self.client.get('/api/calendar/currencies/')
        assert response.status_code == status.HTTP_200_OK
        assert sorted(response.data) == ['EUR', 'USD']
        assert len(response.data) == len(set(response.data))


class SyncCalendarTaskTests(TestCase):
    @patch('data.tasks.get_economic_calendar')
    def test_sync_creates_events(self, mock_get):
        mock_get.return_value = [
            {
                'eventId': 'test1', 'time': '2026-11-26T14:00:00Z',
                'countryCode': 'US', 'currency': 'USD', 'name': 'Test',
                'importance': 'high', 'actual': None, 'forecast': 1.5,
                'previous': 1.0, 'unit': 'percent'
            }
        ]
        sync_economic_calendar()
        assert EconomicEvent.objects.filter(event_id='test1').exists()

    @patch('data.tasks.get_economic_calendar')
    def test_sync_updates_events(self, mock_get):
        EconomicEvent.objects.create(
            event_id='test1', time = timezone.now() + timedelta(hours=1), country='US', currency='USD',
            name='Old', importance='high'
        )
        mock_get.return_value = [
            {
                'eventId': 'test1', 'time': '2026-11-26T14:00:00Z',
                'countryCode': 'US', 'currency': 'USD', 'name': 'Updated',
                'importance': 'high', 'actual': 2.0, 'forecast': 1.5,
                'previous': 1.0, 'unit': 'percent'
            }
        ]
        sync_economic_calendar()
        event = EconomicEvent.objects.get(event_id='test1')
        assert event.name == 'Updated'
        assert event.actual == Decimal('2.0')