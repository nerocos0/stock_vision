import { toUnixSeconds } from './utils.js';

const API_BASE = '/api';

const ACCESS_KEY = 'access_token';
const REFRESH_KEY = 'refresh_token';

let refreshPromise = null;

async function refreshAccessToken() {
    if (refreshPromise) return refreshPromise;

    refreshPromise = (async () => {
        const refresh = localStorage.getItem(REFRESH_KEY);
        if (!refresh) throw new Error('no refresh token');

        const resp = await fetch(`${API_BASE}/auth/token/refresh/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ refresh }),
        });
        if (!resp.ok) throw new Error('refresh failed');

        const data = await resp.json();
        localStorage.setItem(ACCESS_KEY, data.access);
        if (data.refresh) localStorage.setItem(REFRESH_KEY, data.refresh);
        return data.access;
    })();

    try {
        return await refreshPromise;
    } finally {
        refreshPromise = null;
    }
}

function forceLogout() {
    localStorage.removeItem(ACCESS_KEY);
    localStorage.removeItem(REFRESH_KEY);
    window.dispatchEvent(new Event('auth:logout'));
}

export async function authFetch(url, options = {}) {
    const doRequest = (token) => {
        const headers = new Headers(options.headers || {});
        if (token) headers.set('Authorization', `Bearer ${token}`);
        return fetch(url, { ...options, headers });
    };

    let resp = await doRequest(localStorage.getItem(ACCESS_KEY));

    if (resp.status === 401) {
        if (!localStorage.getItem(REFRESH_KEY)) {
            forceLogout();
            return resp;
        }
        try {
            const newToken = await refreshAccessToken();
            resp = await doRequest(newToken);
        } catch (e) {
            forceLogout();
        }
    }
    return resp;
}

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

export async function addFavorite(instrumentId) {
    const response = await authFetch(`${API_BASE}/auth/favorites/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ instrument: instrumentId })
    });
    if (!response.ok) throw new Error('Ошибка добавления в избранное');
    return await response.json();
}

export async function removeFavorite(favoriteId) {
    const response = await authFetch(`${API_BASE}/auth/favorites/${favoriteId}/`, {
        method: 'DELETE',
    });
    if (!response.ok) throw new Error('Ошибка удаления из избранного');
}

export async function fetchFavorites() {
    const response = await authFetch(`${API_BASE}/auth/favorites/`);
    if (!response.ok) throw new Error('Ошибка загрузки избранного');
    return await response.json();
}

export async function reorderFavorites(items) {
    const response = await authFetch(`${API_BASE}/auth/favorites/reorder/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ items })
    });
    if (!response.ok) throw new Error('Ошибка сохранения порядка');
    return await response.json();
}

// Получить значения индикатора (например, RSI)
export async function fetchIndicator(symbol, timeframe, type, period, fromDate, toDate) {
    const url = `${API_BASE}/indicators/?symbol=${symbol}&timeframe=${timeframe}&type=${type}&period=${period}&from=${fromDate}&to=${toDate}`;
    const response = await fetch(url);
    if (!response.ok) throw new Error('Ошибка загрузки индикатора');
    return await response.json();
}

export async function fetchCurrentCandle(symbol, timeframe) {
    try {
        const resp = await fetch(`/api/candles/current/?symbol=${symbol}&timeframe=${timeframe}`);
        if (!resp.ok) return null;
        const c = await resp.json();
        return {
            time: toUnixSeconds(c.time),
            open: parseFloat(c.open),
            high: parseFloat(c.high),
            low: parseFloat(c.low),
            close: parseFloat(c.close),
        };
    } catch (e) {
        console.warn("Не удалось загрузить текущую свечу:", e);
        return null;
    }
}