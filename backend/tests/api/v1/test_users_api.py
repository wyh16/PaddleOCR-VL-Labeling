from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from typing import Any

import httpx
import pytest

from app.api.v1.endpoints import access as access_endpoint
from app.db.models import User
from app.main import create_app
from app.services import access_service


class ScalarResult:
    def __init__(self, items: list[object]):
        self._items = items

    def all(self) -> list[object]:
        return self._items


class FakeDb:
    def __init__(self, users: list[object] | None = None):
        self.users = users or []
        self.audit_logs: list[object] = []
        self.committed = False
        self.refreshed: list[object] = []

    def scalars(self, _stmt: object) -> ScalarResult:
        return ScalarResult(self.users)

    def scalar(self, _stmt: object) -> object | None:
        if self.users:
            return self.users[0]
        return None

    def add(self, obj: object) -> None:
        if obj.__class__.__name__ == "AuditLog":
            self.audit_logs.append(obj)
            return
        if isinstance(obj, User):
            if not getattr(obj, "id", None):
                obj.id = len(self.users) + 1
            now = datetime.now(UTC)
            obj.created_at = now
            obj.updated_at = now
            obj.last_login_at = None
            obj.deleted_at = None
            self.users.insert(0, obj)

    def flush(self) -> None:
        return None

    def commit(self) -> None:
        self.committed = True

    def refresh(self, obj: object) -> None:
        self.refreshed.append(obj)


def build_user(*, user_id: int, is_system_admin: bool, status: str = "active") -> User:
    now = datetime.now(UTC)
    return User(
        id=user_id,
        username=f"user_{user_id}",
        display_name=f"用户 {user_id}",
        email=f"user_{user_id}@example.com",
        password_hash="hashed",
        status=status,
        is_system_admin=is_system_admin,
        created_at=now,
        updated_at=now,
        last_login_at=None,
        deleted_at=None,
    )


def create_test_app(db: FakeDb, current_user: User):
    app = create_app()
    app.dependency_overrides[access_endpoint.get_current_user] = lambda: current_user
    app.dependency_overrides[access_endpoint.get_db_session] = lambda: db
    return app


def request(app: Any, method: str, path: str, **kwargs: Any) -> httpx.Response:
    async def _send() -> httpx.Response:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport,
            base_url="http://testserver",
        ) as client:
            return await client.request(method, path, **kwargs)

    return asyncio.run(_send())


def test_list_users_requires_system_admin() -> None:
    db = FakeDb(users=[build_user(user_id=2, is_system_admin=False)])
    app = create_test_app(db, build_user(user_id=1, is_system_admin=False))

    response = request(app, "GET", "/api/v1/users")

    assert response.status_code == 403
    assert response.json()["detail"] == "Permission denied."


def test_list_users_returns_visible_users() -> None:
    db = FakeDb(
        users=[
            build_user(user_id=2, is_system_admin=False),
            build_user(user_id=3, is_system_admin=True),
        ]
    )
    app = create_test_app(db, build_user(user_id=1, is_system_admin=True))

    response = request(app, "GET", "/api/v1/users")

    assert response.status_code == 200
    body = response.json()
    assert body["data"][0]["id"] == 2
    assert body["data"][1]["is_system_admin"] is True
    assert body["request_id"].startswith("req_")


def test_create_user_supports_assigning_system_admin_role(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    db = FakeDb()
    app = create_test_app(db, build_user(user_id=1, is_system_admin=True))
    monkeypatch.setattr(
        access_service, "hash_password", lambda password: f"hashed::{password}"
    )

    response = request(
        app,
        "POST",
        "/api/v1/users",
        json={
            "username": "admin2",
            "display_name": "管理员二号",
            "temporary_password": "ChangeMe-123456",
            "email": "admin2@example.com",
            "is_system_admin": True,
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["data"]["username"] == "admin2"
    assert body["data"]["is_system_admin"] is True
    assert db.users[0].password_hash == "hashed::ChangeMe-123456"
    assert len(db.audit_logs) == 1


def test_update_user_updates_profile_and_password(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    target_user = build_user(user_id=2, is_system_admin=False, status="active")
    db = FakeDb(users=[target_user])
    app = create_test_app(db, build_user(user_id=1, is_system_admin=True))
    monkeypatch.setattr(
        access_service, "hash_password", lambda password: f"hashed::{password}"
    )

    response = request(
        app,
        "PATCH",
        "/api/v1/users/2",
        json={
            "display_name": "新显示名",
            "email": None,
            "temporary_password": "ChangeMe-654321",
            "is_system_admin": True,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["data"]["display_name"] == "新显示名"
    assert body["data"]["email"] is None
    assert body["data"]["is_system_admin"] is True
    assert target_user.display_name == "新显示名"
    assert target_user.email is None
    assert target_user.password_hash == "hashed::ChangeMe-654321"
    assert len(db.audit_logs) == 1


def test_disable_user_updates_status() -> None:
    target_user = build_user(user_id=2, is_system_admin=False, status="active")
    db = FakeDb(users=[target_user])
    app = create_test_app(db, build_user(user_id=1, is_system_admin=True))

    response = request(app, "POST", "/api/v1/users/2/disable")

    assert response.status_code == 200
    assert response.json()["data"]["status"] == "disabled"
    assert target_user.status == "disabled"


def test_enable_user_updates_status() -> None:
    target_user = build_user(user_id=2, is_system_admin=False, status="disabled")
    db = FakeDb(users=[target_user])
    app = create_test_app(db, build_user(user_id=1, is_system_admin=True))

    response = request(app, "POST", "/api/v1/users/2/enable")

    assert response.status_code == 200
    assert response.json()["data"]["status"] == "active"
    assert target_user.status == "active"


def test_system_admin_cannot_disable_self() -> None:
    current_user = build_user(user_id=1, is_system_admin=True, status="active")
    db = FakeDb(users=[current_user])
    app = create_test_app(db, current_user)

    response = request(app, "POST", "/api/v1/users/1/disable")

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
    assert response.json()["error"]["message"] == "You cannot disable your own account."
    assert current_user.status == "active"


def test_system_admin_cannot_remove_own_system_role() -> None:
    current_user = build_user(user_id=1, is_system_admin=True, status="active")
    db = FakeDb(users=[current_user])
    app = create_test_app(db, current_user)

    response = request(
        app,
        "PATCH",
        "/api/v1/users/1",
        json={"is_system_admin": False},
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
    assert (
        response.json()["error"]["message"]
        == "You cannot remove your own system administrator role."
    )
    assert current_user.is_system_admin is True


def test_last_active_system_admin_cannot_be_demoted() -> None:
    target_user = build_user(user_id=2, is_system_admin=True, status="active")
    db = FakeDb(users=[target_user])
    app = create_test_app(db, build_user(user_id=1, is_system_admin=True))

    response = request(
        app,
        "PATCH",
        "/api/v1/users/2",
        json={"is_system_admin": False},
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
    assert (
        response.json()["error"]["message"]
        == "At least one active system administrator must remain."
    )
    assert target_user.is_system_admin is True


def test_disabled_system_admin_cannot_manage_users() -> None:
    db = FakeDb(users=[build_user(user_id=2, is_system_admin=False)])
    app = create_test_app(
        db, build_user(user_id=1, is_system_admin=True, status="disabled")
    )

    response = request(app, "GET", "/api/v1/users")

    assert response.status_code == 403
    assert response.json()["detail"] == "Permission denied."
