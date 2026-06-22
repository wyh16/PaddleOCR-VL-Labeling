"""M4a 访问管理 service 验收测试。

覆盖事项：
1. 当前用户项目 capabilities 可返回给前端，用于按钮展示或禁用。
2. viewer 不具备创建 annotation revision 的能力。
3. 项目成员禁用、移除和项目角色授予、撤销都必须写 audit_logs。
"""

from __future__ import annotations

from typing import Any

import pytest

from app.core.security import verify_password
from app.db.models import MemberRoleBinding, ProjectMember, RoleRegistry, User
from app.services import access_service


class RecordingDb:
    def __init__(self) -> None:
        self.commits = 0
        self.rollbacks = 0

    def commit(self) -> None:
        self.commits += 1

    def rollback(self) -> None:
        self.rollbacks += 1


class RecordingAccessRepository:
    def __init__(self) -> None:
        self.viewer_role = RoleRegistry(
            id=1,
            code="viewer",
            display_name="查看者",
            scope="project",
            permissions_json={"capabilities": ["can_view_project"]},
            is_active=True,
        )
        self.annotator_role = RoleRegistry(
            id=2,
            code="annotator",
            display_name="标注员",
            scope="project",
            permissions_json={
                "capabilities": [
                    "can_view_project",
                    "can_create_annotation_revision",
                ]
            },
            is_active=True,
        )
        self.project_admin_role = RoleRegistry(
            id=3,
            code="project_admin",
            display_name="项目管理员",
            scope="project",
            permissions_json={
                "capabilities": [
                    "can_view_project",
                    "can_manage_project_members",
                    "can_create_annotation_revision",
                ]
            },
            is_active=True,
        )
        self.system_admin_role = RoleRegistry(
            id=4,
            code="system_admin",
            display_name="系统管理员",
            scope="system",
            permissions_json={"capabilities": ["can_manage_system_users"]},
            is_active=True,
        )
        self.inactive_role = RoleRegistry(
            id=5,
            code="inactive_project_role",
            display_name="停用角色",
            scope="project",
            permissions_json={"capabilities": ["can_view_project"]},
            is_active=False,
        )
        self.users = {
            20: User(
                id=20,
                username="target_user",
                display_name="目标用户",
                status="active",
            ),
            21: User(
                id=21,
                username="disabled_user",
                display_name="停用用户",
                status="disabled",
            ),
            22: User(
                id=22,
                username="pending_user",
                display_name="待初始化用户",
                status="pending",
            ),
        }
        self.member = ProjectMember(
            id=7,
            project_id=10,
            user_id=20,
            member_status="active",
        )
        self.bindings: list[MemberRoleBinding] = []
        self.audit_logs: list[dict[str, Any]] = []
        self.last_lock_for_update = False

    def list_users(self, _db: object) -> list[User]:
        return list(self.users.values())

    def list_active_system_admins(
        self,
        _db: object,
        *,
        lock_for_update: bool = False,
    ) -> list[User]:
        self.last_lock_for_update = lock_for_update
        return [
            user
            for user in self.users.values()
            if user.is_system_admin and user.status == "active"
        ]

    def get_user(self, _db: object, user_id: int) -> User | None:
        return self.users.get(user_id)

    def get_user_by_username(self, _db: object, username: str) -> User | None:
        normalized_username = username.casefold()
        for user in self.users.values():
            if user.username.casefold() == normalized_username:
                return user
        return None

    def get_user_by_email(self, _db: object, email: str) -> User | None:
        normalized_email = email.casefold()
        for user in self.users.values():
            if user.email is not None and user.email.casefold() == normalized_email:
                return user
        return None

    def create_user(
        self,
        _db: object,
        *,
        username: str,
        display_name: str,
        email: str | None,
        password_hash: str,
        is_system_admin: bool,
        password_must_change: bool,
    ) -> User:
        user_id = max(self.users) + 1
        user = User(
            id=user_id,
            username=username,
            display_name=display_name,
            email=email,
            password_hash=password_hash,
            status="active",
            is_system_admin=is_system_admin,
        )
        user.password_must_change = password_must_change
        self.users[user_id] = user
        return user

    def list_builtin_roles(self, _db: object) -> list[RoleRegistry]:
        return [
            self.viewer_role,
            self.annotator_role,
            self.project_admin_role,
            self.system_admin_role,
            self.inactive_role,
        ]

    def get_project_member(
        self,
        _db: object,
        *,
        project_id: int,
        member_id: int,
    ) -> ProjectMember | None:
        if project_id == self.member.project_id and member_id == self.member.id:
            return self.member
        return None

    def get_project_member_by_user(
        self,
        _db: object,
        *,
        project_id: int,
        user_id: int,
    ) -> ProjectMember | None:
        if project_id == self.member.project_id and user_id == self.member.user_id:
            return self.member
        return None

    def list_project_members(
        self, _db: object, *, project_id: int
    ) -> list[ProjectMember]:
        return [self.member] if project_id == self.member.project_id else []

    def add_project_member(
        self,
        _db: object,
        *,
        project_id: int,
        user_id: int,
        created_by: int,
    ) -> ProjectMember:
        self.member.project_id = project_id
        self.member.user_id = user_id
        self.member.created_by = created_by
        self.member.member_status = "active"
        return self.member

    def set_member_status(
        self,
        _db: object,
        *,
        member: ProjectMember,
        status: str,
    ) -> ProjectMember:
        member.member_status = status
        return member

    def get_role_by_code(self, _db: object, role_code: str) -> RoleRegistry | None:
        return {
            "viewer": self.viewer_role,
            "annotator": self.annotator_role,
            "project_admin": self.project_admin_role,
            "system_admin": self.system_admin_role,
            "inactive_project_role": self.inactive_role,
        }.get(role_code)

    def list_member_role_codes(
        self,
        _db: object,
        *,
        project_member_id: int,
    ) -> list[str]:
        return sorted(
            role.code
            for binding in self.bindings
            if binding.project_member_id == project_member_id
            and binding.status == "active"
            for role in [self.get_role_by_id(binding.role_id)]
            if role is not None
        )

    def list_member_role_records(
        self,
        _db: object,
        *,
        project_member_id: int,
    ) -> list[RoleRegistry]:
        return [
            role
            for binding in self.bindings
            if binding.project_member_id == project_member_id
            and binding.status == "active"
            for role in [self.get_role_by_id(binding.role_id)]
            if role is not None
        ]

    def get_role_by_id(self, role_id: int) -> RoleRegistry | None:
        for role in [
            self.viewer_role,
            self.annotator_role,
            self.project_admin_role,
            self.system_admin_role,
            self.inactive_role,
        ]:
            if role.id == role_id:
                return role
        return None

    def find_active_role_binding(
        self,
        _db: object,
        *,
        project_member_id: int,
        role_id: int,
    ) -> MemberRoleBinding | None:
        for binding in self.bindings:
            if (
                binding.project_member_id == project_member_id
                and binding.role_id == role_id
                and binding.status == "active"
            ):
                return binding
        return None

    def grant_project_role(
        self,
        _db: object,
        *,
        project_member_id: int,
        role: RoleRegistry,
        granted_by: int,
    ) -> MemberRoleBinding:
        existing = self.find_active_role_binding(
            _db,
            project_member_id=project_member_id,
            role_id=role.id,
        )
        if existing is not None:
            return existing
        binding = MemberRoleBinding(
            id=len(self.bindings) + 100,
            project_member_id=project_member_id,
            role_id=role.id,
            role_scope="project",
            granted_by=granted_by,
            status="active",
        )
        self.bindings.append(binding)
        return binding

    def revoke_project_role(
        self,
        _db: object,
        *,
        binding: MemberRoleBinding,
        revoked_by: int,
    ) -> MemberRoleBinding:
        binding.status = "revoked"
        binding.revoked_by = revoked_by
        return binding

    def write_audit_log(self, _db: object, **kwargs: Any) -> None:
        self.audit_logs.append(kwargs)


