import { initAuthUI } from './auth.js';
import { showToast } from './utils.js';

const tbody = document.getElementById('calendar-body');
let allEvents = [];

async function loadCalendar() {
    try {
        const response = await fetch('/api/calendar/'); // Убедись, что URL правильный
        if (!response.ok) throw new Error('Ошибка загрузки календаря');
        allEvents = await response.json();
        renderEvents();
    } catch (error) {
        console.error(error);
        showToast('Не удалось загрузить календарь', 'error');
    }
}

function renderEvents() {
    tbody.innerHTML = '';
    
    const showHigh = document.getElementById('filter-high').checked;
    const showMedium = document.getElementById('filter-medium').checked;
    const showLow = document.getElementById('filter-low').checked;

    const filtered = allEvents.filter(e => {
        if (e.importance === 'high' && !showHigh) return false;
        if (e.importance === 'medium' && !showMedium) return false;
        if (e.importance === 'low' && !showLow) return false;
        return true;
    });

    filtered.forEach(event => {
        const tr = document.createElement('tr');
        tr.className = `importance-${event.importance}`;
        
        const time = new Date(event.time).toLocaleString('ru-RU', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' });
        
        // Форматируем числа (просто для красоты)
        const formatVal = (val) => val === null ? '—' : val;

        tr.innerHTML = `
            <td>${time}</td>
            <td><strong>${event.currency}</strong></td>
            <td>${event.name}</td>
            <td>${formatVal(event.actual)}</td>
            <td>${formatVal(event.forecast)}</td>
            <td>${formatVal(event.previous)}</td>
        `;
        tbody.appendChild(tr);
    });
}

// Вешаем обработчики на фильтры
document.getElementById('filter-high').addEventListener('change', renderEvents);
document.getElementById('filter-medium').addEventListener('change', renderEvents);
document.getElementById('filter-low').addEventListener('change', renderEvents);

loadCalendar();
initAuthUI();