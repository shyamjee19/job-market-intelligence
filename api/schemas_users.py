from datetime import datetime

from pydantic import BaseModel, Field


class FavoriteCompanyOut(BaseModel):
    company_key: int
    company_name: str
    favorited_at: datetime


class AlertCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    keywords: str | None = Field(None, max_length=255)
    location: str | None = Field(None, max_length=255)
    tag: str | None = Field(None, max_length=128)
    source: str | None = Field(None, max_length=64)
    salary_min: int | None = Field(None, ge=0)
    remote_type: str | None = None
    frequency: str = Field("daily", pattern="^(instant|daily|weekly)$")


class AlertOut(BaseModel):
    alert_id: int
    name: str
    keywords: str | None
    location: str | None
    tag: str | None
    source: str | None
    salary_min: int | None
    remote_type: str | None
    frequency: str
    is_active: bool
    last_checked_at: datetime | None
    created_at: datetime


class ResumeUploadResponse(BaseModel):
    resume_filename: str
    resume_uploaded_at: datetime


class NotificationOut(BaseModel):
    notification_id: int
    alert_id: int | None
    subject: str | None
    body: str | None
    status: str
    is_read: bool
    created_at: datetime


class NotificationListResponse(BaseModel):
    items: list[NotificationOut]
    total: int
    page: int
    page_size: int
