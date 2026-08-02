"""
workflow.py

LangGraph Agent Workflow for the Equity Backtesting System.
Defines explicit graph nodes for:
Load Data -> Run Strategy -> Run Backtest -> Calculate Metrics -> Generate Charts -> Call LLM -> Generate Final Report
"""

import os
import sys
from typing import Dict, Any, TypedDict, Optional
import pandas as pd

# Ensure local imports work
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC_DIR = os.path.join(BASE_DIR, "src")
if SRC_DIR not in sys.path:
    sys.path.append(SRC_DIR)

from strategy import generate_signals
from backtester import run_backtest
from metrics import calculate_metrics
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


# Define Workflow State Schema
class BacktestState(TypedDict):
    ticker: str
    strategy_name: str
    strategy_kwargs: Dict[str, Any]
    initial_capital: float
    commission_pct: float
    position_size: float
    stop_loss: Optional[float]
    take_profit: Optional[float]
    
    price_df: Optional[pd.DataFrame]
    signals_df: Optional[pd.DataFrame]
    portfolio_df: Optional[pd.DataFrame]
    trade_log_df: Optional[pd.DataFrame]
    metrics: Optional[Dict[str, Any]]
    llm_analysis: Optional[Dict[str, Any]]
    results_dir: str
    report_path: str
    optimization_iterations: int
    max_optimization_iterations: int
    target_sharpe: float


# --- Node Functions ---

def node_load_data(state: BacktestState) -> BacktestState:
    """Node 1: Load processed stock data."""
    ticker = state["ticker"]
    file_path = os.path.join(BASE_DIR, "data", "processed", f"{ticker}.csv")
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Data file for {ticker} not found at {file_path}")

    df = pd.read_csv(file_path, index_col="Date")
    df.index = pd.to_datetime(df.index)
    state["price_df"] = df
    print(f"[Node 1: Load Data] Loaded {len(df)} price rows for {ticker}")
    return state


def node_run_strategy(state: BacktestState) -> BacktestState:
    """Node 2: Calculate indicators and generate trading signals."""
    price_df = state["price_df"]
    strat_name = state["strategy_name"]
    strat_kwargs = state.get("strategy_kwargs", {})

    signals_df = generate_signals(price_df, strategy_name=strat_name, **strat_kwargs)
    state["signals_df"] = signals_df
    print(f"[Node 2: Run Strategy] Generated signals using {strat_name} (Params: {strat_kwargs})")
    return state


def node_run_backtest(state: BacktestState) -> BacktestState:
    """Node 3: Execute backtest simulation engine."""
    signals_df = state["signals_df"]
    capital = state.get("initial_capital", 100000.0)
    commission = state.get("commission_pct", 0.001)
    pos_size = state.get("position_size", 0.2)
    sl = state.get("stop_loss", None)
    tp = state.get("take_profit", None)

    portfolio_df, trade_log_df = run_backtest(
        signals_df,
        initial_capital=capital,
        txn_cost_rate=commission,
        slippage_rate=0.0005,
        position_size=pos_size,
        stop_loss=sl,
        take_profit=tp
    )
    state["portfolio_df"] = portfolio_df
    state["trade_log_df"] = trade_log_df
    print(f"[Node 3: Run Backtest] Executed backtest. Trades: {len(trade_log_df)}")
    return state


def node_calculate_metrics(state: BacktestState) -> BacktestState:
    """Node 4: Compute comprehensive KPIs."""
    portfolio_df = state["portfolio_df"]
    trade_log_df = state["trade_log_df"]
    capital = state.get("initial_capital", 100000.0)

    metrics = calculate_metrics(portfolio_df, trade_log_df, initial_capital=capital)
    state["metrics"] = metrics
    print(f"[Node 4: Calculate Metrics] Sharpe: {metrics['Sharpe Ratio']:.2f}, CAGR: {metrics['CAGR']*100:.2f}%")
    return state


