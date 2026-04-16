"""The dream factory — calls an LLM to hallucinate module source code."""

from __future__ import annotations

import logging
import re

from hallucipip.prompts import SYSTEM_PROMPT, build_user_prompt

log = logging.getLogger("hallucipip")


def _strip_markdown_fences(text: str) -> str:
    """Remove ```python ... ``` wrappers if the LLM ignored our instructions."""
    pattern = r"^```(?:python)?\s*\n(.*?)```\s*$"
    match = re.match(pattern, text.strip(), re.DOTALL)
    if match:
        return match.group(1).strip()
    return text.strip()


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

    # Lazy imports — these must not be imported at hook-install time because
    # loading openai triggers httpcore which tries optional imports (trio, h2,
    # socksio) that would hit our hook before the HTTP stack is ready.
    from openai import OpenAI
    from rich.console import Console
    from rich.spinner import Spinner
    from rich.live import Live

    console = Console(stderr=True)
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

    with Live(
        Spinner("dots", text=f"[bold cyan]Hallucinating {module_name}...[/]"),
        console=console,
        transient=True,
    ):
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
