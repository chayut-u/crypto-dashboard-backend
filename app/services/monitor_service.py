import json
import logging
from typing import Any

import httpx
from sqlalchemy.orm import Session

from app.repositories.transaction_repository import TransactionRepository
from app.services.alert_service import AlertService

logger = logging.getLogger(__name__)


class MonitorService:
    def __init__(self, db: Session):
        self.db = db
        self.transaction_repository = TransactionRepository(db)
        self.alert_service = AlertService(db)
        self.endpoints = {
            "buybacks": "https://litdash.xyz/api/buybacks/trades?limit=12&offset=0",
            "transfers": "https://litdash.xyz/api/transfers/recent?days=3",
            "stats": "https://litdash.xyz/api/stats",
            "account": "https://mainnet.zklighter.elliot.ai/api/v1/account?by=index&value=281474976624800",
        }

    async def fetch_json(self, client: httpx.AsyncClient, url: str) -> Any:
        response = await client.get(url)
        response.raise_for_status()
        return response.json()

    def _normalize_items(self, source: str, payload: Any) -> list[dict]:
        if isinstance(payload, list):
            items = payload
        elif isinstance(payload, dict):
            for key in ["data", "items", "results", "trades", "transfers"]:
                if isinstance(payload.get(key), list):
                    items = payload[key]
                    break
            else:
                items = [payload]
        else:
            items = [{"value": str(payload)}]

        normalized = []
        for index, item in enumerate(items):
            item_dict = item if isinstance(item, dict) else {"value": item}
            external_id = str(item_dict.get("id") or item_dict.get("txHash") or item_dict.get("hash") or f"{source}-{index}-{abs(hash(json.dumps(item_dict, sort_keys=True, default=str)))}")
            amount = item_dict.get("amount") or item_dict.get("size") or item_dict.get("value") or item_dict.get("quantity") or 0
            symbol = item_dict.get("symbol") or item_dict.get("asset") or item_dict.get("token") or "UNKNOWN"
            wallet_address = item_dict.get("wallet") or item_dict.get("address") or item_dict.get("from") or item_dict.get("to") or ""
            exchange_name = item_dict.get("exchange") or item_dict.get("venue") or item_dict.get("counterparty") or None
            normalized.append(
                {
                    "source": source,
                    "external_id": external_id,
                    "tx_type": source,
                    "amount": float(amount) if str(amount).replace('.', '', 1).isdigit() else 0.0,
                    "symbol": str(symbol),
                    "wallet_address": str(wallet_address),
                    "exchange_name": str(exchange_name) if exchange_name else None,
                    "raw_payload": item_dict,
                    "description": f"Normalized {source} record",
                }
            )
        return normalized

    async def collect_and_process(self) -> dict:
        stored = 0
        alerts = 0
        stats_snapshot = {}
        async with httpx.AsyncClient(timeout=30.0) as client:
            for source, url in self.endpoints.items():
                try:
                    payload = await self.fetch_json(client, url)
                    if source == "stats":
                        stats_snapshot = payload if isinstance(payload, dict) else {"raw": payload}
                    records = self._normalize_items(source, payload)
                    for record in records:
                        if self.transaction_repository.get_by_external_id(record["external_id"]):
                            continue
                        self.transaction_repository.create(record)
                        stored += 1
                        alert = await self.alert_service.create_alert_if_needed(record)
                        if alert:
                            alerts += 1
                except Exception as exc:
                    logger.exception("Failed to monitor source %s", source)
                    stats_snapshot[f"{source}_error"] = str(exc)
        return {"stored": stored, "alerts": alerts, "stats": stats_snapshot}
