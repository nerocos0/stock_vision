import { fetchInstruments, fetchCandles, fetchIndicator, addFavorite, removeFavorite, fetchFavorites, fetchSummary, reorderFavorites } from './api.js';
import { initAuthUI } from './auth.js';

// ==========================================
// 1. КОНСТАНТЫ И СОСТОЯНИЕ (STATE)
// ==========================================
const DEFAULT_SYMBOL = 'EURUSD';
const DEFAULT_TIMEFRAME = '1h';

const state = {
    symbol: DEFAULT_SYMBOL,
    timeframe: DEFAULT_TIMEFRAME,
    indicators: {
        rsi: { enabled: false, period: 14 },
        ema: { enabled: false, period: 20 },
        sma: { enabled: false, period: 50 }
    }
};

const loader = document.getElementById('loader');

let currentTimezoneOffset = parseInt(localStorage.getItem('timezoneOffset') || '0');

// ==========================================
// 2. ИНИЦИАЛИЗАЦИЯ ГРАФИКА
// ==========================================
const chartContainer = document.getElementById('chart-container');
const chart = LightweightCharts.createChart(chartContainer, {
    width: chartContainer.clientWidth,
    height: chartContainer.clientHeight,
    layout: { background: { color: '#131722' }, textColor: '#d1d4dc' },
    grid: { vertLines: { color: '#2B2B43' }, horzLines: { color: '#2B2B43' } },
    timeScale: { 
        timeVisible: true,
        secondsVisible: false,
        rightOffset: 100,
        tickMarkFormatter: (time) => {
            const date = new Date((time + currentTimezoneOffset * 3600) * 1000);
            const hours = String(date.getUTCHours()).padStart(2, '0');
            const minutes = String(date.getUTCMinutes()).padStart(2, '0');
            return `${hours}:${minutes}`;
        }
    },
    localization: {
        timeFormatter: (time) => {
            const date = new Date((time + currentTimezoneOffset * 3600) * 1000);
            const days = ['вс', 'пн', 'вт', 'ср', 'чт', 'пт', 'сб'];
            const months = ['Янв', 'Фев', 'Мар', 'Апр', 'Май', 'Июн', 'Июл', 'Авг', 'Сен', 'Окт', 'Ноя', 'Дек'];
            const dayOfWeek = days[date.getUTCDay()];
            const day = String(date.getUTCDate()).padStart(2, '0');
            const month = months[date.getUTCMonth()];
            const year = String(date.getUTCFullYear()).slice(-2);
            const hours = String(date.getUTCHours()).padStart(2, '0');
            const minutes = String(date.getUTCMinutes()).padStart(2, '0');
            return `${dayOfWeek} ${day} ${month} '${year}  ${hours}:${minutes}`;
        }
    },
    crosshair: { mode: LightweightCharts.CrosshairMode.Normal },
});

// Отслеживаем изменение размеров контейнера графика (вместо window.resize)
const resizeObserver = new ResizeObserver(entries => {
    for (let entry of entries) {
        chart.applyOptions({ 
            width: entry.contentRect.width, 
            height: entry.contentRect.height 
        });
    }
});
resizeObserver.observe(chartContainer);

const candleSeries = chart.addCandlestickSeries({
    upColor: '#26a69a', downColor: '#ef5350', borderVisible: false,
    wickUpColor: '#26a69a', wickDownColor: '#ef5350'
});

const emaSeries = chart.addLineSeries({ color: '#FF9800', lineWidth: 2 });
const smaSeries = chart.addLineSeries({ color: '#2196F3', lineWidth: 2 });

const rsiSeries = chart.addLineSeries({ color: '#7E57C2', lineWidth: 2, priceScaleId: 'rsi' });
chart.priceScale('rsi').applyOptions({
    scaleMargins: { top: 0.8, bottom: 0 },
});

// ==========================================
// 3. ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
// ==========================================
function getDateRange(timeframe) {
    const now = new Date();
    const toDate = now.toISOString().split('T')[0] + ' 23:59:59';
    const date = new Date();
    let monthsToSubtract = 12;
    if (timeframe === '5min') monthsToSubtract = 1;
    else if (timeframe === '1h') monthsToSubtract = 12;
    else if (timeframe === '4h') monthsToSubtract = 24;
    else monthsToSubtract = 60;
    date.setMonth(date.getMonth() - monthsToSubtract);
    const fromDate = date.toISOString().split('T')[0];
    return { fromDate, toDate };
}

