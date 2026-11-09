"""Order pricing with bulk discounts and coupons."""

DEFAULT_RULES = {"bulk_threshold": 10, "bulk_discount": 0.10}


class PriceCalculator:
    """Each calculator owns its own rules; changing one must not affect another."""

    def __init__(self, rules=None):
        self.rules = rules or DEFAULT_RULES

    def with_coupon(self, percent_off: float) -> "PriceCalculator":
        if not 0 <= percent_off < 1:
            raise ValueError("percent_off must be in [0, 1)")
        self.rules["coupon"] = percent_off
        return self

    def total(self, unit_price: float, quantity: int) -> float:
        subtotal = unit_price * quantity
        threshold = self.rules.get("bulk_threshold")
        if threshold is not None and quantity >= threshold:
            subtotal *= 1 - self.rules.get("bulk_discount", 0)
        subtotal *= 1 - self.rules.get("coupon", 0)
        return round(subtotal, 2)
