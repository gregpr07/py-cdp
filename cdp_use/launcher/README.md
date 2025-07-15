# Chrome DevTools Protocol Browser Launcher

A Python port of the [go-rod/launcher](https://github.com/go-rod/rod/tree/main/lib/launcher) for downloading, configuring, and launching browsers for Chrome DevTools Protocol automation.

## Features

- **Automatic browser download** - Downloads Chromium automatically if not found
- **Cross-platform support** - Works on Windows, macOS, and Linux
- **Multiple download sources** - Falls back to fastest available mirror (Google, NPM, Playwright)
- **Fluent configuration API** - Chain methods for easy configuration
- **Dataclass configuration** - Type-safe configuration with Python dataclasses
- **Process management** - Proper process cleanup and leakless mode
- **URL parsing** - Automatically extracts debug WebSocket URL from browser output

## Installation

```bash
pip install httpx  # Required for HTTP requests
```

## Quick Start

### Basic Usage

```python
from cdp_use.launcher import Launcher

# Launch with default settings (headless, auto-download browser)
launcher = Launcher()
websocket_url = launcher.launch()
print(f"Browser debug URL: {websocket_url}")

# Use with your CDP client
# client = YourCDPClient(websocket_url)

# Clean up when done
launcher.kill()
launcher.cleanup()
```

### Using System Browser

```python
from cdp_use.launcher import Launcher, find_installed_browser

# Find and use installed browser
browser_path = find_installed_browser()
if browser_path:
    launcher = Launcher().bin(str(browser_path))
    websocket_url = launcher.launch()
else:
    print("No browser found, will download automatically")
```

## Configuration

### Using Dataclass Configuration

```python
from cdp_use.launcher import Launcher, LauncherConfig

# Configure with dataclass
config = LauncherConfig(
    headless=False,
    window_size=(1920, 1080),
    user_data_dir="/path/to/profile",
    remote_debugging_port=9222,
    devtools=True
)

launcher = Launcher(config)
websocket_url = launcher.launch()
```

### Using Fluent API

```python
from cdp_use.launcher import Launcher

# Chain configuration methods
launcher = (Launcher()
    .headless(False)
    .window_size(1920, 1080)
    .user_data_dir("/path/to/profile")
    .remote_debugging_port(9222)
    .devtools(True)
    .no_sandbox(True)
    .proxy("proxy.example.com:8080"))

websocket_url = launcher.launch()
```

## Configuration Options

### Display Settings

```python
launcher = (Launcher()
    .headless(True)           # Run in headless mode
    .headless_new(True)       # Use new headless mode (--headless=new)
    .window_size(1920, 1080)  # Set window dimensions
    .window_position(100, 50) # Set window position
    .devtools(True))          # Auto-open DevTools
```

### Browser Binary

```python
launcher = (Launcher()
    .bin("/path/to/chrome")   # Use specific browser binary
    .revision(1234567))       # Download specific revision
```

### User Data and Profiles

```python
launcher = (Launcher()
    .user_data_dir("/path/to/userdata")  # Browser user data directory
    .profile_dir("Profile 1")            # Specific profile within user data
    .preferences('{"key": "value"}'))     # Set browser preferences
```

### Network Settings

```python
launcher = (Launcher()
    .remote_debugging_port(9222)         # Fixed port (0 for random)
    .proxy("proxy.example.com:8080"))    # HTTP proxy
```

### Process Settings

```python
launcher = (Launcher()
    .working_dir("/path/to/workdir")     # Process working directory
    .env(TZ="America/New_York")          # Environment variables
    .leakless(True)                      # Force kill on exit
    .no_sandbox(True))                   # Disable sandbox (for containers)
```

### Advanced Settings

```python
# Custom browser flags
launcher = (Launcher()
    .flag("disable-web-security")
    .flag("disable-features", "VizDisplayCompositor", "AudioServiceOutOfProcess")
    .delete_flag("enable-automation"))

# XVFB support (Linux only)
launcher = Launcher().xvfb("-a", "-screen", "0", "1920x1080x24")

# Start URL
launcher = Launcher().start_url("https://example.com")
```

## Convenience Functions

### Default Launcher

```python
from cdp_use.launcher import new

launcher = new()  # Equivalent to Launcher()
```

### User Mode

For automation of personal browser with existing profile:

```python
from cdp_use.launcher import new_user_mode

launcher = new_user_mode()
websocket_url = launcher.launch()
# Browser will use system default profile
```

### App Mode

Run browser like a native application:

```python
from cdp_use.launcher import new_app_mode

launcher = new_app_mode("https://example.com")
websocket_url = launcher.launch()
# Browser opens as app without typical browser UI
```

## Error Handling

```python
from cdp_use.launcher import Launcher, AlreadyLaunchedError, BrowserNotFoundError

try:
    launcher = Launcher()
    websocket_url = launcher.launch(timeout=60)  # 60 second timeout
    
    # Try to launch again (will fail)
    launcher.launch()  # Raises AlreadyLaunchedError
    
except AlreadyLaunchedError:
    print("Browser already launched")
except BrowserNotFoundError:
    print("Could not find or download browser")
except Exception as e:
    print(f"Launch failed: {e}")
finally:
    launcher.kill()
    launcher.cleanup()
```

## Async Support

```python
import asyncio
from cdp_use.launcher import Launcher

async def launch_browser():
    launcher = Launcher()
    try:
        websocket_url = await launcher.launch_async()
        print(f"Browser launched: {websocket_url}")
        return websocket_url
    finally:
        launcher.kill()
        launcher.cleanup()

# Run async
websocket_url = asyncio.run(launch_browser())
```

## Browser Management

### Download and Validation

```python
from cdp_use.launcher import Browser

# Download specific browser revision
browser = Browser(revision=1234567)
browser_path = browser.get()  # Downloads and validates

# Check if browser exists
if browser.exists():
    print("Browser already downloaded")

# Validate browser
try:
    if browser.validate():
        print("Browser is valid")
except BrowserValidationError as e:
    print(f"Browser validation failed: {e}")
```

### Custom Download Hosts

```python
from cdp_use.launcher import Browser, HostGoogle, HostNPM

def custom_host(revision: int) -> str:
    return f"https://my-mirror.com/chromium/{revision}/chrome.zip"

browser = Browser(
    revision=1234567,
    hosts=[custom_host, HostGoogle, HostNPM]  # Try custom host first
)
```

## Platform-Specific Notes

### Linux Containers

When running in Docker or other containers, the launcher automatically detects the container environment and enables `--no-sandbox` mode.

```python
# Explicit no-sandbox for containers
launcher = Launcher().no_sandbox(True)
```

### Linux with XVFB

For headful mode on headless Linux servers:

```python
launcher = (Launcher()
    .headless(False)
    .xvfb("-a", "-screen", "0", "1920x1080x24"))
```

### macOS

The launcher automatically handles macOS-specific browser paths and app bundle structure.

### Windows

Windows process management uses `taskkill` for proper process cleanup.

## URL Resolution

The launcher can resolve various URL formats to WebSocket debug URLs:

```python
from cdp_use.launcher.url_parser import resolve_url

# Various input formats
websocket_url = resolve_url("9222")              # -> ws://127.0.0.1:9222/devtools/...
websocket_url = resolve_url(":9222")             # -> ws://127.0.0.1:9222/devtools/...
websocket_url = resolve_url("localhost:9222")    # -> ws://localhost:9222/devtools/...
websocket_url = resolve_url("http://host:9222")  # -> ws://host:9222/devtools/...
```

## Best Practices

### Resource Cleanup

Always clean up launcher resources:

```python
launcher = Launcher()
try:
    websocket_url = launcher.launch()
    # Use browser...
finally:
    launcher.kill()      # Kill browser process
    launcher.cleanup()   # Remove temporary files
```

### Context Manager Pattern

```python
from contextlib import contextmanager

@contextmanager
def browser_launcher(**kwargs):
    launcher = Launcher(**kwargs)
    try:
        websocket_url = launcher.launch()
        yield websocket_url
    finally:
        launcher.kill()
        launcher.cleanup()

# Usage
with browser_launcher(headless=False) as websocket_url:
    # Use browser...
    pass  # Automatically cleaned up
```

### Reusing Profiles

For session persistence across launches:

```python
import tempfile

# Create persistent user data directory
user_data_dir = tempfile.mkdtemp(prefix="browser-profile-")

launcher = (Launcher()
    .user_data_dir(user_data_dir)
    .leakless(False))  # Don't auto-cleanup

# Browser will remember cookies, localStorage, etc.
```

## Integration Examples

### With Selenium

```python
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from cdp_use.launcher import Launcher

# Launch browser
launcher = Launcher().headless(False).remote_debugging_port(9222)
websocket_url = launcher.launch()

# Connect Selenium
chrome_options = Options()
chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")

driver = webdriver.Chrome(options=chrome_options)
driver.get("https://example.com")
```

### With Playwright

```python
from playwright.sync_api import sync_playwright
from cdp_use.launcher import Launcher

# Launch browser
launcher = Launcher().headless(False).remote_debugging_port(9222)
websocket_url = launcher.launch()

# Connect Playwright
with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp("http://127.0.0.1:9222")
    page = browser.new_page()
    page.goto("https://example.com")
```

## License

This project is a Python port of the [go-rod/launcher](https://github.com/go-rod/rod) library. See the original project for license details.