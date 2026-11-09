import requests
import logging

logger = logging.getLogger(__name__)

class BiquoteError(Exception):
    """Базовая ошибка Biquote."""


def get_economic_calendar(countries="US,EU,GB", importance="high"):
    url = 'https://biquote.io/api/calendar'
    params = {
        'countries': countries,
        'importance': importance,
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if isinstance(data, list):
            return data
        else:
            raise BiquoteError(f"Неожиданный формат ответа: {type(data)}")
            
    except requests.RequestException as e:
        raise BiquoteError(f"Ошибка запроса к Biquote: {e}")