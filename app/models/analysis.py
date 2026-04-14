from sqlalchemy import Column, DateTime, Integer, JSON, String, Text
from sqlalchemy.sql import func

from app.database import Base


class Analysis(Base):
    __tablename__ = "analyses"

    id = Column(Integer, primary_key=True, index=True)
    analysis_date = Column(String(20), nullable=False, unique=True, index=True)
    summary = Column(Text, nullable=False)
    sentiment = Column(String(50), nullable=False)
    signals = Column(JSON, nullable=False)
    recommended_actions = Column(JSON, nullable=False)
    source = Column(String(50), nullable=False, default="mock")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
