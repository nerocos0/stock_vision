import { fetchInstruments, fetchCandles, fetchIndicator, addFavorite, removeFavorite, fetchFavorites } from './api.js';
import { initAuthUI } from './auth.js';

// ==========================================
// 1. КОНСТАНТЫ И СОСТОЯНИЕ (STATE)
// ==========================================
const DEFAULT_SYMBOL = 'EURUSD';
const DEFAULT_TIMEFRAME = '1h';

// Единое состояние приложения
const state = {
    symbol: DEFAULT_SYMBOL,
    timeframe: DEFAULT_TIMEFRAME,
    activeIndicators: new Set(), // Храним включенные индикаторы (rsi, ema, sma)
};

// Настройки периодов для индикаторов
const INDICATOR_PERIODS = {
    rsi: 14,
    ema: 20,
    sma: 50
};

// ==========================================
// 2. ИНИЦИАЛИЗАЦИЯ ГРАФИКА
// ==========================================
const chartContainer = document.getElementById('chart-container');
const chart = LightweightCharts.createChart(chartContainer, {
    width: chartContainer.clientWidth,
    height: chartContainer.clientHeight,
    layout: { background: { color: '#131722' }, textColor: '#d1d4dc' },
    grid: { vertLines: { color: '#2B2B43' }, horzLines: { color: '#2B2B43' } },
    timeScale: { timeVisible: true, secondsVisible: false },
    crosshair: { mode: LightweightCharts.CrosshairMode.Normal },
});

window.addEventListener('resize', () => {
    chart.applyOptions({ 
        width: chartContainer.clientWidth, 
        height: chartContainer.clientHeight 
    });
});

// Создаем серии (графики)
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
    const toDate = now.toISOString().split('T')[0];
    const date = new Date();
    
    let monthsToSubtract = 12; // Дефолт
    if (timeframe === '5min') monthsToSubtract = 1;
    else if (timeframe === '1h') monthsToSubtract = 12;
    else if (timeframe === '4h') monthsToSubtract = 24;
    else monthsToSubtract = 60;

    date.setMonth(date.getMonth() - monthsToSubtract);
    const fromDate = date.toISOString().split('T')[0];
    
    return { fromDate, toDate };
}

// ==========================================
// 4. ЗАГРУЗКА И ОТРИСОВКА ДАННЫХ
// ==========================================
async function updateChart() {
    try {
        const { fromDate, toDate } = getDateRange(state.timeframe);
        const data = await fetchCandles(state.symbol, state.timeframe, fromDate, toDate);
        
        const formattedData = data.results.map(candle => ({
            time: Math.floor(new Date(candle.datetime).getTime() / 1000),
            open: parseFloat(candle.open_price),
            high: parseFloat(candle.high_price),
            low: parseFloat(candle.low_price),
            close: parseFloat(candle.close_price),
        }));

        candleSeries.setData(formattedData);
        
        // ВАЖНО: Сначала ждем загрузки всех индикаторов
        await updateAllActiveIndicators();
        
        // И ТОЛЬКО ПОТОМ делаем автомасштаб (fitContent)
        // Даем браузеру микросекунду отрисовать данные
        setTimeout(() => chart.timeScale().fitContent(), 10);
        
    } catch (error) {
        console.error("Ошибка при обновлении графика:", error);
    }
}

async function updateIndicator(type) {
    const seriesMap = { rsi: rsiSeries, ema: emaSeries, sma: smaSeries };
    const series = seriesMap[type];
    const period = INDICATOR_PERIODS[type];
    
    if (!state.activeIndicators.has(type)) {
        series.setData([]); // Очищаем, если выключен
        return;
    }

    try {
        const { fromDate, toDate } = getDateRange(state.timeframe);
        const data = await fetchIndicator(state.symbol, state.timeframe, type, period, fromDate, toDate);
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

    if (!token) {
        favBtn.style.display = 'none';
        return;
    }

    favBtn.style.display = 'block';

    try {
        const favoritesData = await fetchFavorites();
        const favorite = favoritesData.results.find(fav => fav.instrument_code === state.symbol);

        if (favorite) {
            favBtn.textContent = '⭐ В избранном';
            favBtn.classList.add('active');
            favBtn.onclick = async () => {
                await removeFavorite(favorite.id);
                await updateFavoriteButton();
            };
        } else {
            favBtn.textContent = '⭐ В избранное';
            favBtn.classList.remove('active');
            favBtn.onclick = async () => {
                await addFavorite(state.symbol);
                await updateFavoriteButton();
            };
        }
    } catch (error) {
        console.error("Ошибка при проверке избранного:", error);
    }
}

// ==========================================
// 7. ОБРАБОТЧИКИ СОБЫТИЙ
// ==========================================
function setupEventListeners() {
    // Переключение ТФ
    document.querySelectorAll('.tf-btn').forEach(button => {
        button.addEventListener('click', (event) => {
            document.querySelectorAll('.tf-btn').forEach(btn => btn.classList.remove('active'));
            event.target.classList.add('active');

            state.timeframe = event.target.dataset.tf;
            updateChart();
        });
    });

    // Смена инструмента
    document.getElementById('symbol-select').addEventListener('change', (event) => {
        state.symbol = event.target.value;
        window.history.pushState({}, '', `${window.location.pathname}?symbol=${state.symbol}`);
        
        updateChart();
        updateFavoriteButton();
    });

    // Открытие/закрытие меню индикаторов
    const dropBtn = document.getElementById('indicator-btn');
    const dropMenu = document.querySelector('.indicator-dropdown');
    
    dropBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        dropMenu.classList.toggle('open');
    });
    
    document.addEventListener('click', (e) => {
        if (!dropMenu.contains(e.target)) dropMenu.classList.remove('open');
    });

    // Чекбоксы индикаторов
    ['rsi', 'ema', 'sma'].forEach(type => {
        document.getElementById(`chk-${type}`).addEventListener('change', (e) => {
            if (e.target.checked) {
                state.activeIndicators.add(type);
            } else {
                state.activeIndicators.delete(type);
            }
            updateIndicator(type);
        });
    });
}

// ==========================================
// 8. ТОЧКА ВХОДА
// ==========================================
async function init() {
    // Берем символ из URL, если он там есть
    const urlParams = new URLSearchParams(window.location.search);
    const symbolFromUrl = urlParams.get('symbol');
    if (symbolFromUrl) state.symbol = symbolFromUrl;

    await initInstruments();
    setupEventListeners();
    await updateChart();
    await updateFavoriteButton();
}

init();
initAuthUI();