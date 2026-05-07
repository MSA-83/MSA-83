"""API key management service."""

import hashlib
import secrets
import uuid
from datetime import UTC, datetime, timedelta

from fastapi import HTTPException, status

from backend.models.api_key import ApiKey
from backend.models.database import get_db

PREFIX = "tk_"
KEY_LENGTH = 48


class ApiKeyService:
    """Service for managing user API keys."""

    def create_key(self, user_id: str, name: str, expires_days: int | None = None) -> dict:
        """Generate a new API key for a user."""
        raw_key = PREFIX + secrets.token_urlsafe(KEY_LENGTH)
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        prefix = raw_key[:12]
        key_id = str(uuid.uuid4())

        expires_at = None
        if expires_days:
            expires_at = datetime.now(UTC) + timedelta(days=expires_days)

        db = next(get_db())
        try:
            api_key = ApiKey(
                id=key_id,
                user_id=user_id,
                name=name,
                key_hash=key_hash,
                prefix=prefix,
                expires_at=expires_at,
            )
            db.add(api_key)
            db.commit()
        finally:
            db.close()

        return {
            "id": key_id,
            "name": name,
            "key": raw_key,
            "prefix": prefix,
            "expires_at": expires_at.isoformat() if expires_at else None,
            "created_at": datetime.now(UTC).isoformat(),
        }

    def validate_key(self, raw_key: str) -> dict | None:
        """Validate an API key and return user info if valid."""
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()

        db = next(get_db())
        try:
            api_key = db.query(ApiKey).filter(
                ApiKey.key_hash == key_hash,
                ApiKey.is_active == True,
            ).first()

            if not api_key:
                return None

            if api_key.expires_at and api_key.expires_at < datetime.now(UTC):
                return None

            api_key.last_used_at = datetime.now(UTC)
            db.commit()

            return {
                "user_id": api_key.user_id,
                "key_id": api_key.id,
                "key_name": api_key.name,
            }
        finally:
            db.close()

    def get_user_keys(self, user_id: str) -> list[dict]:
        """List all API keys for a user."""
        db = next(get_db())
        try:
            keys = db.query(ApiKey).filter(ApiKey.user_id == user_id).order_by(ApiKey.created_at.desc()).all()
            return [
                {
                    "id": k.id,
                    "name": k.name,
                    "prefix": k.prefix,
                    "is_active": k.is_active,
                    "last_used_at": k.last_used_at.isoformat() if k.last_used_at else None,
                    "expires_at": k.expires_at.isoformat() if k.expires_at else None,
                    "created_at": k.created_at.isoformat(),
                }
                for k in keys
            ]
        finally:
            db.close()

    def revoke_key(self, user_id: str, key_id: str) -> bool:
        """Revoke an API key."""
        db = next(get_db())
        try:
            api_key = db.query(ApiKey).filter(
                ApiKey.id == key_id,
                ApiKey.user_id == user_id,
            ).first()

            if not api_key:
                return False

            api_key.is_active = False
            db.commit()
            return True
        finally:
            db.close()

    def cleanup_expired(self) -> int:
        """Deactivate expired keys."""
        db = next(get_db())
        try:
            result = db.query(ApiKey).filter(
                ApiKey.expires_at < datetime.now(UTC),
                ApiKey.is_active == True,
            ).update({"is_active": False})
            db.commit()
            return result
        finally:
            db.close()


api_key_service = ApiKeyService()


async def require_api_key(authorization: str | None = None) -> dict:
    """Dependency to authenticate via API key."""
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = authorization.replace("Bearer ", "").strip()
    if not token.startswith(PREFIX):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key format",
        )

    user_info = api_key_service.validate_key(token)
    if not user_info:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired API key",
        )

    return user_info
