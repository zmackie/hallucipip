"""hallucipip demo — watch modules get hallucinated into existence.

Usage:
    OPENROUTER_API_KEY=sk-or-... uv run python demo.py

Optional env vars:
    HALLUCIPIP_MODEL          — default: anthropic/claude-3.7-sonnet
    HALLUCIPIP_INTENSITY      — 1 (boring) to 10 (unhinged), default: 7
"""

import sys


def main():
    import hallucipip

    hallucipip.configure(
        model="nvidia/nemotron-3-super-120b-a12b:free",
        hallucination_intensity=7,
        debug="--debug" in sys.argv,
    )

    if not hallucipip._config["api_key"]:
        print("ERROR: Set OPENROUTER_API_KEY to run this demo.")
        print("  e.g.:  OPENROUTER_API_KEY=sk-or-... uv run python demo.py")
        sys.exit(1)

    print("=" * 60)
    print("  hallucipip demo — dreaming up dependencies")
    print("=" * 60)
    print()

    # --- 1. Import a fake library ---
    print("[1/3] Importing 'fake_math_lib'...")
    import fake_math_lib

    print(f"  Module: {fake_math_lib}")
    print(f"  Version: {getattr(fake_math_lib, '__version__', 'unknown')}")

    # Try calling something on it
    for attr in ("add", "multiply", "sqrt", "pi", "e"):
        if hasattr(fake_math_lib, attr):
            val = getattr(fake_math_lib, attr)
            if callable(val):
                try:
                    result = val(3, 4) if attr in ("add", "multiply") else val(16) if attr == "sqrt" else None
                    print(f"  {attr}(...) = {result}")
                except Exception as exc:
                    print(f"  {attr}(...) raised: {exc}")
            else:
                print(f"  {attr} = {val}")

    print()

    # --- 2. Import it again (should be instant from cache) ---
    print("[2/3] Importing 'fake_math_lib' again (should be cached)...")
    import importlib
    importlib.invalidate_caches()
    # Force re-resolve from cache
    del sys.modules["fake_math_lib"]
    import fake_math_lib as fml2  # noqa: F811

    print(f"  Cached module: {fml2}")
    print()

    # --- 3. Import something more ambitious ---
    print("[3/3] Importing 'fake_web_framework'...")
    import fake_web_framework

    print(f"  Module: {fake_web_framework}")
    print(f"  Version: {getattr(fake_web_framework, '__version__', 'unknown')}")

    for attr in dir(fake_web_framework):
        if not attr.startswith("_"):
            print(f"  .{attr} = {getattr(fake_web_framework, attr)!r:.80}")

    print()
    print("=" * 60)
    print("  Done! Run 'hallucipip cache list' to see cached modules.")
    print("=" * 60)


if __name__ == "__main__":
    main()
