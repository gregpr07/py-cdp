"""
Event Registry Library for CDP Client

Provides typesafe event registration for all Chrome DevTools Protocol domains.
"""

from typing import TYPE_CHECKING

from .event_registry import EventRegistry
from .page_event_registry import PageEventRegistry
from .runtime_event_registry import RuntimeEventRegistry

if TYPE_CHECKING:
    pass

class EventRegistryLibrary:
    """Main event registry library with domain-specific event registries."""
    
    def __init__(self):
        self._registry = EventRegistry()
        
        # Page domain events
        self.Page = PageEventRegistry(self._registry)
        
        # Runtime domain events
        self.Runtime = RuntimeEventRegistry(self._registry)
        
        # TODO: Add other domain event registries as needed
        # self.DOM = DOMEventRegistry(self._registry)
        # self.Network = NetworkEventRegistry(self._registry)
        # etc.
    
    def handle_event(self, method: str, params: any, session_id: str | None = None) -> bool:
        """Handle an event through the registry. Returns True if handled."""
        return self._registry.handle_event(method, params, session_id)
    
    def get_registered_methods(self) -> list[str]:
        """Get list of all registered event methods."""
        return self._registry.get_registered_methods()