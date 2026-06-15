from __future__ import annotations

import asyncio
from typing import Any

import httpx
from sqlalchemy.exc import IntegrityError

from app.api.v1.endpoints import projects as projects_endpoint
from app.db.models import User
from app.db.models.project import Project
from app.main import create_app


class FakeDb:
    def __init__(
        self,
        *,
        project: object | None = None,
        delete_raises_integrity_error: bool = False,
        commit_raises_integrity_error: bool = False,
    ):
        self._project = project
        self._delete_raises_integrity_error = delete_raises_integrity_error
        self._commit_raises_integrity_error = commit_raises_integrity_error
        self.deleted_objects: list[object] = []
        self.committed = False
        self.rolled_back = False

    def get(self, model: object, _id: object) -> object | None:
        if model is Project:
            return self._project
        return None

    def delete(self, obj: object) -> None:
        if self._delete_raises_integrity_error:
            raise IntegrityError("DELETE FROM projects", {}, None)
        self.deleted_objects.append(obj)

    def commit(self) -> None:
        if self._commit_raises_integrity_error:
            raise IntegrityError("COMMIT", {}, None)
        self.committed = True

    def rollback(self) -> None:
        self.rolled_back = True


def _project_row(*, created_by: int = 99) -> object:
    return type(
        "ProjectRow",
        (),
        {
            "id": 10,
            "name": "demo-project",
            "description": None,
            "schema_version": "v1",
            "created_by": created_by,
        },
    )()


def create_test_app(monkeypatch: Any, db: FakeDb, *, current_user_id: int = 99):
    app = create_app()
    app.dependency_overrides[projects_endpoint.get_current_user] = lambda: User(
        id=current_user_id,
        username="project-owner",
        display_name="项目创建者",
        status="active",
    )
    app.dependency_overrides[projects_endpoint.get_db_session] = lambda: db
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


def test_project_owner_can_delete_project(monkeypatch: Any) -> None:
    project = _project_row(created_by=99)
    db = FakeDb(project=project)
    app = create_test_app(monkeypatch, db, current_user_id=99)

    response = request(app, "DELETE", "/api/v1/projects/10")

    assert response.status_code == 204
    assert db.deleted_objects == [project]
    assert db.committed is True


def test_non_owner_cannot_delete_project(monkeypatch: Any) -> None:
    db = FakeDb(project=_project_row(created_by=99))
    app = create_test_app(monkeypatch, db, current_user_id=101)

    response = request(app, "DELETE", "/api/v1/projects/10")

    assert response.status_code == 403
    assert response.json()["detail"] == "Access denied"


def test_delete_unknown_project_returns_404(monkeypatch: Any) -> None:
    app = create_test_app(monkeypatch, FakeDb(project=None), current_user_id=99)

    response = request(app, "DELETE", "/api/v1/projects/10")

    assert response.status_code == 404
    assert response.json()["detail"] == "Project not found"


def test_delete_project_with_related_data_returns_409(monkeypatch: Any) -> None:
    db = FakeDb(
        project=_project_row(created_by=99),
        delete_raises_integrity_error=True,
    )
    app = create_test_app(monkeypatch, db, current_user_id=99)

    response = request(app, "DELETE", "/api/v1/projects/10")

    assert response.status_code == 409
    assert (
        response.json()["detail"] == "Project has related data and cannot be deleted."
    )
    assert db.rolled_back is True


def test_delete_project_with_commit_integrity_error_returns_409(
    monkeypatch: Any,
) -> None:
    project = _project_row(created_by=99)
    db = FakeDb(
        project=project,
        commit_raises_integrity_error=True,
    )
    app = create_test_app(monkeypatch, db, current_user_id=99)

    response = request(app, "DELETE", "/api/v1/projects/10")

    assert response.status_code == 409
    assert (
        response.json()["detail"] == "Project has related data and cannot be deleted."
    )
    assert db.deleted_objects == [project]
    assert db.committed is False
    assert db.rolled_back is True
