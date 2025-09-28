"""SQLAlchemy test stubs for improved mock quality."""

from typing import Any, List, Optional


class ScalarResultStub:
    """Stub for SQLAlchemy ScalarResult."""

    def __init__(self, data: List[Any]):
        self._data = data

    def all(self) -> List[Any]:
        """Return all results."""
        return self._data

    def first(self) -> Optional[Any]:
        """Return first result or None."""
        return self._data[0] if self._data else None

    def one_or_none(self) -> Optional[Any]:
        """Return one result or None."""
        return self._data[0] if len(self._data) == 1 else None


class ResultStub:
    """Stub for SQLAlchemy Result with proper scalars() method."""

    def __init__(self, data: List[Any]):
        self._data = data

    def scalars(self) -> ScalarResultStub:
        """Return ScalarResultStub for chaining."""
        return ScalarResultStub(self._data)

    def first(self) -> Optional[Any]:
        """Return first result or None."""
        return self._data[0] if self._data else None

    def all(self) -> List[Any]:
        """Return all results."""
        return self._data

    def one_or_none(self) -> Optional[Any]:
        """Return one result or None."""
        return self._data[0] if len(self._data) == 1 else None


def create_result_stub(data: List[Any]) -> ResultStub:
    """Factory function to create ResultStub instances."""
    return ResultStub(data)