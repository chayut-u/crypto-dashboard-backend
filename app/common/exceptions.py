from fastapi import HTTPException, status


def unauthorized_exception():
    return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")
