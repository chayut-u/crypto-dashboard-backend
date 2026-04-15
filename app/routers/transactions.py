from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.common.responses import success_response
from app.common.security import validate_api_key
from app.database import get_db
from app.repositories.transaction_repository import TransactionRepository

router = APIRouter(prefix="/transactions", tags=["transactions"], dependencies=[Depends(validate_api_key)])


def serialize_transaction(item):
    return {
        "id": item.id,
        "source": item.source,
        "category": item.category,
        "external_id": item.external_id,
        "tx_type": item.tx_type,
        "amount": item.amount,
        "symbol": item.symbol,
        "wallet_address": item.wallet_address,
        "account_index": item.account_index,
        "exchange_name": item.exchange_name,
        "direction": item.direction,
        "unit_price": item.unit_price,
        "quote_amount": item.quote_amount,
        "event_timestamp": item.event_timestamp,
        "is_interesting": item.is_interesting,
        "interesting_reason": item.interesting_reason,
        "description": item.description,
        "created_at": item.created_at,
    }


@router.get("")
def list_transactions(limit: int = 50, db: Session = Depends(get_db)):
    repository = TransactionRepository(db)
    transactions = repository.list_recent(limit=limit)
    return success_response([serialize_transaction(item) for item in transactions])


@router.get("/interesting")
def list_interesting_transactions(limit: int = 50, db: Session = Depends(get_db)):
    repository = TransactionRepository(db)
    transactions = repository.list_interesting(limit=limit)
    return success_response([serialize_transaction(item) for item in transactions])
