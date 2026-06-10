from __future__ import annotations

import pytest
from fastapi import HTTPException, status

from app.api.v1.endpoints import projects as projects_endpoint


class DummyDb:
    def __init__(self, project: object | None):
        self._project = project

    def get(self, _model: object, _id: int):
        return self._project


def test_get_my_capabilities_returns_404_for_missing_project() -> None:
    db = DummyDb(project=None)
    current_user = type("User", (), {"id": 1, "is_system_admin": False})()

    with pytest.raises(HTTPException) as exc_info:
        projects_endpoint.get_my_capabilities(project_id=1, db=db, current_user=current_user)

    assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND


def test_get_my_capabilities_returns_all_project_caps_for_creator(monkeypatch: pytest.MonkeyPatch) -> None:
    project = type("Project", (), {"created_by": 1})()
    db = DummyDb(project=project)
    current_user = type("User", (), {"id": 1, "is_system_admin": False})()

    monkeypatch.setattr(projects_endpoint, "get_project_capabilities", lambda *_args, **_kwargs: set())

    result = projects_endpoint.get_my_capabilities(project_id=1, db=db, current_user=current_user)
    for cap in projects_endpoint.PROJECT_CAPABILITIES:
        assert result[cap] is True
    assert result["can_manage_system_users"] is False


def test_get_my_capabilities_returns_project_member_caps(monkeypatch: pytest.MonkeyPatch) -> None:
    project = type("Project", (), {"created_by": 999})()
    db = DummyDb(project=project)
    current_user = type("User", (), {"id": 1, "is_system_admin": False})()

    monkeypatch.setattr(
        projects_endpoint,
        "get_project_capabilities",
        lambda *_args, **_kwargs: {"can_create_annotation_revision", "can_view_project"},
    )

    result = projects_endpoint.get_my_capabilities(project_id=1, db=db, current_user=current_user)
    assert result["can_view_project"] is True
    assert result["can_create_annotation_revision"] is True
    assert result["can_review_revision"] is False


def test_get_my_capabilities_includes_system_caps_for_system_admin(monkeypatch: pytest.MonkeyPatch) -> None:
    project = type("Project", (), {"created_by": 999})()
    db = DummyDb(project=project)
    current_user = type("User", (), {"id": 1, "is_system_admin": True})()

    monkeypatch.setattr(projects_endpoint, "get_project_capabilities", lambda *_args, **_kwargs: set())

    result = projects_endpoint.get_my_capabilities(project_id=1, db=db, current_user=current_user)
    assert result["can_manage_system_users"] is True
