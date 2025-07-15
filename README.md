# CDP Use

A **type-safe Python client generator** for the **Chrome DevTools Protocol (CDP)**. This library automatically generates Python bindings with full TypeScript-like type safety from the official CDP protocol specifications.

## 🚀 Features

- **🔒 Type Safety**: Full type hints with `TypedDict` classes for all CDP commands, parameters, and return types
- **🎯 Event Registration**: Typesafe event handlers with full IDE support
- **🏗️ Auto-Generated**: Code generated directly from official Chrome DevTools Protocol specifications
- **🎯 IntelliSense Support**: Perfect IDE autocompletion and type checking
- **📦 Domain Separation**: Clean organization with separate modules for each CDP domain
- **🔄 Always Up-to-Date**: Easy regeneration from latest protocol specs

## 🛠️ Installation & Setup

1. **Clone and install dependencies:**

```bash
git clone https://github.com/browser-use/cdp-use
cd cdp-use
uv sync  # or pip install -r requirements.txt
```

2. **Generate the CDP client library:**

```bash
python -m cdp_use.generator
```

This automatically downloads the latest protocol specifications and generates all type-safe bindings.

## 📖 Usage Examples

### Basic Usage

```python
import asyncio
from cdp_use.client import CDPClient

async def main():
    # Connect to Chrome DevTools
    async with CDPClient("ws://localhost:9222/devtools/browser/...") as cdp:
        # Get all browser targets with full type safety
        targets = await cdp.send.Target.getTargets()
        print(f"Found {len(targets['targetInfos'])} targets")

        # Navigate to a page
        await cdp.send.Page.navigate({"url": "https://example.com"})

asyncio.run(main())
```

### Type Safety in Action

```python
# ✅ Fully typed parameters
await cdp.send.Runtime.evaluate(params={
    "expression": "document.title",
    "returnByValue": True
})

# ✅ Return types are fully typed
result = await cdp.send.DOM.getDocument(params={"depth": 1})
node_id: int = result["root"]["nodeId"]  # Full IntelliSense support

# ❌ Type errors caught at development time
await cdp.send.DOM.getDocument(params={"invalid": "param"})  # Type error!
```

## 🎧 Event Registration

The library provides **typesafe event registration** with full IDE support:

### Basic Event Registration

```python
import asyncio
from cdp_use.client import CDPClient
from cdp_use.cdp.page.events import FrameAttachedEvent, DomContentEventFiredEvent
from cdp_use.cdp.runtime.events import ConsoleAPICalledEvent
from typing import Optional

def on_frame_attached(event: FrameAttachedEvent, session_id: Optional[str]) -> None:
    print(f"Frame {event['frameId']} attached to {event['parentFrameId']}")

def on_dom_content_loaded(event: DomContentEventFiredEvent, session_id: Optional[str]) -> None:
    print(f"DOM content loaded at: {event['timestamp']}")

def on_console_message(event: ConsoleAPICalledEvent, session_id: Optional[str]) -> None:
    print(f"Console: {event['type']}")

async def main():
    async with CDPClient("ws://localhost:9222/devtools/page/...") as client:
        # Register event handlers with camelCase method names (matching CDP)
        client.register.Page.frameAttached(on_frame_attached)
        client.register.Page.domContentEventFired(on_dom_content_loaded)
        client.register.Runtime.consoleAPICalled(on_console_message)

        # Enable domains to start receiving events
        await client.send.Page.enable()
        await client.send.Runtime.enable()

        # Navigate and receive events
        await client.send.Page.navigate({"url": "https://example.com"})
        await asyncio.sleep(5)  # Keep listening for events
```

### Event Registration Features

✅ **Type Safety**: Event handlers are validated at compile time  
✅ **IDE Support**: Full autocomplete for domains and event methods  
✅ **Parameter Validation**: Callback signatures are type-checked  
✅ **Event Type Definitions**: Each event has its own TypedDict interface

### Registration Syntax

```python
client.register.Domain.eventName(callback_function)
```

Where:

- `Domain` is any CDP domain (Page, Runtime, Network, etc.)
- `eventName` is the camelCase CDP event name (matching CDP specs)
- `callback_function` must accept `(event_data, session_id)` parameters

### Available Event Domains

- **Page**: `client.register.Page.*` - Page lifecycle, navigation, frames
- **Runtime**: `client.register.Runtime.*` - JavaScript execution, console, exceptions
- **Network**: `client.register.Network.*` - HTTP requests, responses, WebSocket
- **DOM**: `client.register.DOM.*` - DOM tree changes, attributes
- **CSS**: `client.register.CSS.*` - Stylesheet changes, media queries
- **Debugger**: `client.register.Debugger.*` - Breakpoints, script parsing
- **Performance**: `client.register.Performance.*` - Performance metrics
- **Security**: `client.register.Security.*` - Security state changes
- And many more...

### Type Safety Examples

**✅ Correct Usage:**

```python
def handle_console(event: ConsoleAPICalledEvent, session_id: Optional[str]) -> None:
    print(f"Console: {event['type']}")

client.register.Runtime.consoleAPICalled(handle_console)
```

**❌ Type Error - Wrong signature:**

```python
def bad_handler(event):  # Missing session_id parameter
    pass

client.register.Runtime.consoleAPICalled(bad_handler)  # Type error!
```

## 📋 What Gets Generated

```
cdp_use/cdp/
├── library.py                    # Main CDPLibrary class
├── registry.py                   # Event registry system
├── registration_library.py       # Event registration interface
├── dom/                          # DOM domain
│   ├── types.py                 # DOM-specific types
│   ├── commands.py              # Command parameter/return types
│   ├── events.py                # Event types
│   ├── library.py               # DOMClient class
│   └── registration.py          # DOM event registration
├── page/                         # Page domain
│   └── ...
└── ... (50+ domains total)
```

## 🏛️ Architecture

### Main Components

```python
class CDPClient:
    def __init__(self, url: str):
        self.send: CDPLibrary                    # Send commands
        self.register: CDPRegistrationLibrary    # Register events

# Domain-specific clients
class CDPLibrary:
    def __init__(self, client: CDPClient):
        self.DOM = DOMClient(client)           # DOM operations
        self.Network = NetworkClient(client)   # Network monitoring
        self.Runtime = RuntimeClient(client)   # JavaScript execution
        # ... 50+ more domains

# Event registration
class CDPRegistrationLibrary:
    def __init__(self, registry: EventRegistry):
        self.Page = PageRegistration(registry)
        self.Runtime = RuntimeRegistration(registry)
        # ... all domains with events
```

## 🔧 Development

### Regenerating Types

```bash
python -m cdp_use.generator
```

This will:

1. Download the latest protocol files from Chrome DevTools repository
2. Generate all Python type definitions and event registrations
3. Create domain-specific client classes
4. Format the code

### Project Structure

```
cdp-use/
├── cdp_use/
│   ├── client.py              # Core CDP WebSocket client
│   ├── generator/             # Code generation tools
│   └── cdp/                   # Generated CDP library (auto-generated)
├── simple.py                  # Example usage
└── README.md
```

## 🤝 Contributing

1. Fork the repository
2. Make changes to generator code (not the generated `cdp_use/cdp/` directory)
3. Run `python -m cdp_use.generator` to regenerate
4. Test with `python simple.py`
5. Submit a pull request

## 🔗 Related

- [Chrome DevTools Protocol Documentation](https://chromedevtools.github.io/devtools-protocol/)
- [Official Protocol Repository](https://github.com/ChromeDevTools/devtools-protocol)

---

**Generated from Chrome DevTools Protocol specifications • Type-safe • Zero runtime overhead**
