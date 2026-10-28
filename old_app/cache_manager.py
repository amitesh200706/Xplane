"""File cache manager — copies a single selected file into local cache."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import threading
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable


ProgressCallback = Callable[[str, int, int], None]


@dataclass
class CacheManifest:
    source_file: str
    file_name: str
    cached_at: str
    size: int
    modified: str
    sha256: str


def _app_data_dir() -> Path:
    base = os.environ.get("LOCALAPPDATA") or os.environ.get("HOME") or "."
    return Path(base) / "FolderCacheApp" / "caches"


def _file_key(source: Path) -> str:
    normalized = str(source.resolve()).lower()
    return hashlib.sha256(normalized.encode()).hexdigest()[:16]


def cache_dir_for(source: Path) -> Path:
    return _app_data_dir() / _file_key(source)


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def list_cached_files() -> list[dict]:
    root = _app_data_dir()
    if not root.exists():
        return []

    results = []
    for entry in sorted(root.iterdir()):
        manifest_path = entry / "manifest.json"
        if manifest_path.is_file():
            try:
                data = json.loads(manifest_path.read_text(encoding="utf-8"))
                if "source_file" in data:
                    results.append(data)
            except (json.JSONDecodeError, OSError):
                continue
    return results


def get_manifest(source: Path) -> CacheManifest | None:
    manifest_path = cache_dir_for(source) / "manifest.json"
    if not manifest_path.is_file():
        return None
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    return CacheManifest(
        source_file=data["source_file"],
        file_name=data["file_name"],
        cached_at=data["cached_at"],
        size=data["size"],
        modified=data["modified"],
        sha256=data["sha256"],
    )


def cache_file(
    source: Path,
    *,
    on_progress: ProgressCallback | None = None,
    cancel_event: threading.Event | None = None,
) -> CacheManifest:
    source = source.resolve()
    if not source.is_file():
        raise FileNotFoundError(f"Not a file: {source}")

    if cancel_event and cancel_event.is_set():
        raise InterruptedError("Caching cancelled")

    dest_root = cache_dir_for(source)
    if dest_root.exists():
        shutil.rmtree(dest_root)
    dest_root.mkdir(parents=True, exist_ok=True)

    if on_progress:
        on_progress(source.name, 0, 1)

    dest_file = dest_root / source.name
    shutil.copy2(source, dest_file)

    if cancel_event and cancel_event.is_set():
        shutil.rmtree(dest_root, ignore_errors=True)
        raise InterruptedError("Caching cancelled")

    stat = source.stat()
    manifest = CacheManifest(
        source_file=str(source),
        file_name=source.name,
        cached_at=datetime.now(tz=timezone.utc).isoformat(),
        size=stat.st_size,
        modified=datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
        sha256=_sha256_file(dest_file),
    )

    if on_progress:
        on_progress(source.name, 1, 1)

    manifest_path = dest_root / "manifest.json"
    manifest_path.write_text(json.dumps(manifest.__dict__, indent=2), encoding="utf-8")

    return manifest


def format_bytes(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024 or unit == "TB":
            return f"{n:.1f} {unit}" if unit != "B" else f"{n} {unit}"
        n /= 1024
    return f"{n:.1f} TB"
