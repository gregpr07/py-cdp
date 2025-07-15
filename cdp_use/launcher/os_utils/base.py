"""Base class for operating system utilities."""

import os
import platform
import subprocess
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional


class OSUtils(ABC):
    """Abstract base class for OS-specific utilities."""

    @abstractmethod
    def kill_process_group(self, pid: int) -> None:
        """Kill a process group by PID."""
        pass

    @abstractmethod
    def setup_process(
        self, cmd: List[str], *, xvfb_args: Optional[List[str]] = None
    ) -> List[str]:
        """Setup process command with OS-specific modifications."""
        pass

    @abstractmethod
    def get_default_browser_dir(self) -> Path:
        """Get the default browser download directory for this OS."""
        pass

    def find_browser_paths(self) -> List[Path]:
        """Find common browser installation paths on this OS."""
        common_paths = self._get_common_browser_paths()
        existing_paths = []

        for path_str in common_paths:
            path = Path(path_str).expanduser()
            if path.exists():
                existing_paths.append(path)

        return existing_paths

    @abstractmethod
    def _get_common_browser_paths(self) -> List[str]:
        """Get list of common browser paths for this OS."""
        pass

    def get_browser_executable_name(self) -> str:
        """Get the browser executable name for this OS."""
        if platform.system() == "Windows":
            return "chrome.exe"
        elif platform.system() == "Darwin":
            return "Chromium.app/Contents/MacOS/Chromium"
        else:
            return "chrome"

    def expand_environment_paths(self, paths: List[str]) -> List[str]:
        """Expand environment variables in paths."""
        expanded = []
        for path in paths:
            expanded_path = os.path.expandvars(path)
            if expanded_path != path:  # Only add if expansion occurred
                expanded.append(expanded_path)
        return expanded

    def is_in_container(self) -> bool:
        """Check if running inside a container (Docker, etc.)."""
        # Check for Docker
        if Path("/.dockerenv").exists():
            return True

        # Check cgroup for container indicators
        try:
            with open("/proc/1/cgroup", "r") as f:
                content = f.read()
                if "docker" in content or "containerd" in content:
                    return True
        except (FileNotFoundError, PermissionError):
            pass

        return False
