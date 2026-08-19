"""Staff role helpers for route guards and templates."""

from flask_security import current_user, roles_accepted, roles_required

ROLE_ADMIN = "Admin"
ROLE_RESEARCHER = "Researcher"
ROLE_VIEWER = "Viewer"

STAFF_ROLES = (ROLE_ADMIN, ROLE_RESEARCHER, ROLE_VIEWER)
LOG_ROLES = (ROLE_ADMIN, ROLE_RESEARCHER)
CATALOG_WRITE_ROLES = (ROLE_ADMIN,)
CATALOG_CREATE_ROLES = (ROLE_ADMIN, ROLE_RESEARCHER)
APE_MANAGE_ROLES = (ROLE_ADMIN,)
EXPORT_ROLES = (ROLE_ADMIN, ROLE_RESEARCHER)


def _has_any(*role_names):
    if not getattr(current_user, "is_authenticated", False):
        return False
    return any(current_user.has_role(name) for name in role_names)


def can_log_meals():
    return _has_any(*LOG_ROLES)


def can_manage_apes():
    return _has_any(*APE_MANAGE_ROLES)


def can_manage_catalog():
    return _has_any(*CATALOG_WRITE_ROLES)


def can_create_foods():
    return _has_any(*CATALOG_CREATE_ROLES)


def can_export_reports():
    return _has_any(*EXPORT_ROLES)


def is_admin():
    return _has_any(ROLE_ADMIN)


def log_required(fn):
    """Admin or Researcher — log and edit meals."""
    return roles_accepted(*LOG_ROLES)(fn)


def catalog_write_required(fn):
    """Admin — edit/delete shared catalog and categories."""
    return roles_required(ROLE_ADMIN)(fn)


def catalog_create_required(fn):
    """Admin or Researcher — add custom foods and favorites."""
    return roles_accepted(*CATALOG_CREATE_ROLES)(fn)


def ape_manage_required(fn):
    """Admin — create/edit/archive apes and upload photos."""
    return roles_required(ROLE_ADMIN)(fn)


def export_required(fn):
    """Admin or Researcher — download reports."""
    return roles_accepted(*EXPORT_ROLES)(fn)
