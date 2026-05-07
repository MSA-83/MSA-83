"""JWT authentication service for Titanium platform."""

import os
from datetime import datetime, timedelta

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from passlib.context import CryptContext
from pydantic import BaseModel


class UserCreate(BaseModel):
    email: str
    password: str
    tier: str = "free"


class UserLogin(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class UserResponse(BaseModel):
    id: str
    email: str
    tier: str
    created_at: str


class AuthConfig:
    """Authentication configuration."""

    SECRET_KEY = os.getenv("JWT_SECRET_KEY", "titanium-dev-secret-change-in-production")
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_EXPIRE", "60"))
    REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("JWT_REFRESH_EXPIRE", "7"))


pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")
security = HTTPBearer()


class AuthService:
    """Service for authentication operations."""

    def __init__(self):
        self._users: dict[str, dict] = {}

    def hash_password(self, password: str) -> str:
        """Hash a password."""
        return pwd_context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        return pwd_context.verify(plain_password, hashed_password)

    def create_access_token(
        self,
        user_id: str,
        email: str,
        tier: str,
        expires_delta: timedelta | None = None,
    ) -> str:
        """Create a JWT access token."""
        expire = datetime.utcnow() + (expires_delta or timedelta(minutes=AuthConfig.ACCESS_TOKEN_EXPIRE_MINUTES))

        to_encode = {
            "sub": user_id,
            "email": email,
            "tier": tier,
            "exp": expire,
            "type": "access",
        }

        return jwt.encode(
            to_encode,
            AuthConfig.SECRET_KEY,
            algorithm=AuthConfig.ALGORITHM,
        )

    def create_refresh_token(self, user_id: str) -> str:
        """Create a JWT refresh token."""
        expire = datetime.utcnow() + timedelta(days=AuthConfig.REFRESH_TOKEN_EXPIRE_DAYS)

        to_encode = {
            "sub": user_id,
            "exp": expire,
            "type": "refresh",
        }

        return jwt.encode(
            to_encode,
            AuthConfig.SECRET_KEY,
            algorithm=AuthConfig.ALGORITHM,
        )

    def decode_token(self, token: str) -> dict:
        """Decode and validate a JWT token."""
        try:
            payload = jwt.decode(
                token,
                AuthConfig.SECRET_KEY,
                algorithms=[AuthConfig.ALGORITHM],
            )
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except (jwt.PyJWTError, jwt.InvalidTokenError):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"},
            )

    def register_user(self, email: str, password: str, tier: str = "free") -> UserResponse:
        """Register a new user."""
        if email in self._users:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered",
            )

        user_id = f"user-{len(self._users) + 1:04d}"

        self._users[email] = {
            "id": user_id,
            "email": email,
            "hashed_password": self.hash_password(password),
            "tier": tier,
            "created_at": datetime.utcnow().isoformat(),
        }

        return UserResponse(
            id=user_id,
            email=email,
            tier=tier,
            created_at=self._users[email]["created_at"],
        )

    def login(self, email: str, password: str) -> TokenResponse:
        """Authenticate a user and return tokens."""
        user = self._users.get(email)

        if not user or not self.verify_password(password, user["hashed_password"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        access_token = self.create_access_token(
            user_id=user["id"],
            email=user["email"],
            tier=user["tier"],
        )

        refresh_token = self.create_refresh_token(user["id"])

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=AuthConfig.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

    def refresh_access_token(self, refresh_token: str) -> TokenResponse:
        """Refresh an access token using a refresh token."""
        payload = self.decode_token(refresh_token)

        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
            )

        user_id = payload.get("sub")

        user = None
        for u in self._users.values():
            if u["id"] == user_id:
                user = u
                break

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
            )

        access_token = self.create_access_token(
            user_id=user["id"],
            email=user["email"],
            tier=user["tier"],
        )

        new_refresh_token = self.create_refresh_token(user["id"])

        return TokenResponse(
            access_token=access_token,
            refresh_token=new_refresh_token,
            expires_in=AuthConfig.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

    def get_user(self, user_id: str) -> UserResponse | None:
        """Get user by ID."""
        for user in self._users.values():
            if user["id"] == user_id:
                return UserResponse(
                    id=user["id"],
                    email=user["email"],
                    tier=user["tier"],
                    created_at=user["created_at"],
                )
        return None


auth_service = AuthService()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    """Dependency to get the current authenticated user."""
    payload = auth_service.decode_token(credentials.credentials)

    return {
        "user_id": payload.get("sub"),
        "email": payload.get("email"),
        "tier": payload.get("tier"),
    }


async def require_tier(min_tier: str):
    """Dependency to require a minimum tier level."""
    tier_levels = {"free": 0, "pro": 1, "enterprise": 2, "defense": 3}

    async def check_tier(
        current_user: dict = Depends(get_current_user),
    ) -> dict:
        user_tier = current_user.get("tier", "free")

        if tier_levels.get(user_tier, 0) < tier_levels.get(min_tier, 0):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires {min_tier} tier or higher",
            )

        return current_user

    return check_tier
