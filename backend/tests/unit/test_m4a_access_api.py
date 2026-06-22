"""M4a 访问管理 API 验收测试。

覆盖事项：
1. v1 router 暴露用户、项目成员和角色相关入口。
2. project_admin 等具备 can_manage_project_members 的用户可以管理成员。
3. annotator 等缺少 can_manage_project_members 的用户不能管理成员。
4. 项目 capabilities 接口继续由 projects router 负责，避免重复路径覆盖。
"""

from __future__ import annotations

from typing import Any

import pytest
from fastapi import HTTPException, status
from fastapi.testclient import TestClient

from app.api.v1.endpoints import access as access_endpoint
from app.db.models import User
from app.main import create_app
from app.services.access_service import (
    AccessNotFoundError,
    AccessValidationError,
)


def route_methods_by_path() -> dict[str, set[str]]:
    app = create_app()
    result: dict[str, set[str]] = {}
    for route in app.routes:
        path = getattr(route, "path", "")
        methods = getattr(route, "methods", None)
        if methods:
            result.setdefault(path, set()).update(methods)
    return result


def route_endpoints_for_path(path: str) -> list[str]:
    app = create_app()
    endpoints: list[str] = []
    for route in app.routes:
        if getattr(route, "path", "") != path:
            continue
        endpoint = getattr(route, "endpoint", None)
        if endpoint is None:
            continue
        endpoints.append(f"{endpoint.__module__}.{endpoint.__name__}")
    return endpoints


def create_test_client(
    monkeypatch: Any,
    *,
    current_user: User | None = None,
) -> TestClient:
    app = create_app()
    app.dependency_overrides[access_endpoint.get_current_user] = lambda: (
        current_user
        or User(
            id=99,
            username="project_admin",
            display_name="项目管理员",
            status="active",
            is_system_admin=True,
        )
    )
    app.dependency_overrides[access_endpoint.get_db_session] = lambda: object()
    monkeypatch.setattr(
        access_endpoint,
        "ensure_project_capability",
        lambda *_args, **_kwargs: None,
    )
    return TestClient(app)


def sample_member_response() -> Any:
    user = type(
        "UserSummary",
        (),
        {
            "id": 20,
            "username": "annotator",
            "display_name": "标注员",
            "email": None,
            "status": "active",
            "is_system_admin": False,
        },
    )()
    return type(
        "ProjectMemberSummary",
        (),
        {
            "member_id": 7,
            "project_id": 10,
            "user": user,
            "member_status": "active",
            "roles": ["annotator"],
        },
    )()


def test_m4a_access_routes_are_registered() -> None:
    routes = route_methods_by_path()

    assert "GET" in routes["/api/v1/users"]
    assert "POST" in routes["/api/v1/users"]
    assert "PATCH" in routes["/api/v1/users/{user_id}"]
    assert "POST" in routes["/api/v1/users/{user_id}/disable"]
    assert "POST" in routes["/api/v1/users/{user_id}/enable"]
    assert "GET" in routes["/api/v1/roles"]
    assert "GET" in routes["/api/v1/projects/{project_id}/members"]
    assert "POST" in routes["/api/v1/projects/{project_id}/members"]
    assert "POST" in routes["/api/v1/projects/{project_id}/members/{member_id}/disable"]
    assert "DELETE" in routes["/api/v1/projects/{project_id}/members/{member_id}"]
    assert "GET" in routes["/api/v1/projects/{project_id}/members/{member_id}/roles"]
    assert "POST" in routes["/api/v1/projects/{project_id}/members/{member_id}/roles"]
    assert (
        "DELETE"
        in routes["/api/v1/projects/{project_id}/members/{member_id}/roles/{role_code}"]
    )


def test_project_capabilities_route_remains_owned_by_projects_router() -> None:
    endpoints = route_endpoints_for_path(
        "/api/v1/projects/{project_id}/me/capabilities"
    )

    assert endpoints == ["app.api.v1.endpoints.projects.get_my_capabilities"]


def test_user_routes_are_owned_by_access_router() -> None:
    list_endpoints = route_endpoints_for_path("/api/v1/users")
    update_endpoints = route_endpoints_for_path("/api/v1/users/{user_id}")
    disable_endpoints = route_endpoints_for_path("/api/v1/users/{user_id}/disable")
    enable_endpoints = route_endpoints_for_path("/api/v1/users/{user_id}/enable")

    assert list_endpoints == [
        "app.api.v1.endpoints.access.read_users",
        "app.api.v1.endpoints.access.create_user_account",
    ]
    assert update_endpoints == ["app.api.v1.endpoints.access.update_user_account"]
    assert disable_endpoints == ["app.api.v1.endpoints.access.disable_user_account"]
    assert enable_endpoints == ["app.api.v1.endpoints.access.enable_user_account"]