// Функция для показа уведомлений
function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    
    container.appendChild(toast);

    // Удаляем через 3 секунды
    setTimeout(() => {
        toast.classList.add('fade-out');
        // Ждем окончания анимации и удаляем
        toast.addEventListener('animationend', () => toast.remove());
    }, 3000);
}

// ==========================================
// 4. ЗАГРУЗКА И ОТРИСОВКА ДАННЫХ
// ==========================================
async function updateChart() {
    try {
        loader.classList.add('visible');
        const { fromDate, toDate } = getDateRange(state.timeframe);
        const data = await fetchCandles(state.symbol, state.timeframe, fromDate, toDate);
        const dataArray = Array.isArray(data) ? data : data.results;
        const formattedData = dataArray.map(candle => ({
            time: Math.floor(new Date(candle.datetime).getTime() / 1000),
            open: parseFloat(candle.open_price),
            high: parseFloat(candle.high_price),
            low: parseFloat(candle.low_price),
            close: parseFloat(candle.close_price),
        }));

        // Динамическая точность цен
        if (formattedData.length > 0) {
            const lastPrice = formattedData[formattedData.length - 1].close;
            let precision = 2; let minMove = 0.01;
            if (lastPrice < 10) { precision = 5; minMove = 0.00001; }
            else if (lastPrice < 100) { precision = 4; minMove = 0.0001; }
            else if (lastPrice < 1000) { precision = 3; minMove = 0.001; }
            else { precision = 2; minMove = 0.01; }
            candleSeries.applyOptions({
                priceFormat: { type: 'price', precision: precision, minMove: minMove }
            });
        }

        candleSeries.setData(formattedData);

        candleSeries.priceScale().applyOptions({
            autoScale: true,
        });

        await updateAllActiveIndicators();

        requestAnimationFrame(() => {
            const visibleBars = 150;
            const totalBars = formattedData.length;

            if (totalBars > visibleBars) {
                chart.timeScale().setVisibleLogicalRange({
                    from: totalBars - visibleBars,
                    to: totalBars + 100
                });
            } else {
                chart.timeScale().fitContent();
            }
        });
        
    } catch (error) {
        console.error("Ошибка при обновлении графика:", error);
        showToast('Ошибка загрузки графика', 'error');
    } finally {
        loader.classList.remove('visible');
    }
}

async function fetchLatestCandle() {
    try {
        const { toDate } = getDateRange(state.timeframe);
        const fromDate = toDate.split(' ')[0];
        const data = await fetchCandles(state.symbol, state.timeframe, fromDate, toDate);
        const dataArray = Array.isArray(data) ? data : data.results;
        
        if (dataArray && dataArray.length > 0) {
            const lastCandle = dataArray[dataArray.length - 1];
            const formattedCandle = {
                time: Math.floor(new Date(lastCandle.datetime).getTime() / 1000),
                open: parseFloat(lastCandle.open_price),
                high: parseFloat(lastCandle.high_price),
                low: parseFloat(lastCandle.low_price),
                close: parseFloat(lastCandle.close_price),
            };
            candleSeries.update(formattedCandle);
        }
    } catch (error) {
        console.error("Ошибка автообновления:", error);
    }
}

async function updateIndicator(type) {
    const seriesMap = { rsi: rsiSeries, ema: emaSeries, sma: smaSeries };
    const series = seriesMap[type];
    const config = state.indicators[type];

    if (!config.enabled) {
        series.setData([]);
        return;
    }

    try {
        const { fromDate, toDate } = getDateRange(state.timeframe);
        const data = await fetchIndicator(state.symbol, state.timeframe, type, config.period, fromDate, toDate);
        series.setData(data);
    } catch (error) {
        console.error(`Ошибка загрузки ${type}:`, error);
    }
}

async function updateAllActiveIndicators() {
    for (const type of ['rsi', 'ema', 'sma']) {
        await updateIndicator(type);
    }
}

