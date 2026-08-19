"""
portfolio.py

Portfolio management, liquidity filtering, position cap enforcement,
and rebalancing schedule engine for equity backtesting.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Any, Optional


class LiquidityFilter:
    """Evaluates whether a security meets liquidity constraints before entry."""

    def __init__(
        self,
        min_avg_daily_volume: float = 10000.0,
        min_avg_traded_value: float = 500000.0, # e.g. INR 5 Lakhs
        min_price: float = 10.0
    ):
        self.min_avg_daily_volume = min_avg_daily_volume
        self.min_avg_traded_value = min_avg_traded_value
        self.min_price = min_price

    def evaluate(self, price: float, volume: float, avg_volume_20d: float) -> Tuple[bool, str]:
        """
        Check liquidity parameters.

        Returns
        -------
        Tuple[bool, str]
            (is_eligible, reason)
        """
        if price < self.min_price:
            return False, f"Price INR {price:.2f} < Min Price INR {self.min_price:.2f}"

        if volume < self.min_avg_daily_volume and avg_volume_20d < self.min_avg_daily_volume:
            return False, f"Volume {volume:,.0f} < Min Volume {self.min_avg_daily_volume:,.0f}"

        traded_val = price * volume
        avg_traded_val = price * avg_volume_20d
        if traded_val < self.min_avg_traded_value and avg_traded_val < self.min_avg_traded_value:
            return False, f"Traded Value INR {traded_val:,.0f} < Min Value INR {self.min_avg_traded_value:,.0f}"

        return True, "Liquidity Passed"


class RebalanceSchedule:
    """Manages rebalancing schedule triggers (Daily, Weekly, Monthly)."""

    @staticmethod
    def is_rebalance_date(current_date: pd.Timestamp, prev_date: Optional[pd.Timestamp], freq: str = "Daily") -> bool:
        """
        Determine if today is a rebalance date according to selected frequency.
        Ensures strict historical determination without future leakage.
        """
        freq_lower = freq.lower().strip()
        if freq_lower in ["daily", "d"]:
            return True
        if prev_date is None:
            return True

        if freq_lower in ["weekly", "w"]:
            # Rebalance on calendar week change (e.g., Monday or first trading day of week)
            return current_date.isocalendar()[1] != prev_date.isocalendar()[1]
        elif freq_lower in ["monthly", "m"]:
            # Rebalance on calendar month change
            return current_date.month != prev_date.month
        
        return True


class PositionAllocator:
    """
    Deterministic signal ranking and position limit manager.
    Applies deterministic selection rule when active signals > max_positions.
    """

    def __init__(self, max_positions: int = 10, ranking_metric: str = "momentum"):
        self.max_positions = max_positions
        self.ranking_metric = ranking_metric

    def filter_and_rank_signals(
        self,
        candidate_signals: List[Dict[str, Any]]
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Rank candidate buy signals deterministically and trim to max_positions limit.

        Parameters
        ----------
        candidate_signals : List[Dict[str, Any]]
            List of candidate signal dicts containing 'ticker', 'signal_score' (e.g. 20-day return).

        Returns
        -------
        Tuple[List[Dict], List[Dict]]
            (accepted_signals, rejected_signals)
        """
        if len(candidate_signals) <= self.max_positions:
            for sig in candidate_signals:
                sig["rank_reason"] = "Within max position limit"
            return candidate_signals, []

        # Sort deterministically by ranking score descending (highest momentum / signal strength first)
        sorted_candidates = sorted(
            candidate_signals,
            key=lambda x: (x.get("score", 0.0), x.get("ticker", "")),
            reverse=True
        )

        accepted = []
        rejected = []

        for idx, sig in enumerate(sorted_candidates):
            if idx < self.max_positions:
                sig["rank_reason"] = f"Accepted (Rank {idx+1}/{len(candidate_signals)})"
                accepted.append(sig)
            else:
                sig["rank_reason"] = f"Rejected: Exceeded max position limit of {self.max_positions} (Rank {idx+1})"
                rejected.append(sig)

        return accepted, rejected
