from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class ProbabilityCalibrator:
    fallback: float = 0.5
    slope: float = 1.0
    intercept: float = 0.0
    is_fitted: bool = False

    def fit(self, scores: np.ndarray, targets: np.ndarray) -> None:
        if len(scores) < 2:
            return
        x = np.asarray(scores, dtype=np.float64)
        y = np.asarray(targets, dtype=np.float64)
        A = np.vstack([x, np.ones(len(x))]).T
        self.slope, self.intercept = np.linalg.lstsq(A, y, rcond=None)[0]
        self.is_fitted = True

    def transform(self, scores: np.ndarray) -> np.ndarray:
        x = np.asarray(scores, dtype=np.float64)
        if not self.is_fitted:
            return np.clip(x, 0.0, 1.0)
        return np.clip(x * self.slope + self.intercept, 0.0, 1.0)
