from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class MarketDataset:
    rows: list[dict[str, Any]]
    feature_columns: list[str]
    target_column: str
    metadata: dict[str, Any]
