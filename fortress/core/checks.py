"""Password risk checks: common-password blocklist + HaveIBeenPwned.

Two complementary checks:

- `is_common(password)` — local check against the 1,000 most-used passwords
  per NCSC's breach analysis. Always available, no network.
- `pwned_count(password)` — k-anonymity lookup against the HIBP Pwned
  Passwords API. Only the first 5 characters of the SHA-1 hash leave your
  machine; the API returns all hashes starting with that prefix and we
  match locally. https://haveibeenpwned.com/API/v3#PwnedPasswords
"""

from __future__ import annotations

import hashlib
import urllib.error
import urllib.request
from functools import cache
from importlib.resources import files

HIBP_API = "https://api.pwnedpasswords.com/range"
DEFAULT_TIMEOUT_SECONDS = 5


class HIBPError(RuntimeError):
    """Raised when the HIBP API is unreachable or returns an unexpected response."""


@cache
def _common_passwords() -> frozenset[str]:
    """Load the embedded common-password blocklist into a frozenset."""
    text = files("fortress.data").joinpath("common_passwords.txt").read_text(encoding="utf-8")
    return frozenset(line.strip() for line in text.splitlines() if line.strip())


def is_common(password: str) -> bool:
    """True if the password (case-sensitive) appears in the top-1000 NCSC list."""
    return password in _common_passwords()


def pwned_count(password: str, *, timeout: float = DEFAULT_TIMEOUT_SECONDS) -> int:
    """Return how many times this password appears in HIBP's breach corpus.

    Uses k-anonymity: only the first 5 hex chars of the SHA-1 are sent to
    the API. The remaining 35 chars stay local and are matched against the
    returned ~600 candidate suffixes.

    Returns 0 if the password is not in any known breach.

    Raises:
        HIBPError: if the API call fails (network down, rate limit, etc.).
    """
    sha1 = hashlib.sha1(password.encode("utf-8")).hexdigest().upper()
    prefix, suffix = sha1[:5], sha1[5:]

    request = urllib.request.Request(
        url=f"{HIBP_API}/{prefix}",
        headers={
            "User-Agent": "fortress-cli",
            "Add-Padding": "true",  # HIBP padding: response size doesn't leak hit count
        },
    )

    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:  # noqa: S310
            body = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        raise HIBPError(f"HIBP API returned HTTP {exc.code}") from exc
    except (urllib.error.URLError, TimeoutError) as exc:
        raise HIBPError(f"HIBP API unreachable: {exc}") from exc

    for line in body.splitlines():
        candidate_suffix, _, count = line.partition(":")
        if candidate_suffix.strip() == suffix:
            try:
                return int(count.strip())
            except ValueError:
                return 0
    return 0
