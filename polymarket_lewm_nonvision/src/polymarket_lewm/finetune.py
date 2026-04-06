from __future__ import annotations

from dataclasses import asdict

import numpy as np
import torch
from torch import nn
from torch.utils.data import DataLoader, TensorDataset

from polymarket_lewm.calibration import ProbabilityCalibrator
from polymarket_lewm.checkpoint import save_model
from polymarket_lewm.config import RuntimeConfig
from polymarket_lewm.data import build_dataset_from_api
from polymarket_lewm.dataset_utils import build_sequences
from polymarket_lewm.io_utils import save_json
from polymarket_lewm.model import NonVisualLeWorldModel
from polymarket_lewm.model_config import LeWMConfig


def run_finetune() -> dict[str, object]:
    runtime = RuntimeConfig()
    config = LeWMConfig()
    dataset = build_dataset_from_api(runtime)
    features, actions, targets = build_sequences(dataset.rows, runtime, config)
    loader = DataLoader(TensorDataset(features, actions, targets), batch_size=runtime.batch_size, shuffle=True)

    model = NonVisualLeWorldModel(config)
    optimizer = torch.optim.AdamW(model.parameters(), lr=runtime.lr)
    bce = nn.BCELoss()
    model.train()

    losses: list[float] = []
    for _ in range(runtime.epochs):
        for feature_batch, action_batch, target_batch in loader:
            output = model(feature_batch, action_batch)
            prob_loss = bce(output["probability"], target_batch)
            loss = output["loss"] + prob_loss
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            losses.append(float(loss.detach().item()))

    model.eval()
    with torch.no_grad():
        raw_prob, confidence = model.infer(features, actions)
    raw_scores = raw_prob.detach().cpu().numpy()
    target_scores = targets.detach().cpu().numpy()
    calibrator = ProbabilityCalibrator()
    calibrator.fit(raw_scores, target_scores)
    calibrated = calibrator.transform(raw_scores)

    ckpt_path = runtime.weights_dir / "lewm_polymarket.pt"
    save_model(model, config, ckpt_path)
    np.save(runtime.weights_dir / "calibrator_scores.npy", calibrated)

    report = {
        "rows": int(len(dataset.rows)),
        "samples": int(features.size(0)),
        "loss": float(np.mean(losses) if losses else 0.0),
        "weights": str(ckpt_path),
        "avg_probability": float(np.mean(calibrated)),
        "avg_confidence": float(confidence.mean().item()),
        "config": asdict(config),
    }
    save_json(runtime.output_dir / "finetune_report.json", report)
    return report
