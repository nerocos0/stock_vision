import requests
import os
from dotenv import load_dotenv
from datetime import  datetime, timedelta
from dateutil.relativedelta import relativedelta

load_dotenv()

INTERVAL_TO_DELTA = {
    '1min': timedelta(minutes=1),
    '5min': timedelta(minutes=5),
    '15min': timedelta(minutes=15),
    '30min': timedelta(minutes=30),
    '1h': timedelta(hours=1),
    '4h': timedelta(hours=4),
    '1day': timedelta(days=1),
    '1week': timedelta(weeks=1),
}

class TwelveDataService:
    BASE_URL = "https://api.twelvedata.com"

    def __init__(self):
        self.api_key = os.getenv('TWELVE_DATA_API_KEY')

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
            raise Exception(f"Ошибка подгрузки свечей: {data.get('message', 'Unknown error')}")

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
                print('больше не найдено свечей')
                break
            
            all_candles.extend(candles)

            if len(candles)<5000:
                break
            
            oldest_datetime_str = candles[-1]['datetime']
            oldest_datetime_dt = datetime.strptime(oldest_datetime_str, '%Y-%m-%d %H:%M:%S')
            current_upper_bound = oldest_datetime_dt-step_skip
        return all_candles

    def _step_for_interval(self, interval):
        if interval=='1month':
            return relativedelta(months=1)
        if interval not in INTERVAL_TO_DELTA:
            raise ValueError(f'Неизвестный таймфрейм: {interval}')
        return INTERVAL_TO_DELTA[interval]


test = TwelveDataService()
candles = test.get_all_candles(symbol='EUR/USD', interval='1month', lower_bound='2021-09-01 16:00:00', upper_bound='2026-08-01 16:09:00')
print(f'Длина финального списка свечей {len(candles)}')
print(candles[-1]['datetime'])