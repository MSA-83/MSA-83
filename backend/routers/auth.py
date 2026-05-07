"""Authentication router for user registration, login, and token management."""

from fastapi import APIRouter, Depends, HTTPException, status

from backend.services.auth.auth_service import (
    RefreshTokenRequest,
    TokenResponse,
    UserCreate,
    UserLogin,
    UserResponse,
    auth_service,
    get_current_user,
)

router = APIRouter()


@router.post("/register", response_model=TokenResponse)
async def register(user_data: UserCreate):
    """Register a new user and return tokens."""
    user = auth_service.register_user(
        email=user_data.email,
        password=user_data.password,
        tier=user_data.tier,
    )

    tokens = auth_service.login(user_data.email, user_data.password)

    return tokens


@router.post("/login", response_model=TokenResponse)
async def login(user_data: UserLogin):
    """Authenticate a user and return tokens."""
    return auth_service.login(
        email=user_data.email,
        password=user_data.password,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(request: RefreshTokenRequest):
    """Refresh an access token."""
    return auth_service.refresh_access_token(request.refresh_token)


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """Get current user information."""
    user = auth_service.get_user(current_user["user_id"])

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return user


@router.post("/logout")
async def logout(current_user: dict = Depends(get_current_user)):
    """Logout (client should discard tokens)."""
    return {"message": "Logged out successfully. Discard your tokens."}
