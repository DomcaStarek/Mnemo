"""Theme, typography, and styling constants for Mnemo."""

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
    "app_title": (FONT_FAMILY, 18, "bold"),
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
    "primary": ("#2563eb", "#3b82f6"),
    "primary_hover": ("#1d4ed8", "#60a5fa"),
    "secondary": ("#e2e8f0", "#334155"),
    "secondary_hover": ("#cbd5e1", "#475569"),
    "success": ("#10b981", "#059669"),
    "success_hover": ("#059669", "#047857"),
    "danger": ("#ef4444", "#dc2626"),
    "danger_hover": ("#dc2626", "#b91c1c"),
    "warning": ("#f59e0b", "#d97706"),
    "card_bg": ("#ffffff", "#1e293b"),
    "card_bg_hover": ("#f1f5f9", "#334155"),
    "card_selected": ("#e0f2fe", "#1e3a8a"),
    "sidebar_bg": ("#f8fafc", "#0f172a"),
    "main_bg": ("#f1f5f9", "#020617"),
    "panel_bg": ("#ffffff", "#1e293b"),
    "border": ("#e2e8f0", "#334155"),
    "text": ("#0f172a", "#f8fafc"),
    "text_muted": ("#64748b", "#94a3b8"),
    "tag_bg": ("#e2e8f0", "#334155"),
    "tag_text": ("#334155", "#cbd5e1"),
    "tag_active_bg": ("#dbeafe", "#1e3a8a"),
    "tag_active_text": ("#1d4ed8", "#93c5fd"),
    "terminal_bg": ("#000000", "#000000"),
    "terminal_fg": ("#00ff66", "#00ff66"),
}
