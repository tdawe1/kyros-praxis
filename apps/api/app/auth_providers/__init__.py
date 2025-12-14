"""
Authentication providers package.

Handles provider-based authentication (OAuth, password, etc.) and session management.
"""

# New provider-based architecture exports
from .providers import AuthProvider  # noqa: F401
from .session import create_session, destroy_session  # noqa: F401

__all__ = ["AuthProvider", "create_session", "destroy_session"]