def node_optimize_params(state: BacktestState) -> BacktestState:
    """Autonomous Node: Refines strategy parameters if performance falls below targets."""
    curr_iter = state.get("optimization_iterations", 0) + 1
    state["optimization_iterations"] = curr_iter
    strat_name = state["strategy_name"]
    strat_kwargs = dict(state.get("strategy_kwargs", {}))

    print(f"[Node Self-Optimize] Iteration {curr_iter}: Tuning strategy parameters for higher Sharpe ratio...")

    if strat_name == "SMA":
        short = strat_kwargs.get("short_window", 20) + 5
        long_w = strat_kwargs.get("long_window", 50) + 10
        strat_kwargs["short_window"] = short
        strat_kwargs["long_window"] = long_w
    elif strat_name == "EMA":
        short = strat_kwargs.get("short_window", 12) + 3
        long_w = strat_kwargs.get("long_window", 26) + 5
        strat_kwargs["short_window"] = short
        strat_kwargs["long_window"] = long_w
    elif strat_name == "RSI":
        ob = max(65, strat_kwargs.get("overbought", 70) - 2)
        os_level = min(35, strat_kwargs.get("oversold", 30) + 2)
        strat_kwargs["overbought"] = ob
        strat_kwargs["oversold"] = os_level

    # Adjust Stop Loss / Take Profit
    state["stop_loss"] = min(0.08, (state.get("stop_loss") or 0.05) + 0.01)
    state["take_profit"] = min(0.15, (state.get("take_profit") or 0.10) + 0.02)
    state["strategy_kwargs"] = strat_kwargs

    print(f"[Node Self-Optimize] Updated params: {strat_kwargs}, SL: {state['stop_loss']:.2f}, TP: {state['take_profit']:.2f}")
    return state


def should_optimize(state: BacktestState) -> str:
    """Conditional Edge: Checks if strategy optimization loop should trigger."""
    metrics = state.get("metrics") or {}
    sharpe = metrics.get("Sharpe Ratio", 0.0)
    target_sharpe = state.get("target_sharpe", 0.5)
    curr_iter = state.get("optimization_iterations", 0)
    max_iter = state.get("max_optimization_iterations", 2)

    if sharpe < target_sharpe and curr_iter < max_iter:
        print(f"[Agent Reflection] Sharpe {sharpe:.2f} < Target {target_sharpe:.2f}. Triggering Self-Optimization (Iter {curr_iter+1}/{max_iter})...")
        return "optimize"
    print(f"[Agent Reflection] Target performance achieved or max iterations reached. Proceeding to charts and LLM analysis.")
    return "proceed"


def node_generate_charts(state: BacktestState) -> BacktestState:
    """Node 5: Render all performance and analytical plots."""
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

    print(f"[Node 5: Generate Charts] Charts written to {res_dir}")
    return state


def node_call_llm(state: BacktestState) -> BacktestState:
    """Node 6: Synthesize strategy rating via structured LLM module."""
    metrics = state["metrics"]
    ticker = state["ticker"]
    strat_name = state["strategy_name"]

    analyzer = LLMStrategyAnalyzer()
    llm_analysis = analyzer.analyze_performance(metrics, ticker, strat_name)
    state["llm_analysis"] = llm_analysis
    print(f"[Node 6: Call LLM] Rating: {llm_analysis['rating']} (Confidence: {llm_analysis['confidence']})")
    return state


def node_generate_report(state: BacktestState) -> BacktestState:
    """Node 7: Export final text report."""
    metrics = state["metrics"]
    ticker = state["ticker"]
    strat_name = state["strategy_name"]
    price_df = state["price_df"]
    portfolio_df = state["portfolio_df"]
    res_dir = state.get("results_dir", os.path.join(BASE_DIR, "results"))
    report_path = os.path.join(res_dir, "summary.txt")

    config = {
        "strategy_name": f"{strat_name} Strategy",
        "stock_ticker": ticker,
        "start_date": price_df.index.min().strftime("%Y-%m-%d"),
        "end_date": price_df.index.max().strftime("%Y-%m-%d"),
        "initial_capital": state.get("initial_capital", 100000.0),
        "final_value": portfolio_df["Portfolio Value"].iloc[-1]
    }
    generate_summary_report(metrics, config, report_path)
    state["report_path"] = report_path
    print(f"[Node 7: Generate Report] Summary report saved to {report_path}")
    return state


