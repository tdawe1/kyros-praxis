from abc import ABC, abstractmethod
from typing import Callable, Dict, List


class EventBus(ABC):
    @abstractmethod
    async def publish(
        self, event_type: str, payload: dict, metadata: dict | None = None
    ): ...
    @abstractmethod
    def subscribe(
        self, event_type: str, handler: Callable[[dict, dict | None], None]
    ): ...


class LocalEventBus(EventBus):
    def __init__(self):
        self._h: Dict[str, List[Callable]] = {}

    def subscribe(self, event_type, handler):
        self._h.setdefault(event_type, []).append(handler)

    async def publish(self, event_type, payload, metadata=None):
        for h in self._h.get(event_type, []):
            try:
                h(payload, metadata)
            except Exception:
                pass
