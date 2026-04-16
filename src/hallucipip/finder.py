"""The import hook that makes the impossible merely improbable."""

from __future__ import annotations

import importlib
import importlib.abc
import importlib.machinery
import importlib.util
import inspect
import logging
import re
import sys
from pathlib import Path

from hallucipip import _config
from hallucipip.cache import get as cache_get, put as cache_put
from hallucipip.generator import generate_module
from hallucipip.prompts import build_request_signature

log = logging.getLogger("hallucipip")

# Modules we should never try to hallucinate
_SKIP_PREFIXES = (
    "hallucipip",
    "_",
    "encodings",
    "codecs",
    "io",
    "abc",
    "os",
    "sys",
    "builtins",
    "importlib",
    "types",
    "warnings",
    "contextlib",
    "functools",
    "operator",
    "keyword",
    "signal",
    "errno",
    "stat",
    "posixpath",
    "genericpath",
    "posix",
    "nt",
    "ntpath",
    "zipimport",
    "marshal",
)


def _is_stdlib_or_installed(module_name: str) -> bool:
    """Check if a module is part of stdlib or already installed."""
    if module_name in sys.modules:
        return True

    # Check if importlib can find a spec via the normal machinery.
    # We temporarily remove ourselves from sys.meta_path to avoid recursion.
    our_finders = [f for f in sys.meta_path if isinstance(f, HallucipipFinder)]
    for f in our_finders:
        sys.meta_path.remove(f)
    try:
        spec = importlib.util.find_spec(module_name)
        return spec is not None
    except (ModuleNotFoundError, ValueError):
        return False
    finally:
        for f in our_finders:
            sys.meta_path.append(f)


def _extract_version_hint(module_name: str) -> str | None:
    """Try to find a `# hallucipip: numpy>=2.0` comment on the import line."""
    try:
        frame = inspect.stack()[3]  # caller of the import
        source_line = frame.code_context[0] if frame.code_context else ""
        match = re.search(
            rf"#\s*hallucipip:\s*{re.escape(module_name)}([^\n]*)", source_line
        )
        if match:
            return match.group(1).strip()
    except Exception:
        pass
    return None


class HallucipipFinder(importlib.abc.MetaPathFinder):
    """A MetaPathFinder that dreams modules into existence."""

    _active = False  # True while we're generating — disables the hook entirely

    def find_spec(self, fullname, path, target=None):
        # While generating, let everything through the normal import system.
        # This prevents circular imports when openai/httpcore/rich load their
        # own optional dependencies (trio, h2, socksio, etc.).
        if self._active:
            return None

        # Only handle top-level modules for now
        if "." in fullname:
            return None

        if fullname.startswith(_SKIP_PREFIXES):
            return None

        if _is_stdlib_or_installed(fullname):
            return None

        log.debug(
            "Intercepted missing import",
            extra={"event_data": {"module": fullname}},
        )

        config = _config.copy()
        model = config["model"]
        cache_dir = Path(config["cache_dir"]).expanduser()
        version_hint = _extract_version_hint(fullname)
        signature = build_request_signature(
            fullname,
            model=model,
            version_hint=version_hint,
            hallucination_intensity=config["hallucination_intensity"],
        )

        # Check cache first
        cached_path = cache_get(fullname, signature, cache_dir)
        if cached_path:
            return importlib.util.spec_from_file_location(
                fullname, cached_path
            )

        # Generate the module — disable the hook for the entire duration
        self._active = True
        try:
            code = generate_module(
                fullname,
                model=model,
                api_key=config["api_key"],
                base_url=config["base_url"],
                temperature=config["temperature"],
                max_tokens=config["max_tokens"],
                hallucination_intensity=config["hallucination_intensity"],
                version_hint=version_hint,
            )
        except Exception as exc:
            log.error(
                "Module generation failed",
                extra={"event_data": {"module": fullname, "error": str(exc)}},
            )
            return None
        finally:
            self._active = False

        # Cache and load
        cached_path = cache_put(fullname, signature, code, cache_dir)
        return importlib.util.spec_from_file_location(fullname, cached_path)
