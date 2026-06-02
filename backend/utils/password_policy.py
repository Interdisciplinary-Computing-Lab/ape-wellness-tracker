"""
Shared password rules for registration and password changes.
"""

import re

from flask_security.password_util import PasswordUtil

PASSWORD_MIN_LENGTH = 8

# Human-readable requirements shown in forms (keep in sync with validate_password).
PASSWORD_POLICY_REQUIREMENTS = [
    f"At least {PASSWORD_MIN_LENGTH} characters",
    "At least one lowercase letter (a–z)",
    "At least one uppercase letter (A–Z)",
    "At least one number (0–9)",
    "At least one special character (e.g. ! @ # $ % ^ & *)",
]


def validate_password(password: str) -> list[str]:
    """Return a list of unmet requirement messages (empty if valid)."""
    if not password:
        return ["Password is required."]

    errors = []
    if len(password) < PASSWORD_MIN_LENGTH:
        errors.append(PASSWORD_POLICY_REQUIREMENTS[0])
    if not re.search(r"[a-z]", password):
        errors.append(PASSWORD_POLICY_REQUIREMENTS[1])
    if not re.search(r"[A-Z]", password):
        errors.append(PASSWORD_POLICY_REQUIREMENTS[2])
    if not re.search(r"\d", password):
        errors.append(PASSWORD_POLICY_REQUIREMENTS[3])
    if not re.search(r"[^a-zA-Z0-9]", password):
        errors.append(PASSWORD_POLICY_REQUIREMENTS[4])
    return errors


class AppPasswordUtil(PasswordUtil):
    """Flask-Security password util with app complexity rules."""

    def validate(self, password: str, is_register: bool, **kwargs):
        msgs, pnorm = super().validate(password, is_register, **kwargs)
        if msgs:
            return msgs, pnorm
        errors = validate_password(pnorm)
        if errors:
            return errors, pnorm
        return None, pnorm
