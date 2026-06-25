"""
QuantCAI — Centralized Exception Hierarchy
============================================
Enterprise-grade error handling with structured responses.
Each exception maps to a specific HTTP status code and error category.
"""

from fastapi import HTTPException, status


class QuantCAIError(HTTPException):
    """Base exception for all QuantCAI application errors."""

    def __init__(self, status_code: int, error: str, message: str, details: dict | None = None):
        content = {
            "status": "error",
            "error": error,
            "message": message,
            "details": details,
        }
        super().__init__(status_code=status_code, detail=content)


class TierLimitError(QuantCAIError):
    """Raised when a user exceeds their subscription tier limits."""

    def __init__(self, error: str, message: str, details: dict | None = None):
        super().__init__(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            error=error,
            message=message,
            details=details,
        )


class PaymentError(QuantCAIError):
    """Raised when a payment operation fails."""

    def __init__(self, message: str, details: dict | None = None):
        super().__init__(
            status_code=status.HTTP_502_BAD_GATEWAY,
            error="PAYMENT_ERROR",
            message=message,
            details=details,
        )


class PaymentConfigError(QuantCAIError):
    """Raised when payment gateway is not configured."""

    def __init__(self, gateway: str):
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            error="PAYMENT_NOT_CONFIGURED",
            message=f"{gateway} billing is not configured on this server.",
        )


class SimulationError(QuantCAIError):
    """Raised when a quantum simulation fails."""

    def __init__(self, message: str, details: dict | None = None):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            error="SIMULATION_ERROR",
            message=message,
            details=details,
        )


class SimulationTimeoutError(QuantCAIError):
    """Raised when a simulation exceeds the time limit."""

    def __init__(self, timeout_seconds: int = 30):
        super().__init__(
            status_code=status.HTTP_408_REQUEST_TIMEOUT,
            error="SIMULATION_TIMEOUT",
            message=f"Simulation timed out after {timeout_seconds} seconds. "
                    f"Try reducing the number of qubits or shots.",
        )


class InsufficientCreditsError(QuantCAIError):
    """Raised when a user's wallet has insufficient credits."""

    def __init__(self, required: float, available: float):
        super().__init__(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            error="INSUFFICIENT_CREDITS",
            message=f"Insufficient wallet balance. Required: {required:.2f} credits. "
                    f"Available: {available:.2f} credits.",
            details={"required": required, "available": available},
        )


class RateLimitError(QuantCAIError):
    """Raised when a rate limit is exceeded."""

    def __init__(self, message: str, reset_in_seconds: int | None = None):
        details = {"reset_in_seconds": reset_in_seconds} if reset_in_seconds else None
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            error="RATE_LIMIT_EXCEEDED",
            message=message,
            details=details,
        )


class WebhookVerificationError(QuantCAIError):
    """Raised when a webhook signature verification fails."""

    def __init__(self, gateway: str):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            error="WEBHOOK_VERIFICATION_FAILED",
            message=f"{gateway} webhook signature verification failed.",
        )


class IdempotencyError(QuantCAIError):
    """Raised when a duplicate webhook/IPN event is detected."""

    def __init__(self, event_id: str):
        super().__init__(
            status_code=status.HTTP_200_OK,  # Return 200 to prevent retries
            error="DUPLICATE_EVENT",
            message=f"Event {event_id} has already been processed.",
        )
