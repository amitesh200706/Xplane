"""Load file content for in-app preview."""

from __future__ import annotations

from pathlib import Path

from app.cache_manager import format_bytes

PREVIEW_LIMIT = 512 * 1024


def load_file_preview(path: Path, limit: int = PREVIEW_LIMIT) -> str:
    path = path.resolve()
    if not path.is_file():
        raise FileNotFoundError(f"Not a file: {path}")

    size = path.stat().st_size
    with path.open("rb") as f:
        data = f.read(limit + 1)

    truncated = len(data) > limit
    if truncated:
        data = data[:limit]

    if b"\x00" in data[:8192]:
        return (
            f"Binary file — {format_bytes(size)}\n\n"
            "This file cannot be previewed in the app. "
            "Use Cache File to save a copy, or Open Externally."
        )

    for encoding in ("utf-8", "utf-8-sig", "latin-1"):
        try:
            text = data.decode(encoding)
            break
        except UnicodeDecodeError:
            continue
    else:
        return (
            f"Binary file — {format_bytes(size)}\n\n"
            "This file cannot be previewed in the app."
        )

    header = f"{path.name} — {format_bytes(size)}\n{'─' * 40}\n"
    if truncated:
        header = (
            f"{path.name} — {format_bytes(size)} "
            f"(showing first {format_bytes(limit)})\n{'─' * 40}\n"
        )
    return header + text
