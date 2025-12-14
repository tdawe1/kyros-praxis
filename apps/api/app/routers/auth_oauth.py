"""
OAuth authentication routes (placeholder for future implementation).

These routes are ready for when OAuth providers are implemented.
Currently returns "not implemented" responses.
"""

from fastapi import APIRouter, HTTPException, Query, Response, status
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.session import get_session
from ..auth.providers import AuthProvider
from ..auth.providers.password import PasswordAuthProvider
# from ..auth.providers.oauth_google import GoogleOAuthProvider  # Implement when needed
# from ..auth.providers.oauth_github import GitHubOAuthProvider  # Implement when needed
from ..auth.session import create_session


router = APIRouter(prefix="/auth", tags=["authentication"])


# Registry of available auth providers
AUTH_PROVIDERS: dict[str, AuthProvider] = {
    "password": PasswordAuthProvider(),
    # Add OAuth providers here when implemented:
    # "google": GoogleOAuthProvider(
    #     client_id=settings.GOOGLE_CLIENT_ID,
    #     client_secret=settings.GOOGLE_CLIENT_SECRET
    # ),
    # "github": GitHubOAuthProvider(
    #     client_id=settings.GITHUB_CLIENT_ID,
    #     client_secret=settings.GITHUB_CLIENT_SECRET
    # ),
}


@router.get("/providers")
async def list_auth_providers():
    """
    List available authentication providers.
    
    Returns:
        List of provider names and whether they're available
    """
    return {
        "providers": [
            {
                "name": "password",
                "display_name": "Email/Password",
                "type": "credentials",
                "available": True
            },
            {
                "name": "google",
                "display_name": "Google",
                "type": "oauth",
                "available": False,
                "note": "Not yet implemented - architecture ready"
            },
            {
                "name": "github",
                "display_name": "GitHub",
                "type": "oauth",
                "available": False,
                "note": "Not yet implemented - architecture ready"
            }
        ]
    }


@router.get("/oauth/{provider}")
async def oauth_login(provider: str):
    """
    Initiate OAuth login flow (placeholder).
    
    When implemented, this will redirect to provider's OAuth page.
    
    Args:
        provider: OAuth provider name (google, github, etc.)
    """
    if provider not in ["google", "github", "azure"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Provider '{provider}' not supported"
        )
    
    # PLACEHOLDER - Implement when adding OAuth
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail={
            "error": "OAuth not yet implemented",
            "message": f"OAuth login with {provider} is coming soon!",
            "implementation_guide": "See apps/OAUTH-DECISION-GUIDE.md",
            "estimated_time": "3-5 days when needed",
            "ready": "Architecture is OAuth-ready, just needs provider implementation"
        }
    )


@router.get("/oauth/{provider}/callback")
async def oauth_callback(
    provider: str,
    code: str = Query(..., description="OAuth authorization code"),
    state: str = Query(..., description="CSRF protection state"),
    response: Response = None,
    session: AsyncSession = Depends(get_session)
):
    """
    OAuth callback endpoint (placeholder).
    
    When implemented, this will:
    1. Exchange code for access token
    2. Get user info from provider
    3. Create or link user account
    4. Create session and return token
    
    Args:
        provider: OAuth provider name
        code: Authorization code from provider
        state: CSRF state token
        response: Response object for setting cookies
        session: Database session
    """
    # PLACEHOLDER - Implement when adding OAuth
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail={
            "error": "OAuth callback not yet implemented",
            "received_code": bool(code),
            "provider": provider,
            "next_steps": "Implement OAuth provider class and complete authentication flow"
        }
    )


@router.post("/link/{provider}")
async def link_oauth_account(
    provider: str,
    session: AsyncSession = Depends(get_session)
):
    """
    Link OAuth account to existing user (placeholder).
    
    When implemented, allows users to add OAuth login to their account.
    
    Args:
        provider: OAuth provider to link
        session: Database session
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail={
            "error": "OAuth account linking not yet implemented",
            "feature": "Account linking",
            "note": "This will allow users to link multiple auth methods to one account"
        }
    )
