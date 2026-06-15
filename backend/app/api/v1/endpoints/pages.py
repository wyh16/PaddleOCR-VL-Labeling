from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Body, Depends, Query, status
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import (
    ensure_project_capability,
    get_current_user,
    get_jwt_secret_key,
)
from app.db.models import User
from app.db.models.asset import Asset
from app.db.models.document import Document
from app.db.models.page import Page
from app.db.models.project import Project
from app.db.models.qc import QcResult
from app.db.session import get_db_session
from app.schemas.annotation import (
    AnnotationRevisionReadData,
    AnnotationRevisionListItem,
    AnnotationRevisionListResponse,
    AnnotationRevisionResponse,
)
from app.schemas.page import (
    PageImageRead,
    PageListOut,
    PageOut,
    PageReadData,
    PageReadResponse,
)
from app.services.annotation_service import (
    AnnotationRevisionNotFoundError,
    InvalidAnnotationError,
    PageNotFoundError,
    create_annotation_revision,
    get_annotation_revision,
    get_latest_annotation_revision,
    get_page_detail,
    list_annotation_revisions,
    RevisionConflictError,
)
from app.storage.local import StorageError
from app.utils.ids import new_public_id

router = APIRouter(tags=["pages"])

PAGE_IMAGE_RAW_METHOD = "GET"
PAGE_IMAGE_NONCE_BYTES = 12
# 主图 raw 链接改为一次性 nonce。这里先用进程内短期缓存阻止重放，
# 避免已签发 URL 在有效期内被重复复用；后续多实例部署再切到 Redis。
_PAGE_IMAGE_NONCE_CACHE: dict[str, int] = {}


# ── 页面详情 ──


