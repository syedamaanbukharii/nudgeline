"""The fixed permission catalogue. Tenants build their own roles from these."""

from __future__ import annotations

PERMISSIONS: dict[str, str] = {
    "workflows.view": "View workflows",
    "workflows.manage": "Create, edit, activate and pause workflows",
    "runs.view": "View orders, calls and outcomes",
    "runs.manage": "Retry, cancel and place test calls",
    "integrations.manage": "Connect stores, WhatsApp and telephony",
    "dnc.manage": "Manage the do-not-call list",
    "users.manage": "Add, edit and deactivate users",
    "roles.manage": "Create and edit roles",
    "settings.manage": "Edit company settings",
}

ALL_PERMISSIONS: frozenset[str] = frozenset(PERMISSIONS)

OWNER_ROLE = "Owner"

DEFAULT_ROLES: dict[str, tuple[str, frozenset[str]]] = {
    OWNER_ROLE: ("Full access. Cannot be edited or deleted.", ALL_PERMISSIONS),
    "Admin": ("Everything except managing roles.", ALL_PERMISSIONS - {"roles.manage"}),
    "Operator": (
        "Works the order queue and watches calls.",
        frozenset({"workflows.view", "runs.view", "runs.manage", "dnc.manage"}),
    ),
    "Viewer": ("Read-only access.", frozenset({"workflows.view", "runs.view"})),
}


def validate_permissions(requested: list[str]) -> list[str]:
    """Return the requested permissions sorted, rejecting unknown keys."""
    unknown = set(requested) - ALL_PERMISSIONS
    if unknown:
        raise ValueError(f"unknown permissions: {', '.join(sorted(unknown))}")
    return sorted(set(requested))
