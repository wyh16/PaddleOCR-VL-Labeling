from __future__ import annotations

from datetime import UTC

from fastapi import Response

from app.api.v1.endpoints import auth as auth_endpoint


class DummyDb:
    def __init__(self, user: object | None):
        self._user = user
        self.committed = False

    def scalar(self, _stmt: object):
        return self._user

    def commit(self) -> None:
        self.committed = True


def test_login_sets_http_only_auth_cookie(monkeypatch) -> None:
    user = type(
        "User",
        (),
        {
            "id": 1,
            "username": "annotator",
            "display_name": "标注员",
            "password_hash": "hashed",
            "status": "active",
            "deleted_at": None,
            "is_system_admin": False,
            "password_must_change": True,
            "last_login_at": None,
        },
    )()
    db = DummyDb(user=user)
    response = Response()

    monkeypatch.setattr(
        auth_endpoint, "verify_password", lambda *_args, **_kwargs: True
    )
    monkeypatch.setattr(
        auth_endpoint, "create_access_token", lambda **_kwargs: "cookie-token"
    )
    monkeypatch.setattr(
        auth_endpoint,
        "get_settings",
        lambda: type("Settings", (), {"jwt_expire_minutes": 60})(),
    )

    result = auth_endpoint.login(
        payload=auth_endpoint.LoginRequest(username="annotator", password="password"),
        response=response,
        db=db,
    )

    assert result.user.username == "annotator"
    assert result.user.password_must_change is True
    assert db.committed is True
    assert user.last_login_at is not None
    assert user.last_login_at.tzinfo == UTC
    set_cookie = response.headers.get("set-cookie", "")
    assert "k12_access_token=cookie-token" in set_cookie
    assert "HttpOnly" in set_cookie


def test_logout_clears_auth_cookie() -> None:
    response = Response()

    result = auth_endpoint.logout(response=response)

    assert result.status_code == 204
    set_cookie = response.headers.get("set-cookie", "")
    assert "k12_access_token=" in set_cookie
    assert "Max-Age=0" in set_cookie or "expires=" in set_cookie.lower()


def test_change_password_clears_first_login_flag(monkeypatch) -> None:
    user = type(
        "User",
        (),
        {
            "id": 1,
            "username": "annotator",
            "display_name": "标注员",
            "password_hash": "old-hash",
            "status": "active",
            "deleted_at": None,
            "is_system_admin": False,
            "password_must_change": True,
        },
    )()
    db = DummyDb(user=user)

    monkeypatch.setattr(
        auth_endpoint, "verify_password", lambda *_args, **_kwargs: True
    )
    monkeypatch.setattr(
        auth_endpoint, "hash_password", lambda password: f"hashed::{password}"
    )

    result = auth_endpoint.change_password(
        payload=auth_endpoint.ChangePasswordRequest(
            current_password="temp123",
            new_password="newpass1",
        ),
        db=db,
        current_user=user,
    )

    assert result.password_must_change is False
    assert user.password_hash == "hashed::newpass1"
    assert user.password_must_change is False
    assert db.committed is True


def test_change_password_rejects_wrong_current_password(monkeypatch) -> None:
    user = type(
        "User",
        (),
        {
            "id": 1,
            "username": "annotator",
            "display_name": "标注员",
            "password_hash": "old-hash",
            "status": "active",
            "deleted_at": None,
            "is_system_admin": False,
            "password_must_change": True,
        },
    )()
    db = DummyDb(user=user)

    monkeypatch.setattr(
        auth_endpoint, "verify_password", lambda *_args, **_kwargs: False
    )

    try:
        auth_endpoint.change_password(
            payload=auth_endpoint.ChangePasswordRequest(
                current_password="wrong-pass",
                new_password="newpass1",
            ),
            db=db,
            current_user=user,
        )
    except auth_endpoint.HTTPException as exc:
        assert exc.status_code == 422
        assert exc.detail == "当前密码不正确。"
    else:
        raise AssertionError("Expected HTTPException to be raised.")

    assert user.password_hash == "old-hash"
    assert user.password_must_change is True
    assert db.committed is False
