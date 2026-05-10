"""Copy text to the system clipboard with an optional auto-clear timer.

Uses the OS-native tool (`pbcopy` on macOS, `xclip`/`xsel`/`wl-copy` on Linux,
`clip` on Windows) so there's no dependency on `pyperclip`. If no tool is
found, raises `ClipboardUnavailable` and the caller decides what to do
(typically: warn the user but still print the password to stdout).
"""

from __future__ import annotations

import contextlib
import shutil
import subprocess
import sys
import threading
import time


class ClipboardUnavailable(RuntimeError):
    """Raised when no system clipboard tool can be found."""


def _command_for_platform() -> list[str] | None:
    """Return the argv to invoke for `<command> <stdin-text>`."""
    if sys.platform == "darwin":
        if shutil.which("pbcopy"):
            return ["pbcopy"]
    elif sys.platform.startswith("linux"):
        if shutil.which("wl-copy"):  # Wayland
            return ["wl-copy"]
        if shutil.which("xclip"):
            return ["xclip", "-selection", "clipboard"]
        if shutil.which("xsel"):
            return ["xsel", "--clipboard", "--input"]
    elif sys.platform == "win32":
        if shutil.which("clip"):
            return ["clip"]
    return None


def copy(text: str) -> None:
    """Write `text` to the system clipboard."""
    cmd = _command_for_platform()
    if cmd is None:
        raise ClipboardUnavailable(
            "No clipboard tool found. Install one of: pbcopy (macOS), "
            "wl-copy / xclip / xsel (Linux), clip (Windows)."
        )
    subprocess.run(cmd, input=text, text=True, check=True)


def copy_with_auto_clear(text: str, *, clear_after_seconds: float) -> None:
    """Copy `text` to clipboard now, and clear it after `clear_after_seconds`.

    The clear is best-effort: it overwrites the clipboard with an empty
    string. If the user has copied something else in the meantime we
    overwrite that too — but that's the cost of "stop holding my password
    in my paste buffer" and is the same trade-off `pass(1)` makes.

    Runs the timer in a daemon thread; the caller doesn't need to await it.
    """
    copy(text)

    def _clear_later() -> None:
        time.sleep(clear_after_seconds)
        with contextlib.suppress(ClipboardUnavailable):
            copy("")

    thread = threading.Thread(target=_clear_later, daemon=True)
    thread.start()
