from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.common.responses import success_response
from app.common.security import validate_api_key
from app.database import get_db
from app.repositories.transaction_repository import TransactionRepository

router = APIRouter(prefix="/transactions", tags=["transactions"], dependencies=[Depends(validate_api_key)])


@router.get("")
def list_transactions(limit: int = 50, db: Session = Depends(get_db)):
    repository = TransactionRepository(db)
    transactions = repository.list_recent(limit=limit)
    data = [
        {
            "id": item.id,
            "source": item.source,
            "external_id": item.external_id,
            "tx_type": item.tx_type,
            "amount": item.amount,
            "symbol": item.symbol,
            "wallet_address": item.wallet_address,
            "exchange_name": item.exchange_name,
            "description": item.description,
            "created_at": item.created_at,
        }
        for item in transactions
    ]
    return success_response(data)
