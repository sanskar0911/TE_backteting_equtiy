"""
analyzer.py

Structured LLM strategy analyzer module.
Produces structured JSON investment ratings and risk assessments from backtest metrics.
"""

import os
import sys
import json
from typing import Dict, Any

# Ensure path imports work
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from llm.prompts import ANALYSIS_SYSTEM_PROMPT, ANALYSIS_USER_PROMPT_TEMPLATE


class LLMStrategyAnalyzer:
    """Analyzes quantitative backtest results using LLM or rule-based synthesis."""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY") or os.getenv("GEMINI_API_KEY")

    def format_prompt(self, metrics: Dict[str, Any], ticker: str, strategy: str) -> str:
        """Format the user prompt template with calculated metrics."""
        return ANALYSIS_USER_PROMPT_TEMPLATE.format(
            ticker=ticker,
            strategy=strategy,
            total_return=metrics.get("Total Return", 0.0) * 100.0,
            cagr=metrics.get("CAGR", 0.0) * 100.0,
            volatility=metrics.get("Annual Volatility", 0.0) * 100.0,
            sharpe=metrics.get("Sharpe Ratio", 0.0),
            sortino=metrics.get("Sortino Ratio", 0.0),
            calmar=metrics.get("Calmar Ratio", 0.0),
            max_drawdown=metrics.get("Maximum Drawdown", 0.0) * 100.0,
            win_rate=metrics.get("Win Rate", 0.0) * 100.0,
            profit_factor=metrics.get("Profit Factor", 0.0),
            holding_period=metrics.get("Average Holding Period", 0.0),
            num_trades=int(metrics.get("Number of Trades", 0))
        )

    def analyze_performance(self, metrics: Dict[str, Any], ticker: str = "INFY", strategy: str = "SMA") -> Dict[str, Any]:
        """
        Analyze strategy performance metrics and return structured JSON assessment.
        """
        user_prompt = self.format_prompt(metrics, ticker, strategy)

        # 1. Attempt LLM API call if key is present
        if self.api_key:
            # 1a. Try OpenAI SDK
            try:
                import openai
                client = openai.OpenAI(api_key=self.api_key)
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": ANALYSIS_SYSTEM_PROMPT},
                        {"role": "user", "content": user_prompt}
                    ],
                    response_format={"type": "json_object"}
                )
                res_content = response.choices[0].message.content
                return json.loads(res_content)
            except Exception as e1:
                # 1b. Try Gemini API if available
                try:
                    import google.generativeai as genai
                    genai.configure(api_key=self.api_key)
                    model = genai.GenerativeModel("gemini-1.5-flash")
                    prompt = f"{ANALYSIS_SYSTEM_PROMPT}\n\n{user_prompt}"
                    res = model.generate_content(prompt)
                    clean_text = res.text.strip().replace("```json", "").replace("```", "").strip()
                    return json.loads(clean_text)
                except Exception as e2:
                    print(f"[LLM Analyzer Note] API calls unconfigured or failed ({e1} | {e2}). Using Next-Level Quantitative Rule Engine.")

        # 2. Advanced Quantitative Rule Engine Fallback
        return self._generate_rule_based_analysis(metrics, ticker, strategy)

    def _generate_rule_based_analysis(self, metrics: Dict[str, Any], ticker: str, strategy: str) -> Dict[str, Any]:
        sharpe = metrics.get("Sharpe Ratio", 0.0)
        sortino = metrics.get("Sortino Ratio", 0.0)
        cagr = metrics.get("CAGR", 0.0)
        max_dd = abs(metrics.get("Maximum Drawdown", 0.0))
        win_rate = metrics.get("Win Rate", 0.0)
        profit_factor = metrics.get("Profit Factor", 0.0)
        volatility = metrics.get("Annual Volatility", 0.0)

        # Advanced Rating Logic
        if sharpe > 1.2 and cagr > 0.15 and max_dd < 0.18:
            rating = "Strong Buy"
            confidence = 0.95
        elif sharpe > 0.5 and cagr > 0.06 and max_dd < 0.30:
            rating = "Moderate Buy"
            confidence = 0.88
        elif sharpe >= 0.0:
            rating = "Neutral"
            confidence = 0.78
        else:
            rating = "Underperform"
            confidence = 0.92

        # Risk Rating Logic
        if max_dd > 0.30 or volatility > 0.25:
            risk = "High"
        elif max_dd > 0.15 or volatility > 0.15:
            risk = "Moderate"
        else:
            risk = "Low"

        # Strengths & Weaknesses
        strengths = []
        weaknesses = []

        if sharpe > 0.8:
            strengths.append(f"Strong risk-adjusted returns with Sharpe ratio of {sharpe:.2f}.")
        if win_rate > 0.50:
            strengths.append(f"Healthy win rate of {win_rate*100:.1f}%.")
        if profit_factor > 1.3:
            strengths.append(f"Robust Profit Factor of {profit_factor:.2f}.")
        if sortino > 1.0:
            strengths.append(f"Excellent downside risk control with Sortino ratio of {sortino:.2f}.")

        if max_dd > 0.20:
            weaknesses.append(f"Significant peak-to-trough drawdown of {max_dd*100:.2f}%.")
        if profit_factor < 1.1:
            weaknesses.append(f"Low profit factor of {profit_factor:.2f} indicates narrow edge.")
        if cagr < 0.05:
            weaknesses.append(f"Subdued annualized growth (CAGR {cagr*100:.2f}%).")

        if not strengths:
            strengths.append("Provides systematic algorithmic signals eliminating emotional bias.")
        if not weaknesses:
            weaknesses.append("Past backtest performance may experience slippage in live trading.")

        # Market Regime & Optimization Suggestions
        if strategy == "SMA":
            regime = "Strong trending bull/bear markets with sustained price direction."
            param_advice = "Consider tuning short/long window ratios or adding ADX filter to eliminate false crossovers during ranging markets."
        elif strategy == "EMA":
            regime = "Momentum-driven trending environments requiring faster reaction time."
            param_advice = "Combine fast/slow EMA with volume confirmation to reduce whipsaws in choppy markets."
        elif strategy == "RSI":
            regime = "Mean-reverting, range-bound markets with clear overbought/oversold boundaries."
            param_advice = "Adjust oversold/overbought thresholds (e.g. 25/75 instead of 30/70) or add a trend filter."
        else:
            regime = "General multi-regime market conditions."
            param_advice = "Optimize stop-loss and take-profit parameters via automated grid search."

        # Sizing Advice
        if risk == "High":
            sizing_advice = "Limit capital allocation to 5%-10% per trade. Implement tight stop-loss (3%-5%)."
        elif risk == "Moderate":
            sizing_advice = "Maintain standard position sizing of 15%-20% per trade with 5% trailing stop-loss."
        else:
            sizing_advice = "Allocation can be safely increased up to 25%-30% per position with periodic rebalancing."

        recommendation = (
            f"The {strategy} strategy on {ticker} achieved a CAGR of {cagr*100:.2f}% with a Sharpe ratio of {sharpe:.2f} "
            f"and max drawdown of {max_dd*100:.2f}%. Win rate stood at {win_rate*100:.1f}% with Profit Factor {profit_factor:.2f}. "
            f"Overall rating is {rating} with {risk.lower()} risk profile."
        )

        return {
            "rating": rating,
            "risk": risk,
            "confidence": confidence,
            "recommendation": recommendation,
            "strengths": strengths,
            "weaknesses": weaknesses,
            "market_regime_suitability": regime,
            "suggested_param_adjustments": param_advice,
            "position_sizing_advice": sizing_advice
        }


if __name__ == "__main__":
    print("Testing LLMStrategyAnalyzer...")
    analyzer = LLMStrategyAnalyzer()
    mock_metrics = {
        "Total Return": 0.25,
        "CAGR": 0.08,
        "Annual Volatility": 0.18,
        "Sharpe Ratio": 0.65,
        "Sortino Ratio": 0.82,
        "Calmar Ratio": 0.45,
        "Maximum Drawdown": -0.18,
        "Win Rate": 0.55,
        "Profit Factor": 1.45,
        "Average Holding Period": 12.5,
        "Number of Trades": 14
    }
    result = analyzer.analyze_performance(mock_metrics, "INFY", "SMA")
    print("Generated Structured JSON:")
    print(json.dumps(result, indent=2))
