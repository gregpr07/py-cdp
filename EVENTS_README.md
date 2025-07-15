# Typesafe Event Registration System

This document explains how to use the new typesafe event registration system for Chrome DevTools Protocol (CDP) events.

## Overview

The event registration system provides compile-time type safety when registering event handlers for CDP events. Instead of manually managing event handlers, you can register them in a type-safe manner using the `cdp_client.register` interface.

## Basic Usage

```python
import asyncio
from typing import Optional
from cdp_use.client import CDPClient
from cdp_use.cdp.page.events import DomContentEventFiredEvent, FrameAttachedEvent

async def main():
    # Create CDP client
    cdp_client = CDPClient("ws://localhost:9222/devtools/page/YOUR_PAGE_ID")
    
    # Define your event handlers with proper type annotations
    def on_dom_content_loaded(event: DomContentEventFiredEvent, session_id: Optional[str] = None):
        print(f"DOM content loaded at timestamp: {event['timestamp']}")
        if session_id:
            print(f"Session ID: {session_id}")
    
    def on_frame_attached(event: FrameAttachedEvent, session_id: Optional[str] = None):
        print(f"Frame attached: {event['frameId']} to parent {event['parentFrameId']}")
    
    # Register event handlers (TYPE SAFE!)
    cdp_client.register.Page.domContentEventFired(on_dom_content_loaded)
    cdp_client.register.Page.frameAttached(on_frame_attached)
    
    # Start the client
    async with cdp_client:
        await cdp_client.send.Page.enable()
        await cdp_client.send.Page.navigate({"url": "https://example.com"})
        await asyncio.sleep(10)  # Listen for events

if __name__ == "__main__":
    asyncio.run(main())
```

## Type Safety Features

### 1. Compile-time Type Checking

The system ensures that your event handler function signature matches the expected event type:

```python
# ✅ CORRECT: Handler matches DomContentEventFiredEvent
def correct_handler(event: DomContentEventFiredEvent, session_id: Optional[str] = None):
    print(event['timestamp'])  # TypedDict ensures 'timestamp' exists

# ❌ WRONG: Type checker will catch this
def wrong_handler(event: SomeOtherEventType, session_id: Optional[str] = None):
    pass  # Type error! Handler doesn't match expected event type

cdp_client.register.Page.domContentEventFired(wrong_handler)  # Type error!
```

### 2. IntelliSense/Autocomplete Support

Your IDE will provide full autocomplete support for:
- Available event registration methods
- Event properties within handlers
- Proper type annotations

### 3. Event Property Access

Event parameters are strongly typed using TypedDict classes:

```python
def on_frame_attached(event: FrameAttachedEvent, session_id: Optional[str] = None):
    # Type checker knows these properties exist
    frame_id = event['frameId']        # Required property
    parent_id = event['parentFrameId'] # Required property
    
    # Optional properties require checking
    if 'stack' in event:
        stack = event['stack']  # Optional stack trace
```

## Available Domains

Currently implemented domains:

### Page Domain
- `cdp_client.register.Page.domContentEventFired(handler)`
- `cdp_client.register.Page.frameAttached(handler)`
- `cdp_client.register.Page.frameDetached(handler)`
- `cdp_client.register.Page.frameNavigated(handler)`
- And more...

### Runtime Domain
- `cdp_client.register.Runtime.consoleAPICalled(handler)`
- `cdp_client.register.Runtime.exceptionThrown(handler)`
- `cdp_client.register.Runtime.executionContextCreated(handler)`
- And more...

## Handler Function Signature

All event handlers must follow this signature:

```python
def handler_function(event: EventTypeHere, session_id: Optional[str] = None) -> None:
    # Your event handling logic here
    pass
```

Where:
- `event`: The strongly-typed event data (TypedDict)
- `session_id`: Optional CDP session identifier
- Return type: `None` (handlers don't return values)

## Advanced Usage

### Lambda Functions

You can use lambda functions for simple handlers:

```python
cdp_client.register.Page.frameDetached(
    lambda event, session_id=None: print(f"Frame {event['frameId']} detached")
)
```

Note: Lambda functions lose some type safety benefits compared to properly annotated functions.

### Session-specific Handling

Handle events differently based on session ID:

```python
def on_console_message(event: ConsoleAPICalledEvent, session_id: Optional[str] = None):
    if session_id == "main_session":
        print(f"Main session console: {event['args']}")
    else:
        print(f"Other session console: {event['args']}")

cdp_client.register.Runtime.consoleAPICalled(on_console_message)
```

### Error Handling

Event handlers are automatically wrapped with error handling. If your handler raises an exception, it will be logged but won't crash the CDP client:

```python
def risky_handler(event: DomContentEventFiredEvent, session_id: Optional[str] = None):
    # If this raises an exception, it will be logged and contained
    risky_operation()
    
cdp_client.register.Page.domContentEventFired(risky_handler)
```

## Integration with Existing Code

The event registration system is fully integrated with the existing CDP client:

1. **Automatic event routing**: Events are automatically routed to registered handlers
2. **No conflicts**: Works alongside existing `send` API for commands
3. **Session support**: Full support for multi-session scenarios
4. **Logging**: Comprehensive logging for debugging

## Extending to Other Domains

To add support for other domains, create a new event registry file:

```python
# Example: dom_event_registry.py
from typing import TYPE_CHECKING, Callable, Optional
from .event_registry import EventRegistry

if TYPE_CHECKING:
    from .cdp.dom.events import AttributeModifiedEvent, NodeRemovedEvent

class DOMEventRegistry:
    def __init__(self, registry: EventRegistry):
        self._registry = registry
    
    def attributeModified(
        self, 
        handler: Callable[["AttributeModifiedEvent", Optional[str]], None]
    ) -> None:
        """Register handler for DOM.attributeModified event."""
        self._registry.register_handler("DOM.attributeModified", handler)
    
    def nodeRemoved(
        self, 
        handler: Callable[["NodeRemovedEvent", Optional[str]], None]
    ) -> None:
        """Register handler for DOM.nodeRemoved event."""
        self._registry.register_handler("DOM.nodeRemoved", handler)
```

Then add it to `EventRegistryLibrary`:

```python
from .dom_event_registry import DOMEventRegistry

class EventRegistryLibrary:
    def __init__(self):
        self._registry = EventRegistry()
        self.Page = PageEventRegistry(self._registry)
        self.Runtime = RuntimeEventRegistry(self._registry)
        self.DOM = DOMEventRegistry(self._registry)  # Add new domain
```

## Debugging

### Check Registered Handlers

```python
# See what events have handlers registered
registered_methods = cdp_client.register.get_registered_methods()
print(f"Registered handlers: {registered_methods}")
```

### Event Logging

Enable debug logging to see event flow:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# You'll see logs like:
# DEBUG:cdp_use.client:Received event: Page.frameAttached (session: None)
# DEBUG:cdp_use.event_registry:Registered handler for: Page.frameAttached
```

## Benefits

1. **Type Safety**: Catch errors at compile time, not runtime
2. **IDE Support**: Full autocomplete and IntelliSense
3. **Documentation**: Self-documenting code with type hints
4. **Maintainability**: Easier to refactor and maintain
5. **Error Prevention**: Prevent common event handling mistakes
6. **Performance**: No runtime type checking overhead

## Limitations

1. Currently only Page and Runtime domains are implemented
2. Some domains may not have events (those will be no-ops)
3. Lambda functions lose some type safety benefits
4. Requires proper TypedDict imports for full type safety

The system is designed to be easily extensible - adding new domain support is straightforward following the established pattern.