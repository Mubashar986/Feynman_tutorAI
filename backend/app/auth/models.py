from datetime import datetime, timezone
from enum import Enum
from typing import Optional
import uuid
from pydantic import EmailStr
from sqlmodel import Field, SQLModel


class UserRole(str, Enum):
    """
    NIST-aligned Role-Based Access Control (RBAC) roles.
    Enforced strictly server-side (PRD FR-021, NFR-005, Non-Negotiable Constraint #6).
    """
    STUDENT = "student"
    INSTRUCTOR = "instructor"
    ADMIN = "admin"


class UserBase(SQLModel):
    """Shared properties for User models."""
    email: str = Field(unique=True, index=True, nullable=False)
    full_name: str = Field(default="", nullable=False)
    role: UserRole = Field(default=UserRole.STUDENT, nullable=False)
    is_active: bool = Field(default=True, nullable=False)


class User(UserBase, table=True):
    """Database entity table representing platform users."""
    __tablename__ = "users"

    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        primary_key=True,
        index=True,
        nullable=False,
    )
    hashed_password: str = Field(nullable=False)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class UserCreate(SQLModel):
    """Registration request payload."""
    email: str
    password: str = Field(min_length=8, description="Minimum 8 characters")
    full_name: str = Field(default="")
    role: UserRole = Field(default=UserRole.STUDENT)


class UserLogin(SQLModel):
    """Login request payload."""
    email: str
    password: str


class UserResponse(UserBase):
    """Public user profile response (excludes hashed_password)."""
    id: str
    created_at: datetime


class TokenResponse(SQLModel):
    """OAuth2 Bearer token response."""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class TokenPayload(SQLModel):
    """Decoded JWT claims payload."""
    sub: str  # user_id
    role: str
    exp: int
