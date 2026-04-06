from __future__ import annotations

from polymarket_lewm.config import RuntimeConfig
from polymarket_lewm.data import build_dataset_from_api


if __name__ == "__main__":
    config = RuntimeConfig()
    dataset = build_dataset_from_api(config)
    print(dataset.frame.head())
