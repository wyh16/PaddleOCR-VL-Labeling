from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    username: str = Field(..., title="用户名", description="登录用户名。")
    password: str = Field(..., title="密码", description="登录密码。")


class ChangePasswordRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    current_password: str = Field(..., title="当前密码", description="当前登录密码。")
    new_password: str = Field(..., title="新密码", description="新的登录密码。")


class AuthenticatedUser(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: int = Field(..., title="用户内部编号", description="用户数据库内部主键。")
    username: str = Field(..., title="用户名", description="登录用户名。")
    display_name: str = Field(..., title="显示名称", description="用户显示名称。")
    is_system_admin: bool = Field(default=False, title="系统管理员", description="是否为系统管理员。")
    password_must_change: bool = Field(
        default=False,
        title="是否必须修改密码",
        description="管理员创建或重置密码后，下次登录需要先修改密码。",
    )


class LoginResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    expires_in: int = Field(..., title="过期秒数", description="访问令牌有效期。")
    user: AuthenticatedUser = Field(..., title="当前用户")
