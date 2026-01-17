# Technical Whitepaper: Advanced Options Analytics System

## 1. Executive Summary

This document details the technical architecture, mathematical framework, and financial engineering principles behind the Options Analytics System. Unlike basic calculators that rely on simple approximations, this system implements an "institutional-grade" approach to derivatives pricing.

The core philosophy bridges the gap between academic theory and trading desk reality by focusing on:
1.  **Numerical Robustness**: Handling edge cases (e.g., expiration approaches) where standard textbook formulas fail.
2.  **Actionable Intelligence**: converting raw Greek values into trader-centric units (e.g., "Dollars per 1% Vol" instead of unitless Vega).
3.  **Scenario Precision**: Re-pricing options under stress tests rather than using linear Delta/Gamma approximations which break down during large market moves.

---

## 2. System Architecture

The application follows a unidirectional data flow architecture designed to decouple pricing logic from market state simulation.

### Data Flow Pipeline
1.  **`DataLoader`**: Ingests raw market data (price history, option chains) and normalizes it into a canonical format.
2.  **`VolatilityAnalyzer`**: Computes realized volatility cones (21d, 63d, 252d) to establish a baseline for "fair value."
3.  **`OptionPricer`**: The core valuation engine that computes theoretical prices using both Historical Volatility (HV) and Implied Volatility (IV).
4.  **`GreeksCalculator`**: Derives second-order sensitivities from the pricing model.
5.  **`ScenarioEngine`**: A simulation layer that mutates market parameters (Stock Price, Volatility, Time) and re-invokes the `OptionPricer` to generate P&L surfaces.

### Design Pattern
The system uses a **Strategy Pattern** for valuation. The `OptionPricer` is stateless regarding the market "scenario." This allows the `ScenarioEngine` to instantiate thousands of hypothetical market states and feed them into the same robust pricing logic without side effects.

---

## 3. Mathematical Framework

### Black-Scholes-Merton Implementation

We implement the generalized Black-Scholes-Merton model for European options.

**Key Formulas:**

$$
C = S N(d_1) - K e^{-rT} N(d_2)
$$

$$
P = K e^{-rT} N(-d_2) - S N(-d_1)
$$

Where:
$$ d_1 = \frac{\ln(S/K) + (r + \frac{\sigma^2}{2})T}{\sigma \sqrt{T}} $$
$$ d_2 = d_1 - \sigma \sqrt{T} $$

### Numerical Robustness

Standard implementations often fail when $T \to 0$ (approaching expiration) due to division by zero in the $d_1$ denominator.

**Our Implementation:**
- **Time Floor**: We enforce `T = max(T, 0.001)` in `src/black_scholes.py`. This prevents `ZeroDivisionError` while maintaining precision for options expiring effectively "now."
- **Error Function**: We use `math.erf` for the Cumulative Distribution Function (CDF) instead of approximation tables, ensuring 15-decimal precision.

### Greeks & Unit Normalization

Raw mathematical Greeks are often unintuitive. We normalize them into "Trader Units" in `src/greeks.py`:

| Greek | Math Definition | Implementation Note | Trader Meaning |
|-------|----------------|---------------------|----------------|
| **Delta** ($\Delta$) | $\partial V / \partial S$ | Standard $0 \to 1$ scale | Share equivalents per contract ($\times 100$). |
| **Theta** ($\Theta$) | $\partial V / \partial t$ | Annualized decay / 365 | Daily dollar decay (negative for long positions). |
| **Vega** ($\nu$) | $\partial V / \partial \sigma$ | $\times 100$ | **P&L per 1% change in Volatility** (Crucial for vol trading). |
| **Rho** ($\rho$) | $\partial V / \partial r$ | $\times 100$ | P&L per 1% change in risk-free rates. |

---

## 4. Financial Engineering

### Volatility Risk Premium (VRP)
We quantify the "edge" available to option sellers by calculating the spread between Implied Volatility (market price) and Historical Volatility (actual movement).

$$ \text{VRP} = \sigma_{IV} - \sigma_{HV} $$

- **Positive VRP**: Options are "expensive" relative to recent moves (Selling opportunity).
- **Negative VRP**: Options are "cheap" (Buying opportunity).

### Dynamic Valuation Logic
The system automatically classifies options based on the `mispricing_pct` metric:
- **EXPENSIVE**: Market Price > Theoretical Price by > 20%
- **CHEAP**: Market Price < Theoretical Price by > 20%
- **FAIR**: Within ±20% band

### Skew Analysis
While the current version focuses on single-leg analysis, the architecture supports skew quantification by comparing IV across strikes (in `OptionPricer`).

---

## 5. Risk & Scenario Analysis

### Non-Linear Re-pricing
A common mistake in risk management is using Delta and Gamma to estimate P&L for large moves. This linear approximation fails because Gamma itself changes (convexity).

**Our Approach (`ScenarioEngine`):**
Instead of approximating, we **fully re-calculate** the Black-Scholes price for every scenario.
- **Example**: For a "Crash" scenario (-15% spot, +20% vol), we calculate:
  `Price_New = BSM(S*0.85, K, T-7days, r, sigma+0.20)`

This captures the "Gamma of the Gamma" (Speed) and "Vol of Vol" (Volga) implicitly.

### Sensitivity Engine
We generate a 2D sensitivity surface:
1.  **Volatility Sweep**: Re-pricing across 50% to 200% of current IV.
2.  **Time Decay Sweep**: Re-pricing from today until expiration.

This allows traders to visualize the "zone of profit" visually rather than relying on single point estimates.
