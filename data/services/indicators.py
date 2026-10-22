import pandas as pd
import numpy as np


"""SMA(скользящая средняя) это индикатор, который жестко считает среднюю цену актива за определенный период времени. для подсчета нужно минимум period свечей"""
def calculate_sma(prices, period):
    return pd.Series(prices).rolling(window=period).mean()


"""EMA(экспоненциальная скользящая средняя) это индикатор, считающий среднюю цену актива за определенный период времени, придавая больший вес последним (свежим) ценам"""
def calculate_ema(prices, period):
    return pd.Series(prices).ewm(span=period, adjust=False).mean()


"""RSI(Индекс относительной силы) это осциллятор, который измеряет скорость и силу изменения цены актива(0-100%)"""
def calculate_rsi(prices, period):
    df = pd.Series(prices)
    delta = df.diff()

    gain = pd.Series(np.where(delta > 0, delta, 0))
    loss = pd.Series(np.where(delta < 0, -delta, 0))

    avg_gain = gain.ewm(alpha=1/period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/period, adjust=False).mean()

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))

    return rsi