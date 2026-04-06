from __future__ import annotations

from collections import defaultdict

import numpy as np
import torch

from polymarket_lewm.config import RuntimeConfig
from polymarket_lewm.model_config import LeWMConfig

FEATURE_ORDER = [
    "price",
    "volume",
    "liquidity",
    "implied_probability",
    "price_return_1",
    "volume_change_1",
    "seconds_to_end",
    "description_length",
]
ACTION_ORDER = ["price_return_1", "volume_change_1", "implied_probability"]


def build_sequences(rows: list[dict[str, object]], config: RuntimeConfig, model_config: LeWMConfig) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    by_event: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in rows:
        by_event[str(row["event_id"])].append(row)
    features: list[np.ndarray] = []
    actions: list[np.ndarray] = []
    targets: list[float] = []
    length = config.lookback + 1
    for group in by_event.values():
        group = sorted(group, key=lambda item: str(item["timestamp"]))
        if len(group) < length:
            continue
        for idx in range(len(group) - length + 1):
            window = group[idx : idx + length]
            features.append(np.array([[float(item[key]) for key in FEATURE_ORDER] for item in window], dtype=np.float32))
            actions.append(np.array([[float(item[key]) for key in ACTION_ORDER] for item in window], dtype=np.float32))
            targets.append(float(window[-1]["target_probability"]))
    if not features:
        return (
            torch.zeros((1, config.lookback + 1, model_config.feature_dim), dtype=torch.float32),
            torch.zeros((1, config.lookback + 1, model_config.action_dim), dtype=torch.float32),
            torch.zeros((1,), dtype=torch.float32),
        )
    return (
        torch.tensor(np.stack(features), dtype=torch.float32),
        torch.tensor(np.stack(actions), dtype=torch.float32),
        torch.tensor(np.array(targets), dtype=torch.float32),
    )
