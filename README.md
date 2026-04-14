# Crypto Dashboard Backend

FastAPI backend for monitoring crypto transactions, generating alert scores, storing daily AI summaries, and serving dashboard APIs.

## Features
- FastAPI + SQLAlchemy + SQLite
- APScheduler background jobs for 10-minute monitoring and 09:00 daily AI summaries
- Alert scoring with weighted factors: size (40), frequency (20), exchange interaction (25), wallet reputation (15)
- LINE Notify integration with graceful mock mode
- OpenAI daily analysis with graceful mock mode
- API key protection via `X-API-Key`
- Docker-ready deployment

## Endpoints
- `GET /transactions`
- `GET /alerts`
- `GET /summary`

## Local run
```bash
cp .env.example .env
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Use header:
```text
X-API-Key: change-me-in-production
```

## Notes
- Scheduler starts on app startup.
- If external credentials are missing, LINE and OpenAI features are mocked.
- SQLite database is stored in `crypto.db` by default.
