import requests
import logging

logger = logging.getLogger(__name__)

class BiquoteError(Exception):
    """Базовая ошибка Biquote."""


def get_events_by_importance(countries, importance):
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

def get_economic_calendar(countries='US,EU,GB', importances=['high', 'medium', 'low']):
    """
    Получает экономический календарь с Biquote API.
    
    :param countries: Страны, для которых нужно получить события (например, "US,EU,GB").
    :param importances: Важность событий (например, "high", "medium", "low").
    :return: Список событий экономического календаря.
    :raises BiquoteError: Если произошла ошибка при запросе или обработке данных.
    """
    all_events = []
    try:
        for importance in importances:
            events = get_events_by_importance(countries, importance)
            if events:
                all_events.extend(events)
    except BiquoteError as e:
        logger.error(f"Ошибка получения экономического календаря: {e}")
        raise

    return all_events