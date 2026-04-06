from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime

import numpy as np


@dataclass
class RiskConfig:
    max_position_pct: float = 0.05
    max_daily_drawdown: float = 0.10
    freeze_days_before_resolution: int = 2
    signal_threshold: float = 0.08
    starting_equity: float = 100000.0


class StrategyEngine:
    def __init__(self, risk: RiskConfig) -> None:
        self.risk = risk

    def generate_signals(self, rows: list[dict[str, object]]) -> list[dict[str, object]]:
        if not rows:
            return []

        grouped: dict[str, list[dict[str, object]]] = defaultdict(list)
        for row in rows:
            grouped[str(row["event_id"])].append(dict(row))

        output: list[dict[str, object]] = []
        for group in grouped.values():
            group.sort(key=lambda item: str(item["timestamp"]))
            for row in group:
                implied = float(row["implied_probability"])
                model_probability = float(row.get("model_probability", implied))
                edge = model_probability - implied
                days_to_end = float(row["seconds_to_end"]) / 86400.0
                allowed = days_to_end > self.risk.freeze_days_before_resolution and abs(edge) >= self.risk.signal_threshold
                signal = float(np.sign(edge)) if allowed else 0.0
                row["model_probability"] = model_probability
                row["edge"] = edge
                row["days_to_end"] = days_to_end
                row["allowed"] = allowed
                row["signal"] = signal
                output.append(row)

        output.sort(key=lambda item: (str(item["event_id"]), str(item["timestamp"])))
        return output

    def backtest(self, rows: list[dict[str, object]]) -> dict[str, float]:
        signals = self.generate_signals(rows)
        if not signals:
            return {"equity": self.risk.starting_equity, "return": 0.0, "max_drawdown": 0.0, "trades": 0.0}

        equity = self.risk.starting_equity
        peak = equity
        max_drawdown = 0.0
        trades = 0
        current_day = None
        daily_pnl = 0.0

        for row in signals:
            day = datetime.fromisoformat(str(row["timestamp"]).replace("Z", "+00:00")).date()
            if current_day != day:
                current_day = day
                daily_pnl = 0.0

            if float(row["signal"]) == 0.0:
                continue

            if daily_pnl <= -self.risk.max_daily_drawdown * self.risk.starting_equity:
                continue

            position = equity * self.risk.max_position_pct
            pnl = position * float(row["signal"]) * (float(row["target_probability"]) - float(row["implied_probability"]))
            daily_pnl += pnl
            equity += pnl
            peak = max(peak, equity)
            if peak > 0:
                max_drawdown = min(max_drawdown, (equity - peak) / peak)
            trades += 1

        return {
            "equity": float(equity),
            "return": float((equity - self.risk.starting_equity) / self.risk.starting_equity),
            "max_drawdown": float(abs(max_drawdown)),
            "trades": float(trades),
        }

    def latest_signal(self, rows: list[dict[str, object]]) -> dict[str, float | str | bool]:
        signals = self.generate_signals(rows)
        if not signals:
            return {"signal": "flat", "allowed": False, "edge": 0.0}

        latest = signals[-1]
        signal = "flat"
        if float(latest["signal"]) > 0:
            signal = "long_yes"
        elif float(latest["signal"]) < 0:
            signal = "long_no"

        return {
            "event_id": str(latest["event_id"]),
            "market_id": str(latest["market_id"]),
            "signal": signal,
            "allowed": bool(latest["allowed"]),
            "edge": float(latest["edge"]),
            "days_to_end": float(latest["days_to_end"]),
            "model_probability": float(latest.get("model_probability", latest["implied_probability"])),
            "model_confidence": float(latest.get("model_confidence", 0.0)),
        }