def test_capability_profile_exposes_frontend_permissions(
    monkeypatch: Any,
) -> None:
    db = RecordingDb()
    repository = RecordingAccessRepository()
    repository.grant_project_role(
        db,
        project_member_id=7,
        role=repository.viewer_role,
        granted_by=1,
    )
    monkeypatch.setattr(
        access_service,
        "get_project_capabilities",
        lambda _db, *, user_id, project_id: {"can_view_project"},
    )

    profile = access_service.get_project_capability_profile(
        db=db,  # type: ignore[arg-type]
        project_id=10,
        user_id=20,
        repository=repository,
    )

    assert profile.roles == ["viewer"]
    assert profile.capabilities == ["can_view_project"]
    assert "can_create_annotation_revision" not in profile.capabilities


def test_capability_profile_for_non_member_is_empty() -> None:
    db = RecordingDb()
    repository = RecordingAccessRepository()

    profile = access_service.get_project_capability_profile(
        db=db,  # type: ignore[arg-type]
        project_id=999,
        user_id=20,
        repository=repository,
    )

    assert profile.member_status is None
    assert profile.roles == []
    assert profile.capabilities == []


def test_capability_profile_for_disabled_member_has_no_write_capability(
    monkeypatch: Any,
) -> None:
    db = RecordingDb()
    repository = RecordingAccessRepository()
    repository.member.member_status = "disabled"
    repository.grant_project_role(
        db,
        project_member_id=7,
        role=repository.annotator_role,
        granted_by=1,
    )
    monkeypatch.setattr(
        access_service,
        "get_project_capabilities",
        lambda _db, *, user_id, project_id: set(),
    )

    profile = access_service.get_project_capability_profile(
        db=db,  # type: ignore[arg-type]
        project_id=10,
        user_id=20,
        repository=repository,
    )

    assert profile.member_status == "disabled"
    assert profile.capabilities == []
    assert "can_create_annotation_revision" not in profile.capabilities


