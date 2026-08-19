"""
workflow.py

Research-Oriented LangGraph Agent Workflow with Controlled Loop Engineering.

Architecture Flow:
                 HYPOTHESIS
                     ↓
                  BASELINE
                     ↓
                 BACKTEST
                     ↓
                  METRICS & BENCHMARK
                     ↓
             RESEARCH EVALUATOR
                     ↓
             ┌───────┴────────┐
             │                │
            PASS           ITERATE
             │                │
             ▼                ▼
         VALIDATION      NEW EXPERIMENT
             │                │
             ▼                ▼
       OOS TESTING        BACKTEST
             │                │
             └───────┬────────┘
                     ↓
              RESEARCH EVALUATOR
                     ↓
           FACT SHEET & REPORT
"""

import os
import sys
from typing import Dict, Any, TypedDict, Optional, List
import pandas as pd

# Ensure local path imports work
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC_DIR = os.path.join(BASE_DIR, "src")
if SRC_DIR not in sys.path:
    sys.path.append(SRC_DIR)

from strategy import generate_signals
from backtester import run_backtest
from metrics import calculate_metrics
from benchmark import compare_strategy_vs_benchmark, load_benchmark_data
from experiments.runner import Experiment
from experiments.out_of_sample import run_out_of_sample_validation
from experiments.robustness import run_robustness_analysis
from experiments.regime_analysis import run_regime_analysis
from experiments.research_warnings import generate_research_warnings
from visualization import (
    plot_signals,
    plot_equity_curve,
    plot_drawdown,
    plot_rolling_sharpe,
    plot_monthly_returns,
    plot_trade_distribution,
    plot_portfolio_allocation
)
from report import generate_summary_report
from llm.analyzer import LLMStrategyAnalyzer

# Try importing LangGraph
try:
    from langgraph.graph import StateGraph, END
    HAS_LANGGRAPH = True
except ImportError:
    HAS_LANGGRAPH = False


class BacktestState(TypedDict):
    experiment_id: str
    hypothesis: str
    ticker: str
    strategy_name: str
    strategy_kwargs: Dict[str, Any]
    initial_capital: float
    commission_pct: float
    slippage_pct: float
    position_size: float
    max_positions: int
    rebalance_freq: str
    stop_loss: Optional[float]
    take_profit: Optional[float]
    min_volume: float
    min_traded_value: float
    min_price: float
    benchmark_symbol: str
    
    price_df: Optional[pd.DataFrame]
    benchmark_df: Optional[pd.DataFrame]
    signals_df: Optional[pd.DataFrame]
    portfolio_df: Optional[pd.DataFrame]
    trade_log_df: Optional[pd.DataFrame]
    
    metrics: Optional[Dict[str, Any]]
    benchmark_comparison: Optional[Dict[str, Any]]
    validation_result: Optional[Dict[str, Any]]
    robustness_result: Optional[Dict[str, Any]]
    regime_result: Optional[Dict[str, Any]]
    warnings: List[str]
    llm_analysis: Optional[Dict[str, Any]]
    
    results_dir: str
    report_path: str
    iteration: int
    max_iterations: int
    loop_decision: str # "ACCEPT", "ITERATE", "VALIDATE", "STOP", "FAIL"
    experiment_history: List[Dict[str, Any]]
    final_conclusion: str


# --- Node Implementations ---

def node_load_data(state: BacktestState) -> BacktestState:
    """Node 1: Load stock and benchmark data."""
    ticker = state["ticker"]
    file_path = os.path.join(BASE_DIR, "data", "processed", f"{ticker}.csv")
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Data file for {ticker} not found at {file_path}")

    df = pd.read_csv(file_path, index_col="Date")
    df.index = pd.to_datetime(df.index)
    state["price_df"] = df

    try:
        b_df = load_benchmark_data(state.get("benchmark_symbol", "NIFTY50"))
        state["benchmark_df"] = b_df
    except Exception:
        state["benchmark_df"] = None

    print(f"[Node 1: Load Data] Loaded {len(df)} price rows for {ticker}")
    return state


