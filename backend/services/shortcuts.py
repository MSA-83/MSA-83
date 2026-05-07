"""Keyboard shortcut documentation."""

SHORTCUTS = [
    {"keys": ["Cmd", "K"], "action": "Focus chat input", "scope": "Chat"},
    {"keys": ["Cmd", "Shift", "N"], "action": "New conversation", "scope": "Chat"},
    {"keys": ["/"], "action": "Focus chat input", "scope": "Chat"},
    {"keys": ["Cmd", "Enter"], "action": "Send message", "scope": "Chat"},
    {"keys": ["Escape"], "action": "Blur current focus", "scope": "Global"},
    {"keys": ["Cmd", "Shift", "T"], "action": "Clear all toasts", "scope": "Global"},
]


def get_shortcut_for_platform(shortcut: str, platform: str = "mac") -> str:
    """Convert shortcut to platform-specific format."""
    if platform == "mac":
        return shortcut.replace("Cmd", "⌘").replace("Shift", "⇧").replace("Ctrl", "⌃").replace("Alt", "⌥")
    else:
        return shortcut.replace("Cmd", "Ctrl").replace("Shift", "Shift").replace("Ctrl", "Ctrl").replace("Alt", "Alt")
