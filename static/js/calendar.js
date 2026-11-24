import { initAuthUI } from './auth.js';
import { showToast } from './utils.js';

const tbody = document.getElementById('calendar-body');
let allEvents = [];

// ==========================================
// 1. ТАЙМЗОНА
// ==========================================
let currentTimezoneOffset = parseInt(localStorage.getItem('calendarTimezoneOffset') || '0');

// Устанавливаем значение селекта при загрузке
const timezoneSelect = document.getElementById('timezone-select');
if (timezoneSelect) {
    timezoneSelect.value = currentTimezoneOffset.toString();
    timezoneSelect.addEventListener('change', (event) => {
        currentTimezoneOffset = parseInt(event.target.value);
        localStorage.setItem('calendarTimezoneOffset', currentTimezoneOffset);
        renderEvents();  // Перерисовываем таблицу с новой таймзоной
    });
}

// ==========================================
// 2. ЗАГРУЗКА ВАЛЮТ (ДИНАМИЧЕСКИ)
// ==========================================
async function loadCurrencies() {
    try {
        const response = await fetch('/api/calendar/currencies/');
        if (!response.ok) throw new Error('Ошибка загрузки валют');
        const currencies = await response.json();
        
        const container = document.getElementById('currency-filters');
        container.innerHTML = '';
        
        currencies.forEach(currency => {
            const label = document.createElement('label');
            label.innerHTML = `<input type="checkbox" value="${currency}" checked> ${currency}`;
            container.appendChild(label);
            
            label.querySelector('input').addEventListener('change', renderEvents);
        });
    } catch (error) {
        console.error(error);
        showToast('Не удалось загрузить список валют', 'error');
    }
}

// ==========================================
// 3. ЗАГРУЗКА СОБЫТИЙ
// ==========================================
async function loadCalendar() {
    try {
        const response = await fetch('/api/calendar/');
        if (!response.ok) throw new Error('Ошибка загрузки календаря');
        allEvents = await response.json();
        
        if (!Array.isArray(allEvents) && allEvents.results) {
            allEvents = allEvents.results;
        }
        
        renderEvents();
    } catch (error) {
        console.error(error);
        showToast('Не удалось загрузить календарь', 'error');
    }
}

// ==========================================
// 4. ОТРИСОВКА СОБЫТИЙ (С ФИЛЬТРАЦИЕЙ И ТАЙМЗОНОЙ)
// ==========================================
function renderEvents() {
    tbody.innerHTML = '';

    const showHigh = document.getElementById('filter-high').checked;
    const showMedium = document.getElementById('filter-medium').checked;
    const showLow = document.getElementById('filter-low').checked;

    const currencyCheckboxes = document.querySelectorAll('#currency-filters input[type="checkbox"]');
    const selectedCurrencies = new Set();
    currencyCheckboxes.forEach(cb => {
        if (cb.checked) selectedCurrencies.add(cb.value);
    });

    const filtered = allEvents.filter(e => {
        if (e.importance === 'high' && !showHigh) return false;
        if (e.importance === 'medium' && !showMedium) return false;
        if (e.importance === 'low' && !showLow) return false;
        if (selectedCurrencies.size > 0 && !selectedCurrencies.has(e.currency)) return false;
        return true;
    });

    filtered.forEach(event => {
        const tr = document.createElement('tr');
        tr.className = `importance-${event.importance}`;

        const eventDate = new Date(event.time);
        const time = new Date(eventDate.getTime() + currentTimezoneOffset * 3600 * 1000);
        const formattedTime = time.toLocaleString('ru-RU', { 
            day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit',
            timeZone: 'UTC'
        });
        
        const formatVal = (val) => val === null ? '—' : val;
        
        const currencyIcon = {
            'USD': '🇺🇸', 'EUR': '🇪🇺', 'GBP': '🇬🇧', 'XAU': '🥇',
            'JPY': '🇯🇵', 'AUD': '🇦🇺', 'CAD': '🇨🇦', 'CHF': '🇨🇭', 'NZD': '🇳🇿',
        }[event.currency] || '🌐';
        
        tr.innerHTML = `
            <td>${formattedTime}</td>
            <td><strong>${currencyIcon} ${event.currency}</strong></td>
            <td>${event.name}</td>
            <td>${formatVal(event.actual)}</td>
            <td>${formatVal(event.forecast)}</td>
            <td>${formatVal(event.previous)}</td>
        `;
        tbody.appendChild(tr);
    });
}

// ==========================================
// 5. ОБРАБОТЧИКИ ФИЛЬТРОВ ВАЖНОСТИ
// ==========================================
['filter-high', 'filter-medium', 'filter-low'].forEach(id => {
    document.getElementById(id).addEventListener('change', renderEvents);
});

// ==========================================
// 6. ИНИЦИАЛИЗАЦИЯ
// ==========================================
async function init() {
    await loadCurrencies();
    await loadCalendar();
}

init();
initAuthUI();