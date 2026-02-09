"""Fortress - Secure Password Generator

A cryptographically secure password generator with entropy estimation.
"""

__version__ = "2.0.0"
__author__ = "Hatim El Hassak"

from fortress.core.generator import generate_password, PasswordConfig
from fortress.core.entropy import calculate_entropy, get_strength_label

__all__ = [
    "generate_password",
    "PasswordConfig",
    "calculate_entropy",
    "get_strength_label",
]
