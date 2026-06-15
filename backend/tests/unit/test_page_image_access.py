from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import pytest
from fastapi.responses import FileResponse, JSONResponse

from app.api.v1.endpoints import pages as pages_endpoint
from app.db.models.asset import Asset


class DummyDb:
    def __init__(self, *, page: object | None = None, asset: object | None = None):
        self._page = page
        self._asset = asset

    def scalar(self, _stmt: object) -> object | None:
        return self._page

    def get(self, model: object, _id: object) -> object | None:
        if model is Asset:
            return self._asset
        return None


def parse_json_response(response: JSONResponse) -> dict:
    return json.loads(response.body.decode("utf-8"))


@pytest.fixture(autouse=True)
def clear_page_image_nonce_cache() -> None:
    pages_endpoint._PAGE_IMAGE_NONCE_CACHE.clear()


def test_get_page_image_url_returns_verifiable_signed_url(monkeypatch) -> None:
    monkeypatch.setattr(
        pages_endpoint,
        "get_page_detail",
        lambda **_kwargs: {"project_id": 10},
    )
    monkeypatch.setattr(
        pages_endpoint,
        "ensure_project_capability",
        lambda *_args, **_kwargs: None,
    )

    response = pages_endpoint.get_page_image_url(
        page_id="page_public_001",
        db=object(),
        current_user=type("User", (), {"id": 99})(),
    )

    parsed = urlparse(response["url"])
    query = parse_qs(parsed.query)
    exp = int(query["exp"][0])
    nonce = query["nonce"][0]
    sig = query["sig"][0]

    assert parsed.path == "/api/v1/pages/page_public_001/image/raw"
    assert pages_endpoint._verify_page_image_url(
        page_id="page_public_001",
        user_id=99,
        exp=exp,
        nonce=nonce,
        sig=sig,
    )
    assert response["expires_at"].endswith("Z")


def test_get_page_image_raw_rejects_expired_signed_url() -> None:
    exp = int((datetime.now(UTC) - timedelta(seconds=1)).timestamp())
    sig = pages_endpoint._sign_page_image_url(
        page_id="page_public_001",
        user_id=99,
        exp=exp,
        nonce="nonce_expired_001",
    )

    response = pages_endpoint.get_page_image_raw(
        page_id="page_public_001",
        db=DummyDb(),
        current_user=type("User", (), {"id": 99})(),
        exp=exp,
        nonce="nonce_expired_001",
        sig=sig,
    )

    assert isinstance(response, JSONResponse)
    assert response.status_code == 401
    payload = parse_json_response(response)
    assert payload["error"]["code"] == "IMAGE_URL_EXPIRED"


def test_get_page_image_raw_rejects_invalid_signature() -> None:
    exp = int((datetime.now(UTC) + timedelta(minutes=5)).timestamp())

    response = pages_endpoint.get_page_image_raw(
        page_id="page_public_001",
        db=DummyDb(),
        current_user=type("User", (), {"id": 99})(),
        exp=exp,
        nonce="nonce_invalid_001",
        sig="invalid_signature",
    )

    assert isinstance(response, JSONResponse)
    assert response.status_code == 401
    payload = parse_json_response(response)
    assert payload["error"]["code"] == "IMAGE_URL_EXPIRED"


def test_get_page_image_raw_returns_file_response_for_valid_signed_url(
    monkeypatch, tmp_path: Path
) -> None:
    image_path = tmp_path / "page.png"
    image_path.write_bytes(b"fake_png")

    page = type("PageRow", (), {"image_asset_id": 1})()
    asset = type(
        "AssetRow",
        (),
        {"storage_path": "page.png", "mime_type": "image/png"},
    )()
    db = DummyDb(page=page, asset=asset)
    exp = int((datetime.now(UTC) + timedelta(minutes=5)).timestamp())
    nonce = "nonce_ok_001"
    sig = pages_endpoint._sign_page_image_url(
        page_id="page_public_001",
        user_id=99,
        exp=exp,
        nonce=nonce,
    )

    monkeypatch.setattr(
        pages_endpoint,
        "get_settings",
        lambda: type("Settings", (), {"storage_root": tmp_path})(),
    )
    monkeypatch.setattr(
        pages_endpoint,
        "get_page_detail",
        lambda **_kwargs: {"project_id": 10},
    )
    monkeypatch.setattr(
        pages_endpoint,
        "ensure_project_capability",
        lambda *_args, **_kwargs: None,
    )

    response = pages_endpoint.get_page_image_raw(
        page_id="page_public_001",
        db=db,
        current_user=type("User", (), {"id": 99})(),
        exp=exp,
        nonce=nonce,
        sig=sig,
    )

    assert isinstance(response, FileResponse)
    assert Path(response.path) == image_path


