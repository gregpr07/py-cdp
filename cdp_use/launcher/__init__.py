"""
Chrome DevTools Protocol Browser Launcher

A Python port of the go-rod launcher for downloading, configuring, and launching browsers
for Chrome DevTools Protocol automation.
"""

from .browser import Browser
from .launcher import Launcher, LauncherConfig
from .url_parser import URLParser
from .errors import LauncherError, AlreadyLaunchedError, BrowserNotFoundError
from .hosts import HostGoogle, HostNPM, HostPlaywright
from .flags import Flag

__version__ = "0.1.0"
__all__ = [
    "Browser",
    "Launcher", 
    "LauncherConfig",
    "URLParser",
    "LauncherError",
    "AlreadyLaunchedError", 
    "BrowserNotFoundError",
    "HostGoogle",
    "HostNPM", 
    "HostPlaywright",
    "Flag",
]