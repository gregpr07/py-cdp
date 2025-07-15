"""Windows specific OS utilities."""

import os
import subprocess
from pathlib import Path
from typing import List, Optional

from .base import OSUtils


class WindowsUtils(OSUtils):
    """Windows specific utilities."""

    def kill_process_group(self, pid: int) -> None:
        """Kill a process group using taskkill."""
        try:
            subprocess.run(
                ["taskkill", "/F", "/T", "/PID", str(pid)],
                check=False,
                capture_output=True,
            )
        except (FileNotFoundError, subprocess.SubprocessError):
            # taskkill not found or other error
            pass

    def setup_process(
        self, cmd: List[str], *, xvfb_args: Optional[List[str]] = None
    ) -> List[str]:
        """Setup process command (XVFB not supported on Windows)."""
        if xvfb_args:
            raise RuntimeError("XVFB is not supported on Windows")
        return cmd

    def get_process_creation_flags(self) -> dict:
        """Get process creation flags for subprocess.Popen."""
        import subprocess

        return {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP}

    def get_default_browser_dir(self) -> Path:
        """Get the default browser download directory."""
        appdata = os.getenv("APPDATA")
        if appdata:
            return Path(appdata) / "bu" / "browser"
        return Path.home() / "AppData" / "Roaming" / "bu" / "browser"

    def _get_common_browser_paths(self) -> List[str]:
        """Get common browser installation paths for Windows."""
        base_paths = [
            "chrome",
            "edge",
        ]

        # Add paths with environment variables
        program_files_paths = [
            r"$PROGRAMFILES\Google\Chrome\Application\chrome.exe",
            r"$PROGRAMFILES\Chromium\Application\chrome.exe",
            r"$PROGRAMFILES\Microsoft\Edge\Application\msedge.exe",
            r"$PROGRAMFILES(X86)\Google\Chrome\Application\chrome.exe",
            r"$PROGRAMFILES(X86)\Chromium\Application\chrome.exe",
            r"$PROGRAMFILES(X86)\Microsoft\Edge\Application\msedge.exe",
            r"$LOCALAPPDATA\Google\Chrome\Application\chrome.exe",
            r"$LOCALAPPDATA\Chromium\Application\chrome.exe",
            r"$LOCALAPPDATA\Microsoft\Edge\Application\msedge.exe",
        ]

        # Expand environment variables
        expanded_paths = self.expand_environment_paths(program_files_paths)

        return base_paths + expanded_paths

    def find_executable(self, name: str) -> Optional[Path]:
        """Find executable using 'where' command."""
        try:
            result = subprocess.run(
                ["where", name], capture_output=True, text=True, check=True
            )
            # 'where' can return multiple paths, use the first one
            paths = result.stdout.strip().split("\n")
            if paths and paths[0]:
                return Path(paths[0])
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass
        return None
