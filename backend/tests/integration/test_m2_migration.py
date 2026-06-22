from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from types import ModuleType

from alembic.config import Config
from alembic.script import ScriptDirectory

from app.db.base import Base
import app.db.models.core  # noqa: F401


BACKEND_ROOT = Path(__file__).resolve().parents[2]
ALEMBIC_ROOT = BACKEND_ROOT / "alembic"
MIGRATION_PATH = BACKEND_ROOT / "alembic" / "versions" / "20260603_0001_create_core_tables.py"
ROLE_MIGRATION_PATH = (
    BACKEND_ROOT
    / "alembic"
    / "versions"
    / "20260603_0002_update_builtin_role_capabilities.py"
)
SEED_ADMIN_MIGRATION_PATH = (
    BACKEND_ROOT
    / "alembic"
    / "versions"
    / "20260608_0003_seed_default_admin.py"
)
RELAX_ANNOTATION_OBJECTS_MIGRATION_PATH = (
    BACKEND_ROOT
    / "alembic"
    / "versions"
    / "20260608_0004_relax_annotation_object_index_constraints.py"
)
PROJECT_CREATED_BY_MIGRATION_PATH = (
    BACKEND_ROOT
    / "alembic"
    / "versions"
    / "20260609_0005_add_project_created_by.py"
)
USER_PASSWORD_FLAG_MIGRATION_PATH = (
    BACKEND_ROOT
    / "alembic"
    / "versions"
    / "20260615_0004_add_user_password_must_change.py"
)
SCHEMA_SQL_PATH = BACKEND_ROOT / "sql" / "schema" / "001_create_core_tables.sql"


class _ScalarOneResult:
    def __init__(self, value: int):
        self._value = value

    def scalar_one(self) -> int:
        return self._value


class _ScalarResult:
    def __init__(self, value: int | None):
        self._value = value

    def scalar(self) -> int | None:
        return self._value


class _FakeBind:
    def __init__(self, *, existing_project_count: int, admin_id: int | None):
        self._existing_project_count = existing_project_count
        self._admin_id = admin_id
        self.executed: list[tuple[str, dict | None]] = []

    def execute(self, statement, params: dict | None = None):
        sql = str(statement)
        self.executed.append((sql, params))
        if "SELECT COUNT(*) FROM projects WHERE created_by IS NULL" in sql:
            return _ScalarOneResult(self._existing_project_count)
        if "SELECT id FROM users WHERE username = :admin_username LIMIT 1" in sql:
            return _ScalarResult(self._admin_id)
        if "UPDATE projects SET created_by = :admin_id WHERE created_by IS NULL" in sql:
            return None
        raise AssertionError(f"Unexpected SQL executed: {sql}")


class _FakeOp:
    def __init__(self, bind: _FakeBind):
        self._bind = bind
        self.calls: list[tuple[str, object]] = []

    def add_column(self, table_name: str, column) -> None:
        self.calls.append(("add_column", table_name, column.name, column.nullable))

    def get_bind(self) -> _FakeBind:
        return self._bind

    def create_foreign_key(
        self,
        constraint_name: str,
        source_table: str,
        referent_table: str,
        local_cols: list[str],
        remote_cols: list[str],
    ) -> None:
        self.calls.append(
            (
                "create_foreign_key",
                constraint_name,
                source_table,
                referent_table,
                tuple(local_cols),
                tuple(remote_cols),
            )
        )

    def alter_column(self, table_name: str, column_name: str, **kwargs) -> None:
        self.calls.append(("alter_column", table_name, column_name, kwargs))


def _load_migration_module(path: Path, module_name: str) -> ModuleType:
    spec = spec_from_file_location(module_name, path)
    assert spec is not None and spec.loader is not None
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_m2_models_register_expected_table_count() -> None:
    assert len(Base.metadata.tables) == 16


def test_initial_migration_is_static_snapshot() -> None:
    source = MIGRATION_PATH.read_text(encoding="utf-8")

    assert "Base.metadata" not in source
    assert "import app.db.models" not in source
    assert "op.create_table(" in source


def test_builtin_role_seed_uses_documented_capabilities() -> None:
    sources = [
        MIGRATION_PATH.read_text(encoding="utf-8"),
        SCHEMA_SQL_PATH.read_text(encoding="utf-8"),
    ]
    legacy_capability_markers = [
        "system.admin",
        "project.read",
        "annotation.write",
        "export.create",
        "role.bind",
        "member.manage",
    ]
    required_capability_markers = [
        "can_view_project",
        "can_create_annotation_revision",
        "can_submit_revision",
        "can_review_revision",
        "can_manage_project_members",
        "can_create_export_job",
        "can_download_export",
        "can_lock_revision",
        "can_unlock_revision",
        "can_rollback_revision",
        "can_view_audit_log",
        "can_manage_system_users",
    ]

    for source in sources:
        for marker in legacy_capability_markers:
            assert marker not in source
        for marker in required_capability_markers:
            assert marker in source


