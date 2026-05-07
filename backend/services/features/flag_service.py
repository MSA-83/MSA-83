"""Feature flag system for Titanium platform."""

import os
from datetime import datetime
from typing import Any


class FlagType:
    """Types of feature flags."""

    BOOLEAN = "boolean"
    STRING = "string"
    NUMBER = "number"
    JSON = "json"


DEFAULT_FLAGS = {
    "enable_websocket_chat": {
        "enabled": True,
        "type": FlagType.BOOLEAN,
        "value": True,
        "description": "Enable WebSocket-based real-time chat",
        "rollout_percentage": 100,
        "environments": ["development", "staging", "production"],
    },
    "enable_agent_workflows": {
        "enabled": True,
        "type": FlagType.BOOLEAN,
        "value": True,
        "description": "Enable LangGraph agent workflows",
        "rollout_percentage": 100,
        "environments": ["development", "staging"],
    },
    "enable_file_upload": {
        "enabled": True,
        "type": FlagType.BOOLEAN,
        "value": True,
        "description": "Enable file upload for PDF/DOCX processing",
        "rollout_percentage": 100,
        "environments": ["development", "staging", "production"],
    },
    "enable_billing": {
        "enabled": True,
        "type": FlagType.BOOLEAN,
        "value": True,
        "description": "Enable Stripe billing integration",
        "rollout_percentage": 50,
        "environments": ["staging", "production"],
    },
    "max_file_size_mb": {
        "enabled": True,
        "type": FlagType.NUMBER,
        "value": 50,
        "description": "Maximum file upload size in MB",
    },
    "default_model": {
        "enabled": True,
        "type": FlagType.STRING,
        "value": "llama3",
        "description": "Default LLM model for chat",
    },
    "experimental_features": {
        "enabled": False,
        "type": FlagType.JSON,
        "value": {
            "voice_input": False,
            "image_generation": False,
            "code_interpreter": True,
        },
        "description": "Experimental feature toggles",
        "rollout_percentage": 10,
        "environments": ["development"],
    },
}


class FeatureFlagService:
    """Service for managing feature flags."""

    def __init__(self):
        self._flags: dict[str, dict] = {}
        self._load_defaults()
        self._load_env_overrides()

    def _load_defaults(self):
        """Load default feature flags."""
        for name, config in DEFAULT_FLAGS.items():
            self._flags[name] = {
                **config,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
            }

    def _load_env_overrides(self):
        """Load flag overrides from environment variables."""
        for key, value in os.environ.items():
            if key.startswith("FLAG_"):
                flag_name = key[5:].lower()
                if flag_name in self._flags:
                    flag_type = self._flags[flag_name]["type"]
                    if flag_type == FlagType.BOOLEAN:
                        self._flags[flag_name]["value"] = value.lower() in ("true", "1", "yes")
                    elif flag_type == FlagType.NUMBER:
                        self._flags[flag_name]["value"] = float(value)
                    else:
                        self._flags[flag_name]["value"] = value
                    self._flags[flag_name]["updated_at"] = datetime.utcnow().isoformat()

    def is_enabled(self, flag_name: str, user_id: str | None = None) -> bool:
        """Check if a feature flag is enabled."""
        flag = self._flags.get(flag_name)
        if not flag:
            return False

        if not flag.get("enabled", False):
            return False

        rollout = flag.get("rollout_percentage", 100)
        if rollout < 100 and user_id:
            import hashlib

            hash_val = int(hashlib.md5(f"{flag_name}:{user_id}".encode()).hexdigest(), 16)
            return (hash_val % 100) < rollout

        return True

    def get_value(self, flag_name: str, default: Any = None) -> Any:
        """Get the value of a feature flag."""
        flag = self._flags.get(flag_name)
        if not flag or not flag.get("enabled", False):
            return default
        return flag.get("value", default)

    def get_all_flags(self, user_id: str | None = None) -> dict:
        """Get all feature flags for a user."""
        result = {}
        for name, flag in self._flags.items():
            result[name] = {
                "enabled": self.is_enabled(name, user_id),
                "value": flag.get("value"),
                "type": flag.get("type"),
                "description": flag.get("description", ""),
            }
        return result

    def set_flag(self, flag_name: str, value: Any, enabled: bool = True):
        """Set a feature flag value."""
        if flag_name in self._flags:
            self._flags[flag_name]["value"] = value
            self._flags[flag_name]["enabled"] = enabled
            self._flags[flag_name]["updated_at"] = datetime.utcnow().isoformat()
        else:
            self._flags[flag_name] = {
                "enabled": enabled,
                "value": value,
                "type": FlagType.BOOLEAN,
                "description": "",
                "rollout_percentage": 100,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
            }

    def get_stats(self) -> dict:
        """Get feature flag statistics."""
        enabled_count = sum(1 for f in self._flags.values() if f.get("enabled"))
        return {
            "total_flags": len(self._flags),
            "enabled_flags": enabled_count,
            "disabled_flags": len(self._flags) - enabled_count,
        }


feature_flags = FeatureFlagService()