def test_project_admin_can_add_member_and_grant_role(monkeypatch: Any) -> None:
    client = create_test_client(monkeypatch)
    monkeypatch.setattr(
        access_endpoint,
        "add_project_member",
        lambda **_kwargs: sample_member_response(),
    )
    monkeypatch.setattr(
        access_endpoint,
        "grant_project_role",
        lambda **_kwargs: ["annotator", "viewer"],
    )

    add_response = client.post("/api/v1/projects/10/members", json={"user_id": 20})
    grant_response = client.post(
        "/api/v1/projects/10/members/7/roles",
        json={"role_code": "viewer"},
    )

    assert add_response.status_code == 201
    assert add_response.json()["data"]["member_id"] == 7
    assert grant_response.status_code == 201
    assert grant_response.json()["data"] == ["annotator", "viewer"]


def test_annotator_cannot_manage_project_members(monkeypatch: Any) -> None:
    client = create_test_client(monkeypatch)
    monkeypatch.setattr(
        access_endpoint,
        "ensure_project_capability",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permission denied.",
            )
        ),
    )
    monkeypatch.setattr(
        access_endpoint,
        "add_project_member",
        lambda **_kwargs: pytest.fail("权限不足时不能添加项目成员"),
    )

    response = client.post("/api/v1/projects/10/members", json={"user_id": 20})

    assert response.status_code == 403


def test_access_endpoint_requires_authentication() -> None:
    client = TestClient(create_app())

    response = client.get("/api/v1/projects/10/members")

    assert response.status_code == 401
    assert response.json()["detail"] == "Missing authentication token."


def test_non_system_admin_cannot_manage_users(monkeypatch: Any) -> None:
    client = create_test_client(
        monkeypatch,
        current_user=User(
            id=100,
            username="project_admin_without_system_flag",
            display_name="普通项目管理员",
            status="active",
            is_system_admin=False,
        ),
    )

    list_response = client.get("/api/v1/users")
    create_response = client.post(
        "/api/v1/users",
        json={
            "username": "new_user",
            "display_name": "新用户",
            "email": None,
            "temporary_password": "ChangeMe-123456",
            "is_system_admin": False,
        },
    )
    disable_response = client.post("/api/v1/users/20/disable")

    assert list_response.status_code == 403
    assert create_response.status_code == 403
    assert disable_response.status_code == 403


def test_user_management_endpoints_check_system_user_capability(
    monkeypatch: Any,
) -> None:
    client = create_test_client(monkeypatch)
    checked_capabilities: list[str] = []
    user_summary = type(
        "UserSummary",
        (),
        {
            "id": 20,
            "username": "target_user",
            "display_name": "目标用户",
            "email": None,
            "status": "active",
            "is_system_admin": False,
        },
    )()

    def record_system_capability(_user: User, *, capability: str) -> None:
        checked_capabilities.append(capability)

    monkeypatch.setattr(
        access_endpoint,
        "ensure_system_capability",
        record_system_capability,
    )
    monkeypatch.setattr(access_endpoint, "list_users", lambda **_kwargs: [])
    monkeypatch.setattr(access_endpoint, "create_user", lambda **_kwargs: user_summary)
    monkeypatch.setattr(access_endpoint, "disable_user", lambda **_kwargs: user_summary)

    list_response = client.get("/api/v1/users")
    create_response = client.post(
        "/api/v1/users",
        json={
            "username": "new_user",
            "display_name": "新用户",
            "email": None,
            "temporary_password": "ChangeMe-123456",
            "is_system_admin": False,
        },
    )
    disable_response = client.post("/api/v1/users/20/disable")

    assert list_response.status_code == 200
    assert create_response.status_code == 201
    assert disable_response.status_code == 200
    assert checked_capabilities == [
        "can_manage_system_users",
        "can_manage_system_users",
        "can_manage_system_users",
    ]


def test_system_admin_can_create_user_without_returning_password(
    monkeypatch: Any,
) -> None:
    client = create_test_client(monkeypatch)
    created_user = type(
        "UserSummary",
        (),
        {
            "id": 23,
            "username": "new_user",
            "display_name": "新用户",
            "email": "new_user@example.com",
            "status": "active",
            "is_system_admin": False,
        },
    )()
    monkeypatch.setattr(
        access_endpoint,
        "create_user",
        lambda **_kwargs: created_user,
        raising=False,
    )

    response = client.post(
        "/api/v1/users",
        json={
            "username": "new_user",
            "display_name": "新用户",
            "email": "new_user@example.com",
            "temporary_password": "ChangeMe-123456",
            "is_system_admin": False,
        },
    )
    payload = response.json()

    assert response.status_code == 201
    assert set(payload) == {"data", "request_id"}
    assert payload["data"] == {
        "id": 23,
        "username": "new_user",
        "display_name": "新用户",
        "email": "new_user@example.com",
        "status": "active",
        "is_system_admin": False,
    }
    assert "temporary_password" not in str(payload)
    assert "password_hash" not in str(payload)
    assert payload["request_id"].startswith("req_")


