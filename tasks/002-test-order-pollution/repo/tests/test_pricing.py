from shop import PriceCalculator


def test_plain_total():
    assert PriceCalculator().total(5.0, 2) == 10.0


def test_bulk_discount():
    assert PriceCalculator().total(10.0, 10) == 90.0


def test_coupon():
    assert PriceCalculator().with_coupon(0.5).total(10.0, 1) == 5.0
