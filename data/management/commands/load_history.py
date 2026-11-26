from django.core.management.base import BaseCommand
from datetime import datetime
from dateutil.relativedelta import relativedelta

from data.services.twelvedata import TwelveDataService
from data.services.candle_saver import validate_candles_for_db
from data.models import Candle


DEPTHS = {
    '5min': relativedelta(months=1),
    '1h': relativedelta(years=1),
    '4h': relativedelta(years=2),
    '1day': relativedelta(years=5),
    '1week': relativedelta(years=5),
    '1month': relativedelta(years=5),
}

#получаем и записываем свечи в бд одного интервала(таймфрейма)
class Command(BaseCommand):
    help = 'Загрузка определенной истории графика одного инструмента'

    def add_arguments(self, parser):
        parser.add_argument('--symbol', type=str, required=True, help='Символ инструмента (например, GBP/USD)')

    def get_valid_candles(self, api_symbol, interval, lower_bound, upper_bound):
        twelve_data = TwelveDataService()
        candles = twelve_data.get_all_candles(api_symbol, interval, lower_bound, upper_bound)
        validated_candles = validate_candles_for_db(
            candles=candles,
            symbol=api_symbol.replace('/', ''),
            interval=interval
        )
        return validated_candles

    def handle(self, *args, **options):
        symbol = options['symbol']
        now = datetime.now()
        now_str = datetime.strftime(now, '%Y-%m-%d %H:%M:%S')
        all_candles_model_list = []
        for interval, depth in DEPTHS.items():
            lower_bound_dt = now - depth
            lower_bound_str = datetime.strftime(lower_bound_dt, '%Y-%m-%d %H:%M:%S')
            all_candles_model_list.extend(self.get_valid_candles(
                api_symbol=symbol,
                interval=interval,
                lower_bound=lower_bound_str,
                upper_bound=now_str
            ))
        Candle.objects.bulk_create(all_candles_model_list, ignore_conflicts=True)

        self.stdout.write(self.style.SUCCESS(f'✅ {symbol}: загружено {len(all_candles_model_list)} свечей'))