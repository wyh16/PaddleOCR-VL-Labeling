from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.core.security import (
    ensure_project_capability,
    ensure_system_capability,
    get_current_user,
)
from app.db.models import User
from app.db.session import get_db_session
from app.schemas.access import (
    AddProjectMemberRequest,
    GrantProjectRoleRequest,
    ProjectCapabilitiesRead,
    ProjectCapabilitiesResponse,
    ProjectMemberListResponse,
    ProjectMemberRead,
    ProjectMemberResponse,
    ProjectMemberRolesResponse,
    RoleListResponse,
    RoleRead,
    UserCreateRequest,
    UserListResponse,
    UserRead,
    UserResponse,
)
from app.services.access_service import (
    AccessNotFoundError,
    AccessValidationError,
    add_project_member,
    create_user,
    disable_project_member,
    disable_user,
    get_project_capability_profile,
    grant_project_role,
    list_project_member_roles,
    list_project_members,
    list_roles,
    list_users,
    remove_project_member,
    revoke_project_role,
)
from app.utils.ids import new_public_id

router = APIRouter(tags=["access"])


@router.get("/users", response_model=UserListResponse, summary="查询用户列表")
def read_users(
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> UserListResponse:
    _ensure_can_manage_system_users(current_user)
    return UserListResponse(
        data=[_user_read(item) for item in list_users(db=db)],
        request_id=new_public_id("req"),
    )


@router.post(
    "/users",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="创建用户",
)
def create_user_account(
    payload: UserCreateRequest,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> UserResponse | JSONResponse:
    _ensure_can_manage_system_users(current_user)
    try:
        user = create_user(
            db=db,
            username=payload.username,
            display_name=payload.display_name,
            email=payload.email,
            temporary_password=payload.temporary_password,
            is_system_admin=payload.is_system_admin,
            actor_id=current_user.id,
        )
        return UserResponse(data=_user_read(user), request_id=new_public_id("req"))
    except AccessValidationError as exc:
        return _error_response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="VALIDATION_ERROR",
            message=str(exc),
            details={"username": payload.username, "email": payload.email},
        )


@router.post(
    "/users/{user_id}/disable",
    response_model=UserResponse,
    summary="禁用用户",
)
def disable_user_account(
    user_id: int,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> UserResponse | JSONResponse:
    _ensure_can_manage_system_users(current_user)
    try:
        user = disable_user(
            db=db,
            user_id=user_id,
            actor_id=current_user.id,
        )
        return UserResponse(data=_user_read(user), request_id=new_public_id("req"))
    except AccessNotFoundError as exc:
        return _error_response(
            status_code=status.HTTP_404_NOT_FOUND,
            code="USER_NOT_FOUND",
            message=str(exc),
            details={"user_id": user_id},
        )


@router.get("/roles", response_model=RoleListResponse, summary="查询内置角色")
def read_roles(
    db: Session = Depends(get_db_session),
    _current_user: User = Depends(get_current_user),
) -> RoleListResponse:
    return RoleListResponse(
        data=[_role_read(item) for item in list_roles(db=db)],
        request_id=new_public_id("req"),
    )


@router.get(
    "/projects/{project_id}/me/capabilities",
    response_model=ProjectCapabilitiesResponse,
    summary="查询当前用户项目能力",
)
def read_my_project_capabilities(
    project_id: int,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> ProjectCapabilitiesResponse:
    profile = get_project_capability_profile(
        db=db,
        project_id=project_id,
        user_id=current_user.id,
    )
    return ProjectCapabilitiesResponse(
        data=_capability_read(profile),
        request_id=new_public_id("req"),
    )


@router.get(
    "/projects/{project_id}/members",
    response_model=ProjectMemberListResponse,
    summary="查询项目成员",
)
def read_project_members(
    project_id: int,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> ProjectMemberListResponse:
    _ensure_can_manage_project_members(
        db, current_user=current_user, project_id=project_id
    )
    return ProjectMemberListResponse(
        data=[
            _member_read(item)
            for item in list_project_members(db=db, project_id=project_id)
        ],
        request_id=new_public_id("req"),
    )


@router.post(
    "/projects/{project_id}/members",
    response_model=ProjectMemberResponse,
    status_code=status.HTTP_201_CREATED,
    summary="添加项目成员",
)
def create_project_member(
    project_id: int,
    payload: AddProjectMemberRequest,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> ProjectMemberResponse | JSONResponse:
    _ensure_can_manage_project_members(
        db, current_user=current_user, project_id=project_id
    )
    try:
        member = add_project_member(
            db=db,
            project_id=project_id,
            user_id=payload.user_id,
            actor_id=current_user.id,
        )
    except AccessNotFoundError as exc:
        return _error_response(
            status_code=status.HTTP_404_NOT_FOUND,
            code="USER_NOT_FOUND",
            message=str(exc),
            details={"user_id": payload.user_id},
        )
    except AccessValidationError as exc:
        return _error_response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="VALIDATION_ERROR",
            message=str(exc),
            details={"user_id": payload.user_id},
        )
    return ProjectMemberResponse(
        data=_member_read(member), request_id=new_public_id("req")
    )


@router.post(
    "/projects/{project_id}/members/{member_id}/disable",
    response_model=ProjectMemberResponse,
    summary="禁用项目成员",
)
def disable_member(
    project_id: int,
    member_id: int,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> ProjectMemberResponse | JSONResponse:
    _ensure_can_manage_project_members(
        db, current_user=current_user, project_id=project_id
    )
    try:
        member = disable_project_member(
            db=db,
            project_id=project_id,
            member_id=member_id,
            actor_id=current_user.id,
        )
    except AccessNotFoundError as exc:
        return _error_response(
            status_code=status.HTTP_404_NOT_FOUND,
            code="PROJECT_MEMBER_NOT_FOUND",
            message=str(exc),
            details={"member_id": member_id},
        )
    return ProjectMemberResponse(
        data=_member_read(member), request_id=new_public_id("req")
    )


@router.delete(
    "/projects/{project_id}/members/{member_id}",
    response_model=ProjectMemberResponse,
    summary="移除项目成员",
)
def delete_project_member(
    project_id: int,
    member_id: int,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> ProjectMemberResponse | JSONResponse:
    _ensure_can_manage_project_members(
        db, current_user=current_user, project_id=project_id
    )
    try:
        member = remove_project_member(
            db=db,
            project_id=project_id,
            member_id=member_id,
            actor_id=current_user.id,
        )
    except AccessNotFoundError as exc:
        return _error_response(
            status_code=status.HTTP_404_NOT_FOUND,
            code="PROJECT_MEMBER_NOT_FOUND",
            message=str(exc),
            details={"member_id": member_id},
        )
    return ProjectMemberResponse(
        data=_member_read(member), request_id=new_public_id("req")
    )


@router.get(
    "/projects/{project_id}/members/{member_id}/roles",
    response_model=ProjectMemberRolesResponse,
    summary="查询项目成员角色",
)
def read_member_roles(
    project_id: int,
    member_id: int,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> ProjectMemberRolesResponse | JSONResponse:
    _ensure_can_manage_project_members(
        db, current_user=current_user, project_id=project_id
    )
    try:
        role_codes = list_project_member_roles(
            db=db,
            project_id=project_id,
            member_id=member_id,
        )
    except AccessNotFoundError as exc:
        return _error_response(
            status_code=status.HTTP_404_NOT_FOUND,
            code="PROJECT_MEMBER_NOT_FOUND",
            message=str(exc),
            details={"member_id": member_id},
        )
    return ProjectMemberRolesResponse(data=role_codes, request_id=new_public_id("req"))


@router.post(
    "/projects/{project_id}/members/{member_id}/roles",
    response_model=ProjectMemberRolesResponse,
    status_code=status.HTTP_201_CREATED,
    summary="授予项目成员角色",
)
def grant_member_role(
    project_id: int,
    member_id: int,
    payload: GrantProjectRoleRequest,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> ProjectMemberRolesResponse | JSONResponse:
    _ensure_can_manage_project_members(
        db, current_user=current_user, project_id=project_id
    )
    try:
        role_codes = grant_project_role(
            db=db,
            project_id=project_id,
            member_id=member_id,
            role_code=payload.role_code,
            actor_id=current_user.id,
        )
    except AccessNotFoundError as exc:
        return _error_response(
            status_code=status.HTTP_404_NOT_FOUND,
            code="ROLE_OR_MEMBER_NOT_FOUND",
            message=str(exc),
            details={"member_id": member_id, "role_code": payload.role_code},
        )
    except AccessValidationError as exc:
        return _error_response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="VALIDATION_ERROR",
            message=str(exc),
            details={"member_id": member_id, "role_code": payload.role_code},
        )
    return ProjectMemberRolesResponse(data=role_codes, request_id=new_public_id("req"))


@router.delete(
    "/projects/{project_id}/members/{member_id}/roles/{role_code}",
    response_model=ProjectMemberRolesResponse,
    summary="撤销项目成员角色",
)
def revoke_member_role(
    project_id: int,
    member_id: int,
    role_code: str,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> ProjectMemberRolesResponse | JSONResponse:
    _ensure_can_manage_project_members(
        db, current_user=current_user, project_id=project_id
    )
    try:
        role_codes = revoke_project_role(
            db=db,
            project_id=project_id,
            member_id=member_id,
            role_code=role_code,
            actor_id=current_user.id,
        )
    except AccessNotFoundError as exc:
        return _error_response(
            status_code=status.HTTP_404_NOT_FOUND,
            code="ROLE_OR_MEMBER_NOT_FOUND",
            message=str(exc),
            details={"member_id": member_id, "role_code": role_code},
        )
    except AccessValidationError as exc:
        return _error_response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="VALIDATION_ERROR",
            message=str(exc),
            details={"member_id": member_id, "role_code": role_code},
        )
    return ProjectMemberRolesResponse(data=role_codes, request_id=new_public_id("req"))


def _ensure_can_manage_system_users(current_user: User) -> None:
    ensure_system_capability(
        current_user,
        capability="can_manage_system_users",
    )


def _ensure_can_manage_project_members(
    db: Session,
    *,
    current_user: User,
    project_id: int,
) -> None:
    ensure_project_capability(
        db,
        user_id=current_user.id,
        project_id=project_id,
        capability="can_manage_project_members",
    )


def _error_response(
    *,
    status_code: int,
    code: str,
    message: str,
    details: dict[str, Any] | None = None,
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": code,
                "message": message,
                "details": details or {},
            },
            "request_id": new_public_id("req"),
        },
    )


def _user_read(value: Any) -> UserRead:
    return UserRead(
        id=value.id,
        username=value.username,
        display_name=value.display_name,
        email=value.email,
        status=value.status,
        is_system_admin=value.is_system_admin,
    )


def _role_read(value: Any) -> RoleRead:
    return RoleRead(
        code=value.code,
        display_name=value.display_name,
        scope=value.scope,
        description=value.description,
        capabilities=value.capabilities,
    )


def _member_read(value: Any) -> ProjectMemberRead:
    return ProjectMemberRead(
        member_id=value.member_id,
        project_id=value.project_id,
        user=_user_read(value.user),
        member_status=value.member_status,
        roles=value.roles,
    )


def _capability_read(value: Any) -> ProjectCapabilitiesRead:
    return ProjectCapabilitiesRead(
        project_id=value.project_id,
        user_id=value.user_id,
        member_status=value.member_status,
        roles=value.roles,
        capabilities=value.capabilities,
    )
