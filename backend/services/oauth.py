"""OAuth provider service for GitHub and Google login."""

import os
import secrets
from urllib.parse import urlencode

import httpx

from backend.services.auth.auth_service import AuthService


class OAuthConfig:
    """OAuth configuration."""

    GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID", "")
    GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET", "")
    GITHUB_REDIRECT_URI = os.getenv("GITHUB_REDIRECT_URI", "http://localhost:8000/api/auth/oauth/github/callback")

    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
    GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/api/auth/oauth/google/callback")


class OAuthProvider:
    """Handle OAuth2 flows for multiple providers."""

    PROVIDERS = {"github", "google"}

    GITHUB_AUTH_URL = "https://github.com/login/oauth/authorize"
    GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
    GITHUB_USER_URL = "https://api.github.com/user"

    GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
    GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
    GOOGLE_USER_URL = "https://www.googleapis.com/oauth2/v3/userinfo"

    def __init__(self):
        self.auth_service = AuthService()

    def get_auth_url(self, provider: str, state: str | None = None) -> str:
        """Generate OAuth authorization URL."""
        if provider == "github":
            params = {
                "client_id": OAuthConfig.GITHUB_CLIENT_ID,
                "redirect_uri": OAuthConfig.GITHUB_REDIRECT_URI,
                "scope": "user:email",
                "state": state or secrets.token_urlsafe(32),
            }
            return f"{self.GITHUB_AUTH_URL}?{urlencode(params)}"

        elif provider == "google":
            params = {
                "client_id": OAuthConfig.GOOGLE_CLIENT_ID,
                "redirect_uri": OAuthConfig.GOOGLE_REDIRECT_URI,
                "response_type": "code",
                "scope": "openid email profile",
                "state": state or secrets.token_urlsafe(32),
            }
            return f"{self.GOOGLE_AUTH_URL}?{urlencode(params)}"

        raise ValueError(f"Unknown OAuth provider: {provider}")

    async def handle_callback(self, provider: str, code: str) -> dict:
        """Handle OAuth callback and return user info + tokens."""
        if provider == "github":
            return await self._handle_github_callback(code)
        elif provider == "google":
            return await self._handle_google_callback(code)
        raise ValueError(f"Unknown OAuth provider: {provider}")

    async def _handle_github_callback(self, code: str) -> dict:
        """Exchange GitHub code for user info."""
        async with httpx.AsyncClient() as client:
            token_response = await client.post(
                self.GITHUB_TOKEN_URL,
                headers={"Accept": "application/json"},
                data={
                    "client_id": OAuthConfig.GITHUB_CLIENT_ID,
                    "client_secret": OAuthConfig.GITHUB_CLIENT_SECRET,
                    "code": code,
                    "redirect_uri": OAuthConfig.GITHUB_REDIRECT_URI,
                },
            )
            token_data = token_response.json()
            access_token = token_data.get("access_token")

            if not access_token:
                raise ValueError("Failed to get access token from GitHub")

            user_response = await client.get(
                self.GITHUB_USER_URL,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/json",
                },
            )
            user_data = user_response.json()

            emails_response = await client.get(
                "https://api.github.com/user/emails",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/json",
                },
            )
            emails = emails_response.json()
            primary_email = next((e["email"] for e in emails if e.get("primary")), emails[0]["email"] if emails else "")

        return self._register_or_login(
            email=primary_email,
            provider="github",
            provider_id=str(user_data.get("id", "")),
            name=user_data.get("login", ""),
            avatar_url=user_data.get("avatar_url", ""),
        )

    async def _handle_google_callback(self, code: str) -> dict:
        """Exchange Google code for user info."""
        async with httpx.AsyncClient() as client:
            token_response = await client.post(
                self.GOOGLE_TOKEN_URL,
                data={
                    "client_id": OAuthConfig.GOOGLE_CLIENT_ID,
                    "client_secret": OAuthConfig.GOOGLE_CLIENT_SECRET,
                    "code": code,
                    "grant_type": "authorization_code",
                    "redirect_uri": OAuthConfig.GOOGLE_REDIRECT_URI,
                },
            )
            token_data = token_response.json()
            access_token = token_data.get("access_token")

            if not access_token:
                raise ValueError("Failed to get access token from Google")

            user_response = await client.get(
                self.GOOGLE_USER_URL,
                headers={"Authorization": f"Bearer {access_token}"},
            )
            user_data = user_response.json()

        return self._register_or_login(
            email=user_data.get("email", ""),
            provider="google",
            provider_id=user_data.get("sub", ""),
            name=user_data.get("name", ""),
            avatar_url=user_data.get("picture", ""),
        )

    def _register_or_login(
        self,
        email: str,
        provider: str,
        provider_id: str,
        name: str,
        avatar_url: str,
    ) -> dict:
        """Register new user or login existing user."""
        try:
            user = self.auth_service.get_user_by_email(email)
            if user:
                user_data = user.dict() if hasattr(user, "dict") else user
            else:
                random_password = secrets.token_urlsafe(32)
                user = self.auth_service.register_user(
                    email=email,
                    password=random_password,
                    tier="free",
                )
                user_data = user.dict() if hasattr(user, "dict") else user
        except Exception:
            random_password = secrets.token_urlsafe(32)
            user = self.auth_service.register_user(
                email=email,
                password=random_password,
                tier="free",
            )
            user_data = user.dict() if hasattr(user, "dict") else user

        tokens = self.auth_service.login_by_email(email, random_password)

        return {
            "user": {
                **user_data,
                "oauth_provider": provider,
                "oauth_id": provider_id,
                "display_name": name,
                "avatar_url": avatar_url,
            },
            "tokens": {
                "access_token": tokens.access_token,
                "refresh_token": tokens.refresh_token,
                "token_type": tokens.token_type,
                "expires_in": tokens.expires_in,
            },
        }


oauth_provider = OAuthProvider()
