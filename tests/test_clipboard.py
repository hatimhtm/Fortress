"""Tests for fortress.core.clipboard."""

from unittest.mock import patch

import pytest

from fortress.core import clipboard
from fortress.core.clipboard import ClipboardUnavailable, copy


class TestCopy:
    def test_unavailable_when_no_tool(self):
        with (
            patch.object(clipboard, "_command_for_platform", return_value=None),
            pytest.raises(ClipboardUnavailable),
        ):
            copy("secret")

    def test_invokes_subprocess_run(self):
        with (
            patch.object(clipboard, "_command_for_platform", return_value=["pbcopy"]),
            patch.object(clipboard.subprocess, "run") as mock_run,
        ):
            copy("secret")
            args, kwargs = mock_run.call_args
            assert args[0] == ["pbcopy"]
            assert kwargs["input"] == "secret"
            assert kwargs["text"] is True
            assert kwargs["check"] is True


class TestCommandForPlatform:
    def test_darwin_returns_pbcopy(self):
        with (
            patch.object(clipboard.sys, "platform", "darwin"),
            patch.object(clipboard.shutil, "which", return_value="/usr/bin/pbcopy"),
        ):
            assert clipboard._command_for_platform() == ["pbcopy"]

    def test_linux_prefers_wl_copy(self):
        with (
            patch.object(clipboard.sys, "platform", "linux"),
            patch.object(clipboard.shutil, "which", side_effect=lambda c: c == "wl-copy"),
        ):
            assert clipboard._command_for_platform() == ["wl-copy"]

    def test_linux_falls_back_to_xclip(self):
        def which(c):
            return None if c == "wl-copy" else (c if c == "xclip" else None)

        with (
            patch.object(clipboard.sys, "platform", "linux"),
            patch.object(clipboard.shutil, "which", side_effect=which),
        ):
            assert clipboard._command_for_platform() == ["xclip", "-selection", "clipboard"]

    def test_windows_returns_clip(self):
        with (
            patch.object(clipboard.sys, "platform", "win32"),
            patch.object(clipboard.shutil, "which", return_value="C:/Windows/System32/clip.exe"),
        ):
            assert clipboard._command_for_platform() == ["clip"]
