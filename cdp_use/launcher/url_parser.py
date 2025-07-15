"""URL parser for extracting browser debug URLs from stdout/stderr."""

import asyncio
import re
import threading
from typing import Optional, Union, Pattern
from urllib.parse import urlparse

import httpx

from .errors import URLParseError


class URLParser:
    """Parses browser debug URL from stdout/stderr output."""
    
    def __init__(self) -> None:
        self._buffer: str = ""
        self._url: Optional[str] = None
        self._error: Optional[str] = None
        self._lock: threading.Lock = threading.Lock()
        self._url_event: threading.Event = threading.Event()
        
        # Regex to match WebSocket debug URLs
        self._ws_regex: Pattern[str] = re.compile(r'ws://[^\s]+/')
    
    def write(self, data: Union[str, bytes]) -> None:
        """Write data to the parser buffer."""
        if isinstance(data, bytes):
            data = data.decode('utf-8', errors='ignore')
        
        with self._lock:
            if self._url is not None:
                return  # Already found URL
            
            self._buffer += data
            
            # Look for WebSocket URL
            match = self._ws_regex.search(self._buffer)
            if match:
                ws_url = match.group().rstrip('/')
                try:
                    parsed = urlparse(ws_url)
                    self._url = f"http://{parsed.netloc}"
                    self._url_event.set()
                    self._buffer = ""  # Clear buffer after finding URL
                except Exception as e:
                    self._error = f"Failed to parse URL: {e}"
                    self._url_event.set()
    
    def get_url(self, timeout: float = 30.0) -> str:
        """Get the parsed URL, blocking until available or timeout."""
        if not self._url_event.wait(timeout):
            with self._lock:
                if self._error:
                    raise URLParseError(f"Failed to get debug URL: {self._error}")
                elif "error while loading shared libraries" in self._buffer:
                    raise URLParseError(
                        f"Failed to launch browser (missing dependencies): {self._buffer.strip()}"
                    )
                else:
                    raise URLParseError(f"Timeout waiting for debug URL: {self._buffer.strip()}")
        
        if self._error:
            raise URLParseError(self._error)
        
        if not self._url:
            raise URLParseError("No URL found")
        
        return self._url
    
    @property
    def url(self) -> Optional[str]:
        """Get the URL if available, non-blocking."""
        return self._url
    
    @property 
    def error(self) -> Optional[str]:
        """Get any error that occurred."""
        return self._error
    
    def clear(self) -> None:
        """Clear the parser state."""
        with self._lock:
            self._buffer = ""
            self._url = None
            self._error = None
            self._url_event.clear()


def resolve_url(url: str) -> str:
    """
    Resolve and normalize a debug URL.
    
    The input can be in various formats:
    - "9222" -> "127.0.0.1:9222"
    - ":9222" -> "127.0.0.1:9222"
    - "host:9222" -> "host:9222"
    - "ws://host:9222" -> extracted to "http://host:9222"
    - "http://host:9222" -> used as-is
    
    Returns the WebSocket debug URL.
    """
    if not url:
        url = "9222"
    
    url = url.strip()
    
    # Handle port-only formats
    if re.match(r'^:?\d+$', url):
        port = url.lstrip(':')
        url = f"127.0.0.1:{port}"
    
    # Add protocol if missing
    if not re.match(r'^\w+://', url):
        url = f"http://{url}"
    
    parsed = urlparse(url)
    
    # Convert to HTTP for version endpoint
    if parsed.scheme in ('ws', 'wss'):
        scheme = 'https' if parsed.scheme == 'wss' else 'http'
        version_url = f"{scheme}://{parsed.netloc}/json/version"
    else:
        version_url = f"{parsed.scheme}://{parsed.netloc}/json/version"
    
    # Get the WebSocket URL from the version endpoint
    try:
        response = httpx.get(version_url, timeout=10)
        response.raise_for_status()
        version_data = response.json()
        
        ws_url = version_data.get('webSocketDebuggerUrl')
        if not ws_url:
            raise URLParseError("No webSocketDebuggerUrl in response")
        
        # Replace host to match the original URL's host
        ws_parsed = urlparse(ws_url)
        final_url = ws_parsed._replace(netloc=parsed.netloc).geturl()
        
        return final_url
        
    except Exception as e:
        raise URLParseError(f"Failed to resolve debug URL {version_url}: {e}")


async def resolve_url_async(url: str) -> str:
    """Async version of resolve_url."""
    if not url:
        url = "9222"
    
    url = url.strip()
    
    # Handle port-only formats
    if re.match(r'^:?\d+$', url):
        port = url.lstrip(':')
        url = f"127.0.0.1:{port}"
    
    # Add protocol if missing
    if not re.match(r'^\w+://', url):
        url = f"http://{url}"
    
    parsed = urlparse(url)
    
    # Convert to HTTP for version endpoint
    if parsed.scheme in ('ws', 'wss'):
        scheme = 'https' if parsed.scheme == 'wss' else 'http'
        version_url = f"{scheme}://{parsed.netloc}/json/version"
    else:
        version_url = f"{parsed.scheme}://{parsed.netloc}/json/version"
    
    # Get the WebSocket URL from the version endpoint
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(version_url, timeout=10)
            response.raise_for_status()
            version_data = response.json()
        
        ws_url = version_data.get('webSocketDebuggerUrl')
        if not ws_url:
            raise URLParseError("No webSocketDebuggerUrl in response")
        
        # Replace host to match the original URL's host
        ws_parsed = urlparse(ws_url)
        final_url = ws_parsed._replace(netloc=parsed.netloc).geturl()
        
        return final_url
        
    except Exception as e:
        raise URLParseError(f"Failed to resolve debug URL {version_url}: {e}")