from fastapi import Header

from app.common.exceptions import unauthorized_exception
from app.config import settings


async def validate_api_key(x_api_key: str = Header(default="")):
    if x_api_key != settings.api_secret_key:
        raise unauthorized_exception()
    return x_api_key
