"""Domain and DB error mapping for core backend."""

from typing import Any, Dict, Optional

from sqlalchemy.exc import DataError, IntegrityError, SQLAlchemyError


class DomainError(Exception):
    """Base domain error with HTTP semantics."""

    status_code = 400
    error_code = "domain_error"

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def to_payload(self) -> Dict[str, Any]:
        return {
            "error": self.error_code,
            "message": self.message,
            "details": self.details,
        }


class ValidationDomainError(DomainError):
    status_code = 400
    error_code = "validation_error"


class NotFoundError(DomainError):
    status_code = 404
    error_code = "not_found"


class ConflictError(DomainError):
    status_code = 409
    error_code = "integrity_conflict"


def _extract_pg_message(exc: Exception) -> str:
    orig = getattr(exc, "orig", None)
    if orig is None:
        return str(exc)
    diag = getattr(orig, "diag", None)
    if diag and getattr(diag, "message_primary", None):
        return str(diag.message_primary)
    return str(orig)


def map_sqlalchemy_error(exc: Exception) -> DomainError:
    """Map SQLAlchemy/PG errors to stable API errors."""
    if isinstance(exc, IntegrityError):
        return ConflictError(_extract_pg_message(exc))
    if isinstance(exc, DataError):
        return ValidationDomainError(_extract_pg_message(exc))
    if isinstance(exc, SQLAlchemyError):
        return DomainError(_extract_pg_message(exc))
    return DomainError(str(exc))
