from abc import ABC, abstractmethod


class TerminalService(ABC):
    @abstractmethod
    async def open(self): ...
    @abstractmethod
    async def write(self, data: str): ...
    @abstractmethod
    async def resize(self, cols: int, rows: int): ...
