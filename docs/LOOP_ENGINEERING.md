# Loop Engineering in LangGraph Agent Workflow

## Overview

Rather than running an uncontrolled loop that blindly optimizes parameters to maximize historical Sharpe ratio (which leads to severe overfitting), the framework implements **Loop Engineering** inside the LangGraph workflow (`src/agent/workflow.py`).

---

## 1. Loop Architecture State Machine

```
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
```

---

## 2. Decision State Rules

At each iteration, the **Research Evaluator** node inspects strategy performance and determines one of five loop decisions:

| Decision | Trigger Condition | Action Taken |
| :--- | :--- | :--- |
| **`VALIDATE`** | Baseline iteration completed | Proceed to Out-of-Sample Validation & Robustness analysis |
| **`ITERATE`** | Sharpe < target or Excess Return < 0, and `iteration < max_iterations` | Trigger controlled parameter variation for next research run |
| **`ACCEPT`** | Sharpe $\ge$ target, Excess Return $> 0$, OOS validation passed, and robust | Strategy accepted; proceed to Fact Sheet generation |
| **`STOP`** | Maximum iterations reached (`iteration >= max_iterations`) | Stop research loop to prevent uncontrolled optimization |
| **`FAIL`** | Look-ahead bias or severe data leakage detected | Terminate workflow immediately and log failure reason |

---

## 3. Stopping Criteria & Guardrails

The research loop will **never** run endlessly. Execution halts immediately upon meeting any of the following guardrails:
1. **Maximum Iterations Cap**: Configurable limit (`max_iterations=3`).
2. **Acceptable Validation Result**: Strategy achieves target Sharpe and passes OOS validation.
3. **Data Leakage Flag**: Look-ahead audit failure.
4. **Overfitting Warning**: Severe degradation between In-Sample and Out-of-Sample returns.

All iteration steps, parameter changes, Sharpe ratios, excess returns, and research warnings are logged chronologically in `experiment_history`.
