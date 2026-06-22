from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any, Protocol

from sqlalchemy.orm import Session

from app.core.security import get_project_capabilities, hash_password
from app.db.models import MemberRoleBinding, ProjectMember, RoleRegistry, User
from app.repositories.access import DEFAULT_ACCESS_REPOSITORY

USERNAME_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_.-]{2,63}$")
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
UNSET = object()


class AccessNotFoundError(ValueError):
    """用户、成员或角色不存在。"""


class AccessValidationError(ValueError):
    """访问管理输入不合法。"""


@dataclass(frozen=True)
class UserSummary:
    id: int
    username: str
    display_name: str
    email: str | None
    status: str
    is_system_admin: bool


@dataclass(frozen=True)
class RoleSummary:
    code: str
    display_name: str
    scope: str
    description: str | None
    capabilities: list[str]


@dataclass(frozen=True)
class ProjectMemberSummary:
    member_id: int
    project_id: int
    user: UserSummary
    member_status: str
    roles: list[str]


@dataclass(frozen=True)
class ProjectCapabilityProfile:
    project_id: int
    user_id: int
    member_status: str | None
    roles: list[str]
    capabilities: list[str]


class AccessRepositoryProtocol(Protocol):
    def list_users(self, db: object) -> list[User]: ...

    def get_user(self, db: object, user_id: int) -> User | None: ...

    def get_user_by_username(self, db: object, username: str) -> User | None: ...

    def get_user_by_email(self, db: object, email: str) -> User | None: ...

    def create_user(
        self,
        db: object,
        *,
        username: str,
        display_name: str,
        email: str | None,
        password_hash: str,
        is_system_admin: bool,
        password_must_change: bool,
    ) -> User: ...

    def list_builtin_roles(self, db: object) -> list[RoleRegistry]: ...

    def get_project_member(
        self,
        db: object,
        *,
        project_id: int,
        member_id: int,
    ) -> ProjectMember | None: ...

    def get_project_member_by_user(
        self,
        db: object,
        *,
        project_id: int,
        user_id: int,
    ) -> ProjectMember | None: ...

    def list_project_members(
        self,
        db: object,
        *,
        project_id: int,
    ) -> list[ProjectMember]: ...

    def add_project_member(
        self,
        db: object,
        *,
        project_id: int,
        user_id: int,
        created_by: int,
    ) -> ProjectMember: ...

    def set_member_status(
        self,
        db: object,
        *,
        member: ProjectMember,
        status: str,
    ) -> ProjectMember: ...

    def get_role_by_code(self, db: object, role_code: str) -> RoleRegistry | None: ...

    def list_member_role_codes(
        self,
        db: object,
        *,
        project_member_id: int,
    ) -> list[str]: ...

    def list_member_role_records(
        self,
        db: object,
        *,
        project_member_id: int,
    ) -> list[RoleRegistry]: ...

    def find_active_role_binding(
        self,
        db: object,
        *,
        project_member_id: int,
        role_id: int,
    ) -> MemberRoleBinding | None: ...

    def grant_project_role(
        self,
        db: object,
        *,
        project_member_id: int,
        role: RoleRegistry,
        granted_by: int,
    ) -> MemberRoleBinding: ...

    def revoke_project_role(
        self,
        db: object,
        *,
        binding: MemberRoleBinding,
        revoked_by: int,
    ) -> MemberRoleBinding: ...

    def write_audit_log(self, db: object, **kwargs: Any) -> None: ...


def list_users(
    *,
    db: Session,
    repository: AccessRepositoryProtocol | None = None,
) -> list[UserSummary]:
    repo = repository or DEFAULT_ACCESS_REPOSITORY
    return [_user_summary(user) for user in repo.list_users(db)]


