from flask import Flask, render_template, request
import yfinance as yf
import mplfinance as mpf
import pandas as pd
import ta
import io
import base64
import matplotlib.pyplot as plt

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        ticker = request.form['ticker']
        period = request.form['period']
        interval = request.form['interval']

        # Download data
        data = yf.download(ticker, period=period, interval=interval)
        
        # Ensure the index is a DatetimeIndex
        data.index = pd.to_datetime(data.index)

        # Plot candlestick chart
        fig, (ax, ax_volume) = plt.subplots(2, figsize=(10, 8), sharex=True, gridspec_kw={'height_ratios': [3, 1]})
        mpf.plot(data, type='candle', style='charles', ax=ax, volume=ax_volume)
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        chart_data = base64.b64encode(buf.getvalue()).decode('utf-8')
        plt.close(fig)

        # Calculate indicators
        data['rsi'] = ta.momentum.RSIIndicator(data['Close']).rsi()
        data['macd'], data['macd_signal'], data['macd_diff'] = ta.trend.MACD(data['Close']).macd(), ta.trend.MACD(data['Close']).macd_signal(), ta.trend.MACD(data['Close']).macd_diff()
        data['stoch_k'], data['stoch_d'] = ta.momentum.StochasticOscillator(data['High'], data['Low'], data['Close']).stoch(), ta.momentum.StochasticOscillator(data['High'], data['Low'], data['Close']).stoch_signal()
        data['adx'] = ta.trend.ADXIndicator(data['High'], data['Low'], data['Close']).adx()
        data['cci'] = ta.trend.CCIIndicator(data['High'], data['Low'], data['Close']).cci()
        data['roc'] = ta.momentum.ROCIndicator(data['Close']).roc()
        data['williamsr'] = ta.momentum.WilliamsRIndicator(data['High'], data['Low'], data['Close']).williams_r()
        data['bbands_upper'], data['bbands_middle'], data['bbands_lower'] = ta.volatility.BollingerBands(data['Close']).bollinger_hband(), ta.volatility.BollingerBands(data['Close']).bollinger_mavg(), ta.volatility.BollingerBands(data['Close']).bollinger_lband()
        data['psar'] = ta.trend.PSARIndicator(data['High'], data['Low'], data['Close']).psar()
        data['ema'] = ta.trend.EMAIndicator(data['Close'], window=20).ema_indicator()

        # Calculate signals
        buy_counts = []
        sell_counts = []
        neutral_counts = []
        for index, row in data.iterrows():
            buy = 0
            sell = 0
            neutral = 0
            if row['rsi'] < 30:
                buy += 1
            elif row['rsi'] > 70:
                sell += 1
            else:
                neutral += 1
            if row['macd'] > row['macd_signal']:
                buy += 1
            elif row['macd'] < row['macd_signal']:
                sell += 1
            else:
                neutral += 1
            if row['stoch_k'] < 20:
                buy += 1
            elif row['stoch_k'] > 80:
                sell += 1
            else:
                neutral += 1
            if row['adx'] > 25:
                neutral += 1
            if row['cci'] < -100:
                buy += 1
            elif row['cci'] > 100:
                sell += 1
            else:
                neutral += 1
            if row['roc'] > 0:
                buy += 1
            elif row['roc'] < 0:
                sell += 1
            else:
                neutral += 1
            if row['williamsr'] < -80:
                buy += 1
            elif row['williamsr'] > -20:
                sell += 1
            else:
                neutral += 1
            if row['Close'] < row['bbands_lower']:
                buy += 1
            elif row['Close'] > row['bbands_upper']:
                sell += 1
            else:
                neutral += 1
            if row['Close'] > row['psar']:
                buy += 1
            elif row['Close'] < row['psar']:
                sell += 1
            else:
                neutral += 1
            if row['Close'] > row['ema']:
                buy += 1
            elif row['Close'] < row['ema']:
                sell += 1
            else:
                neutral += 1
            buy_counts.append(buy)
            sell_counts.append(sell)
            neutral_counts.append(neutral)
        
        results = pd.DataFrame({
            'datetime': data.index,
            'closing price': data['Close'],
            'Buy': buy_counts,
            'Sell': sell_counts,
            'Neutral': neutral_counts
        })

        return render_template('index.html', chart_data=chart_data, tables=[results.to_html(classes='data', index=False)])

    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
