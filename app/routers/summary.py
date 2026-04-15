from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.common.responses import success_response
from app.common.security import validate_api_key
from app.database import get_db
from app.repositories.alert_repository import AlertRepository
from app.repositories.analysis_repository import AnalysisRepository
from app.repositories.transaction_repository import TransactionRepository

router = APIRouter(prefix="/summary", tags=["summary"], dependencies=[Depends(validate_api_key)])


@router.get("")
def get_summary(db: Session = Depends(get_db)):
    transaction_repository = TransactionRepository(db)
    alert_repository = AlertRepository(db)
    analysis_repository = AnalysisRepository(db)

    transactions = transaction_repository.list_recent(limit=20)
    interesting_transactions = transaction_repository.list_interesting(limit=10)
    alerts = alert_repository.list_recent(limit=10)
    latest_analysis = analysis_repository.get_latest()

    data = {
        "stats": {
            "recent_transactions": transaction_repository.count_recent(),
            "recent_alerts": len(alerts),
            "interesting_movements": transaction_repository.count_interesting(),
            "tracked_wallets": transaction_repository.count_distinct_wallets(),
        },
        "latest_analysis": None,
        "latest_transactions": [
            {
                "id": item.id,
                "source": item.source,
                "category": item.category,
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
                "created_at": item.created_at,
                "description": item.description,
            }
            for item in transactions
        ],
        "interesting_transactions": [
            {
                "id": item.id,
                "source": item.source,
                "category": item.category,
                "tx_type": item.tx_type,
                "amount": item.amount,
                "symbol": item.symbol,
                "wallet_address": item.wallet_address,
                "account_index": item.account_index,
                "direction": item.direction,
                "quote_amount": item.quote_amount,
                "event_timestamp": item.event_timestamp,
                "interesting_reason": item.interesting_reason,
                "created_at": item.created_at,
                "description": item.description,
            }
            for item in interesting_transactions
        ],
    }

    if latest_analysis:
        data["latest_analysis"] = {
            "id": latest_analysis.id,
            "analysis_date": latest_analysis.analysis_date,
            "summary": latest_analysis.summary,
            "sentiment": latest_analysis.sentiment,
            "signals": latest_analysis.signals,
            "recommended_actions": latest_analysis.recommended_actions,
            "source": latest_analysis.source,
            "created_at": latest_analysis.created_at,
        }

    return success_response(data)
