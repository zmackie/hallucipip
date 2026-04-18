"""hallucipip — dependencies that hallucinate themselves into existence.

Just `import hallucipip` and then import whatever you want.
The LLM will dream it up for you.
"""

from __future__ import annotations

import logging
import os
import sys
from typing import Any

__version__ = "0.2.0"

log = logging.getLogger("hallucipip")


class _StructuredFormatter(logging.Formatter):
    """Minimal structured formatter that stays dependency-free."""

    def format(self, record: logging.LogRecord) -> str:
        fields = {
            "logger": record.name,
            "level": record.levelname,
            "message": record.getMessage(),
        }
        extras = getattr(record, "event_data", None)
        if isinstance(extras, dict):
            fields.update(extras)
        return " ".join(f"{key}={value!r}" for key, value in fields.items())

# Global configuration — mutated by configure(), read by finder/generator
_config: dict = {
    "model": os.environ.get("HALLUCIPIP_MODEL", "anthropic/claude-3.7-sonnet"),
    "api_key": os.environ.get(
        "OPENROUTER_API_KEY",
        os.environ.get("ANTHROPIC_API_KEY", os.environ.get("OPENAI_API_KEY", "")),
    ),
    "base_url": os.environ.get("HALLUCIPIP_BASE_URL", "https://openrouter.ai/api/v1"),
    "temperature": float(os.environ.get("HALLUCIPIP_TEMPERATURE", "0.7")),
    "max_tokens": int(os.environ.get("HALLUCIPIP_MAX_TOKENS", "8000")),
    "hallucination_intensity": int(os.environ.get("HALLUCIPIP_INTENSITY", "5")),
    "cache_dir": os.environ.get("HALLUCIPIP_CACHE_DIR", "~/.hallucipip/cache"),
    "debug": os.environ.get("HALLUCIPIP_DEBUG", "").lower() in ("1", "true", "yes"),
}


def _configure_logging(debug: bool) -> None:
    logger = logging.getLogger("hallucipip")
    logger.handlers.clear()

    handler = logging.StreamHandler()
    handler.setFormatter(_StructuredFormatter())
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG if debug else logging.INFO)
    logger.propagate = False


if _config["debug"]:
    _configure_logging(True)


def configure(
    *,
    model: str | None = None,
    api_key: str | None = None,
    base_url: str | None = None,
    temperature: float | None = None,
    max_tokens: int | None = None,
    hallucination_intensity: int | None = None,
    cache_dir: str | None = None,
    debug: bool | None = None,
) -> None:
    """Configure hallucipip. Call this before importing hallucinated modules.

    All parameters are optional — anything you don't pass keeps its current
    value (from env vars or previous configure() calls).
    """
    if model is not None:
        _config["model"] = model
    if api_key is not None:
        _config["api_key"] = api_key
    if base_url is not None:
        _config["base_url"] = base_url
    if temperature is not None:
        _config["temperature"] = temperature
    if max_tokens is not None:
        _config["max_tokens"] = max_tokens
    if hallucination_intensity is not None:
        _config["hallucination_intensity"] = max(1, min(10, hallucination_intensity))
    if cache_dir is not None:
        _config["cache_dir"] = cache_dir
    if debug is not None:
        _config["debug"] = debug
        _configure_logging(debug)


def get_config() -> dict[str, Any]:
    """Return a shallow copy of the active configuration."""
    return _config.copy()


def _install_hook() -> None:
    """Insert our finder into sys.meta_path if it's not already there."""
    # Pre-import the entire LLM dependency chain BEFORE the hook is active.
    # openai lazily imports httpcore, so we force the full chain here to
    # ensure httpcore's optional deps (trio, h2, socksio) resolve through the
    # normal import system and don't get intercepted by our hook.
    import httpcore  # noqa: F401
    import httpx  # noqa: F401
    import openai  # noqa: F401

    from hallucipip.finder import HallucipipFinder

    if not any(isinstance(f, HallucipipFinder) for f in sys.meta_path):
        sys.meta_path.append(HallucipipFinder())
        log.debug(
            "Import hook installed",
            extra={"event_data": {"component": "finder", "action": "install"}},
        )


# Auto-install the hook when hallucipip is imported
_install_hook()
