from django.test import TestCase
from unittest.mock import patch, Mock
from datetime import datetime, timedelta

from ..services.twelvedata import TwelveDataService, TwelveDataRateLimitError


class TwelveDataServiceTests(TestCase):

    def setUp(self):
        self.service = TwelveDataService()
        self.service.api_key = "fake_api_key"

    @patch('requests.get')
    def test_get_candles_success(self, mock_get):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "ok",
            "values": [
                {"datetime": "2026-10-24 10:00:00", "open": "1.1", "high": "1.2", "low": "1.0", "close": "1.15"},
                {"datetime": "2026-10-24 09:00:00", "open": "1.0", "high": "1.1", "low": "0.9", "close": "1.05"}
            ]
        }
        mock_get.return_value = mock_response

        result = self.service.get_candles(
            symbol="EUR/USD", interval="1h",
            start_date="2026-10-24", end_date="2026-10-25", outputsize=2
        )

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['datetime'], "2026-10-24 10:00:00")
        
        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        self.assertEqual(kwargs['params']['symbol'], "EUR/USD")
        self.assertEqual(kwargs['params']['interval'], "1h")

    @patch('requests.get')
    def test_get_candles_rate_limit_error(self, mock_get):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "error",
            "message": "You have run out of API credits for the current minute."
        }
        mock_get.return_value = mock_response

        with self.assertRaises(TwelveDataRateLimitError):
            self.service.get_candles(
                symbol="EUR/USD", interval="1h", 
                start_date="2026-10-24", end_date="2026-10-25", outputsize=2
            )

    @patch('requests.get')
    def test_get_all_candles_pagination(self, mock_get):
        base_time = datetime(2026, 10, 24, 12, 0, 0)
        fake_candles_page1 = []
        for i in range(5000):
            dt_str = (base_time - timedelta(minutes=i)).strftime('%Y-%m-%d %H:%M:%S')
            fake_candles_page1.append({"datetime": dt_str, "open": "1", "high": "1", "low": "1", "close": "1"})

        fake_candles_page2 = [
            {"datetime": "2026-10-20 12:00:00", "open": "1", "high": "1", "low": "1", "close": "1"}
        ]

        mock_response_1 = Mock()
        mock_response_1.status_code = 200
        mock_response_1.json.return_value = {"status": "ok", "values": fake_candles_page1}

        mock_response_2 = Mock()
        mock_response_2.status_code = 200
        mock_response_2.json.return_value = {"status": "ok", "values": fake_candles_page2}

        mock_get.side_effect = [mock_response_1, mock_response_2]

        result = self.service.get_all_candles(
            symbol="EUR/USD", interval="1h",
            lower_bound="2026-10-20 00:00:00",
            upper_bound="2026-10-24 12:00:00"
        )

        self.assertEqual(len(result), 5001)
        self.assertEqual(mock_get.call_count, 2)