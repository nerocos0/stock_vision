import asyncio
from pysignalr.client import SignalRClient
from datetime import datetime


TIMEFRAME_MINUTES = 5

current_candle = None

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
    global current_candle

    for tick in tick_data:
        price = float(tick["mid"])
        tick_time = datetime.strptime(tick["time"], "%Y.%m.%d %H:%M:%S")

        period_start = get_period_start(tick_time)

        if current_candle is None:
            current_candle = create_candle(price, period_start)
            print(f"Начата новая свеча: {current_candle}")
            return

        if current_candle["time"] == period_start:
            print('ОБНОВЛЕНА СВЕЧА')
            current_candle = update_candle(current_candle, price)

        else:
            close_candle(current_candle)
            current_candle = create_candle(price, period_start)
            print(f"Начата новая свеча: {current_candle}")

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
