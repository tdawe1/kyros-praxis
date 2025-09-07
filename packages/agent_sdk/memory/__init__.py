"""Memory and storage systems for agents."""

from .store import AgentMemoryStore, InteractionRecord

try:
    from .sqlite_store import SQLiteMemoryStore  # type: ignore

    _HAS_SQLITE = True
except Exception:  # aiosqlite missing or import error
    SQLiteMemoryStore = None  # type: ignore
    _HAS_SQLITE = False

__all__ = ["AgentMemoryStore", "InteractionRecord"] + (
    ["SQLiteMemoryStore"] if _HAS_SQLITE else []
)