def create_user(
    *,
    db: Session,
    username: str,
    display_name: str,
    email: str | None,
    temporary_password: str,
    is_system_admin: bool,
    actor_id: int,
    repository: AccessRepositoryProtocol | None = None,
) -> UserSummary:
    repo = repository or DEFAULT_ACCESS_REPOSITORY
    normalized_username = _normalize_username(username)
    normalized_email = _normalize_email(email)
    normalized_display_name = _normalize_display_name(display_name)
    _validate_temporary_password(temporary_password)

    if repo.get_user_by_username(db, normalized_username) is not None:
        raise AccessValidationError(f"用户名已存在：{normalized_username}")
    if normalized_email is not None and repo.get_user_by_email(db, normalized_email):
        raise AccessValidationError(f"邮箱已存在：{normalized_email}")

    user = repo.create_user(
        db,
        username=normalized_username,
        display_name=normalized_display_name,
        email=normalized_email,
        password_hash=hash_password(temporary_password),
        is_system_admin=is_system_admin,
        password_must_change=True,
    )
    # 审计只记录可追溯的开户事实，禁止写入 temporary_password 或
    # password_hash；否则审计表会变成长期敏感凭据泄露面。
    repo.write_audit_log(
        db,
        project_id=None,
        actor_id=actor_id,
        action="user.create",
        resource_type="user",
        resource_id=str(user.id),
        after_json={
            "user_id": user.id,
            "username": user.username,
            "email": user.email,
            "status": user.status,
            "is_system_admin": user.is_system_admin,
            "password_must_change": user.password_must_change,
        },
    )
    _commit_if_possible(db)
    return _user_summary(user)


def update_user(
    *,
    db: Session,
    user_id: int,
    actor_id: int,
    display_name: str | None = None,
    email: str | None | object = UNSET,
    temporary_password: str | None = None,
    is_system_admin: bool | None = None,
    repository: AccessRepositoryProtocol | None = None,
) -> UserSummary:
    repo = repository or DEFAULT_ACCESS_REPOSITORY
    user = repo.get_user(db, user_id)
    if user is None:
        raise AccessNotFoundError(f"用户不存在：{user_id}")

    if is_system_admin is False and user.id == actor_id:
        raise AccessValidationError(
            "You cannot remove your own system administrator role."
        )
    if is_system_admin is False:
        _ensure_not_last_active_system_admin(db=db, target_user=user, repository=repo)

    before_json = {
        "display_name": user.display_name,
        "email": user.email,
        "is_system_admin": user.is_system_admin,
        "password_must_change": user.password_must_change,
    }

    if display_name is not None:
        user.display_name = _normalize_display_name(display_name)
    if email is not UNSET:
        normalized_email = _normalize_email(email)
        if (
            normalized_email is not None
            and normalized_email != user.email
            and repo.get_user_by_email(db, normalized_email) is not None
        ):
            raise AccessValidationError(f"邮箱已存在：{normalized_email}")
        user.email = normalized_email
    if temporary_password is not None:
        _validate_temporary_password(temporary_password)
        user.password_hash = hash_password(temporary_password)
        user.password_must_change = True
    if is_system_admin is not None:
        user.is_system_admin = is_system_admin

    repo.write_audit_log(
        db,
        project_id=None,
        actor_id=actor_id,
        action="user.update",
        resource_type="user",
        resource_id=str(user.id),
        before_json=before_json,
        after_json={
            "display_name": user.display_name,
            "email": user.email,
            "is_system_admin": user.is_system_admin,
            "password_must_change": user.password_must_change,
        },
    )
    _commit_if_possible(db)
    return _user_summary(user)


def disable_user(
    *,
    db: Session,
    user_id: int,
    actor_id: int,
    repository: AccessRepositoryProtocol | None = None,
) -> UserSummary:
    repo = repository or DEFAULT_ACCESS_REPOSITORY
    user = repo.get_user(db, user_id)
    if user is None:
        raise AccessNotFoundError(f"用户不存在：{user_id}")
    if user.id == actor_id:
        raise AccessValidationError("You cannot disable your own account.")
    _ensure_not_last_active_system_admin(db=db, target_user=user, repository=repo)
    before_status = user.status
    user.status = "disabled"
    repo.write_audit_log(
        db,
        project_id=None,
        actor_id=actor_id,
        action="user.disable",
        resource_type="user",
        resource_id=str(user.id),
        before_json={"status": before_status},
        after_json={"status": user.status},
    )
    _commit_if_possible(db)
    return _user_summary(user)


