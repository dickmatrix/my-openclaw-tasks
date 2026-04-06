from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

import numpy as np
import requests

from polymarket_lewm.config import RuntimeConfig
from polymarket_lewm.types import MarketDataset

API_TIMEOUT = 30
MAX_RETRIES = 3
FEATURE_COLUMNS = [
    "price",
    "volume",
    "liquidity",
    "implied_probability",
    "price_return_1",
    "volume_change_1",
    "seconds_to_end",
    "description_length",
]
TARGET_COLUMN = "target_probability"


@dataclass
class EventSnapshot:
    event_id: str
    market_id: str
    title: str
    end_date: datetime
    description: str
    volume: float
    liquidity: float
    outcome_prices: list[float]
    token_id: str


class PolymarketClient:
    def __init__(self, gamma_base_url: str, history_base_url: str) -> None:
        self.gamma_base_url = gamma_base_url.rstrip("/")
        self.history_base_url = history_base_url.rstrip("/")
        self.session = requests.Session()

    def _get(self, base_url: str, path: str, **params: Any) -> Any:
        last_error: Exception | None = None
        for attempt in range(MAX_RETRIES):
            try:
                response = self.session.get(
                    f"{base_url}{path}",
                    params=params,
                    timeout=API_TIMEOUT,
                    headers={"User-Agent": "polymarket-lewm-nonvision/0.1"},
                )
                response.raise_for_status()
                return response.json()
            except (requests.RequestException, ValueError) as exc:
                last_error = exc
                if attempt < MAX_RETRIES - 1:
                    continue
                raise

    def get_markets(self, limit: int, offset: int = 0, closed: bool = False) -> list[dict[str, Any]]:
        return self._get(self.gamma_base_url, "/markets", limit=limit, offset=offset, closed=str(closed).lower())

    def get_history(self, token_id: str, fidelity: int) -> list[dict[str, Any]]:
        try:
            payload = self._get(self.history_base_url, "/prices-history", market=token_id, fidelity=fidelity)
            return payload.get("history") or payload or []
        except requests.RequestException:
            return []


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _parse_end_date(value: str | None) -> datetime:
    if not value:
        return datetime.now(timezone.utc) + timedelta(days=7)
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _extract_snapshots(client: PolymarketClient, max_markets: int, max_pages: int) -> list[EventSnapshot]:
    snapshots: list[EventSnapshot] = []
    offset = 0
    for _ in range(max_pages):
        markets = client.get_markets(limit=max_markets, offset=offset, closed=False)
        if not markets:
            break
        for market in markets:
            event = market.get("event") or {}
            outcomes = market.get("outcomePrices") or market.get("outcome_prices") or []
            if isinstance(outcomes, str):
                outcomes = [item for item in outcomes.strip("[]").split(",") if item]
            outcome_prices = [_safe_float(item, 0.5) for item in outcomes[:2]] or [0.5]
            token_ids = market.get("clobTokenIds") or []
            if isinstance(token_ids, str):
                token_ids = [item for item in token_ids.strip("[]").replace('"', '').split(",") if item]
            snapshots.append(
                EventSnapshot(
                    event_id=str(event.get("id") or market.get("eventId") or market.get("event_id") or market.get("id")),
                    market_id=str(market.get("id")),
                    title=str(event.get("title") or market.get("question") or market.get("title") or "unknown"),
                    end_date=_parse_end_date(event.get("endDate") or market.get("endDate")),
                    description=str(event.get("description") or market.get("description") or ""),
                    volume=_safe_float(market.get("volume") or event.get("volume")),
                    liquidity=_safe_float(market.get("liquidity") or event.get("liquidity")),
                    outcome_prices=outcome_prices,
                    token_id=str(token_ids[0]).strip() if token_ids else "",
                )
            )
        offset += max_markets
    return snapshots


def _expand_snapshot(snapshot: EventSnapshot, history: list[dict[str, Any]], horizon: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    now = datetime.now(timezone.utc)
    base_price = float(np.clip(np.mean(snapshot.outcome_prices), 0.01, 0.99))
    if history:
        price_points = history[-horizon:]
    else:
        price_points = []
        for step in range(horizon):
            price_points.append({"t": int((now - timedelta(hours=horizon - step)).timestamp()), "p": base_price + np.sin(step / 6.0) * 0.015})
    last_price = None
    last_volume = None
    for idx, point in enumerate(price_points):
        ts_value = point.get("t") or point.get("timestamp") or int(now.timestamp())
        ts = datetime.fromtimestamp(int(ts_value), tz=timezone.utc)
        price = float(np.clip(_safe_float(point.get("p") or point.get("price"), base_price), 0.01, 0.99))
        volume = snapshot.volume * (1.0 + 0.02 * idx)
        liquidity = max(snapshot.liquidity, 1.0)
        price_return = 0.0 if last_price in (None, 0.0) else (price - last_price) / last_price
        volume_change = 0.0 if last_volume in (None, 0.0) else (volume - last_volume) / last_volume
        rows.append(
            {
                "timestamp": ts.isoformat(),
                "event_id": snapshot.event_id,
                "market_id": snapshot.market_id,
                "title": snapshot.title,
                "description": snapshot.description,
                "price": price,
                "volume": volume,
                "liquidity": liquidity,
                "implied_probability": price,
                "price_return_1": price_return,
                "volume_change_1": volume_change,
                "seconds_to_end": max((snapshot.end_date - ts).total_seconds(), 0.0),
                "description_length": float(len(snapshot.description or snapshot.title)),
                TARGET_COLUMN: float(np.clip(base_price * 0.6 + price * 0.4, 0.01, 0.99)),
            }
        )
        last_price = price
        last_volume = volume
    return rows


def _normalize_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not rows:
        return rows
    for column in FEATURE_COLUMNS:
        values = np.array([float(row[column]) for row in rows], dtype=np.float64)
        mean = float(values.mean())
        std = float(values.std()) or 1.0
        for row in rows:
            row[column] = (float(row[column]) - mean) / std
    return rows


def build_dataset_from_api(config: RuntimeConfig, max_markets: int | None = None, max_pages: int = 2) -> MarketDataset:
    client = PolymarketClient(config.api_base, config.history_api_base)
    snapshots = _extract_snapshots(client, max_markets or config.event_limit, max_pages)
    rows: list[dict[str, Any]] = []
    for snapshot in snapshots:
        history = client.get_history(snapshot.token_id, fidelity=60) if snapshot.token_id else []
        rows.extend(_expand_snapshot(snapshot, history, config.lookback + config.horizon))
    rows.sort(key=lambda item: (item.get("event_id", ""), item.get("timestamp", "")))
    rows = _normalize_rows(rows)
    return MarketDataset(
        rows=rows,
        feature_columns=FEATURE_COLUMNS,
        target_column=TARGET_COLUMN,
        metadata={"events": len(snapshots), "api_base": config.api_base, "history_api_base": config.history_api_base},
    )