def node_run_backtest(state: BacktestState) -> BacktestState:
    """Node 2: Calculate indicators, signals, and run backtest simulation."""
    price_df = state["price_df"]
    strat_name = state["strategy_name"]
    strat_kwargs = state.get("strategy_kwargs", {})

    signals_df = generate_signals(price_df, strategy_name=strat_name, **strat_kwargs)
    state["signals_df"] = signals_df

    portfolio_df, trade_log_df = run_backtest(
        signals_df,
        initial_capital=state.get("initial_capital", 100000.0),
        txn_cost_rate=state.get("commission_pct", 0.001),
        slippage_rate=state.get("slippage_pct", 0.0005),
        position_size=state.get("position_size", 0.2),
        stop_loss=state.get("stop_loss"),
        take_profit=state.get("take_profit"),
        min_volume=state.get("min_volume", 0.0),
        min_traded_value=state.get("min_traded_value", 0.0),
        min_price=state.get("min_price", 0.0),
        max_positions=state.get("max_positions", 10),
        rebalance_freq=state.get("rebalance_freq", "Daily")
    )

    state["portfolio_df"] = portfolio_df
    state["trade_log_df"] = trade_log_df
    print(f"[Node 2: Backtest] Iteration {state.get('iteration', 1)}: Backtest executed. Trades: {len(trade_log_df)}")
    return state


def node_calculate_metrics(state: BacktestState) -> BacktestState:
    """Node 3: Compute quantitative performance and benchmark metrics."""
    portfolio_df = state["portfolio_df"]
    trade_log_df = state["trade_log_df"]
    capital = state.get("initial_capital", 100000.0)

    metrics = calculate_metrics(portfolio_df, trade_log_df, initial_capital=capital)
    state["metrics"] = metrics

    bench_comp = compare_strategy_vs_benchmark(
        portfolio_df,
        state.get("benchmark_df"),
        benchmark_symbol=state.get("benchmark_symbol", "NIFTY50"),
        initial_capital=capital
    )
    state["benchmark_comparison"] = bench_comp

    print(f"[Node 3: Metrics] Sharpe: {metrics['Sharpe Ratio']:.2f}, CAGR: {metrics['CAGR']*100:.2f}%, Excess Return: {bench_comp.get('excess_return', 0.0)*100:.2f}%")
    return state


def node_research_evaluator(state: BacktestState) -> BacktestState:
    """
    Node 4: Research Evaluator - Decision State Machine.
    Evaluates:
    1. Did experiment satisfy hypothesis?
    2. Did strategy beat benchmark?
    3. Is performance stable?
    4. Is there evidence of overfitting or data leakage?
    5. Is another iteration justified?
    """
    curr_iter = state.get("iteration", 1)
    max_iter = state.get("max_iterations", 3)
    metrics = state.get("metrics") or {}
    bench_comp = state.get("benchmark_comparison") or {}

    sharpe = metrics.get("Sharpe Ratio", 0.0)
    cagr = metrics.get("CAGR", 0.0)
    excess = bench_comp.get("excess_return", 0.0)

    # Generate warnings for current iteration
    warnings = generate_research_warnings(
        metrics, bench_comp,
        validation_results=state.get("validation_result"),
        robustness_results=state.get("robustness_result")
    )
    state["warnings"] = warnings

    # Record iteration history
    history_entry = {
        "iteration": curr_iter,
        "strategy": state["strategy_name"],
        "params": dict(state.get("strategy_kwargs", {})),
        "sharpe": sharpe,
        "cagr": cagr,
        "excess_return": excess,
        "warnings": list(warnings)
    }
    history = list(state.get("experiment_history") or [])
    history.append(history_entry)
    state["experiment_history"] = history

    # Loop Decision Rules
    if curr_iter == 1:
        # After baseline run, move to validation
        state["loop_decision"] = "VALIDATE"
        print(f"[Research Evaluator] Baseline completed (Sharpe: {sharpe:.2f}). Proceeding to Validation stage.")
    elif curr_iter < max_iter and (sharpe < 0.5 or excess < 0.0):
        # Controlled iteration if target not reached
        state["loop_decision"] = "ITERATE"
        print(f"[Research Evaluator] Iteration {curr_iter}: Sharpe {sharpe:.2f} / Excess Return {excess*100:.2f}%. Controlled iteration triggered.")
    elif curr_iter >= max_iter:
        state["loop_decision"] = "STOP"
        print(f"[Research Evaluator] Reached max iterations ({max_iter}). Stopping research loop.")
    else:
        state["loop_decision"] = "ACCEPT"
        print(f"[Research Evaluator] Strategy passed research evaluation criteria (Sharpe: {sharpe:.2f}). Accepted!")

    return state


