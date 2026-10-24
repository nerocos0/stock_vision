import math
from django.test import TestCase

from ..services.indicators import calculate_rsi, calculate_ema, calculate_sma
class IndicatorsLogicTests(TestCase):

    def setUp(self):
        self.prices = [1.0, 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 1.9]

    def test_sma_calculation(self):
        sma = calculate_sma(self.prices, period=3)
        
        # Проверяем, что первые два значения - это NaN
        self.assertTrue(math.isnan(sma.iloc[0]))
        self.assertTrue(math.isnan(sma.iloc[1]))
        
        # Проверяем третье значение (оно должно быть средним за 3 периода)
        self.assertAlmostEqual(float(sma.iloc[2]), 1.1, places=4)

    def test_ema_calculation(self):
        ema = calculate_ema(self.prices, period=3)
        self.assertIsNotNone(ema.iloc[0])
        self.assertEqual(len(ema), len(self.prices))

    def test_rsi_calculation(self):
        rsi = calculate_rsi(self.prices, period=3)
        
        self.assertFalse(rsi.isna().any(), "RSI не должен содержать NaN!")

        for val in rsi:
            if val is not None:
                self.assertTrue(0 <= val <= 100)