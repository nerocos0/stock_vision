import pandas as pd
import numpy as np

"""Нужно понять, что period - это не количество свечей которые нужно закинуть в индикатор для подсчета,
   количество свечей, а точнее их список, мы закидываем в prices,
   а период это такое количесвто свечей, которое будет влиять на следующую свечу.
   Например, даны 100 свечей и период = 14 для RSI, это значит что каждая следующая свеча начиная с первой в списке будет зависеть от 14 предыдущих,
   то есть например чтобы посчитать значение RSI для 35 свечи, нужно просканировать предыдущие 14 свечей, то есть от 20 до 34, и на основе этого посчитать 35 свечу"""


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

    rsi = rsi.replace([np.inf, -np.inf], 100) 
    rsi = rsi.fillna(50)
    
    return rsi