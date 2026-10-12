"""Theme, typography, and styling constants for Mnemo matching the modern dark aesthetic."""

from __future__ import annotations

import platform

# Font configurations
SYSTEM_OS = platform.system()

if SYSTEM_OS == "Windows":
    FONT_FAMILY = "Segoe UI"
    MONO_FONT_FAMILY = "Consolas"
elif SYSTEM_OS == "Darwin":
    FONT_FAMILY = "SF Pro Text"
    MONO_FONT_FAMILY = "Menlo"
else:
    FONT_FAMILY = "Ubuntu"
    MONO_FONT_FAMILY = "DejaVu Sans Mono"

FONTS = {
    "app_title": (FONT_FAMILY, 17, "bold"),
    "section_title": (FONT_FAMILY, 14, "bold"),
    "item_title": (FONT_FAMILY, 13, "bold"),
    "body": (FONT_FAMILY, 12),
    "body_bold": (FONT_FAMILY, 12, "bold"),
    "small": (FONT_FAMILY, 10),
    "small_bold": (FONT_FAMILY, 10, "bold"),
    "code": (MONO_FONT_FAMILY, 12),
    "code_small": (MONO_FONT_FAMILY, 10),
    "title_entry": (FONT_FAMILY, 15, "bold"),
}

# Color definitions [light_mode_color, dark_mode_color]
COLORS = {
    # Brand accents
    "primary": ("#0284c7", "#06b6d4"),
    "primary_hover": ("#0369a1", "#0891b2"),
    "accent_cyan": ("#0284c7", "#00d2d3"),
    "success": ("#059669", "#10b981"),
    "success_hover": ("#047857", "#059669"),
    "danger": ("#dc2626", "#ef4444"),
    "danger_hover": ("#b91c1c", "#dc2626"),
    "warning": ("#d97706", "#f59e0b"),
    "secondary": ("#e2e8f0", "#1e2535"),
    "secondary_hover": ("#cbd5e1", "#283247"),
    # Surfaces & Panels (Deep sleek dark slate from idea.jpg)
    "topbar_bg": ("#ffffff", "#121620"),
    "sidebar_bg": ("#f8fafc", "#141824"),
    "main_bg": ("#f1f5f9", "#10141d"),
    "panel_bg": ("#ffffff", "#161b27"),
    "editor_bg": ("#f8fafc", "#0f131c"),
    "card_bg": ("#ffffff", "#1b212f"),
    "card_bg_hover": ("#f1f5f9", "#222a3c"),
    "card_selected": ("#e0f2fe", "#242e42"),
    "card_accent_bar": ("#0284c7", "#00d2d3"),
    "border": ("#e2e8f0", "#242d3f"),
    "border_subtle": ("#f1f5f9", "#1e2535"),
    "input_bg": ("#f8fafc", "#191f2c"),
    # Text
    "text": ("#0f172a", "#f8fafc"),
    "text_muted": ("#64748b", "#94a3b8"),
    "text_dim": ("#94a3b8", "#64748b"),
    # Terminal runner
    "terminal_bg": ("#000000", "#080b11"),
    "terminal_fg": ("#00ff66", "#00ff66"),
}

# Distinct colorful tag palettes matching idea.jpg
TAG_PALETTES = [
    {"bg": "#14283d", "text": "#38bdf8", "border": "#1e4063"},  # Cyan / Blue (#ssh)
    {
        "bg": "#112e22",
        "text": "#34d399",
        "border": "#194a36",
    },  # Emerald Green (#server)
    {"bg": "#261a3b", "text": "#c084fc", "border": "#3d2760"},  # Purple (#git)
    {"bg": "#102e2b", "text": "#2dd4bf", "border": "#194a45"},  # Teal (#db)
    {
        "bg": "#33191d",
        "text": "#f87171",
        "border": "#53252c",
    },  # Coral / Salmon (#template)
    {"bg": "#312214", "text": "#fb923c", "border": "#50361e"},  # Amber / Orange (#json)
    {"bg": "#222533", "text": "#a5b4fc", "border": "#363b52"},  # Indigo
    {"bg": "#282a17", "text": "#facc15", "border": "#434624"},  # Yellow
]


def get_tag_colors(tag_name: str) -> dict[str, str]:
    """Return consistent, attractive dark-mode colors for a tag matching idea.jpg."""
    t = tag_name.lower().strip()
    if t in ("ssh", "network", "api", "curl", "remote"):
        return TAG_PALETTES[0]  # blue/cyan
    if t in ("server", "servers", "prod", "env", "node", "linux"):
        return TAG_PALETTES[1]  # emerald green
    if t in ("git", "vcs", "workflow", "commit"):
        return TAG_PALETTES[2]  # purple
    if t in ("db", "database", "postgres", "sql", "sqlite", "redis"):
        return TAG_PALETTES[3]  # teal
    if t in ("template", "draft", "todo", "dev"):
        return TAG_PALETTES[4]  # coral / salmon
    if t in ("json", "docker", "config", "shell", "bash"):
        return TAG_PALETTES[5]  # orange / amber
    idx = sum(ord(c) for c in t) % len(TAG_PALETTES)
    return TAG_PALETTES[idx]
