from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import os


@dataclass
class RuntimeConfig:
    input_dir: Path = field(default_factory=lambda: Path("/workspace/input"))
    output_dir: Path = field(default_factory=lambda: Path("/workspace/output"))
    data_dir: Path = field(default_factory=lambda: Path("/workspace/data"))
    weights_dir: Path = field(default_factory=lambda: Path("/workspace/weights"))
    api_base: str = "https://gamma-api.polymarket.com"
    history_api_base: str = "https://clob.polymarket.com"
    event_limit: int = field(default_factory=lambda: int(os.getenv("POLYMARKET_EVENT_LIMIT", "50")))
    horizon: int = 24
    lookback: int = 64
    batch_size: int = 16
    epochs: int = 3
    lr: float = 3e-4
    risk_freeze_days: int = 2
    max_position_pct: float = 0.05
    max_daily_drawdown: float = 0.10
    threshold: float = 0.08
