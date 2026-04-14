def success_response(data, message: str = "Success"):
    return {
        "success": True,
        "message": message,
        "data": data,
    }
