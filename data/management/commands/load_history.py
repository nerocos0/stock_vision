from django.core.management.base import BaseCommand
from datetime import datetime, timezone
from decimal import Decimal
from dateutil.relativedelta import relativedelta

from data.constants import INTERVAL_DATE_FORMAT
from data.services.twelvedata import TwelveDataService
from data.models import Candle, Instrument


DEPTHS = {
    '5min': relativedelta(months=1),
    '1h': relativedelta(years=1),
    '4h': relativedelta(years=2),
    '1day': relativedelta(years=5),
    '1week': relativedelta(years=5),
    '1month': relativedelta(years=5),
}

class Command(BaseCommand):
    help = 'Загрузка определенной истории графика одного инструмента'

    #получаем и записываем свечи в бд одного интервала
    def get_valid_candles(self, symbol, interval, lower_bound, upper_bound):
        twelve_data = TwelveDataService()
        candles = twelve_data.get_all_candles(symbol, interval, lower_bound, upper_bound)
        models_list = []
        for candle in candles:
            fmt = INTERVAL_DATE_FORMAT[interval]
            candle['datetime'] = datetime.strptime(candle['datetime'], fmt).replace(tzinfo=timezone.utc)
            instrument = Instrument.objects.get(code=symbol.replace('/', ''))
            new_instance = Candle(
                instrument=instrument,
                timeframe=interval,
                datetime=candle['datetime'],
                open_price=Decimal(candle['open']),
                high_price=Decimal(candle['high']),
                low_price=Decimal(candle['low']),
                close_price=Decimal(candle['close']),
            )
            models_list.append(new_instance)
        return models_list

    def handle(self, *args, **options):
        now = datetime.now()
        now_str = datetime.strftime(now, '%Y-%m-%d %H:%M:%S')
        all_candles_model_list = []
        for interval, depth in DEPTHS.items():
            lower_bound_dt = now - depth
            lower_bound_str = datetime.strftime(lower_bound_dt, '%Y-%m-%d %H:%M:%S')
            all_candles_model_list.extend(self.get_valid_candles(
                symbol='EUR/USD',
                interval=interval,
                lower_bound=lower_bound_str,
                upper_bound=now_str
            ))
        Candle.objects.bulk_create(all_candles_model_list, ignore_conflicts=True)        