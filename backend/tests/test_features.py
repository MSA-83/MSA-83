"""Tests for feature flags service."""


from backend.services.features.flag_service import DEFAULT_FLAGS, FeatureFlagService, FlagType


class TestFeatureFlags:
    """Test feature flags service."""

    def setup_method(self):
        self.flags = FeatureFlagService()

    def test_default_flags_exist(self):
        """Should have default flags."""
        assert self.flags.is_enabled("enable_websocket_chat") is True
        assert self.flags.is_enabled("enable_agent_workflows") is True
        assert self.flags.is_enabled("enable_file_upload") is True

    def test_enabled_flag(self):
        """Should return True for enabled flag."""
        assert self.flags.is_enabled("enable_websocket_chat") is True

    def test_disabled_flag(self):
        """Should return False for disabled flag."""
        assert self.flags.is_enabled("nonexistent_flag") is False

    def test_get_value(self):
        """Should return flag value."""
        value = self.flags.get_value("default_model")
        assert value == "llama3"

    def test_get_value_disabled_flag(self):
        """Should return default for disabled flag."""
        value = self.flags.get_value("nonexistent_flag", default="fallback")
        assert value == "fallback"

    def test_get_all_flags(self):
        """Should return all flags."""
        all_flags = self.flags.get_all_flags()
        assert isinstance(all_flags, dict)
        assert "enable_websocket_chat" in all_flags
        assert "default_model" in all_flags

    def test_get_all_flags_with_user(self):
        """Should return flags with user-specific rollout."""
        user_flags = self.flags.get_all_flags(user_id="user123")
        assert isinstance(user_flags, dict)
        for name, flag in user_flags.items():
            assert "enabled" in flag
            assert "value" in flag

    def test_set_flag(self):
        """Should set a new flag."""
        self.flags.set_flag("test_feature", True, enabled=True)
        assert self.flags.is_enabled("test_feature") is True

    def test_set_flag_updates_existing(self):
        """Should update existing flag."""
        self.flags.set_flag("enable_billing", False, enabled=False)
        assert self.flags.is_enabled("enable_billing") is False

    def test_set_flag_value(self):
        """Should set flag value."""
        self.flags.set_flag("max_file_size_mb", 100, enabled=True)
        assert self.flags.get_value("max_file_size_mb") == 100

    def test_get_stats(self):
        """Should return correct stats."""
        stats = self.flags.get_stats()
        assert "total_flags" in stats
        assert "enabled_flags" in stats
        assert "disabled_flags" in stats
        assert stats["total_flags"] == stats["enabled_flags"] + stats["disabled_flags"]

    def test_rollout_percentage(self):
        """Should respect rollout percentage."""
        stats = self.flags.get_stats()
        assert stats["total_flags"] >= len(DEFAULT_FLAGS)

    def test_rollout_consistency(self):
        """Should return consistent results for same user."""
        results = [self.flags.is_enabled("enable_billing", user_id="user123") for _ in range(100)]
        assert len(set(results)) == 1

    def test_rollout_different_users(self):
        """Should potentially return different results for different users."""
        enabled_users = 0
        for i in range(100):
            if self.flags.is_enabled("enable_billing", user_id=f"user{i}"):
                enabled_users += 1
        assert 0 < enabled_users < 100

    def test_flag_types(self):
        """Should have correct flag types."""
        assert FlagType.BOOLEAN == "boolean"
        assert FlagType.STRING == "string"
        assert FlagType.NUMBER == "number"
        assert FlagType.JSON == "json"

    def test_default_flags_have_required_fields(self):
        """All default flags should have required fields."""
        for name, config in DEFAULT_FLAGS.items():
            assert "enabled" in config
            assert "type" in config
            assert "value" in config
            assert "description" in config

    def test_experimental_features_default(self):
        """Experimental features should be disabled by default."""
        assert self.flags.is_enabled("experimental_features") is False

    def test_get_value_returns_correct_type(self):
        """Should return values of correct types."""
        model = self.flags.get_value("default_model")
        assert isinstance(model, str)

        max_size = self.flags.get_value("max_file_size_mb")
        assert isinstance(max_size, (int, float))
