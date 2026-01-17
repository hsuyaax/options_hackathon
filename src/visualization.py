"""
Visualization module for generating analysis charts.
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
import math


class ChartGenerator:
    """Generates professional charts for the analysis."""

    def __init__(self, config):
        self.config = config
        self.colors = config.COLORS
        self.output_dir = config.FIGURES_DIR

        # Set plot style with fallback
        try:
            plt.style.use(config.CHART_STYLE)
        except:
            try:
                plt.style.use('seaborn-whitegrid')
            except:
                plt.style.use('ggplot')
        
        plt.rcParams['font.family'] = 'sans-serif'
        plt.rcParams['font.size'] = 10

    def generate_all(self, **data):
        """Generate all required charts."""
        self._plot_stock_history(data['stock_data'])
        self._plot_volatility(data['vol_metrics'], data['selected']['implied_volatility'])
        self._plot_greeks(data['greeks'], data['selected'], data['metadata'])
        self._plot_scenarios(data['scenarios'])
        self._plot_pricing(data['pricing'], data['selected']['mid_price'])

    def _plot_stock_history(self, stock_data):
        """12-month stock price chart."""
        fig, ax = plt.subplots(figsize=(12, 5))

        ax.plot(stock_data.index, stock_data['Close'],
                color=self.colors['primary'], linewidth=1.5)
        ax.fill_between(stock_data.index, stock_data['Close'],
                        alpha=0.1, color=self.colors['primary'])

        current = stock_data['Close'].iloc[-1]
        ax.axhline(y=current, color=self.colors['negative'],
                   linestyle='--', alpha=0.7)
        ax.annotate(f'${current:.2f}',
                    xy=(stock_data.index[-1], current),
                    xytext=(5, 5), textcoords='offset points',
                    fontweight='bold', color=self.colors['negative'])

        ax.set_title('NVDA Stock Price - 12 Month History', fontweight='bold')
        ax.set_xlabel('Date')
        ax.set_ylabel('Price ($)')

        plt.tight_layout()
        plt.savefig(self.output_dir / 'stock_history.png',
                    dpi=self.config.CHART_DPI, bbox_inches='tight')
        plt.close()

    def _plot_volatility(self, vol_metrics, iv):
        """Volatility comparison chart."""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

        # Historical volatility over time
        history = vol_metrics['hv_history']
        ax1.plot(history.index, history['hv_21d'] * 100,
                 color=self.colors['primary'], linewidth=1.5, label='21-Day HV')
        ax1.axhline(y=iv * 100, color=self.colors['negative'],
                    linestyle='--', linewidth=2, label='Implied Vol')

        ax1.set_title('Historical vs Implied Volatility', fontweight='bold')
        ax1.set_xlabel('Date')
        ax1.set_ylabel('Volatility (%)')
        ax1.legend()

        # Bar comparison
        hv = vol_metrics['hv_21d'] * 100
        iv_pct = iv * 100
        vrp = iv_pct - hv

        bars = ax2.bar(['Historical Vol', 'Implied Vol'],
                       [hv, iv_pct],
                       color=[self.colors['primary'], self.colors['negative']])

        for bar, val in zip(bars, [hv, iv_pct]):
            ax2.annotate(f'{val:.1f}%',
                         xy=(bar.get_x() + bar.get_width()/2, bar.get_height()),
                         xytext=(0, 5), textcoords='offset points',
                         ha='center', fontweight='bold')

        ax2.set_title(f'Volatility Risk Premium: {vrp:+.1f}%', fontweight='bold')
        ax2.set_ylabel('Volatility (%)')

        plt.tight_layout()
        plt.savefig(self.output_dir / 'volatility_analysis.png',
                    dpi=self.config.CHART_DPI, bbox_inches='tight')
        plt.close()

    def _plot_greeks(self, greeks, selected, metadata):
        """Greeks dashboard."""
        fig = plt.figure(figsize=(14, 8))
        gs = GridSpec(2, 3, figure=fig, hspace=0.3, wspace=0.3)

        delta = greeks['delta']
        theta = greeks['theta_daily']
        vega = greeks['vega']

        # Delta gauge
        ax1 = fig.add_subplot(gs[0, 0])
        ax1.barh(['Delta'], [delta], color=self.colors['primary'], height=0.5)
        ax1.barh(['Delta'], [1-delta], left=[delta], color='#e0e0e0', height=0.5)
        ax1.set_xlim(0, 1)
        ax1.set_title(f'Delta: {delta:.3f}', fontweight='bold')
        ax1.text(delta/2, 0, f'{delta*100:.0f}%', ha='center', va='center',
                 color='white', fontweight='bold')

        # Theta decay
        ax2 = fig.add_subplot(gs[0, 1])
        days = np.arange(1, 15)
        decay = np.abs(theta) * 100 * days
        ax2.bar(days, decay, color=self.colors['negative'], alpha=0.7)
        ax2.set_title(f'Theta: ${abs(theta)*100:.2f}/day', fontweight='bold')
        ax2.set_xlabel('Days')
        ax2.set_ylabel('Cumulative Decay ($)')

        # Vega exposure
        ax3 = fig.add_subplot(gs[0, 2])
        vol_changes = np.arange(-10, 11, 2)
        pnl = vega * 100 * vol_changes
        colors = [self.colors['negative'] if x < 0 else self.colors['secondary'] for x in pnl]
        ax3.bar(vol_changes, pnl, color=colors, alpha=0.7)
        ax3.axhline(y=0, color='black', linewidth=0.5)
        ax3.set_title(f'Vega: ${vega*100:.2f} per 1% IV', fontweight='bold')
        ax3.set_xlabel('IV Change (%)')
        ax3.set_ylabel('P&L ($)')

        # Delta curve
        ax4 = fig.add_subplot(gs[1, :2])
        S = metadata['current_price']
        K = selected['strike']
        T = metadata['dte'] / 365
        r = metadata['risk_free_rate']
        sigma = selected['implied_volatility']

        strikes = np.linspace(S * 0.7, S * 1.3, 100)
        deltas = []
        for strike in strikes:
            d1 = (np.log(S/strike) + (r + 0.5*sigma**2)*T) / (sigma * np.sqrt(T))
            deltas.append(0.5 * (1 + math.erf(d1 / np.sqrt(2))))

        ax4.plot(strikes, deltas, color=self.colors['primary'], linewidth=2)
        ax4.axvline(x=K, color=self.colors['negative'], linestyle='--',
                    label=f'Strike: ${K:.0f}')
        ax4.axvline(x=S, color=self.colors['secondary'], linestyle=':',
                    label=f'Current: ${S:.0f}')
        ax4.scatter([K], [delta], color=self.colors['negative'], s=100, zorder=5)
        ax4.set_title('Delta Across Strikes', fontweight='bold')
        ax4.set_xlabel('Strike ($)')
        ax4.set_ylabel('Delta')
        ax4.legend()
        ax4.set_ylim(0, 1)

        # Summary table
        ax5 = fig.add_subplot(gs[1, 2])
        ax5.axis('off')
        table_data = [
            ['Greek', 'Value', 'Meaning'],
            ['Delta', f'{delta:.3f}', f'{delta*100:.0f} shares/contract'],
            ['Gamma', f'{greeks["gamma"]:.5f}', 'Delta change/$1'],
            ['Theta', f'${theta*100:.2f}', 'Daily decay'],
            ['Vega', f'${vega*100:.2f}', 'Per 1% IV'],
        ]
        table = ax5.table(cellText=table_data[1:], colLabels=table_data[0],
                          loc='center', cellLoc='center')
        table.auto_set_font_size(False)
        table.set_fontsize(10)
        table.scale(1.2, 1.8)

        plt.savefig(self.output_dir / 'greeks_dashboard.png',
                    dpi=self.config.CHART_DPI, bbox_inches='tight')
        plt.close()

    def _plot_scenarios(self, scenarios):
        """Scenario P&L chart."""
        fig, ax = plt.subplots(figsize=(12, 6))

        results = sorted(scenarios['all'], key=lambda x: x['pnl'])
        names = [r['name'] for r in results]
        pnls = [r['pnl'] for r in results]
        colors = [self.colors['secondary'] if p > 0 else self.colors['negative'] for p in pnls]

        bars = ax.barh(names, pnls, color=colors)
        ax.axvline(x=0, color='black', linewidth=1)

        for bar, pnl in zip(bars, pnls):
            x = bar.get_width()
            ax.annotate(f'${pnl:+,.0f}',
                        xy=(x, bar.get_y() + bar.get_height()/2),
                        xytext=(5 if pnl >= 0 else -5, 0),
                        textcoords='offset points',
                        ha='left' if pnl >= 0 else 'right',
                        va='center', fontweight='bold')

        ax.set_title('Scenario Analysis: 1-Week P&L (10 Contracts)', fontweight='bold')
        ax.set_xlabel('Profit / Loss ($)')

        plt.tight_layout()
        plt.savefig(self.output_dir / 'scenario_analysis.png',
                    dpi=self.config.CHART_DPI, bbox_inches='tight')
        plt.close()

    def _plot_pricing(self, pricing, market_price):
        """Pricing comparison chart."""
        fig, ax = plt.subplots(figsize=(10, 6))

        categories = ['Market Price', 'Model (HV)', 'Model (IV)']
        values = [market_price, pricing['price_hv'], pricing['price_iv']]
        colors = [self.colors['negative'], self.colors['primary'], self.colors['secondary']]

        bars = ax.bar(categories, values, color=colors, width=0.6)

        for bar, val in zip(bars, values):
            ax.annotate(f'${val:.2f}',
                        xy=(bar.get_x() + bar.get_width()/2, bar.get_height()),
                        xytext=(0, 5), textcoords='offset points',
                        ha='center', fontsize=14, fontweight='bold')

        valuation = pricing['valuation']
        mispricing = pricing['mispricing_pct']
        ax.text(0.98, 0.95, f'{valuation}\n({mispricing:+.1f}%)',
                transform=ax.transAxes, ha='right', va='top',
                fontsize=12, fontweight='bold',
                color=self.colors['negative'] if valuation == 'EXPENSIVE' else self.colors['secondary'],
                bbox=dict(boxstyle='round', facecolor='white', edgecolor='gray'))

        ax.set_title('Option Pricing Comparison', fontweight='bold')
        ax.set_ylabel('Price ($)')

        plt.tight_layout()
        plt.savefig(self.output_dir / 'pricing_comparison.png',
                    dpi=self.config.CHART_DPI, bbox_inches='tight')
        plt.close()

    def plot_sensitivity_analysis(self, sensitivity_data):
        """Plot volatility and time decay sensitivity curves."""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

        vol_sweep = sensitivity_data['vol_sweep']
        time_sweep = sensitivity_data['time_sweep']
        current_vol = sensitivity_data['current_vol']
        current_dte = sensitivity_data['current_dte']

        # Volatility sensitivity curve
        vols = [v['vol_pct'] for v in vol_sweep]
        vol_pnls = [v['pnl'] for v in vol_sweep]

        ax1.plot(vols, vol_pnls, color=self.colors['primary'], linewidth=2)
        ax1.axhline(y=0, color='black', linewidth=0.5, linestyle='--')
        ax1.axvline(x=current_vol, color=self.colors['negative'], linewidth=2,
                    linestyle='--', label=f'Current IV: {current_vol:.1f}%')
        ax1.fill_between(vols, vol_pnls, alpha=0.3, color=self.colors['primary'])

        ax1.set_title('P&L Sensitivity to Implied Volatility', fontweight='bold')
        ax1.set_xlabel('Implied Volatility (%)')
        ax1.set_ylabel('P&L ($)')
        ax1.legend()
        ax1.grid(True, alpha=0.3)

        # Time decay curve
        dtes = [t['dte'] for t in time_sweep]
        time_pnls = [t['pnl'] for t in time_sweep]

        ax2.plot(dtes, time_pnls, color=self.colors['negative'], linewidth=2)
        ax2.axhline(y=0, color='black', linewidth=0.5, linestyle='--')
        ax2.axvline(x=current_dte, color=self.colors['secondary'], linewidth=2,
                    linestyle='--', label=f'Current DTE: {current_dte}')
        ax2.fill_between(dtes, time_pnls, alpha=0.3, color=self.colors['negative'])

        ax2.set_title('P&L Time Decay (Theta)', fontweight='bold')
        ax2.set_xlabel('Days to Expiration')
        ax2.set_ylabel('P&L ($)')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        ax2.invert_xaxis()  # Higher DTE on left

        plt.tight_layout()
        plt.savefig(self.output_dir / 'sensitivity_analysis.png',
                    dpi=self.config.CHART_DPI, bbox_inches='tight')
        plt.close()

    def plot_call_put_comparison(self, call_data, put_data):
        """Plot comparison between call and put options."""
        fig, axes = plt.subplots(1, 3, figsize=(18, 6))

        # 1. Price Comparison
        labels = ['Call', 'Put']
        market_prices = [call_data['market_price'], put_data['market_price']]
        model_prices = [call_data['model_price_iv'], put_data['model_price_iv']]

        x = range(len(labels))
        width = 0.35

        ax1 = axes[0]
        ax1.bar([i - width/2 for i in x], market_prices, width, label='Market Price', color=self.colors['primary'])
        ax1.bar([i + width/2 for i in x], model_prices, width, label='Model Price (IV)', color=self.colors['secondary'])

        ax1.set_ylabel('Price ($)')
        ax1.set_title('Price Comparison', fontweight='bold')
        ax1.set_xticks(x)
        ax1.set_xticklabels(labels)
        ax1.legend()
        ax1.grid(True, axis='y', alpha=0.3)

        # 2. Greeks Comparison (Delta)
        ax2 = axes[1]
        call_delta = call_data['greeks']['delta']
        put_delta = put_data['greeks']['delta']

        ax2.bar(['Call Delta'], [call_delta], width, color=self.colors['primary'])
        ax2.bar(['Put Delta'], [put_delta], width, color=self.colors['negative'])

        ax2.axhline(0, color='black', linewidth=0.8)
        ax2.set_title('Delta Exposure', fontweight='bold')
        ax2.set_ylabel('Delta')
        ax2.grid(True, axis='y', alpha=0.3)

        # 3. Implied Volatility Comparison
        ax3 = axes[2]
        call_iv = call_data['implied_vol'] * 100
        put_iv = put_data['implied_vol'] * 100

        bars = ax3.bar(['Call IV', 'Put IV'], [call_iv, put_iv], width=0.5,
                       color=[self.colors['primary'], self.colors['negative']])

        ax3.set_ylabel('Implied Volatility (%)')
        ax3.set_title('Implied Volatility Skew', fontweight='bold')
        ax3.grid(True, axis='y', alpha=0.3)

        # Add values on top of bars
        for bar in bars:
            height = bar.get_height()
            ax3.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                     f'{height:.1f}%', ha='center', va='bottom')

        plt.tight_layout()
        plt.savefig(self.output_dir / 'call_put_comparison.png',
                    dpi=self.config.CHART_DPI, bbox_inches='tight')
        plt.close()
