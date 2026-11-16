# data/management/commands/run_aggregator.py
import asyncio
import logging
import redis.asyncio as redis
from django.core.management.base import BaseCommand
from pysignalr.client import SignalRClient
from data.services.biquote_aggregator import CandleAggregator

logger = logging.getLogger(__name__)

TIMEFRAMES = {
    '5min': 5,
    '1h': 60,
    '4h': 240,
    '1day': 1440,
}

class Command(BaseCommand):
    help = 'Запускает агрегатор тиков biquote (WebSocket)'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Запускаю агрегатор...'))
        try:
            asyncio.run(self.run_aggregator())
        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING('Остановлено пользователем.'))

    async def run_aggregator(self):
        redis_client = redis.Redis(host='localhost', port=6379, db=0)
        aggregator = CandleAggregator(TIMEFRAMES, redis_client, logger)

        client = SignalRClient("https://biquote.io/hubs/tick")

        async def on_tick(tick_data):
            for tick in tick_data:
                try:
                    await aggregator.on_tick(tick)
                except Exception as e:
                    logger.error(f"ОШИБКА В АГРЕГАТОРЕ: {type(e).__name__}: {e}")

        async def on_open():
            logger.info("Подключились к biquote. Подписываемся на XAUUSD...")
            await client.send("Subscribe", [["XAUUSD"]])

        client.on("ReceiveTick", on_tick)
        client.on_open(on_open)

        await client.run()