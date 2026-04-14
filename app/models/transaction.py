from sqlalchemy import Column, DateTime, Float, Integer, JSON, String, Text
from sqlalchemy.sql import func

from app.database import Base


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    source = Column(String(100), nullable=False)
    external_id = Column(String(255), nullable=False, unique=True, index=True)
    tx_type = Column(String(50), nullable=False)
    amount = Column(Float, nullable=True)
    symbol = Column(String(50), nullable=True)
    wallet_address = Column(String(255), nullable=True)
    exchange_name = Column(String(100), nullable=True)
    raw_payload = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    description = Column(Text, nullable=True)
