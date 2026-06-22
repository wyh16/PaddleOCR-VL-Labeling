from __future__ import annotations

import pytest

from app.core.password_policy import normalize_and_validate_password
from app.core.security import hash_password


def test_normalize_and_validate_password_rejects_short_password() -> None:
    with pytest.raises(ValueError) as exc_info:
        normalize_and_validate_password("12345")
    assert str(exc_info.value) == "密码长度不能少于 6 个字符。"


def test_hash_password_rejects_too_long_password() -> None:
    with pytest.raises(ValueError) as exc_info:
        hash_password("a" * 129)

    assert str(exc_info.value) == "密码长度不能超过 128 个字符。"


def test_normalize_and_validate_password_trims_before_validation() -> None:
    assert normalize_and_validate_password("  12345678  ") == "12345678"