def test_role_capability_data_migration_updates_existing_databases() -> None:
    source = ROLE_MIGRATION_PATH.read_text(encoding="utf-8")

    assert 'revision: str = "20260603_0002"' in source
    assert 'down_revision: str | None = "20260603_0001"' in source
    assert "UPDATE role_registry" in source
    assert "can_upload_assets" in source
    assert "project.read" in source


def test_post_m2_migration_file_metadata_uses_linear_revision_chain() -> None:
    seed_source = SEED_ADMIN_MIGRATION_PATH.read_text(encoding="utf-8")
    relax_source = RELAX_ANNOTATION_OBJECTS_MIGRATION_PATH.read_text(encoding="utf-8")
    created_by_source = PROJECT_CREATED_BY_MIGRATION_PATH.read_text(encoding="utf-8")
    password_flag_source = USER_PASSWORD_FLAG_MIGRATION_PATH.read_text(encoding="utf-8")

    assert 'revision: str = "20260608_0003"' in seed_source
    assert 'down_revision: str | None = "20260603_0002"' in seed_source
    assert 'revision: str = "20260608_0004"' in relax_source
    assert 'down_revision: str | None = "20260608_0003"' in relax_source
    assert 'revision: str = "20260609_0005"' in created_by_source
    assert 'down_revision: str | None = "20260608_0004"' in created_by_source
    assert 'revision: str = "20260615_0004"' in password_flag_source
    assert 'down_revision: str | None = "20260609_0005"' in password_flag_source


def test_post_m2_migrations_have_single_head_and_expected_order() -> None:
    config = Config()
    config.set_main_option("script_location", str(ALEMBIC_ROOT))
    script = ScriptDirectory.from_config(config)

    assert script.get_heads() == ["20260619_0006"]
    assert script.get_revision("20260608_0003").down_revision == "20260603_0002"
    assert script.get_revision("20260608_0004").down_revision == "20260608_0003"
    assert script.get_revision("20260609_0005").down_revision == "20260608_0004"
    assert script.get_revision("20260615_0004").down_revision == "20260609_0005"
    assert script.get_revision("20260619_0006").down_revision == "20260615_0004"


def test_project_created_by_migration_avoids_hard_coded_admin_id() -> None:
    source = PROJECT_CREATED_BY_MIGRATION_PATH.read_text(encoding="utf-8")

    assert "WHERE username = :admin_username" in source
    assert "UPDATE projects SET created_by = :admin_id" in source
    assert "created_by = 1" not in source


def test_project_created_by_migration_backfills_existing_projects_with_admin_user(
    monkeypatch,
) -> None:
    migration = _load_migration_module(
        PROJECT_CREATED_BY_MIGRATION_PATH,
        "migration_20260609_0005_success",
    )
    bind = _FakeBind(existing_project_count=2, admin_id=7)
    fake_op = _FakeOp(bind)
    monkeypatch.setattr(migration, "op", fake_op)
    monkeypatch.setattr(migration, "_load_env_file", lambda: None)
    monkeypatch.setenv("SEED_ADMIN_USERNAME", "seed-admin")

    migration.upgrade()

    assert (
        "UPDATE projects SET created_by = :admin_id WHERE created_by IS NULL",
        {"admin_id": 7},
    ) in bind.executed
    assert ("add_column", "projects", "created_by", True) in fake_op.calls
    assert (
        "create_foreign_key",
        "fk_projects_created_by",
        "projects",
        "users",
        ("created_by",),
        ("id",),
    ) in fake_op.calls
    assert (
        "alter_column",
        "projects",
        "created_by",
        {"nullable": False},
    ) in fake_op.calls


def test_project_created_by_migration_fails_when_admin_user_missing(
    monkeypatch,
) -> None:
    migration = _load_migration_module(
        PROJECT_CREATED_BY_MIGRATION_PATH,
        "migration_20260609_0005_missing_admin",
    )
    bind = _FakeBind(existing_project_count=1, admin_id=None)
    fake_op = _FakeOp(bind)
    monkeypatch.setattr(migration, "op", fake_op)
    monkeypatch.setattr(migration, "_load_env_file", lambda: None)
    monkeypatch.setenv("SEED_ADMIN_USERNAME", "seed-admin")

    try:
        migration.upgrade()
    except RuntimeError as exc:
        assert "requires an existing admin user" in str(exc)
    else:
        raise AssertionError("Expected RuntimeError when admin user is missing")


def test_user_password_must_change_migration_adds_explicit_first_login_flag() -> None:
    source = USER_PASSWORD_FLAG_MIGRATION_PATH.read_text(encoding="utf-8")

    assert 'revision: str = "20260615_0004"' in source
    assert 'down_revision: str | None = "20260609_0005"' in source
    assert '"users"' in source
    assert '"password_must_change"' in source
    assert "server_default=sa.text(\"true\")" in source
