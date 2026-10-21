import { fetchInstruments, fetchCandles, addFavorite, removeFavorite, fetchFavorites } from './api.js';
import { initAuthUI } from './auth.js';

const DEFAULT_SYMBOL = 'EURUSD';
const DEFAULT_TIMEFRAME = '1h';

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

const candleSeries = chart.addCandlestickSeries({
    upColor: '#26a69a', downColor: '#ef5350', borderVisible: false,
    wickUpColor: '#26a69a', wickDownColor: '#ef5350'
});

const urlParams = new URLSearchParams(window.location.search);
const symbolFromUrl = urlParams.get('symbol');

let currentSymbol = symbolFromUrl ? symbolFromUrl : DEFAULT_SYMBOL;
let currentTimeframe = DEFAULT_TIMEFRAME;

function getDateMonthsAgo(months) {
    const date = new Date();
    date.setMonth(date.getMonth() - months);
    return date.toISOString().split('T')[0];
}

async function updateChart() {
    try {
        const now = new Date();
        const toDate = now.getFullYear() + '-' + String(now.getMonth() + 1).padStart(2, '0') + '-' + String(now.getDate()).padStart(2, '0');
        
        let fromDate;
        if (currentTimeframe === '5min') {
            fromDate = getDateMonthsAgo(1);
        } else if (currentTimeframe === '1h') {
            fromDate = getDateMonthsAgo(12);
        } else if (currentTimeframe === '4h') {
            fromDate = getDateMonthsAgo(24);
        } else {
            fromDate = getDateMonthsAgo(60);
        }

        const data = await fetchCandles(currentSymbol, currentTimeframe, fromDate, toDate);
        
        const formattedData = data.results.map(candle => ({
            time: Math.floor(new Date(candle.datetime).getTime() / 1000),
            open: parseFloat(candle.open_price),
            high: parseFloat(candle.high_price),
            low: parseFloat(candle.low_price),
            close: parseFloat(candle.close_price),
        }));

        candleSeries.setData(formattedData);
        chart.timeScale().fitContent();
    } catch (error) {
        console.error("Ошибка при обновлении графика:", error);
    }
}

async function initInstruments() {
    try {
        const data = await fetchInstruments();
        const select = document.getElementById('symbol-select');
        select.innerHTML = ''; 
        
        data.results.forEach(inst => {
            const option = document.createElement('option');
            option.value = inst.code;
            option.textContent = `${inst.code} — ${inst.name}`;
            if (inst.code === currentSymbol) option.selected = true;
            select.appendChild(option);
        });
    } catch (error) {
        console.error("Ошибка при загрузке инструментов:", error);
    }
}

function setupEventListeners() {
    document.querySelectorAll('.tf-btn').forEach(button => {
        button.addEventListener('click', (event) => {
            document.querySelectorAll('.tf-btn').forEach(btn => btn.classList.remove('active'));
            event.target.classList.add('active');

            currentTimeframe = event.target.dataset.tf;
            updateChart();
        });
    });

    document.getElementById('symbol-select').addEventListener('change', (event) => {
        currentSymbol = event.target.value;
        
        const newUrl = `${window.location.pathname}?symbol=${currentSymbol}`;
        window.history.pushState({ path: newUrl }, '', newUrl);
        
        updateChart();
        updateFavoriteButton();
    });
}

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
        const favorite = favoritesData.results.find(fav => fav.instrument_code === currentSymbol);

        if (favorite) {
            favBtn.textContent = '⭐';
            favBtn.classList.add('active');
            
            favBtn.onclick = async () => {
                try {
                    await removeFavorite(favorite.id);
                    updateFavoriteButton();
                } catch (error) {
                    console.error(error);
                }
            };
        } else {
            favBtn.textContent = '⭐';
            favBtn.classList.remove('active');
            
            favBtn.onclick = async () => {
                try {
                    await addFavorite(currentSymbol);
                    updateFavoriteButton();
                } catch (error) {
                    console.error(error);
                }
            };
        }
    } catch (error) {
        console.error("Ошибка при проверке избранного:", error);
    }
}


async function init() {
    await initInstruments();
    setupEventListeners();
    await updateChart();
    await updateFavoriteButton();
}

init();
initAuthUI();