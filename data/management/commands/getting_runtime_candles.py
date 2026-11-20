import os
import asyncio
import logging
import redis.asyncio as redis
from django.core.management.base import BaseCommand
from pysignalr.client import SignalRClient
from pysignalr.exceptions import NegotiationFailure

from data.services.biquote_aggregator import CandleAggregator
from data.models import Instrument

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

        symbols = list(
            Instrument.objects.filter(is_active=True).values_list('code', flat=True)
        )
        if not symbols:
            logger.error('Нет активных инструментов в БД')
            return
                
        try:
            asyncio.run(self.run_aggregator(symbols))
        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING('Остановлено пользователем.'))

    async def run_aggregator(self, symbols):
        redis_client = redis.Redis(
            host=os.getenv('REDIS_HOST', 'localhost'),
            port=6379,
            db=0
        )
        aggregator = CandleAggregator(TIMEFRAMES, redis_client, logger)

        client = SignalRClient(
            "https://biquote.io/hubs/tick",
            retry_sleep=5,
            retry_multiplier=2,
            retry_count=5,
        )

        async def on_tick(tick_data):
            for tick in tick_data:
                try:
                    await aggregator.on_tick(tick)
                except Exception as e:
                    logger.error(f"ОШИБКА В АГРЕГАТОРЕ: {type(e).__name__}: {e}")

        async def on_open():
            logger.info(f"Подключились к biquote. Подписываемся на {symbols} ...")
            await client.send("Subscribe", [symbols])

        async def on_subscription_state(*args):
            logger.debug(f"Состояние подписки biquote: {args}")

        client.on("ReceiveTick", on_tick)
        client.on_open(on_open)
        client.on("ReceiveSubscriptionState", on_subscription_state)

        while True:
            try:
                await client.run()
            except NegotiationFailure as e:
                logger.error(f"Не удалось подключиться к biquote (429?): {e}")
                logger.info("Жду 60 секунд перед повторной попыткой...")
                await asyncio.sleep(60)