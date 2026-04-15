from sqlalchemy import Boolean, Column, DateTime, Float, Integer, JSON, String, Text
from sqlalchemy.sql import func

from app.database import Base


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    source = Column(String(100), nullable=False)
    category = Column(String(100), nullable=True, index=True)
    external_id = Column(String(255), nullable=False, unique=True, index=True)
    tx_type = Column(String(50), nullable=False)
    amount = Column(Float, nullable=True)
    symbol = Column(String(50), nullable=True)
    wallet_address = Column(String(255), nullable=True, index=True)
    account_index = Column(String(64), nullable=True, index=True)
    exchange_name = Column(String(100), nullable=True)
    direction = Column(String(20), nullable=True)
    unit_price = Column(Float, nullable=True)
    quote_amount = Column(Float, nullable=True)
    event_timestamp = Column(DateTime(timezone=True), nullable=True, index=True)
    is_interesting = Column(Boolean, nullable=False, default=False)
    interesting_reason = Column(Text, nullable=True)
    raw_payload = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    description = Column(Text, nullable=True)
