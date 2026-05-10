"""EFF Diceware large wordlist loader.

The EFF Large Wordlist (7,776 words, 12.92 bits of entropy per word) ships
inside the wheel. Loaded once on first call, kept as a tuple for O(1) indexing.

Reference: https://www.eff.org/dice
"""

from __future__ import annotations

import math
from functools import cache
from importlib.resources import files


@cache
def eff_large() -> tuple[str, ...]:
    """Return the EFF Large Diceware wordlist as a tuple of 7,776 words."""
    text = files("fortress.data").joinpath("eff_large_wordlist.txt").read_text(encoding="utf-8")
    words = tuple(line.strip() for line in text.splitlines() if line.strip())
    if len(words) != 7776:
        raise RuntimeError(
            f"EFF wordlist sanity check failed: got {len(words)} words, expected 7776"
        )
    return words


def bits_per_word() -> float:
    """Entropy contributed by each random word (≈ 12.925 bits for EFF Large)."""
    return math.log2(len(eff_large()))
