"""Tests for fortress.core.generator module."""

import pytest
import string

from fortress.core.generator import (
    generate_password,
    generate_passphrase,
    PasswordConfig,
)


class TestPasswordConfig:
    """Tests for PasswordConfig dataclass."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = PasswordConfig()
        assert config.length == 16
        assert config.use_uppercase is True
        assert config.use_lowercase is True
        assert config.use_digits is True
        assert config.use_symbols is True
        assert config.exclude_ambiguous is False
    
    def test_custom_config(self):
        """Test custom configuration."""
        config = PasswordConfig(
            length=32,
            use_symbols=False,
            exclude_ambiguous=True,
        )
        assert config.length == 32
        assert config.use_symbols is False
        assert config.exclude_ambiguous is True
    
    def test_invalid_length_zero(self):
        """Test that length < 1 raises ValueError."""
        with pytest.raises(ValueError, match="at least 1"):
            PasswordConfig(length=0)
    
    def test_invalid_length_negative(self):
        """Test that negative length raises ValueError."""
        with pytest.raises(ValueError, match="at least 1"):
            PasswordConfig(length=-5)
    
    def test_invalid_length_too_long(self):
        """Test that length > 1024 raises ValueError."""
        with pytest.raises(ValueError, match="cannot exceed 1024"):
            PasswordConfig(length=2000)
    
    def test_no_character_sets(self):
        """Test that disabling all character sets raises ValueError."""
        with pytest.raises(ValueError, match="At least one character set"):
            PasswordConfig(
                use_uppercase=False,
                use_lowercase=False,
                use_digits=False,
                use_symbols=False,
            )
    
    def test_get_charset_all(self):
        """Test charset includes all categories by default."""
        config = PasswordConfig()
        charset = config.get_charset()
        
        assert any(c in charset for c in string.ascii_uppercase)
        assert any(c in charset for c in string.ascii_lowercase)
        assert any(c in charset for c in string.digits)
        assert any(c in charset for c in string.punctuation)
    
    def test_get_charset_no_symbols(self):
        """Test charset excludes symbols when disabled."""
        config = PasswordConfig(use_symbols=False)
        charset = config.get_charset()
        
        assert not any(c in charset for c in string.punctuation)
    
    def test_get_charset_exclude_ambiguous(self):
        """Test that ambiguous characters are excluded."""
        config = PasswordConfig(exclude_ambiguous=True)
        charset = config.get_charset()
        
        ambiguous = "0O1lI|"
        for char in ambiguous:
            assert char not in charset
    
    def test_custom_chars(self):
        """Test custom characters are included."""
        config = PasswordConfig(custom_chars="€£¥")
        charset = config.get_charset()
        
        assert "€" in charset
        assert "£" in charset
        assert "¥" in charset


class TestGeneratePassword:
    """Tests for generate_password function."""
    
    def test_default_length(self):
        """Test default password length is 16."""
        password = generate_password()
        assert len(password) == 16
    
    def test_custom_length(self):
        """Test custom password length."""
        password = generate_password(length=32)
        assert len(password) == 32
    
    def test_short_password(self):
        """Test minimum length password."""
        password = generate_password(length=1)
        assert len(password) == 1
    
    def test_long_password(self):
        """Test long password generation."""
        password = generate_password(length=128)
        assert len(password) == 128
    
    def test_passwords_are_unique(self):
        """Test that generated passwords are unique."""
        passwords = [generate_password() for _ in range(100)]
        assert len(set(passwords)) == 100
    
    def test_config_override(self):
        """Test that length parameter overrides config."""
        config = PasswordConfig(length=8)
        password = generate_password(length=24, config=config)
        assert len(password) == 24
    
    def test_no_symbols_password(self):
        """Test password without symbols."""
        config = PasswordConfig(use_symbols=False)
        password = generate_password(config=config)
        
        for char in password:
            assert char not in string.punctuation
    
    def test_digits_only(self):
        """Test password with only digits."""
        config = PasswordConfig(
            use_uppercase=False,
            use_lowercase=False,
            use_digits=True,
            use_symbols=False,
        )
        password = generate_password(length=20, config=config)
        
        assert password.isdigit()


class TestGeneratePassphrase:
    """Tests for generate_passphrase function."""
    
    def test_default_word_count(self):
        """Test default passphrase has 4 words."""
        passphrase = generate_passphrase()
        words = passphrase.split("-")
        assert len(words) == 4
    
    def test_custom_word_count(self):
        """Test custom word count."""
        passphrase = generate_passphrase(word_count=6)
        words = passphrase.split("-")
        assert len(words) == 6
    
    def test_custom_separator(self):
        """Test custom separator."""
        passphrase = generate_passphrase(separator="_")
        assert "_" in passphrase
        assert "-" not in passphrase
    
    def test_capitalization(self):
        """Test words are capitalized by default."""
        passphrase = generate_passphrase()
        words = passphrase.split("-")
        
        for word in words:
            assert word[0].isupper()
    
    def test_no_capitalization(self):
        """Test words are not capitalized when disabled."""
        passphrase = generate_passphrase(capitalize=False)
        words = passphrase.split("-")
        
        for word in words:
            assert word.islower()
    
    def test_passphrases_are_unique(self):
        """Test that generated passphrases are unique."""
        passphrases = [generate_passphrase() for _ in range(50)]
        # Due to randomness, we expect high uniqueness but not guarantee 100%
        assert len(set(passphrases)) >= 45
