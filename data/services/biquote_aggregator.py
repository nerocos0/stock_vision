import json
from calendar import timegm
from datetime import datetime

from data.tasks import save_realtime_candle


class CandleAggregator():
    """
    Собирает тики biquote в свечи для нескольких таймфреймов.
    Текущие свечи хранит в Redis, закрытые отправляет в Celery для записи в БД.
    """
    def __init__(self, timeframes, redis_client, logger):
        self.timeframes = timeframes
        self.redis = redis_client
        self.logger = logger

    def _get_period_start(self, dt, minutes):
        if minutes < 60:
            minute = (dt.minute // minutes) * minutes
            return dt.replace(minute=minute, second=0, microsecond=0)
        elif minutes < 1440:
            hours_step = minutes // 60
            hour = (dt.hour // hours_step) * hours_step
            return dt.replace(hour=hour, minute=0, second=0, microsecond=0)
        else:
            return dt.replace(hour=0, minute=0, second=0, microsecond=0)

    def _create_candle(self, price, period_start):
        return {
            "open": price,
            "high": price,
            "low": price,
            "close": price,
            "time": period_start,
        }

    def _update_candle(self, candle, price):
        candle['high'] = max(candle['high'], price)
        candle['low'] = min(candle['low'], price)
        candle['close'] = price
        return candle

    def _close_candle(self, candle, symbol, tf_name):
        self.logger.info(f"СВЕЧА {tf_name} ЗАКРЫЛАСЬ: {candle}")
        try:
            save_realtime_candle.delay(symbol, tf_name, candle)
        except Exception as e:
            self.logger.error(f"Не удалось отправить задачу в Celery: {e}")

    async def _write_in_redis(self, candle, key, symbol, timeframe):
        candle_str = json.dumps(candle, default=str)
        await self.redis.set(key, candle_str)

        candle_for_pub = candle.copy()
        candle_for_pub['symbol'] = symbol
        candle_for_pub['timeframe'] = timeframe
        candle_for_pub['time'] = timegm(candle['time'].utctimetuple())

        await self.redis.publish("candle_updates", json.dumps(candle_for_pub, default=str))

    async def on_tick(self, tick):
        symbol = tick['symbol']
        price = float(tick['mid'])
        tick_time = datetime.strptime(tick["time"], "%Y.%m.%d %H:%M:%S")

        for tf_name, tf_minutes in self.timeframes.items():
            key = f"candle:{symbol}:{tf_name}"
            raw = await self.redis.get(key)
            period_start = self._get_period_start(tick_time, tf_minutes)

            if raw:
                candle = json.loads(raw)
                candle["time"] = datetime.strptime(candle["time"], "%Y-%m-%d %H:%M:%S")
            else:
                candle = None

            if candle is None:
                candle = self._create_candle(price, period_start)
                await self._write_in_redis(candle, key, symbol, tf_name)
                continue

            if candle["time"] == period_start:
                candle = self._update_candle(candle, price)
                await self._write_in_redis(candle, key, symbol, tf_name)
            else:
                self._close_candle(candle, symbol, tf_name)
                candle = self._create_candle(price, period_start)
                await self._write_in_redis(candle, key, symbol, tf_name)