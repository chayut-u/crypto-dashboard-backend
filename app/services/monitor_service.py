import logging
from datetime import datetime, timezone
from typing import Any

import httpx
from sqlalchemy.orm import Session

from app.config import settings
from app.repositories.transaction_repository import TransactionRepository
from app.services.alert_service import AlertService

logger = logging.getLogger(__name__)


class MonitorService:
    def __init__(self, db: Session):
        self.db = db
        self.transaction_repository = TransactionRepository(db)
        self.alert_service = AlertService(db)
        self.endpoints = {
            "buyback_trades": "https://litdash.xyz/api/buybacks/trades?limit=100&offset=0",
            "buyback_daily": "https://litdash.xyz/api/buybacks/daily-summary",
            "llp_transfers": "https://litdash.xyz/api/llp/transfers?limit=100&offset=0",
            "llp_top": "https://litdash.xyz/api/llp/top-wallets",
            "staking_top": "https://litdash.xyz/api/staking/top-wallets",
        }

    async def fetch_json(self, client: httpx.AsyncClient, url: str) -> Any:
        response = await client.get(url)
        response.raise_for_status()
        return response.json()

    def _parse_timestamp(self, value: Any) -> datetime | None:
        if value in (None, ""):
            return None
        if isinstance(value, (int, float)):
            if value > 10_000_000_000:
                value = value / 1000
            return datetime.fromtimestamp(value, tz=timezone.utc)
        if isinstance(value, str):
            cleaned = value.replace("Z", "+00:00")
            try:
                dt = datetime.fromisoformat(cleaned)
            except ValueError:
                return None
            if dt.tzinfo is None:
                return dt.replace(tzinfo=timezone.utc)
            return dt
        return None

    def _to_float(self, value: Any) -> float | None:
        try:
            if value in (None, ""):
                return None
            return float(value)
        except (TypeError, ValueError):
            return None

    def _is_interesting(self, tx: dict) -> tuple[bool, str | None]:
        reasons: list[str] = []
        amount = float(tx.get("amount") or 0)
        quote_amount = float(tx.get("quote_amount") or 0)
        tx_type = str(tx.get("tx_type") or "")
        account_index = str(tx.get("account_index") or "")
        direction = str(tx.get("direction") or "")

        if tx_type == "buyback" and quote_amount >= 5_000:
            reasons.append("large buyback spend")
        if tx_type in {"deposit", "withdraw"} and amount >= 10_000:
            reasons.append("large pool flow")
        if amount >= 50_000:
            reasons.append("large notional size")
        if account_index == settings.buyback_wallet_account_index and tx_type == "buyback":
            reasons.append("buyback program wallet activity")
        if direction in {"in", "out"} and amount >= 25_000:
            reasons.append("significant capital movement")

        return (len(reasons) > 0, "; ".join(reasons) if reasons else None)

    def _build_record(
        self,
        *,
        source: str,
        category: str,
        external_id: str,
        tx_type: str,
        amount: Any,
        symbol: str,
        wallet_address: str = "",
        account_index: Any = None,
        exchange_name: str | None = None,
        direction: str | None = None,
        unit_price: Any = None,
        quote_amount: Any = None,
        event_timestamp: Any = None,
        raw_payload: dict,
        description: str,
    ) -> dict:
        record = {
            "source": source,
            "category": category,
            "external_id": str(external_id),
            "tx_type": tx_type,
            "amount": self._to_float(amount),
            "symbol": symbol,
            "wallet_address": wallet_address or "",
            "account_index": str(account_index) if account_index not in (None, "") else None,
            "exchange_name": exchange_name,
            "direction": direction,
            "unit_price": self._to_float(unit_price),
            "quote_amount": self._to_float(quote_amount),
            "event_timestamp": self._parse_timestamp(event_timestamp),
            "raw_payload": raw_payload,
            "description": description,
        }
        is_interesting, interesting_reason = self._is_interesting(record)
        record["is_interesting"] = is_interesting
        record["interesting_reason"] = interesting_reason
        return record

    def _normalize_items(self, source: str, payload: Any) -> list[dict]:
        records: list[dict] = []

        if source == "buyback_trades":
            trades = payload.get("trades", []) if isinstance(payload, dict) else []
            for item in trades:
                tx_hash = item.get("hash") or item.get("txHash") or item.get("id")
                lit_bought = item.get("size") or item.get("litBought") or 0
                price = item.get("price") or 0
                usdc_spent = item.get("usdcValue") or item.get("usdcSpent") or ((self._to_float(lit_bought) or 0) * (self._to_float(price) or 0))
                account_index = item.get("accountIndex") or item.get("account_index") or settings.buyback_wallet_account_index
                records.append(
                    self._build_record(
                        source=source,
                        category="buybacks",
                        external_id=f"buyback-{tx_hash}",
                        tx_type="buyback",
                        amount=lit_bought,
                        symbol="LIT",
                        wallet_address=item.get("walletAddress") or "",
                        account_index=account_index,
                        direction="in",
                        unit_price=price,
                        quote_amount=usdc_spent,
                        event_timestamp=item.get("time") or item.get("timestamp"),
                        raw_payload=item,
                        description=f"Buyback bought {self._to_float(lit_bought) or 0:,.2f} LIT at ${self._to_float(price) or 0:,.4f}",
                    )
                )

        elif source == "buyback_daily":
            days = payload.get("days", []) if isinstance(payload, dict) else []
            for item in days:
                day = item.get("day")
                lit_bought = item.get("litBought") or 0
                usdc_spent = item.get("usdcSpent") or 0
                records.append(
                    self._build_record(
                        source=source,
                        category="buybacks",
                        external_id=f"buyback-daily-{day}",
                        tx_type="buyback_summary",
                        amount=lit_bought,
                        symbol="LIT",
                        account_index=settings.buyback_wallet_account_index,
                        direction="in",
                        quote_amount=usdc_spent,
                        event_timestamp=day,
                        raw_payload=item,
                        description=f"Daily buyback summary for {day}",
                    )
                )

        elif source == "llp_transfers":
            transfers = payload.get("transfers", []) if isinstance(payload, dict) else []
            for item in transfers:
                tx_hash = item.get("txHash") or item.get("hash") or item.get("id")
                tx_type = item.get("type") or "transfer"
                amount = item.get("amount") or 0
                direction = "in" if tx_type == "deposit" else "out" if tx_type == "withdraw" else None
                records.append(
                    self._build_record(
                        source=source,
                        category="llp",
                        external_id=f"llp-{tx_hash}",
                        tx_type=tx_type,
                        amount=amount,
                        symbol="USDC",
                        wallet_address=item.get("walletAddress") or "",
                        account_index=item.get("accountIndex"),
                        direction=direction,
                        event_timestamp=item.get("timestamp") or item.get("time"),
                        raw_payload=item,
                        description=f"LLP {tx_type} of {self._to_float(amount) or 0:,.2f} USDC",
                    )
                )

        elif source in {"llp_top", "staking_top"}:
            if isinstance(payload, dict):
                top_keys = ["topDepositor", "topWithdrawer", "topStaker", "topUnstaker"]
                for key in top_keys:
                    item = payload.get(key)
                    if not isinstance(item, dict):
                        continue
                    amount = item.get("totalAmount") or item.get("netStaked") or item.get("netDeposited") or 0
                    category = "llp" if source == "llp_top" else "staking"
                    symbol = "USDC" if category == "llp" else "LIT"
                    records.append(
                        self._build_record(
                            source=source,
                            category=category,
                            external_id=f"{source}-{key}-{item.get('accountIndex') or item.get('address')}",
                            tx_type=key,
                            amount=amount,
                            symbol=symbol,
                            wallet_address=item.get("address") or "",
                            account_index=item.get("accountIndex"),
                            direction="in" if "Depositor" in key or "Staker" in key else "out",
                            raw_payload=item,
                            description=f"{key} moved {self._to_float(amount) or 0:,.2f} {symbol}",
                        )
                    )

        return records

    async def collect_and_process(self) -> dict:
        stored = 0
        alerts = 0
        interesting = 0
        collected: list[dict] = []

        async with httpx.AsyncClient(timeout=30.0) as client:
            for source, url in self.endpoints.items():
                try:
                    payload = await self.fetch_json(client, url)
                    records = self._normalize_items(source, payload)
                    for record in records:
                        if self.transaction_repository.get_by_external_id(record["external_id"]):
                            continue
                        created = self.transaction_repository.create(record)
                        stored += 1
                        collected.append(record)
                        if created.is_interesting:
                            interesting += 1
                        alert = await self.alert_service.create_alert_if_needed(record)
                        if alert:
                            alerts += 1
                except Exception:
                    logger.exception("Failed to monitor source %s", source)

        return {
            "stored": stored,
            "alerts": alerts,
            "interesting": interesting,
            "stats": {
                "stored": stored,
                "alerts": alerts,
                "interesting": interesting,
                "sources": list(self.endpoints.keys()),
            },
            "recent_records": collected[:20],
        }
