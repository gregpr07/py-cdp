#!/usr/bin/env python3
"""
Example demonstrating typesafe event registration with the CDP client.

This example shows how to register event handlers in a type-safe manner.
"""

import asyncio
from typing import Optional

from cdp_use.client import CDPClient
from cdp_use.cdp.page.events import DomContentEventFiredEvent, FrameAttachedEvent
from cdp_use.cdp.runtime.events import ConsoleAPICalledEvent, ExceptionThrownEvent


async def main():
    """Example of using the typesafe event registration system."""
    
    # Example event handlers with proper type annotations
    def on_dom_content_loaded(event: DomContentEventFiredEvent, session_id: Optional[str] = None):
        """Handle DOM content loaded event."""
        print(f"DOM content loaded at timestamp: {event['timestamp']}")
        if session_id:
            print(f"Session ID: {session_id}")
    
    def on_frame_attached(event: FrameAttachedEvent, session_id: Optional[str] = None):
        """Handle frame attached event."""
        print(f"Frame attached: {event['frameId']} to parent {event['parentFrameId']}")
        if 'stack' in event:
            print(f"Stack trace available: {event['stack']}")
        if session_id:
            print(f"Session ID: {session_id}")
    
    def on_console_api_called(event: ConsoleAPICalledEvent, session_id: Optional[str] = None):
        """Handle console API calls (console.log, console.error, etc.)."""
        print(f"Console {event['type']}: {[arg.get('value', str(arg)) for arg in event['args']]}")
        if session_id:
            print(f"Session ID: {session_id}")
    
    def on_exception_thrown(event: ExceptionThrownEvent, session_id: Optional[str] = None):
        """Handle JavaScript exceptions."""
        exception_details = event['exceptionDetails']
        print(f"Exception: {exception_details['text']}")
        if 'url' in exception_details:
            print(f"At: {exception_details['url']}:{exception_details.get('lineNumber', '?')}")
        if session_id:
            print(f"Session ID: {session_id}")

    # Create CDP client
    cdp_client = CDPClient("ws://localhost:9222/devtools/page/YOUR_PAGE_ID")
    
    # Register event handlers with type safety
    # The type checker will ensure the handler function signature matches the event type
    
    # Page domain events
    cdp_client.register.Page.domContentEventFired(on_dom_content_loaded)
    cdp_client.register.Page.frameAttached(on_frame_attached)
    
    # Runtime domain events  
    cdp_client.register.Runtime.consoleAPICalled(on_console_api_called)
    cdp_client.register.Runtime.exceptionThrown(on_exception_thrown)
    
    # You can also use lambda functions (though they lose some type safety)
    cdp_client.register.Page.frameDetached(
        lambda event, session_id=None: print(f"Frame detached: {event['frameId']}")
    )
    
    # Start the client and enable events
    async with cdp_client:
        # Enable domains to start receiving events
        await cdp_client.send.Page.enable()
        await cdp_client.send.Runtime.enable()
        
        # Navigate to a page to trigger events
        await cdp_client.send.Page.navigate({"url": "https://example.com"})
        
        # Keep the client running to receive events
        print("Listening for events... Press Ctrl+C to stop")
        try:
            await asyncio.sleep(30)  # Listen for 30 seconds
        except KeyboardInterrupt:
            print("Stopping...")


if __name__ == "__main__":
    asyncio.run(main())