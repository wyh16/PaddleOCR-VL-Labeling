from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import get_current_user, get_project_capabilities
from app.db.models import User
from app.db.models.project import Project
from app.db.session import get_db_session
from app.schemas.page import PageListOut
from app.schemas.project import ProjectCreate, ProjectListOut, ProjectOut, ProjectUpdate

router = APIRouter(prefix="/projects", tags=["projects"])

PROJECT_CAPABILITIES: tuple[str, ...] = (
    "can_view_project",
    "can_create_annotation_revision",
    "can_submit_revision",
    "can_review_revision",
    "can_create_export_job",
    "can_download_export",
    "can_manage_project_members",
    "can_manage_labels",
    "can_manage_relations",
    "can_lock_revision",
    "can_unlock_revision",
    "can_rollback_revision",
    "can_upload_assets",
    "can_import_pages",
    "can_view_audit_log",
)

SYSTEM_CAPABILITIES: tuple[str, ...] = ("can_manage_system_users",)


@router.get("", response_model=ProjectListOut, summary="获取项目列表")
def list_projects(
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> ProjectListOut:
    projects = db.scalars(
        select(Project)
        .where(Project.created_by == current_user.id)
        .order_by(Project.created_at.desc())
    ).all()
    return ProjectListOut(
        items=[ProjectOut.model_validate(p) for p in projects],
        total=len(projects),
    )


@router.post(
    "",
    response_model=ProjectOut,
    status_code=status.HTTP_201_CREATED,
    summary="创建项目",
)
def create_project(
    payload: ProjectCreate,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> ProjectOut:
    project = Project(
        name=payload.name,
        description=payload.description,
        created_by=current_user.id,
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return ProjectOut.model_validate(project)


@router.get("/{project_id}", response_model=ProjectOut, summary="获取项目详情")
def get_project(
    project_id: int,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> ProjectOut:
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )
    # 只能访问自己创建的项目
    if project.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
        )
    return ProjectOut.model_validate(project)


@router.patch("/{project_id}", response_model=ProjectOut, summary="更新项目")
def update_project(
    project_id: int,
    payload: ProjectUpdate,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> ProjectOut:
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )
    if project.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
        )
    if payload.name is not None:
        project.name = payload.name
    if payload.description is not None:
        project.description = payload.description
    db.commit()
    db.refresh(project)
    return ProjectOut.model_validate(project)


@router.delete(
    "/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
    response_class=Response,
    summary="删除项目",
)
def delete_project(
    project_id: int,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> None:
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )
    if project.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
        )
    db.delete(project)
    db.commit()


@router.get(
    "/{project_id}/pages", response_model=PageListOut, summary="获取项目页面列表"
)
def list_project_pages(
    project_id: int,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> PageListOut:
    from app.api.v1.endpoints.pages import list_project_pages as _list

    return _list(project_id, db, current_user)


@router.get("/{project_id}/me/capabilities", summary="获取当前用户在项目中的能力")
def get_my_capabilities(
    project_id: int,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> dict:
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )

    if project.created_by == current_user.id:
        capabilities = set(PROJECT_CAPABILITIES)
    else:
        capabilities = get_project_capabilities(
            db,
            user_id=current_user.id,
            project_id=project_id,
        )

    if current_user.is_system_admin:
        capabilities.update(SYSTEM_CAPABILITIES)

    all_caps = (*PROJECT_CAPABILITIES, *SYSTEM_CAPABILITIES)
    return {capability: capability in capabilities for capability in all_caps}
