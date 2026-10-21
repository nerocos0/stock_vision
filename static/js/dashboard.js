import { fetchSummary, fetchFavorites, addFavorite, removeFavorite } from './api.js';
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
                    <!-- Звёздочка для избранного -->
                    <span class="card-fav-icon" data-code="${inst.code}" style="cursor: pointer; font-size: 18px; color: #787b86;">☆</span>
                </div>
                <div class="card-price">${parseFloat(inst.close).toFixed(5)}</div>
                <div class="card-change ${colorClass}">
                    ${sign}${changeValue.toFixed(2)}%
                </div>
            `;

            grid.appendChild(card);
        });

        await initFavorites();

    } catch (error) {
        console.error("Ошибка при отрисовке дашборда:", error);
        grid.innerHTML = '<p style="color: #ef5350;">Не удалось загрузить данные.</p>';
    }
}

async function initFavorites() {
    const token = localStorage.getItem('access_token');
    if (!token) return;

    try {
        const favoritesData = await fetchFavorites();
        const favCodes = favoritesData.results.map(f => f.instrument_code);
        
        document.querySelectorAll('.card-fav-icon').forEach(star => {
            const code = star.dataset.code;
            
            const isFav = favCodes.includes(code);

            if (isFav) {
                star.textContent = '★';
                star.style.color = '#F9A825';
            } else {
                star.textContent = '☆';
                star.style.color = '#787b86';
            }

            star.addEventListener('click', async (e) => {
                e.stopPropagation();

                try {
                    if (isFav) {
                        const favObj = favoritesData.results.find(f => f.instrument_code === code);
                        await removeFavorite(favObj.id);
                    } else {
                        await addFavorite(code);
                    }
                    
                    await initFavorites(); 
                    
                } catch (error) {
                    console.error("Ошибка при изменении избранного:", error);
                }
            });
        });
    } catch (error) {
        console.error("Ошибка при загрузке избранного:", error);
    }
}

initDashboard();
initAuthUI();