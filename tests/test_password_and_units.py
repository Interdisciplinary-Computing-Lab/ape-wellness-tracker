from backend.utils.password_policy import validate_password
from backend.utils.weight_units import kg_to_lb, lb_to_kg


def test_password_policy_rejects_simple_password():
    errors = validate_password("admin123")
    assert errors


def test_password_policy_accepts_complex_password():
    assert validate_password("StaffPass1!") == []


def test_weight_round_trip():
    kg = lb_to_kg(44.1)
    assert kg_to_lb(kg) == 44.1
