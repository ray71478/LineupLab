"""
Custom exception classes for Cortex application.

These exceptions provide clear, actionable error messages for different failure scenarios.
"""


class CortexException(Exception):
    """Base exception for Cortex application."""

    def __init__(self, message: str, status_code: int = 500):
        """
        Initialize CortexException.

        Args:
            message: Human-readable error message
            status_code: HTTP status code for API responses
        """
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class DataImportError(CortexException):
    """Raised when data import fails (file parsing, validation, etc.)."""

    def __init__(self, message: str):
        """
        Initialize DataImportError.

        Args:
            message: Human-readable error message describing the import failure
        """
        super().__init__(message, status_code=400)


class ValidationError(CortexException):
    """Raised when validation fails (data type, business rules, etc.)."""

    def __init__(self, message: str):
        """
        Initialize ValidationError.

        Args:
            message: Human-readable error message describing the validation failure
        """
        super().__init__(message, status_code=422)


class PlayerMatchingError(CortexException):
    """Raised when fuzzy matching or player lookup fails."""

    def __init__(self, message: str):
        """
        Initialize PlayerMatchingError.

        Args:
            message: Human-readable error message describing the matching failure
        """
        super().__init__(message, status_code=400)
