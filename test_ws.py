import asyncio
import json
import redis.asyncio as redis
from pysignalr.client import SignalRClient
from datetime import datetime


TIMEFRAME_MINUTES = 5

redis_client = redis.Redis(host='localhost', port=6379, db=0)


def get_period_start(dt):
    minute = (dt.minute // TIMEFRAME_MINUTES) * TIMEFRAME_MINUTES
    dt = dt.replace(minute=minute, second=0, microsecond=0)
    return dt

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
    print(f'СВЕЧА ЗАКРЫЛАСЬ: {candle}')

async def on_tick(tick_data):
    for tick in tick_data:
        key = f"candle:{tick['symbol']}:5m"
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
            candle_str = json.dumps(candle, default=str)

            await redis_client.set(key, candle_str)

            print(f"Начата новая свеча: {candle}")
            continue

        if candle["time"] == period_start:
            print('ОБНОВЛЕНА СВЕЧА')
            candle = update_candle(candle, price)
            candle_str = json.dumps(candle, default=str)
                
            await redis_client.set(key, candle_str)
        else:
            close_candle(candle)
            candle = create_candle(price, period_start)
            candle_str = json.dumps(candle, default=str)
                
            await redis_client.set(key, candle_str)            
            'загружаю в бд тут'
            print(f"Начата новая свеча: {candle}")

async def on_open(client):
    print("Подключились. Подписываемся на EURUSD...")
    await client.send("Subscribe", [["EURUSD"]])

async def main():
    client = SignalRClient("https://biquote.io/hubs/tick")
    client.on("ReceiveTick", on_tick)
    client.on_open(lambda: on_open(client))
    
    print("Запускаю агрегатор (Ctrl+C для выхода)...")
    await client.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nОстановлено.")
