#!/usr/bin/env python3
"""
Example usage of the Chrome DevTools Protocol Browser Launcher.

This example demonstrates various launcher configurations and usage patterns.
"""

import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

# Always import these as they don't require httpx
from cdp_use.launcher.flags import Flag, FlagManager
from cdp_use.launcher.hosts import REVISION_DEFAULT, HostGoogle

# Try to import the full launcher functionality
_FULL_FUNCTIONALITY_AVAILABLE = True
try:
    from cdp_use.launcher.browser import Browser as _Browser
    from cdp_use.launcher.browser import (
        find_installed_browser as _find_installed_browser,
    )
    from cdp_use.launcher.launcher import Launcher as _Launcher
    from cdp_use.launcher.launcher import LauncherConfig as _LauncherConfig
    from cdp_use.launcher.launcher import new as _new
    from cdp_use.launcher.launcher import new_app_mode as _new_app_mode
    from cdp_use.launcher.launcher import new_user_mode as _new_user_mode
except ImportError:
    _FULL_FUNCTIONALITY_AVAILABLE = False
    print("Note: This example requires httpx to be installed for full functionality.")
    print("Some imports may fail without httpx. Install with: pip install httpx")
    print()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Define mock classes for demonstration when full functionality isn't available
class MockLauncherConfig:
    """Mock launcher config for demonstration purposes."""

    def __init__(self, **kwargs: Any) -> None:
        self.headless: bool = kwargs.get("headless", True)
        self.remote_debugging_port: int = kwargs.get("remote_debugging_port", 0)
        self.window_size: Optional[Tuple[int, int]] = kwargs.get("window_size")
        self.user_data_dir: Optional[str] = kwargs.get("user_data_dir")
        self.no_sandbox: bool = kwargs.get("no_sandbox", False)
        self.devtools: bool = kwargs.get("devtools", False)
        self.start_url: Optional[str] = kwargs.get("start_url")
        self.custom_flags: Dict[str, List[str]] = kwargs.get("custom_flags", {})


class MockLauncher:
    """Mock launcher for demonstration purposes."""

    def __init__(self, config: Optional[MockLauncherConfig] = None) -> None:
        self.config = config or MockLauncherConfig()

    def headless(self, enable: bool = True) -> "MockLauncher":
        self.config.headless = enable
        return self

    def window_size(self, width: int, height: int) -> "MockLauncher":
        self.config.window_size = (width, height)
        return self

    def user_data_dir(self, path: str) -> "MockLauncher":
        self.config.user_data_dir = path
        return self

    def remote_debugging_port(self, port: int) -> "MockLauncher":
        self.config.remote_debugging_port = port
        return self

    def no_sandbox(self, enable: bool = True) -> "MockLauncher":
        self.config.no_sandbox = enable
        return self

    def devtools(self, enable: bool = True) -> "MockLauncher":
        self.config.devtools = enable
        return self

    def flag(self, name: str, *values: str) -> "MockLauncher":
        self.config.custom_flags[name] = list(values)
        return self

    def delete_flag(self, name: str) -> "MockLauncher":
        self.config.custom_flags.pop(name, None)
        return self


class MockBrowser:
    """Mock browser for demonstration purposes."""

    def __init__(self, revision: int = REVISION_DEFAULT) -> None:
        self.revision = revision

    def get_browser_dir(self) -> Path:
        return Path.home() / ".cache" / "bu" / "browser" / f"chromium-{self.revision}"

    def get_bin_path(self) -> Path:
        return self.get_browser_dir() / "chrome"

    def exists(self) -> bool:
        return False


def mock_new() -> MockLauncher:
    """Create a mock launcher."""
    return MockLauncher()


def mock_new_user_mode() -> MockLauncher:
    """Create a mock user mode launcher."""
    return MockLauncher(MockLauncherConfig(headless=False, remote_debugging_port=37712))


def mock_new_app_mode(url: str) -> MockLauncher:
    """Create a mock app mode launcher."""
    return MockLauncher(MockLauncherConfig(headless=False, start_url=url))


def mock_find_installed_browser() -> Optional[Path]:
    """Mock find installed browser function."""
    return None


# Define type aliases for the API
if _FULL_FUNCTIONALITY_AVAILABLE:
    LauncherConfig = _LauncherConfig
    Launcher = _Launcher
    Browser = _Browser
    new = _new
    new_user_mode = _new_user_mode
    new_app_mode = _new_app_mode
    find_installed_browser = _find_installed_browser
else:
    LauncherConfig = MockLauncherConfig  # type: ignore
    Launcher = MockLauncher  # type: ignore
    Browser = MockBrowser  # type: ignore
    new = mock_new  # type: ignore
    new_user_mode = mock_new_user_mode  # type: ignore
    new_app_mode = mock_new_app_mode  # type: ignore
    find_installed_browser = mock_find_installed_browser  # type: ignore


