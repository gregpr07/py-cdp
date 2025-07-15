#!/usr/bin/env python3
"""
Example usage of the Chrome DevTools Protocol Browser Launcher.

This example demonstrates various launcher configurations and usage patterns.
"""

import logging
import time
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import launcher components (using absolute imports for example)
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from launcher import Launcher, LauncherConfig, new, new_user_mode, new_app_mode
    from browser import Browser, find_installed_browser
    from flags import Flag
    from hosts import HostGoogle, REVISION_DEFAULT
except ImportError:
    print("Note: This example requires httpx to be installed for full functionality.")
    print("Some imports may fail without httpx. Install with: pip install httpx")
    
    # Fallback imports for demonstration
    from flags import Flag, FlagManager
    from hosts import HostGoogle, REVISION_DEFAULT
    
    # Mock classes for demonstration
    class LauncherConfig:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)
    
    class Launcher:
        def __init__(self, config=None):
            self.config = config or LauncherConfig(headless=True, remote_debugging_port=0)
        
        def headless(self, enable=True):
            self.config.headless = enable
            return self
        
        def window_size(self, width, height):
            self.config.window_size = (width, height)
            return self
        
        def user_data_dir(self, path):
            self.config.user_data_dir = path
            return self
        
        def remote_debugging_port(self, port):
            self.config.remote_debugging_port = port
            return self
        
        def no_sandbox(self, enable=True):
            self.config.no_sandbox = enable
            return self
        
        def devtools(self, enable=True):
            self.config.devtools = enable
            return self
        
        def flag(self, name, *values):
            if not hasattr(self.config, 'custom_flags'):
                self.config.custom_flags = {}
            self.config.custom_flags[name] = list(values)
            return self
        
        def delete_flag(self, name):
            if hasattr(self.config, 'custom_flags'):
                self.config.custom_flags.pop(name, None)
            return self
    
    def new():
        return Launcher()
    
    def new_user_mode():
        return Launcher(LauncherConfig(headless=False, remote_debugging_port=37712))
    
    def new_app_mode(url):
        return Launcher(LauncherConfig(headless=False, start_url=url))
    
    class Browser:
        def __init__(self, revision=REVISION_DEFAULT):
            self.revision = revision
        
        def get_browser_dir(self):
            return Path.home() / ".cache" / "rod" / "browser" / f"chromium-{self.revision}"
        
        def get_bin_path(self):
            return self.get_browser_dir() / "chrome"
        
        def exists(self):
            return False
    
    def find_installed_browser():
        return None


def example_basic_usage():
    """Basic launcher usage example."""
    print("=== Basic Usage Example ===")
    
    # Create launcher with default settings
    launcher = Launcher()
    print(f"Default config: headless={launcher.config.headless}, port={launcher.config.remote_debugging_port}")
    
    # Note: We won't actually launch since we don't have httpx installed
    print("Note: Actual launching requires 'pip install httpx'")
    print("Would launch browser with: launcher.launch()")
    print()


def example_fluent_api():
    """Fluent API configuration example."""
    print("=== Fluent API Example ===")
    
    launcher = (Launcher()
        .headless(False)
        .window_size(1920, 1080)
        .user_data_dir("/tmp/browser-profile")
        .remote_debugging_port(9222)
        .no_sandbox(True)
        .devtools(True))
    
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
        }
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
    launcher.flag("disable-features", "VizDisplayCompositor", "AudioServiceOutOfProcess")
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