from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select

from backend.app.core.database import get_db
from backend.app.auth.models import (
    TokenResponse,
    User,
    UserCreate,
    UserLogin,
    UserResponse,
    UserRole,
)
from backend.app.auth.security import create_access_token, hash_password, verify_password
from backend.app.auth.dependencies import get_current_user, require_role

router = APIRouter(prefix="/auth", tags=["Authentication & RBAC"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new platform user",
)
async def register(
    user_in: UserCreate,
    session: AsyncSession = Depends(get_db),
) -> UserResponse:
    """
    Registers a new student, instructor, or admin user.
    Enforces email uniqueness and bcrypt password hashing.
    """
    statement = select(User).where(User.email == user_in.email.strip().lower())
    result = await session.execute(statement)
    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email address already exists.",
        )

    hashed_pw = hash_password(user_in.password)
    new_user = User(
        email=user_in.email.strip().lower(),
        full_name=user_in.full_name.strip(),
        role=user_in.role,
        hashed_password=hashed_pw,
        is_active=True,
    )

    session.add(new_user)
    await session.commit()
    await session.refresh(new_user)

    return UserResponse.model_validate(new_user)


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Authenticate user and issue JWT token",
)
async def login(
    credentials: UserLogin,
    session: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """
    Authenticates user credentials and returns a signed JWT access token.
    """
    statement = select(User).where(User.email == credentials.email.strip().lower())
    result = await session.execute(statement)
    user = result.scalar_one_or_none()

    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated",
        )

    token = create_access_token(user_id=user.id, role=user.role.value)
    user_response = UserResponse.model_validate(user)

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=user_response,
    )


@router.get(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get current authenticated user profile",
)
async def get_me(
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    """
    Returns the authenticated user profile for the caller.
    """
    return UserResponse.model_validate(current_user)


@router.get(
    "/instructor-only",
    status_code=status.HTTP_200_OK,
    summary="Protected instructor diagnostic route",
)
async def instructor_only_check(
    current_user: User = Depends(require_role([UserRole.INSTRUCTOR, UserRole.ADMIN])),
) -> dict:
    """
    Diagnostic endpoint verifying Server-Side Role-Based Access Control (PRD Constraint #6).
    """
    return {
        "message": "Authorized instructor access",
        "user_id": current_user.id,
        "role": current_user.role.value,
    }
