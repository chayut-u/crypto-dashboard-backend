from typing import List

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.models.alert import Alert


class AlertRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, data: dict) -> Alert:
        alert = Alert(**data)
        self.db.add(alert)
        self.db.commit()
        self.db.refresh(alert)
        return alert

    def list_recent(self, limit: int = 50) -> List[Alert]:
        return self.db.query(Alert).order_by(desc(Alert.created_at)).limit(limit).all()
