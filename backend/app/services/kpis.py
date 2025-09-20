from decimal import Decimal

def compute_item_price(apulines: list[dict]) -> Decimal:
    total = Decimal("0")
    for l in apulines:
        coeff = Decimal(str(l.get("coeff", 0)))
        unit_cost = Decimal(str(l.get("unit_cost", 0)))
        total += coeff * unit_cost
    return total.quantize(Decimal("0.01"))