def enable_user(
    *,
    db: Session,
    user_id: int,
    actor_id: int,
    repository: AccessRepositoryProtocol | None = None,
) -> UserSummary:
    repo = repository or DEFAULT_ACCESS_REPOSITORY
    user = repo.get_user(db, user_id)
    if user is None:
        raise AccessNotFoundError(f"用户不存在：{user_id}")
    before_status = user.status
    user.status = "active"
    repo.write_audit_log(
        db,
        project_id=None,
        actor_id=actor_id,
        action="user.enable",
        resource_type="user",
        resource_id=str(user.id),
        before_json={"status": before_status},
        after_json={"status": user.status},
    )
    _commit_if_possible(db)
    return _user_summary(user)


def _ensure_not_last_active_system_admin(
    *,
    db: Session,
    target_user: User,
    repository: AccessRepositoryProtocol,
) -> None:
    if not target_user.is_system_admin or target_user.status != "active":
        return

    remaining_active_admins = [
        user
        for user in repository.list_users(db)
        if user.id != target_user.id
        and user.is_system_admin
        and user.status == "active"
    ]
    if remaining_active_admins:
        return
    raise AccessValidationError("At least one active system administrator must remain.")


def list_roles(
    *,
    db: Session,
    repository: AccessRepositoryProtocol | None = None,
) -> list[RoleSummary]:
    repo = repository or DEFAULT_ACCESS_REPOSITORY
    return [_role_summary(role) for role in repo.list_builtin_roles(db)]


def list_project_members(
    *,
    db: Session,
    project_id: int,
    repository: AccessRepositoryProtocol | None = None,
) -> list[ProjectMemberSummary]:
    repo = repository or DEFAULT_ACCESS_REPOSITORY
    return [
        _member_summary(db=db, member=member, repository=repo)
        for member in repo.list_project_members(db, project_id=project_id)
    ]


def add_project_member(
    *,
    db: Session,
    project_id: int,
    user_id: int,
    actor_id: int,
    repository: AccessRepositoryProtocol | None = None,
) -> ProjectMemberSummary:
    repo = repository or DEFAULT_ACCESS_REPOSITORY
    user = repo.get_user(db, user_id)
    if user is None:
        raise AccessNotFoundError(f"用户不存在：{user_id}")
    if user.status != "active":
        raise AccessValidationError("只能把 active 用户加入项目。")
    member = repo.add_project_member(
        db,
        project_id=project_id,
        user_id=user_id,
        created_by=actor_id,
    )
    repo.write_audit_log(
        db,
        project_id=project_id,
        actor_id=actor_id,
        action="member.add",
        resource_type="project_member",
        resource_id=str(member.id),
        after_json={
            "project_member_id": member.id,
            "user_id": user_id,
            "member_status": member.member_status,
        },
    )
    _commit_if_possible(db)
    return _member_summary(db=db, member=member, repository=repo)


def disable_project_member(
    *,
    db: Session,
    project_id: int,
    member_id: int,
    actor_id: int,
    repository: AccessRepositoryProtocol | None = None,
) -> ProjectMemberSummary:
    return _set_project_member_status(
        db=db,
        project_id=project_id,
        member_id=member_id,
        actor_id=actor_id,
        status="disabled",
        action="member.disable",
        repository=repository,
    )


def remove_project_member(
    *,
    db: Session,
    project_id: int,
    member_id: int,
    actor_id: int,
    repository: AccessRepositoryProtocol | None = None,
) -> ProjectMemberSummary:
    return _set_project_member_status(
        db=db,
        project_id=project_id,
        member_id=member_id,
        actor_id=actor_id,
        status="removed",
        action="member.remove",
        repository=repository,
    )