# --- Build LangGraph Agent Workflow ---

def build_agent_graph():
    """Build and compile the LangGraph agent graph if available."""
    if not HAS_LANGGRAPH:
        return None

    builder = StateGraph(BacktestState)

    builder.add_node("load_data", node_load_data)
    builder.add_node("run_strategy", node_run_strategy)
    builder.add_node("run_backtest", node_run_backtest)
    builder.add_node("calculate_metrics", node_calculate_metrics)
    builder.add_node("optimize_params", node_optimize_params)
    builder.add_node("generate_charts", node_generate_charts)
    builder.add_node("call_llm", node_call_llm)
    builder.add_node("generate_report", node_generate_report)

    builder.set_entry_point("load_data")

    builder.add_edge("load_data", "run_strategy")
    builder.add_edge("run_strategy", "run_backtest")
    builder.add_edge("run_backtest", "calculate_metrics")
    
    # Conditional reflection edge
    builder.add_conditional_edges(
        "calculate_metrics",
        should_optimize,
        {
            "optimize": "optimize_params",
            "proceed": "generate_charts"
        }
    )
    builder.add_edge("optimize_params", "run_strategy")

    builder.add_edge("generate_charts", "call_llm")
    builder.add_edge("call_llm", "generate_report")
    builder.add_edge("generate_report", END)

    return builder.compile()


def run_agent_workflow(
    ticker: str = "INFY",
    strategy_name: str = "SMA",
    initial_capital: float = 100000.0,
    commission_pct: float = 0.001,
    position_size: float = 0.2,
    stop_loss: Optional[float] = 0.05,
    take_profit: Optional[float] = 0.10,
    target_sharpe: float = 0.5,
    max_optimization_iterations: int = 2,
    **strategy_kwargs
) -> BacktestState:
    """Execute the full agent workflow sequentially or via LangGraph."""
    initial_state: BacktestState = {
        "ticker": ticker,
        "strategy_name": strategy_name,
        "strategy_kwargs": strategy_kwargs,
        "initial_capital": initial_capital,
        "commission_pct": commission_pct,
        "position_size": position_size,
        "stop_loss": stop_loss,
        "take_profit": take_profit,
        "price_df": None,
        "signals_df": None,
        "portfolio_df": None,
        "trade_log_df": None,
        "metrics": None,
        "llm_analysis": None,
        "results_dir": os.path.join(BASE_DIR, "results"),
        "report_path": "",
        "optimization_iterations": 0,
        "max_optimization_iterations": max_optimization_iterations,
        "target_sharpe": target_sharpe
    }

    graph = build_agent_graph()
    if graph:
        print("Executing Agent Workflow via LangGraph StateGraph...")
        return graph.invoke(initial_state)
    else:
        print("Executing Agent Workflow via Autonomous Reflection Loop...")
        s = node_load_data(initial_state)
        while True:
            s = node_run_strategy(s)
            s = node_run_backtest(s)
            s = node_calculate_metrics(s)
            action = should_optimize(s)
            if action == "optimize":
                s = node_optimize_params(s)
            else:
                break
        s = node_generate_charts(s)
        s = node_call_llm(s)
        s = node_generate_report(s)
        return s


if __name__ == "__main__":
    print("Testing Next-Level LangGraph Agent Workflow...")
    final_state = run_agent_workflow("RELIANCE", "SMA", position_size=0.2, stop_loss=0.05, take_profit=0.10, target_sharpe=0.6)
    print("\nWorkflow Finished Successfully!")
    print(f"Final Report Path: {final_state['report_path']}")
    print(f"AI Rating: {final_state['llm_analysis']['rating']}")
    print(f"Strengths: {final_state['llm_analysis'].get('strengths')}")

