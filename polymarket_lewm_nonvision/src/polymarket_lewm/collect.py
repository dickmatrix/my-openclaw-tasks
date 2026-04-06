from __future__ import annotations

import csv
from pathlib import Path

from polymarket_lewm.config import RuntimeConfig
from polymarket_lewm.data import build_dataset_from_api
from polymarket_lewm.io_utils import save_json


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("")
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def run_collection() -> dict[str, object]:
    config = RuntimeConfig()
    dataset = build_dataset_from_api(config)
    json_path = config.data_dir / "polymarket_events.json"
    csv_path = config.data_dir / "polymarket_events.csv"
    save_json(json_path, {"rows": dataset.rows, "metadata": dataset.metadata})
    _write_csv(csv_path, dataset.rows)
    report = {
        "rows": len(dataset.rows),
        "events": dataset.metadata.get("events", 0),
        "json": str(json_path),
        "csv": str(csv_path),
        "features": dataset.feature_columns,
    }
    save_json(config.output_dir / "collection_report.json", report)
    return report
