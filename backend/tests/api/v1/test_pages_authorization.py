from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from typing import Any

import httpx
from fastapi import HTTPException, status

from app.api.v1.endpoints import pages as pages_endpoint
from app.db.models import User
from app.db.models.document import Document
from app.db.models.page import Page
from app.db.models.project import Project
from app.main import create_app


class _ScalarResult:
    def __init__(self, items: list[object]):
        self._items = items

    def all(self) -> list[object]:
        return self._items


class _ExecuteResult:
    def __init__(self, rows: list[tuple[object, object]]):
        self._rows = rows

    def all(self) -> list[tuple[object, object]]:
        return self._rows


class FakeDb:
    def __init__(
        self,
        *,
        project: object | None = None,
        page: object | None = None,
        document: object | None = None,
        page_rows: list[tuple[object, object]] | None = None,
        qc_rows: list[object] | None = None,
    ):
        self._project = project
        self._page = page
        self._document = document
        self._page_rows = page_rows or []
        self._qc_rows = qc_rows or []
        self.deleted_objects: list[object] = []
        self.committed = False
        self.rolled_back = False

    def get(self, model: object, _id: object) -> object | None:
        if model is Project:
            return self._project
        if model is Document:
            return self._document
        if model is Page:
            return self._page
        return None

    def scalar(self, _stmt: object) -> object | None:
        return self._page

    def scalars(self, _stmt: object) -> _ScalarResult:
        return _ScalarResult(self._qc_rows)

    def execute(self, _stmt: object) -> _ExecuteResult:
        return _ExecuteResult(self._page_rows)

    def delete(self, obj: object) -> None:
        self.deleted_objects.append(obj)

    def commit(self) -> None:
        self.committed = True

    def rollback(self) -> None:
        self.rolled_back = True


def _project_row(project_id: int = 10) -> object:
    return type("ProjectRow", (), {"id": project_id})()


def _document_row(project_id: int = 10) -> object:
    return type(
        "DocumentRow",
        (),
        {
            "id": 20,
            "project_id": project_id,
            "domain_metadata_json": {"original_filename": "exam-page-1.png"},
        },
    )()


def _page_row() -> object:
    now = datetime.now(UTC)
    return type(
        "PageRow",
        (),
        {
            "id": 30,
            "public_id": "page_public_001",
            "document_id": 20,
            "status": "uploaded",
            "width": 1200,
            "height": 1600,
            "created_at": now,
            "updated_at": now,
        },
    )()


def _qc_row() -> object:
    return type(
        "QcRow",
        (),
        {
            "id": 40,
            "status": "warning",
            "qc_type": "bbox_overlap",
            "summary": "Boxes overlap",
            "details_json": {"suggestion": "Split the regions"},
            "created_at": datetime.now(UTC),
        },
    )()


def create_test_app(
    monkeypatch: Any,
    db: FakeDb,
    *,
    allowed_project_ids: set[int],
    allowed_capabilities: set[str] | None = None,
):
    allowed_capabilities = allowed_capabilities or {"can_view_project"}
    app = create_app()
    app.dependency_overrides[pages_endpoint.get_current_user] = lambda: User(
        id=99,
        username="annotator",
        display_name="标注员",
        status="active",
    )
    app.dependency_overrides[pages_endpoint.get_db_session] = lambda: db

    def check_capability(
        _db: Any,
        *,
        user_id: int,
        project_id: int,
        capability: str,
    ) -> None:
        assert user_id == 99
        assert capability in allowed_capabilities
        if project_id not in allowed_project_ids:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permission denied.",
            )

    monkeypatch.setattr(pages_endpoint, "ensure_project_capability", check_capability)
    monkeypatch.setattr(
        pages_endpoint,
        "get_page_detail",
        lambda *, db, page_public_id: (
            {
                "page_id": 30,
                "page_public_id": page_public_id,
                "document_id": 20,
                "document_public_id": "doc_public_001",
                "project_id": 10,
                "status": "uploaded",
                "page_index": 1,
                "capture_method": None,
                "visual_difficulty": None,
                "image_asset_public_id": None,
                "width": 1200,
                "height": 1600,
                "image_sha256": None,
            }
            if db._page is not None
            else (_ for _ in ()).throw(pages_endpoint.PageNotFoundError(page_public_id))
        ),
    )
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


def test_project_member_can_list_project_pages(monkeypatch: Any) -> None:
    db = FakeDb(
        project=_project_row(),
        page_rows=[(_page_row(), _document_row())],
    )
    app = create_test_app(monkeypatch, db, allowed_project_ids={10})

    response = request(app, "GET", "/api/v1/projects/10/pages")

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 1
    assert payload["items"][0]["page_id"] == "page_public_001"
    assert payload["items"][0]["project_id"] == 10
    assert payload["items"][0]["filename"] == "exam-page-1.png"


def test_non_member_cannot_list_project_pages(monkeypatch: Any) -> None:
    db = FakeDb(project=_project_row())
    app = create_test_app(monkeypatch, db, allowed_project_ids=set())

    response = request(app, "GET", "/api/v1/projects/10/pages")

    assert response.status_code == 403


def test_unknown_project_id_returns_404_for_project_pages(monkeypatch: Any) -> None:
    app = create_test_app(monkeypatch, FakeDb(project=None), allowed_project_ids={10})

    response = request(app, "GET", "/api/v1/projects/999/pages")

    assert response.status_code == 404
    payload = response.json()
    assert payload["error"]["code"] == "PROJECT_NOT_FOUND"


def test_project_member_can_list_page_qc(monkeypatch: Any) -> None:
    db = FakeDb(
        page=_page_row(),
        document=_document_row(),
        qc_rows=[_qc_row()],
    )
    app = create_test_app(monkeypatch, db, allowed_project_ids={10})

    response = request(app, "GET", "/api/v1/pages/page_public_001/qc")

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 1
    assert payload["items"][0]["page_id"] == "page_public_001"
    assert payload["items"][0]["severity"] == "warning"
    assert payload["items"][0]["code"] == "bbox_overlap"


def test_non_member_cannot_list_page_qc(monkeypatch: Any) -> None:
    db = FakeDb(
        page=_page_row(),
        document=_document_row(),
    )
    app = create_test_app(monkeypatch, db, allowed_project_ids=set())

    response = request(app, "GET", "/api/v1/pages/page_public_001/qc")

    assert response.status_code == 403


def test_unknown_page_id_returns_404_for_page_qc(monkeypatch: Any) -> None:
    app = create_test_app(monkeypatch, FakeDb(page=None), allowed_project_ids={10})

    response = request(app, "GET", "/api/v1/pages/page_missing/qc")

    assert response.status_code == 404
    payload = response.json()
    assert payload["error"]["code"] == "PAGE_NOT_FOUND"


def test_delete_page_endpoint_is_not_exposed(monkeypatch: Any) -> None:
    app = create_test_app(
        monkeypatch,
        FakeDb(page=_page_row()),
        allowed_project_ids={10},
    )

    response = request(app, "DELETE", "/api/v1/pages/page_public_001")

    assert response.status_code == 405
