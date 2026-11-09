"""Custom exceptions (Day 5)."""


class ConfigError(Exception):
    """Raised when the policy configuration file is missing or invalid."""


class DataValidationError(Exception):
    """Raised when a single CSV row fails validation."""
