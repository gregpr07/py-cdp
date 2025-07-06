#!/usr/bin/env python3
"""
CDP Protocol Downloader and Generator

Downloads the latest Chrome DevTools Protocol specifications and generates
type-safe Python bindings.
"""

import tempfile
from pathlib import Path
from urllib.request import urlretrieve

from .constants import BROWSER_PROTOCOL_FILE, JS_PROTOCOL_FILE
from .generator import CDPGenerator


def download_protocol_files() -> tuple[str, str]:
    """Download the latest protocol files from the official repository."""
    temp_dir = Path(tempfile.mkdtemp())

    print("Downloading Chrome DevTools Protocol specifications...")

    # Download JavaScript protocol
    js_protocol_path = temp_dir / "js_protocol.json"
    print(f"  Downloading JS protocol from {JS_PROTOCOL_FILE}")
    urlretrieve(JS_PROTOCOL_FILE, js_protocol_path)

    # Download Browser protocol
    browser_protocol_path = temp_dir / "browser_protocol.json"
    print(f"  Downloading Browser protocol from {BROWSER_PROTOCOL_FILE}")
    urlretrieve(BROWSER_PROTOCOL_FILE, browser_protocol_path)

    print("✅ Protocol files downloaded successfully")

    return str(js_protocol_path), str(browser_protocol_path)


def main():
    """Main entry point for the generator."""
    try:
        # Download protocol files
        js_file, browser_file = download_protocol_files()

        # Create generator and run it
        generator = CDPGenerator()
        generator.generate_all(protocol_files=[js_file, browser_file])

        print("🎉 CDP type-safe client generation completed!")
        print("")
        print("📖 Usage:")
        print("   from cdp_use.client import CDPClient")
        print("   # cdp.send.Target.getTargets() - fully type safe!")

    except Exception as e:
        print(f"❌ Error during generation: {e}")
        raise


if __name__ == "__main__":
    main()
