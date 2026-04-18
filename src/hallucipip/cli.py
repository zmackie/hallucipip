"""CLI for managing your hallucinated dependencies.

Stdlib-only on purpose: hallucipip ships with exactly one real dependency
(an LLM client), so the CLI has to make do with argparse and print().
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from hallucipip import _config, __version__, configure
from hallucipip.cache import clear as cache_clear
from hallucipip.cache import list_cached


def _cmd_cache_list(_args: argparse.Namespace) -> int:
    cache_dir = Path(_config["cache_dir"]).expanduser()
    files = list_cached(cache_dir)
    if not files:
        print("No cached modules. The void is empty.")
        return 0

    rows = [(f.stem.rsplit("_", 1)[0], f.stat().st_size, str(f)) for f in files]
    name_w = max(len("Module"), max(len(r[0]) for r in rows))
    size_w = max(len("Size"), max(len(f"{r[1]:,} B") for r in rows))

    print(f"{'Module'.ljust(name_w)}  {'Size'.rjust(size_w)}  Path")
    print(f"{'-' * name_w}  {'-' * size_w}  {'-' * 4}")
    for name, size, path in rows:
        print(f"{name.ljust(name_w)}  {f'{size:,} B'.rjust(size_w)}  {path}")
    return 0


def _cmd_cache_clear(_args: argparse.Namespace) -> int:
    cache_dir = Path(_config["cache_dir"]).expanduser()
    count = cache_clear(cache_dir)
    if count:
        print(f"Purged {count} hallucination(s) from the cache.")
    else:
        print("Cache was already empty. Nothing to forget.")
    return 0


def _cmd_config(_args: argparse.Namespace) -> int:
    print("hallucipip configuration")
    print("-" * 32)
    for key, value in _config.items():
        display = str(value)
        if key == "api_key" and value:
            display = value[:8] + "..." + value[-4:] if len(value) > 12 else "***"
        print(f"  {key:<25} {display}")
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="hallucipip",
        description="hallucipip — dependencies that hallucinate themselves into existence.",
    )
    parser.add_argument("--version", action="version", version=f"hallucipip {__version__}")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging.")

    sub = parser.add_subparsers(dest="command", required=True)

    cache_parser = sub.add_parser("cache", help="Manage the hallucination cache.")
    cache_sub = cache_parser.add_subparsers(dest="cache_command", required=True)

    list_parser = cache_sub.add_parser("list", help="List all cached hallucinated modules.")
    list_parser.set_defaults(func=_cmd_cache_list)

    clear_parser = cache_sub.add_parser(
        "clear", help="Wipe all cached modules. They'll be re-hallucinated on next import."
    )
    clear_parser.set_defaults(func=_cmd_cache_clear)

    config_parser = sub.add_parser("config", help="Show current hallucipip configuration.")
    config_parser.set_defaults(func=_cmd_config)

    return parser


def cli(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.debug:
        configure(debug=True)

    return args.func(args)


def main() -> None:
    sys.exit(cli())


if __name__ == "__main__":
    main()
