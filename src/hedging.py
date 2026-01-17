"""
Delta hedging analysis module.
"""


class HedgingAnalyzer:
    """
    Analyzes delta hedging requirements.

    Delta hedging neutralizes directional risk by taking
    an offsetting position in the underlying stock.
    """

    def __init__(self, greeks, stock_price, num_contracts):
        self.delta = greeks['delta']
        self.stock_price = stock_price
        self.num_contracts = num_contracts
        self.shares_per_contract = 100

    def calculate(self):
        """Calculate hedge requirements."""
        # Total delta exposure
        total_delta = self.delta * self.num_contracts * self.shares_per_contract

        # To hedge: take opposite position
        # Long calls have positive delta, so short stock to hedge
        hedge_shares = -total_delta

        return {
            'delta_per_contract': self.delta,
            'delta_exposure': total_delta,
            'shares': hedge_shares,
            'direction': 'SHORT' if hedge_shares < 0 else 'LONG',
            'capital': abs(hedge_shares) * self.stock_price
        }

    def get_hedge_pnl(self, price_change_pct):
        """Calculate hedge P&L for a given price move."""
        new_price = self.stock_price * (1 + price_change_pct)
        hedge_shares = -self.delta * self.num_contracts * self.shares_per_contract
        return hedge_shares * (new_price - self.stock_price)
