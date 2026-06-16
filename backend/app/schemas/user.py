from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.core.password_policy import (
    PASSWORD_MAX_LENGTH,
    PASSWORD_MIN_LENGTH,
    normalize_and_validate_password,
)


def _normalize_optional_text(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    return normalized or None


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: int = Field(..., title="用户内部编号", description="用户数据库内部主键。")
    username: str = Field(..., title="用户名", description="登录用户名。")
    display_name: str = Field(..., title="显示名称", description="用户显示名称。")
    email: str | None = Field(default=None, title="邮箱", description="用户邮箱。")
    status: str = Field(
        ..., title="用户状态", description="用户状态：active / disabled / pending。"
    )
    is_system_admin: bool = Field(
        default=False,
        title="系统管理员",
        description="是否为系统管理员。系统管理员可管理系统用户。",
    )
    last_login_at: datetime | None = Field(
        default=None,
        title="最近登录时间",
        description="最近登录时间。",
    )
    created_at: datetime = Field(..., title="创建时间", description="创建时间。")
    updated_at: datetime = Field(..., title="更新时间", description="更新时间。")


class UserListOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[UserOut] = Field(default_factory=list, title="用户列表")
    total: int = Field(..., title="总数", description="返回用户总数。")


class UserCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    username: str = Field(..., title="用户名", description="登录用户名。")
    display_name: str = Field(..., title="显示名称", description="用户显示名称。")
    password: str = Field(
        ...,
        min_length=PASSWORD_MIN_LENGTH,
        max_length=PASSWORD_MAX_LENGTH,
        title="初始密码",
        description="用户初始密码。",
    )
    email: str | None = Field(default=None, title="邮箱", description="用户邮箱。")
    project_id: int | None = Field(
        default=None, title="项目ID", description="需要加入的项目内部主键。"
    )
    project_role_codes: list[str] = Field(
        default_factory=list,
        title="项目角色编码列表",
        description="要授予的项目级角色编码列表。",
    )
    is_system_admin: bool = Field(
        default=False,
        title="系统管理员",
        description="是否授予系统管理员能力。",
    )

    @field_validator("username", "display_name")
    @classmethod
    def validate_required_text(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("字段不能为空。")
        return normalized

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        return normalize_and_validate_password(value)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str | None) -> str | None:
        return _normalize_optional_text(value)

    @field_validator("project_role_codes")
    @classmethod
    def normalize_project_role_codes(cls, value: list[str]) -> list[str]:
        normalized = [item.strip() for item in value if item and item.strip()]
        return list(dict.fromkeys(normalized))

    @model_validator(mode="after")
    def validate_project_assignment(self) -> "UserCreate":
        if self.project_role_codes and self.project_id is None:
            raise ValueError("分配项目角色时必须提供 project_id。")
        return self


class UserUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    display_name: str | None = Field(
        default=None, title="显示名称", description="更新后的显示名称。"
    )
    password: str | None = Field(
        default=None,
        min_length=PASSWORD_MIN_LENGTH,
        max_length=PASSWORD_MAX_LENGTH,
        title="新密码",
        description="管理员重置的新密码。",
    )
    email: str | None = Field(default=None, title="邮箱", description="更新后的邮箱。")
    project_id: int | None = Field(
        default=None, title="项目ID", description="需要更新角色的项目内部主键。"
    )
    project_role_codes: list[str] | None = Field(
        default=None,
        title="项目角色编码列表",
        description="更新后的项目角色编码列表。传空数组表示清空该项目角色。",
    )
    is_system_admin: bool | None = Field(
        default=None,
        title="系统管理员",
        description="是否授予系统管理员能力。",
    )

    @field_validator("display_name")
    @classmethod
    def validate_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        if not normalized:
            raise ValueError("字段不能为空。")
        return normalized

    @field_validator("password")
    @classmethod
    def validate_optional_password(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return normalize_and_validate_password(value)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str | None) -> str | None:
        return _normalize_optional_text(value)

    @field_validator("project_role_codes")
    @classmethod
    def normalize_project_role_codes(cls, value: list[str] | None) -> list[str] | None:
        if value is None:
            return None
        normalized = [item.strip() for item in value if item and item.strip()]
        return list(dict.fromkeys(normalized))

    @model_validator(mode="after")
    def validate_has_update_fields(self) -> "UserUpdate":
        if (
            self.display_name is None
            and self.password is None
            and self.email is None
            and self.project_role_codes is None
            and self.is_system_admin is None
        ):
            raise ValueError("至少需要提供一个可更新字段。")
        if self.project_role_codes is not None and self.project_id is None:
            raise ValueError("更新项目角色时必须提供 project_id。")
        return self
