"""
Data loading utilities for stock and options data.
"""

import pandas as pd
import numpy as np
from datetime import datetime


class DataLoader:
    """Handles loading and preprocessing of market data."""

    def __init__(self, config):
        self.config = config
        self.data_dir = config.DATA_DIR

    def load_all(self):
        """Load all required data files."""
        stock_data = self._load_stock_data()
        call_chain = self._load_option_chain()
        put_chain = self._load_put_chain()
        metadata = self._load_metadata()
        return stock_data, call_chain, put_chain, metadata

    def _load_stock_data(self):
        """Load historical stock price data."""
        filepath = self.data_dir / f"{self.config.TICKER}_historical.csv"
        df = pd.read_csv(filepath, index_col=0, parse_dates=True)
        return df

    def _load_option_chain(self):
        """Load call option chain data."""
        filepath = self.data_dir / f"{self.config.TICKER}_calls.csv"
        df = pd.read_csv(filepath)
        return df

    def _load_put_chain(self):
        """Load put option chain data."""
        filepath = self.data_dir / f"{self.config.TICKER}_puts.csv"
        df = pd.read_csv(filepath)
        return df

    def _load_metadata(self):
        """Load analysis metadata."""
        filepath = self.data_dir / f"{self.config.TICKER}_metadata.csv"
        df = pd.read_csv(filepath)

        expiry_str = df['expiration'].iloc[0]
        expiry_date = datetime.strptime(expiry_str, '%Y-%m-%d')
        dte = (expiry_date - datetime.now()).days

        return {
            'ticker': df['ticker'].iloc[0],
            'expiration': expiry_str,
            'dte': dte,
            'risk_free_rate': df['risk_free_rate'].iloc[0],
            'current_price': df['current_price'].iloc[0],
            'data_date': df['data_end_date'].iloc[0]
        }

    def select_option(self, chain, current_price):
        """
        Select optimal call option contract based on:
        - Moneyness (prefer ~10% OTM)
        - Liquidity (high open interest)
        - Tight bid-ask spread
        """
        # Filter for OTM calls
        otm = chain[chain['strike'] > current_price].copy()

        # Calculate moneyness
        otm['pct_otm'] = (otm['strike'] - current_price) / current_price * 100
        return self._filter_and_score(otm)

    def select_put_option(self, chain, current_price):
        """
        Select optimal put option contract.
        """
        # Filter for OTM puts (Strike < Current Price)
        otm = chain[chain['strike'] < current_price].copy()

        # Calculate moneyness (positive for OTM)
        otm['pct_otm'] = (current_price - otm['strike']) / current_price * 100
        return self._filter_and_score(otm)

    def _filter_and_score(self, otm):
        """Common filtering and scoring logic."""
        # Apply filters
        filtered = otm[
            (otm['pct_otm'] >= self.config.MIN_OTM_PCT) &
            (otm['pct_otm'] <= self.config.MAX_OTM_PCT) &
            (otm['openInterest'] > self.config.MIN_OPEN_INTEREST)
        ].copy()

        if filtered.empty:
            filtered = otm[otm['openInterest'] > 50].copy()

        # Calculate spread
        filtered['spread'] = filtered['ask'] - filtered['bid']
        filtered['spread_pct'] = filtered['spread'] / filtered['lastPrice'] * 100

        # Score based on proximity to target OTM and liquidity
        target = self.config.TARGET_OTM_PCT
        filtered['score'] = (
            -abs(filtered['pct_otm'] - target) * 2 +
            np.log1p(filtered['openInterest']) * 1.5 -
            filtered['spread_pct'] * 0.5
        )

        if filtered.empty:
             # Fallback if no options match strict criteria
             # Just return the one with highest Open Interest that is somewhat OTM
             return None

        # Select best option
        best = filtered.loc[filtered['score'].idxmax()]

        return {
            'contract': best['contractSymbol'],
            'strike': best['strike'],
            'last_price': best['lastPrice'],
            'bid': best['bid'],
            'ask': best['ask'],
            'mid_price': (best['bid'] + best['ask']) / 2,
            'open_interest': int(best['openInterest']),
            'volume': int(best['volume']),
            'implied_volatility': best['impliedVolatility'],
            'pct_otm': best['pct_otm']
        }
