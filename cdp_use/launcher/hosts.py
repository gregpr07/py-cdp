"""Browser download host providers."""

import platform
from typing import Callable, Dict, Tuple


# Host function type - takes revision number and returns download URL
HostFunction = Callable[[int], str]

# Host configuration mapping
_HOST_CONFIG = {
    ("Darwin", "x86_64"): {"url_prefix": "Mac", "zip_name": "chrome-mac.zip"},
    ("Darwin", "arm64"): {"url_prefix": "Mac_Arm", "zip_name": "chrome-mac.zip"},
    ("Linux", "x86_64"): {"url_prefix": "Linux_x64", "zip_name": "chrome-linux.zip"},
    ("Windows", "AMD64"): {"url_prefix": "Win_x64", "zip_name": "chrome-win.zip"},
    ("Windows", "x86"): {"url_prefix": "Win", "zip_name": "chrome-win.zip"},
}

# Default revision numbers
REVISION_DEFAULT = 1321438
REVISION_PLAYWRIGHT = 1124


def _get_host_config() -> Dict[str, str]:
    """Get host configuration for current platform."""
    system: str = platform.system()
    machine: str = platform.machine()

    # Normalize machine names
    if machine in ("AMD64", "x86_64"):
        machine = "x86_64"
    elif machine in ("arm64", "aarch64"):
        machine = "arm64"
    elif machine in ("i386", "i686"):
        machine = "x86"

    config = _HOST_CONFIG.get((system, machine))
    if not config:
        raise RuntimeError(f"Unsupported platform: {system} {machine}")

    return config


def HostGoogle(revision: int) -> str:
    """Google storage host for browser downloads."""
    config = _get_host_config()
    return f"https://storage.googleapis.com/chromium-browser-snapshots/{config['url_prefix']}/{revision}/{config['zip_name']}"


def HostNPM(revision: int) -> str:
    """NPM mirror host for browser downloads."""
    config = _get_host_config()
    return (
        f"https://registry.npmmirror.com/-/binary/chromium-browser-snapshots/"
        f"{config['url_prefix']}/{revision}/{config['zip_name']}"
    )


def HostPlaywright(revision: int) -> str:
    """Playwright host for browser downloads."""
    config = _get_host_config()

    # Use default Playwright revision for ARM64 Linux
    if platform.system() == "Linux" and platform.machine() == "arm64":
        revision = REVISION_PLAYWRIGHT

    return f"https://playwright.azureedge.net/builds/chromium/{revision}/chromium-linux-arm64.zip"


# Default host functions in order of preference
DEFAULT_HOSTS = [HostGoogle, HostNPM, HostPlaywright]
