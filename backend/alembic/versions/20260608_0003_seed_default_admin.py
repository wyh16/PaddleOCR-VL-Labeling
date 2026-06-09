"""seed default admin user

Revision ID: 20260608_0003
Revises: 20260603_0002
Create Date: 2026-06-08
"""

from typing import Sequence

from alembic import op

revision: str = "20260608_0003"
down_revision: str | None = "20260603_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    import base64
    import hashlib
    import secrets

    password = "123456"
    salt = secrets.token_urlsafe(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 210_000)
    password_hash = (
        f"pbkdf2_sha256$210000${salt}$"
        f"{base64.urlsafe_b64encode(digest).decode('ascii').rstrip('=')}"
    )

    op.execute(
        f"""
        INSERT INTO users (username, display_name, password_hash, status, is_system_admin)
        VALUES ('admin', '管理员', '{password_hash}', 'active', true)
        ON CONFLICT (username) DO NOTHING
        """
    )


def downgrade() -> None:
    op.execute("DELETE FROM users WHERE username = 'admin' AND is_system_admin = true")