def node_controlled_iteration(state: BacktestState) -> BacktestState:
    """Node 5: Controlled parameter variation for next research iteration."""
    curr_iter = state.get("iteration", 1) + 1
    state["iteration"] = curr_iter

    strat_name = state["strategy_name"]
    strat_kwargs = dict(state.get("strategy_kwargs", {}))

    print(f"[Controlled Iteration] Preparing Iteration {curr_iter} parameter adjustment...")

    if strat_name == "SMA":
        strat_kwargs["short_window"] = strat_kwargs.get("short_window", 20) + 10
        strat_kwargs["long_window"] = strat_kwargs.get("long_window", 50) + 20
    elif strat_name == "EMA":
        strat_kwargs["short_window"] = strat_kwargs.get("short_window", 12) + 5
        strat_kwargs["long_window"] = strat_kwargs.get("long_window", 26) + 10
    elif strat_name == "RSI":
        strat_kwargs["overbought"] = max(65, strat_kwargs.get("overbought", 70) - 2)
        strat_kwargs["oversold"] = min(35, strat_kwargs.get("oversold", 30) + 2)

    state["strategy_kwargs"] = strat_kwargs
    print(f"[Controlled Iteration] New params: {strat_kwargs}")
    return state


def node_run_validation(state: BacktestState) -> BacktestState:
    """Node 6: Execute Out-of-Sample Split, Robustness & Regime Analysis."""
    price_df = state["price_df"]
    strat_name = state["strategy_name"]
    strat_kwargs = state.get("strategy_kwargs", {})

    print("[Node 6: Validation] Running Out-of-Sample Split & Robustness tests...")

    # 1. Out of sample validation
    oos_res = run_out_of_sample_validation(
        price_df,
        strategy_name=strat_name,
        strategy_params=strat_kwargs,
        initial_capital=state.get("initial_capital", 100000.0),
        txn_cost_rate=state.get("commission_pct", 0.001),
        slippage_rate=state.get("slippage_pct", 0.0005),
        position_size=state.get("position_size", 0.2)
    )
    state["validation_result"] = oos_res

    # 2. Robustness analysis
    rob_res = run_robustness_analysis(
        price_df,
        strategy_name=strat_name,
        baseline_params=strat_kwargs,
        initial_capital=state.get("initial_capital", 100000.0),
        baseline_txn_cost=state.get("commission_pct", 0.001),
        baseline_slippage=state.get("slippage_pct", 0.0005),
        baseline_position_size=state.get("position_size", 0.2)
    )
    state["robustness_result"] = rob_res

    # 3. Market Regime Analysis
    if state.get("benchmark_df") is not None and state.get("portfolio_df") is not None:
        reg_res = run_regime_analysis(
            state["portfolio_df"],
            state["trade_log_df"],
            state["benchmark_df"],
            initial_capital=state.get("initial_capital", 100000.0)
        )
        state["regime_result"] = reg_res

    return state


def route_evaluator_decision(state: BacktestState) -> str:
    """Conditional Edge based on loop_decision."""
    decision = state.get("loop_decision", "STOP")
    if decision == "ITERATE":
        return "iterate"
    elif decision == "VALIDATE":
        return "validate"
    return "finalize"


def node_generate_artifacts(state: BacktestState) -> BacktestState:
    """Node 7: Render visual charts, call LLM analyzer, and write summary report."""
    ticker = state["ticker"]
    signals_df = state["signals_df"]
    portfolio_df = state["portfolio_df"]
    trade_log_df = state["trade_log_df"]
    res_dir = state.get("results_dir", os.path.join(BASE_DIR, "results"))
    os.makedirs(res_dir, exist_ok=True)

    plot_signals(signals_df, ticker, os.path.join(res_dir, "signals_chart.png"))
    plot_equity_curve(portfolio_df, ticker, os.path.join(res_dir, "equity_curve.png"))
    plot_drawdown(portfolio_df, os.path.join(res_dir, "drawdown.png"))
    plot_rolling_sharpe(portfolio_df, os.path.join(res_dir, "rolling_sharpe.png"))
    plot_monthly_returns(portfolio_df, os.path.join(res_dir, "monthly_returns.png"))
    plot_trade_distribution(trade_log_df, os.path.join(res_dir, "trade_dist.png"))
    plot_portfolio_allocation(portfolio_df, os.path.join(res_dir, "allocation.png"))

    # LLM Strategy Analysis
    analyzer = LLMStrategyAnalyzer()
    llm_analysis = analyzer.analyze_performance(state["metrics"], ticker, state["strategy_name"])
    state["llm_analysis"] = llm_analysis

    # Final Text Summary Report
    report_path = os.path.join(res_dir, "summary.txt")
    config = {
        "strategy_name": f"{state['strategy_name']} Strategy",
        "stock_ticker": ticker,
        "start_date": state["price_df"].index.min().strftime("%Y-%m-%d"),
        "end_date": state["price_df"].index.max().strftime("%Y-%m-%d"),
        "initial_capital": state.get("initial_capital", 100000.0),
        "final_value": portfolio_df["Portfolio Value"].iloc[-1]
    }
    generate_summary_report(state["metrics"], config, report_path)
    state["report_path"] = report_path

    print(f"[Node 7: Artifacts] Charts and summary report generated at {report_path}")
    return state


