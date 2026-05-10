"""Fortress core — generation, entropy, breach checks, clipboard."""

from fortress.core.checks import HIBPError, is_common, pwned_count
from fortress.core.clipboard import ClipboardUnavailable, copy, copy_with_auto_clear
from fortress.core.entropy import (
    CrackTimes,
    calculate_entropy,
    crack_times,
    entropy_of_random,
    estimate_entropy,
    get_crack_time_estimate,
    get_strength_label,
    strength_label,
)
from fortress.core.generator import (
    AMBIGUOUS_CHARS,
    PasswordConfig,
    generate_passphrase,
    generate_password,
    generate_pin,
)
from fortress.core.wordlist import bits_per_word, eff_large

__all__ = [
    "AMBIGUOUS_CHARS",
    "ClipboardUnavailable",
    "CrackTimes",
    "HIBPError",
    "PasswordConfig",
    "bits_per_word",
    "calculate_entropy",  # deprecated alias for estimate_entropy
    "copy",
    "copy_with_auto_clear",
    "crack_times",
    "eff_large",
    "entropy_of_random",
    "estimate_entropy",
    "generate_passphrase",
    "generate_password",
    "generate_pin",
    "get_crack_time_estimate",  # deprecated alias
    "get_strength_label",  # deprecated alias for strength_label
    "is_common",
    "pwned_count",
    "strength_label",
]
