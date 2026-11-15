import asyncio
import json
import logging
import redis.asyncio as redis
from pysignalr.client import SignalRClient
from datetime import datetime

logger = logging.getLogger(__name__)

TIMEFRAME_MINUTES = 5
redis_client = redis.Redis(host='localhost', port=6379, db=0)


def get_period_start(dt):
    minute = (dt.minute // TIMEFRAME_MINUTES) * TIMEFRAME_MINUTES
    return dt.replace(minute=minute, second=0, microsecond=0)


def create_candle(price, period_start):
    return {
        "open": price,
        "high": price,
        "low": price,
        "close": price,
        "time": period_start,
    }


def update_candle(candle, price):
    candle['high'] = max(candle['high'], price)
    candle['low'] = min(candle['low'], price)
    candle['close'] = price
    return candle


def close_candle(candle):
    logger.info(f"СВЕЧА ЗАКРЫЛАСЬ: {candle}")


async def write_in_redis(candle, key, symbol):
    candle_str = json.dumps(candle, default=str)
    await redis_client.set(key, candle_str)

    candle_for_pub = candle.copy()
    candle_for_pub['symbol'] = symbol
    candle_for_pub['timeframe'] = '5min'

    await redis_client.publish("candle_updates", json.dumps(candle_for_pub, default=str))


async def on_tick(tick_data):
    for tick in tick_data:
        symbol = tick['symbol']
        key = f"candle:{symbol}:5min"
        raw = await redis_client.get(key)

        if raw:
            candle = json.loads(raw)
            candle["time"] = datetime.strptime(candle["time"], "%Y-%m-%d %H:%M:%S")
        else:
            candle = None

        price = float(tick["mid"])
        tick_time = datetime.strptime(tick["time"], "%Y.%m.%d %H:%M:%S")
        period_start = get_period_start(tick_time)

        if candle is None:
            candle = create_candle(price, period_start)
            await write_in_redis(candle, key, symbol)
            continue

        if candle["time"] == period_start:
            candle = update_candle(candle, price)
            await write_in_redis(candle, key, symbol)
        else:
            close_candle(candle)
            candle = create_candle(price, period_start)
            await write_in_redis(candle, key, symbol)


async def on_open(client):
    logger.info("Подключились к biquote. Подписываемся на EURUSD...")
    await client.send("Subscribe", [["EURUSD"]])


async def main():
    client = SignalRClient("https://biquote.io/hubs/tick")
    client.on("ReceiveTick", on_tick)
    client.on_open(lambda: on_open(client))

    logger.info("Запускаю агрегатор (Ctrl+C для выхода)...")
    await client.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Остановлено.")