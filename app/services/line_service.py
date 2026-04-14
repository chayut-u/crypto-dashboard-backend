import logging

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


class LineService:
    async def send_message(self, message: str) -> dict:
        if not settings.line_notify_token:
            logger.info("LINE Notify token missing. Mock notification: %s", message)
            return {"status": "mocked", "message": message}

        headers = {"Authorization": f"Bearer {settings.line_notify_token}"}
        data = {"message": message}
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                response = await client.post("https://notify-api.line.me/api/notify", headers=headers, data=data)
                response.raise_for_status()
            return {"status": "sent", "message": message}
        except Exception as exc:
            logger.exception("Failed to send LINE notification")
            return {"status": "failed", "error": str(exc), "message": message}
