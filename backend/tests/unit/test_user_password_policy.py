from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.core.security import hash_password
from app.schemas.user import UserCreate, UserUpdate


def test_user_create_rejects_short_password() -> None:
    with pytest.raises(ValidationError) as exc_info:
        UserCreate(
            username="user1",
            display_name="用户一",
            password="12345",
        )
    assert "String should have at least 6 characters" in str(exc_info.value)


def test_user_update_rejects_short_password() -> None:
    with pytest.raises(ValidationError) as exc_info:
        UserUpdate(password="12345")
    assert "String should have at least 6 characters" in str(exc_info.value)


def test_hash_password_rejects_too_long_password() -> None:
    with pytest.raises(ValueError) as exc_info:
        hash_password("a" * 129)

    assert str(exc_info.value) == "密码长度不能超过 128 个字符。"


def test_user_create_trims_password_before_validation() -> None:
    payload = UserCreate(
        username="user1",
        display_name="用户一",
        password="  12345678  ",
    )

    assert payload.password == "12345678"
