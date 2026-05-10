"""Fortress — cryptographically secure password / passphrase / PIN generator.

Pure-stdlib core (no runtime dependencies). CLI and server are opt-in extras.
"""

__version__ = "3.0.0"
__author__ = "Hatim El Hassak"

from fortress.core import (
    AMBIGUOUS_CHARS,
    ClipboardUnavailable,
    CrackTimes,
    HIBPError,
    PasswordConfig,
    bits_per_word,
    copy,
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

# Back-compat aliases (2.x callers).
calculate_entropy = estimate_entropy
get_strength_label = strength_label

__all__ = [
    "AMBIGUOUS_CHARS",
    "ClipboardUnavailable",
    "CrackTimes",
    "HIBPError",
    "PasswordConfig",
    "bits_per_word",
    "calculate_entropy",
    "copy",
    "copy_with_auto_clear",
    "crack_times",
    "entropy_of_random",
    "estimate_entropy",
    "generate_passphrase",
    "generate_password",
    "generate_pin",
    "get_strength_label",
    "is_common",
    "pwned_count",
    "strength_label",
]
