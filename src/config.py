"""
Configuration settings for the options analysis.
"""

from pathlib import Path


class Config:
    """Central configuration for the analysis pipeline."""

    # Target stock
    TICKER = "NVDA"

    # Position size for scenario analysis
    NUM_CONTRACTS = 10

    # Option selection criteria
    TARGET_OTM_PCT = 10.0   # Target 10% out-of-the-money
    MIN_OTM_PCT = 5.0       # Minimum OTM percentage
    MAX_OTM_PCT = 20.0      # Maximum OTM percentage
    MIN_OPEN_INTEREST = 100 # Minimum liquidity threshold

    # Paths
    ROOT_DIR = Path(__file__).parent.parent
    DATA_DIR = ROOT_DIR / "data"
    FIGURES_DIR = ROOT_DIR / "figures"
    REPORTS_DIR = ROOT_DIR / "reports"

    # Ensure directories exist
    FIGURES_DIR.mkdir(exist_ok=True)
    REPORTS_DIR.mkdir(exist_ok=True)

    # Chart styling
    COLORS = {
        'primary': '#1a237e',    # Deep blue
        'secondary': '#2e7d32',  # Green
        'negative': '#c62828',   # Red
        'neutral': '#616161',    # Gray
        'light': '#e8eaf6',      # Light blue
    }

    CHART_DPI = 150
    CHART_STYLE = 'seaborn-v0_8-whitegrid'
