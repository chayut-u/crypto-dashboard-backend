import logging

from fastapi import FastAPI
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.database import Base, engine
from app.routers.alerts import router as alerts_router
from app.routers.summary import router as summary_router
from app.routers.transactions import router as transactions_router
from app.workers.scheduler import start_scheduler

logging.basicConfig(level=logging.INFO)

limiter = Limiter(key_func=get_remote_address)
app = FastAPI(title="Crypto Monitoring Dashboard API", version="1.0.0")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
    start_scheduler()


@app.get("/")
def healthcheck():
    return {"status": "ok", "service": "crypto-dashboard-backend"}


app.include_router(transactions_router)
app.include_router(alerts_router)
app.include_router(summary_router)
