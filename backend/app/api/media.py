"""Helpers for exposing generated media safely through the API."""
from __future__ import annotations

from pathlib import Path


def public_media_url(path: str | None, *, storage_dir: str) -> str | None:
    """Convert a local storage path to a browser-usable ``/storage/...`` URL.

    Keeps already-public URLs unchanged. This lets the Runway pipeline persist
    local files while dashboard/landing clients receive stable HTTP paths.
    """
    if not path:
        return None
    if path.startswith(("http://", "https://", "/storage/")):
        return path

    try:
        media_path = Path(path).resolve()
        storage_path = Path(storage_dir).resolve()
        rel = media_path.relative_to(storage_path)
    except (OSError, ValueError):
        return path

    return f"/storage/{rel.as_posix()}"
