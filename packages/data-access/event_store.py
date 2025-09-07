from abc import ABC, abstractmethod
from typing import Iterable


class EventStore(ABC):
    @abstractmethod
    async def append(
        self, stream_id: str, events: list[dict], expected_version: int | None = None
    ): ...
    @abstractmethod
    async def read(self, stream_id: str, from_version: int = 0) -> Iterable[dict]: ...
