from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import User
from backend.schemas.auth import (
    MessageResponse,
    RefreshTokenRequest,
    RefreshTokenResponse,
    Token,
    UserCreate,
    UserLogin,
    UserResponse,
)
from backend.services.auth_service import (
    authenticate_user,
    create_access_token,
    create_refresh_token,
    get_current_user_optional,
    register_user,
    revoke_user_refresh_token,
    rotate_refresh_token,
)

router = APIRouter(prefix="/api/auth", tags=["Authentication (Double Token)"])


@router.post(
    "/register",
    response_model=Token,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account and receive access & refresh tokens",
)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    """Registers a new user, hashes password, and issues initial access and refresh tokens."""
    user = register_user(user_in=user_in, db=db)
    access_token = create_access_token(user_id=user.id, tenant_id=user.tenant_id, email=user.email)
    refresh_token = create_refresh_token(user_id=user.id, tenant_id=user.tenant_id, db=db)

    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        tenant_id=user.tenant_id,
        user_id=user.id,
        user=UserResponse.model_validate(user),
    )


@router.post(
    "/login",
    response_model=Token,
    summary="Authenticate with email & password to receive access & refresh tokens",
)
def login(login_in: UserLogin, db: Session = Depends(get_db)):
    """Authenticates credentials and returns a 15-minute access token + 7-day refresh token."""
    user = authenticate_user(
        email=login_in.email,
        password=login_in.password,
        tenant_id=login_in.tenant_id,
        db=db,
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(user_id=user.id, tenant_id=user.tenant_id, email=user.email)
    refresh_token = create_refresh_token(user_id=user.id, tenant_id=user.tenant_id, db=db)

    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        tenant_id=user.tenant_id,
        user_id=user.id,
        user=UserResponse.model_validate(user),
    )


@router.post(
    "/refresh",
    response_model=RefreshTokenResponse,
    summary="Rotate refresh token and issue a fresh access token",
)
def refresh_tokens(payload: RefreshTokenRequest, db: Session = Depends(get_db)):
    """
    Refresh Token Rotation:
    Accepts an existing refresh token, verifies it in the DB, revokes it, and issues
    a new 15-minute access token and a new 7-day refresh token.
    """
    new_access_token, new_refresh_token, _ = rotate_refresh_token(
        refresh_token_str=payload.refresh_token,
        db=db,
    )
    return RefreshTokenResponse(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
    )


@router.post(
    "/logout",
    response_model=MessageResponse,
    summary="Revoke the refresh token on user logout",
)
def logout(payload: RefreshTokenRequest, db: Session = Depends(get_db)):
    """Revokes the refresh token in PostgreSQL to prevent further session renewals."""
    revoke_user_refresh_token(payload.refresh_token, db=db)
    return MessageResponse(message="Successfully logged out and session revoked.")


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current authenticated user profile",
)
def get_me(user: User = Depends(get_current_user_optional)):
    """Returns the profile of the currently authenticated user."""
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated or invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return UserResponse.model_validate(user)
