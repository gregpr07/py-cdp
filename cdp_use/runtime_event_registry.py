"""
Runtime Domain Event Registry

Provides typesafe event registration for Runtime domain events.
"""

from typing import TYPE_CHECKING, Callable, Optional

from .event_registry import EventRegistry

if TYPE_CHECKING:
    from .cdp.runtime.events import (
        BindingCalledEvent,
        ConsoleAPICalledEvent,
        ExceptionRevokedEvent,
        ExceptionThrownEvent,
        ExecutionContextCreatedEvent,
        ExecutionContextDestroyedEvent,
        ExecutionContextsClearedEvent,
        InspectRequestedEvent,
    )


class RuntimeEventRegistry:
    """Type-safe event registry for Runtime domain events."""
    
    def __init__(self, registry: EventRegistry):
        self._registry = registry
    
    def bindingCalled(
        self, 
        handler: Callable[["BindingCalledEvent", Optional[str]], None]
    ) -> None:
        """Register handler for Runtime.bindingCalled event."""
        self._registry.register_handler("Runtime.bindingCalled", handler)
    
    def consoleAPICalled(
        self, 
        handler: Callable[["ConsoleAPICalledEvent", Optional[str]], None]
    ) -> None:
        """Register handler for Runtime.consoleAPICalled event."""
        self._registry.register_handler("Runtime.consoleAPICalled", handler)
    
    def exceptionRevoked(
        self, 
        handler: Callable[["ExceptionRevokedEvent", Optional[str]], None]
    ) -> None:
        """Register handler for Runtime.exceptionRevoked event."""
        self._registry.register_handler("Runtime.exceptionRevoked", handler)
    
    def exceptionThrown(
        self, 
        handler: Callable[["ExceptionThrownEvent", Optional[str]], None]
    ) -> None:
        """Register handler for Runtime.exceptionThrown event."""
        self._registry.register_handler("Runtime.exceptionThrown", handler)
    
    def executionContextCreated(
        self, 
        handler: Callable[["ExecutionContextCreatedEvent", Optional[str]], None]
    ) -> None:
        """Register handler for Runtime.executionContextCreated event."""
        self._registry.register_handler("Runtime.executionContextCreated", handler)
    
    def executionContextDestroyed(
        self, 
        handler: Callable[["ExecutionContextDestroyedEvent", Optional[str]], None]
    ) -> None:
        """Register handler for Runtime.executionContextDestroyed event."""
        self._registry.register_handler("Runtime.executionContextDestroyed", handler)
    
    def executionContextsCleared(
        self, 
        handler: Callable[["ExecutionContextsClearedEvent", Optional[str]], None]
    ) -> None:
        """Register handler for Runtime.executionContextsCleared event."""
        self._registry.register_handler("Runtime.executionContextsCleared", handler)
    
    def inspectRequested(
        self, 
        handler: Callable[["InspectRequestedEvent", Optional[str]], None]
    ) -> None:
        """Register handler for Runtime.inspectRequested event."""
        self._registry.register_handler("Runtime.inspectRequested", handler)