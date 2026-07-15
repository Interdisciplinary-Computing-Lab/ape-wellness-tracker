"""Ape body weight unit conversions (UI displays lb; database stores kg)."""

LB_PER_KG = 2.20462
KG_PER_LB = 1 / LB_PER_KG


def kg_to_lb(kg):
    """Convert kilograms to pounds, rounded to one decimal place."""
    if kg is None:
        return None
    return round(kg * LB_PER_KG, 1)


def lb_to_kg(lb):
    """Convert pounds to kilograms for database storage."""
    if lb is None:
        return None
    return float(lb) * KG_PER_LB