def test_add_project_member_writes_audit_log() -> None:
    db = RecordingDb()
    repository = RecordingAccessRepository()

    member = access_service.add_project_member(
        db=db,  # type: ignore[arg-type]
        project_id=10,
        user_id=20,
        actor_id=99,
        repository=repository,
    )

    assert member.member_id == 7
    assert db.commits == 1
    assert repository.audit_logs[-1]["action"] == "member.add"
    assert repository.audit_logs[-1]["project_id"] == 10
    assert repository.audit_logs[-1]["actor_id"] == 99
    assert repository.audit_logs[-1]["after_json"]["member_status"] == "active"


def test_add_project_member_rejects_missing_user() -> None:
    db = RecordingDb()
    repository = RecordingAccessRepository()

    with pytest.raises(access_service.AccessNotFoundError, match="用户不存在"):
        access_service.add_project_member(
            db=db,  # type: ignore[arg-type]
            project_id=10,
            user_id=404,
            actor_id=99,
            repository=repository,
        )

    assert db.commits == 0
    assert repository.audit_logs == []


@pytest.mark.parametrize("user_id", [21, 22])
def test_add_project_member_rejects_inactive_user(user_id: int) -> None:
    db = RecordingDb()
    repository = RecordingAccessRepository()

    with pytest.raises(access_service.AccessValidationError, match="active"):
        access_service.add_project_member(
            db=db,  # type: ignore[arg-type]
            project_id=10,
            user_id=user_id,
            actor_id=99,
            repository=repository,
        )

    assert db.commits == 0
    assert repository.audit_logs == []


def test_disable_user_writes_audit_log() -> None:
    db = RecordingDb()
    repository = RecordingAccessRepository()

    user = access_service.disable_user(
        db=db,  # type: ignore[arg-type]
        user_id=20,
        actor_id=99,
        repository=repository,
    )

    assert user.status == "disabled"
    assert db.commits == 1
    assert repository.audit_logs[-1]["action"] == "user.disable"
    assert repository.audit_logs[-1]["resource_type"] == "user"
    assert repository.audit_logs[-1]["before_json"] == {"status": "active"}
    assert repository.audit_logs[-1]["after_json"] == {"status": "disabled"}


def test_list_roles_returns_active_builtin_capabilities() -> None:
    db = RecordingDb()
    repository = RecordingAccessRepository()

    roles = access_service.list_roles(
        db=db,  # type: ignore[arg-type]
        repository=repository,
    )

    role_by_code = {role.code: role for role in roles}
    assert role_by_code["viewer"].capabilities == ["can_view_project"]
    assert role_by_code["project_admin"].capabilities == [
        "can_create_annotation_revision",
        "can_manage_project_members",
        "can_view_project",
    ]


def test_list_project_members_skips_orphan_member() -> None:
    db = RecordingDb()
    repository = RecordingAccessRepository()
    orphan_member = ProjectMember(
        id=8,
        project_id=10,
        user_id=404,
        member_status="active",
    )
    repository.list_project_members = lambda _db, *, project_id: (  # type: ignore[method-assign]
        [repository.member, orphan_member] if project_id == 10 else []
    )

    members = access_service.list_project_members(
        db=db,  # type: ignore[arg-type]
        project_id=10,
        repository=repository,
    )

    assert [member.member_id for member in members] == [7]


