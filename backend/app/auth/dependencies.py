from typing import Callable, List
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select

from backend.app.core.database import get_db
from backend.app.auth.models import User, UserRole
from backend.app.auth.security import decode_token

# OAuth2 Password Bearer pointing to login endpoint
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=True)


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_db),
) -> User:
    """
    Extracts, decodes, and verifies the JWT token from the Authorization header.
    Fetches the authenticated User entity from the database.
    Enforces multi-tenant isolation and active status (PRD Constraint #2, FR-021).
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials or token expired",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = decode_token(token)
    if payload is None or not payload.sub:
        raise credentials_exception

    statement = select(User).where(User.id == payload.sub)
    result = await session.execute(statement)
    user = result.scalar_one_or_none()

    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated",
        )

    return user


def require_role(allowed_roles: List[UserRole]) -> Callable:
    """
    Dependency factory enforcing Server-Side Role-Based Access Control (RBAC).
    Guarantees that unauthorized users cannot execute privileged operations (PRD Constraint #6).
    """
    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access forbidden: requires one of the following roles: {[r.value for r in allowed_roles]}",
            )
        return current_user

    return role_checker
