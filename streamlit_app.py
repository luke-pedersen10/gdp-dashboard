import streamlit as st
import yfinance as yf
import pandas as pd

# Set the title and favicon
st.set_page_config(
    page_title='Stock Dashboard',
    page_icon=':chart_with_upwards_trend:',
)

# Function to fetch stock data
@st.cache_data
def get_stock_data(tickers, start_date, end_date):
    df = yf.download(tickers, start=start_date, end=end_date)
    
    # Debugging: Print the raw DataFrame
    st.write("Raw yfinance Data:", df.head())

    if df.empty:
        st.error("Failed to fetch stock data. Please check the ticker symbols and date range.")
        return None

    # If 'Adj Close' is missing, print the columns for debugging
    if 'Adj Close' not in df.columns:
        st.write("Unexpected data format. Columns received:", df.columns)
        st.error("Unexpected data format received from yfinance.")
        return None

    return df['Adj Close']

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
