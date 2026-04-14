import json

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.common.responses import success_response
from app.common.security import validate_api_key
from app.database import get_db
from app.repositories.alert_repository import AlertRepository

router = APIRouter(prefix="/alerts", tags=["alerts"], dependencies=[Depends(validate_api_key)])


@router.get("")
def list_alerts(limit: int = 50, db: Session = Depends(get_db)):
    repository = AlertRepository(db)
    alerts = repository.list_recent(limit=limit)
    data = [
        {
            "id": item.id,
            "transaction_external_id": item.transaction_external_id,
            "score": item.score,
            "threshold": item.threshold,
            "status": item.status,
            "reason": item.reason,
            "payload": json.loads(item.payload),
            "created_at": item.created_at,
        }
        for item in alerts
    ]
    return success_response(data)
