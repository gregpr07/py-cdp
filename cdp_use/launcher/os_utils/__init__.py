"""Operating system utilities for browser process management."""

import platform
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .base import OSUtils

# Import the appropriate OS utilities based on platform
_system = platform.system().lower()

if _system == "windows":
    from .windows import WindowsUtils as _OSUtilsImpl
else:
    from .unix import UnixUtils as _OSUtilsImpl

# Singleton instance
os_utils: "OSUtils" = _OSUtilsImpl()

__all__ = ["os_utils"]
