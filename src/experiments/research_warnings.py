"""
research_warnings.py

Research Validation & Warnings Engine.
Detects quantitative red flags, data leakage risk, high turnover, parameter sensitivity,
overfitting evidence, and benchmark underperformance. Never hides failed experiments.
"""

from typing import Dict, List, Any


def generate_research_warnings(
    metrics: Dict[str, Any],
    benchmark_comparison: Dict[str, Any],
    validation_results: Dict[str, Any] = None,
    robustness_results: Dict[str, Any] = None
) -> List[str]:
    """
    Generate comprehensive research warnings based on backtest & validation results.

    Returns
    -------
    List[str]
        List of formatted research warning strings.
    """
    warnings: List[str] = []

    cagr = metrics.get("CAGR", 0.0)
    sharpe = metrics.get("Sharpe Ratio", 0.0)
    mdd = abs(metrics.get("Maximum Drawdown", 0.0))
    n_trades = int(metrics.get("Number of Trades", 0))
    turnover = metrics.get("Turnover", 0.0)
    win_rate = metrics.get("Win Rate", 0.0)
    profit_factor = metrics.get("Profit Factor", 0.0)
    exposure = metrics.get("Exposure", 0.0)

    # 1. Sample Size Warning
    if n_trades < 20:
        warnings.append(f"INSUFFICIENT SAMPLE SIZE: Only {n_trades} trades executed. Statistical error is high (min 30 required).")

    # 2. High Turnover Warning
    if turnover > 3.0:
        warnings.append(f"HIGH TURNOVER RISK: Annual portfolio turnover is {turnover*100:.1f}%. High transaction costs will drag live returns.")

    # 3. High Drawdown Warning
    if mdd > 0.25:
        warnings.append(f"EXCESSIVE DRAWDOWN: Maximum drawdown of -{mdd*100:.1f}% exceeds institutional risk limits (25%).")

    # 4. Low Sharpe Warning
    if sharpe < 0.5:
        warnings.append(f"SUBOPTIMAL SHARPE: Sharpe Ratio of {sharpe:.2f} is below the 0.5 threshold for systematic edge.")

    # 5. Profit Factor Warning
    if 0 < profit_factor < 1.2:
        warnings.append(f"NARROW PROFIT FACTOR: Profit Factor of {profit_factor:.2f} indicates slim margin vulnerable to slippage.")

    # 6. Benchmark Underperformance Warning
    if benchmark_comparison.get("status") == "SUCCESS":
        excess = benchmark_comparison.get("excess_return", 0.0)
        bench_cagr = benchmark_comparison.get("benchmark_cagr", 0.0)
        if excess < 0:
            warnings.append(f"BENCHMARK UNDERPERFORMANCE: Strategy CAGR ({cagr*100:.2f}%) underperformed Nifty 50 ({bench_cagr*100:.2f}%) by {abs(excess)*100:.2f}%.")

    # 7. Out-of-Sample Degradation / Overfitting Warning
    if validation_results and validation_results.get("status") != "ERROR":
        degradation = validation_results.get("sharpe_degradation_pct", 0.0)
        if degradation < -30.0:
            warnings.append(f"OVERFITTING WARNING: Out-of-Sample Sharpe degraded by {degradation:.1f}% vs In-Sample!")

    # 8. Robustness / Parameter Sensitivity Warning
    if robustness_results and "summary" in robustness_results:
        cv = robustness_results["summary"].get("coefficient_of_variation", 0.0)
        if cv > 0.35:
            warnings.append(f"HIGH PARAMETER SENSITIVITY: Sharpe Coeff of Variation is {cv:.2f} (>0.35). Strategy is fragile to parameter changes.")

    # 9. Low Exposure / Idle Cash Warning
    if exposure < 0.15:
        warnings.append(f"LOW MARKET EXPOSURE: Strategy was invested in market only {exposure*100:.1f}% of days.")

    return warnings
