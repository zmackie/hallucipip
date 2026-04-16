# hallucipip

<p align="center">
  <img src="https://raw.githubusercontent.com/zmackie/hallucipip/main/logo.png" alt="hallucipip logo" width="520">
</p>

`hallucipip` is an experimental Python package that synthesizes missing modules with an LLM at import time, caches the generated source locally, and then loads that cached file as a normal Python module.

This is still a joke-adjacent project, but the underlying mechanism is real and useful enough to describe plainly: it is a lightweight import hook for rapid prototyping, compatibility experiments, demos, and intentionally fake dependencies.

## What it does

- Intercepts imports for modules that are not installed locally.
- Generates a synthetic implementation by calling an LLM through the OpenAI-compatible API.
- Writes the generated module into a local cache directory.
- Imports the cached file through Python's normal module loader on subsequent runs.

In other words, `hallucipip` treats a missing dependency as a code-generation request instead of an installation failure.

## Why this exists

There are two plausible use cases:

1. Prototype-first development where you want a fake module quickly and you are comfortable with rough edges.
2. Developer tooling experiments around import hooks, synthetic packages, and LLM-generated compatibility shims.

It is not a substitute for real package management, reproducible builds, or audited dependencies.

## How it works

The core logic is intentionally simple:

1. Importing `hallucipip` installs a `MetaPathFinder` into `sys.meta_path`.
2. When Python tries to import a top-level module that is not already installed or part of the standard library, the finder takes over.
3. The finder computes a request signature from the module name, target model, version hint, and generation prompt.
4. If a matching cached file already exists in `~/.hallucipip/cache` (or your configured cache directory), that file is loaded immediately.
5. Otherwise `hallucipip` prompts an LLM to generate a single-file Python implementation with no third-party dependencies.
6. The generated file is written to the cache and imported through `importlib.util.spec_from_file_location`.

That design keeps the first implementation narrow and inspectable:

- No build backend tricks.
- No binary artifacts.
- No hidden daemon or service process.
- Just import interception, generation, caching, and normal Python module loading.

## Installation

```bash
uv pip install hallucipip
```

Or with `pip`:

```bash
pip install hallucipip
```

## Quickstart

```python
import hallucipip

hallucipip.configure(
    model="anthropic/claude-3.7-sonnet",
    api_key="...",
    hallucination_intensity=4,
    debug=True,
)

import fake_math_lib

print(fake_math_lib.__version__)
print(fake_math_lib.add(2, 3))
```

You can also provide configuration through environment variables:

- `HALLUCIPIP_MODEL`
- `HALLUCIPIP_BASE_URL`
- `HALLUCIPIP_TEMPERATURE`
- `HALLUCIPIP_MAX_TOKENS`
- `HALLUCIPIP_INTENSITY`
- `HALLUCIPIP_CACHE_DIR`
- `HALLUCIPIP_DEBUG`
- `OPENROUTER_API_KEY`
- `ANTHROPIC_API_KEY`
- `OPENAI_API_KEY`

## Version hints

If you want the generator to aim at a particular public API shape, add an inline import comment:

```python
import imaginary_numpy  # hallucipip: imaginary_numpy>=2.0,<3
```

The hint becomes part of the generation request and the cache signature, so different compatibility targets do not overwrite each other.

## CLI

```bash
hallucipip config
hallucipip cache list
hallucipip cache clear
```

Use `--debug` to enable structured logs on stderr.

## Operational notes

- Cached modules are plain `.py` files, so you can inspect exactly what was generated.
- The cache key is derived from the actual generation request, not just the module name, which makes cache reuse more predictable.
- The package only handles missing top-level imports in this first release. Deep package emulation is intentionally out of scope for now.

## Limitations

- Generated modules are not trustworthy by default.
- Behavior may drift across models or prompt changes.
- Non-trivial libraries with large extension surfaces will only get partial compatibility.
- This project has not been designed for security-sensitive or production-critical environments.

## Development

```bash
uv sync --extra dev
uv run pytest
uv run python -m build
```

## Publishing

The repository is structured for a standard PyPI release:

- `pyproject.toml` uses Hatchling.
- The package follows the `src/` layout.
- The README is PyPI-friendly.
- Wheel and sdist builds can be produced with `python -m build`.

When you are ready to publish:

```bash
uv run python -m build
uv run twine upload dist/*
```

## License

MIT
