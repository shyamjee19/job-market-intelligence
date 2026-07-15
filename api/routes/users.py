from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from api.schemas import JobSummary
from api.schemas_users import (
    AlertCreateRequest,
    AlertOut,
    FavoriteCompanyOut,
    NotificationListResponse,
    ResumeUploadResponse,
)
from auth.dependencies import get_current_user
from auth.schemas import ProfileOut, ProfileUpdateRequest
from config.settings import settings
from database import queries
from database.users_queries import (
    count_unread_notifications,
    get_company_key_by_name,
    get_profile,
    list_alerts,
    list_favorite_companies,
    list_notifications,
    list_saved_jobs,
)
from database.users_repository import (
    create_alert,
    delete_alert,
    favorite_company,
    log_audit,
    mark_all_notifications_read,
    mark_notification_read,
    save_job,
    set_alert_active,
    set_resume,
    unfavorite_company,
    unsave_job,
    upsert_profile,
)
from utils.exceptions import DataValidationError
from utils.resume_storage import save_resume

router = APIRouter(prefix="/users/me", tags=["users"])


@router.put("/profile", response_model=ProfileOut)
def update_profile(body: ProfileUpdateRequest, user: dict = Depends(get_current_user)):
    fields = body.model_dump(exclude_unset=True)
    upsert_profile(user["user_id"], **fields)
    log_audit(user["user_id"], "profile_update")
    return get_profile(user["user_id"]) or ProfileOut(
        headline=None, bio=None, location=None, skills=[], experience_years=None,
        resume_filename=None, resume_uploaded_at=None,
    )


@router.post("/resume", response_model=ResumeUploadResponse)
async def upload_resume(file: UploadFile = File(...), user: dict = Depends(get_current_user)):
    contents = await file.read()
    try:
        path = save_resume(
            settings.RESUME_UPLOAD_DIR, user["user_id"], file.filename or "resume", contents, settings.RESUME_MAX_SIZE_MB
        )
    except DataValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)) from e

    set_resume(user["user_id"], file.filename or "resume", path)
    log_audit(user["user_id"], "resume_upload", resource_type="resume")
    profile = get_profile(user["user_id"])
    return ResumeUploadResponse(resume_filename=profile["resume_filename"], resume_uploaded_at=profile["resume_uploaded_at"])


@router.get("/saved-jobs", response_model=list[JobSummary])
def get_saved_jobs(user: dict = Depends(get_current_user)):
    return list_saved_jobs(user["user_id"])


@router.post("/saved-jobs/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
def add_saved_job(job_id: int, user: dict = Depends(get_current_user)):
    if queries.get_job_by_id(job_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    save_job(user["user_id"], job_id)


@router.delete("/saved-jobs/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_saved_job(job_id: int, user: dict = Depends(get_current_user)):
    unsave_job(user["user_id"], job_id)


@router.get("/favorites", response_model=list[FavoriteCompanyOut])
def get_favorite_companies(user: dict = Depends(get_current_user)):
    return list_favorite_companies(user["user_id"])


@router.post("/favorites/{company_name}", status_code=status.HTTP_204_NO_CONTENT)
def add_favorite_company(company_name: str, user: dict = Depends(get_current_user)):
    company_key = get_company_key_by_name(company_name)
    if company_key is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    favorite_company(user["user_id"], company_key)


@router.delete("/favorites/{company_name}", status_code=status.HTTP_204_NO_CONTENT)
def remove_favorite_company(company_name: str, user: dict = Depends(get_current_user)):
    company_key = get_company_key_by_name(company_name)
    if company_key is not None:
        unfavorite_company(user["user_id"], company_key)


@router.get("/alerts", response_model=list[AlertOut])
def get_alerts(user: dict = Depends(get_current_user)):
    return list_alerts(user["user_id"])


@router.post("/alerts", response_model=AlertOut, status_code=status.HTTP_201_CREATED)
def add_alert(body: AlertCreateRequest, user: dict = Depends(get_current_user)):
    alert = create_alert(user["user_id"], **body.model_dump())
    log_audit(user["user_id"], "alert_create", resource_type="job_alert", resource_id=str(alert["alert_id"]))
    return alert


@router.patch("/alerts/{alert_id}", response_model=None, status_code=status.HTTP_204_NO_CONTENT)
def toggle_alert(alert_id: int, is_active: bool, user: dict = Depends(get_current_user)):
    set_alert_active(alert_id, user["user_id"], is_active)


@router.delete("/alerts/{alert_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_alert(alert_id: int, user: dict = Depends(get_current_user)):
    delete_alert(alert_id, user["user_id"])


@router.get("/notifications", response_model=NotificationListResponse)
def get_notifications(page: int = 1, page_size: int = 20, user: dict = Depends(get_current_user)):
    items, total = list_notifications(user["user_id"], page, page_size)
    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.get("/notifications/unread-count")
def get_unread_notification_count(user: dict = Depends(get_current_user)):
    return {"count": count_unread_notifications(user["user_id"])}


@router.patch("/notifications/read-all", status_code=status.HTTP_204_NO_CONTENT)
def read_all_notifications(user: dict = Depends(get_current_user)):
    mark_all_notifications_read(user["user_id"])


@router.patch("/notifications/{notification_id}/read", status_code=status.HTTP_204_NO_CONTENT)
def read_notification(notification_id: int, user: dict = Depends(get_current_user)):
    mark_notification_read(notification_id, user["user_id"])
