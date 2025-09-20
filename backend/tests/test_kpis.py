from app.services.kpis import compute_item_price


def test_compute_item_price_basic():
    lines = [
        {"coeff": 2, "unit_cost": 10},
        {"coeff": 0.5, "unit_cost": 100},
    ]
    price = compute_item_price(lines)
    # 2*10 + 0.5*100 = 20 + 50 = 70
    assert str(price) == "70.00"
