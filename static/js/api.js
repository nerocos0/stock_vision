//  Базовые URL-адреса нашего API
const API_BASE = '/api';

//получить список доступных инструментов
export async function fetchInstruments() {
    const response = await fetch(`${API_BASE}/instruments/`);
    if (!response.ok) throw new Error('Ошибка загрузки инструментов');
    return await response.json();
}

//получить свечи по параметрам
export async function fetchCandles(symbol, timeframe, fromDate, toDate) {
    const url = `${API_BASE}/candles/?symbol=${symbol}&timeframe=${timeframe}&from=${fromDate}&to=${toDate}`;
    const response = await fetch(url);
    if (!response.ok) throw new Error('Ошибка загрузки свечей');
    return await response.json();
}