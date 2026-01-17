"""
Report generation module.
Creates the consulting memo and analysis summary.
"""

import json
from datetime import datetime


class ReportGenerator:
    """Generates professional analysis reports."""

    def __init__(self, config):
        self.config = config
        self.output_dir = config.REPORTS_DIR

    def generate(self, **data):
        """Generate all reports."""
        self._generate_memo(data)
        self._generate_json_summary(data)

    def _generate_memo(self, data):
        """Generate one-page consulting memo."""
        metadata = data['metadata']
        selected = data['selected']
        vol = data['vol_metrics']
        pricing = data['pricing']
        greeks = data['greeks']
        hedge = data['hedge']
        scenarios = data['scenarios']

        vrp = (selected['implied_volatility'] - vol['hv_21d']) * 100

        memo = f"""
================================================================================
                        CONSULTING MEMORANDUM
================================================================================

TO:       Portfolio Management Team
FROM:     Quantitative Analysis Desk
DATE:     {datetime.now().strftime('%Y-%m-%d')}
RE:       {metadata['ticker']} Options Analysis

--------------------------------------------------------------------------------
EXECUTIVE SUMMARY
--------------------------------------------------------------------------------

Position:     {metadata['ticker']} ${selected['strike']:.0f} Call
Expiration:   {metadata['expiration']} ({metadata['dte']} days)
Stock Price:  ${metadata['current_price']:.2f}

FINDING: Option is {pricing['valuation']} relative to historical volatility
         ({pricing['mispricing_pct']:+.1f}% vs model price)

RECOMMENDATION: {'Consider selling premium or waiting for better entry' if pricing['valuation'] == 'EXPENSIVE' else 'Favorable entry for long position'}

--------------------------------------------------------------------------------
PRICING ANALYSIS
--------------------------------------------------------------------------------

  Market Price:       ${selected['mid_price']:.2f}
  Model Price (HV):   ${pricing['price_hv']:.2f}
  Model Price (IV):   ${pricing['price_iv']:.2f}

  Valuation:          {pricing['valuation']} ({pricing['mispricing_pct']:+.1f}%)

--------------------------------------------------------------------------------
VOLATILITY
--------------------------------------------------------------------------------

  21-Day Realized:    {vol['hv_21d']*100:.1f}%
  Implied Vol:        {selected['implied_volatility']*100:.1f}%
  Risk Premium:       {vrp:+.1f}%
  Regime:             {vol['regime']} ({vol['percentile']:.0f}th percentile)

--------------------------------------------------------------------------------
GREEKS
--------------------------------------------------------------------------------

  Delta:   {greeks['delta']:.3f}    (~{greeks['shares_equiv']:.0f} shares per contract)
  Gamma:   {greeks['gamma']:.5f}
  Theta:   ${greeks['theta_daily']*100:.2f}/day
  Vega:    ${greeks['vega_dollar']:.2f} per 1% IV

--------------------------------------------------------------------------------
HEDGING
--------------------------------------------------------------------------------

  Position Size:     {self.config.NUM_CONTRACTS} contracts
  Delta Exposure:    {hedge['delta_exposure']:.0f} shares
  To Hedge:          {hedge['direction']} {abs(hedge['shares']):.0f} shares
  Capital Required:  ${hedge['capital']:,.2f}

--------------------------------------------------------------------------------
SCENARIOS (1 Week)
--------------------------------------------------------------------------------

  Best Case:    {scenarios['best']['name']:15} ${scenarios['best']['pnl']:>+10,.0f}
  Worst Case:   {scenarios['worst']['name']:15} ${scenarios['worst']['pnl']:>+10,.0f}

--------------------------------------------------------------------------------
MONITORING
--------------------------------------------------------------------------------

  - Stock price relative to ${selected['strike']:.0f} strike
  - Implied volatility changes
  - Time decay acceleration near expiry
  - Delta drift requiring hedge rebalance

--------------------------------------------------------------------------------
MODEL LIMITATIONS
--------------------------------------------------------------------------------

Black-Scholes Assumptions:
  - Constant volatility (reality: volatility changes over time)
  - Lognormal price distribution (reality: fat tails, skewness)
  - No dividends (NVDA pays minimal dividends, acceptable)
  - European exercise (these are American options)
  - Continuous trading (reality: gaps, halts possible)

Practical Considerations:
  - Bid-ask spread impact on entry/exit
  - Transaction costs reduce profitability
  - Model uses mid-price; actual fills may differ
  - Greeks change continuously (gamma risk)

Risk Factors:
  - Earnings announcements can cause vol spikes
  - Liquidity can dry up in stress scenarios
  - Early exercise risk for American options

================================================================================
                          CONFIDENTIAL
================================================================================
"""
        filepath = self.output_dir / 'consulting_memo.txt'
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(memo)

    def _generate_json_summary(self, data):
        """Generate JSON summary for programmatic use."""
        metadata = data['metadata']
        selected = data['selected']
        vol = data['vol_metrics']
        pricing = data['pricing']
        greeks = data['greeks']
        hedge = data['hedge']
        scenarios = data['scenarios']

        summary = {
            'generated': datetime.now().isoformat(),
            'position': {
                'ticker': metadata['ticker'],
                'strike': selected['strike'],
                'expiration': metadata['expiration'],
                'dte': metadata['dte'],
                'stock_price': metadata['current_price'],
                'option_price': selected['mid_price'],
                'pct_otm': selected['pct_otm']
            },
            'pricing': {
                'market_price': selected['mid_price'],
                'model_price_hv': pricing['price_hv'],
                'model_price_iv': pricing['price_iv'],
                'mispricing_pct': pricing['mispricing_pct'],
                'valuation': pricing['valuation']
            },
            'volatility': {
                'hv_21d': vol['hv_21d'],
                'implied_vol': selected['implied_volatility'],
                'vrp': selected['implied_volatility'] - vol['hv_21d'],
                'regime': vol['regime']
            },
            'greeks': {
                'delta': greeks['delta'],
                'gamma': greeks['gamma'],
                'theta_daily': greeks['theta_daily'],
                'vega': greeks['vega']
            },
            'hedge': {
                'contracts': self.config.NUM_CONTRACTS,
                'delta_exposure': hedge['delta_exposure'],
                'hedge_shares': hedge['shares'],
                'hedge_capital': hedge['capital']
            },
            'scenarios': {
                'best': scenarios['best'],
                'worst': scenarios['worst']
            }
        }

        filepath = self.output_dir / 'analysis_summary.json'
        with open(filepath, 'w') as f:
            json.dump(summary, f, indent=2)
