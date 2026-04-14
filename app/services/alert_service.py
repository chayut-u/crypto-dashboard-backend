import json

from sqlalchemy.orm import Session

from app.config import settings
from app.repositories.alert_repository import AlertRepository
from app.repositories.transaction_repository import TransactionRepository
from app.services.line_service import LineService


class AlertService:
    def __init__(self, db: Session):
        self.db = db
        self.alert_repository = AlertRepository(db)
        self.transaction_repository = TransactionRepository(db)
        self.line_service = LineService()

    def calculate_score(self, transaction_data: dict) -> tuple[int, str]:
        score = 0
        reasons = []
        amount = float(transaction_data.get("amount") or 0)
        frequency = self.transaction_repository.count_wallet_frequency(transaction_data.get("wallet_address", ""))
        exchange_name = transaction_data.get("exchange_name")
        wallet_address = (transaction_data.get("wallet_address") or "").lower()

        if amount >= 1_000_000:
            score += 40
            reasons.append("Large transfer or trade size")
        elif amount >= 100_000:
            score += 25
            reasons.append("Medium transfer or trade size")
        elif amount > 0:
            score += 10
            reasons.append("Detected non-zero value movement")

        if frequency >= 10:
            score += 20
            reasons.append("High wallet activity frequency")
        elif frequency >= 5:
            score += 10
            reasons.append("Moderate wallet activity frequency")

        if exchange_name:
            score += 25
            reasons.append("Interaction with exchange-related entity")

        flagged_terms = ["binance", "okx", "bybit", "kucoin", "mexc"]
        if any(term in wallet_address for term in flagged_terms):
            score += 15
            reasons.append("Wallet reputation heuristic triggered")
        else:
            score += 5
            reasons.append("Unknown wallet reputation")

        return min(score, 100), "; ".join(reasons)

    async def create_alert_if_needed(self, transaction_data: dict):
        score, reason = self.calculate_score(transaction_data)
        if score <= settings.alert_score_threshold:
            return None

        alert = self.alert_repository.create(
            {
                "transaction_external_id": transaction_data["external_id"],
                "score": score,
                "threshold": settings.alert_score_threshold,
                "status": "sent",
                "reason": reason,
                "payload": json.dumps(transaction_data),
            }
        )
        await self.line_service.send_message(
            f"Crypto alert: score={score}, source={transaction_data['source']}, amount={transaction_data.get('amount')}"
        )
        return alert
