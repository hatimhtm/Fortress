"""Cryptographically secure password / passphrase / PIN generation.

All randomness comes from the stdlib `secrets` module, which is sourced from
`os.urandom` (CSPRNG). No fallbacks, no homemade RNGs.
"""

from __future__ import annotations

import secrets
import string
from dataclasses import dataclass, field

from fortress.core.wordlist import eff_large

# Glyphs commonly mistaken for one another in monospace fonts and on paper.
AMBIGUOUS_CHARS = frozenset("0O1lI|`'\",.;:5S8B")


@dataclass(slots=True)
class PasswordConfig:
    """Configuration for password generation.

    All character-set toggles default to True. `exclude_ambiguous=True` removes
    glyphs that are easy to mis-read (0/O, 1/l/I, 5/S, 8/B, …).

    `no_repeat=True` forbids the same character appearing twice in a row — useful
    for human transcription but lowers entropy by ~1 bit per character.
    """

    length: int = 16
    use_uppercase: bool = True
    use_lowercase: bool = True
    use_digits: bool = True
    use_symbols: bool = True
    exclude_ambiguous: bool = False
    no_repeat: bool = False
    custom_chars: str = ""

    # Lengths longer than this are almost certainly a bug or DoS attempt.
    _max_length: int = field(default=1024, init=False, repr=False)

    def __post_init__(self) -> None:
        if self.length < 1:
            raise ValueError("Password length must be at least 1")
        if self.length > self._max_length:
            raise ValueError(f"Password length cannot exceed {self._max_length}")
        if not (
            self.use_uppercase
            or self.use_lowercase
            or self.use_digits
            or self.use_symbols
            or self.custom_chars
        ):
            raise ValueError("At least one character set must be enabled")

    def charset(self) -> str:
        """The de-duplicated character pool the generator will sample from."""
        parts: list[str] = []
        if self.use_uppercase:
            parts.append(string.ascii_uppercase)
        if self.use_lowercase:
            parts.append(string.ascii_lowercase)
        if self.use_digits:
            parts.append(string.digits)
        if self.use_symbols:
            parts.append(string.punctuation)
        if self.custom_chars:
            parts.append(self.custom_chars)

        chars = "".join(parts)
        if self.exclude_ambiguous:
            chars = "".join(c for c in chars if c not in AMBIGUOUS_CHARS)

        # De-duplicate, preserve order
        seen: set[str] = set()
        return "".join(c for c in chars if not (c in seen or seen.add(c)))

    # `get_charset` kept as an alias for back-compat with 2.x callers.
    def get_charset(self) -> str:
        return self.charset()


def generate_password(
    length: int | None = None,
    config: PasswordConfig | None = None,
) -> str:
    """Generate a cryptographically secure password.

    Args:
        length: Override `config.length` if both are given.
        config: A `PasswordConfig`. Sensible defaults used if omitted.

    Examples:
        >>> p = generate_password()
        >>> len(p)
        16
        >>> p = generate_password(length=32, config=PasswordConfig(use_symbols=False))
        >>> len(p)
        32
    """
    if config is None:
        config = PasswordConfig()
    if length is not None and length != config.length:
        # Rebuild only the length — `slots=True` rules out `replace()`-style mutation.
        config = PasswordConfig(
            length=length,
            use_uppercase=config.use_uppercase,
            use_lowercase=config.use_lowercase,
            use_digits=config.use_digits,
            use_symbols=config.use_symbols,
            exclude_ambiguous=config.exclude_ambiguous,
            no_repeat=config.no_repeat,
            custom_chars=config.custom_chars,
        )

    charset = config.charset()
    if not charset:
        raise ValueError("Empty character set after filtering — relax exclude_ambiguous?")

    if not config.no_repeat:
        return "".join(secrets.choice(charset) for _ in range(config.length))

    if len(charset) < 2:
        raise ValueError("no_repeat=True requires a charset of at least 2 characters")

    out: list[str] = []
    last = ""
    for _ in range(config.length):
        c = secrets.choice(charset)
        while c == last:
            c = secrets.choice(charset)
        out.append(c)
        last = c
    return "".join(out)


def generate_passphrase(
    word_count: int = 6,
    separator: str = "-",
    capitalize: bool = False,
    add_number: bool = False,
    add_symbol: bool = False,
) -> str:
    """Generate an EFF Large Diceware passphrase.

    Default of six words gives ~77 bits of entropy — well above current
    NIST guidance for memorised secrets. Capitalisation, an appended digit,
    and an appended symbol are optional sprinkles that some systems require
    but they don't materially increase entropy.

    Args:
        word_count: Number of words. Six recommended; four for low-stakes.
        separator: String between words.
        capitalize: Capitalise each word.
        add_number: Append a random digit at the end.
        add_symbol: Append a random symbol at the end.
    """
    if word_count < 1:
        raise ValueError("word_count must be at least 1")

    words_pool = eff_large()
    chosen = [secrets.choice(words_pool) for _ in range(word_count)]
    if capitalize:
        chosen = [w.capitalize() for w in chosen]

    phrase = separator.join(chosen)
    if add_number:
        phrase += secrets.choice(string.digits)
    if add_symbol:
        phrase += secrets.choice(string.punctuation)
    return phrase


def generate_pin(length: int = 6) -> str:
    """Generate a numeric PIN.

    For ATM-style use. A 6-digit PIN has ~20 bits of entropy — fine when
    backed by a lockout policy, weak otherwise.
    """
    if length < 1:
        raise ValueError("PIN length must be at least 1")
    if length > 32:
        raise ValueError("PIN length cannot exceed 32")
    return "".join(secrets.choice(string.digits) for _ in range(length))
