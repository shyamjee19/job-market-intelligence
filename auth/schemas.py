from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, model_validator


class RegisterRequest(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    confirm_password: str
    country: str | None = Field(None, max_length=100)
    job_title: str | None = Field(None, max_length=255)
    terms_accepted: bool

    @model_validator(mode="after")
    def _check_confirm_and_terms(self):
        if self.password != self.confirm_password:
            raise ValueError("passwords do not match")
        if not self.terms_accepted:
            raise ValueError("you must accept the terms of service to create an account")
        return self

    @property
    def full_name(self) -> str:
        return f"{self.first_name.strip()} {self.last_name.strip()}".strip()


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    remember_me: bool = False


class RefreshRequest(BaseModel):
    refresh_token: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8, max_length=128)


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=128)


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
