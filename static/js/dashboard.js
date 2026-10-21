import { fetchSummary } from './api.js';
import { initAuthUI } from './auth.js';

async function initDashboard() {
    const grid = document.getElementById('cards-grid');

    try {
        const instruments = await fetchSummary();

        instruments.forEach(inst => {
            if (inst.error) return;

            const changeValue = parseFloat(inst.percent_change);
            const isPositive = changeValue >= 0;
            const colorClass = isPositive ? 'price-up' : 'price-down';
            const sign = isPositive ? '+' : '';

            const card = document.createElement('div');
            card.className = 'card';
            
            card.onclick = () => {
                window.location.href = `/chart/?symbol=${inst.code}`;
            };

            card.innerHTML = `
                <div class="card-header">
                    <span class="card-code">${inst.code}</span>
                    <span class="card-name">${inst.name}</span>
                </div>
                <div class="card-price">${parseFloat(inst.close).toFixed(5)}</div>
                <div class="card-change ${colorClass}">
                    ${sign}${changeValue.toFixed(2)}%
                </div>
            `;

            grid.appendChild(card);
        });

    } catch (error) {
        console.error("Ошибка при отрисовке дашборда:", error);
        grid.innerHTML = '<p style="color: #ef5350;">Не удалось загрузить данные.</p>';
    }
}

initDashboard();
initAuthUI();