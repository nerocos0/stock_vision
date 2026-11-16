import json
import asyncio
import logging
import redis.asyncio as redis
from channels.generic.websocket import AsyncWebsocketConsumer

logger = logging.getLogger(__name__)


class CandleConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.symbol = self.scope['url_route']['kwargs']['symbol']
        self.timeframe = self.scope['url_route']['kwargs']['timeframe']

        self.redis_client = redis.Redis(
            host='localhost',
            port=6379,
            db=0,
            health_check_interval=30,
        )

        await self.accept()

        self.pubsub = self.redis_client.pubsub()
        await self.pubsub.subscribe("candle_updates")

        self.listener_task = asyncio.create_task(self.listen_pubsub())

    async def listen_pubsub(self):
        while True:
            try:
                async for message in self.pubsub.listen():
                    if message['type'] == 'message':
                        data = json.loads(message['data'])
                        if data.get('symbol') == self.symbol and data.get('timeframe') == self.timeframe:
                            await self.send(text_data=json.dumps(data))
            except Exception as e:
                logger.error(f"ОШИБКА В CONSUMER (перезапуск через 1 сек): {type(e).__name__}: {e}")
                await asyncio.sleep(1)
                try:
                    await self.pubsub.close()
                except Exception:
                    pass
                self.pubsub = self.redis_client.pubsub()
                await self.pubsub.subscribe("candle_updates")

    async def disconnect(self, close_code):
        if hasattr(self, 'listener_task'):
            self.listener_task.cancel()
        if hasattr(self, 'pubsub'):
            await self.pubsub.unsubscribe("candle_updates")
            await self.pubsub.close()
        if hasattr(self, 'redis_client'):
            await self.redis_client.close()