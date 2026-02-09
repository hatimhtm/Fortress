"""Tests for fortress.core.entropy module."""

import pytest

from fortress.core.entropy import (
    calculate_entropy,
    get_strength_label,
    get_crack_time_estimate,
)


class TestCalculateEntropy:
    """Tests for calculate_entropy function."""
    
    def test_empty_password(self):
        """Test entropy of empty password is 0."""
        assert calculate_entropy("") == 0.0
    
    def test_single_char_lowercase(self):
        """Test entropy of single lowercase character."""
        entropy = calculate_entropy("a")
        # log2(26) ≈ 4.7
        assert 4.5 < entropy < 5.0
    
    def test_longer_password_higher_entropy(self):
        """Test that longer passwords have higher entropy."""
        short = calculate_entropy("abc")
        long = calculate_entropy("abcdefgh")
        
        assert long > short
    
    def test_mixed_charset_higher_entropy(self):
        """Test that mixed charsets increase entropy."""
        lowercase_only = calculate_entropy("abcdefgh")
        mixed = calculate_entropy("Abc1!efg")
        
        assert mixed > lowercase_only
    
    def test_known_entropy_value(self):
        """Test entropy calculation with known value."""
        # 8 lowercase chars = 8 * log2(26) ≈ 37.6 bits
        password = "abcdefgh"
        entropy = calculate_entropy(password)
        
        assert 37 < entropy < 38


class TestGetStrengthLabel:
    """Tests for get_strength_label function."""
    
    def test_very_weak(self):
        """Test very weak strength level."""
        label, color = get_strength_label(20)
        assert label == "Very Weak"
        assert color == "red"
    
    def test_weak(self):
        """Test weak strength level."""
        label, color = get_strength_label(30)
        assert label == "Weak"
        assert color == "bright_red"
    
    def test_fair(self):
        """Test fair strength level."""
        label, color = get_strength_label(50)
        assert label == "Fair"
        assert color == "yellow"
    
    def test_strong(self):
        """Test strong strength level."""
        label, color = get_strength_label(80)
        assert label == "Strong"
        assert color == "green"
    
    def test_very_strong(self):
        """Test very strong strength level."""
        label, color = get_strength_label(140)
        assert label == "Very Strong"
        assert color == "cyan"


class TestGetCrackTimeEstimate:
    """Tests for get_crack_time_estimate function."""
    
    def test_instant_crack(self):
        """Test very low entropy is cracked instantly."""
        result = get_crack_time_estimate(10)
        assert result == "instantly"
    
    def test_seconds_range(self):
        """Test seconds range."""
        result = get_crack_time_estimate(35)
        assert "second" in result.lower() or "instant" in result.lower()
    
    def test_high_entropy_centuries(self):
        """Test very high entropy takes centuries."""
        result = get_crack_time_estimate(200)
        assert "centur" in result.lower() or "year" in result.lower()
    
    def test_returns_string(self):
        """Test that function always returns a string."""
        for entropy in [0, 10, 50, 100, 200]:
            result = get_crack_time_estimate(entropy)
            assert isinstance(result, str)
            assert len(result) > 0
