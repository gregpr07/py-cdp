"""Custom exceptions for the launcher module."""


class LauncherError(Exception):
    """Base exception for launcher-related errors."""

    pass


class AlreadyLaunchedError(LauncherError):
    """Raised when trying to launch a browser that has already been launched."""

    pass


class BrowserNotFoundError(LauncherError):
    """Raised when a browser binary cannot be found or downloaded."""

    pass


class BrowserValidationError(LauncherError):
    """Raised when browser binary validation fails."""

    pass


class URLParseError(LauncherError):
    """Raised when unable to parse the debug URL from browser output."""

    pass