def test_get_page_image_raw_rejects_replayed_nonce(monkeypatch, tmp_path: Path) -> None:
    image_path = tmp_path / "page.png"
    image_path.write_bytes(b"fake_png")

    page = type("PageRow", (), {"image_asset_id": 1})()
    asset = type(
        "AssetRow",
        (),
        {"storage_path": "page.png", "mime_type": "image/png"},
    )()
    db = DummyDb(page=page, asset=asset)
    exp = int((datetime.now(UTC) + timedelta(minutes=5)).timestamp())
    nonce = "nonce_replay_001"
    sig = pages_endpoint._sign_page_image_url(
        page_id="page_public_001",
        user_id=99,
        exp=exp,
        nonce=nonce,
    )

    monkeypatch.setattr(
        pages_endpoint,
        "get_settings",
        lambda: type("Settings", (), {"storage_root": tmp_path})(),
    )
    monkeypatch.setattr(
        pages_endpoint,
        "get_page_detail",
        lambda **_kwargs: {"project_id": 10},
    )
    monkeypatch.setattr(
        pages_endpoint,
        "ensure_project_capability",
        lambda *_args, **_kwargs: None,
    )

    first = pages_endpoint.get_page_image_raw(
        page_id="page_public_001",
        db=db,
        current_user=type("User", (), {"id": 99})(),
        exp=exp,
        nonce=nonce,
        sig=sig,
    )
    second = pages_endpoint.get_page_image_raw(
        page_id="page_public_001",
        db=db,
        current_user=type("User", (), {"id": 99})(),
        exp=exp,
        nonce=nonce,
        sig=sig,
    )

    assert isinstance(first, FileResponse)
    assert isinstance(second, JSONResponse)
    assert second.status_code == 401


def test_get_page_image_raw_rejects_signature_for_other_user(monkeypatch) -> None:
    monkeypatch.setattr(
        pages_endpoint,
        "get_page_detail",
        lambda **_kwargs: {"project_id": 10},
    )
    monkeypatch.setattr(
        pages_endpoint,
        "ensure_project_capability",
        lambda *_args, **_kwargs: None,
    )
    exp = int((datetime.now(UTC) + timedelta(minutes=5)).timestamp())
    nonce = "nonce_user_binding_001"
    sig = pages_endpoint._sign_page_image_url(
        page_id="page_public_001",
        user_id=99,
        exp=exp,
        nonce=nonce,
    )

    response = pages_endpoint.get_page_image_raw(
        page_id="page_public_001",
        db=DummyDb(),
        current_user=type("User", (), {"id": 100})(),
        exp=exp,
        nonce=nonce,
        sig=sig,
    )

    assert isinstance(response, JSONResponse)
    assert response.status_code == 401


def test_get_page_image_raw_checks_current_user_project_capability(monkeypatch) -> None:
    calls: list[tuple[int, int, str]] = []
    exp = int((datetime.now(UTC) + timedelta(minutes=5)).timestamp())
    nonce = "nonce_capability_001"
    sig = pages_endpoint._sign_page_image_url(
        page_id="page_public_001",
        user_id=99,
        exp=exp,
        nonce=nonce,
    )

    monkeypatch.setattr(
        pages_endpoint,
        "get_page_detail",
        lambda **_kwargs: {"project_id": 10},
    )
    monkeypatch.setattr(
        pages_endpoint,
        "ensure_project_capability",
        lambda _db, *, user_id, project_id, capability: calls.append(
            (user_id, project_id, capability)
        ),
    )

    pages_endpoint.get_page_image_raw(
        page_id="page_public_001",
        db=DummyDb(),
        current_user=type("User", (), {"id": 99})(),
        exp=exp,
        nonce=nonce,
        sig=sig,
    )

    assert calls == [(99, 10, "can_view_project")]
