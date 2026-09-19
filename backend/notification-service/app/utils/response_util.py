from typing import Any


def success(data: Any = None, message: str = "Success") -> dict:
    return {"success": True, "data": data, "message": message}


def error(code: str, message: str) -> dict:
    return {"success": False, "error": {"code": code, "message": message}}
