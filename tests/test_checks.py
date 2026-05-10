"""Tests for fortress.core.checks (common-password + HIBP)."""

import urllib.error
from unittest.mock import MagicMock, patch

import pytest

from fortress.core import checks
from fortress.core.checks import HIBPError, is_common, pwned_count


class TestIsCommon:
    def test_known_terrible_passwords(self):
        # Top-1000 NCSC list — these must always be flagged
        assert is_common("123456")
        assert is_common("password")
        assert is_common("qwerty")

    def test_random_password_is_not_common(self):
        # A high-entropy generated password should never match the blocklist
        assert not is_common("M^vT8L#qXz4!nP9w")

    def test_case_sensitive(self):
        # NCSC list is case-sensitive; we don't normalise (intentional)
        assert is_common("password") is True
        # Uppercase variant may or may not be in the list — just verify the
        # function doesn't crash on case
        is_common("PASSWORD")


class TestPwnedCount:
    """HIBP API tests — all network mocked."""

    def _mock_response(self, body: str):
        response = MagicMock()
        response.read.return_value = body.encode("utf-8")
        # Allow `with urlopen(...) as response:` to work
        response.__enter__ = lambda self_: response
        response.__exit__ = lambda *a: None
        return response

    def test_hits_when_suffix_present(self, monkeypatch):
        # SHA-1("password") = 5BAA61E4C9B93F3F0682250B6CF8331B7EE68FD8
        suffix_for_password = "1E4C9B93F3F0682250B6CF8331B7EE68FD8"
        body = f"{suffix_for_password}:9659365\nDEADBEEF0123:1\n"
        with patch.object(checks.urllib.request, "urlopen", return_value=self._mock_response(body)):
            assert pwned_count("password") == 9659365

    def test_zero_when_not_in_response(self, monkeypatch):
        body = "FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF:1\n"
        with patch.object(checks.urllib.request, "urlopen", return_value=self._mock_response(body)):
            assert pwned_count("a-very-unlikely-password-12345") == 0

    def test_network_error_raises_hibp_error(self, monkeypatch):
        def boom(*args, **kwargs):
            raise urllib.error.URLError("connection refused")

        with (
            patch.object(checks.urllib.request, "urlopen", side_effect=boom),
            pytest.raises(HIBPError, match="unreachable"),
        ):
            pwned_count("anything")

    def test_http_error_raises_hibp_error(self, monkeypatch):
        def boom(*args, **kwargs):
            raise urllib.error.HTTPError(
                url="https://api.pwnedpasswords.com/range/AAAAA",
                code=429,
                msg="rate limited",
                hdrs=None,
                fp=None,
            )

        with (
            patch.object(checks.urllib.request, "urlopen", side_effect=boom),
            pytest.raises(HIBPError, match="429"),
        ):
            pwned_count("anything")
