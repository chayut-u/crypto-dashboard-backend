import logging

from apscheduler.schedulers.background import BackgroundScheduler

from app.config import settings
from app.database import SessionLocal
from app.services.ai_service import AIService
from app.services.monitor_service import MonitorService
from app.repositories.transaction_repository import TransactionRepository

logger = logging.getLogger(__name__)
scheduler = BackgroundScheduler(timezone="Europe/Berlin")


def monitor_job():
    db = SessionLocal()
    try:
        service = MonitorService(db)
        import asyncio
        asyncio.run(service.collect_and_process())
    except Exception:
        logger.exception("Monitor job failed")
    finally:
        db.close()


def daily_summary_job():
    db = SessionLocal()
    try:
        monitor_service = MonitorService(db)
        transaction_repository = TransactionRepository(db)
        transactions = transaction_repository.list_recent(limit=20)
        import asyncio
        stats_result = asyncio.run(monitor_service.collect_and_process())
        ai_service = AIService(db)
        ai_service.generate_daily_analysis(
            stats_result.get("stats", {}),
            [transaction.raw_payload for transaction in transactions],
        )
    except Exception:
        logger.exception("Daily summary job failed")
    finally:
        db.close()


def start_scheduler():
    if scheduler.running:
        return
    scheduler.add_job(monitor_job, "interval", minutes=settings.monitor_interval_minutes, id="monitor_job", replace_existing=True)
    scheduler.add_job(daily_summary_job, "cron", hour=settings.daily_summary_hour, minute=0, id="daily_summary_job", replace_existing=True)
    scheduler.start()
