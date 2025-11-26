"""Event bus and pub/sub system for inter-module communication."""

import asyncio
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional
from datetime import datetime


@dataclass
class Event:
    """Base event class."""

    event_type: str
    source: str = "system"
    timestamp: datetime = field(default_factory=datetime.utcnow)
    data: Dict[str, Any] = field(default_factory=dict)

    def __repr__(self) -> str:
        """String representation."""
        return f"<Event(type={self.event_type}, source={self.source})>"


@dataclass
class SearchStartedEvent(Event):
    """Event fired when search starts."""

    event_type: str = "search.started"


@dataclass
class SearchProgressEvent(Event):
    """Event fired during search progress."""

    event_type: str = "search.progress"


@dataclass
class SearchCompleteEvent(Event):
    """Event fired when search completes."""

    event_type: str = "search.completed"


@dataclass
class ProfileFoundEvent(Event):
    """Event fired when profile is found."""

    event_type: str = "profile.found"


@dataclass
class ProfileNotFoundEvent(Event):
    """Event fired when profile is not found."""

    event_type: str = "profile.not_found"


@dataclass
class TargetCreatedEvent(Event):
    """Event fired when target is created."""

    event_type: str = "target.created"


@dataclass
class TargetUpdatedEvent(Event):
    """Event fired when target is updated."""

    event_type: str = "target.updated"


class EventBus:
    """Publish/Subscribe event bus for async event handling."""

    def __init__(self):
        """Initialize event bus."""
        self.subscribers: Dict[str, List[Callable]] = {}
        self.event_queue: asyncio.Queue = asyncio.Queue()
        self.running = False

    def subscribe(self, event_type: str, handler: Callable) -> None:
        """Subscribe to event type.

        Args:
            event_type: Event type to subscribe to (use "*" for all events)
            handler: Async handler function that takes Event as argument
        """
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(handler)

    def unsubscribe(self, event_type: str, handler: Callable) -> None:
        """Unsubscribe from event type.

        Args:
            event_type: Event type to unsubscribe from
            handler: Handler function to remove
        """
        if event_type in self.subscribers:
            self.subscribers[event_type] = [
                h for h in self.subscribers[event_type] if h != handler
            ]

    async def publish(self, event: Event) -> None:
        """Publish event to all subscribers.

        Args:
            event: Event to publish
        """
        await self.event_queue.put(event)

    async def _process_event(self, event: Event) -> None:
        """Process single event and call handlers.

        Args:
            event: Event to process
        """
        # Call specific event type handlers
        if event.event_type in self.subscribers:
            for handler in self.subscribers[event.event_type]:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        await handler(event)
                    else:
                        handler(event)
                except Exception as e:
                    # Log error but don't break event processing
                    print(f"Error in event handler: {e}")

        # Call wildcard handlers
        if "*" in self.subscribers:
            for handler in self.subscribers["*"]:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        await handler(event)
                    else:
                        handler(event)
                except Exception as e:
                    print(f"Error in event handler: {e}")

    async def run(self) -> None:
        """Run event loop. Should be called as background task."""
        self.running = True
        try:
            while self.running:
                try:
                    # Get event with timeout to allow graceful shutdown
                    event = await asyncio.wait_for(self.event_queue.get(), timeout=1.0)
                    await self._process_event(event)
                except asyncio.TimeoutError:
                    continue
        finally:
            self.running = False

    async def stop(self) -> None:
        """Stop event bus."""
        self.running = False

    async def wait_empty(self) -> None:
        """Wait until event queue is empty."""
        await self.event_queue.join()


# Global event bus instance
_event_bus: Optional[EventBus] = None


def get_event_bus() -> EventBus:
    """Get global event bus instance."""
    global _event_bus
    if _event_bus is None:
        _event_bus = EventBus()
    return _event_bus


async def start_event_bus() -> EventBus:
    """Start global event bus as background task."""
    global _event_bus
    _event_bus = EventBus()
    asyncio.create_task(_event_bus.run())
    return _event_bus
