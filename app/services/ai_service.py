from datetime import date
from typing import Any

from openai import OpenAI
from sqlalchemy.orm import Session

from app.config import settings
from app.repositories.analysis_repository import AnalysisRepository


class AIService:
    def __init__(self, db: Session):
        self.db = db
        self.analysis_repository = AnalysisRepository(db)

    def _mock_analysis(self, stats: dict, transactions: list[dict]) -> dict[str, Any]:
        return {
            "analysis_date": str(date.today()),
            "summary": f"Mock daily analysis generated from {len(transactions)} tracked transactions.",
            "sentiment": "neutral",
            "signals": [
                "Buyback activity is being tracked.",
                f"Stats snapshot available: {', '.join(list(stats.keys())[:3]) or 'no keys'}.",
            ],
            "recommended_actions": [
                "Review high-score alerts.",
                "Validate exchange-related transfers manually.",
            ],
            "source": "mock",
        }

    def generate_daily_analysis(self, stats: dict, transactions: list[dict]):
        if not settings.openai_api_key:
            data = self._mock_analysis(stats, transactions)
            return self.analysis_repository.upsert_daily(data)

        prompt = (
            "Analyze the following crypto monitoring data and return JSON only with keys "
            "summary, sentiment, signals, recommended_actions.\n"
            f"stats={stats}\ntransactions={transactions[:20]}"
        )
        try:
            client = OpenAI(api_key=settings.openai_api_key)
            response = client.responses.create(
                model="gpt-4.1-mini",
                input=prompt,
            )
            content = response.output_text
            import json
            parsed = json.loads(content)
            data = {
                "analysis_date": str(date.today()),
                "summary": parsed["summary"],
                "sentiment": parsed["sentiment"],
                "signals": parsed["signals"],
                "recommended_actions": parsed["recommended_actions"],
                "source": "openai",
            }
            return self.analysis_repository.upsert_daily(data)
        except Exception:
            data = self._mock_analysis(stats, transactions)
            return self.analysis_repository.upsert_daily(data)
