from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import AuditLog, MemberRoleBinding, ProjectMember, RoleRegistry, User


class AccessRepository:
    def list_users(self, db: Session) -> list[User]:
        stmt = select(User).where(User.deleted_at.is_(None)).order_by(User.id)
        return list(db.scalars(stmt))

    def get_user(self, db: Session, user_id: int) -> User | None:
        stmt = select(User).where(User.id == user_id, User.deleted_at.is_(None))
        return db.scalar(stmt)

    def get_user_by_username(self, db: Session, username: str) -> User | None:
        stmt = select(User).where(
            func.lower(User.username) == username.lower(),
            User.deleted_at.is_(None),
        )
        return db.scalar(stmt)

    def get_user_by_email(self, db: Session, email: str) -> User | None:
        stmt = select(User).where(
            func.lower(User.email) == email.lower(),
            User.deleted_at.is_(None),
        )
        return db.scalar(stmt)

    def create_user(
        self,
        db: Session,
        *,
        username: str,
        display_name: str,
        email: str | None,
        password_hash: str,
        is_system_admin: bool,
        password_must_change: bool,
    ) -> User:
        user = User(
            username=username,
            display_name=display_name,
            email=email,
            password_hash=password_hash,
            password_must_change=password_must_change,
            status="active",
            is_system_admin=is_system_admin,
        )
        db.add(user)
        db.flush()
        return user

    def list_builtin_roles(self, db: Session) -> list[RoleRegistry]:
        stmt = (
            select(RoleRegistry)
            .where(RoleRegistry.is_builtin.is_(True), RoleRegistry.is_active.is_(True))
            .order_by(RoleRegistry.scope, RoleRegistry.code)
        )
        return list(db.scalars(stmt))

    def get_project_member(
        self,
        db: Session,
        *,
        project_id: int,
        member_id: int,
    ) -> ProjectMember | None:
        stmt = select(ProjectMember).where(
            ProjectMember.id == member_id,
            ProjectMember.project_id == project_id,
        )
        return db.scalar(stmt)

    def get_project_member_by_user(
        self,
        db: Session,
        *,
        project_id: int,
        user_id: int,
    ) -> ProjectMember | None:
        stmt = select(ProjectMember).where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user_id,
        )
        return db.scalar(stmt)

    def list_project_members(
        self, db: Session, *, project_id: int
    ) -> list[ProjectMember]:
        stmt = (
            select(ProjectMember)
            .where(ProjectMember.project_id == project_id)
            .order_by(ProjectMember.id)
        )
        return list(db.scalars(stmt))

    def add_project_member(
        self,
        db: Session,
        *,
        project_id: int,
        user_id: int,
        created_by: int,
    ) -> ProjectMember:
        existing = self.get_project_member_by_user(
            db,
            project_id=project_id,
            user_id=user_id,
        )
        if existing is not None:
            existing.member_status = "active"
            existing.removed_at = None
            return existing

        member = ProjectMember(
            project_id=project_id,
            user_id=user_id,
            member_status="active",
            created_by=created_by,
        )
        db.add(member)
        db.flush()
        return member

    def set_member_status(
        self,
        db: Session,
        *,
        member: ProjectMember,
        status: str,
    ) -> ProjectMember:
        member.member_status = status
        if status == "removed":
            member.removed_at = datetime.now(UTC)
        db.flush()
        return member

    def get_role_by_code(self, db: Session, role_code: str) -> RoleRegistry | None:
        stmt = select(RoleRegistry).where(RoleRegistry.code == role_code)
        return db.scalar(stmt)

    def list_member_role_codes(
        self,
        db: Session,
        *,
        project_member_id: int,
    ) -> list[str]:
        stmt = (
            select(RoleRegistry.code)
            .join(MemberRoleBinding, MemberRoleBinding.role_id == RoleRegistry.id)
            .where(
                MemberRoleBinding.project_member_id == project_member_id,
                MemberRoleBinding.status == "active",
                RoleRegistry.scope == "project",
                RoleRegistry.is_active.is_(True),
            )
            .order_by(RoleRegistry.code)
        )
        return list(db.scalars(stmt))

    def list_member_role_records(
        self,
        db: Session,
        *,
        project_member_id: int,
    ) -> list[RoleRegistry]:
        stmt = (
            select(RoleRegistry)
            .join(MemberRoleBinding, MemberRoleBinding.role_id == RoleRegistry.id)
            .where(
                MemberRoleBinding.project_member_id == project_member_id,
                MemberRoleBinding.status == "active",
                RoleRegistry.scope == "project",
                RoleRegistry.is_active.is_(True),
            )
            .order_by(RoleRegistry.code)
        )
        return list(db.scalars(stmt))

    def find_active_role_binding(
        self,
        db: Session,
        *,
        project_member_id: int,
        role_id: int,
    ) -> MemberRoleBinding | None:
        stmt = select(MemberRoleBinding).where(
            MemberRoleBinding.project_member_id == project_member_id,
            MemberRoleBinding.role_id == role_id,
            MemberRoleBinding.status == "active",
        )
        return db.scalar(stmt)

    def grant_project_role(
        self,
        db: Session,
        *,
        project_member_id: int,
        role: RoleRegistry,
        granted_by: int,
    ) -> MemberRoleBinding:
        existing = self.find_active_role_binding(
            db,
            project_member_id=project_member_id,
            role_id=role.id,
        )
        if existing is not None:
            return existing
        binding = MemberRoleBinding(
            project_member_id=project_member_id,
            role_id=role.id,
            role_scope="project",
            granted_by=granted_by,
            status="active",
        )
        db.add(binding)
        db.flush()
        return binding

    def revoke_project_role(
        self,
        db: Session,
        *,
        binding: MemberRoleBinding,
        revoked_by: int,
    ) -> MemberRoleBinding:
        binding.status = "revoked"
        binding.revoked_by = revoked_by
        binding.revoked_at = datetime.now(UTC)
        db.flush()
        return binding

    def write_audit_log(
        self,
        db: Session,
        *,
        project_id: int | None,
        actor_id: int | None,
        action: str,
        resource_type: str,
        resource_id: str | None,
        before_json: dict[str, Any] | None = None,
        after_json: dict[str, Any] | None = None,
    ) -> None:
        db.add(
            AuditLog(
                project_id=project_id,
                actor_id=actor_id,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                before_json=before_json,
                after_json=after_json,
            )
        )


DEFAULT_ACCESS_REPOSITORY = AccessRepository()
