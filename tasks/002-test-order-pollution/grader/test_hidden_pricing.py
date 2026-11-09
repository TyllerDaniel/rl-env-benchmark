"""Tests are ordered on purpose: the coupon test runs first, then the others
check that no state leaked out of it."""

import pytest

from shop import DEFAULT_RULES, PriceCalculator

ORIGINAL_DEFAULTS = dict(DEFAULT_RULES)


def test_1_coupon_applies_to_its_own_calculator():
    assert PriceCalculator().with_coupon(0.5).total(10.0, 1) == 5.0


def test_2_new_calculator_has_no_coupon():
    assert PriceCalculator().total(5.0, 2) == 10.0


def test_3_default_rules_untouched():
    assert DEFAULT_RULES == ORIGINAL_DEFAULTS


def test_4_custom_rules_not_mutated():
    rules = {"bulk_threshold": 3, "bulk_discount": 0.5}
    PriceCalculator(rules).with_coupon(0.2)
    assert rules == {"bulk_threshold": 3, "bulk_discount": 0.5}


def test_5_empty_rules_means_no_rules():
    assert PriceCalculator(rules={}).total(10.0, 50) == 500.0


def test_6_calculators_are_independent():
    a = PriceCalculator().with_coupon(0.25)
    b = PriceCalculator()
    assert a.total(100.0, 1) == 75.0
    assert b.total(100.0, 1) == 100.0


def test_7_bulk_and_coupon_stack():
    assert PriceCalculator().with_coupon(0.5).total(10.0, 10) == 45.0


def test_8_coupon_validation():
    with pytest.raises(ValueError):
        PriceCalculator().with_coupon(1.0)
