#!/usr/bin/env python3
"""
NVDA Options Pricing & Risk Analysis
=====================================
National Level Hackathon Submission

Team: [Your Team Name]
Date: January 2026

This analysis examines a live NVDA call option using:
- Black-Scholes option pricing model
- Greeks calculation and interpretation
- Delta hedging strategy
- Scenario-based risk analysis
"""

import sys
import os
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from config import Config
from data_loader import DataLoader
from volatility import VolatilityAnalyzer
from black_scholes import OptionPricer
from greeks import GreeksCalculator
from hedging import HedgingAnalyzer
from scenarios import ScenarioEngine
from visualization import ChartGenerator
from report_generator import ReportGenerator


def print_header():
    print()
    print("=" * 70)
    print("     NVDA OPTIONS ANALYSIS - HACKATHON SUBMISSION")
    print("=" * 70)
    print(f"     Execution Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    print()


def print_section(title):
    print()
    print("-" * 50)
    print(f"  {title}")
    print("-" * 50)


def run_analysis():
    """Execute the complete options analysis pipeline."""

    print_header()

    # Initialize configuration
    config = Config()

    # Step 1: Load market data
    print_section("LOADING MARKET DATA")
    loader = DataLoader(config)
    stock_data, option_chain, put_chain, metadata = loader.load_all()
    print(f"  Stock: {config.TICKER}")
    print(f"  Current Price: ${metadata['current_price']:.2f}")
    print(f"  Option Expiry: {metadata['expiration']}")

    # Step 2: Select optimal option contract
    print_section("OPTION SELECTION")
    selected = loader.select_option(option_chain, metadata['current_price'])
    print(f"  Selected: ${selected['strike']:.0f} Call")
    print(f"  Market Price: ${selected['mid_price']:.2f}")
    print(f"  OTM: {selected['pct_otm']:.1f}%")
    print(f"  Open Interest: {selected['open_interest']:,}")

    # Step 3: Volatility analysis
    print_section("VOLATILITY ANALYSIS")
    vol_analyzer = VolatilityAnalyzer(stock_data)
    vol_metrics = vol_analyzer.analyze()
    vrp = selected['implied_volatility'] - vol_metrics['hv_21d']
    vol_metrics['vrp'] = vrp
    print(f"  21-Day Historical Vol: {vol_metrics['hv_21d']*100:.1f}%")
    print(f"  Implied Volatility: {selected['implied_volatility']*100:.1f}%")
    print(f"  Vol Risk Premium: {vrp*100:+.1f}%")
    print(f"  Regime: {vol_metrics['regime']}")

    # Step 4: Black-Scholes pricing
    print_section("BLACK-SCHOLES PRICING")
    pricer = OptionPricer(
        S=metadata['current_price'],
        K=selected['strike'],
        T=metadata['dte'] / 365,
        r=metadata['risk_free_rate'],
        sigma_hv=vol_metrics['hv_21d'],
        sigma_iv=selected['implied_volatility']
    )
    pricing = pricer.calculate()
    print(f"  Model Price (HV): ${pricing['price_hv']:.2f}")
    print(f"  Model Price (IV): ${pricing['price_iv']:.2f}")
    print(f"  Market Price: ${selected['mid_price']:.2f}")
    print(f"  Mispricing: {pricing['mispricing_pct']:+.1f}%")
    print(f"  Valuation: {pricing['valuation']}")

    # Step 5: Greeks calculation
    print_section("GREEKS ANALYSIS")
    greeks_calc = GreeksCalculator(pricer)
    greeks = greeks_calc.calculate()
    print(f"  Delta: {greeks['delta']:.4f} ({greeks['delta']*100:.0f} shares equiv.)")
    print(f"  Gamma: {greeks['gamma']:.6f}")
    print(f"  Theta: ${greeks['theta_daily']:.2f}/day")
    print(f"  Vega: ${greeks['vega_dollar']:.2f} per 1% IV")

    # Step 6: Hedging strategy
    print_section("HEDGING STRATEGY")
    hedger = HedgingAnalyzer(greeks, metadata['current_price'], config.NUM_CONTRACTS)
    hedge = hedger.calculate()
    print(f"  Position: {config.NUM_CONTRACTS} contracts")
    print(f"  Delta Exposure: {hedge['delta_exposure']:.0f} shares")
    print(f"  Hedge: {hedge['direction']} {abs(hedge['shares']):.0f} shares")
    print(f"  Hedge Capital: ${hedge['capital']:,.2f}")

    # Step 7: Scenario analysis
    print_section("SCENARIO ANALYSIS")
    scenario_engine = ScenarioEngine(pricer, selected['mid_price'], config.NUM_CONTRACTS)
    scenarios = scenario_engine.run()
    print(f"  Best Case: {scenarios['best']['name']} -> ${scenarios['best']['pnl']:+,.0f}")
    print(f"  Worst Case: {scenarios['worst']['name']} -> ${scenarios['worst']['pnl']:+,.0f}")

    # Feature 1: Sensitivity Analysis
    print("\n  Generating sensitivity analysis...")
    sensitivity_data = scenario_engine.generate_sensitivity_analysis()

    # Feature 2: Put Option Comparison
    print_section("PUT OPTION ANALYSIS")
    put_selected = loader.select_put_option(put_chain, metadata['current_price'])

    put_data_chart = None
    if put_selected:
        print(f"  Selected Put: ${put_selected['strike']:.0f} Put")
        print(f"  Market Price: ${put_selected['mid_price']:.2f}")
        print(f"  OTM: {put_selected['pct_otm']:.1f}%")

        # Put Pricing
        put_pricer = OptionPricer(
            S=metadata['current_price'],
            K=put_selected['strike'],
            T=metadata['dte'] / 365,
            r=metadata['risk_free_rate'],
            sigma_hv=vol_metrics['hv_21d'],
            sigma_iv=put_selected['implied_volatility']
        )
        put_pricing = put_pricer.calculate_put()

        # Put Greeks
        put_greeks_calc = GreeksCalculator(put_pricer, option_type='put')
        put_greeks = put_greeks_calc.calculate()

        print(f"  Put Delta: {put_greeks['delta']:.4f}")
        print(f"  Put Implied Vol: {put_selected['implied_volatility']*100:.1f}%")

        # Structure data for comparison chart
        call_data_chart = {
            'market_price': selected['mid_price'],
            'model_price_iv': pricing['price_iv'],
            'greeks': greeks,
            'implied_vol': selected['implied_volatility']
        }

        put_data_chart = {
            'market_price': put_selected['mid_price'],
            'model_price_iv': put_pricing['price_iv'],
            'greeks': put_greeks,
            'implied_vol': put_selected['implied_volatility']
        }
    else:
        print("  No suitable put option found for comparison.")

    # Step 8: Generate visualizations
    print_section("GENERATING CHARTS")
    chart_gen = ChartGenerator(config)
    chart_gen.generate_all(
        stock_data=stock_data,
        vol_metrics=vol_metrics,
        pricing=pricing,
        greeks=greeks,
        scenarios=scenarios,
        selected=selected,
        metadata=metadata
    )

    # Feature 1 Chart
    chart_gen.plot_sensitivity_analysis(sensitivity_data)

    # Feature 2 Chart
    if put_data_chart:
        chart_gen.plot_call_put_comparison(call_data_chart, put_data_chart)

    print(f"  Charts saved to: figures/")

    # Step 9: Generate report
    print_section("GENERATING REPORT")
    report_gen = ReportGenerator(config)
    report_gen.generate(
        metadata=metadata,
        selected=selected,
        vol_metrics=vol_metrics,
        pricing=pricing,
        greeks=greeks,
        hedge=hedge,
        scenarios=scenarios
    )
    print(f"  Report saved to: reports/")

    # Summary
    print()
    print("=" * 70)
    print("  ANALYSIS COMPLETE")
    print("=" * 70)
    print()
    print(f"  Key Finding: Option is {pricing['valuation']}")
    print(f"  Recommendation: {'Sell premium' if pricing['valuation'] == 'EXPENSIVE' else 'Buy'}")
    print()

    return True


if __name__ == "__main__":
    try:
        success = run_analysis()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)