// ==========================================
// 5. ИНИЦИАЛИЗАЦИЯ ИНСТРУМЕНТОВ (СЕЛЕКТ)
// ==========================================
async function initInstruments() {
    try {
        const data = await fetchInstruments();
        const select = document.getElementById('symbol-select');
        select.innerHTML = ''; 
        data.results.forEach(inst => {
            const option = document.createElement('option');
            option.value = inst.code;
            option.textContent = `${inst.code} — ${inst.name}`;
            if (inst.code === state.symbol) option.selected = true;
            select.appendChild(option);
        });
    } catch (error) {
        console.error("Ошибка при загрузке инструментов:", error);
    }
}

// ==========================================
// 6. ИЗБРАННОЕ (КНОПКА В ШАПКЕ)
// ==========================================
async function updateFavoriteButton() {
    const favBtn = document.getElementById('fav-btn');
    const token = localStorage.getItem('access_token');
    if (!token) { favBtn.style.display = 'none'; return; }
    favBtn.style.display = 'block';
    try {
        const favoritesData = await fetchFavorites();
        const favorite = favoritesData.results.find(fav => fav.instrument_code === state.symbol);
        if (favorite) {
            favBtn.textContent = 'В избранном';
            favBtn.classList.add('active');
            favBtn.onclick = async () => {
                await removeFavorite(favorite.id);
                showToast('Удалено из избранного', 'info');
                await updateFavoriteButton();
                await updateWatchlist();
            };
        } else {
            favBtn.textContent = 'В избранное';
            favBtn.classList.remove('active');
            favBtn.onclick = async () => {
                await addFavorite(state.symbol);
                showToast('Добавлено в избранное', 'success');
                await updateFavoriteButton();
                await updateWatchlist();
            };
        }
    } catch (error) {
        console.error("Ошибка при проверке избранного:", error);
    }
}

// ==========================================
// 7. WATCHLIST (СПИСОК ИЗБРАННОГО)
// ==========================================
async function updateWatchlist() {
    const container = document.getElementById('watchlist-items');
    const token = localStorage.getItem('access_token');

    if (!token) {
        container.innerHTML = '<p style="color: #787b86; font-size: 14px; padding: 10px;">Войдите, чтобы видеть избранное</p>';
        return;
    }

    try {
        const data = await fetchFavorites();
        container.innerHTML = ''; 

        if (data.results.length === 0) {
            container.innerHTML = '<p style="color: #787b86; font-size: 14px; padding: 10px;">Список пуст</p>';
            return;
        }

        const summaryData = await fetchSummary();
        const summaryMap = {};
        if (Array.isArray(summaryData)) {
            summaryData.forEach(item => { summaryMap[item.code] = item; });
        }

        data.results.forEach(fav => {
            const btn = document.createElement('div');
            btn.className = 'watchlist-item';
            btn.draggable = true;
            btn.dataset.id = fav.id;
            if (fav.instrument_code === state.symbol) btn.classList.add('active');

            const info = summaryMap[fav.instrument_code] || {};
            const price = info.close ? parseFloat(info.close).toFixed(4) : '...';
            const change = info.percent_change ? parseFloat(info.percent_change).toFixed(2) : '0.00';
            const isUp = change >= 0;

            btn.innerHTML = `
                <div class="wl-left">
                    <div class="wl-symbol">${fav.instrument_code}</div>
                    <div class="wl-price">${price}</div>
                    <div class="wl-change ${isUp ? 'up' : 'down'}">${isUp ? '+' : ''}${change}%</div>
                </div>
                <button class="wl-delete" data-id="${fav.id}">✕</button>
            `;

            // Клик по элементу (переключение графика)
            btn.onclick = (e) => {
                if (e.target.closest('.wl-delete')) return;
                state.symbol = fav.instrument_code;
                window.history.pushState({}, '', `${window.location.pathname}?symbol=${state.symbol}`);
                document.getElementById('symbol-select').value = state.symbol;
                updateChart();
                updateFavoriteButton();
                updateWatchlist();
            };

            // Удаление
            const deleteBtn = btn.querySelector('.wl-delete');
            deleteBtn.onclick = async (e) => {
                e.stopPropagation();
                await removeFavorite(fav.id);
                showToast('Инструмент удален', 'info');
                await updateWatchlist();
                await updateFavoriteButton();
            };

            // Drag-and-drop
            btn.addEventListener('dragstart', (e) => {
                e.dataTransfer.setData('text/plain', fav.id);
                e.dataTransfer.effectAllowed = 'move';
                setTimeout(() => btn.classList.add('dragging'), 0);
            });

            btn.addEventListener('dragend', () => { btn.classList.remove('dragging'); });
            btn.addEventListener('dragover', (e) => { e.preventDefault(); btn.classList.add('drag-over'); });
            btn.addEventListener('dragleave', () => { btn.classList.remove('drag-over'); });

            btn.addEventListener('drop', async (e) => {
                e.preventDefault();
                btn.classList.remove('drag-over');
                const draggedId = e.dataTransfer.getData('text/plain');
                if (draggedId === fav.id) return;

                const items = Array.from(container.children);
                const draggedIndex = items.findIndex(item => item.dataset.id === draggedId);
                const targetIndex = items.findIndex(item => item.dataset.id === fav.id);

                if (draggedIndex < targetIndex) {
                    container.insertBefore(container.children[draggedIndex], btn.nextSibling);
                } else {
                    container.insertBefore(container.children[draggedIndex], btn);
                }

                const newOrder = Array.from(container.children).map((item, index) => ({
                    id: parseInt(item.dataset.id),
                    order: index
                }));
                
                try {
                    await reorderFavorites(newOrder);
                } catch (error) {
                    console.error("Ошибка сохранения порядка:", error);
                }
            });

            container.appendChild(btn);
        });
    } catch (error) {
        console.error("Ошибка при загрузке Watchlist:", error);
        container.innerHTML = '<p style="color: #ef5350; font-size: 14px; padding: 10px;">Ошибка загрузки</p>';
    }
}

