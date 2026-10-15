from django.core.management.base import BaseCommand
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from django.forms.models import model_to_dict

from data.services.twelvedata import TwelveDataService
from data.models import Candle, Instrument

class Command(BaseCommand):
    #получаем и записываем свечи в бд одного интервала
    def get_and_save_candles_in_db(self, symbol, interval, start_date, end_date):
        twelve_data = TwelveDataService()
        candles = twelve_data.get_candles(symbol, interval, start_date, end_date)
        keys_to_exclude = {'open', 'close', 'high', 'low'}
        models_list = []
        for candle in candles:
            candle['datetime'] = datetime.strptime(candle['datetime'], '%Y-%m-%d %H:%M:%S').replace(tzinfo=timezone(timedelta(hours=3)))
            candle['open_price'] = Decimal(candle['open'])
            candle['close_price'] = Decimal(candle['close'])
            candle['high_price'] = Decimal(candle['high'])
            candle['low_price'] = Decimal(candle['low'])
            candle['timeframe'] = interval
            candle['instrument'] = Instrument.objects.get(code=symbol.replace('/', ''))
            clean_data = {k: v for k, v in candle.items() if k not in keys_to_exclude}
            new_instance = Candle(**clean_data)
            models_list.append(new_instance)
        Candle.objects.bulk_create(models_list, ignore_conflicts=True)
    def handle():
        pass

test = Command()
test.get_and_save_candles_in_db(symbol='EUR/USD', interval='5min', start_date='2026-10-13T16:00:00', end_date='2026-10-13T16:09:00')