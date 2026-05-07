"""Tests for RBAC enforcement."""


from backend.security.rbac import (
    ROLE_PERMISSIONS,
    TIER_FEATURES,
    TIER_LEVELS,
    RBACEnforcer,
    Role,
    Tier,
)


class TestRBACEnforcer:
    """Test RBAC enforcement."""

    def setup_method(self):
        self.rbac = RBACEnforcer()

    def test_user_has_basic_permissions(self):
        """User role should have basic permissions."""
        assert self.rbac.has_permission(Role.USER, "chat:send") is True
        assert self.rbac.has_permission(Role.USER, "memory:search") is True
        assert self.rbac.has_permission(Role.USER, "billing:read") is True

    def test_user_lacks_admin_permissions(self):
        """User role should not have admin permissions."""
        assert self.rbac.has_permission(Role.USER, "user:manage") is False
        assert self.rbac.has_permission(Role.USER, "system:config") is False
        assert self.rbac.has_permission(Role.USER, "feature:toggle") is False

    def test_admin_has_extended_permissions(self):
        """Admin role should have extended permissions."""
        assert self.rbac.has_permission(Role.ADMIN, "user:manage") is True
        assert self.rbac.has_permission(Role.ADMIN, "feature:toggle") is True
        assert self.rbac.has_permission(Role.ADMIN, "memory:delete") is True

    def test_admin_lacks_super_admin_permissions(self):
        """Admin should not have super admin permissions."""
        assert self.rbac.has_permission(Role.ADMIN, "system:config") is False
        assert self.rbac.has_permission(Role.ADMIN, "user:admin") is False

    def test_super_admin_has_all_permissions(self):
        """Super admin should have all permissions."""
        assert self.rbac.has_permission(Role.SUPER_ADMIN, "system:config") is True
        assert self.rbac.has_permission(Role.SUPER_ADMIN, "user:admin") is True
        assert self.rbac.has_permission(Role.SUPER_ADMIN, "chat:send") is True

    def test_unknown_role_has_no_permissions(self):
        """Unknown role should have no permissions."""
        result = self.rbac.has_permission(Role.USER, "nonexistent:perm")
        assert result is False

    def test_free_tier_features(self):
        """Free tier should have basic features."""
        assert self.rbac.has_tier_feature(Tier.FREE, "basic_chat") is True
        assert self.rbac.has_tier_feature(Tier.FREE, "single_agent") is True

    def test_free_tier_lacks_pro_features(self):
        """Free tier should not have pro features."""
        assert self.rbac.has_tier_feature(Tier.FREE, "sso") is False
        assert self.rbac.has_tier_feature(Tier.FREE, "api_access") is False

    def test_pro_tier_features(self):
        """Pro tier should have pro features."""
        assert self.rbac.has_tier_feature(Tier.PRO, "all_agents") is True
        assert self.rbac.has_tier_feature(Tier.PRO, "file_upload") is True
        assert self.rbac.has_tier_feature(Tier.PRO, "export") is True

    def test_pro_tier_lacks_enterprise_features(self):
        """Pro tier should not have enterprise features."""
        assert self.rbac.has_tier_feature(Tier.PRO, "sso") is False
        assert self.rbac.has_tier_feature(Tier.PRO, "custom_models") is False

    def test_enterprise_tier_features(self):
        """Enterprise tier should have enterprise features."""
        assert self.rbac.has_tier_feature(Tier.ENTERPRISE, "sso") is True
        assert self.rbac.has_tier_feature(Tier.ENTERPRISE, "api_access") is True

    def test_enterprise_lacks_defense_features(self):
        """Enterprise should not have defense-only features."""
        assert self.rbac.has_tier_feature(Tier.ENTERPRISE, "air_gapped") is False
        assert self.rbac.has_tier_feature(Tier.ENTERPRISE, "audit_logs") is False

    def test_defense_tier_has_all_features(self):
        """Defense tier should have all features."""
        assert self.rbac.has_tier_feature(Tier.DEFENSE, "air_gapped") is True
        assert self.rbac.has_tier_feature(Tier.DEFENSE, "custom_retention") is True
        assert self.rbac.has_tier_feature(Tier.DEFENSE, "basic_chat") is True

    def test_can_upgrade_free_to_pro(self):
        """Should allow upgrade from free to pro."""
        assert self.rbac.can_upgrade(Tier.FREE, Tier.PRO) is True

    def test_can_upgrade_pro_to_enterprise(self):
        """Should allow upgrade from pro to enterprise."""
        assert self.rbac.can_upgrade(Tier.PRO, Tier.ENTERPRISE) is True

    def test_cannot_downgrade(self):
        """Should not allow downgrade."""
        assert self.rbac.can_upgrade(Tier.ENTERPRISE, Tier.PRO) is False
        assert self.rbac.can_upgrade(Tier.PRO, Tier.FREE) is False

    def test_cannot_upgrade_to_same_tier(self):
        """Should not allow upgrade to same tier."""
        assert self.rbac.can_upgrade(Tier.FREE, Tier.FREE) is False

    def test_get_available_tiers_from_free(self):
        """Should return all tiers above free."""
        available = self.rbac.get_available_tiers(Tier.FREE)
        assert Tier.PRO in available
        assert Tier.ENTERPRISE in available
        assert Tier.DEFENSE in available
        assert Tier.FREE not in available

    def test_get_available_tiers_from_enterprise(self):
        """Should return only defense from enterprise."""
        available = self.rbac.get_available_tiers(Tier.ENTERPRISE)
        assert available == [Tier.DEFENSE]

    def test_get_available_tiers_from_defense(self):
        """Should return no tiers from defense."""
        available = self.rbac.get_available_tiers(Tier.DEFENSE)
        assert available == []

    def test_tier_levels_ordered(self):
        """Tier levels should be strictly increasing."""
        assert TIER_LEVELS[Tier.FREE] < TIER_LEVELS[Tier.PRO]
        assert TIER_LEVELS[Tier.PRO] < TIER_LEVELS[Tier.ENTERPRISE]
        assert TIER_LEVELS[Tier.ENTERPRISE] < TIER_LEVELS[Tier.DEFENSE]

    def test_permissions_are_sets(self):
        """All role permissions should be sets."""
        for role, perms in ROLE_PERMISSIONS.items():
            assert isinstance(perms, set)

    def test_features_are_sets(self):
        """All tier features should be sets."""
        for tier, features in TIER_FEATURES.items():
            assert isinstance(features, set)

    def test_role_inheritance(self):
        """Admin permissions should be superset of user permissions."""
        assert ROLE_PERMISSIONS[Role.USER].issubset(ROLE_PERMISSIONS[Role.ADMIN])
        assert ROLE_PERMISSIONS[Role.ADMIN].issubset(ROLE_PERMISSIONS[Role.SUPER_ADMIN])

    def test_tier_feature_inheritance(self):
        """Higher tiers should include all features of lower tiers."""
        assert TIER_FEATURES[Tier.FREE].issubset(TIER_FEATURES[Tier.PRO])
        assert TIER_FEATURES[Tier.PRO].issubset(TIER_FEATURES[Tier.ENTERPRISE])
        assert TIER_FEATURES[Tier.ENTERPRISE].issubset(TIER_FEATURES[Tier.DEFENSE])
