from __future__ import annotations

from polymarket_lewm.config import RuntimeConfig
from polymarket_lewm.io_utils import save_json
from polymarket_lewm.predict import predict_from_api
from polymarket_lewm.strategy import RiskConfig, StrategyEngine


def run_backtest() -> dict[str, object]:
    runtime = RuntimeConfig()
    prediction = predict_from_api(runtime)
    strategy = StrategyEngine(
        RiskConfig(
            max_position_pct=runtime.max_position_pct,
            max_daily_drawdown=runtime.max_daily_drawdown,
            freeze_days_before_resolution=runtime.risk_freeze_days,
            signal_threshold=runtime.threshold,
        )
    )
    report = strategy.backtest(prediction.rows)
    save_json(runtime.output_dir / "backtest_report.json", report)
    return report
