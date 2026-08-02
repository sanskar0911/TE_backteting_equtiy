# Professional Equity Quantitative Backtesting & AI Analytics System

A production-grade, modular Python Equity Backtesting and AI-driven Quantitative Analysis framework for NSE stock equities.

---

## 📁 Complete Project Structure & File Directory

```text
TE_backteting_equtiy-main/
│
├── README.md                      # Comprehensive system architecture & file documentation
├── AI_CODING_REPORT.md            # AI engineering report on prompt design & code reviews
├── requirements.txt               # External Python package dependencies
├── index.html                     # Web UI static dashboard template
│
├── data/                          # Market data repository
│   ├── raw/                       # Raw OHLCV CSV data downloaded via yfinance
│   └── processed/                 # Cleaned and validated CSV data for backtesting
│       ├── INFY.csv
│       ├── RELIANCE.csv
│       ├── TCS.csv
│       ├── HDFCBANK.csv
│       └── ICICIBANK.csv
│
├── notebooks/                     # Interactive Jupyter Notebooks
│   ├── EDA.ipynb                  # Exploratory Data Analysis & returns correlation notebook
│   └── Backtesting.ipynb          # Step-by-step strategy backtest tutorial notebook
│
├── results/                       # Backtest output artifacts
│   ├── signals.csv                # Strategy indicators and signal log
│   ├── portfolio.csv              # Daily equity tracking log
│   ├── trade_log.csv              # Executed trades log
│   ├── summary.txt                # Formatted text performance summary
│   ├── signals_chart.png          # Stock price & signal markers plot
│   ├── equity_curve.png           # Portfolio growth vs initial capital plot
│   ├── drawdown.png               # Underwater drawdown chart
│   ├── rolling_sharpe.png         # Rolling 60-day annualized Sharpe Ratio chart
│   ├── monthly_returns.png        # Monthly returns breakdown bar chart
│   ├── trade_dist.png             # Histogram of completed trade returns
│   └── allocation.png             # Stacked area asset allocation chart (Cash vs Equity)
│
└── src/                           # Core Source Code Engine
    ├── __init__.py
    ├── main.py                    # Main orchestrator CLI & pipeline runner
    ├── app.py                     # Interactive Streamlit Web Dashboard & server fallback
    ├── backtester.py              # Enhanced simulation engine (costs, position sizing, SL/TP)
    ├── strategy.py                # Facade module delegating to strategy library
    ├── metrics.py                 # Quantitative KPIs & risk metrics calculator
    ├── visualization.py           # Publication-grade chart generation engine
    ├── report.py                  # Automated text summary report generator
    ├── data_loader.py             # YFinance historical market data loader
    ├── clean_data.py              # Data cleaning, missing value handler & validator
    ├── utils.py                   # Shared calculation helper utilities
    │
    ├── strategies/                # Modular Strategy Library (Strategy Factory Pattern)
    │   ├── __init__.py
    │   ├── base.py                # Abstract Base Strategy interface (BaseStrategy)
    │   ├── sma_crossover.py       # Simple Moving Average Crossover Strategy (SMA)
    │   ├── ema_crossover.py       # Exponential Moving Average Crossover Strategy (EMA)
    │   ├── rsi_strategy.py        # Relative Strength Index Strategy (RSI)
    │   └── factory.py             # Strategy Factory class (StrategyFactory)
    │
    ├── llm/                       # LLM Strategy Analysis Engine
    │   ├── __init__.py
    │   ├── prompts.py             # Structured financial prompts & JSON output schemas
    │   └── analyzer.py            # LLM analyzer module (returns JSON rating, risk, confidence)
    │
    └── agent/                     # LangGraph Agent Workflow
        ├── __init__.py
        └── workflow.py            # Node-based agent workflow (StateGraph execution)
```

---

## 📄 File-by-File Detailed Responsibilities

### Root Directory
- **`README.md`**: Primary documentation detailing repository layout, file functions, and execution commands.
- **`AI_CODING_REPORT.md`**: Detailed report covering Cursor prompt engineering, GitHub Copilot utilization, code reviews, and hallucination management.
- **`requirements.txt`**: Complete list of Python libraries needed (`pandas`, `numpy`, `matplotlib`, `yfinance`, `streamlit`, `langchain-core`, `langgraph`, `openai`).
- **`index.html`**: HTML web view dashboard interface.

