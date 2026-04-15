from datetime import datetime
from typing import List, Optional

from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from app.models.transaction import Transaction


class TransactionRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_external_id(self, external_id: str) -> Optional[Transaction]:
        return self.db.query(Transaction).filter(Transaction.external_id == external_id).first()

    def create(self, data: dict) -> Transaction:
        transaction = Transaction(**data)
        self.db.add(transaction)
        self.db.commit()
        self.db.refresh(transaction)
        return transaction

    def list_recent(self, limit: int = 50) -> List[Transaction]:
        return self.db.query(Transaction).order_by(desc(Transaction.event_timestamp), desc(Transaction.created_at)).limit(limit).all()

    def list_interesting(self, limit: int = 50) -> List[Transaction]:
        return (
            self.db.query(Transaction)
            .filter(Transaction.is_interesting.is_(True))
            .order_by(desc(Transaction.event_timestamp), desc(Transaction.created_at))
            .limit(limit)
            .all()
        )

    def count_wallet_frequency(self, wallet_address: str) -> int:
        if not wallet_address:
            return 0
        return self.db.query(Transaction).filter(Transaction.wallet_address == wallet_address).count()

    def count_recent(self, since: Optional[datetime] = None) -> int:
        query = self.db.query(func.count(Transaction.id))
        if since is not None:
            query = query.filter(Transaction.created_at >= since)
        return query.scalar() or 0

    def count_interesting(self) -> int:
        return self.db.query(func.count(Transaction.id)).filter(Transaction.is_interesting.is_(True)).scalar() or 0

    def count_distinct_wallets(self) -> int:
        return (
            self.db.query(func.count(func.distinct(Transaction.wallet_address)))
            .filter(Transaction.wallet_address.isnot(None))
            .filter(Transaction.wallet_address != "")
            .scalar()
            or 0
        )
