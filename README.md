# hallucipip

<p align="center">
  <img src="https://raw.githubusercontent.com/zmackie/hallucipip/main/logo.png" alt="hallucipip logo" width="520">
</p>

<p align="center"><em>Supply-chain security is hard. Have one dependency and hallucinate the rest.</em></p>

---

`hallucipip` ships with exactly **one** runtime dependency — an LLM client. Every other module you `import` is generated on demand by an LLM, written to disk as a plain `.py` file, and loaded through Python's normal import machinery.

It is a joke. The mechanism is real.

## The premise

Modern Python projects routinely pull in hundreds of transitive dependencies, any one of which can own your supply chain. `hallucipip` asks: what if you just didn't install them? What if, at import time, we generated the module ourselves?

Every hallucinated module is:

- Generated from a prompt, not fetched from PyPI.
- Cached locally as a plain Python file you can read.
- Uniquely yours — different API key, different model, different code.

The blast radius of a compromised dependency is zero, because the dependency does not exist.

The blast radius of a bad hallucination is, admittedly, non-zero.

## How it works

1. `import hallucipip` installs a `MetaPathFinder` into `sys.meta_path`.
2. When Python tries to import a top-level module that isn't stdlib and isn't installed, the finder takes over.
3. The finder computes a request signature from the module name, model, version hint, and prompt.
4. If a matching file exists in `~/.hallucipip/cache`, it's loaded immediately.
5. Otherwise an LLM is asked to produce a single-file implementation with no third-party imports, the result is written to the cache, and Python loads it normally.

The generated code is just a `.py` file. You can `cat` it. You can edit it. You can check it into version control if you hate yourself.

## Installation

```bash
uv pip install hallucipip
# or
pip install hallucipip
```

## Quickstart

```python
import hallucipip

hallucipip.configure(
    model="anthropic/claude-sonnet-4.5",
    api_key="...",            # or set OPENROUTER_API_KEY
    hallucination_intensity=4,
    debug=True,
)

import fake_math_lib          # does not exist on PyPI
print(fake_math_lib.__version__)
print(fake_math_lib.add(2, 3))
```

The first import takes an LLM call. Every subsequent import is a disk read.

## Configuration

All of these can be set as env vars or passed to `hallucipip.configure()`:

| Env var | Purpose | Default |
| --- | --- | --- |
| `HALLUCIPIP_MODEL` | Model slug | `anthropic/claude-3.7-sonnet` |
| `HALLUCIPIP_BASE_URL` | OpenAI-compatible endpoint | `https://openrouter.ai/api/v1` |
| `HALLUCIPIP_TEMPERATURE` | Sampling temperature | `0.7` |
| `HALLUCIPIP_MAX_TOKENS` | Generation cap | `8000` |
| `HALLUCIPIP_INTENSITY` | `1` (conservative) – `10` (unhinged) | `5` |
| `HALLUCIPIP_CACHE_DIR` | Where cached modules live | `~/.hallucipip/cache` |
| `HALLUCIPIP_DEBUG` | Verbose logging | `false` |
| `OPENROUTER_API_KEY` / `ANTHROPIC_API_KEY` / `OPENAI_API_KEY` | Whichever you have | — |

## Version hints

If you want the generator to aim at a particular public API shape, drop an inline comment:

```python
import imaginary_numpy  # hallucipip: imaginary_numpy>=2.0,<3
```

The hint becomes part of the generation request and the cache signature, so different compatibility targets don't overwrite each other.

## CLI

```bash
hallucipip config           # show active configuration
hallucipip cache list       # list cached hallucinations
hallucipip cache clear      # wipe cache — next import re-hallucinates
hallucipip --debug ...      # structured logs on stderr
```

## Dependencies

One. `openai` — used as a thin OpenAI-compatible HTTP client so you can point at OpenRouter, Anthropic, OpenAI, or your own endpoint. The CLI uses `argparse`. Pretty output uses `print`. There is no `rich`, no `click`, no `requests`, no `pydantic`.

If `openai` itself offends you philosophically, the joke lands harder.

## What this is not

- A substitute for real package management.
- A substitute for reproducible builds.
- A substitute for audited dependencies.
- Safe.
- Deterministic.
- A good idea.

It is a useful import hook for prototyping, demos, compatibility experiments, and the occasional cursed notebook.

## Limitations

- Generated code is not trustworthy by default. Read it before you trust it.
- Behavior drifts across models and prompts.
- Only top-level imports are handled right now. Deep package emulation is out of scope.
- Non-trivial libraries with large C-extension surfaces will only get partial compatibility.

## Development

```bash
uv sync --extra dev
uv run pytest
uv run python -m build
```

## Publishing

```bash
uv run python -m build
uv run twine upload dist/*
```

## License

MIT
