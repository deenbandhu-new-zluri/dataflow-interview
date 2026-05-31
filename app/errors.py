"""Domain error types, mapped to HTTP status codes in the API layer."""


class ValidationError(Exception):
    """Raised when a pipeline definition is invalid (bad operator config,
    unknown source, etc). The API layer maps this to a 400 response."""


class NotFoundError(Exception):
    """Raised when a referenced resource (pipeline, run, source) does not
    exist. The API layer maps this to a 404 response."""