// Изменение ширины панели
function setupResizer() {
    const resizer = document.getElementById('dragMe');
    const sidebar = document.getElementById('watchlist-sidebar');
    let isResizing = false;

    resizer.addEventListener('mousedown', () => {
        isResizing = true;
        document.body.style.cursor = 'col-resize';
        document.body.style.userSelect = 'none'; 
    });

    document.addEventListener('mousemove', (e) => {
        if (!isResizing) return;
        const newWidth = document.body.clientWidth - e.clientX;
        if (newWidth > 150 && newWidth < 500) {
            sidebar.style.width = `${newWidth}px`;
            localStorage.setItem('sidebarWidth', newWidth);
        }
    });

    document.addEventListener('mouseup', () => {
        if (isResizing) {
            isResizing = false;
            document.body.style.cursor = 'default';
            document.body.style.userSelect = '';
        }
    });
}

// ==========================================
// 8. ОБРАБОТЧИКИ СОБЫТИЙ
// ==========================================
function setupEventListeners() {
    document.querySelectorAll('.tf-btn').forEach(button => {
        button.addEventListener('click', (event) => {
            document.querySelectorAll('.tf-btn').forEach(btn => btn.classList.remove('active'));
            event.target.classList.add('active');
            state.timeframe = event.target.dataset.tf;
            updateChart();
        });
    });

    document.getElementById('timezone-select').addEventListener('change', (event) => {
        currentTimezoneOffset = parseInt(event.target.value);
        localStorage.setItem('timezoneOffset', event.target.value);
        
        chart.applyOptions({
            timeScale: {
                tickMarkFormatter: (time) => {
                    const date = new Date((time + currentTimezoneOffset * 3600) * 1000);
                    const hours = String(date.getUTCHours()).padStart(2, '0');
                    const minutes = String(date.getUTCMinutes()).padStart(2, '0');
                    return `${hours}:${minutes}`;
                }
            },
            localization: {
                timeFormatter: (time) => {
                    const date = new Date((time + currentTimezoneOffset * 3600) * 1000);
                    const days = ['вс', 'пн', 'вт', 'ср', 'чт', 'пт', 'сб'];
                    const months = ['Янв', 'Фев', 'Мар', 'Апр', 'Май', 'Июн', 'Июл', 'Авг', 'Сен', 'Окт', 'Ноя', 'Дек'];
                    const dayOfWeek = days[date.getUTCDay()];
                    const day = String(date.getUTCDate()).padStart(2, '0');
                    const month = months[date.getUTCMonth()];
                    const year = String(date.getUTCFullYear()).slice(-2);
                    const hours = String(date.getUTCHours()).padStart(2, '0');
                    const minutes = String(date.getUTCMinutes()).padStart(2, '0');
                    return `${dayOfWeek} ${day} ${month} '${year}  ${hours}:${minutes}`;
                }
            }
        });
        chart.applyOptions({});
    });

    document.getElementById('symbol-select').addEventListener('change', (event) => {
        state.symbol = event.target.value;
        window.history.pushState({}, '', `${window.location.pathname}?symbol=${state.symbol}`);
        updateChart();
        updateFavoriteButton();
        updateWatchlist();
    });

    document.getElementById('export-btn').addEventListener('click', () => {
        const { fromDate, toDate } = getDateRange(state.timeframe);
        const url = `/api/candles/export/?symbol=${state.symbol}&timeframe=${state.timeframe}&from=${fromDate}&to=${toDate}`;
        
        const link = document.createElement('a');
        link.href = url;
        link.setAttribute('download', '');
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        
        showToast('Начинается скачивание CSV...', 'info');
    });

    const dropBtn = document.getElementById('indicator-btn');
    const dropMenu = document.querySelector('.indicator-dropdown');
    
    dropBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        dropMenu.classList.toggle('open');
    });
    
    document.addEventListener('click', (e) => {
        if (!dropMenu.contains(e.target)) dropMenu.classList.remove('open');
    });

    ['rsi', 'ema', 'sma'].forEach(type => {
        const checkbox = document.getElementById(`chk-${type}`);
        const periodInput = document.getElementById(`period-${type}`);

        checkbox.addEventListener('change', (e) => {
            state.indicators[type].enabled = e.target.checked;
            saveIndicatorSettings();
            updateIndicator(type);
        });

        periodInput.addEventListener('change', (e) => {
            let val = parseInt(e.target.value);
            if (isNaN(val) || val < 2) val = 2;
            if (val > 200) val = 200;
            e.target.value = val;
            
            state.indicators[type].period = val;
            saveIndicatorSettings();
            
            if (state.indicators[type].enabled) {
                updateIndicator(type);
            }
        });
    });
}

