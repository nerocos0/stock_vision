import pandas as pd

def aggregate_candles(candles, target_timeframe):
    data = [{
        'datetime': candle.datetime,
        'open': float(candle.open_price),
        'high': float(candle.high_price),
        'low': float(candle.low_price),
        'close': float(candle.close_price),
    } for candle in candles]

    df = pd.DataFrame(data)
    df.set_index('datetime', inplace=True)

    agg_rules = {
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last',
    }

    resampled = df.resample(target_timeframe).agg(agg_rules).dropna()

    result = []
    for index, row in resampled.iterrows():
        result.append({
            'datetime': index.to_pydatetime(),
            'open': row['open'],
            'high': row['high'],
            'low': row['low'],
            'close': row['close'],
        })
        
    return result