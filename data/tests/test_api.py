from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from django.core.cache import cache

from ..models import Instrument, Candle


class APITests(APITestCase):
    """Тестируем эндпоинты"""

    def setUp(self):
        cache.clear()

        self.instrument = Instrument.objects.create(
            code="EURUSD", name="Euro / USD", instrument_type="forex"
        )

        self.dt = datetime.now(timezone.utc)

        for i in range(5):
            Candle.objects.create(
                instrument=self.instrument,
                timeframe="1h",
                datetime=self.dt - timedelta(hours=i),
                open_price=Decimal("1.1000"),
                high_price=Decimal("1.1100"),
                low_price=Decimal("1.0900"),
                close_price=Decimal("1.1050")
            )

        for i in range(20):
            Candle.objects.create(
                instrument=self.instrument,
                timeframe="1h",
                datetime=self.dt - timedelta(days=2, hours=i),
                open_price=Decimal("1.1000"),
                high_price=Decimal("1.1100"),
                low_price=Decimal("1.0900"),
                close_price=Decimal("1.1050")
            )

    def test_instruments_list(self):
        """GET /api/instruments/ - должен вернуть список"""
        url = reverse('data:instruments-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['code'], "EURUSD")

    def test_candles_list_with_filter(self):
        """GET /api/candles/ - проверяем фильтрацию по символу и ТФ"""
        url = reverse('data:candles-list')

        response = self.client.get(url, {'symbol': 'EURUSD', 'timeframe': '1h'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.data

        self.assertEqual(len(data), 25)

    def test_indicators_endpoint(self):
        """GET /api/indicators/ - проверяем расчет RSI через API"""
        url = '/api/indicators/'

        params = {
            'symbol': 'EURUSD',
            'timeframe': '1h',
            'type': 'rsi',
            'period': 3,
            'from': (self.dt - timedelta(hours=5)).strftime('%Y-%m-%d %H:%M:%S'),
            'to': self.dt.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        response = self.client.get(url, params)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertTrue(len(response.data) > 0, "IndicatorView вернул пустой список")

        first_item = response.data[0]
        self.assertIn('time', first_item)
        self.assertIn('value', first_item)

        self.assertTrue(0 <= first_item['value'] <= 100)