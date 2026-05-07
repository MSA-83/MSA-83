"""Role-based access control (RBAC) enforcement."""

from collections.abc import Callable
from enum import Enum

from fastapi import HTTPException, Request


class Role(str, Enum):
    USER = "user"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"


class Tier(str, Enum):
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"
    DEFENSE = "defense"


TIER_LEVELS = {
    Tier.FREE: 0,
    Tier.PRO: 1,
    Tier.ENTERPRISE: 2,
    Tier.DEFENSE: 3,
}

ROLE_PERMISSIONS: dict[Role, set[str]] = {
    Role.USER: {
        "chat:send",
        "chat:read",
        "memory:ingest",
        "memory:search",
        "memory:read",
        "agent:run",
        "agent:read",
        "conversation:create",
        "conversation:read",
        "conversation:delete",
        "billing:read",
        "export:download",
    },
    Role.ADMIN: {
        "chat:send",
        "chat:read",
        "chat:moderate",
        "memory:ingest",
        "memory:search",
        "memory:read",
        "memory:delete",
        "memory:admin",
        "agent:run",
        "agent:read",
        "agent:configure",
        "conversation:create",
        "conversation:read",
        "conversation:delete",
        "conversation:admin",
        "billing:read",
        "billing:manage",
        "export:download",
        "export:admin",
        "user:read",
        "user:manage",
        "feature:toggle",
    },
    Role.SUPER_ADMIN: {
        "chat:send",
        "chat:read",
        "chat:moderate",
        "memory:ingest",
        "memory:search",
        "memory:read",
        "memory:delete",
        "memory:admin",
        "agent:run",
        "agent:read",
        "agent:configure",
        "agent:admin",
        "conversation:create",
        "conversation:read",
        "conversation:delete",
        "conversation:admin",
        "billing:read",
        "billing:manage",
        "billing:admin",
        "export:download",
        "export:admin",
        "user:read",
        "user:manage",
        "user:admin",
        "feature:toggle",
        "system:config",
        "system:metrics",
        "system:logs",
    },
}

TIER_FEATURES: dict[Tier, set[str]] = {
    Tier.FREE: {"basic_chat", "basic_memory", "single_agent"},
    Tier.PRO: {
        "basic_chat",
        "basic_memory",
        "single_agent",
        "advanced_memory",
        "all_agents",
        "file_upload",
        "export",
        "priority_queue",
    },
    Tier.ENTERPRISE: {
        "basic_chat",
        "basic_memory",
        "single_agent",
        "advanced_memory",
        "all_agents",
        "file_upload",
        "export",
        "priority_queue",
        "sso",
        "custom_models",
        "api_access",
    },
    Tier.DEFENSE: {
        "basic_chat",
        "basic_memory",
        "single_agent",
        "advanced_memory",
        "all_agents",
        "file_upload",
        "export",
        "priority_queue",
        "sso",
        "custom_models",
        "api_access",
        "air_gapped",
        "audit_logs",
        "custom_retention",
    },
}


class RBACEnforcer:
    """Enforce role-based access control."""

    @staticmethod
    def has_permission(role: Role, permission: str) -> bool:
        """Check if a role has a specific permission."""
        return permission in ROLE_PERMISSIONS.get(role, set())

    @staticmethod
    def has_tier_feature(tier: Tier, feature: str) -> bool:
        """Check if a tier includes a specific feature."""
        return feature in TIER_FEATURES.get(tier, set())

    @staticmethod
    def can_upgrade(current: Tier, target: Tier) -> bool:
        """Check if upgrade from current to target is valid."""
        return TIER_LEVELS.get(target, 0) > TIER_LEVELS.get(current, 0)

    @staticmethod
    def get_available_tiers(current: Tier) -> list[Tier]:
        """Get tiers available for upgrade."""
        current_level = TIER_LEVELS.get(current, 0)
        return [t for t, level in TIER_LEVELS.items() if level > current_level]


def require_permission(permission: str) -> Callable:
    """FastAPI dependency to require a specific permission."""

    async def check(request: Request) -> bool:
        user = getattr(request.state, "user", None)
        if not user:
            raise HTTPException(status_code=401, detail="Authentication required")

        role = Role(user.get("role", "user"))
        if not RBACEnforcer.has_permission(role, permission):
            raise HTTPException(status_code=403, detail=f"Permission denied: {permission}")

        return True

    return check


def require_tier_feature(feature: str) -> Callable:
    """FastAPI dependency to require a specific tier feature."""

    async def check(request: Request) -> bool:
        user = getattr(request.state, "user", None)
        if not user:
            raise HTTPException(status_code=401, detail="Authentication required")

        tier = Tier(user.get("tier", "free"))
        if not RBACEnforcer.has_tier_feature(tier, feature):
            raise HTTPException(
                status_code=402,
                detail=f"Feature '{feature}' requires a higher tier. Current tier: {tier.value}",
            )

        return True

    return check


rbac = RBACEnforcer()
