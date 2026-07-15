from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    full_name: str | None = Field(None, max_length=255)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    user_id: int
    email: str
    full_name: str | None
    role: str
    is_active: bool
    created_at: datetime


class ProfileOut(BaseModel):
    headline: str | None
    bio: str | None
    location: str | None
    skills: list[str]
    experience_years: int | None
    resume_filename: str | None
    resume_uploaded_at: datetime | None


class ProfileUpdateRequest(BaseModel):
    headline: str | None = Field(None, max_length=255)
    bio: str | None = Field(None, max_length=4000)
    location: str | None = Field(None, max_length=255)
    skills: list[str] | None = None
    experience_years: int | None = Field(None, ge=0, le=80)
