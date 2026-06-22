from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class UserRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: int = Field(..., title="用户内部编号", description="users.id 数据库内部主键。")
    username: str = Field(..., title="用户名", description="登录和展示用用户名。")
    display_name: str = Field(..., title="显示名称", description="页面展示名称。")
    email: str | None = Field(None, title="邮箱", description="用户邮箱，可为空。")
    status: str = Field(
        ..., title="用户状态", description="用户状态，例如 active、disabled、pending。"
    )
    is_system_admin: bool = Field(
        ...,
        title="是否系统管理员",
        description="是否具备系统级用户管理能力；不代表项目内业务权限。",
    )
    last_login_at: datetime | None = Field(
        None,
        title="最近登录时间",
        description="最近登录时间；从未登录时为 null。",
    )
    created_at: datetime | None = Field(
        None,
        title="创建时间",
        description="用户创建时间。",
    )
    updated_at: datetime | None = Field(
        None,
        title="更新时间",
        description="用户最后更新时间。",
    )


class UserListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    data: list[UserRead] = Field(..., title="用户列表", description="用户列表。")
    request_id: str = Field(..., title="请求编号", description="本次请求的追踪编号。")


class UserCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    username: str = Field(
        ...,
        min_length=3,
        max_length=64,
        title="用户名",
        description="登录用户名；服务端会按白名单校验并归一化为小写。",
    )
    display_name: str = Field(
        ...,
        min_length=1,
        max_length=128,
        title="显示名称",
        description="页面展示名称。",
    )
    email: str | None = Field(
        None,
        max_length=255,
        title="邮箱",
        description="用户邮箱，可为空；填写时服务端会校验格式和唯一性。",
    )
    temporary_password: str = Field(
        ...,
        min_length=6,
        max_length=128,
        title="临时密码",
        description="只用于本次创建请求；后端只保存哈希，不返回、不审计明文。",
    )
    is_system_admin: bool = Field(
        default=False,
        title="是否系统管理员",
        description="是否创建为系统管理员；普通实验室成员应为 false。",
    )


class UserUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    display_name: str | None = Field(
        None,
        min_length=1,
        max_length=128,
        title="显示名称",
        description="页面展示名称；不传表示保持原值。",
    )
    email: str | None = Field(
        None,
        max_length=255,
        title="邮箱",
        description="用户邮箱；传 null 表示清空，省略表示保持原值。",
    )
    temporary_password: str | None = Field(
        None,
        min_length=6,
        max_length=128,
        title="临时密码",
        description="管理员重置的临时密码；不传表示不修改密码。",
    )
    is_system_admin: bool | None = Field(
        default=None,
        title="是否系统管理员",
        description="是否更新为系统管理员；不传表示保持原值。",
    )


class UserResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    data: UserRead = Field(..., title="用户", description="用户详情。")
    request_id: str = Field(..., title="请求编号", description="本次请求的追踪编号。")


class RoleRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str = Field(..., title="角色编码", description="稳定角色编码。")
    display_name: str = Field(..., title="角色显示名", description="角色中文显示名。")
    scope: str = Field(
        ..., title="角色作用域", description="角色作用域，当前为 project 或 system。"
    )
    description: str | None = Field(
        None, title="角色说明", description="角色用途说明，可为空。"
    )
    capabilities: list[str] = Field(
        ..., title="能力列表", description="该角色声明的 capability 编码列表。"
    )


class RoleListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    data: list[RoleRead] = Field(..., title="角色列表", description="内置角色列表。")
    request_id: str = Field(..., title="请求编号", description="本次请求的追踪编号。")


class ProjectMemberRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    member_id: int = Field(
        ..., title="项目成员内部编号", description="project_members.id 数据库内部主键。"
    )
    project_id: int = Field(
        ..., title="项目内部编号", description="projects.id 数据库内部主键。"
    )
    user: UserRead = Field(..., title="成员用户", description="项目成员关联的用户。")
    member_status: str = Field(
        ...,
        title="成员状态",
        description="项目成员状态，例如 active、disabled、removed。",
    )
    roles: list[str] = Field(
        ..., title="当前有效项目角色", description="当前 active 项目角色编码列表。"
    )


class ProjectMemberListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    data: list[ProjectMemberRead] = Field(
        ..., title="项目成员列表", description="项目成员列表。"
    )
    request_id: str = Field(..., title="请求编号", description="本次请求的追踪编号。")


class AddProjectMemberRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    user_id: int = Field(
        ..., title="用户内部编号", description="要加入项目的 users.id。"
    )


class ProjectMemberResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    data: ProjectMemberRead = Field(..., title="项目成员", description="项目成员详情。")
    request_id: str = Field(..., title="请求编号", description="本次请求的追踪编号。")


class GrantProjectRoleRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role_code: str = Field(
        ..., title="项目角色编码", description="要授予的项目级角色编码。"
    )


class ProjectMemberRolesResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    data: list[str] = Field(
        ..., title="当前有效项目角色", description="成员当前 active 项目角色编码列表。"
    )
    request_id: str = Field(..., title="请求编号", description="本次请求的追踪编号。")


class ProjectCapabilitiesRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    project_id: int = Field(
        ..., title="项目内部编号", description="projects.id 数据库内部主键。"
    )
    user_id: int = Field(
        ..., title="用户内部编号", description="当前登录用户的 users.id。"
    )
    member_status: str | None = Field(
        None,
        title="成员状态",
        description="当前用户在该项目中的成员状态；非项目成员时为 null。",
    )
    roles: list[str] = Field(
        ..., title="项目角色", description="当前 active 项目角色编码列表。"
    )
    capabilities: list[str] = Field(
        ...,
        title="能力列表",
        description="后端基于当前用户和项目计算出的 capability 列表。",
    )


class ProjectCapabilitiesResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    data: ProjectCapabilitiesRead = Field(
        ..., title="当前用户项目能力", description="当前用户在项目内的角色和能力。"
    )
    request_id: str = Field(..., title="请求编号", description="本次请求的追踪编号。")