def list_project_member_roles(
    *,
    db: Session,
    project_id: int,
    member_id: int,
    repository: AccessRepositoryProtocol | None = None,
) -> list[str]:
    repo = repository or DEFAULT_ACCESS_REPOSITORY
    member = _get_member_or_raise(
        db=db,
        project_id=project_id,
        member_id=member_id,
        repository=repo,
    )
    return repo.list_member_role_codes(db, project_member_id=member.id)


def grant_project_role(
    *,
    db: Session,
    project_id: int,
    member_id: int,
    role_code: str,
    actor_id: int,
    repository: AccessRepositoryProtocol | None = None,
) -> list[str]:
    repo = repository or DEFAULT_ACCESS_REPOSITORY
    member = _get_member_or_raise(
        db=db,
        project_id=project_id,
        member_id=member_id,
        repository=repo,
    )
    _ensure_member_active(member)
    role = _get_project_role_or_raise(db=db, role_code=role_code, repository=repo)
    binding = repo.grant_project_role(
        db,
        project_member_id=member.id,
        role=role,
        granted_by=actor_id,
    )
    repo.write_audit_log(
        db,
        project_id=project_id,
        actor_id=actor_id,
        action="role.grant",
        resource_type="member_role_binding",
        resource_id=str(binding.id) if binding.id is not None else None,
        after_json={
            "project_member_id": member.id,
            "user_id": member.user_id,
            "role_id": role.id,
            "role_code": role.code,
            "role_scope": role.scope,
            "status": binding.status,
            "granted_by": actor_id,
        },
    )
    _commit_if_possible(db)
    return repo.list_member_role_codes(db, project_member_id=member.id)


def revoke_project_role(
    *,
    db: Session,
    project_id: int,
    member_id: int,
    role_code: str,
    actor_id: int,
    repository: AccessRepositoryProtocol | None = None,
) -> list[str]:
    repo = repository or DEFAULT_ACCESS_REPOSITORY
    member = _get_member_or_raise(
        db=db,
        project_id=project_id,
        member_id=member_id,
        repository=repo,
    )
    role = _get_project_role_or_raise(db=db, role_code=role_code, repository=repo)
    binding = repo.find_active_role_binding(
        db,
        project_member_id=member.id,
        role_id=role.id,
    )
    if binding is None:
        raise AccessNotFoundError(f"成员未绑定项目角色：{role_code}")
    repo.revoke_project_role(db, binding=binding, revoked_by=actor_id)
    repo.write_audit_log(
        db,
        project_id=project_id,
        actor_id=actor_id,
        action="role.revoke",
        resource_type="member_role_binding",
        resource_id=str(binding.id) if binding.id is not None else None,
        before_json={
            "project_member_id": member.id,
            "user_id": member.user_id,
            "role_code": role.code,
            "status": "active",
        },
        after_json={
            "project_member_id": member.id,
            "user_id": member.user_id,
            "role_code": role.code,
            "status": binding.status,
            "revoked_by": actor_id,
        },
    )
    _commit_if_possible(db)
    return repo.list_member_role_codes(db, project_member_id=member.id)


def get_project_capability_profile(
    *,
    db: Session,
    project_id: int,
    user_id: int,
    repository: AccessRepositoryProtocol | None = None,
) -> ProjectCapabilityProfile:
    repo = repository or DEFAULT_ACCESS_REPOSITORY
    member = repo.get_project_member_by_user(
        db,
        project_id=project_id,
        user_id=user_id,
    )
    if member is None:
        return ProjectCapabilityProfile(
            project_id=project_id,
            user_id=user_id,
            member_status=None,
            roles=[],
            capabilities=[],
        )
    roles = repo.list_member_role_codes(db, project_member_id=member.id)
    capabilities = sorted(
        get_project_capabilities(db, user_id=user_id, project_id=project_id)
    )
    return ProjectCapabilityProfile(
        project_id=project_id,
        user_id=user_id,
        member_status=member.member_status,
        roles=roles,
        capabilities=capabilities,
    )


