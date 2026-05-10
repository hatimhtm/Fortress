"""Tests for fortress.core.entropy."""

import math

import pytest

from fortress.core.entropy import (
    crack_times,
    entropy_of_random,
    estimate_entropy,
    strength_label,
)


class TestEntropyOfRandom:
    def test_exact_value(self):
        # 20 chars from a 94-char charset
        assert entropy_of_random(20, 94) == pytest.approx(20 * math.log2(94), rel=1e-6)

    def test_zero_when_charset_trivial(self):
        assert entropy_of_random(20, 1) == 0.0
        assert entropy_of_random(0, 94) == 0.0


class TestEstimateEntropy:
    def test_empty(self):
        assert estimate_entropy("") == 0.0

    def test_monotonic_with_length(self):
        assert estimate_entropy("aaa") < estimate_entropy("aaaaaa")

    def test_mixed_higher_than_single_class(self):
        assert estimate_entropy("Abc1!xyz") > estimate_entropy("abcdefgh")

    def test_unicode_bonus(self):
        ascii_only = estimate_entropy("abcdefgh")
        with_unicode = estimate_entropy("abcdefg€")
        assert with_unicode > ascii_only


class TestStrengthLabel:
    @pytest.mark.parametrize(
        "entropy,expected",
        [
            (20, "Very Weak"),
            (30, "Weak"),
            (50, "Fair"),
            (70, "Strong"),
            (100, "Very Strong"),
            (140, "Excellent"),
        ],
    )
    def test_bands(self, entropy, expected):
        label, _ = strength_label(entropy)
        assert label == expected


class TestCrackTimes:
    def test_returns_all_scenarios(self):
        t = crack_times(60)
        for field in (
            "online_throttled",
            "online_unthrottled",
            "offline_slow_hash",
            "offline_fast_hash",
            "offline_specialized",
        ):
            value = getattr(t, field)
            assert isinstance(value, str) and value

    def test_higher_entropy_takes_longer(self):
        weak = crack_times(20).offline_fast_hash
        strong = crack_times(120).offline_fast_hash
        assert any(unit in strong for unit in ("years", "universe"))
        assert any(unit in weak for unit in ("instant", "ms", "second", "minute", "hour"))
