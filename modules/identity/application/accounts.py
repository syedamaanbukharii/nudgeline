"""Sign-up, login, users and roles."""

from __future__ import annotations

import re
import secrets
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import func, select

from modules.identity.domain.models import Role, User
from modules.identity.domain.permissions import DEFAULT_ROLES, OWNER_ROLE, validate_permissions
from modules.identity.domain.security import DUMMY_HASH, hash_password, verify_password
from modules.tenancy.application.audit import audit
from modules.tenancy.application.keyring import new_tenant_data_key
from modules.tenancy.domain.models import Tenant
from modules.tenancy.domain.regions import REGIONS, region_for

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


class AccountError(Exception):
    """A user-facing account problem (bad input, conflict, not allowed)."""

    def __init__(self, status: int, message: str) -> None:
        super().__init__(message)
        self.status = status
        self.message = message


@dataclass(frozen=True)
class Principal:
    user: User
    role: Role
    tenant: Tenant

    @property
    def permissions(self) -> frozenset[str]:
        return frozenset(self.role.permissions)

    def can(self, permission: str) -> bool:
        return permission in self.permissions


def normalize_email(email: str) -> str:
    email = email.strip().lower()
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        raise AccountError(422, "Enter a valid email address")
    return email


def _slugify(name: str) -> str:
    base = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")[:40] or "team"
    return f"{base}-{secrets.token_hex(3)}"


def _password_hash(password: str) -> str:
    try:
        return hash_password(password)
    except ValueError as exc:
        raise AccountError(422, str(exc)) from exc


async def sign_up(
    system: AsyncSession, *, company_name: str, full_name: str, email: str, password: str, country: str
) -> User:
    """Create a tenant with the default roles and its first (Owner) user. Use a system session."""
    email = normalize_email(email)
    country = country.upper()
    if country not in REGIONS:
        raise AccountError(422, "Unsupported country")
    if (await system.execute(select(User.id).where(User.email == email))).first():
        raise AccountError(409, "An account with this email already exists")

    region = region_for(country)
    tenant_id = uuid.uuid4()
    tenant = Tenant(
        id=tenant_id,
        name=company_name.strip(),
        slug=_slugify(company_name),
        country=country,
        timezone=region.timezone,
        currency=region.currency,
        locale="ar" if region.arabic else "en",
        data_key_enc=await new_tenant_data_key(tenant_id),
    )
    system.add(tenant)
    await system.flush()

    roles = {
        name: Role(
            tenant_id=tenant_id, name=name, description=desc, permissions=sorted(perms), is_system=name == OWNER_ROLE
        )
        for name, (desc, perms) in DEFAULT_ROLES.items()
    }
    system.add_all(roles.values())
    await system.flush()

    user = User(
        tenant_id=tenant_id,
        email=email,
        full_name=full_name.strip(),
        password_hash=_password_hash(password),
        role_id=roles[OWNER_ROLE].id,
    )
    system.add(user)
    await system.flush()
    audit(system, tenant_id, user.id, "tenant.created", "tenant", tenant_id)
    return user


async def authenticate(system: AsyncSession, email: str, password: str) -> User | None:
    """Check credentials across all tenants. Use a system session."""
    try:
        email = normalize_email(email)
    except AccountError:
        return None
    user = (await system.execute(select(User).where(User.email == email))).scalar_one_or_none()
    if user is None:
        verify_password(DUMMY_HASH, password)
        return None
    if not user.is_active or not verify_password(user.password_hash, password):
        return None
    user.last_login_at = datetime.now(UTC)
    return user


async def load_principal(session: AsyncSession, user_id: uuid.UUID) -> Principal | None:
    """Load an active user with their role and tenant, inside a tenant session."""
    row = (
        await session.execute(
            select(User, Role, Tenant)
            .join(Role, Role.id == User.role_id)
            .join(Tenant, Tenant.id == User.tenant_id)
            .where(User.id == user_id, User.is_active.is_(True), Tenant.status == "active")
        )
    ).first()
    if row is None:
        return None
    return Principal(user=row[0], role=row[1], tenant=row[2])


# ── Users ──────────────────────────────────────────────────────────


async def list_users(session: AsyncSession) -> list[User]:
    return list((await session.execute(select(User).order_by(User.created_at))).scalars())


async def _role(session: AsyncSession, role_id: uuid.UUID) -> Role:
    role = await session.get(Role, role_id)
    if role is None:
        raise AccountError(404, "Role not found")
    return role


