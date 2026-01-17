"""
Greeks calculation module.
Computes Delta, Gamma, Theta, Vega, and Rho.
"""

import math
from black_scholes import norm_cdf, norm_pdf


class GreeksCalculator:
    """
    Calculates option Greeks for risk management.

    Greeks measure sensitivity of option price to various factors:
    - Delta: Price sensitivity to underlying
    - Gamma: Delta sensitivity to underlying
    - Theta: Time decay per day
    - Vega: Sensitivity to volatility
    - Rho: Sensitivity to interest rates
    """

    def __init__(self, pricer, option_type='call'):
        self.S = pricer.S
        self.K = pricer.K
        self.T = pricer.T
        self.r = pricer.r
        self.sigma = pricer.sigma_iv
        self.d1 = pricer.get_d1()
        self.d2 = pricer.get_d2()
        self.option_type = option_type.lower()

    def calculate(self):
        """Compute all Greeks."""
        delta = self._delta()
        gamma = self._gamma()
        theta = self._theta()
        vega = self._vega()
        rho = self._rho()

        return {
            'delta': delta,
            'gamma': gamma,
            'theta': theta,
            'theta_daily': theta,
            'theta_weekly': theta * 7,
            'vega': vega,
            'vega_dollar': vega * 100,  # Per contract
            'rho': rho,
            'shares_equiv': delta * 100
        }

    def _delta(self):
        """
        Delta: Rate of change of option price w.r.t. underlying.
        For calls: N(d1), ranges from 0 to 1
        For puts: N(d1) - 1, ranges from -1 to 0
        """
        if self.option_type == 'put':
            return norm_cdf(self.d1) - 1
        return norm_cdf(self.d1)

    def _gamma(self):
        """
        Gamma: Rate of change of delta w.r.t. underlying.
        Same for calls and puts.
        """
        return norm_pdf(self.d1) / (self.S * self.sigma * math.sqrt(self.T))

    def _theta(self):
        """
        Theta: Daily time decay.
        Negative for long options (they lose value over time).
        """
        term1 = -(self.S * norm_pdf(self.d1) * self.sigma) / (2 * math.sqrt(self.T))
        if self.option_type == 'put':
            term2 = -self.r * self.K * math.exp(-self.r * self.T) * norm_cdf(-self.d2)
        else:
            term2 = self.r * self.K * math.exp(-self.r * self.T) * norm_cdf(self.d2)
        annual_theta = term1 - term2
        return annual_theta / 365

    def _vega(self):
        """
        Vega: Sensitivity to 1% change in volatility.
        Same for calls and puts.
        """
        raw_vega = self.S * math.sqrt(self.T) * norm_pdf(self.d1)
        return raw_vega / 100  # Per 1% vol change

    def _rho(self):
        """
        Rho: Sensitivity to 1% change in interest rate.
        """
        if self.option_type == 'put':
            raw_rho = -self.K * self.T * math.exp(-self.r * self.T) * norm_cdf(-self.d2)
        else:
            raw_rho = self.K * self.T * math.exp(-self.r * self.T) * norm_cdf(self.d2)
        return raw_rho / 100  # Per 1% rate change
