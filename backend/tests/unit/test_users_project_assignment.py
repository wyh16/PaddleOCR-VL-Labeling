from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace

from app.api.v1.endpoints import users as users_endpoint
from app.db.models import AuditLog, MemberRoleBinding, ProjectMember, RoleRegistry, User
from app.db.models.project import Project


class ScalarResult:
    def __init__(self, items: list[object]) -> None:
        self._items = items

    def all(self) -> list[object]:
        return self._items


class RecordingSession:
    def __init__(
        self,
        *,
        project: Project,
        member: ProjectMember | None,
        available_roles: list[RoleRegistry],
        active_bindings: list[MemberRoleBinding],
    ) -> None:
        self.project = project
        self.member = member
        self.available_roles = available_roles
        self.active_bindings = active_bindings
        self.added: list[object] = []
        self._scalar_calls = 0
        self._scalars_calls = 0

    def get(self, model: type[object], identity: int) -> object | None:
        if model is Project and identity == self.project.id:
            return self.project
        return None

    def scalar(self, _stmt: object) -> object | None:
        self._scalar_calls += 1
        if self._scalar_calls == 1:
            return self.member
        raise AssertionError("unexpected scalar() call")

    def scalars(self, _stmt: object) -> ScalarResult:
        self._scalars_calls += 1
        if self._scalars_calls == 1:
            return ScalarResult(self.available_roles)
        if self._scalars_calls == 2:
            return ScalarResult(self.active_bindings)
        raise AssertionError("unexpected scalars() call")

    def add(self, value: object) -> None:
        self.added.append(value)
        if isinstance(value, ProjectMember):
            self.member = value

    def flush(self) -> None:
        for value in self.added:
            if isinstance(value, ProjectMember) and getattr(value, "id", None) is None:
                value.id = 501
            if isinstance(value, MemberRoleBinding) and getattr(value, "id", None) is None:
                value.id = 900 + sum(
                    1
                    for item in self.added
                    if isinstance(item, MemberRoleBinding)
                    and getattr(item, "id", None) is not None
                )


def build_user(*, user_id: int, is_system_admin: bool = False) -> User:
    now = datetime.now(UTC)
    return User(
        id=user_id,
        username=f"user_{user_id}",
        display_name=f"用户 {user_id}",
        email=f"user_{user_id}@example.com",
        password_hash="hashed",
        status="active",
        is_system_admin=is_system_admin,
        created_at=now,
        updated_at=now,
        last_login_at=None,
        deleted_at=None,
    )


def build_request() -> SimpleNamespace:
    return SimpleNamespace(
        headers={"x-request-id": "req-1", "user-agent": "pytest"},
        client=SimpleNamespace(host="127.0.0.1"),
    )


def build_project(project_id: int) -> Project:
    return Project(
        id=project_id,
        name=f"项目 {project_id}",
        description=None,
        schema_version="v1",
        created_by=1,
    )


def build_role(role_id: int, code: str) -> RoleRegistry:
    return RoleRegistry(
        id=role_id,
        code=code,
        display_name=code,
        scope="project",
        permissions_json={},
        is_active=True,
        is_builtin=True,
    )


def test_upsert_project_assignment_creates_member_and_role_bindings() -> None:
    project = build_project(7)
    actor = build_user(user_id=1, is_system_admin=True)
    target_user = build_user(user_id=2)
    session = RecordingSession(
        project=project,
        member=None,
        available_roles=[build_role(11, "viewer"), build_role(12, "annotator")],
        active_bindings=[],
    )

    users_endpoint._upsert_project_assignment(
        db=session,  # type: ignore[arg-type]
        actor=actor,
        request=build_request(),  # type: ignore[arg-type]
        target_user=target_user,
        project_id=project.id,
        role_codes=["viewer", "annotator"],
    )

    members = [item for item in session.added if isinstance(item, ProjectMember)]
    bindings = [item for item in session.added if isinstance(item, MemberRoleBinding)]
    audit_logs = [item for item in session.added if isinstance(item, AuditLog)]

    assert len(members) == 1
    assert members[0].project_id == 7
    assert members[0].user_id == 2
    assert members[0].member_status == "active"
    assert len(bindings) == 2
    assert {binding.role_id for binding in bindings} == {11, 12}
    assert all(binding.status == "active" for binding in bindings)
    assert len(audit_logs) == 3
    assert audit_logs[0].resource_type == "project_member"
    assert audit_logs[0].project_id == 7
    assert {log.resource_type for log in audit_logs[1:]} == {"member_role_binding"}


def test_upsert_project_assignment_reactivates_member_and_replaces_roles() -> None:
    project = build_project(9)
    actor = build_user(user_id=1, is_system_admin=True)
    target_user = build_user(user_id=3)
    member = ProjectMember(
        id=88,
        project_id=project.id,
        user_id=target_user.id,
        member_status="removed",
        created_by=actor.id,
        removed_at=datetime.now(UTC),
    )
    old_binding = MemberRoleBinding(
        id=301,
        project_member_id=member.id,
        role_id=21,
        role_scope="project",
        granted_by=actor.id,
        status="active",
    )
    session = RecordingSession(
        project=project,
        member=member,
        available_roles=[build_role(22, "reviewer")],
        active_bindings=[old_binding],
    )

    users_endpoint._upsert_project_assignment(
        db=session,  # type: ignore[arg-type]
        actor=actor,
        request=build_request(),  # type: ignore[arg-type]
        target_user=target_user,
        project_id=project.id,
        role_codes=["reviewer"],
    )

    bindings = [item for item in session.added if isinstance(item, MemberRoleBinding)]
    audit_logs = [item for item in session.added if isinstance(item, AuditLog)]

    assert member.member_status == "active"
    assert member.removed_at is None
    assert old_binding.status == "revoked"
    assert old_binding.revoked_by == actor.id
    assert old_binding.revoked_at is not None
    assert len(bindings) == 1
    assert bindings[0].role_id == 22
    assert bindings[0].status == "active"
    assert [log.action for log in audit_logs] == [
        "project_member_reactivated",
        "project_member_role_revoked",
        "project_member_role_granted",
    ]