def test_create_user_maps_validation_error_to_422(monkeypatch: Any) -> None:
    client = create_test_client(monkeypatch)
    monkeypatch.setattr(
        access_endpoint,
        "create_user",
        lambda **_kwargs: (_ for _ in ()).throw(
            AccessValidationError("用户名已存在：target_user")
        ),
        raising=False,
    )

    response = client.post(
        "/api/v1/users",
        json={
            "username": "target_user",
            "display_name": "目标用户",
            "email": None,
            "temporary_password": "ChangeMe-123456",
            "is_system_admin": False,
        },
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_disable_user_endpoint_returns_wrapped_success_response(
    monkeypatch: Any,
) -> None:
    client = create_test_client(monkeypatch)
    disabled_user = type(
        "UserSummary",
        (),
        {
            "id": 20,
            "username": "target_user",
            "display_name": "目标用户",
            "email": None,
            "status": "disabled",
            "is_system_admin": False,
        },
    )()
    monkeypatch.setattr(
        access_endpoint,
        "disable_user",
        lambda **_kwargs: disabled_user,
    )

    response = client.post("/api/v1/users/20/disable")
    payload = response.json()

    assert response.status_code == 200
    assert set(payload) == {"data", "request_id"}
    assert payload["data"]["id"] == 20
    assert payload["data"]["status"] == "disabled"
    assert payload["request_id"].startswith("req_")


def test_add_project_member_maps_missing_user_to_404(monkeypatch: Any) -> None:
    client = create_test_client(monkeypatch)
    monkeypatch.setattr(
        access_endpoint,
        "add_project_member",
        lambda **_kwargs: (_ for _ in ()).throw(AccessNotFoundError("用户不存在：404")),
    )

    response = client.post("/api/v1/projects/10/members", json={"user_id": 404})

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "USER_NOT_FOUND"


def test_add_project_member_maps_inactive_user_to_422(monkeypatch: Any) -> None:
    client = create_test_client(monkeypatch)
    monkeypatch.setattr(
        access_endpoint,
        "add_project_member",
        lambda **_kwargs: (_ for _ in ()).throw(
            AccessValidationError("只能把 active 用户加入项目。")
        ),
    )

    response = client.post("/api/v1/projects/10/members", json={"user_id": 21})

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_disable_or_remove_missing_member_returns_404(monkeypatch: Any) -> None:
    client = create_test_client(monkeypatch)
    monkeypatch.setattr(
        access_endpoint,
        "disable_project_member",
        lambda **_kwargs: (_ for _ in ()).throw(
            AccessNotFoundError("项目成员不存在：404")
        ),
    )
    monkeypatch.setattr(
        access_endpoint,
        "remove_project_member",
        lambda **_kwargs: (_ for _ in ()).throw(
            AccessNotFoundError("项目成员不存在：404")
        ),
    )

    disable_response = client.post("/api/v1/projects/10/members/404/disable")
    remove_response = client.delete("/api/v1/projects/10/members/404")

    assert disable_response.status_code == 404
    assert disable_response.json()["error"]["code"] == "PROJECT_MEMBER_NOT_FOUND"
    assert remove_response.status_code == 404
    assert remove_response.json()["error"]["code"] == "PROJECT_MEMBER_NOT_FOUND"


def test_grant_system_role_maps_validation_error_to_422(monkeypatch: Any) -> None:
    client = create_test_client(monkeypatch)
    monkeypatch.setattr(
        access_endpoint,
        "grant_project_role",
        lambda **_kwargs: (_ for _ in ()).throw(
            AccessValidationError("不能把系统级角色绑定到项目成员：system_admin")
        ),
    )

    response = client.post(
        "/api/v1/projects/10/members/7/roles",
        json={"role_code": "system_admin"},
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_revoke_unbound_role_maps_not_found_to_404(monkeypatch: Any) -> None:
    client = create_test_client(monkeypatch)
    monkeypatch.setattr(
        access_endpoint,
        "revoke_project_role",
        lambda **_kwargs: (_ for _ in ()).throw(
            AccessNotFoundError("成员未绑定项目角色：viewer")
        ),
    )

    response = client.delete("/api/v1/projects/10/members/7/roles/viewer")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "ROLE_OR_MEMBER_NOT_FOUND"


def test_missing_member_or_role_request_body_returns_422(monkeypatch: Any) -> None:
    client = create_test_client(monkeypatch)

    add_response = client.post("/api/v1/projects/10/members", json={})
    grant_response = client.post("/api/v1/projects/10/members/7/roles", json={})

    assert add_response.status_code == 422
    assert grant_response.status_code == 422