function saveIndicatorSettings() {
    localStorage.setItem('indicatorSettings', JSON.stringify(state.indicators));
}

// ==========================================
// 9. ТОЧКА ВХОДА
// ==========================================
async function init() {
    const savedIndicators = localStorage.getItem('indicatorSettings');
    if (savedIndicators) {
        try {
            const parsed = JSON.parse(savedIndicators);
            for (const type in parsed) {
                if (state.indicators[type]) {
                    state.indicators[type].enabled = parsed[type].enabled;
                    state.indicators[type].period = parsed[type].period;

                    const checkbox = document.getElementById(`chk-${type}`);
                    const periodInput = document.getElementById(`period-${type}`);
                    if (checkbox) checkbox.checked = parsed[type].enabled;
                    if (periodInput) periodInput.value = parsed[type].period;
                }
            }
        } catch (e) {
            console.error("Ошибка парсинга настроек индикаторов", e);
        }
    }
    
    const urlParams = new URLSearchParams(window.location.search);
    const symbolFromUrl = urlParams.get('symbol');
    if (symbolFromUrl) state.symbol = symbolFromUrl;
    
    const savedOffset = localStorage.getItem('timezoneOffset');
    if (savedOffset) {
        currentTimezoneOffset = parseInt(savedOffset);
        document.getElementById('timezone-select').value = savedOffset;
    }

    const savedWidth = localStorage.getItem('sidebarWidth');
    if (savedWidth) document.getElementById('watchlist-sidebar').style.width = `${savedWidth}px`;

    await initInstruments();
    setupEventListeners();
    await updateChart();
    await updateFavoriteButton();
    await updateWatchlist();
    setupResizer();
    
    setInterval(() => {
        fetchLatestCandle();
    }, 30000);
}

init();
initAuthUI();