def _set_project_member_status(
    *,
    db: Session,
    project_id: int,
    member_id: int,
    actor_id: int,
    status: str,
    action: str,
    repository: AccessRepositoryProtocol | None,
) -> ProjectMemberSummary:
    repo = repository or DEFAULT_ACCESS_REPOSITORY
    member = _get_member_or_raise(
        db=db,
        project_id=project_id,
        member_id=member_id,
        repository=repo,
    )
    before_status = member.member_status
    repo.set_member_status(db, member=member, status=status)
    repo.write_audit_log(
        db,
        project_id=project_id,
        actor_id=actor_id,
        action=action,
        resource_type="project_member",
        resource_id=str(member.id),
        before_json={"member_status": before_status},
        after_json={
            "project_member_id": member.id,
            "user_id": member.user_id,
            "member_status": member.member_status,
        },
    )
    _commit_if_possible(db)
    return _member_summary(db=db, member=member, repository=repo)


def _get_member_or_raise(
    *,
    db: object,
    project_id: int,
    member_id: int,
    repository: AccessRepositoryProtocol,
) -> ProjectMember:
    member = repository.get_project_member(
        db,
        project_id=project_id,
        member_id=member_id,
    )
    if member is None:
        raise AccessNotFoundError(f"项目成员不存在：{member_id}")
    return member


def _ensure_member_active(member: ProjectMember) -> None:
    if member.member_status != "active":
        raise AccessValidationError("只能为 active 项目成员授予角色。")


def _get_project_role_or_raise(
    *,
    db: object,
    role_code: str,
    repository: AccessRepositoryProtocol,
) -> RoleRegistry:
    role = repository.get_role_by_code(db, role_code)
    if role is None or not role.is_active:
        raise AccessNotFoundError(f"项目角色不存在或不可用：{role_code}")
    if role.scope != "project":
        raise AccessValidationError(f"不能把系统级角色绑定到项目成员：{role_code}")
    return role


def _normalize_username(username: str) -> str:
    normalized = username.strip().lower()
    if not USERNAME_PATTERN.fullmatch(normalized):
        raise AccessValidationError(
            "用户名只能使用 3-64 位小写字母、数字、下划线、点或连字符，且必须以字母或数字开头。"
        )
    return normalized


def _normalize_display_name(display_name: str) -> str:
    normalized = display_name.strip()
    if not normalized:
        raise AccessValidationError("显示名称不能为空。")
    return normalized


def _normalize_email(email: str | None) -> str | None:
    if email is None:
        return None
    normalized = email.strip().lower()
    if not normalized:
        return None
    if not EMAIL_PATTERN.fullmatch(normalized):
        raise AccessValidationError("邮箱格式不合法。")
    return normalized


def _validate_temporary_password(temporary_password: str) -> None:
    if len(temporary_password) < 12:
        raise AccessValidationError("临时密码长度不能少于 12 个字符。")


def _user_summary(user: User) -> UserSummary:
    return UserSummary(
        id=user.id,
        username=user.username,
        display_name=user.display_name,
        email=user.email,
        status=user.status,
        is_system_admin=user.is_system_admin,
    )


def _role_summary(role: RoleRegistry) -> RoleSummary:
    capability_items = role.permissions_json.get("capabilities", [])
    capabilities = (
        sorted(item for item in capability_items if isinstance(item, str))
        if isinstance(capability_items, list)
        else []
    )
    return RoleSummary(
        code=role.code,
        display_name=role.display_name,
        scope=role.scope,
        description=role.description,
        capabilities=capabilities,
    )


def _member_summary(
    *,
    db: object,
    member: ProjectMember,
    repository: AccessRepositoryProtocol,
) -> ProjectMemberSummary:
    user = repository.get_user(db, member.user_id)
    if user is None:
        raise AccessNotFoundError(f"项目成员关联用户不存在：{member.user_id}")
    roles = repository.list_member_role_codes(db, project_member_id=member.id)
    return ProjectMemberSummary(
        member_id=member.id,
        project_id=member.project_id,
        user=_user_summary(user),
        member_status=member.member_status,
        roles=roles,
    )


def _commit_if_possible(db: object) -> None:
    if hasattr(db, "commit"):
        db.commit()
