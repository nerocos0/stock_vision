import json
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock
from data.services.biquote_aggregator import CandleAggregator


@pytest.fixture
def redis_mock():
    mock = AsyncMock()
    mock.get = AsyncMock(return_value=None)
    mock.set = AsyncMock()
    mock.publish = AsyncMock()
    return mock


@pytest.fixture
def logger_mock():
    return MagicMock()


@pytest.fixture
def aggregator(redis_mock, logger_mock):
    timeframes = {'5min': 5, '1h': 60, '4h': 240, '1day': 1440}
    return CandleAggregator(timeframes, redis_mock, logger_mock)


class TestGetPeriodStart:
    def test_5min(self, aggregator):
        dt = datetime(2026, 11, 26, 14, 3, 45)
        assert aggregator._get_period_start(dt, 5) == datetime(2026, 11, 26, 14, 0, 0)

    def test_5min_boundary(self, aggregator):
        dt = datetime(2026, 11, 26, 14, 5, 0)
        assert aggregator._get_period_start(dt, 5) == datetime(2026, 11, 26, 14, 5, 0)

    def test_1h(self, aggregator):
        dt = datetime(2026, 11, 26, 14, 45, 0)
        assert aggregator._get_period_start(dt, 60) == datetime(2026, 11, 26, 14, 0, 0)

    def test_4h(self, aggregator):
        dt = datetime(2026, 11, 26, 14, 30, 0)
        assert aggregator._get_period_start(dt, 240) == datetime(2026, 11, 26, 12, 0, 0)

    def test_1day(self, aggregator):
        dt = datetime(2026, 11, 26, 14, 30, 0)
        assert aggregator._get_period_start(dt, 1440) == datetime(2026, 11, 26, 0, 0, 0)


class TestCandleOperations:
    def test_create_candle(self, aggregator):
        period_start = datetime(2026, 11, 26, 14, 0, 0)
        candle = aggregator._create_candle(1.1050, period_start)
        assert candle == {
            'open': 1.1050, 'high': 1.1050, 'low': 1.1050, 'close': 1.1050,
            'time': period_start
        }

    def test_update_candle_high(self, aggregator):
        candle = aggregator._create_candle(1.1050, datetime(2026, 11, 26, 14, 0, 0))
        result = aggregator._update_candle(candle, 1.1060)
        assert result['high'] == 1.1060
        assert result['close'] == 1.1060

    def test_update_candle_low(self, aggregator):
        candle = aggregator._create_candle(1.1050, datetime(2026, 11, 26, 14, 0, 0))
        result = aggregator._update_candle(candle, 1.1040)
        assert result['low'] == 1.1040
        assert result['close'] == 1.1040


@pytest.mark.asyncio
class TestOnTick:
    async def test_create_new_candle(self, aggregator, redis_mock):
        redis_mock.get = AsyncMock(return_value=None)
        tick = {'symbol': 'EURUSD', 'mid': '1.1050', 'time': '2026.11.26 14:03:45'}
        
        await aggregator.on_tick(tick)
        
        assert redis_mock.set.call_count == 4
        key = redis_mock.set.call_args_list[0][0][0]
        assert 'EURUSD:5min' in key

    async def test_update_existing_candle(self, aggregator, redis_mock):
        existing = {'open': 1.1050, 'high': 1.1050, 'low': 1.1050, 'close': 1.1050, 'time': '2026-11-26 14:00:00'}
        redis_mock.get = AsyncMock(return_value=json.dumps(existing))
        tick = {'symbol': 'EURUSD', 'mid': '1.1060', 'time': '2026.11.26 14:03:45'}
        
        await aggregator.on_tick(tick)
        
        assert redis_mock.set.call_count == 4

    async def test_close_and_create_new(self, aggregator, redis_mock):
        old = {'open': 1.1050, 'high': 1.1060, 'low': 1.1040, 'close': 1.1055, 'time': '2026-11-26 14:00:00'}
        redis_mock.get = AsyncMock(return_value=json.dumps(old))
        tick = {'symbol': 'EURUSD', 'mid': '1.1065', 'time': '2026.11.26 14:05:01'}
        
        await aggregator.on_tick(tick)
        
        aggregator.logger.info.assert_called()
        assert redis_mock.set.call_count == 4

    async def test_invalid_time_format(self, aggregator):
        tick = {'symbol': 'EURUSD', 'mid': '1.1050', 'time': 'invalid'}
        with pytest.raises(ValueError):
            await aggregator.on_tick(tick)


@pytest.mark.asyncio
class TestWriteInRedis:
    async def test_write_and_publish(self, aggregator, redis_mock):
        candle = {'open': 1.1050, 'high': 1.1060, 'low': 1.1040, 'close': 1.1055, 'time': datetime(2026, 11, 26, 14, 0, 0)}
        
        await aggregator._write_in_redis(candle, 'candle:EURUSD:5min', 'EURUSD', '5min')
        
        redis_mock.set.assert_called_once()
        redis_mock.publish.assert_called_once()
        
        publish_args = redis_mock.publish.call_args[0]
        assert publish_args[0] == 'candle_updates'
        data = json.loads(publish_args[1])
        assert data['symbol'] == 'EURUSD'
        assert data['timeframe'] == '5min'
        assert 'time' in data