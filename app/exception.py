from fastapi import HTTPException, status
from fastapi import HTTPException, status
import logging

logger = logging.getLogger("app.exception")

class BaseAPIException(HTTPException):
    """Base exception class with built-in logging"""
    def __init__(self, status_code: int, detail: str, log_level: str = "error"):
        super().__init__(status_code=status_code, detail=detail)
        # Log exception with appropriate level
        log_method = getattr(logger, log_level, logger.error)
        log_method(f"{self.__class__.__name__}: {detail}")

# Update all existing exceptions to inherit from BaseAPIException
class EmailAlreadyRegisteredError(BaseAPIException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
            log_level="warning"
        )

class InvalidCredentialsError(BaseAPIException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

# ... update all other exceptions similarly to inherit from BaseAPIException ...

# Add new exceptions

class ExternalServiceError(BaseAPIException):
    def __init__(self, detail: str = "External service unavailable"):
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=detail
        )




class InactiveUserError(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )



class InsufficientPrivilegesError(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges"
        )

class ProductNotFoundError(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )

class InvalidTokenError(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired token"
        )

class EmptyCartError(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cart is empty"
        )

class InsufficientStockError(HTTPException):
    def __init__(self, detail: str = "Insufficient stock"):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail
        )

class EmailSendError(HTTPException):
    def __init__(self, detail: str = "Error sending email"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail
        )

# Add to app/exception.py

class OrderCreationError(HTTPException):
    def __init__(self, detail: str = "Failed to create order"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail
        )

class DatabaseError(HTTPException):
    def __init__(self, detail: str = "Database operation failed"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail
        )


class InvalidInputError:
    def __init__(self, detail: str = "Invalid input provided"):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail
        )
    pass