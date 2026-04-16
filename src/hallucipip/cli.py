"""CLI for managing your hallucinated dependencies."""

from __future__ import annotations
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from hallucipip import _config, configure
from hallucipip.cache import list_cached, clear as cache_clear

console = Console()


@click.group()
@click.option("--debug", is_flag=True, envvar="HALLUCIPIP_DEBUG", help="Enable debug logging.")
def cli(debug: bool):
    """hallucipip — dependencies that hallucinate themselves into existence."""
    if debug:
        configure(debug=True)


@cli.group()
def cache():
    """Manage the hallucination cache."""


@cache.command("list")
def cache_list():
    """List all cached hallucinated modules."""
    cache_dir = Path(_config["cache_dir"]).expanduser()
    files = list_cached(cache_dir)
    if not files:
        console.print("[dim]No cached modules. The void is empty.[/]")
        return

    table = Table(title="Cached Hallucinations")
    table.add_column("Module", style="cyan")
    table.add_column("Size", justify="right", style="green")
    table.add_column("Path", style="dim")

    for f in files:
        name = f.stem.rsplit("_", 1)[0]
        size = f"{f.stat().st_size:,} B"
        table.add_row(name, size, str(f))

    console.print(table)


@cache.command("clear")
def cache_clear_cmd():
    """Wipe all cached modules. They'll be re-hallucinated on next import."""
    cache_dir = Path(_config["cache_dir"]).expanduser()
    count = cache_clear(cache_dir)
    if count:
        console.print(f"[bold red]Purged {count} hallucination(s) from the cache.[/]")
    else:
        console.print("[dim]Cache was already empty. Nothing to forget.[/]")


@cli.command("config")
def config_show():
    """Show current hallucipip configuration."""
    table = Table(title="hallucipip Configuration")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="yellow")

    for key, value in _config.items():
        display = str(value)
        if key == "api_key" and value:
            display = value[:8] + "..." + value[-4:] if len(value) > 12 else "***"
        table.add_row(key, display)

    console.print(table)
