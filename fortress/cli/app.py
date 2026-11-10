"""Fortress CLI — generate, passphrase, pin, check, serve."""

from __future__ import annotations

import dataclasses
import json
import sys

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from fortress import __version__
from fortress.core import (
    ClipboardUnavailable,
    HIBPError,
    PasswordConfig,
    copy_with_auto_clear,
    crack_times,
    entropy_of_random,
    estimate_entropy,
    generate_passphrase,
    generate_password,
    generate_pin,
    is_common,
    pwned_count,
    strength_label,
)
from fortress.core.wordlist import bits_per_word

app = typer.Typer(
    name="fortress",
    help="🏰 Cryptographically secure password / passphrase / PIN generator with entropy + breach checks.",
    add_completion=True,
    no_args_is_help=True,
    rich_markup_mode="rich",
)

console = Console()
err_console = Console(stderr=True)


# ── Helpers ────────────────────────────────────────────────────────────


def _emit_or_copy(
    password: str,
    *,
    quiet: bool,
    copy_seconds: int | None,
) -> None:
    """Print the password (or copy to clipboard + print a notice instead)."""
    if copy_seconds is not None:
        try:
            copy_with_auto_clear(password, clear_after_seconds=copy_seconds)
        except ClipboardUnavailable as exc:
            err_console.print(f"[yellow]⚠ {exc}[/yellow] — falling back to stdout.")
            print(password) if quiet else console.print(password)
            return
        if not quiet:
            err_console.print(
                f"[green]✓[/green] Copied to clipboard. Auto-clear in [bold]{copy_seconds}s[/bold]."
            )
        return

    if quiet:
        print(password)
    else:
        console.print(Panel(password, title="Password", border_style="cyan"))


def _emit_json(payload: dict) -> None:
    """JSON output to stdout — for piping into other tools."""
    print(json.dumps(payload, indent=2))


def _strength_table(password: str, entropy: float) -> Table:
    """Render strength + crack-time scenarios as a Rich table."""
    label, colour = strength_label(entropy)
    times = crack_times(entropy)

    table = Table(show_header=False, box=None, padding=(0, 1))
    table.add_column(style="dim")
    table.add_column()

    table.add_row("Length", str(len(password)))
    table.add_row("Entropy", f"{entropy:.1f} bits")
    table.add_row("Strength", f"[{colour}]{label}[/{colour}]")
    table.add_row("", "")
    table.add_row("Online (throttled)", times.online_throttled)
    table.add_row("Online (unthrottled)", times.online_unthrottled)
    table.add_row("Offline (bcrypt)", times.offline_slow_hash)
    table.add_row("Offline (GPU)", times.offline_fast_hash)
    table.add_row("Offline (ASIC cluster)", times.offline_specialized)
    return table


# ── Commands ───────────────────────────────────────────────────────────


@app.command()
def generate(
    length: int = typer.Option(20, "--length", "-l", help="Password length."),
    no_uppercase: bool = typer.Option(False, "--no-uppercase", "-U"),
    no_lowercase: bool = typer.Option(False, "--no-lowercase", "-L"),
    no_digits: bool = typer.Option(False, "--no-digits", "-D"),
    no_symbols: bool = typer.Option(False, "--no-symbols", "-S"),
    exclude_ambiguous: bool = typer.Option(
        False, "--exclude-ambiguous", "-x", help="Remove 0/O, 1/l/I, 5/S, …"
    ),
    no_repeat: bool = typer.Option(
        False, "--no-repeat", help="Forbid consecutive duplicate characters."
    ),
    count: int = typer.Option(1, "--count", "-c", help="Number of passwords to generate."),
    copy: int | None = typer.Option(  # noqa: A002 — typer wants the arg named like this
        None,
        "--copy",
        help="Copy to clipboard and clear after N seconds.",
        show_default=False,
    ),
    json_out: bool = typer.Option(False, "--json", help="Emit JSON to stdout."),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Just the password, no UI."),
) -> None:
    """Generate one or more cryptographically secure passwords."""
    try:
        config = PasswordConfig(
            length=length,
            use_uppercase=not no_uppercase,
            use_lowercase=not no_lowercase,
            use_digits=not no_digits,
            use_symbols=not no_symbols,
            exclude_ambiguous=exclude_ambiguous,
            no_repeat=no_repeat,
        )
    except ValueError as exc:
        err_console.print(f"[red]✗ {exc}[/red]")
        raise typer.Exit(1) from exc

    charset_size = len(config.charset())

    for _ in range(count):
        password = generate_password(config=config)
        entropy = entropy_of_random(len(password), charset_size)

        if json_out:
            label, _ = strength_label(entropy)
            _emit_json(
                {
                    "password": password,
                    "length": len(password),
                    "charset_size": charset_size,
                    "entropy_bits": round(entropy, 2),
                    "strength": label,
                    "crack_times": dataclasses.asdict(crack_times(entropy)),
                }
            )
            continue

        _emit_or_copy(password, quiet=quiet, copy_seconds=copy)
        if not quiet and count == 1:
            console.print(_strength_table(password, entropy))