def test_create_user_hashes_password_sets_first_login_flag_and_writes_safe_audit() -> (
    None
):
    db = RecordingDb()
    repository = RecordingAccessRepository()

    user = access_service.create_user(
        db=db,  # type: ignore[arg-type]
        username="new_annotator",
        display_name="新标注员",
        email="new_annotator@example.com",
        temporary_password="ChangeMe-123456",
        is_system_admin=False,
        actor_id=99,
        repository=repository,
    )
    stored_user = repository.users[user.id]

    assert user.username == "new_annotator"
    assert user.status == "active"
    assert user.is_system_admin is False
    assert stored_user.password_hash != "ChangeMe-123456"
    assert verify_password("ChangeMe-123456", stored_user.password_hash)
    assert stored_user.password_must_change is True
    assert db.commits == 1
    assert repository.audit_logs[-1]["action"] == "user.create"
    assert repository.audit_logs[-1]["resource_type"] == "user"
    assert repository.audit_logs[-1]["actor_id"] == 99
    assert repository.audit_logs[-1]["after_json"] == {
        "user_id": user.id,
        "username": "new_annotator",
        "email": "new_annotator@example.com",
        "status": "active",
        "is_system_admin": False,
        "password_must_change": True,
    }
    assert "temporary_password" not in str(repository.audit_logs[-1])
    assert "password_hash" not in str(repository.audit_logs[-1])
    assert "ChangeMe-123456" not in str(repository.audit_logs[-1])


@pytest.mark.parametrize(
    ("field", "value", "error_match"),
    [
        ("username", "target_user", "用户名已存在"),
        ("email", "target@example.com", "邮箱已存在"),
    ],
)
def test_create_user_rejects_duplicate_username_or_email(
    field: str,
    value: str,
    error_match: str,
) -> None:
    db = RecordingDb()
    repository = RecordingAccessRepository()
    repository.users[20].email = "target@example.com"
    kwargs = {
        "username": "unique_user",
        "display_name": "唯一用户",
        "email": "unique@example.com",
        "temporary_password": "ChangeMe-123456",
        "is_system_admin": False,
    }
    kwargs[field] = value

    with pytest.raises(access_service.AccessValidationError, match=error_match):
        access_service.create_user(
            db=db,  # type: ignore[arg-type]
            actor_id=99,
            repository=repository,
            **kwargs,
        )

    assert db.commits == 0
    assert repository.audit_logs == []


def test_update_user_validates_before_mutating_user_state() -> None:
    db = RecordingDb()
    repository = RecordingAccessRepository()
    target_user = repository.users[20]
    target_user.email = "target@example.com"
    repository.users[30] = User(
        id=30,
        username="other_user",
        display_name="其他用户",
        email="duplicate@example.com",
        status="active",
        is_system_admin=False,
    )

    with pytest.raises(access_service.AccessValidationError, match="邮箱已存在"):
        access_service.update_user(
            db=db,  # type: ignore[arg-type]
            user_id=20,
            actor_id=99,
            display_name="新的显示名",
            email="duplicate@example.com",
            repository=repository,
        )

    assert target_user.display_name == "目标用户"
    assert target_user.email == "target@example.com"
    assert db.commits == 0
    assert db.rollbacks == 0
    assert repository.audit_logs == []


def test_disable_user_checks_last_admin_with_lock() -> None:
    db = RecordingDb()
    repository = RecordingAccessRepository()
    repository.users[20].is_system_admin = True
    repository.users[99] = User(
        id=99,
        username="system_admin_2",
        display_name="系统管理员二号",
        status="active",
        is_system_admin=True,
    )

    access_service.disable_user(
        db=db,  # type: ignore[arg-type]
        user_id=20,
        actor_id=101,
        repository=repository,
    )

    assert repository.last_lock_for_update is True


def test_update_user_demotes_system_admin_with_lock() -> None:
    db = RecordingDb()
    repository = RecordingAccessRepository()
    repository.users[99] = User(
        id=99,
        username="system_admin_2",
        display_name="系统管理员二号",
        status="active",
        is_system_admin=True,
    )
    repository.users[20].is_system_admin = True

    access_service.update_user(
        db=db,  # type: ignore[arg-type]
        user_id=20,
        actor_id=101,
        is_system_admin=False,
        repository=repository,
    )

    assert repository.last_lock_for_update is True


