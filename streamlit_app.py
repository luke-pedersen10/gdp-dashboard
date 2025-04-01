import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors  
import seaborn as sns

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

#Moneyflow calculation
def calculate_money_flow(data,tickers, period='5d', interval='1d'):
    results = []
    
    # Loop over each ticker to process its data individually
    for ticker in tickers:
        if isinstance(data.columns, pd.MultiIndex):
            ticker_data = data.xs(ticker, axis=1, level=1)
        else:
            ticker_data = data.copy()
        
        # Verify required columns exist
        required_columns = ['High', 'Low', 'Close', 'Volume']
        for col in required_columns:
            if col not in ticker_data.columns:
                raise KeyError(f"Missing expected column: {col} for ticker: {ticker}")
        
        # Calculate Typical Price
        ticker_data['Typical Price'] = (ticker_data['High'] + ticker_data['Low'] + ticker_data['Close']) / 3
        
        # Calculate Money Flow
        ticker_data['Money Flow'] = ticker_data['Typical Price'] * ticker_data['Volume']
        
        # Add the ticker as a column for identification
        ticker_data['Ticker'] = ticker
        
        # Append the results for this ticker 
        results.append(ticker_data[['Ticker', 'Money Flow']].reset_index())
    
    # Combine all individual ticker results into one DataFrame
    result_df = pd.concat(results, ignore_index=True)
    return result_df


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

# Input fields for user interaction
st.write("### Search Financial Data")
search_term = ticker_input
max_results = st.slider("Maximum results to fetch:", 1, 20, 10)

if search_term:
    # Fetch news
    st.write(f"**Fetching news for:** {search_term}")
    news = yf.Search(search_term, news_count=max_results).news
    if news:
        st.write("### News:")
        for article in news:
            st.write(f"- [{article.get('title', 'No title')}](article.get('link', '#'))")
    else:
        st.write("No news found.")

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
            moneyflow_tickers = tickers

            st.title("Stock Market Sector Performance")

            # Dictionary of S&P 500 sectors and their corresponding ETFs
            sectors = {
                "Technology (XLK)": "XLK",
                "Energy (XLE)": "XLE",
                "Health Care (XLV)": "XLV",
                "Financials (XLF)": "XLF",
                "Consumer Discretionary (XLY)": "XLY",
                "Consumer Staples (XLP)": "XLP",
                "Industrials (XLI)": "XLI",
                "Utilities (XLU)": "XLU",
                "Materials (XLB)": "XLB",
                "Real Estate (XLRE)": "XLRE",
                "Communication Services (XLC)": "XLC",
            }

            # Create checkboxes 
            selected_sectors = {sector: st.checkbox(sector) for sector in sectors.keys()}

            # Function to fetch the latest closing price
            def get_closing_price(ticker):
                stock = yf.Ticker(ticker)
                data = stock.history(period="1d")  # Get the latest daily data
                return data["Close"].iloc[-1] if not data.empty else "No data available"

            # Display sector closing prices
            st.write("### Stock and Sector Money Flow:")
            for sector, is_selected in selected_sectors.items():
                if is_selected:
                     moneyflow_tickers.append(sectors[sector])









            df2 = yf.download(tickers, period='5d', interval='1d')
            moneyflow_data = calculate_money_flow(df2, moneyflow_tickers)
            heatmap_data = moneyflow_data.pivot(index='Date', columns='Ticker', values='Money Flow')
            # Create the heatmap figure
            fig, ax = plt.subplots(figsize=(10, 6))
            sns.heatmap(heatmap_data, cmap='coolwarm', norm=mcolors.LogNorm(), ax=ax)

            # Add title and format labels
            ax.set_title("Stock Money Flow Heat Map")
            plt.xticks(rotation=45)

            # Display in Streamlit
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
