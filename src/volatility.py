"""
Volatility analysis module.
Calculates historical volatility and compares with implied volatility.
"""

import numpy as np
import pandas as pd


class VolatilityAnalyzer:
    """Analyzes realized vs implied volatility."""

    def __init__(self, stock_data):
        self.stock_data = stock_data
        self.returns = stock_data['Log_Returns'].dropna()

    def analyze(self):
        """Run complete volatility analysis."""
        hv = self._calculate_historical_vol()
        regime = self._determine_regime(hv['hv_21d'])

        return {
            'hv_21d': hv['hv_21d'],
            'hv_63d': hv['hv_63d'],
            'hv_252d': hv['hv_252d'],
            'hv_history': hv['history'],
            'regime': regime['label'],
            'percentile': regime['percentile'],
            'vrp': None  # Set later when IV is available
        }

    def _calculate_historical_vol(self):
        """
        Calculate rolling historical volatility.
        Uses log returns with annualization factor of sqrt(252).
        """
        windows = {'hv_21d': 21, 'hv_63d': 63, 'hv_252d': 252}
        history = pd.DataFrame()

        for name, window in windows.items():
            history[name] = self.returns.rolling(window=window).std() * np.sqrt(252)

        return {
            'hv_21d': history['hv_21d'].iloc[-1],
            'hv_63d': history['hv_63d'].iloc[-1],
            'hv_252d': history['hv_252d'].iloc[-1],
            'history': history
        }

    def _determine_regime(self, current_hv):
        """Classify current volatility regime relative to history."""
        all_hv = self.returns.rolling(window=21).std() * np.sqrt(252)
        all_hv = all_hv.dropna()

        percentile = (all_hv < current_hv).mean() * 100

        if percentile > 80:
            label = "HIGH"
        elif percentile < 20:
            label = "LOW"
        else:
            label = "NORMAL"

        return {'label': label, 'percentile': percentile}

    def set_implied_vol(self, iv):
        """Calculate volatility risk premium once IV is known."""
        self.iv = iv

    def get_vrp(self, iv, hv):
        """Volatility Risk Premium = IV - Realized Vol"""
        return iv - hv