def example_basic_usage():
    """Basic launcher usage example."""
    print("=== Basic Usage Example ===")

    # Create launcher with default settings
    launcher = Launcher()
    print(
        f"Default config: headless={launcher.config.headless}, port={launcher.config.remote_debugging_port}"
    )

    # Note: We won't actually launch since we don't have httpx installed
    print("Note: Actual launching requires 'pip install httpx'")
    print("Would launch browser with: launcher.launch()")
    print()


def example_fluent_api():
    """Fluent API configuration example."""
    print("=== Fluent API Example ===")

    launcher = (
        Launcher()
        .headless(False)
        .window_size(1920, 1080)
        .user_data_dir("/tmp/browser-profile")
        .remote_debugging_port(9222)
        .no_sandbox(True)
        .devtools(True)
    )

    print(f"Configured launcher:")
    print(f"  Headless: {launcher.config.headless}")
    print(f"  Window size: {launcher.config.window_size}")
    print(f"  Debug port: {launcher.config.remote_debugging_port}")
    print(f"  No sandbox: {launcher.config.no_sandbox}")
    print(f"  DevTools: {launcher.config.devtools}")
    print()


def example_dataclass_config():
    """Dataclass configuration example."""
    print("=== Dataclass Configuration Example ===")

    config = LauncherConfig(
        headless=False,
        window_size=(1366, 768),
        user_data_dir="/tmp/custom-profile",
        remote_debugging_port=9223,
        devtools=True,
        custom_flags={
            "disable-web-security": [],
            "disable-features": ["VizDisplayCompositor"],
        },
    )

    launcher = Launcher(config)
    print(f"Dataclass config:")
    print(f"  Headless: {config.headless}")
    print(f"  Window size: {config.window_size}")
    print(f"  User data dir: {config.user_data_dir}")
    print(f"  Custom flags: {config.custom_flags}")
    print()


def example_browser_management():
    """Browser download and management example."""
    print("=== Browser Management Example ===")

    # Check for installed browser
    installed = find_installed_browser()
    if installed:
        print(f"Found installed browser: {installed}")
    else:
        print("No installed browser found")

    # Browser downloader
    browser = Browser(revision=REVISION_DEFAULT)
    print(f"Browser download directory: {browser.get_browser_dir()}")
    print(f"Browser executable path: {browser.get_bin_path()}")
    print(f"Browser exists: {browser.exists()}")

    # Host URLs
    google_url = HostGoogle(REVISION_DEFAULT)
    print(f"Google download URL: {google_url}")
    print()


def example_convenience_functions():
    """Convenience functions example."""
    print("=== Convenience Functions Example ===")

    # Default launcher
    default_launcher = new()
    print(f"Default launcher headless: {default_launcher.config.headless}")

    # User mode launcher
    user_launcher = new_user_mode()
    print(f"User mode headless: {user_launcher.config.headless}")
    print(f"User mode port: {user_launcher.config.remote_debugging_port}")

    # App mode launcher
    app_launcher = new_app_mode("https://example.com")
    print(f"App mode URL: {app_launcher.config.start_url}")
    print(f"App mode headless: {app_launcher.config.headless}")
    print()


def example_flag_management():
    """Flag management example."""
    print("=== Flag Management Example ===")

    launcher = Launcher()

    # Add custom flags
    launcher.flag("disable-web-security")
    launcher.flag(
        "disable-features", "VizDisplayCompositor", "AudioServiceOutOfProcess"
    )
    launcher.flag("custom-flag", "value1", "value2")

    # Remove a flag
    launcher.delete_flag("custom-flag")

    print(f"Custom flags: {launcher.config.custom_flags}")
    print()


def example_command_building():
    """Command line building example."""
    print("=== Command Line Building Example ===")

    from flags import FlagManager

    # Build command line arguments
    flag_manager = FlagManager()
    flag_manager.set(Flag.HEADLESS)
    flag_manager.set(Flag.USER_DATA_DIR, "/tmp/test")
    flag_manager.set(Flag.REMOTE_DEBUGGING_PORT, "9222")
    flag_manager.set(Flag.WINDOW_SIZE, "1920,1080")
    flag_manager.set("disable-features", "feature1", "feature2")

    args = flag_manager.format_args()
    print("Generated command line arguments:")
    for arg in args:
        print(f"  {arg}")
    print()


def main():
    """Run all examples."""
    print("Chrome DevTools Protocol Browser Launcher Examples")
    print("=" * 50)
    print()

    example_basic_usage()
    example_fluent_api()
    example_dataclass_config()
    example_browser_management()
    example_convenience_functions()
    example_flag_management()
    example_command_building()

    print("Examples completed!")
    print()
    print("To actually launch a browser, install httpx:")
    print("  pip install httpx")
    print()
    print("Then you can use:")
    print("  launcher = Launcher().headless(False)")
    print("  websocket_url = launcher.launch()")
    print("  # Use websocket_url with your CDP client")
    print("  launcher.kill()")
    print("  launcher.cleanup()")


if __name__ == "__main__":
    main()
