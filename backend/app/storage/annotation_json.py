from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from app.core.config import get_settings
from app.storage.local import StorageError


@dataclass(frozen=True)
class StoredJsonAsset:
    public_id: str
    storage_path: str
    sha256: str
    size_bytes: int


class AnnotationJsonStorage:
    def __init__(self, storage_root: Path | None = None) -> None:
        settings = get_settings()
        self.storage_root = (
            (storage_root or settings.storage_root).expanduser().resolve()
        )
        self.storage_root.mkdir(parents=True, exist_ok=True)

    def write_revision_json(
        self,
        *,
        revision_public_id: str,
        annotation_json: dict[str, object],
    ) -> StoredJsonAsset:
        """写入不可变 revision JSON，路径只由后端生成的 revision_public_id 决定。"""

        content = json.dumps(
            annotation_json,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        sha256 = hashlib.sha256(content).hexdigest()
        relative_path = (
            PurePosixPath("annotations")
            / "revisions"
            / revision_public_id[:10]
            / f"{revision_public_id}.json"
        )
        target_path = self._controlled_path(relative_path)
        target_path.parent.mkdir(parents=True, exist_ok=True)
        if target_path.exists():
            raise StorageError("标注 revision JSON 已存在，拒绝覆盖历史版本。")

        temp_path = target_path.with_suffix(".tmp")
        if temp_path.exists():
            temp_path.unlink()
        try:
            temp_path.write_bytes(content)
            temp_path.rename(target_path)
        except Exception:
            temp_path.unlink(missing_ok=True)
            raise

        return StoredJsonAsset(
            public_id=f"asset_{revision_public_id}",
            storage_path=relative_path.as_posix(),
            sha256=sha256,
            size_bytes=len(content),
        )

    def read_revision_json(self, storage_path: str) -> dict[str, object]:
        target_path = self._controlled_path(PurePosixPath(storage_path))
        with target_path.open("rb") as input_file:
            decoded = json.loads(input_file.read().decode("utf-8"))
        if not isinstance(decoded, dict):
            raise StorageError("标注 revision JSON 顶层必须是对象。")
        return decoded

    def remove_revision_json(self, storage_path: str) -> None:
        """清理本次事务写入但数据库登记失败的 revision JSON。"""

        target_path = self._controlled_path(PurePosixPath(storage_path))
        target_path.unlink(missing_ok=True)

    def _controlled_path(self, relative_path: PurePosixPath) -> Path:
        if relative_path.is_absolute() or ".." in relative_path.parts:
            raise StorageError("标注存储路径必须是 STORAGE_ROOT 内的安全相对路径。")
        target_path = (self.storage_root / Path(*relative_path.parts)).resolve()
        try:
            target_path.relative_to(self.storage_root)
        except ValueError as exc:
            raise StorageError("标注存储路径超出 STORAGE_ROOT。") from exc
        return target_path
