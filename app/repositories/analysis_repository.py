from typing import Optional

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.models.analysis import Analysis


class AnalysisRepository:
    def __init__(self, db: Session):
        self.db = db

    def upsert_daily(self, data: dict) -> Analysis:
        existing = self.db.query(Analysis).filter(Analysis.analysis_date == data["analysis_date"]).first()
        if existing:
            existing.summary = data["summary"]
            existing.sentiment = data["sentiment"]
            existing.signals = data["signals"]
            existing.recommended_actions = data["recommended_actions"]
            existing.source = data["source"]
            self.db.commit()
            self.db.refresh(existing)
            return existing

        analysis = Analysis(**data)
        self.db.add(analysis)
        self.db.commit()
        self.db.refresh(analysis)
        return analysis

    def get_latest(self) -> Optional[Analysis]:
        return self.db.query(Analysis).order_by(desc(Analysis.created_at)).first()