@app.command()
def passphrase(
    words: int = typer.Option(6, "--words", "-w", help="Number of words."),
    separator: str = typer.Option("-", "--separator", "-s"),
    capitalize: bool = typer.Option(False, "--capitalize", "-C"),
    add_number: bool = typer.Option(False, "--add-number"),
    add_symbol: bool = typer.Option(False, "--add-symbol"),
    count: int = typer.Option(1, "--count", "-c"),
    copy: int | None = typer.Option(None, "--copy", show_default=False),  # noqa: A002
    json_out: bool = typer.Option(False, "--json"),
    quiet: bool = typer.Option(False, "--quiet", "-q"),
) -> None:
    """Generate an EFF Diceware passphrase (7,776-word list, ~12.9 bits per word)."""
    try:
        per_word = bits_per_word()
        for _ in range(count):
            phrase = generate_passphrase(
                word_count=words,
                separator=separator,
                capitalize=capitalize,
                add_number=add_number,
                add_symbol=add_symbol,
            )
            # Random words contribute exactly bits_per_word; sprinkled digit/symbol are bonus
            entropy = words * per_word + (3.32 if add_number else 0) + (5.0 if add_symbol else 0)

            if json_out:
                label, _ = strength_label(entropy)
                _emit_json(
                    {
                        "passphrase": phrase,
                        "word_count": words,
                        "entropy_bits": round(entropy, 2),
                        "strength": label,
                        "crack_times": dataclasses.asdict(crack_times(entropy)),
                    }
                )
                continue

            _emit_or_copy(phrase, quiet=quiet, copy_seconds=copy)
            if not quiet and count == 1:
                console.print(_strength_table(phrase, entropy))
    except ValueError as exc:
        err_console.print(f"[red]✗ {exc}[/red]")
        raise typer.Exit(1) from exc


@app.command()
def pin(
    length: int = typer.Option(6, "--length", "-l", help="PIN length (1–32)."),
    count: int = typer.Option(1, "--count", "-c"),
    copy: int | None = typer.Option(None, "--copy", show_default=False),  # noqa: A002
    json_out: bool = typer.Option(False, "--json"),
    quiet: bool = typer.Option(False, "--quiet", "-q"),
) -> None:
    """Generate a numeric PIN."""
    try:
        for _ in range(count):
            p = generate_pin(length)
            entropy = entropy_of_random(length, 10)

            if json_out:
                _emit_json(
                    {
                        "pin": p,
                        "length": length,
                        "entropy_bits": round(entropy, 2),
                    }
                )
                continue

            _emit_or_copy(p, quiet=quiet, copy_seconds=copy)
            if not quiet and count == 1:
                console.print(_strength_table(p, entropy))
    except ValueError as exc:
        err_console.print(f"[red]✗ {exc}[/red]")
        raise typer.Exit(1) from exc


@app.command()
def check(
    password: str | None = typer.Argument(
        None,
        help="Password to check. If omitted, you'll be prompted (hidden input).",
    ),
    pwned: bool = typer.Option(
        False, "--pwned", help="Also look up against HIBP (network required)."
    ),
    json_out: bool = typer.Option(False, "--json"),
) -> None:
    """Check the strength of an existing password.

    Reads from a prompt if no argument is given — that way the password
    doesn't end up in your shell history.
    """
    if password is None:
        password = typer.prompt("Password", hide_input=True)

    entropy = estimate_entropy(password)
    label, _ = strength_label(entropy)

    common = is_common(password)
    pwned_hits: int | None = None
    pwned_error: str | None = None
    if pwned:
        try:
            pwned_hits = pwned_count(password)
        except HIBPError as exc:
            pwned_error = str(exc)

    if json_out:
        _emit_json(
            {
                "length": len(password),
                "entropy_bits": round(entropy, 2),
                "strength": label,
                "is_common": common,
                "pwned_count": pwned_hits,
                "pwned_error": pwned_error,
                "crack_times": dataclasses.asdict(crack_times(entropy)),
            }
        )
        return

    console.print(_strength_table(password, entropy))
    if common:
        console.print(
            "[red]✗ This password appears in the top-1,000 most-used passwords list.[/red]"
        )
    if pwned:
        if pwned_error:
            err_console.print(f"[yellow]⚠ HIBP lookup failed: {pwned_error}[/yellow]")
        elif pwned_hits and pwned_hits > 0:
            console.print(
                f"[red]✗ Pwned: this password appears in {pwned_hits:,} known breaches.[/red]"
            )
        else:
            console.print("[green]✓ Not found in HIBP's breach corpus.[/green]")


@app.command()
def serve(
    host: str = typer.Option("0.0.0.0", "--host"),
    port: int = typer.Option(8000, "--port", "-p"),
) -> None:
    """Run the HTTP API (requires `pip install 'fortress[server]'`)."""
    from fortress.server import run as run_server  # local import keeps base install lean

    run_server(host=host, port=port)


@app.command()
def version() -> None:
    """Print version and exit."""
    print(f"fortress {__version__}")


def main() -> None:
    try:
        app()
    except KeyboardInterrupt:
        err_console.print("\n[yellow]✗ interrupted[/yellow]")
        sys.exit(130)


if __name__ == "__main__":
    main()
