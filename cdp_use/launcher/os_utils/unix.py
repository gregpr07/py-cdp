"""Unix/Linux/macOS specific OS utilities."""

import os
import signal
import subprocess
from pathlib import Path
from typing import List, Optional

from .base import OSUtils


class UnixUtils(OSUtils):
    """Unix/Linux/macOS specific utilities."""
    
    def kill_process_group(self, pid: int) -> None:
        """Kill a process group using SIGKILL."""
        try:
            # Kill the entire process group
            os.killpg(pid, signal.SIGKILL)
        except (ProcessLookupError, PermissionError, OSError):
            # Process may have already exited or we don't have permission
            pass
    
    def setup_process(self, cmd: List[str], *, xvfb_args: Optional[List[str]] = None) -> List[str]:
        """Setup process command with Unix-specific modifications."""
        if xvfb_args:
            # Prepend xvfb-run command
            return ["xvfb-run"] + xvfb_args + cmd
        return cmd
    
    def get_process_creation_flags(self) -> dict:
        """Get process creation flags for subprocess.Popen."""
        return {
            "preexec_fn": os.setsid,  # Create new process group
            "start_new_session": True
        }
    
    def get_default_browser_dir(self) -> Path:
        """Get the default browser download directory."""
        home = Path.home()
        if os.name == "posix":
            if "darwin" in os.uname().sysname.lower():
                # macOS
                return home / ".cache" / "rod" / "browser"
            else:
                # Linux and other Unix
                return home / ".cache" / "rod" / "browser"
        return home / ".rod" / "browser"
    
    def _get_common_browser_paths(self) -> List[str]:
        """Get common browser installation paths for Unix systems."""
        if "darwin" in os.uname().sysname.lower():
            # macOS paths
            return [
                "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                "/Applications/Chromium.app/Contents/MacOS/Chromium", 
                "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
                "/Applications/Google Chrome Canary.app/Contents/MacOS/Google Chrome Canary",
                "/usr/bin/google-chrome-stable",
                "/usr/bin/google-chrome",
                "/usr/bin/chromium",
                "/usr/bin/chromium-browser",
            ]
        else:
            # Linux paths
            return [
                "chrome",
                "google-chrome",
                "/usr/bin/google-chrome",
                "microsoft-edge", 
                "/usr/bin/microsoft-edge",
                "chromium",
                "chromium-browser",
                "google-chrome-stable",
                "/usr/bin/google-chrome-stable",
                "/usr/bin/chromium",
                "/usr/bin/chromium-browser",
                "/snap/bin/chromium",
                "/data/data/com.termux/files/usr/bin/chromium-browser",
            ]
    
    def find_executable(self, name: str) -> Optional[Path]:
        """Find executable in PATH."""
        result = subprocess.run(
            ["which", name],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            return Path(result.stdout.strip())
        return None