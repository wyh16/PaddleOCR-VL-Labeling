from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Body, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.core.security import ensure_project_capability, get_current_user
from app.db.models import User
from app.db.session import get_db_session
from app.schemas.annotation import (
    AnnotationRevisionReadData,
    AnnotationRevisionResponse,
)
from app.schemas.page import PageImageRead, PageReadData, PageReadResponse
from app.services.annotation_service import (
    AnnotationRevisionNotFoundError,
    InvalidAnnotationError,
    PageNotFoundError,
    create_annotation_revision,
    get_annotation_revision,
    get_latest_annotation_revision,
    get_page_detail,
    RevisionConflictError,
)
from app.storage.local import StorageError
from app.utils.ids import new_public_id

router = APIRouter(tags=["pages"])


@router.get(
    "/pages/{page_id}",
    response_model=PageReadResponse,
    summary="获取页面详情",
)
def read_page(
    page_id: str,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> PageReadResponse | JSONResponse:
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


@router.get(
    "/pages/{page_id}/annotation/latest",
    response_model=AnnotationRevisionResponse,
    summary="读取页面最新标注版本",
)
def read_latest_annotation_revision(
    page_id: str,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> AnnotationRevisionResponse | JSONResponse:
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
    except AnnotationRevisionNotFoundError as exc:
        return _error_response(
            status_code=status.HTTP_404_NOT_FOUND,
            code="ANNOTATION_REVISION_NOT_FOUND",
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
) -> AnnotationRevisionResponse | JSONResponse:
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