async def _active_owner_count(session: AsyncSession) -> int:
    return (
        await session.execute(
            select(func.count())
            .select_from(User)
            .join(Role, Role.id == User.role_id)
            .where(Role.is_system.is_(True), User.is_active.is_(True))
        )
    ).scalar_one()


async def create_user(
    session: AsyncSession,
    actor: Principal,
    *,
    email: str,
    full_name: str,
    password: str,
    role_id: uuid.UUID,
) -> User:
    email = normalize_email(email)
    role = await _role(session, role_id)
    if role.is_system and not actor.role.is_system:
        raise AccountError(403, "Only an Owner can add another Owner")
    user = User(
        tenant_id=actor.tenant.id,
        email=email,
        full_name=full_name.strip(),
        password_hash=_password_hash(password),
        role_id=role.id,
    )
    session.add(user)
    try:
        await session.flush()
    except Exception as exc:  # unique violation on email
        raise AccountError(409, "An account with this email already exists") from exc
    audit(session, actor.tenant.id, actor.user.id, "user.created", "user", user.id, {"role": role.name})
    return user


async def update_user(
    session: AsyncSession,
    actor: Principal,
    user_id: uuid.UUID,
    *,
    full_name: str | None = None,
    role_id: uuid.UUID | None = None,
    is_active: bool | None = None,
    password: str | None = None,
) -> User:
    user = await session.get(User, user_id)
    if user is None:
        raise AccountError(404, "User not found")
    current_role = await _role(session, user.role_id)
    changes: dict[str, object] = {}

    if full_name is not None:
        user.full_name = full_name.strip()
        changes["full_name"] = user.full_name
    if role_id is not None and role_id != user.role_id:
        new_role = await _role(session, role_id)
        if (new_role.is_system or current_role.is_system) and not actor.role.is_system:
            raise AccountError(403, "Only an Owner can change Owner access")
        user.role_id = new_role.id
        changes["role"] = new_role.name
    if is_active is not None and is_active != user.is_active:
        if user.id == actor.user.id and not is_active:
            raise AccountError(422, "You can't deactivate yourself")
        user.is_active = is_active
        changes["is_active"] = is_active
    if password is not None:
        user.password_hash = _password_hash(password)
        changes["password"] = "changed"

    await session.flush()
    if await _active_owner_count(session) == 0:
        raise AccountError(422, "At least one active Owner is required")
    audit(session, actor.tenant.id, actor.user.id, "user.updated", "user", user.id, changes)
    return user


# ── Roles ──────────────────────────────────────────────────────────


async def list_roles(session: AsyncSession) -> list[Role]:
    return list((await session.execute(select(Role).order_by(Role.is_system.desc(), Role.name))).scalars())


def _checked_permissions(permissions: list[str]) -> list[str]:
    try:
        return validate_permissions(permissions)
    except ValueError as exc:
        raise AccountError(422, str(exc)) from exc


async def create_role(
    session: AsyncSession, actor: Principal, *, name: str, description: str, permissions: list[str]
) -> Role:
    role = Role(
        tenant_id=actor.tenant.id,
        name=name.strip(),
        description=description.strip(),
        permissions=_checked_permissions(permissions),
    )
    session.add(role)
    try:
        await session.flush()
    except Exception as exc:
        raise AccountError(409, "A role with this name already exists") from exc
    audit(session, actor.tenant.id, actor.user.id, "role.created", "role", role.id, {"permissions": role.permissions})
    return role


async def update_role(
    session: AsyncSession,
    actor: Principal,
    role_id: uuid.UUID,
    *,
    name: str | None = None,
    description: str | None = None,
    permissions: list[str] | None = None,
) -> Role:
    role = await _role(session, role_id)
    if role.is_system:
        raise AccountError(422, "The Owner role can't be changed")
    if name is not None:
        role.name = name.strip()
    if description is not None:
        role.description = description.strip()
    if permissions is not None:
        role.permissions = _checked_permissions(permissions)
    try:
        await session.flush()
    except Exception as exc:
        raise AccountError(409, "A role with this name already exists") from exc
    audit(session, actor.tenant.id, actor.user.id, "role.updated", "role", role.id, {"permissions": role.permissions})
    return role


async def delete_role(session: AsyncSession, actor: Principal, role_id: uuid.UUID) -> None:
    role = await _role(session, role_id)
    if role.is_system:
        raise AccountError(422, "The Owner role can't be deleted")
    in_use = (await session.execute(select(func.count()).where(User.role_id == role.id))).scalar_one()
    if in_use:
        raise AccountError(409, "Move users off this role before deleting it")
    await session.delete(role)
    audit(session, actor.tenant.id, actor.user.id, "role.deleted", "role", role.id, {"name": role.name})
