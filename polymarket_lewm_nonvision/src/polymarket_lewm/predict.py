from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import torch

from polymarket_lewm.checkpoint import load_or_init_model
from polymarket_lewm.config import RuntimeConfig
from polymarket_lewm.dataset_utils import ACTION_ORDER, FEATURE_ORDER
from polymarket_lewm.model import NonVisualLeWorldModel
from polymarket_lewm.model_config import LeWMConfig


@dataclass
class PredictionResult:
    rows: list[dict[str, Any]]


def _build_window_tensor(window: list[dict[str, object]], feature_dim: int, action_dim: int) -> tuple[torch.Tensor, torch.Tensor]:
    features = torch.tensor(
        [[float(item[key]) for key in FEATURE_ORDER] for item in window],
        dtype=torch.float32,
    ).view(1, len(window), feature_dim)
    actions = torch.tensor(
        [[float(item[key]) for key in ACTION_ORDER] for item in window],
        dtype=torch.float32,
    ).view(1, len(window), action_dim)
    return features, actions


def attach_model_predictions(
    rows: list[dict[str, object]],
    runtime: RuntimeConfig,
    model: NonVisualLeWorldModel,
    model_config: LeWMConfig,
) -> PredictionResult:
    if not rows:
        return PredictionResult(rows=[])

    grouped: dict[str, list[dict[str, object]]] = {}
    for row in rows:
        event_id = str(row["event_id"])
        grouped.setdefault(event_id, []).append(dict(row))

    model.eval()
    output: list[dict[str, Any]] = []

    for group in grouped.values():
        group.sort(key=lambda item: str(item["timestamp"]))
        length = runtime.lookback + 1
        if len(group) < length:
            for row in group:
                row["model_probability"] = float(row["implied_probability"])
                row["model_confidence"] = 0.0
                output.append(row)
            continue

        for idx in range(len(group)):
            if idx < length - 1:
                group[idx]["model_probability"] = float(group[idx]["implied_probability"])
                group[idx]["model_confidence"] = 0.0
                continue
            window = group[idx - (length - 1) : idx + 1]
            features, actions = _build_window_tensor(window, model_config.feature_dim, model_config.action_dim)
            probability, confidence = model.infer(features, actions)
            group[idx]["model_probability"] = float(probability.squeeze(0).item())
            group[idx]["model_confidence"] = float(confidence.squeeze(0).item())

        output.extend(group)

    output.sort(key=lambda item: (str(item["event_id"]), str(item["timestamp"])))
    return PredictionResult(rows=output)


def predict_from_api(runtime: RuntimeConfig) -> PredictionResult:
    model, model_config, _ = load_or_init_model(runtime.weights_dir)
    from polymarket_lewm.data import build_dataset_from_api

    dataset = build_dataset_from_api(runtime)
    return attach_model_predictions(dataset.rows, runtime, model, model_config)
