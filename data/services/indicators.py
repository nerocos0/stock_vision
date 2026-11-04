import pandas as pd
import numpy as np

"""Нужно понять, что period - это не количество свечей которые нужно закинуть в индикатор для подсчета,
   количество свечей, а точнее их список, мы закидываем в prices,
   а период это такое количесвто свечей, которое будет влиять на следующую свечу.
   Например, даны 100 свечей и период = 14 для RSI, это значит что каждая следующая свеча начиная с первой в списке будет зависеть от 14 предыдущих,
   то есть например чтобы посчитать значение RSI для 35 свечи, нужно просканировать предыдущие 14 свечей, то есть от 20 до 34, и на основе этого посчитать 35 свечу"""


def calculate_sma(prices, period):
    """SMA(скользящая средняя) это индикатор, который жестко считает среднюю цену актива за определенный период времени. для подсчета нужно минимум period свечей"""
    sma = pd.Series(prices).rolling(window=period).mean()
    return sma.where(pd.notnull(sma), None)


def calculate_ema(prices, period):
    """EMA(экспоненциальная скользящая средняя) это индикатор, считающий среднюю цену актива за определенный период времени, придавая больший вес последним (свежим) ценам"""
    ema = pd.Series(prices).ewm(span=period, adjust=False).mean()
    return ema.where(pd.notnull(ema), None)


def calculate_rsi(prices, period):
    """RSI(Индекс относительной силы) это осциллятор, который измеряет скорость и силу изменения цены актива(0-100%)"""
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

def calculate_macd(prices, period=None):
    ema_fast = calculate_ema(prices, 12)
    ema_slow = calculate_ema(prices, 26)

    macd_line = ema_fast - ema_slow

    return macd_line