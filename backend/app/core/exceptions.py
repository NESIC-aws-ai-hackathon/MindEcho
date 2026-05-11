from fastapi import HTTPException, status


class AppError(HTTPException):
    """Base application error."""

    def __init__(self, status_code: int, code: str, message: str, details: list | None = None):
        self.code = code
        self.error_message = message
        self.details = details or []
        super().__init__(
            status_code=status_code,
            detail={"error": {"code": code, "message": message, "details": self.details}},
        )


class UnauthorizedError(AppError):
    def __init__(self, message: str = "メールアドレスまたはパスワードが正しくありません"):
        super().__init__(status.HTTP_401_UNAUTHORIZED, "UNAUTHORIZED", message)


class ForbiddenError(AppError):
    def __init__(self, message: str = "この操作を行う権限がありません"):
        super().__init__(status.HTTP_403_FORBIDDEN, "FORBIDDEN", message)


class NotFoundError(AppError):
    def __init__(self, message: str = "リソースが見つかりません"):
        super().__init__(status.HTTP_404_NOT_FOUND, "NOT_FOUND", message)


class ConflictError(AppError):
    def __init__(self, message: str = "リソースが競合しています"):
        super().__init__(status.HTTP_409_CONFLICT, "CONFLICT", message)


class ValidationError(AppError):
    def __init__(self, message: str = "入力内容に問題があります", details: list | None = None):
        super().__init__(status.HTTP_422_UNPROCESSABLE_ENTITY, "VALIDATION_ERROR", message, details)
