"""Main browser launcher with configuration management."""

import asyncio
import json
import logging
import os
import subprocess
import tempfile
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union, TYPE_CHECKING

if TYPE_CHECKING:
    from typing_extensions import Self
else:
    try:
        from typing import Self
    except ImportError:
        from typing_extensions import Self

from .browser import Browser, find_installed_browser
from .errors import AlreadyLaunchedError, BrowserNotFoundError, LauncherError
from .flags import Flag, FlagManager
from .hosts import REVISION_DEFAULT
from .os_utils import os_utils
from .url_parser import URLParser, resolve_url


@dataclass
class LauncherConfig:
    """Configuration for browser launcher using dataclass."""
    
    # Browser binary settings
    bin_path: Optional[str] = None
    revision: int = REVISION_DEFAULT
    
    # Window and display settings  
    headless: bool = True
    headless_new: bool = False
    window_size: Optional[Tuple[int, int]] = None
    window_position: Optional[Tuple[int, int]] = None
    
    # Data and profile settings
    user_data_dir: Optional[str] = None
    profile_dir: Optional[str] = None
    
    # Network settings
    remote_debugging_port: int = 0  # 0 for random port
    proxy_server: Optional[str] = None
    
    # Security settings
    no_sandbox: bool = False
    
    # Process settings
    working_dir: Optional[str] = None
    env: Optional[Dict[str, str]] = None
    
    # Advanced settings
    leakless: bool = True
    xvfb: Optional[List[str]] = None
    devtools: bool = False
    preferences: Optional[str] = None
    start_url: Optional[str] = None
    
    # Custom flags
    custom_flags: Dict[str, List[str]] = field(default_factory=dict)
    
    def __post_init__(self):
        """Post-initialization setup."""
        if self.user_data_dir is None:
            # Use temporary directory by default
            temp_base = Path(tempfile.gettempdir()) / "bu" / "user-data"
            self.user_data_dir = str(temp_base / f"session-{os.getpid()}")


