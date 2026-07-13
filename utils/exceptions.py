class JobPulseError(Exception):
    """Base exception for all job-market-intelligence errors."""


class APIRequestError(JobPulseError):
    """Raised when the upstream jobs API can't be reached or returns bad data."""


class DataValidationError(JobPulseError):
    """Raised when a raw record fails required-field validation during transform."""


class DatabaseError(JobPulseError):
    """Raised when a database operation fails."""
