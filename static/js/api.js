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

// Получить сводку по всем инструментам для главной страницы
export async function fetchSummary() {
    const response = await fetch(`${API_BASE}/instruments/summary/`);
    if (!response.ok) throw new Error('Ошибка загрузки сводки');
    return await response.json();
}

// Логин пользователя (получение JWT)
export async function loginUser(username, password) {
    const response = await fetch(`${API_BASE}/auth/token/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ username, password })
    });
    
    if (!response.ok) {
        throw new Error('Неверный логин или пароль');
    }
    return await response.json(); // Вернет { access: "...", refresh: "..." }
}

// Добавить в избранное
export async function addFavorite(instrumentId) {
    const token = localStorage.getItem('access_token');
    const response = await fetch(`${API_BASE}/auth/favorites/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ instrument: instrumentId })
    });
    if (!response.ok) throw new Error('Ошибка добавления в избранное');
    return await response.json();
}

// Удалить из избранного
export async function removeFavorite(favoriteId) {
    const token = localStorage.getItem('access_token');
    const response = await fetch(`${API_BASE}/auth/favorites/${favoriteId}/`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
    });
    if (!response.ok) throw new Error('Ошибка удаления из избранного');
}

// Получить список избранного текущего пользователя
export async function fetchFavorites() {
    const token = localStorage.getItem('access_token');
    const response = await fetch(`${API_BASE}/auth/favorites/`, {
        headers: { 
            'Authorization': `Bearer ${token}` 
        }
    });
    
    if (!response.ok) {
        throw new Error('Ошибка загрузки избранного');
    }
    
    return await response.json();
}