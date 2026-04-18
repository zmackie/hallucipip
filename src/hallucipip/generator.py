"""The dream factory — calls an LLM to hallucinate module source code."""

from __future__ import annotations

import itertools
import logging
import re
import sys
import threading
import time

from hallucipip.prompts import SYSTEM_PROMPT, build_user_prompt

log = logging.getLogger("hallucipip")


def _strip_markdown_fences(text: str) -> str:
    """Remove ```python ... ``` wrappers if the LLM ignored our instructions."""
    pattern = r"^```(?:python)?\s*\n(.*?)```\s*$"
    match = re.match(pattern, text.strip(), re.DOTALL)
    if match:
        return match.group(1).strip()
    return text.strip()


class _StderrSpinner:
    """Tiny stdlib-only spinner that writes to stderr while work is happening."""

    _FRAMES = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"

    def __init__(self, text: str) -> None:
        self._text = text
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._enabled = sys.stderr.isatty()

    def __enter__(self) -> "_StderrSpinner":
        if self._enabled:
            self._thread = threading.Thread(target=self._run, daemon=True)
            self._thread.start()
        else:
            print(self._text, file=sys.stderr, flush=True)
        return self

    def __exit__(self, _exc_type, _exc, _tb) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=0.5)
        if self._enabled:
            sys.stderr.write("\r\x1b[2K")
            sys.stderr.flush()

    def _run(self) -> None:
        for frame in itertools.cycle(self._FRAMES):
            if self._stop.is_set():
                return
            sys.stderr.write(f"\r{frame} {self._text}")
            sys.stderr.flush()
            time.sleep(0.08)


def generate_module(
    module_name: str,
    *,
    model: str,
    api_key: str,
    base_url: str,
    temperature: float,
    max_tokens: int,
    hallucination_intensity: int,
    version_hint: str | None = None,
) -> str:
    """Call the LLM and return generated Python source code."""
    if not api_key:
        raise RuntimeError(
            "No API key configured. Set OPENROUTER_API_KEY, ANTHROPIC_API_KEY, "
            "OPENAI_API_KEY, or pass api_key=... to hallucipip.configure()."
        )

    # Lazy import — loading openai triggers httpcore, which probes optional
    # deps (trio, h2, socksio). Doing it here keeps the import-time surface of
    # hallucipip itself minimal.
    from openai import OpenAI

    client = OpenAI(api_key=api_key, base_url=base_url)

    user_prompt = build_user_prompt(module_name, version_hint, hallucination_intensity)

    log.debug(
        "Generating module",
        extra={
            "event_data": {
                "module": module_name,
                "model": model,
                "temperature": temperature,
                "max_tokens": max_tokens,
            }
        },
    )

    with _StderrSpinner(f"Hallucinating {module_name}..."):
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
        )

    code = response.choices[0].message.content or ""
    code = _strip_markdown_fences(code)

    if not code:
        raise RuntimeError(
            f"The LLM returned an empty response for '{module_name}'. "
            "It seems even AI doesn't want to implement this one."
        )

    log.debug(
        "Generated module",
        extra={"event_data": {"module": module_name, "bytes": len(code)}},
    )
    return code
