class AppException(Exception):
    def __init__(
        self,
        status_code: int = 500,
        detail: str = "Internal server error",
        error_code: str | None = None,
    ):
        self.status_code = status_code
        self.detail = detail
        self.error_code = error_code
        super().__init__(detail)


class NotFoundException(AppException):
    def __init__(self, detail: str = "Resource not found"):
        super().__init__(status_code=404, detail=detail, error_code="NOT_FOUND")


class UnauthorizedException(AppException):
    def __init__(self, detail: str = "Not authenticated"):
        super().__init__(status_code=401, detail=detail, error_code="UNAUTHORIZED")


class ForbiddenException(AppException):
    def __init__(self, detail: str = "Forbidden"):
        super().__init__(status_code=403, detail=detail, error_code="FORBIDDEN")


class BadRequestException(AppException):
    def __init__(self, detail: str = "Bad request"):
        super().__init__(status_code=400, detail=detail, error_code="BAD_REQUEST")


class ConflictException(AppException):
    def __init__(self, detail: str = "Conflict"):
        super().__init__(status_code=409, detail=detail, error_code="CONFLICT")


class PaymentRequiredException(AppException):
    """No API key for a bring-your-own-key feature (the interviewer agent)."""

    def __init__(self, detail: str = "No API key configured"):
        super().__init__(status_code=402, detail=detail, error_code="NO_API_KEY")
