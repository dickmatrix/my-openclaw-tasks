import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from polymarket_lewm.config import RuntimeConfig
from polymarket_lewm.predict import predict_from_api
from polymarket_lewm.strategy import RiskConfig, StrategyEngine


def main() -> None:
    config = RuntimeConfig()
    prediction = predict_from_api(config)
    strategy = StrategyEngine(RiskConfig())
    backtest = strategy.backtest(prediction.rows)

    report = {
        "status": "ok",
        "rows": len(prediction.rows),
        "events": len({str(row["event_id"]) for row in prediction.rows}),
        "backtest": backtest,
    }
    out = config.output_dir / "selfcheck.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2))
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
