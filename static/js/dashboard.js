import { fetchSummary, fetchFavorites, addFavorite, removeFavorite } from './api.js';
import { initAuthUI } from './auth.js';

let isFavoriteListenerAttached = false; // Защита от бесконечных кликов

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
    const grid = document.getElementById('cards-grid');
    const stars = document.querySelectorAll('.card-fav-icon');

    // Если не авторизован - вешаем редирект (один раз)
    if (!token) {
        if (!isFavoriteListenerAttached) {
            grid.addEventListener('click', (e) => {
                if (e.target.classList.contains('card-fav-icon')) {
                    e.stopPropagation();
                    e.preventDefault();
                    window.location.href = '/auth/';
                }
            }, true); // capture phase
            isFavoriteListenerAttached = true;
        }
        return;
    }

    try {
        const favoritesData = await fetchFavorites();
        const favCodes = favoritesData.results.map(f => f.instrument_code);
        
        // Просто обновляем визуал (цвет/звездочку) - обработчики не трогаем!
        stars.forEach(star => {
            const code = star.dataset.code;
            const isFav = favCodes.includes(code);
            star.textContent = isFav ? '★' : '☆';
            star.style.color = isFav ? '#F9A825' : '#787b86';
        });

        // Вешаем ОДИН обработчик на всю сетку
        if (!isFavoriteListenerAttached) {
            grid.addEventListener('click', async (e) => {
                if (!e.target.classList.contains('card-fav-icon')) return;
                
                e.stopPropagation(); // Не открываем график
                e.preventDefault();
                
                const star = e.target;
                const code = star.dataset.code;
                const isFav = star.textContent === '★'; // Смотрим, что нарисовано сейчас

                try {
                    // ВСЕГДА получаем свежий список перед удалением
                    const freshFavData = await fetchFavorites(); 
                    
                    if (isFav) {
                        const favObj = freshFavData.results.find(f => f.instrument_code === code);
                        if (favObj) await removeFavorite(favObj.id);
                    } else {
                        await addFavorite(code);
                    }
                    
                    // После действия обновляем визуал
                    await initFavorites(); 
                    
                } catch (error) {
                    console.error("Ошибка при изменении избранного:", error);
                }
            }, true); 
            
            isFavoriteListenerAttached = true;
        }

    } catch (error) {
        console.error("Ошибка при загрузке избранного:", error);
    }
}

initDashboard();
initAuthUI();