"""
Event Registry System for CDP Client

Provides typesafe event registration for Chrome DevTools Protocol events.
Allows registration of handlers with compile-time type checking.
"""

import logging
from typing import Any, Callable, Dict, Optional, Protocol, TypeVar

logger = logging.getLogger(__name__)

# Type variable for event data
EventData = TypeVar('EventData')

class EventHandler(Protocol[EventData]):
    """Protocol for event handler functions."""
    def __call__(self, event_data: EventData, session_id: Optional[str] = None) -> None:
        """Handle an event with the specified data and optional session ID."""
        ...

class EventRegistry:
    """Registry for CDP event handlers."""
    
    def __init__(self):
        self._handlers: Dict[str, Callable[[Any, Optional[str]], None]] = {}
    
    def register_handler(self, method: str, handler: Callable[[Any, Optional[str]], None]) -> None:
        """Register an event handler for a specific method."""
        if method in self._handlers:
            logger.warning(f"Overriding existing handler for method: {method}")
        self._handlers[method] = handler
        logger.debug(f"Registered handler for: {method}")
    
    def unregister_handler(self, method: str) -> None:
        """Unregister an event handler."""
        if method in self._handlers:
            del self._handlers[method]
            logger.debug(f"Unregistered handler for: {method}")
    
    def handle_event(self, method: str, params: Any, session_id: Optional[str] = None) -> bool:
        """Handle an event if a handler is registered. Returns True if handled."""
        if method in self._handlers:
            try:
                self._handlers[method](params, session_id)
                return True
            except Exception as e:
                logger.error(f"Error in event handler for {method}: {e}")
                return True  # Still consumed, even though it failed
        return False
    
    def get_registered_methods(self) -> list[str]:
        """Get list of all registered event methods."""
        return list(self._handlers.keys())