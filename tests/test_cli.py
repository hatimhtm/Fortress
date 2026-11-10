"""CLI-level tests: invalid options fail cleanly (no traceback)."""

import pytest
from typer.testing import CliRunner

from fortress.cli.app import app

runner = CliRunner(mix_stderr=False)


def _combined(result) -> str:
    return (result.output or "") + (getattr(result, "stderr", "") or "")


@pytest.mark.parametrize("words", [0, -2])
def test_passphrase_invalid_word_count_exits_cleanly(words):
    """`passphrase --words <n<1>` must print a clean error and exit 1.

    Regression: used to bubble an unhandled ValueError (rich traceback,
    empty stdout) while sibling commands (`generate`, `pin`) already
    reported the same class of error cleanly with exit code 1.
    """
    result = runner.invoke(app, ["passphrase", "--words", str(words)])
    assert result.exit_code == 1
    # No leaked exception: typer.Exit surfaces as SystemExit, not ValueError.
    assert isinstance(result.exception, SystemExit)
    assert "word_count must be at least 1" in _combined(result)


def test_passphrase_valid_word_count_still_works():
    result = runner.invoke(app, ["passphrase", "--words", "3", "--quiet"])
    assert result.exit_code == 0
    assert len(result.output.strip().split("-")) == 3