def test_grant_project_role_rejects_disabled_member() -> None:
    db = RecordingDb()
    repository = RecordingAccessRepository()
    repository.member.member_status = "disabled"

    with pytest.raises(access_service.AccessValidationError, match="active"):
        access_service.grant_project_role(
            db=db,  # type: ignore[arg-type]
            project_id=10,
            member_id=7,
            role_code="viewer",
            actor_id=99,
            repository=repository,
        )

    assert db.commits == 0
    assert repository.bindings == []


@pytest.mark.parametrize(
    ("role_code", "error_type"),
    [
        ("system_admin", access_service.AccessValidationError),
        ("inactive_project_role", access_service.AccessNotFoundError),
        ("missing_role", access_service.AccessNotFoundError),
    ],
)
def test_grant_project_role_rejects_invalid_role(
    role_code: str,
    error_type: type[Exception],
) -> None:
    db = RecordingDb()
    repository = RecordingAccessRepository()

    with pytest.raises(error_type):
        access_service.grant_project_role(
            db=db,  # type: ignore[arg-type]
            project_id=10,
            member_id=7,
            role_code=role_code,
            actor_id=99,
            repository=repository,
        )

    assert db.commits == 0
    assert repository.bindings == []


def test_grant_project_role_is_idempotent_for_existing_active_binding() -> None:
    db = RecordingDb()
    repository = RecordingAccessRepository()

    first_roles = access_service.grant_project_role(
        db=db,  # type: ignore[arg-type]
        project_id=10,
        member_id=7,
        role_code="viewer",
        actor_id=99,
        repository=repository,
    )
    second_roles = access_service.grant_project_role(
        db=db,  # type: ignore[arg-type]
        project_id=10,
        member_id=7,
        role_code="viewer",
        actor_id=99,
        repository=repository,
    )

    assert first_roles == ["viewer"]
    assert second_roles == ["viewer"]
    assert len(repository.bindings) == 1


def test_revoke_project_role_rejects_unbound_role() -> None:
    db = RecordingDb()
    repository = RecordingAccessRepository()

    with pytest.raises(access_service.AccessNotFoundError, match="未绑定"):
        access_service.revoke_project_role(
            db=db,  # type: ignore[arg-type]
            project_id=10,
            member_id=7,
            role_code="viewer",
            actor_id=99,
            repository=repository,
        )

    assert db.commits == 0
    assert repository.audit_logs == []


def test_member_and_role_changes_write_audit_logs() -> None:
    db = RecordingDb()
    repository = RecordingAccessRepository()

    access_service.grant_project_role(
        db=db,  # type: ignore[arg-type]
        project_id=10,
        member_id=7,
        role_code="annotator",
        actor_id=99,
        repository=repository,
    )
    access_service.revoke_project_role(
        db=db,  # type: ignore[arg-type]
        project_id=10,
        member_id=7,
        role_code="annotator",
        actor_id=99,
        repository=repository,
    )
    access_service.disable_project_member(
        db=db,  # type: ignore[arg-type]
        project_id=10,
        member_id=7,
        actor_id=99,
        repository=repository,
    )
    access_service.remove_project_member(
        db=db,  # type: ignore[arg-type]
        project_id=10,
        member_id=7,
        actor_id=99,
        repository=repository,
    )

    assert [item["action"] for item in repository.audit_logs] == [
        "role.grant",
        "role.revoke",
        "member.disable",
        "member.remove",
    ]
    for item in repository.audit_logs:
        assert item["project_id"] == 10
        assert item["actor_id"] == 99
        assert item["resource_type"] in {"member_role_binding", "project_member"}
        assert item["resource_id"] is not None
    assert db.commits == 4


def test_disable_project_member_rejects_non_active_member() -> None:
    db = RecordingDb()
    repository = RecordingAccessRepository()
    repository.member.member_status = "disabled"

    with pytest.raises(access_service.AccessValidationError, match="只能禁用 active"):
        access_service.disable_project_member(
            db=db,  # type: ignore[arg-type]
            project_id=10,
            member_id=7,
            actor_id=99,
            repository=repository,
        )

    assert db.commits == 0


def test_remove_project_member_rejects_already_removed_member() -> None:
    db = RecordingDb()
    repository = RecordingAccessRepository()
    repository.member.member_status = "removed"

    with pytest.raises(access_service.AccessValidationError, match="已被移除"):
        access_service.remove_project_member(
            db=db,  # type: ignore[arg-type]
            project_id=10,
            member_id=7,
            actor_id=99,
            repository=repository,
        )

    assert db.commits == 0
