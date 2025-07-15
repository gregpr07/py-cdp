# Typesafe Event Registration

This CDP library now supports **typesafe event registration** that allows you to register event handlers with full type checking and IDE support.

## Features

✅ **Type Safety**: Event handlers are validated at compile time  
✅ **IDE Support**: Full autocomplete for domains and event methods  
✅ **Parameter Validation**: Callback signatures are type-checked  
✅ **Event Type Definitions**: Each event has its own TypedDict interface  

## Usage

### Basic Registration

```python
from cdp_use.client import CDPClient
from cdp_use.cdp.page.events import FrameAttachedEvent
from typing import Optional

def on_frame_attached(event: FrameAttachedEvent, session_id: Optional[str]) -> None:
    print(f"Frame {event['frameId']} attached to {event['parentFrameId']}")

# Register the handler
client = CDPClient("ws://localhost:9222/devtools/page/...")
client.register.Page.frame_attached(on_frame_attached)
```

### Available Syntax

The registration system follows this pattern:

```python
client.register.Domain.event_name(callback_function)
```

Where:
- `Domain` is any CDP domain (Page, Runtime, Network, etc.)
- `event_name` is the snake_case version of the CDP event name
- `callback_function` must accept `(event_data, session_id)` parameters

### Type Safety Examples

**✅ Correct Usage:**
```python
def handle_console(event: ConsoleAPICalledEvent, session_id: Optional[str]) -> None:
    print(f"Console: {event['type']}")

client.register.Runtime.console_api_called(handle_console)
```

**❌ Type Error - Wrong signature:**
```python
def bad_handler(event):  # Missing session_id parameter
    pass

client.register.Runtime.console_api_called(bad_handler)  # Type error!
```

**❌ Type Error - Wrong event type:**
```python
def bad_handler(event: FrameAttachedEvent, session_id: Optional[str]) -> None:
    pass

# This will cause a type error because ConsoleAPICalledEvent is expected
client.register.Runtime.console_api_called(bad_handler)  # Type error!
```

### Complete Example

```python
import asyncio
from typing import Optional
from cdp_use.client import CDPClient
from cdp_use.cdp.page.events import FrameAttachedEvent, DomContentEventFiredEvent
from cdp_use.cdp.runtime.events import ConsoleAPICalledEvent, ExceptionThrownEvent

def on_frame_attached(event: FrameAttachedEvent, session_id: Optional[str]) -> None:
    print(f"🖼️  New frame: {event['frameId']}")

def on_dom_ready(event: DomContentEventFiredEvent, session_id: Optional[str]) -> None:
    print(f"📄 DOM ready at: {event['timestamp']}")

def on_console(event: ConsoleAPICalledEvent, session_id: Optional[str]) -> None:
    args = [str(arg.get('value', '')) for arg in event.get('args', [])]
    print(f"🚨 Console.{event['type']}: {' '.join(args)}")

def on_error(event: ExceptionThrownEvent, session_id: Optional[str]) -> None:
    details = event['exceptionDetails']
    print(f"💥 JavaScript Error: {details['text']}")

async def main():
    async with CDPClient("ws://localhost:9222/devtools/page/...") as client:
        # Register all event handlers
        client.register.Page.frame_attached(on_frame_attached)
        client.register.Page.dom_content_event_fired(on_dom_ready)
        client.register.Runtime.console_api_called(on_console)
        client.register.Runtime.exception_thrown(on_error)
        
        # Enable the domains to start receiving events
        await client.send.Page.enable()
        await client.send.Runtime.enable()
        
        # Navigate to a page
        await client.send.Page.navigate({"url": "https://example.com"})
        
        # Keep the client running to receive events
        await asyncio.sleep(10)

if __name__ == "__main__":
    asyncio.run(main())
```

## Available Domains

The registration system supports all CDP domains that have events:

- **Page**: `client.register.Page.*` - Page lifecycle, navigation, frames
- **Runtime**: `client.register.Runtime.*` - JavaScript execution, console, exceptions  
- **Network**: `client.register.Network.*` - HTTP requests, responses, WebSocket
- **DOM**: `client.register.DOM.*` - DOM tree changes, attributes
- **CSS**: `client.register.CSS.*` - Stylesheet changes, media queries
- **Debugger**: `client.register.Debugger.*` - Breakpoints, script parsing
- **Performance**: `client.register.Performance.*` - Performance metrics
- **Security**: `client.register.Security.*` - Security state changes
- And many more...

## Event Type Definitions

Each event has its own TypedDict that defines the available fields:

```python
# Example: FrameAttachedEvent
class FrameAttachedEvent(TypedDict):
    frameId: "FrameId"              # Required field
    parentFrameId: "FrameId"        # Required field  
    stack: "NotRequired[StackTrace]" # Optional field
```

This provides:
- **Autocomplete** in your IDE for event fields
- **Type validation** when accessing event data
- **Documentation** of available fields and their types

## Generator Integration

The event registration system is fully integrated into the CDP generator:

1. **Automatic Generation**: Registration interfaces are generated from CDP protocol specs
2. **Type Consistency**: Event types match exactly with the CDP protocol definitions
3. **Domain Organization**: Each domain gets its own registration class
4. **Method Naming**: CDP event names are converted to Python snake_case

To regenerate after protocol updates:

```bash
python -m cdp_use.generator
```

## Architecture

The system consists of several generated components:

- **`EventRegistry`**: Central registry managing all event callbacks
- **`CDPRegistrationLibrary`**: Main registration interface with domain properties
- **`DomainRegistration`**: Per-domain registration classes (e.g., `PageRegistration`)
- **Event TypedDicts**: Type definitions for each event

The `CDPClient` integrates these components and automatically dispatches incoming events to registered handlers.