import requests
from datetime import  datetime, timedelta
from dateutil.relativedelta import relativedelta

from django.conf import settings


INTERVAL_TO_DELTA = {
    '5min': timedelta(minutes=5),
    '1h': timedelta(hours=1),
    '4h': timedelta(hours=4),
    '1day': timedelta(days=1),
    '1week': timedelta(weeks=1),
    '1month': relativedelta(months=1),
}


class TwelveDataError(Exception):
    """Базовая ошибка Twelve Data."""


class TwelveDataRateLimitError(TwelveDataError):
    """Превышен лимит запросов."""


class TwelveDataService:

    """Нужно понять, что start_date это нижняя граница нужного промежутка времени, соответственно end_date это верхняя граница(то есть свеча, новее start_date),
    но при этом данные отдаются от новым к старым, то есть от end_date к start_date.
    Чтобы не запутаться окончательно потом назову start_date и end_date - lower_bound и upper_bound соответственно, то есть нижняя и верхняя граница диапазона 
    и двигаться будем от верхней границы"""

    BASE_URL = "https://api.twelvedata.com"

    def __init__(self):
        self.api_key = settings.TWELVE_DATA_API_KEY

    def get_candles(self, symbol, interval, start_date, end_date, outputsize):
        url = f"{self.BASE_URL}/time_series"
        params = {
            'apikey': self.api_key,
            'symbol': symbol,
            'interval': interval,
            'start_date': start_date,
            'end_date': end_date,
            'outputsize': outputsize
        }
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        if data.get('status') != 'error' and 'values' in data:
            print(f'Загружаю свечи с {start_date} по {end_date},первая свеча {data['values'][0]['datetime']}, последняя свеча {data['values'][-1]['datetime']}')
            return data['values']
        else:
            message = data.get('message', 'Unknown error')
            if 'run out of API credits' in message or 'limit' in message.lower():
                raise TwelveDataRateLimitError(message)
            raise TwelveDataError(message)

    def get_all_candles(self, symbol, interval, lower_bound, upper_bound):
        all_candles = []
        current_upper_bound = datetime.strptime(upper_bound, '%Y-%m-%d %H:%M:%S')
        lower_bound = datetime.strptime(lower_bound, '%Y-%m-%d %H:%M:%S')
        step_skip = self._step_for_interval(interval)

        while current_upper_bound>lower_bound:
            candles = self.get_candles(
                symbol = symbol,
                interval = interval,
                start_date = lower_bound,
                end_date = current_upper_bound,
                outputsize=5000,
            )
            if not candles:
                break
            
            all_candles.extend(candles)

            if len(candles)<5000:
                break
            
            oldest_datetime_str = candles[-1]['datetime']
            oldest_datetime_dt = datetime.strptime(oldest_datetime_str, '%Y-%m-%d %H:%M:%S')
            current_upper_bound = oldest_datetime_dt-step_skip
        return all_candles

    def _step_for_interval(self, interval):
        if interval not in INTERVAL_TO_DELTA:
            raise ValueError(f'Неизвестный таймфрейм: {interval}')
        return INTERVAL_TO_DELTA[interval]

    def get_instrument_changes(self, symbol):
        url = f"{self.BASE_URL}/quote"
        params = {
            'apikey': self.api_key,
            'symbol': symbol,
        }
        response = requests.get(url, params)
        response.raise_for_status()
        data = response.json()

        if data.get('status') != 'error':
            return {
                'code': data['symbol'].replace('/', ''),
                'name': data['name'],
                'close': data['close'],
                'change': data['change'],
                'percent_change': data['percent_change'],
            }
        else:
            message = data.get('message', 'Неизвестная ошибка получения данных с TwelveData')
            if 'run out of API credits' in message or 'limit' in message.lower():
                raise TwelveDataRateLimitError(message)
            raise TwelveDataError(message)