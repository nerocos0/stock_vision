import logging
from celery import shared_task
from datetime import timedelta
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist

from .models import Candle, Instrument
from .services.twelvedata import TwelveDataService
from .services.candle_saver import validate_candles_for_db
from .services.aggregator import aggregate_candles


class UpdateRealtimeError(Exception):
    """Базовая ошибка realtime обновления свечей"""

class UpdateRealtime5mCandlesError(UpdateRealtimeError):
    """Не удалось обновить 5m свечи"""

class UpdateRealtimeOtherCandlesError(UpdateRealtimeError):
    """Не удалось обновить остальные свечи свечи"""


logger = logging.getLogger(__name__)

@shared_task
def update_realtime_all_candles():
    logger.info('Запуск обновления свечей')
    active_instruments = Instrument.objects.filter(is_active=True)

    for instrument in active_instruments:
        try:
            logger.info(f'Обновляю 5m свечи для {instrument}')
            update_realtime_5m_candles(instrument.code)
        except Exception as e:
            logger.error(f'Ошибка обновления 5m свечей для {instrument}: {e}')
            continue

        try:
            logger.info(f'Обновляю остальные свечи для {instrument}')
            update_realtime_other_candles(instrument)
        except Exception as e:
            logger.error(f'Ошибка обновления остальных свечей для {instrument}: {e}')

        logger.info(f'Успешно обновились все свечи {instrument}')



def update_realtime_5m_candles(symbol):
    timeframe = '5min'
    now = timezone.now()
    end_date_str = now.strftime('%Y-%m-%d %H:%M:%S')

    try:
        instrument = Instrument.objects.get(code=symbol, is_active=True)
    except ObjectDoesNotExist:
        raise UpdateRealtime5mCandlesError(f'Инструмент {symbol} не найден или неактивен')

    last_5m_candle = Candle.objects.filter(instrument=instrument, timeframe=timeframe).order_by('-datetime').first()
    if last_5m_candle and last_5m_candle.datetime < now:
        start_date = last_5m_candle.datetime.strftime('%Y-%m-%d %H:%M:%S')
    else:
        start_date = (now - timedelta(hours=1)).strftime('%Y-%m-%d %H:%M:%S')

    api_symbol = f"{instrument.code[:3]}/{instrument.code[3:]}"

    twelve_data = TwelveDataService()
    try:
        new_5m_candles = twelve_data.get_candles(
            symbol=api_symbol,
            interval=timeframe,
            start_date=start_date,
            end_date=end_date_str,
            outputsize=5000
        )
    except Exception as e:
        raise UpdateRealtime5mCandlesError(f"Ошибка API при получении 5m для {symbol}: {e}") from e

    validated_candles = validate_candles_for_db(
        candles=new_5m_candles,
        symbol=symbol,
        interval=timeframe
    )
    if validated_candles:
        Candle.objects.bulk_create(
            validated_candles, 
            update_conflicts=True, 
            unique_fields=['instrument', 'timeframe', 'datetime'],
            update_fields=['open_price', 'high_price', 'low_price', 'close_price']
        )

#пока сделаем для 4h базовый интервал(00:00-04:00-08:00.....)
#потом будем фильтровать для разных инструментов, ибо например для XAUUSD нужно 01:00-05:00-09:00.....
def update_realtime_other_candles(instrument):
    now = timezone.now()
    #для 1h
    start_of_1h = now.replace(minute=0, second=0, microsecond=0)
    get_aggregate_and_save_in_db_candles(
        start_hour=start_of_1h,
        now=now,
        instrument=instrument,
        timeframe_for_aggregate='1h'
    )

    #для 4h
    hour_block = (now.hour//4)*4
    start_of_4h = now.replace(hour=hour_block, minute=0, second=0, microsecond=0)
    get_aggregate_and_save_in_db_candles(
        start_hour=start_of_4h,
        now=now,
        instrument=instrument,
        timeframe_for_aggregate='4h'
    )    


def get_aggregate_and_save_in_db_candles(start_hour, now, instrument, timeframe_for_aggregate):
    candles_for_aggregate = Candle.objects.filter(
        instrument=instrument,
        timeframe = '5min',
        datetime__gte=start_hour,
        datetime__lte=now        
    )
    if not candles_for_aggregate.exists():
        return
    
    aggregated_data = aggregate_candles(candles_for_aggregate, timeframe_for_aggregate)
    validated_candles = validate_candles_for_db(
        candles=aggregated_data,
        symbol=instrument.code,
        interval=timeframe_for_aggregate
    )

    if validated_candles:
        Candle.objects.bulk_create(
            validated_candles, 
            update_conflicts=True, 
            unique_fields=['instrument', 'timeframe', 'datetime'],
            update_fields=['open_price', 'high_price', 'low_price', 'close_price']
        )