class Launcher:
    """Browser launcher with fluent configuration API."""
    
    def __init__(self, config: Optional[LauncherConfig] = None):
        """
        Initialize launcher with configuration.
        
        Args:
            config: Launcher configuration, uses default if None
        """
        self.config = config or LauncherConfig()
        self._process: Optional[subprocess.Popen] = None
        self._url_parser: Optional[URLParser] = None
        self._browser: Optional[Browser] = None
        self._launched = False
        self._lock = threading.Lock()
        self.logger = logging.getLogger(__name__)
        
    # Fluent configuration methods
    
    def bin(self, path: str) -> Self:
        """Set browser binary path."""
        self.config.bin_path = path
        return self
    
    def revision(self, rev: int) -> Self:
        """Set browser revision to download."""
        self.config.revision = rev
        return self
    
    def headless(self, enable: bool = True) -> Self:
        """Enable/disable headless mode."""
        self.config.headless = enable
        self.config.headless_new = False  # Reset headless new
        return self
    
    def headless_new(self, enable: bool = True) -> Self:
        """Enable/disable new headless mode (--headless=new)."""
        self.config.headless_new = enable
        if enable:
            self.config.headless = False  # Disable regular headless
        return self
    
    def no_sandbox(self, enable: bool = True) -> Self:
        """Enable/disable no-sandbox mode."""
        self.config.no_sandbox = enable
        return self
    
    def window_size(self, width: int, height: int) -> Self:
        """Set browser window size."""
        self.config.window_size = (width, height)
        return self
    
    def window_position(self, x: int, y: int) -> Self:
        """Set browser window position."""
        self.config.window_position = (x, y)
        return self
    
    def user_data_dir(self, path: str) -> Self:
        """Set user data directory."""
        self.config.user_data_dir = path
        return self
    
    def profile_dir(self, path: str) -> Self:
        """Set profile directory."""
        self.config.profile_dir = path
        return self
    
    def remote_debugging_port(self, port: int) -> Self:
        """Set remote debugging port (0 for random)."""
        self.config.remote_debugging_port = port
        return self
    
    def proxy(self, proxy_server: str) -> Self:
        """Set proxy server."""
        self.config.proxy_server = proxy_server
        return self
    
    def working_dir(self, path: str) -> Self:
        """Set working directory."""
        self.config.working_dir = path
        return self
    
    def env(self, **env_vars: str) -> Self:
        """Set environment variables."""
        if self.config.env is None:
            self.config.env = {}
        self.config.env.update(env_vars)
        return self
    
    def leakless(self, enable: bool = True) -> Self:
        """Enable/disable leakless mode (force kill on exit)."""
        self.config.leakless = enable
        return self
    
    def xvfb(self, *args: str) -> Self:
        """Enable XVFB with optional arguments (Unix only)."""
        self.config.xvfb = list(args) if args else []
        return self
    
    def devtools(self, enable: bool = True) -> Self:
        """Enable/disable auto-open devtools."""
        self.config.devtools = enable
        return self
    
    def preferences(self, prefs: Union[str, dict]) -> Self:
        """Set browser preferences (JSON string or dict)."""
        if isinstance(prefs, dict):
            prefs = json.dumps(prefs)
        self.config.preferences = prefs
        return self
    
    def start_url(self, url: str) -> Self:
        """Set start URL."""
        self.config.start_url = url
        return self
    
    def flag(self, name: str, *values: str) -> Self:
        """Add custom browser flag."""
        self.config.custom_flags[name] = list(values)
        return self
    
    def delete_flag(self, name: str) -> Self:
        """Remove a browser flag."""
        self.config.custom_flags.pop(name, None)
        return self
    
    # Launch methods
    
    def launch(self, timeout: float = 30.0) -> str:
        """
        Launch browser and return debug WebSocket URL.
        
        Args:
            timeout: Timeout in seconds to wait for browser startup
            
        Returns:
            WebSocket debug URL
            
        Raises:
            AlreadyLaunchedError: If browser has already been launched
            LauncherError: If launch fails
        """
        with self._lock:
            if self._launched:
                raise AlreadyLaunchedError("Browser has already been launched")
            
            try:
                # Get browser binary
                browser_path = self._get_browser_path()
                
                # Setup user preferences if specified
                self._setup_user_preferences()
                
                # Build command line arguments
                cmd = self._build_command(browser_path)
                
                # Setup URL parser
                self._url_parser = URLParser()
                
                # Start process
                self._process = self._start_process(cmd)
                self._launched = True
                
                self.logger.info("Browser process started with PID %d", self._process.pid)
                
                # Wait for debug URL
                debug_url = self._url_parser.get_url(timeout)
                
                # Resolve to WebSocket URL
                try:
                    return resolve_url(debug_url)
                except Exception as e:
                    # Fallback: if URL resolution fails, return the debug URL as-is
                    self.logger.warning("Failed to resolve WebSocket URL: %s", e)
                    return debug_url
                
            except Exception as e:
                self._cleanup()
                raise LauncherError(f"Failed to launch browser: {e}") from e
    
    async def launch_async(self, timeout: float = 30.0) -> str:
        """Async version of launch()."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.launch, timeout)
    
    def kill(self) -> None:
        """Kill the browser process."""
        if self._process and self._process.pid:
            self.logger.info("Killing browser process %d", self._process.pid)
            
            # Give process a moment to start up
            time.sleep(0.1)
            
            try:
                os_utils.kill_process_group(self._process.pid)
            except Exception as e:
                self.logger.warning("Failed to kill process group: %s", e)
            
            # Also try to terminate the main process
            try:
                self._process.terminate()
                self._process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._process.kill()
            except Exception as e:
                self.logger.warning("Failed to terminate process: %s", e)
    
    def cleanup(self) -> None:
        """Wait for process to exit and clean up user data directory."""
        if self._process:
            try:
                self._process.wait()
            except Exception:
                pass
        
        # Clean up user data directory if it's a temporary one
        if (self.config.user_data_dir and 
            "bu" in self.config.user_data_dir and 
            "session-" in self.config.user_data_dir):
            
            user_data_path = Path(self.config.user_data_dir)
            if user_data_path.exists():
                import shutil
                try:
                    shutil.rmtree(user_data_path)
                    self.logger.info("Cleaned up user data directory: %s", user_data_path)
                except Exception as e:
                    self.logger.warning("Failed to clean up user data directory: %s", e)
    
    @property
    def pid(self) -> Optional[int]:
        """Get browser process PID."""
        return self._process.pid if self._process else None
    
    def _get_browser_path(self) -> Path:
        """Get browser executable path."""
        if self.config.bin_path:
            browser_path = Path(self.config.bin_path)
            if not browser_path.exists():
                raise BrowserNotFoundError(f"Browser binary not found: {browser_path}")
            return browser_path
        
        # Try to find installed browser first
        if installed_browser := find_installed_browser():
            self.logger.info("Using installed browser: %s", installed_browser)
            return installed_browser
        
        # Download browser if not found
        if not self._browser:
            self._browser = Browser(revision=self.config.revision)
        
        return self._browser.get()
    
    def _setup_user_preferences(self) -> None:
        """Setup user preferences file if specified."""
        if not self.config.preferences or not self.config.user_data_dir:
            return
        
        user_data_path = Path(self.config.user_data_dir)
        profile = self.config.profile_dir or "Default"
        prefs_path = user_data_path / profile / "Preferences"
        
        # Create directories
        prefs_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write preferences
        prefs_path.write_text(self.config.preferences)
        self.logger.info("Created preferences file: %s", prefs_path)
    
    def _build_command(self, browser_path: Path) -> List[str]:
        """Build browser command line arguments."""
        flag_manager = FlagManager()
        
        # Set basic flags
        if self.config.headless:
            flag_manager.set(Flag.HEADLESS)
        elif self.config.headless_new:
            flag_manager.set(Flag.HEADLESS, "new")
        
        if self.config.no_sandbox or os_utils.is_in_container():
            flag_manager.set(Flag.NO_SANDBOX)
        
        if self.config.user_data_dir:
            flag_manager.set(Flag.USER_DATA_DIR, str(Path(self.config.user_data_dir).absolute()))
        
        if self.config.profile_dir:
            flag_manager.set(Flag.PROFILE_DIRECTORY, self.config.profile_dir)
        
        # Set port (use random if 0)
        port = self.config.remote_debugging_port
        if port == 0:
            import socket
            with socket.socket() as s:
                s.bind(('', 0))
                port = s.getsockname()[1]
        flag_manager.set(Flag.REMOTE_DEBUGGING_PORT, str(port))
        
        if self.config.proxy_server:
            flag_manager.set(Flag.PROXY_SERVER, self.config.proxy_server)
        
        if self.config.window_size:
            flag_manager.set(Flag.WINDOW_SIZE, f"{self.config.window_size[0]},{self.config.window_size[1]}")
        
        if self.config.window_position:
            flag_manager.set(Flag.WINDOW_POSITION, f"{self.config.window_position[0]},{self.config.window_position[1]}")
        
        # Default Chrome flags for stability
        flag_manager.set("no-first-run")
        flag_manager.set("no-startup-window")
        flag_manager.set("disable-features", "site-per-process", "TranslateUI")
        flag_manager.set("disable-dev-shm-usage")
        flag_manager.set("disable-background-networking")
        flag_manager.set("disable-background-timer-throttling")
        flag_manager.set("disable-backgrounding-occluded-windows")
        flag_manager.set("disable-breakpad")
        flag_manager.set("disable-client-side-phishing-detection")
        flag_manager.set("disable-component-extensions-with-background-pages")
        flag_manager.set("disable-default-apps")
        flag_manager.set("disable-hang-monitor")
        flag_manager.set("disable-ipc-flooding-protection")
        flag_manager.set("disable-popup-blocking")
        flag_manager.set("disable-prompt-on-repost")
        flag_manager.set("disable-renderer-backgrounding")
        flag_manager.set("disable-sync")
        flag_manager.set("disable-site-isolation-trials")
        flag_manager.set("enable-automation")
        flag_manager.set("enable-features", "NetworkService", "NetworkServiceInProcess")
        flag_manager.set("force-color-profile", "srgb")
        flag_manager.set("metrics-recording-only")
        flag_manager.set("use-mock-keychain")
        
        # Add devtools flag
        if self.config.devtools:
            flag_manager.set("auto-open-devtools-for-tabs")
        
        # Add custom flags
        for name, values in self.config.custom_flags.items():
            if values:
                flag_manager.set(name, *values)
            else:
                flag_manager.set(name)
        
        # Add start URL as positional argument
        if self.config.start_url:
            flag_manager.set(Flag.ARGUMENTS, self.config.start_url)
        
        # Build final command
        args = flag_manager.format_args()
        
        # Handle XVFB on Unix
        cmd = [str(browser_path)] + args
        if self.config.xvfb is not None:
            cmd = os_utils.setup_process(cmd, xvfb_args=self.config.xvfb)
        
        self.logger.debug("Browser command: %s", ' '.join(cmd))
        return cmd
    
    def _start_process(self, cmd: List[str]) -> subprocess.Popen:
        """Start browser process."""
        # Setup environment
        env = os.environ.copy()
        if self.config.env:
            env.update(self.config.env)
        
        # Setup process creation flags
        process_kwargs = {
            "stdout": subprocess.PIPE,
            "stderr": subprocess.STDOUT,
            "text": True,
            "env": env,
            "cwd": self.config.working_dir,
        }
        
        # Add OS-specific process creation flags
        if hasattr(os_utils, 'get_process_creation_flags'):
            process_kwargs.update(os_utils.get_process_creation_flags())
        
        # Start process
        process = subprocess.Popen(cmd, **process_kwargs)
        
        # Setup output forwarding to URL parser
        def forward_output():
            for line in process.stdout:
                self._url_parser.write(line)
                self.logger.debug("Browser output: %s", line.rstrip())
        
        threading.Thread(target=forward_output, daemon=True).start()
        
        return process
    
    def _cleanup(self) -> None:
        """Internal cleanup on launch failure."""
        if self._process:
            try:
                self._process.terminate()
            except Exception:
                pass
        self._launched = False
        self._process = None
        self._url_parser = None


# Convenience functions for common use cases

def new() -> Launcher:
    """Create a new Launcher with default settings."""
    return Launcher()

def new_user_mode() -> Launcher:
    """Create a launcher for user mode (using existing user profile)."""
    config = LauncherConfig(
        headless=False,
        user_data_dir=None,  # Use system default
        leakless=False,
        remote_debugging_port=37712,  # Fixed port for reconnection
    )
    
    # Try to find installed browser
    if browser_path := find_installed_browser():
        config.bin_path = str(browser_path)
    
    return Launcher(config).delete_flag("no-startup-window").delete_flag("enable-automation")

def new_app_mode(url: str) -> Launcher:
    """Create a launcher for app mode (like a native application)."""
    config = LauncherConfig(
        headless=False,
        start_url=url,
        leakless=True,
    )
    
    return (Launcher(config)
            .flag(Flag.APP, url)
            .env(GOOGLE_API_KEY="no")
            .delete_flag("no-startup-window")
            .delete_flag("enable-automation"))