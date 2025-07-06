# CDP Use

A **type-safe Python client generator** for the **Chrome DevTools Protocol (CDP)**. This library automatically generates Python bindings with full TypeScript-like type safety from the official CDP protocol specifications.

## 🚀 Features

- **🔒 Type Safety**: Full type hints with `TypedDict` classes for all CDP commands, parameters, and return types
- **🏗️ Auto-Generated**: Code generated directly from official Chrome DevTools Protocol specifications
- **🎯 IntelliSense Support**: Perfect IDE autocompletion and type checking
- **📦 Domain Separation**: Clean organization with separate modules for each CDP domain (DOM, Network, Runtime, etc.)
- **🔄 Always Up-to-Date**: Easy regeneration from latest protocol specs
- **🚫 No Runtime Overhead**: Pure Python types with no validation libraries required

## 📋 What Gets Generated

The generator creates a complete type-safe CDP client library:

```
cdp_use/cdp/
├── library.py              # Main CDPLibrary class
├── dom/                     # DOM domain
│   ├── types.py            # DOM-specific types
│   ├── commands.py         # Command parameter/return types
│   ├── events.py           # Event types
│   └── library.py          # DOMClient class
├── network/                # Network domain
│   └── ...
├── runtime/                # Runtime domain
│   └── ...
└── ... (50+ domains total)
```

## 🛠️ Installation & Setup

1. **Clone and install dependencies:**

```bash
git clone https://github.com/browser-use/cdp-use
cd cdp-use
uv sync  # or pip install -r requirements.txt
```

2. **Generate the CDP client library:**

```bash
python -m cdp_use.generator.generate
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

        # Attach to a page target
        page_target = next(t for t in targets["targetInfos"] if t["type"] == "page")
        session = await cdp.send.Target.attachToTarget(params={
            "targetId": page_target["targetId"],
            "flatten": True
        })

        # Enable DOM and get document with type safety
        await cdp.send.DOM.enable(session_id=session["sessionId"])
        document = await cdp.send.DOM.getDocument(
            params={"depth": -1, "pierce": True},
            session_id=session["sessionId"]
        )

        print(f"Root node ID: {document['root']['nodeId']}")

asyncio.run(main())
```

### Type Safety in Action

The generated library provides complete type safety:

```python
# ✅ Fully typed parameters
await cdp.send.Runtime.evaluate(params={
    "expression": "document.title",
    "returnByValue": True,
    "awaitPromise": True
})

# ✅ Optional parameters work correctly
await cdp.send.Target.getTargets()  # No params needed

# ✅ Return types are fully typed
result = await cdp.send.DOM.getDocument(params={"depth": 1})
node_id: int = result["root"]["nodeId"]  # Full IntelliSense support

# ❌ Type errors caught at development time
await cdp.send.DOM.getDocument(params={"invalid": "param"})  # Type error!
```

### Concurrent Operations

```python
# Execute multiple CDP commands concurrently with type safety
tasks = [
    cdp.send.DOM.getDocument(params={"depth": -1}, session_id=session_id)
    for _ in range(10)
]
results = await asyncio.gather(*tasks)
print(f"Completed {len(results)} concurrent requests")
```

## 🏛️ Architecture

### Generated Structure

- **Domain Libraries**: Each CDP domain (DOM, Network, Runtime, etc.) gets its own client class
- **Type Definitions**: Complete `TypedDict` classes for all CDP types, commands, and events
- **Main Library**: `CDPLibrary` class that combines all domain clients
- **Type Safety**: All method signatures use quoted type annotations to avoid runtime evaluation

### Key Components

```python
# Main library class
class CDPLibrary:
    def __init__(self, client: CDPClient):
        self.DOM = DOMClient(client)           # DOM operations
        self.Network = NetworkClient(client)   # Network monitoring
        self.Runtime = RuntimeClient(client)   # JavaScript execution
        self.Target = TargetClient(client)     # Target management
        # ... 50+ more domains

# Domain-specific client example
class DOMClient:
    async def getDocument(
        self,
        params: Optional[GetDocumentParameters] = None,
        session_id: Optional[str] = None
    ) -> GetDocumentReturns:
        # Fully type-safe implementation
```

## 🔧 Development

### Regenerating Types

To update to the latest CDP specifications:

```bash
python -m cdp_use.generator.generate
```

This will:

1. Download the latest protocol files from the official Chrome DevTools repository
2. Generate all Python type definitions
3. Create domain-specific client classes
4. Format the code with `ruff`
5. Add auto-generated file headers

### Project Structure

```
cdp-use/
├── cdp_use/
│   ├── client.py              # Core CDP WebSocket client
│   ├── generator/             # Code generation tools
│   │   ├── generator.py       # Main generator
│   │   ├── type_generator.py  # TypedDict generation
│   │   ├── command_generator.py # Command type generation
│   │   ├── event_generator.py # Event type generation
│   │   ├── library_generator.py # Client class generation
│   │   └── constants.py       # Protocol file URLs
│   └── cdp/                   # Generated CDP library (auto-generated)
├── simple.py                  # Example usage
└── README.md
```

## 🎯 Type Safety Features

### Quoted Type Annotations

All generated code uses quoted type annotations to prevent runtime evaluation issues:

```python
async def getDocument(
    self,
    params: Optional["GetDocumentParameters"] = None,
    session_id: Optional[str] = None,
) -> "GetDocumentReturns":
    return cast("GetDocumentReturns", await self._client.send_raw(...))
```

### Optional Parameter Handling

Commands with all-optional parameters are handled correctly:

```python
# These work without type errors:
await cdp.send.Target.getTargets()                    # No params
await cdp.send.Target.getTargets(params=None)         # Explicit None
await cdp.send.Target.getTargets(params={"filter": ...}) # With params
```

### Cross-Domain Type References

Types are properly imported across domains using `TYPE_CHECKING` blocks to avoid circular imports.

## 🤝 Contributing

1. Fork the repository
2. Make your changes to the generator code (not the generated `cdp_use/cdp/` directory)
3. Run `python -m cdp_use.generator.generate` to regenerate the library
4. Test your changes with `python simple.py`
5. Submit a pull request

## 📝 License

[Your License Here]

## 🔗 Related

- [Chrome DevTools Protocol Documentation](https://chromedevtools.github.io/devtools-protocol/)
- [Official Protocol Repository](https://github.com/ChromeDevTools/devtools-protocol)

---

**Generated from Chrome DevTools Protocol specifications • Type-safe • Zero runtime overhead**
