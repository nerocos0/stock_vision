from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from datetime import datetime, timezone, timedelta
from decimal import Decimal

from ..models import Instrument, Candle


class APITests(APITestCase):
    """Тестируем эндпоинты"""

    def setUp(self):
        # 1. Создаем инструмент
        self.instrument = Instrument.objects.create(
            code="EURUSD", name="Euro / USD", instrument_type="forex"
        )
        
        # Берем текущее время
        self.dt = datetime.now(timezone.utc)
        
        # 2. Создаем 5 свечей для ОСНОВНОГО диапазона (которые должны попасть в график)
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
            
        # 3. Создаем 20 свечей для РАЗОГРЕВА (warmup), которые старше основного диапазона
        # (Это нужно, чтобы RSI в IndicatorView смог посчитать значения)
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
        # ВАЖНО: так как у нас DefaultRouter с basename='instruments', 
        # имя пути будет 'data:instruments-list'
        url = reverse('data:instruments-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Проверяем, что в результатах есть наш EURUSD
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['code'], "EURUSD")

    def test_candles_list_with_filter(self):
        """GET /api/candles/ - проверяем фильтрацию по символу и ТФ"""
        url = reverse('data:candle-list')
        
        # Запрашиваем свечи для EURUSD за последние несколько часов
        response = self.client.get(url, {'symbol': 'EURUSD', 'timeframe': '1h'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Так как мы не отключали пагинацию, данные лежат в ключе 'results'
        data = response.data.get('results', response.data)
        
        # Проверяем, что вернулись ВСЕ свечи (5 основных + 20 разогрева = 25)
        # Если фильтр по датам в CandleView не передавался, он вернет все 25
        self.assertEqual(len(data), 25)

    def test_indicators_endpoint(self):
        """GET /api/indicators/ - проверяем расчет RSI через API"""
        url = '/api/indicators/' # Используем прямой путь, так как это обычный APIView
        
        # Формируем запрос: запрашиваем RSI с периодом 3 за последние 5 часов
        params = {
            'symbol': 'EURUSD',
            'timeframe': '1h',
            'type': 'rsi',
            'period': 3,
            'from': (self.dt - timedelta(hours=5)).strftime('%Y-%m-%d %H:%M:%S'),
            'to': self.dt.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        response = self.client.get(url, params)
        
        # Проверяем, что запрос прошел успешно
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Проверяем, что вернулся непустой список
        self.assertTrue(len(response.data) > 0, "IndicatorView вернул пустой список")
        
        # Проверяем структуру ответа
        first_item = response.data[0]
        self.assertIn('time', first_item)
        self.assertIn('value', first_item)
        
        # Проверяем, что значение RSI в пределах 0-100
        self.assertTrue(0 <= first_item['value'] <= 100)