"""
Page Domain Event Registry

Provides typesafe event registration for Page domain events.
"""

from typing import TYPE_CHECKING, Callable, Optional

from .event_registry import EventRegistry

if TYPE_CHECKING:
    from .cdp.page.events import (
        DomContentEventFiredEvent,
        FileChooserOpenedEvent,
        FrameAttachedEvent,
        FrameClearedScheduledNavigationEvent,
        FrameDetachedEvent,
        FrameSubtreeWillBeDetachedEvent,
        FrameNavigatedEvent,
        # Add other page events as needed
    )


class PageEventRegistry:
    """Type-safe event registry for Page domain events."""
    
    def __init__(self, registry: EventRegistry):
        self._registry = registry
    
    def domContentEventFired(
        self, 
        handler: Callable[["DomContentEventFiredEvent", Optional[str]], None]
    ) -> None:
        """Register handler for Page.domContentEventFired event."""
        self._registry.register_handler("Page.domContentEventFired", handler)
    
    def fileChooserOpened(
        self, 
        handler: Callable[["FileChooserOpenedEvent", Optional[str]], None]
    ) -> None:
        """Register handler for Page.fileChooserOpened event."""
        self._registry.register_handler("Page.fileChooserOpened", handler)
    
    def frameAttached(
        self, 
        handler: Callable[["FrameAttachedEvent", Optional[str]], None]
    ) -> None:
        """Register handler for Page.frameAttached event."""
        self._registry.register_handler("Page.frameAttached", handler)
    
    def frameClearedScheduledNavigation(
        self, 
        handler: Callable[["FrameClearedScheduledNavigationEvent", Optional[str]], None]
    ) -> None:
        """Register handler for Page.frameClearedScheduledNavigation event."""
        self._registry.register_handler("Page.frameClearedScheduledNavigation", handler)
    
    def frameDetached(
        self, 
        handler: Callable[["FrameDetachedEvent", Optional[str]], None]
    ) -> None:
        """Register handler for Page.frameDetached event."""
        self._registry.register_handler("Page.frameDetached", handler)
    
    def frameSubtreeWillBeDetached(
        self, 
        handler: Callable[["FrameSubtreeWillBeDetachedEvent", Optional[str]], None]
    ) -> None:
        """Register handler for Page.frameSubtreeWillBeDetached event."""
        self._registry.register_handler("Page.frameSubtreeWillBeDetached", handler)
    
    def frameNavigated(
        self, 
        handler: Callable[["FrameNavigatedEvent", Optional[str]], None]
    ) -> None:
        """Register handler for Page.frameNavigated event."""
        self._registry.register_handler("Page.frameNavigated", handler)