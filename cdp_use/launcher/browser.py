"""Browser binary download and management."""

import hashlib
import logging
import shutil
import subprocess
import tempfile
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import List, Optional, Tuple

import httpx

from .errors import BrowserNotFoundError, BrowserValidationError
from .hosts import DEFAULT_HOSTS, REVISION_DEFAULT, HostFunction
from .os_utils import os_utils


class Browser:
    """Manages browser binary download and validation."""

    def __init__(
        self,
        revision: int = REVISION_DEFAULT,
        hosts: Optional[List[HostFunction]] = None,
        root_dir: Optional[Path] = None,
        logger: Optional[logging.Logger] = None,
        http_client: Optional[httpx.Client] = None,
    ):
        """
        Initialize browser manager.

        Args:
            revision: Browser revision number to download
            hosts: List of host functions for download sources
            root_dir: Root directory for browser downloads
            logger: Logger instance
            http_client: HTTP client for downloads
        """
        self.revision = revision
        self.hosts = hosts or DEFAULT_HOSTS.copy()
        self.root_dir = root_dir or os_utils.get_default_browser_dir()
        self.logger = logger or logging.getLogger(__name__)
        self.http_client = http_client

    def get_browser_dir(self) -> Path:
        """Get the directory for this browser revision."""
        return self.root_dir / f"chromium-{self.revision}"

    def get_bin_path(self) -> Path:
        """Get the browser executable path."""
        browser_dir = self.get_browser_dir()
        executable_name = os_utils.get_browser_executable_name()
        return browser_dir / executable_name

    def exists(self) -> bool:
        """Check if browser binary exists."""
        return self.get_bin_path().exists()

    def validate(self) -> bool:
        """
        Validate browser binary by running a simple test.

        Returns:
            True if browser is valid, False otherwise

        Raises:
            BrowserValidationError: If validation fails with specific error
        """
        bin_path = self.get_bin_path()

        if not bin_path.exists():
            return False

        # Try to run browser with headless mode to test basic functionality
        try:
            result = subprocess.run(
                [
                    str(bin_path),
                    "--headless",
                    "--no-sandbox",
                    "--use-mock-keychain",
                    "--disable-dev-shm-usage",
                    "--disable-gpu",
                    "--dump-dom",
                    "about:blank",
                ],
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )

            # Check for library dependency errors (treat as valid but warn)
            if "error while loading shared libraries" in result.stderr:
                self.logger.warning(
                    "Browser binary has missing dependencies but is considered valid: %s",
                    result.stderr.strip(),
                )
                return True

            if result.returncode != 0:
                raise BrowserValidationError(
                    f"Browser failed to run: {result.stderr or result.stdout}"
                )

            # Check if output contains expected HTML
            expected_html = "<html><head></head><body></body></html>"
            if expected_html not in result.stdout:
                raise BrowserValidationError(
                    "Browser doesn't support headless mode or produced unexpected output"
                )

            return True

        except subprocess.TimeoutExpired:
            raise BrowserValidationError("Browser validation timed out")
        except Exception as e:
            raise BrowserValidationError(f"Browser validation failed: {e}")

    def download(self, force: bool = False) -> None:
        """
        Download browser binary from the fastest available host.

        Args:
            force: Force download even if browser already exists

        Raises:
            BrowserNotFoundError: If download fails from all hosts
        """
        if self.exists() and not force:
            self.logger.info("Browser already exists at %s", self.get_bin_path())
            return

        browser_dir = self.get_browser_dir()

        # Create temporary directory for download
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Try downloading from hosts in parallel to find fastest
            download_urls = [host(self.revision) for host in self.hosts]

            self.logger.info("Downloading browser revision %d...", self.revision)

            archive_path = self._download_fastest(download_urls, temp_path)

            # Extract archive
            self.logger.info("Extracting browser archive...")
            self._extract_archive(archive_path, temp_path)

            # Move to final location
            if browser_dir.exists():
                shutil.rmtree(browser_dir)

            # Find the extracted directory (should be only one)
            extracted_dirs = [d for d in temp_path.iterdir() if d.is_dir()]
            if not extracted_dirs:
                raise BrowserNotFoundError("No extracted directory found")

            extracted_dir = extracted_dirs[0]
            browser_dir.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(extracted_dir), str(browser_dir))

            self.logger.info("Browser downloaded to %s", browser_dir)

    def get(self, validate: bool = True) -> Path:
        """
        Get browser binary path, downloading if necessary.

        Args:
            validate: Whether to validate the browser after ensuring it exists

        Returns:
            Path to browser executable

        Raises:
            BrowserNotFoundError: If browser cannot be found or downloaded
            BrowserValidationError: If validation is requested and fails
        """
        if not self.exists():
            self.download()

        bin_path = self.get_bin_path()

        if validate and not self.validate():
            # Try re-downloading once
            self.logger.warning("Browser validation failed, re-downloading...")
            self.download(force=True)

            if not self.validate():
                raise BrowserValidationError(
                    "Browser validation failed after re-download"
                )

        return bin_path

    def _download_fastest(self, urls: List[str], dest_dir: Path) -> Path:
        """Download from the fastest responding URL."""
        if not urls:
            raise BrowserNotFoundError("No download URLs provided")

        # Test download speed with small request to each URL
        fastest_url = self._find_fastest_url(urls)

        self.logger.info("Downloading from %s", fastest_url)

        # Download the full file
        response = self._get_http_client().get(fastest_url, timeout=300)
        response.raise_for_status()

        # Determine filename from URL
        filename = fastest_url.split("/")[-1]
        archive_path = dest_dir / filename

        # Write file
        archive_path.write_bytes(response.content)

        return archive_path

    def _find_fastest_url(self, urls: List[str]) -> str:
        """Find the fastest responding URL by testing small requests."""

        def test_url(url: str) -> Tuple[str, float]:
            try:
                import time

                start: float = time.time()
                response = self._get_http_client().get(
                    url,
                    headers={"Range": "bytes=0-1023"},  # Test with 1KB
                    timeout=10,
                )
                elapsed: float = time.time() - start

                if response.status_code in (200, 206):  # OK or Partial Content
                    return url, elapsed
                else:
                    return url, float("inf")

            except Exception:
                return url, float("inf")

        # Test all URLs in parallel
        with ThreadPoolExecutor(max_workers=len(urls)) as executor:
            futures = {executor.submit(test_url, url): url for url in urls}
            results = []

            for future in as_completed(futures):
                url, elapsed = future.result()
                results.append((url, elapsed))

        # Sort by response time and return fastest
        results.sort(key=lambda x: x[1])

        if not results or results[0][1] == float("inf"):
            raise BrowserNotFoundError("All download URLs failed to respond")

        return results[0][0]

    def _extract_archive(self, archive_path: Path, dest_dir: Path) -> None:
        """Extract zip archive and strip first directory level."""
        with zipfile.ZipFile(archive_path, "r") as zip_file:
            zip_file.extractall(dest_dir)

        # Strip first directory level if all files are in a single top-level directory
        extracted_items = list(dest_dir.iterdir())

        if len(extracted_items) == 1 and extracted_items[0].is_dir():
            # Move contents up one level
            top_dir = extracted_items[0]
            temp_name = dest_dir / "_temp_browser"

            # Move top directory to temp name
            top_dir.rename(temp_name)

            # Move contents of temp directory to dest_dir
            for item in temp_name.iterdir():
                item.rename(dest_dir / item.name)

            # Remove empty temp directory
            temp_name.rmdir()

    def _get_http_client(self) -> httpx.Client:
        """Get HTTP client for downloads."""
        if self.http_client:
            return self.http_client

        return httpx.Client(
            timeout=httpx.Timeout(300.0),
            headers={"User-Agent": "Chrome-Launcher-Python"},
        )


def find_installed_browser() -> Optional[Path]:
    """
    Find an installed browser on the system.

    Returns:
        Path to browser executable if found, None otherwise
    """
    # First try common browser names in PATH
    common_names = ["chrome", "google-chrome", "chromium", "chromium-browser"]

    for name in common_names:
        if hasattr(os_utils, "find_executable"):
            path = os_utils.find_executable(name)
            if path:
                return path

    # Then try known installation paths
    for path in os_utils.find_browser_paths():
        if path.exists():
            return path

    return None
