"""
Scenario analysis engine.
Simulates P&L under various market conditions.
"""

import math


def norm_cdf(x):
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


class ScenarioEngine:
    """
    Runs scenario analysis for option positions.

    Scenarios include:
    - Bull/bear market moves
    - Volatility spikes and crushes
    - Pure time decay
    """

    def __init__(self, pricer, market_price, num_contracts):
        self.S = pricer.S
        self.K = pricer.K
        self.T = pricer.T
        self.r = pricer.r
        self.sigma = pricer.sigma_iv
        self.market_price = market_price
        self.num_contracts = num_contracts

    def run(self):
        """Execute all scenarios and return results."""
        scenarios = [
            {'name': 'Bull Rally', 'stock_chg': 0.15, 'vol_chg': -0.05, 'days': 7},
            {'name': 'Moderate Up', 'stock_chg': 0.05, 'vol_chg': 0.0, 'days': 7},
            {'name': 'Flat', 'stock_chg': 0.0, 'vol_chg': 0.0, 'days': 7},
            {'name': 'Moderate Down', 'stock_chg': -0.05, 'vol_chg': 0.05, 'days': 7},
            {'name': 'Crash', 'stock_chg': -0.15, 'vol_chg': 0.20, 'days': 7},
            {'name': 'Vol Spike', 'stock_chg': 0.0, 'vol_chg': 0.10, 'days': 7},
            {'name': 'Vol Crush', 'stock_chg': 0.0, 'vol_chg': -0.10, 'days': 7},
        ]

        results = []
        for s in scenarios:
            pnl = self._calculate_scenario_pnl(
                s['stock_chg'], s['vol_chg'], s['days']
            )
            results.append({
                'name': s['name'],
                'stock_change': s['stock_chg'] * 100,
                'vol_change': s['vol_chg'] * 100,
                'pnl': pnl,
                'pnl_pct': (pnl / (self.market_price * 100 * self.num_contracts)) * 100
            })

        # Find best and worst
        sorted_results = sorted(results, key=lambda x: x['pnl'])
        worst = sorted_results[0]
        best = sorted_results[-1]

        return {
            'all': results,
            'best': best,
            'worst': worst
        }

    def _calculate_scenario_pnl(self, stock_change, vol_change, days):
        """Calculate P&L for a specific scenario."""
        new_S = self.S * (1 + stock_change)
        new_sigma = max(self.sigma + vol_change, 0.05)
        new_T = max(self.T - days/365, 0.001)

        # Calculate new option price
        new_price = self._bs_call(new_S, self.K, new_T, self.r, new_sigma)

        # P&L per contract
        pnl_per_contract = (new_price - self.market_price) * 100
        return pnl_per_contract * self.num_contracts

    def _bs_call(self, S, K, T, r, sigma):
        """Black-Scholes call price."""
        d1 = (math.log(S/K) + (r + 0.5*sigma**2)*T) / (sigma * math.sqrt(T))
        d2 = d1 - sigma * math.sqrt(T)
        return S * norm_cdf(d1) - K * math.exp(-r*T) * norm_cdf(d2)

    def generate_sensitivity_analysis(self):
        """
        Generate sensitivity analysis data for volatility and time decay.

        Returns structured data for plotting:
        - Volatility sweep: 20 points from 50% to 200% of current IV
        - Time decay sweep: 30 points from current DTE to 1 day
        """
        # Volatility sensitivity sweep (20 points from 50% to 200% of current IV)
        vol_multipliers = [0.5 + (1.5 * i / 19) for i in range(20)]  # 0.5 to 2.0
        vol_sweep = []
        for mult in vol_multipliers:
            test_sigma = self.sigma * mult
            price = self._bs_call(self.S, self.K, self.T, self.r, test_sigma)
            pnl = (price - self.market_price) * 100 * self.num_contracts
            vol_sweep.append({
                'vol_pct': test_sigma * 100,
                'vol_mult': mult,
                'price': price,
                'pnl': pnl
            })

        # Time decay sweep (30 points from current DTE to 1 day)
        current_dte = int(self.T * 365)
        if current_dte < 2:
            current_dte = 30  # Default if DTE is too low
        time_points = 30
        time_sweep = []
        for i in range(time_points):
            dte = max(1, current_dte - (current_dte - 1) * i / (time_points - 1))
            test_T = dte / 365
            price = self._bs_call(self.S, self.K, test_T, self.r, self.sigma)
            pnl = (price - self.market_price) * 100 * self.num_contracts
            time_sweep.append({
                'dte': dte,
                'price': price,
                'pnl': pnl
            })

        return {
            'vol_sweep': vol_sweep,
            'time_sweep': time_sweep,
            'current_vol': self.sigma * 100,
            'current_dte': current_dte
        }
