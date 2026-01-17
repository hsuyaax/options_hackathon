"""
Black-Scholes option pricing model implementation.
"""

import math


def norm_cdf(x):
    """Standard normal cumulative distribution function."""
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def norm_pdf(x):
    """Standard normal probability density function."""
    return math.exp(-0.5 * x * x) / math.sqrt(2.0 * math.pi)


class OptionPricer:
    """
    Black-Scholes option pricing.

    Parameters:
        S: Current stock price
        K: Strike price
        T: Time to expiration (years)
        r: Risk-free rate
        sigma_hv: Historical volatility
        sigma_iv: Implied volatility
    """

    def __init__(self, S, K, T, r, sigma_hv, sigma_iv):
        self.S = S
        self.K = K
        self.T = max(T, 0.001)  # Prevent zero division
        self.r = r
        self.sigma_hv = sigma_hv
        self.sigma_iv = sigma_iv

    def calculate(self):
        """Calculate option prices using both HV and IV."""
        price_hv = self._bs_call_price(self.sigma_hv)
        price_iv = self._bs_call_price(self.sigma_iv)

        return {
            'price_hv': price_hv,
            'price_iv': price_iv,
            'mispricing': price_iv - price_hv,
            'mispricing_pct': ((price_iv - price_hv) / price_hv) * 100 if price_hv > 0 else 0,
            'valuation': self._get_valuation(price_hv, price_iv)
        }

    def _bs_call_price(self, sigma):
        """Calculate Black-Scholes call option price."""
        d1 = self._d1(sigma)
        d2 = self._d2(sigma)

        price = (self.S * norm_cdf(d1) -
                 self.K * math.exp(-self.r * self.T) * norm_cdf(d2))
        return price

    def _d1(self, sigma):
        """Calculate d1 parameter."""
        numerator = math.log(self.S / self.K) + (self.r + 0.5 * sigma**2) * self.T
        return numerator / (sigma * math.sqrt(self.T))

    def _d2(self, sigma):
        """Calculate d2 parameter."""
        return self._d1(sigma) - sigma * math.sqrt(self.T)

    def _get_valuation(self, price_hv, price_iv):
        """Determine if option is cheap, fair, or expensive."""
        diff_pct = ((price_iv - price_hv) / price_hv) * 100 if price_hv > 0 else 0

        if diff_pct > 20:
            return "EXPENSIVE"
        elif diff_pct < -20:
            return "CHEAP"
        else:
            return "FAIR"

    def get_d1(self):
        return self._d1(self.sigma_iv)

    def get_d2(self):
        return self._d2(self.sigma_iv)

    def get_price_iv(self):
        return self._bs_call_price(self.sigma_iv)

    def calculate_put(self):
        """Calculate put option prices using both HV and IV."""
        price_hv = self._bs_put_price(self.sigma_hv)
        price_iv = self._bs_put_price(self.sigma_iv)

        return {
            'price_hv': price_hv,
            'price_iv': price_iv,
            'mispricing': price_iv - price_hv,
            'mispricing_pct': ((price_iv - price_hv) / price_hv) * 100 if price_hv > 0 else 0,
            'valuation': self._get_valuation(price_hv, price_iv)
        }

    def _bs_put_price(self, sigma):
        """Calculate Black-Scholes put option price."""
        d1 = self._d1(sigma)
        d2 = self._d2(sigma)

        price = (self.K * math.exp(-self.r * self.T) * norm_cdf(-d2) -
                 self.S * norm_cdf(-d1))
        return price

    def get_put_price_iv(self):
        return self._bs_put_price(self.sigma_iv)
