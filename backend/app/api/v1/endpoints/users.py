from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import get_current_user, hash_password
from app.db.models import AuditLog, MemberRoleBinding, ProjectMember, RoleRegistry, User
from app.db.models.project import Project
from app.db.session import get_db_session
from app.schemas.user import UserCreate, UserListOut, UserOut, UserUpdate

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=UserListOut, summary="获取系统用户列表")
def list_users(
    q: str | None = None,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> UserListOut:
    _ensure_system_admin(current_user)

    stmt = (
        select(User).where(User.deleted_at.is_(None)).order_by(User.created_at.desc())
    )
    keyword = q.strip() if q else ""
    if keyword:
        like_pattern = f"%{keyword}%"
        stmt = stmt.where(
            or_(
                User.username.ilike(like_pattern),
                User.display_name.ilike(like_pattern),
                User.email.ilike(like_pattern),
            )
        )

    users = db.scalars(stmt).all()
    return UserListOut(
        items=[UserOut.model_validate(user) for user in users], total=len(users)
    )


@router.post(
    "",
    response_model=UserOut,
    status_code=status.HTTP_201_CREATED,
    summary="创建系统用户",
)
def create_user(
    payload: UserCreate,
    request: Request,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> UserOut:
    _ensure_system_admin(current_user)

    user = User(
        username=payload.username,
        display_name=payload.display_name,
        email=payload.email,
        password_hash=hash_password(payload.password),
        status="active",
        is_system_admin=payload.is_system_admin,
    )
    db.add(user)
    _flush_user_change(db)
    _append_audit_log(
        db=db,
        actor=current_user,
        request=request,
        action="system_user_created",
        resource_id=str(user.id),
        after_json=_serialize_user(user),
    )
    if payload.project_id is not None:
        _upsert_project_assignment(
            db=db,
            actor=current_user,
            request=request,
            target_user=user,
            project_id=payload.project_id,
            role_codes=payload.project_role_codes,
        )
    _commit_user_change(db)
    db.refresh(user)
    return UserOut.model_validate(user)


@router.patch("/{user_id}", response_model=UserOut, summary="更新系统用户")
def update_user(
    user_id: int,
    payload: UserUpdate,
    request: Request,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> UserOut:
    _ensure_system_admin(current_user)
    user = _get_user_or_404(db, user_id)
    before_json = _serialize_user(user)

    if payload.display_name is not None:
        user.display_name = payload.display_name
    if payload.email is not None:
        user.email = payload.email
    if payload.password is not None:
        user.password_hash = hash_password(payload.password)
    if payload.is_system_admin is not None:
        user.is_system_admin = payload.is_system_admin

    _append_audit_log(
        db=db,
        actor=current_user,
        request=request,
        action="system_user_updated",
        resource_id=str(user.id),
        before_json=before_json,
        after_json=_serialize_user(user),
    )
    if payload.project_id is not None and payload.project_role_codes is not None:
        _upsert_project_assignment(
            db=db,
            actor=current_user,
            request=request,
            target_user=user,
            project_id=payload.project_id,
            role_codes=payload.project_role_codes,
        )
    _commit_user_change(db)
    db.refresh(user)
    return UserOut.model_validate(user)


@router.post("/{user_id}/disable", response_model=UserOut, summary="禁用系统用户")
def disable_user(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> UserOut:
    _ensure_system_admin(current_user)
    user = _get_user_or_404(db, user_id)
    before_json = _serialize_user(user)
    user.status = "disabled"
    _append_audit_log(
        db=db,
        actor=current_user,
        request=request,
        action="system_user_disabled",
        resource_id=str(user.id),
        before_json=before_json,
        after_json=_serialize_user(user),
    )
    _commit_user_change(db)
    db.refresh(user)
    return UserOut.model_validate(user)


@router.post("/{user_id}/enable", response_model=UserOut, summary="启用系统用户")
def enable_user(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> UserOut:
    _ensure_system_admin(current_user)
    user = _get_user_or_404(db, user_id)
    before_json = _serialize_user(user)
    user.status = "active"
    _append_audit_log(
        db=db,
        actor=current_user,
        request=request,
        action="system_user_enabled",
        resource_id=str(user.id),
        before_json=before_json,
        after_json=_serialize_user(user),
    )
    _commit_user_change(db)
    db.refresh(user)
    return UserOut.model_validate(user)


def _ensure_system_admin(current_user: User) -> None:
    if not current_user.is_system_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied.",
        )


def _get_user_or_404(db: Session, user_id: int) -> User:
    user = db.scalar(select(User).where(User.id == user_id, User.deleted_at.is_(None)))
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return user


def _append_audit_log(
    *,
    db: Session,
    actor: User,
    request: Request,
    action: str,
    resource_id: str,
    resource_type: str = "user",
    project_id: int | None = None,
    before_json: dict | None = None,
    after_json: dict | None = None,
) -> None:
    db.add(
        AuditLog(
            project_id=project_id,
            actor_id=actor.id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            before_json=before_json,
            after_json=after_json,
            request_id=request.headers.get("x-request-id"),
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )
    )


def _upsert_project_assignment(
    *,
    db: Session,
    actor: User,
    request: Request,
    target_user: User,
    project_id: int,
    role_codes: list[str],
) -> None:
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    member = db.scalar(
        select(ProjectMember).where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == target_user.id,
        )
    )
    if member is None:
        member = ProjectMember(
            project_id=project_id,
            user_id=target_user.id,
            member_status="active",
            created_by=actor.id,
        )
        db.add(member)
        db.flush()
        _append_audit_log(
            db=db,
            actor=actor,
            request=request,
            action="project_member_created",
            resource_id=str(member.id),
            resource_type="project_member",
            project_id=project_id,
            after_json={
                "project_id": project_id,
                "user_id": target_user.id,
                "member_status": member.member_status,
            },
        )
    elif member.member_status != "active":
        before_json = {
            "project_id": member.project_id,
            "user_id": member.user_id,
            "member_status": member.member_status,
        }
        member.member_status = "active"
        member.removed_at = None
        _append_audit_log(
            db=db,
            actor=actor,
            request=request,
            action="project_member_reactivated",
            resource_id=str(member.id),
            resource_type="project_member",
            project_id=project_id,
            before_json=before_json,
            after_json={
                "project_id": member.project_id,
                "user_id": member.user_id,
                "member_status": member.member_status,
            },
        )

    available_roles = db.scalars(
        select(RoleRegistry).where(
            RoleRegistry.scope == "project",
            RoleRegistry.is_active.is_(True),
            RoleRegistry.code.in_(role_codes or ["__empty__"]),
        )
    ).all()
    available_roles_by_code = {role.code: role for role in available_roles}
    unknown_role_codes = [role_code for role_code in role_codes if role_code not in available_roles_by_code]
    if unknown_role_codes:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unknown project roles: {', '.join(unknown_role_codes)}",
        )

    active_bindings = db.scalars(
        select(MemberRoleBinding).where(
            MemberRoleBinding.project_member_id == member.id,
            MemberRoleBinding.status == "active",
        )
    ).all()
    active_bindings_by_role_id = {binding.role_id: binding for binding in active_bindings}
    desired_role_ids = {role.id for role in available_roles}
    now = datetime.now(UTC)

    for binding in active_bindings:
        if binding.role_id in desired_role_ids:
            continue
        before_json = {
            "project_member_id": member.id,
            "role_id": binding.role_id,
            "status": binding.status,
        }
        binding.status = "revoked"
        binding.revoked_by = actor.id
        binding.revoked_at = now
        _append_audit_log(
            db=db,
            actor=actor,
            request=request,
            action="project_member_role_revoked",
            resource_id=str(binding.id),
            resource_type="member_role_binding",
            project_id=project_id,
            before_json=before_json,
            after_json={
                "project_member_id": member.id,
                "role_id": binding.role_id,
                "status": binding.status,
            },
        )

    for role in available_roles:
        if role.id in active_bindings_by_role_id:
            continue
        binding = MemberRoleBinding(
            project_member_id=member.id,
            role_id=role.id,
            role_scope="project",
            granted_by=actor.id,
            status="active",
        )
        db.add(binding)
        db.flush()
        _append_audit_log(
            db=db,
            actor=actor,
            request=request,
            action="project_member_role_granted",
            resource_id=str(binding.id),
            resource_type="member_role_binding",
            project_id=project_id,
            after_json={
                "project_member_id": member.id,
                "role_id": role.id,
                "role_code": role.code,
                "status": binding.status,
            },
        )


def _flush_user_change(db: Session) -> None:
    try:
        db.flush()
    except IntegrityError as exc:
        db.rollback()
        _raise_user_conflict(exc)


def _commit_user_change(db: Session) -> None:
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        _raise_user_conflict(exc)


def _raise_user_conflict(exc: IntegrityError) -> None:
    message = str(exc.orig) if exc.orig is not None else str(exc)
    if "uq_users_username" in message or "users_username_key" in message:
        detail = "Username already exists."
    elif "uq_users_email" in message or "users_email_key" in message:
        detail = "Email already exists."
    else:
        detail = "User data conflicts with existing records."
    raise HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail=detail,
    ) from None


def _serialize_user(user: User) -> dict:
    return {
        "id": user.id,
        "username": user.username,
        "display_name": user.display_name,
        "email": user.email,
        "status": user.status,
        "is_system_admin": user.is_system_admin,
    }
