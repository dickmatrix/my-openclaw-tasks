from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

import torch

from polymarket_lewm.model import NonVisualLeWorldModel
from polymarket_lewm.model_config import LeWMConfig


def load_or_init_model(weights_dir: Path) -> tuple[NonVisualLeWorldModel, LeWMConfig, Path]:
    weights_dir.mkdir(parents=True, exist_ok=True)
    ckpt_path = weights_dir / "lewm_polymarket.pt"
    config = LeWMConfig()
    model = NonVisualLeWorldModel(config)
    if ckpt_path.exists():
        payload = torch.load(ckpt_path, map_location="cpu")
        if "config" in payload and isinstance(payload["config"], dict):
            capacity = float(payload["config"].get("capacity_scalar", 1.0))
            config = LeWMConfig(capacity_scalar=capacity)
            model = NonVisualLeWorldModel(config)
        model.load_state_dict(payload["state_dict"])
    return model, config, ckpt_path


def save_model(model: NonVisualLeWorldModel, config: LeWMConfig, ckpt_path: Path) -> None:
    ckpt_path.parent.mkdir(parents=True, exist_ok=True)
    torch.save({"state_dict": model.state_dict(), "config": {"capacity_scalar": config.capacity_scalar}}, ckpt_path)
