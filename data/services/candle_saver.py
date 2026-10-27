from datetime import datetime, timezone
from decimal import Decimal

from data.models import Candle, Instrument


INTERVAL_DATE_FORMAT = {
    '5min': '%Y-%m-%d %H:%M:%S',
    '1h': '%Y-%m-%d %H:%M:%S',
    '4h': '%Y-%m-%d %H:%M:%S',
    '1day': '%Y-%m-%d',
    '1week': '%Y-%m-%d',
    '1month': '%Y-%m-%d',
}


def validate_candles_for_db(candles, symbol, interval):
    instrument = Instrument.objects.get(code=symbol)    
    models_list = []
    for candle in candles:
        fmt = INTERVAL_DATE_FORMAT[interval]
        candle['datetime'] = datetime.strptime(candle['datetime'], fmt).replace(tzinfo=timezone.utc)
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