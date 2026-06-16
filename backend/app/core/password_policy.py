from __future__ import annotations

PASSWORD_MIN_LENGTH = 6
PASSWORD_MAX_LENGTH = 128


def normalize_and_validate_password(password: str) -> str:
    normalized = password.strip()
    if not normalized:
        raise ValueError("字段不能为空。")
    if len(normalized) < PASSWORD_MIN_LENGTH:
        raise ValueError(f"密码长度不能少于 {PASSWORD_MIN_LENGTH} 个字符。")
    if len(normalized) > PASSWORD_MAX_LENGTH:
        raise ValueError(f"密码长度不能超过 {PASSWORD_MAX_LENGTH} 个字符。")
    return normalized
