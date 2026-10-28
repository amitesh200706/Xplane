"""Folder wrapper — lets the app directory act as a layer over a target folder."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


CONFIG_NAME = "wrapper.json"


@dataclass
class WrapperConfig:
    target_folder: str
    set_at: str


def app_dir() -> Path:
    return Path(__file__).resolve().parent


def config_path(base: Path | None = None) -> Path:
    return (base or app_dir()) / CONFIG_NAME


def get_wrapper(base: Path | None = None) -> Path | None:
    path = config_path(base)
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        target = Path(data["target_folder"]).resolve()
        if target.is_dir():
            return target
    except (json.JSONDecodeError, KeyError, OSError):
        pass
    return None


def set_wrapper(target: Path, base: Path | None = None) -> WrapperConfig:
    target = target.resolve()
    if not target.is_dir():
        raise NotADirectoryError(f"Not a directory: {target}")

    config = WrapperConfig(
        target_folder=str(target),
        set_at=datetime.now(tz=timezone.utc).isoformat(),
    )
    config_path(base).write_text(
        json.dumps(config.__dict__, indent=2),
        encoding="utf-8",
    )
    return config


def clear_wrapper(base: Path | None = None) -> None:
    path = config_path(base)
    if path.is_file():
        path.unlink()


def resolve_file(path: str | Path, base: Path | None = None) -> Path:
    candidate = Path(path)
    if candidate.is_absolute():
        resolved = candidate.resolve()
    else:
        wrapper = get_wrapper(base)
        if wrapper:
            resolved = (wrapper / candidate).resolve()
        else:
            resolved = (Path.cwd() / candidate).resolve()

    if not resolved.is_file():
        raise FileNotFoundError(f"Not a file: {resolved}")
    return resolved


def is_under_wrapper(file_path: Path, wrapper: Path) -> bool:
    try:
        file_path.resolve().relative_to(wrapper.resolve())
        return True
    except ValueError:
        return False


def list_wrapper_files(base: Path | None = None) -> list[tuple[str, Path]]:
    wrapper = get_wrapper(base)
    if not wrapper:
        return []

    results: list[tuple[str, Path]] = []
    for root, _dirs, filenames in os.walk(wrapper):
        root_path = Path(root)
        for name in sorted(filenames, key=str.lower):
            full = root_path / name
            rel = full.relative_to(wrapper).as_posix()
            if rel != CONFIG_NAME and not rel.endswith(f"/{CONFIG_NAME}"):
                results.append((rel, full))
    return results
