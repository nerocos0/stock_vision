from datetime import datetime, timezone, timedelta
from decimal import Decimal
from django.core.cache import cache
from rest_framework.test import APITestCase
from rest_framework import status
from data.models import Instrument, Candle


class CandleLimitTests(APITestCase):
    def setUp(self):
        cache.clear()
        
        self.instrument = Instrument.objects.create(
            code='EURUSD', name='Euro', instrument_type='FOREX'
        )
        now = datetime.now(timezone.utc)
        for i in range(500):
            Candle.objects.create(
                instrument=self.instrument, timeframe='1h',
                datetime=now - timedelta(hours=i),
                open_price=Decimal('1.1'), high_price=Decimal('1.2'),
                low_price=Decimal('1.0'), close_price=Decimal('1.15')
            )

    def test_limit_returns_last_n(self):
        response = self.client.get('/api/candles/', {
            'symbol': 'EURUSD', 'timeframe': '1h', 'limit': 10
        })
        assert response.status_code == status.HTTP_200_OK
        data = response.data
        assert len(data) == 10
        datetimes = [item['datetime'] for item in data]
        assert datetimes == sorted(datetimes)

    def test_limit_with_to_date(self):
        now = datetime.now(timezone.utc)
        to_date = (now - timedelta(hours=100)).strftime('%Y-%m-%d %H:%M:%S')
        response = self.client.get('/api/candles/', {
            'symbol': 'EURUSD', 'timeframe': '1h', 'limit': 10, 'to': to_date
        })
        assert response.status_code == status.HTTP_200_OK
        data = response.data
        assert len(data) == 10
        for item in data:
            assert datetime.fromisoformat(item['datetime']) <= now

    def test_no_limit_returns_all(self):
        response = self.client.get('/api/candles/', {
            'symbol': 'EURUSD', 'timeframe': '1h'
        })
        assert response.status_code == status.HTTP_200_OK
        data = response.data
        assert len(data) == 500