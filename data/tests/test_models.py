from django.test import TestCase
from django.db.utils import IntegrityError
from datetime import datetime, timezone
from decimal import Decimal

from ..models import Instrument, Candle

class ModelTests(TestCase):

    def setUp(self):
        self.instrument = Instrument.objects.create(
            code="TESTUSD",
            name="Test Currency",
            instrument_type="forex"
        )

    def test_instrument_str(self):
        self.assertEqual(str(self.instrument), "TESTUSD")

    def test_candle_creation(self):
        candle = Candle.objects.create(
            instrument=self.instrument,
            timeframe="1h",
            datetime=datetime.now(timezone.utc),
            open_price=Decimal("1.1000"),
            high_price=Decimal("1.1100"),
            low_price=Decimal("1.0900"),
            close_price=Decimal("1.1050")
        )
        self.assertEqual(candle.instrument.code, "TESTUSD")
        self.assertIn("TESTUSD", str(candle))

    def test_candle_unique_constraint(self):
        dt = datetime.now(timezone.utc)
        
        Candle.objects.create(
            instrument=self.instrument, timeframe="1h", datetime=dt,
            open_price=1, high_price=1, low_price=1, close_price=1
        )
        
        with self.assertRaises(IntegrityError):
            Candle.objects.create(
                instrument=self.instrument, timeframe="1h", datetime=dt,
                open_price=2, high_price=2, low_price=2, close_price=2
            )