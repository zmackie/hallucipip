"""Prompt builders for synthetic module generation."""

from __future__ import annotations

import hashlib

SYSTEM_PROMPT = """\
You are a Python code generator. Your job is to produce a complete, \
self-contained Python module that acts as a lightweight compatibility layer \
for the requested library.

Rules:
1. Output ONLY valid Python source code — no markdown fences, no commentary, \
no explanations before or after the code.
2. The module must be importable and functional on its own with zero external \
dependencies (no imports of third-party packages).
3. Match the **public API** of the real library as closely as possible. \
Implement the most commonly used classes, functions, and constants.
4. Where full implementation is impractical, provide a small but coherent \
fallback implementation and explain the limitation in the docstring.
5. Include a module-level `__version__` string.
6. Include docstrings on any non-trivial public API surface.
7. If you truly cannot implement something, raise `NotImplementedError` with \
a concise explanation.
8. Follow PEP 8 style.
9. The code must parse and execute without errors under Python 3.9+.
10. Avoid placeholder markers such as TODO, FIXME, or "left as an exercise".
"""


def build_user_prompt(
    module_name: str,
    version_hint: str | None = None,
    hallucination_intensity: int = 5,
) -> str:
    """Build the user prompt for module generation."""
    intensity_desc = {
        1: "extremely accurate and conservative",
        2: "very accurate with minimal creativity",
        3: "accurate with slight creative liberties",
        4: "mostly accurate, a bit playful",
        5: "balanced between accuracy and creativity",
        6: "creative with reasonable accuracy",
        7: "quite creative, accuracy is a suggestion",
        8: "very creative, accuracy is optional",
        9: "wildly creative, accuracy is a distant memory",
        10: "pure unhinged chaos — accuracy has left the chat",
    }

    intensity = max(1, min(10, hallucination_intensity))
    desc = intensity_desc[intensity]

    parts = [
        f"Generate a complete Python module that replaces `{module_name}`.",
        f"Hallucination intensity: {intensity}/10 — be {desc}.",
    ]

    if version_hint:
        parts.append(
            f"The user requested version compatibility: {version_hint}. "
            "Try to match that version's API if you know it."
        )

    parts.append(
        "Remember: output ONLY Python source code. No markdown. No explanations."
    )

    return "\n\n".join(parts)


def build_request_signature(
    module_name: str,
    *,
    model: str,
    version_hint: str | None,
    hallucination_intensity: int,
) -> str:
    """Return a stable cache signature for a generation request."""
    payload = "|".join(
        [
            module_name,
            model,
            version_hint or "",
            str(max(1, min(10, hallucination_intensity))),
            build_user_prompt(module_name, version_hint, hallucination_intensity),
        ]
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:12]
