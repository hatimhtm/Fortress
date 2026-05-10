"""Tests for fortress.core.generator."""

import string

import pytest

from fortress.core.generator import (
    AMBIGUOUS_CHARS,
    PasswordConfig,
    generate_passphrase,
    generate_password,
    generate_pin,
)


class TestPasswordConfig:
    def test_defaults(self):
        cfg = PasswordConfig()
        assert cfg.length == 16
        assert cfg.use_uppercase and cfg.use_lowercase
        assert cfg.use_digits and cfg.use_symbols
        assert not cfg.exclude_ambiguous and not cfg.no_repeat

    def test_invalid_length(self):
        with pytest.raises(ValueError, match="at least 1"):
            PasswordConfig(length=0)
        with pytest.raises(ValueError, match="at least 1"):
            PasswordConfig(length=-3)
        with pytest.raises(ValueError, match="cannot exceed"):
            PasswordConfig(length=10_000)

    def test_no_charset_enabled(self):
        with pytest.raises(ValueError, match="At least one character set"):
            PasswordConfig(
                use_uppercase=False,
                use_lowercase=False,
                use_digits=False,
                use_symbols=False,
            )

    def test_charset_dedupes_and_filters(self):
        cs = PasswordConfig(exclude_ambiguous=True).charset()
        assert all(c not in AMBIGUOUS_CHARS for c in cs)
        assert len(cs) == len(set(cs))  # no duplicates

    def test_custom_chars(self):
        cs = PasswordConfig(custom_chars="€£¥").charset()
        assert "€" in cs and "£" in cs and "¥" in cs


class TestGeneratePassword:
    def test_default_length(self):
        assert len(generate_password()) == 16

    def test_custom_length(self):
        assert len(generate_password(length=64)) == 64

    def test_length_override(self):
        cfg = PasswordConfig(length=8)
        assert len(generate_password(length=32, config=cfg)) == 32

    def test_excludes_ambiguous(self):
        cfg = PasswordConfig(length=200, exclude_ambiguous=True)
        for _ in range(5):
            assert not any(c in AMBIGUOUS_CHARS for c in generate_password(config=cfg))

    def test_digits_only(self):
        cfg = PasswordConfig(
            length=50,
            use_uppercase=False,
            use_lowercase=False,
            use_digits=True,
            use_symbols=False,
        )
        assert generate_password(config=cfg).isdigit()

    def test_uniqueness_at_scale(self):
        """50 random 16-char passwords should never collide in practice."""
        passwords = {generate_password() for _ in range(50)}
        assert len(passwords) == 50

    def test_no_repeat(self):
        cfg = PasswordConfig(length=200, no_repeat=True)
        for _ in range(5):
            p = generate_password(config=cfg)
            for a, b in zip(p, p[1:], strict=True):
                assert a != b, f"adjacent dupes found in {p!r}"

    def test_no_repeat_with_tiny_charset_raises(self):
        cfg = PasswordConfig(
            length=10,
            use_uppercase=False,
            use_lowercase=False,
            use_digits=False,
            use_symbols=False,
            custom_chars="a",
        )
        with pytest.raises(ValueError, match="at least 2"):
            generate_password(config=cfg)


class TestGeneratePassphrase:
    def test_default_word_count(self):
        words = generate_passphrase().split("-")
        assert len(words) == 6

    def test_eff_words_only(self):
        """All chosen words should come from the EFF list (lowercase, ascii)."""
        phrase = generate_passphrase(word_count=20).lower()
        for w in phrase.split("-"):
            assert w.isascii() and w.isalpha()

    def test_custom_separator(self):
        p = generate_passphrase(separator="_")
        assert "_" in p and "-" not in p

    def test_capitalize(self):
        words = generate_passphrase(capitalize=True).split("-")
        assert all(w[0].isupper() for w in words)

    def test_add_number_and_symbol(self):
        p = generate_passphrase(add_number=True, add_symbol=True)
        assert p[-1] in string.punctuation
        assert p[-2] in string.digits

    def test_invalid_word_count(self):
        with pytest.raises(ValueError):
            generate_passphrase(word_count=0)


class TestGeneratePin:
    def test_default(self):
        p = generate_pin()
        assert len(p) == 6 and p.isdigit()

    def test_custom_length(self):
        p = generate_pin(12)
        assert len(p) == 12 and p.isdigit()

    def test_bounds(self):
        with pytest.raises(ValueError):
            generate_pin(0)
        with pytest.raises(ValueError):
            generate_pin(33)
