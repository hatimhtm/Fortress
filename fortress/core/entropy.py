"""Entropy calculation and password strength estimation."""

import math
import string
from typing import Tuple


def calculate_entropy(password: str) -> float:
    """Calculate the entropy of a password in bits.
    
    Entropy is a measure of password strength. Higher entropy means
    a stronger password. The formula is:
    
        entropy = log2(charset_size ^ password_length)
               = password_length * log2(charset_size)
    
    Args:
        password: The password to analyze.
        
    Returns:
        Entropy value in bits.
        
    Examples:
        >>> calculate_entropy("abc")  # 3 chars from 26 lowercase
        14.1...
        
        >>> calculate_entropy("Abc1!")  # Mixed charset
        32.9...
    """
    if not password:
        return 0.0
        
    charset_size = _estimate_charset_size(password)
    
    if charset_size <= 1:
        return 0.0
        
    # Entropy = length * log2(charset_size)
    entropy = len(password) * math.log2(charset_size)
    
    return entropy


def _estimate_charset_size(password: str) -> int:
    """Estimate the character set size used in the password.
    
    This estimates based on character categories present:
    - Lowercase letters: 26
    - Uppercase letters: 26
    - Digits: 10
    - Symbols: 32
    
    Args:
        password: The password to analyze.
        
    Returns:
        Estimated size of the character set.
    """
    size = 0
    
    has_lower = any(c in string.ascii_lowercase for c in password)
    has_upper = any(c in string.ascii_uppercase for c in password)
    has_digit = any(c in string.digits for c in password)
    has_symbol = any(c in string.punctuation for c in password)
    has_other = any(
        c not in string.ascii_letters + string.digits + string.punctuation
        for c in password
    )
    
    if has_lower:
        size += 26
    if has_upper:
        size += 26
    if has_digit:
        size += 10
    if has_symbol:
        size += 32
    if has_other:
        size += 100  # Unicode characters
        
    return size


def get_strength_label(entropy: float) -> Tuple[str, str]:
    """Get a human-readable strength label and color based on entropy.
    
    Strength levels based on entropy bits:
    - < 28 bits: Very Weak (red)
    - 28-35 bits: Weak (orange)
    - 36-59 bits: Fair (yellow)
    - 60-127 bits: Strong (green)
    - >= 128 bits: Very Strong (cyan)
    
    Args:
        entropy: Password entropy in bits.
        
    Returns:
        Tuple of (strength_label, ansi_color_code).
        
    Examples:
        >>> get_strength_label(25)
        ('Very Weak', 'red')
        
        >>> get_strength_label(80)
        ('Strong', 'green')
    """
    if entropy < 28:
        return ("Very Weak", "red")
    elif entropy < 36:
        return ("Weak", "bright_red")
    elif entropy < 60:
        return ("Fair", "yellow")
    elif entropy < 128:
        return ("Strong", "green")
    else:
        return ("Very Strong", "cyan")


def get_crack_time_estimate(entropy: float) -> str:
    """Estimate time to crack password based on entropy.
    
    Assumes an attacker can try 10 billion (10^10) passwords per second,
    which is achievable with modern GPU clusters.
    
    Args:
        entropy: Password entropy in bits.
        
    Returns:
        Human-readable time estimate string.
    """
    # Number of possible combinations
    combinations = 2 ** entropy
    
    # Assume 10 billion attempts per second
    attempts_per_second = 10_000_000_000
    
    # Time in seconds (on average, half the keyspace)
    seconds = combinations / (2 * attempts_per_second)
    
    if seconds < 1:
        return "instantly"
    elif seconds < 60:
        return f"{seconds:.0f} seconds"
    elif seconds < 3600:
        return f"{seconds / 60:.0f} minutes"
    elif seconds < 86400:
        return f"{seconds / 3600:.0f} hours"
    elif seconds < 31536000:
        return f"{seconds / 86400:.0f} days"
    elif seconds < 31536000 * 100:
        return f"{seconds / 31536000:.0f} years"
    elif seconds < 31536000 * 1000000:
        return f"{seconds / 31536000:.0f} years"
    else:
        return "centuries"