@router.get(
    "/pages/{page_id}",
    response_model=PageReadResponse,
    summary="获取页面详情",
)
def read_page(
    page_id: str,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    try:
        page = get_page_detail(db=db, page_public_id=page_id)
    except PageNotFoundError as exc:
        return _error_response(
            status_code=status.HTTP_404_NOT_FOUND,
            code="PAGE_NOT_FOUND",
            message=str(exc),
            details={"page_id": page_id},
        )
    ensure_project_capability(
        db,
        user_id=current_user.id,
        project_id=int(page["project_id"]),
        capability="can_view_project",
    )
    return PageReadResponse(data=_page_data(page), request_id=new_public_id("req"))


# ── 页面图片 ──


@router.get(
    "/pages/{page_id}/image", summary="获取页面图片访问 URL", response_model=None
)
def get_page_image_url(
    page_id: str,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    try:
        page_data = get_page_detail(db=db, page_public_id=page_id)
    except PageNotFoundError as exc:
        return _error_response(
            status_code=status.HTTP_404_NOT_FOUND,
            code="PAGE_NOT_FOUND",
            message=str(exc),
            details={"page_id": page_id},
        )
    ensure_project_capability(
        db,
        user_id=current_user.id,
        project_id=int(page_data["project_id"]),
        capability="can_view_project",
    )
    expires_at = datetime.now(UTC) + timedelta(minutes=5)
    exp = int(expires_at.timestamp())
    nonce = secrets.token_urlsafe(PAGE_IMAGE_NONCE_BYTES)
    sig = _sign_page_image_url(
        page_id=page_id,
        user_id=current_user.id,
        exp=exp,
        nonce=nonce,
    )
    return {
        "url": f"/api/v1/pages/{page_id}/image/raw?exp={exp}&nonce={nonce}&sig={sig}",
        "expires_at": expires_at.isoformat().replace("+00:00", "Z"),
    }


@router.get(
    "/pages/{page_id}/image/raw", summary="获取页面图片文件", response_model=None
)
def get_page_image_raw(
    page_id: str,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
    exp: int = Query(..., ge=0),
    nonce: str = Query(..., min_length=8),
    sig: str = Query(..., min_length=8),
):
    if not _verify_page_image_url(
        page_id=page_id,
        user_id=current_user.id,
        exp=exp,
        nonce=nonce,
        sig=sig,
    ):
        return _error_response(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="IMAGE_URL_EXPIRED",
            message="Image URL expired.",
            details={"page_id": page_id},
        )
    try:
        page_data = get_page_detail(db=db, page_public_id=page_id)
    except PageNotFoundError:
        page_data = None
    if page_data is not None:
        ensure_project_capability(
            db,
            user_id=current_user.id,
            project_id=int(page_data["project_id"]),
            capability="can_view_project",
        )
    page = db.scalar(select(Page).where(Page.public_id == page_id))
    if not page:
        return _error_response(
            status_code=status.HTTP_404_NOT_FOUND,
            code="PAGE_NOT_FOUND",
            message="Page not found",
            details={"page_id": page_id},
        )
    if not page.image_asset_id:
        return _error_response(
            status_code=status.HTTP_404_NOT_FOUND,
            code="IMAGE_NOT_FOUND",
            message="Page has no image asset",
            details={"page_id": page_id},
        )

    asset = db.get(Asset, page.image_asset_id)
    if not asset:
        return _error_response(
            status_code=status.HTTP_404_NOT_FOUND,
            code="ASSET_NOT_FOUND",
            message="Asset not found",
            details={"page_id": page_id},
        )

    settings = get_settings()
    file_path = Path(settings.storage_root) / asset.storage_path
    if not file_path.exists():
        return _error_response(
            status_code=status.HTTP_404_NOT_FOUND,
            code="FILE_NOT_FOUND",
            message="Image file not found on disk",
            details={"page_id": page_id},
        )

    return FileResponse(
        path=str(file_path), media_type=asset.mime_type or "application/octet-stream"
    )


# ── 标注 ──


@router.get(
    "/pages/{page_id}/annotation/latest",
    response_model=AnnotationRevisionResponse,
    summary="读取页面最新标注版本",
)
def read_latest_annotation_revision(
    page_id: str,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    try:
        page = get_page_detail(db=db, page_public_id=page_id)
    except PageNotFoundError as exc:
        return _error_response(
            status_code=status.HTTP_404_NOT_FOUND,
            code="PAGE_NOT_FOUND",
            message=str(exc),
            details={"page_id": page_id},
        )
    ensure_project_capability(
        db,
        user_id=current_user.id,
        project_id=int(page["project_id"]),
        capability="can_view_project",
    )
    try:
        result = get_latest_annotation_revision(db=db, page_public_id=page_id)
    except AnnotationRevisionNotFoundError:
        return AnnotationRevisionResponse(
            data=None,
            request_id=new_public_id("req"),
        )
    except StorageError as exc:
        return _error_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            code="STORAGE_ERROR",
            message=str(exc),
            details={"page_id": page_id},
        )
    return AnnotationRevisionResponse(
        data=_revision_data(
            revision=result["revision"],
            asset=result["asset"],
            annotation_json=result["annotation_json"],
            page_id=page_id,
        ),
        request_id=new_public_id("req"),
    )


@router.post(
    "/pages/{page_id}/annotation/revisions",
    response_model=AnnotationRevisionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="创建页面标注版本",
)
def create_page_annotation_revision(
    page_id: str,
    payload: dict[str, Any] = Body(
        ..., description="整页 annotation JSON 或包装后的提交请求。"
    ),
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    try:
        page = get_page_detail(db=db, page_public_id=page_id)
    except PageNotFoundError as exc:
        return _error_response(
            status_code=status.HTTP_404_NOT_FOUND,
            code="PAGE_NOT_FOUND",
            message=str(exc),
            details={"page_id": page_id},
        )
    ensure_project_capability(
        db,
        user_id=current_user.id,
        project_id=int(page["project_id"]),
        capability="can_create_annotation_revision",
    )
    annotation_json, change_summary, change_reason, base_revision_id = (
        _extract_revision_payload(payload)
    )
    try:
        revision = create_annotation_revision(
            db=db,
            page_public_id=page_id,
            annotation_json=annotation_json,
            created_by=current_user.id,
            change_summary=change_summary,
            change_reason=change_reason,
            base_revision_id=base_revision_id,
        )
        result = get_annotation_revision(db=db, revision_public_id=revision.public_id)
    except InvalidAnnotationError as exc:
        return _error_response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="VALIDATION_ERROR",
            message=str(exc),
            details={"page_id": page_id},
        )
    except RevisionConflictError as exc:
        return _error_response(
            status_code=status.HTTP_409_CONFLICT,
            code="REVISION_CONFLICT",
            message=str(exc),
            details={"page_id": page_id},
        )
    except PageNotFoundError as exc:
        return _error_response(
            status_code=status.HTTP_404_NOT_FOUND,
            code="PAGE_NOT_FOUND",
            message=str(exc),
            details={"page_id": page_id},
        )
    except StorageError as exc:
        return _error_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            code="STORAGE_ERROR",
            message=str(exc),
            details={"page_id": page_id},
        )
    return AnnotationRevisionResponse(
        data=_revision_data(
            revision=revision,
            asset=result["asset"],
            annotation_json=result["annotation_json"],
            page_id=page_id,
        ),
        request_id=new_public_id("req"),
    )


@router.get(
    "/pages/{page_id}/annotation/revisions",
    response_model=AnnotationRevisionListResponse,
    summary="列出页面标注版本",
)
def list_page_annotation_revisions(
    page_id: str,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    try:
        page = get_page_detail(db=db, page_public_id=page_id)
    except PageNotFoundError as exc:
        return _error_response(
            status_code=status.HTTP_404_NOT_FOUND,
            code="PAGE_NOT_FOUND",
            message=str(exc),
            details={"page_id": page_id},
        )
    ensure_project_capability(
        db,
        user_id=current_user.id,
        project_id=int(page["project_id"]),
        capability="can_view_project",
    )

    revisions, total = list_annotation_revisions(
        db=db,
        page_public_id=page_id,
        limit=limit,
        offset=offset,
    )
    items = [
        AnnotationRevisionListItem(
            revision_id=r.public_id,
            page_id=page_id,
            revision_no=r.revision_no,
            status=r.status,
            qc_status=r.qc_status,
            created_at=getattr(r, "created_at", None),
            change_summary=getattr(r, "change_summary", None),
        )
        for r in revisions
    ]
    return AnnotationRevisionListResponse(items=items, total=total)


@router.get(
    "/pages/{page_id}/annotation/revisions/{revision_id}",
    response_model=AnnotationRevisionResponse,
    summary="读取页面指定标注版本",
)
def read_page_annotation_revision(
    page_id: str,
    revision_id: str,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    try:
        page = get_page_detail(db=db, page_public_id=page_id)
    except PageNotFoundError as exc:
        return _error_response(
            status_code=status.HTTP_404_NOT_FOUND,
            code="PAGE_NOT_FOUND",
            message=str(exc),
            details={"page_id": page_id, "revision_id": revision_id},
        )
    ensure_project_capability(
        db,
        user_id=current_user.id,
        project_id=page["project_id"],
        capability="can_view_project",
    )
    try:
        result = get_annotation_revision(db=db, revision_public_id=revision_id)
        if result["revision"].page_id != page["page_id"]:
            raise AnnotationRevisionNotFoundError(f"标注版本不存在：{revision_id}")
    except AnnotationRevisionNotFoundError as exc:
        return _error_response(
            status_code=status.HTTP_404_NOT_FOUND,
            code="ANNOTATION_REVISION_NOT_FOUND",
            message=str(exc),
            details={"page_id": page_id, "revision_id": revision_id},
        )
    except StorageError as exc:
        return _error_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            code="STORAGE_ERROR",
            message=str(exc),
            details={"page_id": page_id, "revision_id": revision_id},
        )
    return AnnotationRevisionResponse(
        data=_revision_data(
            revision=result["revision"],
            asset=result["asset"],
            annotation_json=result["annotation_json"],
            page_id=page_id,
        ),
        request_id=new_public_id("req"),
    )


# ── QC ──


@router.get("/pages/{page_id}/qc", summary="获取页面 QC 问题列表", response_model=None)
def list_page_qc(
    page_id: str,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    page = db.scalar(select(Page).where(Page.public_id == page_id))
    if not page:
        return _error_response(
            status_code=status.HTTP_404_NOT_FOUND,
            code="PAGE_NOT_FOUND",
            message="Page not found",
            details={"page_id": page_id},
        )

    document = db.get(Document, page.document_id)
    if not document:
        return _error_response(
            status_code=status.HTTP_404_NOT_FOUND,
            code="DOCUMENT_NOT_FOUND",
            message="Document not found for page",
            details={"page_id": page_id},
        )

    ensure_project_capability(
        db,
        user_id=current_user.id,
        project_id=document.project_id,
        capability="can_view_project",
    )

    rows = db.scalars(
        select(QcResult)
        .where(QcResult.page_id == page.id)
        .order_by(QcResult.created_at.desc())
    ).all()

    items = []
    for r in rows:
        items.append(
            {
                "id": str(r.id),
                "page_id": page.public_id,
                "annotation_id": None,
                "severity": r.status,
                "code": r.qc_type,
                "message": r.summary or "",
                "details": r.details_json,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
        )

    return {"items": items, "total": len(items)}


# ── 项目级页面列表 ──


def list_project_pages(
    project_id: int,
    db: Session,
    current_user: User,
) -> PageListOut:
    """被 projects router 调用的内部函数：获取项目下所有页面。"""
    project = db.get(Project, project_id)
    if not project:
        return _error_response(
            status_code=status.HTTP_404_NOT_FOUND,
            code="PROJECT_NOT_FOUND",
            message="Project not found",
        )

    ensure_project_capability(
        db,
        user_id=current_user.id,
        project_id=project_id,
        capability="can_view_project",
    )

    stmt = (
        select(Page, Document)
        .join(Document, Page.document_id == Document.id)
        .where(Document.project_id == project_id)
        .order_by(Page.created_at.desc())
    )
    rows = db.execute(stmt).all()

    items = []
    for page, doc in rows:
        filename = (doc.domain_metadata_json or {}).get(
            "original_filename"
        ) or f"page-{page.public_id}"
        items.append(
            PageOut(
                id=page.id,
                page_id=page.public_id,
                project_id=doc.project_id,
                filename=filename,
                status=page.status,
                width=page.width,
                height=page.height,
                created_at=page.created_at,
                updated_at=page.updated_at,
            )
        )

    return PageListOut(items=items, total=len(items))


# ── 内部工具函数 ──


def _build_page_image_raw_path(page_id: str) -> str:
    return f"/api/v1/pages/{page_id}/image/raw"


def _sign_page_image_url(*, page_id: str, user_id: int, exp: int, nonce: str) -> str:
    message = (
        f"{PAGE_IMAGE_RAW_METHOD}.{_build_page_image_raw_path(page_id)}."
        f"{page_id}.{user_id}.{exp}.{nonce}"
    ).encode("utf-8")
    digest = hmac.new(
        get_jwt_secret_key().encode("utf-8"),
        message,
        hashlib.sha256,
    ).digest()
    return base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")


def _verify_page_image_url(
    *, page_id: str, user_id: int, exp: int, nonce: str, sig: str
) -> bool:
    now = int(datetime.now(UTC).timestamp())
    if exp <= now:
        return False
    if exp - now > 60 * 60:
        return False
    expected = _sign_page_image_url(
        page_id=page_id,
        user_id=user_id,
        exp=exp,
        nonce=nonce,
    )
    if not hmac.compare_digest(expected, sig):
        return False
    return _consume_page_image_nonce(user_id=user_id, nonce=nonce, exp=exp)


def _consume_page_image_nonce(*, user_id: int, nonce: str, exp: int) -> bool:
    now = int(datetime.now(UTC).timestamp())
    expired_cache_keys = [
        cache_key
        for cache_key, cache_exp in _PAGE_IMAGE_NONCE_CACHE.items()
        if cache_exp <= now
    ]
    for cache_key in expired_cache_keys:
        _PAGE_IMAGE_NONCE_CACHE.pop(cache_key, None)

    cache_key = f"{user_id}:{nonce}"
    if cache_key in _PAGE_IMAGE_NONCE_CACHE:
        return False
    _PAGE_IMAGE_NONCE_CACHE[cache_key] = exp
    return True


def _error_response(
    *,
    status_code: int,
    code: str,
    message: str,
    details: dict[str, Any] | None = None,
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": code,
                "message": message,
                "details": details or {},
            },
            "request_id": new_public_id("req"),
        },
    )


def _extract_revision_payload(
    payload: dict[str, Any],
) -> tuple[dict[str, Any], str | None, str | None, str | None]:
    annotation_json = payload.get("annotation_json")
    if isinstance(annotation_json, dict):
        return (
            annotation_json,
            _optional_text(payload.get("change_summary")),
            _optional_text(payload.get("change_reason")),
            _optional_text(payload.get("base_revision_id")),
        )
    return payload, None, None, None


def _optional_text(value: Any) -> str | None:
    return value if isinstance(value, str) and value.strip() else None


def _page_data(page: dict[str, Any]) -> PageReadData:
    return PageReadData(
        page_id=page["page_public_id"],
        document_id=page["document_public_id"],
        project_id=page["project_id"],
        page_index=page["page_index"],
        status=page["status"],
        capture_method=page.get("capture_method"),
        visual_difficulty=page.get("visual_difficulty"),
        image=PageImageRead(
            asset_id=page.get("image_asset_public_id"),
            width=page["width"],
            height=page["height"],
            sha256=page.get("image_sha256"),
        ),
    )


def _revision_data(
    *,
    revision: Any,
    asset: Any,
    annotation_json: dict[str, Any],
    page_id: str,
) -> AnnotationRevisionReadData:
    return AnnotationRevisionReadData(
        revision_id=revision.public_id,
        page_id=page_id,
        revision_no=revision.revision_no,
        status=revision.status,
        qc_status=revision.qc_status,
        sha256=getattr(asset, "sha256", None),
        size_bytes=getattr(asset, "size_bytes", None),
        annotation_json=annotation_json,
    )
