import { fetchInstruments, fetchCandles } from './api.js';

// Константы
const DEFAULT_SYMBOL = 'EURUSD';
const DEFAULT_TIMEFRAME = '1h';
const DATE_FROM = '2026-09-01';
const DATE_TO = '2026-10-15';

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

let currentSymbol = DEFAULT_SYMBOL;
let currentTimeframe = DEFAULT_TIMEFRAME;

async function updateChart() {
    try {
        const data = await fetchCandles(currentSymbol, currentTimeframe, DATE_FROM, DATE_TO);
        
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
        updateChart();
    });
}


async function init() {
    await initInstruments();
    setupEventListeners();
    await updateChart();
}

init();