# --- Build LangGraph StateGraph ---

def build_agent_graph():
    """Build and compile the research-oriented LangGraph agent workflow."""
    if not HAS_LANGGRAPH:
        return None

    builder = StateGraph(BacktestState)

    builder.add_node("load_data", node_load_data)
    builder.add_node("run_backtest", node_run_backtest)
    builder.add_node("calculate_metrics", node_calculate_metrics)
    builder.add_node("research_evaluator", node_research_evaluator)
    builder.add_node("controlled_iteration", node_controlled_iteration)
    builder.add_node("run_validation", node_run_validation)
    builder.add_node("generate_artifacts", node_generate_artifacts)

    builder.set_entry_point("load_data")

    builder.add_edge("load_data", "run_backtest")
    builder.add_edge("run_backtest", "calculate_metrics")
    builder.add_edge("calculate_metrics", "research_evaluator")

    # Conditional decision routing from Research Evaluator
    builder.add_conditional_edges(
        "research_evaluator",
        route_evaluator_decision,
        {
            "iterate": "controlled_iteration",
            "validate": "run_validation",
            "finalize": "generate_artifacts"
        }
    )

    builder.add_edge("controlled_iteration", "run_backtest")
    builder.add_edge("run_validation", "generate_artifacts")
    builder.add_edge("generate_artifacts", END)

    return builder.compile()


def run_agent_workflow(
    ticker: str = "INFY",
    strategy_name: str = "SMA",
    initial_capital: float = 100000.0,
    commission_pct: float = 0.001,
    slippage_pct: float = 0.0005,
    position_size: float = 0.2,
    max_positions: int = 10,
    rebalance_freq: str = "Daily",
    stop_loss: Optional[float] = 0.05,
    take_profit: Optional[float] = 0.10,
    benchmark_symbol: str = "NIFTY50",
    max_iterations: int = 3,
    hypothesis: str = "Test quantitative momentum edge on Indian equities",
    **strategy_kwargs
) -> BacktestState:
    """Execute research-oriented agent workflow."""
    initial_state: BacktestState = {
        "experiment_id": f"EXP_{ticker}_{strategy_name}",
        "hypothesis": hypothesis,
        "ticker": ticker,
        "strategy_name": strategy_name,
        "strategy_kwargs": strategy_kwargs or ({"short_window": 20, "long_window": 50} if strategy_name == "SMA" else {}),
        "initial_capital": initial_capital,
        "commission_pct": commission_pct,
        "slippage_pct": slippage_pct,
        "position_size": position_size,
        "max_positions": max_positions,
        "rebalance_freq": rebalance_freq,
        "stop_loss": stop_loss,
        "take_profit": take_profit,
        "min_volume": 0.0,
        "min_traded_value": 0.0,
        "min_price": 0.0,
        "benchmark_symbol": benchmark_symbol,
        "price_df": None,
        "benchmark_df": None,
        "signals_df": None,
        "portfolio_df": None,
        "trade_log_df": None,
        "metrics": None,
        "benchmark_comparison": None,
        "validation_result": None,
        "robustness_result": None,
        "regime_result": None,
        "warnings": [],
        "llm_analysis": None,
        "results_dir": os.path.join(BASE_DIR, "results"),
        "report_path": "",
        "iteration": 1,
        "max_iterations": max_iterations,
        "loop_decision": "PENDING",
        "experiment_history": [],
        "final_conclusion": ""
    }

    graph = build_agent_graph()
    if graph:
        print("Executing Research Workflow via LangGraph StateGraph...")
        return graph.invoke(initial_state)
    else:
        print("Executing Research Workflow via Autonomous Evaluator Loop...")
        s = node_load_data(initial_state)
        while True:
            s = node_run_backtest(s)
            s = node_calculate_metrics(s)
            s = node_research_evaluator(s)
            route = route_evaluator_decision(s)
            if route == "iterate":
                s = node_controlled_iteration(s)
            elif route == "validate":
                s = node_run_validation(s)
                break
            else:
                break
        s = node_generate_artifacts(s)
        return s


if __name__ == "__main__":
    print("Testing Research LangGraph Workflow with Loop Engineering...")
    final_state = run_agent_workflow("RELIANCE", "SMA", max_iterations=2)
    print("\nWorkflow Execution Complete!")
    print(f"Final Loop Decision: {final_state['loop_decision']}")
    print(f"Total Iterations: {final_state['iteration']}")
    print(f"Warnings Logged: {len(final_state['warnings'])}")
