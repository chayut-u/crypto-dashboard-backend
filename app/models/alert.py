from sqlalchemy import Column, DateTime, Float, Integer, String, Text
from sqlalchemy.sql import func

from app.database import Base


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    transaction_external_id = Column(String(255), nullable=False, index=True)
    score = Column(Integer, nullable=False)
    threshold = Column(Integer, nullable=False)
    status = Column(String(50), nullable=False, default="sent")
    reason = Column(Text, nullable=False)
    payload = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
