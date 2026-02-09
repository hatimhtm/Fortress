"""Core password generation module using cryptographically secure random."""

import secrets
import string
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class PasswordConfig:
    """Configuration for password generation.
    
    Attributes:
        length: Password length (default: 16)
        use_uppercase: Include uppercase letters (default: True)
        use_lowercase: Include lowercase letters (default: True)
        use_digits: Include digits (default: True)
        use_symbols: Include punctuation symbols (default: True)
        exclude_ambiguous: Exclude ambiguous characters like 0/O, 1/l/I (default: False)
        custom_chars: Additional custom characters to include
    """
    length: int = 16
    use_uppercase: bool = True
    use_lowercase: bool = True
    use_digits: bool = True
    use_symbols: bool = True
    exclude_ambiguous: bool = False
    custom_chars: str = ""
    
    # Ambiguous characters that can be confused
    _ambiguous_chars: str = field(default="0O1lI|", init=False, repr=False)
    
    def __post_init__(self) -> None:
        """Validate configuration after initialization."""
        if self.length < 1:
            raise ValueError("Password length must be at least 1")
        if self.length > 1024:
            raise ValueError("Password length cannot exceed 1024")
        if not any([self.use_uppercase, self.use_lowercase, 
                    self.use_digits, self.use_symbols, self.custom_chars]):
            raise ValueError("At least one character set must be enabled")
    
    def get_charset(self) -> str:
        """Build the character set based on configuration.
        
        Returns:
            String containing all allowed characters for password generation.
        """
        chars = ""
        
        if self.use_uppercase:
            chars += string.ascii_uppercase
        if self.use_lowercase:
            chars += string.ascii_lowercase
        if self.use_digits:
            chars += string.digits
        if self.use_symbols:
            chars += string.punctuation
        if self.custom_chars:
            chars += self.custom_chars
            
        if self.exclude_ambiguous:
            chars = "".join(c for c in chars if c not in self._ambiguous_chars)
            
        # Remove duplicates while preserving order
        seen = set()
        unique_chars = []
        for c in chars:
            if c not in seen:
                seen.add(c)
                unique_chars.append(c)
                
        return "".join(unique_chars)


def generate_password(
    length: Optional[int] = None,
    config: Optional[PasswordConfig] = None,
) -> str:
    """Generate a cryptographically secure password.
    
    Uses the `secrets` module which is designed for generating
    cryptographically strong random numbers suitable for security-sensitive
    applications like password generation.
    
    Args:
        length: Password length. Overrides config.length if provided.
        config: Password configuration. Uses defaults if not provided.
        
    Returns:
        A randomly generated password string.
        
    Raises:
        ValueError: If configuration is invalid.
        
    Examples:
        >>> # Generate a default 16-character password
        >>> password = generate_password()
        >>> len(password)
        16
        
        >>> # Generate a 32-character password
        >>> password = generate_password(length=32)
        >>> len(password)
        32
        
        >>> # Generate with custom config
        >>> config = PasswordConfig(length=20, use_symbols=False)
        >>> password = generate_password(config=config)
        >>> len(password)
        20
    """
    if config is None:
        config = PasswordConfig()
        
    if length is not None:
        config = PasswordConfig(
            length=length,
            use_uppercase=config.use_uppercase,
            use_lowercase=config.use_lowercase,
            use_digits=config.use_digits,
            use_symbols=config.use_symbols,
            exclude_ambiguous=config.exclude_ambiguous,
            custom_chars=config.custom_chars,
        )
    
    charset = config.get_charset()
    
    if not charset:
        raise ValueError("No characters available for password generation")
    
    # Use secrets.choice for cryptographically secure selection
    password = "".join(secrets.choice(charset) for _ in range(config.length))
    
    return password


def generate_passphrase(
    word_count: int = 4,
    separator: str = "-",
    capitalize: bool = True,
) -> str:
    """Generate a passphrase using random words.
    
    Passphrases are often easier to remember than random passwords
    while still providing good security.
    
    Args:
        word_count: Number of words in the passphrase (default: 4)
        separator: Character(s) to separate words (default: "-")
        capitalize: Whether to capitalize each word (default: True)
        
    Returns:
        A passphrase string.
    """
    # Common English words for passphrase generation
    wordlist = [
        "apple", "beach", "cloud", "dance", "eagle", "flame", "grape", "horse",
        "ivory", "joker", "knife", "lemon", "maple", "night", "ocean", "piano",
        "queen", "river", "storm", "tiger", "ultra", "voice", "water", "xerox",
        "yacht", "zebra", "amber", "brave", "crown", "dream", "ember", "frost",
        "globe", "haven", "index", "jewel", "karma", "lunar", "magic", "noble",
        "orbit", "pearl", "quest", "royal", "solar", "tower", "unity", "vivid",
        "world", "xenon", "youth", "zesty", "arrow", "blaze", "coral", "dusk",
        "epoch", "fiber", "gamma", "honey", "iris", "jazz", "kite", "lotus",
    ]
    
    words = [secrets.choice(wordlist) for _ in range(word_count)]
    
    if capitalize:
        words = [word.capitalize() for word in words]
        
    return separator.join(words)
