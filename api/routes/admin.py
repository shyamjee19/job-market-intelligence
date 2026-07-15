from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from auth.dependencies import require_admin
from database.users_queries import admin_stats, list_audit_logs, list_users
from database.users_repository import log_audit, set_user_active, set_user_role

router = APIRouter(prefix="/admin", tags=["admin"])


class UserListResponse(BaseModel):
    items: list[dict]
    total: int
    page: int
    page_size: int


class AuditLogListResponse(BaseModel):
    items: list[dict]
    total: int
    page: int
    page_size: int


class RoleUpdateRequest(BaseModel):
    role: str


@router.get("/stats")
def get_admin_stats(admin: dict = Depends(require_admin)):
    return admin_stats()


@router.get("/users", response_model=UserListResponse)
def get_users(page: int = Query(1, ge=1), page_size: int = Query(50, ge=1, le=100), admin: dict = Depends(require_admin)):
    rows, total = list_users(page, page_size)
    return {"items": rows, "total": total, "page": page, "page_size": page_size}


@router.patch("/users/{user_id}/role", status_code=status.HTTP_204_NO_CONTENT)
def update_user_role(user_id: int, body: RoleUpdateRequest, admin: dict = Depends(require_admin)):
    if body.role not in ("user", "admin"):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="role must be 'user' or 'admin'")
    set_user_role(user_id, body.role)
    log_audit(admin["user_id"], "admin_role_change", resource_type="user", resource_id=str(user_id), metadata={"new_role": body.role})


@router.patch("/users/{user_id}/active", status_code=status.HTTP_204_NO_CONTENT)
def update_user_active(user_id: int, is_active: bool, admin: dict = Depends(require_admin)):
    set_user_active(user_id, is_active)
    log_audit(admin["user_id"], "admin_active_change", resource_type="user", resource_id=str(user_id), metadata={"is_active": is_active})


@router.get("/audit-logs", response_model=AuditLogListResponse)
def get_audit_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    user_id: int | None = None,
    admin: dict = Depends(require_admin),
):
    rows, total = list_audit_logs(page, page_size, user_id)
    return {"items": rows, "total": total, "page": page, "page_size": page_size}
