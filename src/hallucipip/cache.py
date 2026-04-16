"""Cache management for hallucinated modules.

Stores generated code in ~/.hallucipip/cache/ so you only pay the LLM toll once.
"""

from __future__ import annotations

import logging
import shutil
from pathlib import Path

log = logging.getLogger("hallucipip")

DEFAULT_CACHE_DIR = Path.home() / ".hallucipip" / "cache"


def _cache_path(module_name: str, signature: str, cache_dir: Path) -> Path:
    return cache_dir / f"{module_name}_{signature}.py"


def get(module_name: str, signature: str, cache_dir: Path | None = None) -> Path | None:
    """Return cached module path if it exists, else None."""
    cache_dir = cache_dir or DEFAULT_CACHE_DIR
    path = _cache_path(module_name, signature, cache_dir)
    if path.exists():
        log.debug(
            "Cache hit",
            extra={"event_data": {"module": module_name, "path": str(path)}},
        )
        return path
    log.debug("Cache miss", extra={"event_data": {"module": module_name}})
    return None


def put(
    module_name: str, signature: str, code: str, cache_dir: Path | None = None
) -> Path:
    """Write generated code to the cache. Returns the file path."""
    cache_dir = cache_dir or DEFAULT_CACHE_DIR
    cache_dir.mkdir(parents=True, exist_ok=True)
    path = _cache_path(module_name, signature, cache_dir)
    path.write_text(code, encoding="utf-8")
    log.debug(
        "Cached module",
        extra={"event_data": {"module": module_name, "path": str(path), "bytes": len(code)}},
    )
    return path


def list_cached(cache_dir: Path | None = None) -> list[Path]:
    """List all cached module files."""
    cache_dir = cache_dir or DEFAULT_CACHE_DIR
    if not cache_dir.exists():
        return []
    return sorted(cache_dir.glob("*.py"))


def clear(cache_dir: Path | None = None) -> int:
    """Delete all cached modules. Returns the number of files removed."""
    cache_dir = cache_dir or DEFAULT_CACHE_DIR
    if not cache_dir.exists():
        return 0
    files = list(cache_dir.glob("*.py"))
    count = len(files)
    shutil.rmtree(cache_dir)
    log.debug("Cleared cache", extra={"event_data": {"count": count}})
    return count