### `src/` Core Modules
- **`src/main.py`**: The CLI entry point. Orchestrates the execution pipeline (`run_pipeline` / `run_agent_workflow`) with configurable strategy, capital, commission, position size, and SL/TP flags.
- **`src/app.py`**: Interactive Streamlit Dashboard application (`streamlit run src/app.py`). Features sidebar control sliders, KPI cards, analytical charts, trade log tables, and report downloads.
- **`src/backtester.py`**: Backtest execution engine. Computes cash balances, share counts, transaction commissions (`txn_cost_rate`), execution slippage (`slippage_rate`), position sizing (`position_size`), stop loss (`stop_loss`), take profit (`take_profit`), and generates trade logs.
- **`src/strategy.py`**: Facade module maintaining backward-compatible functions `calculate_indicators()` and `generate_signals()` while routing calls to `StrategyFactory`.
- **`src/metrics.py`**: Quantitative metrics calculator computing Total Return, CAGR, Volatility, Sharpe Ratio, Sortino Ratio, Calmar Ratio, Max Drawdown, Win Rate, Profit Factor, Average Holding Period, Average Trade Return, Turnover, Exposure, and Daily Hit Ratio.
- **`src/visualization.py`**: Chart plotter producing high-DPI matplotlib plots for Signals, Equity Curve, Drawdowns, Rolling Sharpe, Monthly Returns, Trade Return Distribution, and Asset Allocation.
- **`src/report.py`**: Generates text reports (`summary.txt`) documenting portfolio returns, risk metrics, trade statistics, and strategy parameters.
- **`src/data_loader.py`**: Downloads raw daily OHLCV data from Yahoo Finance (`.NS` tickers) into `data/raw/`.
- **`src/clean_data.py`**: Parses dates, removes duplicates, handles missing values, sorts chronologically, and saves processed CSVs to `data/processed/`.
- **`src/utils.py`**: Helper utilities for moving averages, percentage returns, and missing data summaries.

### `src/strategies/` Strategy Library
- **`src/strategies/base.py`**: Defines abstract class `BaseStrategy` with mandatory `calculate_indicators()` and `generate_signals()` interface contracts.
- **`src/strategies/sma_crossover.py`**: `SMACrossoverStrategy` for fast/slow Simple Moving Average crossovers.
- **`src/strategies/ema_crossover.py`**: `EMACrossoverStrategy` for fast/slow Exponential Moving Average crossovers.
- **`src/strategies/rsi_strategy.py`**: `RSIStrategy` for oversold (<30) buying and overbought (>70) selling.
- **`src/strategies/factory.py`**: `StrategyFactory` class implementing the Strategy Factory pattern for dynamic strategy lookup (`StrategyFactory.get_strategy("SMA")`).

### `src/llm/` LLM Analysis Engine
- **`src/llm/prompts.py`**: Prompt templates instructing the LLM to analyze performance metrics and return structured JSON.
- **`src/llm/analyzer.py`**: `LLMStrategyAnalyzer` module that executes API prompts (or fallback rule engines) and returns structured JSON: `{ "rating", "risk", "recommendation", "confidence" }`.

### `src/agent/` LangGraph Workflow Engine
- **`src/agent/workflow.py`**: Implements the node-based workflow (`Load Data` ➔ `Run Strategy` ➔ `Run Backtest` ➔ `Calculate Metrics` ➔ `Generate Charts` ➔ `Call LLM` ➔ `Generate Report`) using LangGraph `StateGraph`.

### `notebooks/`
- **`notebooks/EDA.ipynb`**: Exploratory Data Analysis notebook for returns distributions and correlations.
- **`notebooks/Backtesting.ipynb`**: Interactive tutorial notebook for building, testing, and plotting custom trading strategies.

---

## 🚀 Execution & Usage Guide

### 1. Installation
```bash
pip install -r requirements.txt
```

### 2. Run Main CLI Orchestrator
```bash
python src/main.py RELIANCE --strategy SMA --position-size 0.2 --stop-loss 0.05 --take-profit 0.10
```

### 3. Launch Streamlit Web Dashboard
```bash
streamlit run src/app.py
```

### 4. Run LangGraph Agent Workflow directly
```bash
python src/agent/workflow.py
```

---

*Engineered with Python, Streamlit, Matplotlib, LangChain, and LangGraph.*
