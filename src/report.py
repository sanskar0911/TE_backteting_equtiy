"""
report.py

Generates a formatted text summary report of the backtest execution, including
key performance metrics, risk metrics, trading statistics, strategy details, and assumptions.
"""

import os
import sys
from typing import Dict, Any

# Ensure local imports work
sys.path.append(os.path.abspath(os.path.dirname(__file__)))


def generate_summary_report(
    metrics: Dict[str, Any],
    config: Dict[str, Any],
    output_path: str
) -> None:
    """
    Format and write backtesting results into a professional text report file.

    Parameters
    ----------
    metrics : Dict[str, Any]
        Dictionary of calculated backtesting performance KPIs (from metrics.py).
    config : Dict[str, Any]
        Dictionary containing configuration details (e.g., Stock, Date Range, etc.).
    output_path : str
        File path where the summary.txt will be saved.
    """
    strategy_name = config.get("strategy_name", "SMA Crossover (20/50)")
    stock_ticker = config.get("stock_ticker", "Unknown Ticker")
    start_date = config.get("start_date", "N/A")
    end_date = config.get("end_date", "N/A")
    initial_capital = config.get("initial_capital", 100000.0)
    final_value = config.get("final_value", 100000.0)

    # Prepare and format strategy metrics
    total_return_pct = metrics.get("Total Return", 0.0) * 100.0
    cagr_pct = metrics.get("CAGR", 0.0) * 100.0
    ann_vol_pct = metrics.get("Annual Volatility", 0.0) * 100.0
    sharpe_ratio = metrics.get("Sharpe Ratio", 0.0)
    sortino_ratio = metrics.get("Sortino Ratio", 0.0)
    max_drawdown_pct = metrics.get("Maximum Drawdown", 0.0) * 100.0
    turnover_pct = metrics.get("Turnover", 0.0) * 100.0
    exposure_pct = metrics.get("Exposure", 0.0) * 100.0
    hit_ratio_pct = metrics.get("Hit Ratio", 0.0) * 100.0
    
    # Trade statistics
    win_rate_pct = metrics.get("Win Rate", 0.0) * 100.0
    avg_win_pct = metrics.get("Average Win", 0.0) * 100.0
    avg_loss_pct = metrics.get("Average Loss", 0.0) * 100.0
    num_trades = metrics.get("Number of Trades", 0)

    report_content = f"""================================================================================
BACKTESTING SYSTEM - STRATEGY SUMMARY REPORT
================================================================================
Strategy Name         : {strategy_name}
Stock Ticker          : {stock_ticker}
Date Range            : {start_date} to {end_date}
================================================================================

PORTFOLIO PERFORMANCE & RISK METRICS:
--------------------------------------------------------------------------------
Initial Capital        : INR {initial_capital:,.2f}
Final Portfolio Value  : INR {final_value:,.2f}
Total Return           : {total_return_pct:.2f}%
CAGR (Ann. Compound)   : {cagr_pct:.2f}%
Annualized Volatility  : {ann_vol_pct:.2f}%
Sharpe Ratio (Rf=0)    : {sharpe_ratio:.2f}
Sortino Ratio (Rf=0)   : {sortino_ratio:.2f}
Maximum Drawdown       : {max_drawdown_pct:.2f}%
Market Exposure        : {exposure_pct:.2f}%
Portfolio Turnover     : {turnover_pct:.2f}%
Daily Hit Ratio        : {hit_ratio_pct:.2f}%

TRADING STATISTICS:
--------------------------------------------------------------------------------
Total Executed Trades  : {int(num_trades)}
Trade Win Rate         : {win_rate_pct:.2f}%
Average Winning Trade  : {avg_win_pct:.2f}%
Average Losing Trade   : {avg_loss_pct:.2f}%

STRATEGY ASSUMPTIONS & PARAMETERS:
--------------------------------------------------------------------------------
1. Long-Only Execution: The strategy only buys and holds long positions.
2. Full Position Size: 100% of available cash is deployed, rounded to whole shares.
3. No Fractional Shares: Only whole shares are transacted on NSE.
4. Transaction Costs: 0.10% (0.001) fee applied to all trade volumes.
5. Execution Slippage: 0.05% (0.0005) price markup on buy, discount on sell.
6. Execution Timing: Trades executed at Adjusted Close price on signal date.
7. No Leverage: Portfolio runs with a leverage factor of 1.0 (no margin debt).
8. Single Position: Only one active position is held at any given time.

================================================================================
Report generated automatically by Backtesting Equity System.
================================================================================
"""
    # Create directory if it does not exist
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, "w") as f:
        f.write(report_content)


if __name__ == "__main__":
    print("Testing report.py writer...")
    mock_metrics = {
        "Total Return": 0.219,
        "CAGR": 0.0404,
        "Annual Volatility": 0.1797,
        "Sharpe Ratio": 0.31,
        "Sortino Ratio": 0.45,
        "Maximum Drawdown": -0.4353,
        "Win Rate": 0.3125,
        "Turnover": 0.125,
        "Exposure": 0.5065,
        "Hit Ratio": 0.521,
        "Average Win": 0.1560,
        "Average Loss": -0.0433,
        "Number of Trades": 16.0,
    }
    
    mock_config = {
        "strategy_name": "SMA Crossover (20/50)",
        "stock_ticker": "RELIANCE.NS",
        "start_date": "2020-01-01",
        "end_date": "2024-12-31",
        "initial_capital": 100000.0,
        "final_value": 121900.48
    }
    
    test_out = "results_test/summary_test.txt"
    generate_summary_report(mock_metrics, mock_config, test_out)
    print(f"Test report written to {test_out}")
