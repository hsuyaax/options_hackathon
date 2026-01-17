import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Configuration
TICKER = "NVDA"  # Our selected stock
END_DATE = datetime.now()
START_DATE = END_DATE - timedelta(days=365)

def fetch_stock_data(ticker, start, end):
    """Fetch historical stock data"""
    stock = yf.Ticker(ticker)
    hist = stock.history(start=start, end=end)
    
    # Calculate daily returns
    hist['Returns'] = hist['Close'].pct_change()
    hist['Log_Returns'] = np.log(hist['Close'] / hist['Close'].shift(1))
    
    return hist

def fetch_option_chain(ticker):
    """Fetch current option chain"""
    stock = yf.Ticker(ticker)
    
    # Get available expiration dates
    expirations = stock.options
    print(f"Available expirations: {expirations[:5]}...")  # Show first 5
    
    # Select expiration ~30-45 days out
    target_dte = 35
    today = datetime.now()
    
    best_exp = None
    min_diff = float('inf')
    for exp in expirations:
        exp_date = datetime.strptime(exp, '%Y-%m-%d')
        diff = abs((exp_date - today).days - target_dte)
        if diff < min_diff:
            min_diff = diff
            best_exp = exp
    
    print(f"Selected expiration: {best_exp} ({min_diff + target_dte} DTE)")
    
    # Fetch option chain for selected expiration
    opt_chain = stock.option_chain(best_exp)
    calls = opt_chain.calls
    puts = opt_chain.puts
    
    return calls, puts, best_exp

def get_risk_free_rate():
    """Fetch current 3-month Treasury yield as risk-free rate"""
    try:
        tbill = yf.Ticker("^IRX")
        rate = tbill.history(period="1d")['Close'].iloc[-1] / 100
        return rate
    except:
        return 0.045  # Fallback to 4.5%

if __name__ == "__main__":
    # Fetch stock data
    print(f"Fetching {TICKER} data...")
    stock_data = fetch_stock_data(TICKER, START_DATE, END_DATE)
    stock_data.to_csv(f"data/{TICKER}_historical.csv")
    print(f"Saved {len(stock_data)} days of data")
    
    # Fetch option chain
    print(f"\nFetching {TICKER} option chain...")
    calls, puts, expiration = fetch_option_chain(TICKER)
    calls.to_csv(f"data/{TICKER}_calls.csv")
    puts.to_csv(f"data/{TICKER}_puts.csv")
    print(f"Saved {len(calls)} calls and {len(puts)} puts")
    
    # Get risk-free rate
    rf_rate = get_risk_free_rate()
    print(f"\nRisk-free rate: {rf_rate:.4f} ({rf_rate*100:.2f}%)")
    
    # Save metadata
    metadata = {
        'ticker': TICKER,
        'expiration': expiration,
        'risk_free_rate': rf_rate,
        'current_price': stock_data['Close'].iloc[-1],
        'data_end_date': END_DATE.strftime('%Y-%m-%d')
    }
    pd.DataFrame([metadata]).to_csv(f"data/{TICKER}_metadata.csv", index=False)
    print(f"\nMetadata saved. Current price: ${metadata['current_price']:.2f}")