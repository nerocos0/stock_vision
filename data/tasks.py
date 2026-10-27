from datetime import timedelta
from django.utils import timezone
from django.core.exceptions import ValidationError

from .models import Candle, Instrument
from .services.twelvedata import TwelveDataService
from .services.candle_saver import validate_candles_for_db


def update_realtime_candles(symbol):
    timeframe = '5min'
    now = timezone.now()

    try:
        instrument = Instrument.objects.get(code=symbol, is_active=True)
    except Instrument.DoesNotExist:
        raise ValidationError(
            'Инструмента %(symbol) не существует или он не активен',
            params={'symbol': symbol},
            code='no_instrument',
        )

    last_5m_candle = Candle.objects.filter(instrument=instrument, timeframe=timeframe).order_by('-datetime').first()
    if last_5m_candle:
        start_date = last_5m_candle.datetime.strftime('%Y-%m-%d %H:%M:%S')
    else:
        start_date = (now - timedelta(hours=1)).strftime('%Y-%m-%d %H:%M:%S')

    api_symbol = f"{instrument.code[:3]}/{instrument.code[3:]}"

    twelve_data = TwelveDataService()
    new_5m_candles = twelve_data.get_candles(
        symbol=api_symbol,
        interval=timeframe,
        start_date=start_date,
        end_date=now
    )

    validated_candles = validate_candles_for_db(
        candles=new_5m_candles,
        symbol=symbol,
        interval=timeframe
    )

    Candle.objects.update_or_create(validated_candles)