from fastapi import HTTPException


class AppError(HTTPException):
    def __init__(self, code: str, message: str, status_code: int = 400):
        self.code = code
        super().__init__(status_code=status_code, detail={"code": code, "message": message})
