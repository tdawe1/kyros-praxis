"""WebSocket token endpoint for Terminal authentication.

Since WebSockets don't support httpOnly cookies in all scenarios,
we provide a temporary token specifically for WebSocket connections.
"""

from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

import app.auth as auth_module
from ..core.config import settings
from ..db.models import User
from ..db.session import get_session


router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/ws-token")
async def get_websocket_token(
    user: User = Depends(auth_module.get_current_user_required),
    session: AsyncSession = Depends(get_session)
):
    """
    Get a temporary token for WebSocket connections.
    
    WebSockets don't support httpOnly cookies in cross-origin scenarios.
    This endpoint provides a short-lived token specifically for WS auth.
    
    Token characteristics:
    - Expires in 5 minutes (single session use)
    - Can only be used for WebSocket connections
    - Not refreshable
    
    Args:
        user: Current authenticated user (from httpOnly cookie)
        session: Database session
        
    Returns:
        Temporary WebSocket token
        
    Security Notes:
        - This token is exposed to JavaScript (less secure than httpOnly)
        - Short 5-minute expiry limits attack window
        - Should only be used immediately for WS connection
        - Token type marked as 'ws' for validation
    """
    # Create short-lived WebSocket token (5 minutes)
    ws_token = auth_module.create_access_token(
        data={
            "sub": user.email,
            "user_id": user.id,
            "username": user.username,
        },
        expires_delta=timedelta(minutes=5),
        token_type="ws"  # Mark as WebSocket token
    )
    
    return {
        "ws_token": ws_token,
        "expires_in": 300,  # 5 minutes in seconds
        "token_type": "ws",
        "note": "Use this token immediately for WebSocket connection. Expires in 5 minutes."
    }
