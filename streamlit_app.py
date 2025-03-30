import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt

# Set the title and favicon
st.set_page_config(
    page_title='Stock Dashboard',
    page_icon=':chart_with_upwards_trend:',
)

# Function to fetch stock data
@st.cache_data
def get_stock_data(tickers, start_date, end_date):
    df = yf.download(tickers, start=start_date, end=end_date)
    
    if df.empty:
        st.error("Failed to fetch stock data. Please check the ticker symbols and date range.")
        return None

    # Handle multi-index columns if necessary
    if isinstance(df.columns, pd.MultiIndex):
        if 'Close' in df.columns.get_level_values(0):
            df = df['Close']
        else:
            st.error("Unexpected data format received from yfinance.")
            return None
    else:
        if 'Close' not in df.columns:
            st.error("Unexpected data format received from yfinance.")
            return None

    return df

# RSI Calculation
def calculate_rsi(data, window=14):
    delta = data.diff(1)
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    
    avg_gain = gain.rolling(window=window, min_periods=1).mean()
    avg_loss = loss.rolling(window=window, min_periods=1).mean()
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi.fillna(50)

# MACD Calculation
def calculate_macd(data, short_window=12, long_window=26, signal_window=9):
    short_ema = data.ewm(span=short_window, adjust=False).mean()
    long_ema = data.ewm(span=long_window, adjust=False).mean()
    macd = short_ema - long_ema
    signal = macd.ewm(span=signal_window, adjust=False).mean()
    return macd, signal

# UI Elements
st.title(':chart_with_upwards_trend: Stock Dashboard')

# Stock ticker input
ticker_input = st.text_input('Enter stock ticker(s) (comma-separated)', 'AAPL, MSFT')
tickers = [ticker.strip().upper() for ticker in ticker_input.split(',') if ticker.strip()]

# Date range selection
date_range = st.date_input(
    'Select date range',
    value=[pd.to_datetime('2023-01-01'), pd.to_datetime('2024-01-01')],
)

if tickers and len(date_range) == 2:
    start_date, end_date = date_range
    
    # Fetch stock data
    stock_data = get_stock_data(tickers, start_date, end_date)
    
    if stock_data is not None:
        # Display stock price trends
        st.subheader('Stock Price Trends')
        st.line_chart(stock_data)
        
        # RSI and MACD Plots
        selected_stock = st.selectbox('Select a stock for RSI & MACD', tickers)

        if selected_stock in stock_data.columns:
            stock_close = stock_data[selected_stock]

            # RSI Calculation and Plot
            rsi = calculate_rsi(stock_close)
            fig, ax = plt.subplots(figsize=(12, 4))
            ax.plot(rsi, label='RSI', color='blue')
            ax.axhline(70, linestyle='--', color='red', label='Overbought (70)')
            ax.axhline(30, linestyle='--', color='green', label='Oversold (30)')
            ax.set_title(f'RSI ({selected_stock})')
            ax.set_ylim(0, 100)
            ax.legend()
            st.pyplot(fig)

            # MACD Calculation and Plot
            macd, signal = calculate_macd(stock_close)
            fig, ax = plt.subplots(figsize=(12, 4))
            ax.plot(macd, label='MACD', color='blue')
            ax.plot(signal, label='Signal Line', color='red', linestyle='--')
            ax.axhline(0, linestyle='-', color='black')
            ax.set_title(f'MACD ({selected_stock})')
            ax.legend()
            st.pyplot(fig)

        # Display latest stock prices
        st.subheader('Latest Stock Prices')
        latest_prices = stock_data.iloc[-1].round(2)
        for ticker in tickers:
            if ticker in latest_prices:
                st.metric(label=f'{ticker} Price', value=f'${latest_prices[ticker]:,.2f}')
            else:
                st.warning(f'No data available for {ticker}')
else:
    st.warning('Please enter at least one valid stock ticker and a valid date range.')
