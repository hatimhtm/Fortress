"""Entropy estimation and crack-time scenarios.

Two distinct functions:

- `entropy_of_random(length, charset_size)` — exact entropy of a uniformly
  random selection. Use this when you generated the password yourself.
- `estimate_entropy(password)` — heuristic upper bound based on character
  classes present. Use this when you don't know how the password was made
  (e.g. user-supplied via `fortress check`).

For human-chosen passwords both formulas overstate the real entropy
substantially — a real password-strength analyser would use zxcvbn. We
intentionally don't bundle zxcvbn (heavy dep, JS-derived) but document
the limitation in the README.
"""

from __future__ import annotations

import math
import string
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CrackTimes:
    """Estimated time-to-crack across attacker scenarios."""

    online_throttled: str  # 100 guesses/sec — login form with rate limiting
    online_unthrottled: str  # 10 guesses/sec * 1000 IPs = 10k/sec
    offline_slow_hash: str  # 10^4/sec — bcrypt cost=12
    offline_fast_hash: str  # 10^10/sec — single GPU on a fast hash
    offline_specialized: str  # 10^12/sec — ASIC/cluster on a fast hash


# Maps the rough character class size used by `estimate_entropy`.
_CHARSET_LOWER = set(string.ascii_lowercase)
_CHARSET_UPPER = set(string.ascii_uppercase)
_CHARSET_DIGIT = set(string.digits)
_CHARSET_SYMBOL = set(string.punctuation)


def entropy_of_random(length: int, charset_size: int) -> float:
    """Exact entropy of a uniformly random password of `length` from `charset_size`.

    Use this when Fortress generated the password — we know the inputs.
    """
    if length <= 0 or charset_size <= 1:
        return 0.0
    return length * math.log2(charset_size)


def estimate_entropy(password: str) -> float:
    """Heuristic entropy of an arbitrary password.

    Determined by character classes present (lower/upper/digit/symbol/other)
    and the password length. Always an overestimate for human-chosen
    passwords — see module docstring.
    """
    if not password:
        return 0.0

    size = 0
    chars = set(password)
    if chars & _CHARSET_LOWER:
        size += 26
    if chars & _CHARSET_UPPER:
        size += 26
    if chars & _CHARSET_DIGIT:
        size += 10
    if chars & _CHARSET_SYMBOL:
        size += 32
    if any(
        c not in (_CHARSET_LOWER | _CHARSET_UPPER | _CHARSET_DIGIT | _CHARSET_SYMBOL)
        for c in password
    ):
        size += 100  # rough Unicode fudge

    if size <= 1:
        return 0.0
    return len(password) * math.log2(size)


def strength_label(entropy: float) -> tuple[str, str]:
    """Return (label, colour) suitable for terminal display.

    Bands aligned with current NIST and CISA guidance for memorised secrets.
    """
    if entropy < 28:
        return ("Very Weak", "red")
    if entropy < 36:
        return ("Weak", "bright_red")
    if entropy < 60:
        return ("Fair", "yellow")
    if entropy < 80:
        return ("Strong", "green")
    if entropy < 128:
        return ("Very Strong", "bright_green")
    return ("Excellent", "cyan")


def crack_times(entropy: float) -> CrackTimes:
    """Estimate average-case crack times across attacker scenarios."""
    combos = 2**entropy
    # Average case: keyspace / 2
    avg = combos / 2

    return CrackTimes(
        online_throttled=_format_seconds(avg / 100),
        online_unthrottled=_format_seconds(avg / 10_000),
        offline_slow_hash=_format_seconds(avg / 10_000),
        offline_fast_hash=_format_seconds(avg / 10_000_000_000),
        offline_specialized=_format_seconds(avg / 1_000_000_000_000),
    )


def _format_seconds(seconds: float) -> str:
    """Render a duration as a short human-readable string."""
    if seconds < 1e-3:
        return "instantly"
    if seconds < 1:
        return f"{seconds*1000:.0f} ms"
    if seconds < 60:
        return f"{seconds:.0f} seconds"
    if seconds < 3_600:
        return f"{seconds/60:.0f} minutes"
    if seconds < 86_400:
        return f"{seconds/3_600:.0f} hours"
    if seconds < 31_536_000:
        return f"{seconds/86_400:.0f} days"
    years = seconds / 31_536_000
    if years < 1_000:
        return f"{years:,.0f} years"
    if years < 1_000_000:
        return f"{years/1_000:.0f}k years"
    if years < 1_000_000_000:
        return f"{years/1_000_000:.0f}M years"
    if years < 1e15:
        return f"{years/1_000_000_000:.0f}B years"
    return "longer than the age of the universe"


# ── Back-compat aliases (2.x callers) ─────────────────────────────────
calculate_entropy = estimate_entropy
get_strength_label = strength_label


def get_crack_time_estimate(entropy: float) -> str:
    """Back-compat: the single-string crack-time used in 2.x."""
    return crack_times(entropy).offline_fast_hash
