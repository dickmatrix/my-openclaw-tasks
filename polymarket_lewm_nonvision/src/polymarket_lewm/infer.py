from __future__ import annotations

import numpy as np

from polymarket_lewm.calibration import ProbabilityCalibrator
from polymarket_lewm.checkpoint import load_or_init_model
from polymarket_lewm.config import RuntimeConfig
from polymarket_lewm.data import build_dataset_from_api
from polymarket_lewm.dataset_utils import build_sequences
from polymarket_lewm.io_utils import save_json


def run_inference() -> dict[str, object]:
    runtime = RuntimeConfig()
    model, config, _ = load_or_init_model(runtime.weights_dir)
    dataset = build_dataset_from_api(runtime)
    features, actions, _ = build_sequences(dataset.rows, runtime, config)
    probability, confidence = model.infer(features, actions)

    calibrator = ProbabilityCalibrator()
    scores_path = runtime.weights_dir / "calibrator_scores.npy"
    raw_scores = probability.detach().cpu().numpy()
    if scores_path.exists():
        scores = np.load(scores_path)
        calibrator.fit(raw_scores[: len(scores)], np.clip(scores, 0.0, 1.0))
    calibrated = calibrator.transform(raw_scores)

    report = {
        "samples": int(features.size(0)),
        "probability": float(calibrated[-1]),
        "confidence": float(confidence[-1].item()),
    }
    save_json(runtime.output_dir / "inference_report.json", report)
    return report
