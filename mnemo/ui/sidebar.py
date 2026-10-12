"""Sidebar component for navigation, tag filters, and global actions."""

from __future__ import annotations

from collections.abc import Callable

import customtkinter as ctk

from mnemo.storage import StorageManager
from mnemo.ui.theme import COLORS, FONTS


class SidebarView(ctk.CTkFrame):
    """Sidebar providing app branding, new snippet button, tag filters, and utility controls."""

    def __init__(
        self,
        parent: ctk.CTk,
        storage: StorageManager,
        on_new_snippet: Callable[[], None],
        on_select_tag: Callable[[str | None], None],
        on_import_json: Callable[[], None],
        on_export_json: Callable[[], None],
        on_export_markdown: Callable[[], None],
        on_load_samples: Callable[[], None],
        **kwargs,
    ) -> None:
        super().__init__(
            parent, fg_color=COLORS["sidebar_bg"], corner_radius=0, **kwargs
        )

        self.storage = storage
        self.on_new_snippet = on_new_snippet
        self.on_select_tag = on_select_tag
        self.on_import_json = on_import_json
        self.on_export_json = on_export_json
        self.on_export_markdown = on_export_markdown
        self.on_load_samples = on_load_samples

        self.selected_tag: str | None = None
        self._tag_buttons: dict[str, ctk.CTkButton] = {}

        self._build_ui()

    def _build_ui(self) -> None:
        # App Branding Header
        brand_frame = ctk.CTkFrame(self, fg_color="transparent")
        brand_frame.pack(fill="x", padx=16, pady=(18, 12))

        lbl_logo = ctk.CTkLabel(
            brand_frame,
            text="⚡ Mnemo",
            font=FONTS["app_title"],
            text_color=COLORS["text"],
            anchor="w",
        )
        lbl_logo.pack(fill="x")

        lbl_sub = ctk.CTkLabel(
            brand_frame,
            text="Notes & Command Manager",
            font=FONTS["small"],
            text_color=COLORS["text_muted"],
            anchor="w",
        )
        lbl_sub.pack(fill="x", pady=(2, 0))

        # New Snippet Button
        self.btn_new = ctk.CTkButton(
            self,
            text="➕ New Snippet  (Ctrl+N)",
            font=FONTS["body_bold"],
            fg_color=COLORS["primary"],
            hover_color=COLORS["primary_hover"],
            height=38,
            corner_radius=8,
            command=self.on_new_snippet,
        )
        self.btn_new.pack(fill="x", padx=16, pady=(4, 16))

        # "All Snippets" navigation button
        self.btn_all = ctk.CTkButton(
            self,
            text=f"📋 All Items ({len(self.storage.notes)})",
            font=FONTS["body_bold"],
            fg_color=COLORS["tag_active_bg"],
            text_color=COLORS["tag_active_text"],
            hover_color=COLORS["secondary_hover"],
            anchor="w",
            height=34,
            corner_radius=6,
            command=self._clear_tag_filter,
        )
        self.btn_all.pack(fill="x", padx=16, pady=(0, 12))

        # Tags Section Header
        tags_hdr_frame = ctk.CTkFrame(self, fg_color="transparent")
        tags_hdr_frame.pack(fill="x", padx=16, pady=(4, 6))

        lbl_tags = ctk.CTkLabel(
            tags_hdr_frame,
            text="TAGS",
            font=FONTS["small_bold"],
            text_color=COLORS["text_muted"],
            anchor="w",
        )
        lbl_tags.pack(side="left")

        # Scrollable Tags Container
        self.tags_scroll = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            corner_radius=0,
        )
        self.tags_scroll.pack(fill="both", expand=True, padx=8, pady=(0, 12))

        # Bottom Utilities Frame
        bottom_frame = ctk.CTkFrame(self, fg_color="transparent")
        bottom_frame.pack(fill="x", side="bottom", padx=16, pady=16)

        # Starter Samples Button
        self.btn_samples = ctk.CTkButton(
            bottom_frame,
            text="💡 Load Starter Samples",
            font=FONTS["small"],
            fg_color=COLORS["secondary"],
            text_color=COLORS["text"],
            hover_color=COLORS["secondary_hover"],
            height=28,
            command=self.on_load_samples,
        )
        self.btn_samples.pack(fill="x", pady=(0, 8))

        # Data Management Dropdown / Buttons
        data_ops_row = ctk.CTkFrame(bottom_frame, fg_color="transparent")
        data_ops_row.pack(fill="x", pady=(0, 8))

        btn_imp = ctk.CTkButton(
            data_ops_row,
            text="Import",
            font=FONTS["small"],
            fg_color=COLORS["secondary"],
            text_color=COLORS["text"],
            hover_color=COLORS["secondary_hover"],
            height=26,
            width=65,
            command=self.on_import_json,
        )
        btn_imp.pack(side="left", padx=(0, 4))

        btn_exp = ctk.CTkButton(
            data_ops_row,
            text="Export JSON",
            font=FONTS["small"],
            fg_color=COLORS["secondary"],
            text_color=COLORS["text"],
            hover_color=COLORS["secondary_hover"],
            height=26,
            command=self.on_export_json,
        )
        btn_exp.pack(side="left", fill="x", expand=True, padx=(0, 4))

        btn_md = ctk.CTkButton(
            data_ops_row,
            text="Markdown",
            font=FONTS["small"],
            fg_color=COLORS["secondary"],
            text_color=COLORS["text"],
            hover_color=COLORS["secondary_hover"],
            height=26,
            width=68,
            command=self.on_export_markdown,
        )
        btn_md.pack(side="right")

        # Theme Selector Row
        theme_row = ctk.CTkFrame(bottom_frame, fg_color="transparent")
        theme_row.pack(fill="x")

        lbl_theme = ctk.CTkLabel(
            theme_row,
            text="Theme:",
            font=FONTS["small"],
            text_color=COLORS["text_muted"],
        )
        lbl_theme.pack(side="left")

        self.theme_menu = ctk.CTkOptionMenu(
            theme_row,
            values=["Dark", "Light", "System"],
            font=FONTS["small"],
            width=90,
            height=24,
            command=self._change_theme,
        )
        self.theme_menu.set(ctk.get_appearance_mode().capitalize() or "Dark")
        self.theme_menu.pack(side="right")

        self.refresh_tags()

    def _change_theme(self, mode: str) -> None:
        ctk.set_appearance_mode(mode.lower())

    def _clear_tag_filter(self) -> None:
        self.selected_tag = None
        self.on_select_tag(None)
        self.refresh_tags()

    def _on_tag_click(self, tag_name: str) -> None:
        if self.selected_tag == tag_name:
            # Toggle off
            self.selected_tag = None
            self.on_select_tag(None)
        else:
            self.selected_tag = tag_name
            self.on_select_tag(tag_name)
        self.refresh_tags()

    def refresh_tags(self) -> None:
        """Update tag counters and buttons."""
        total_notes = len(self.storage.notes)
        self.btn_all.configure(
            text=f"📋 All Items ({total_notes})",
            fg_color=COLORS["tag_active_bg"]
            if self.selected_tag is None
            else "transparent",
            text_color=COLORS["tag_active_text"]
            if self.selected_tag is None
            else COLORS["text"],
        )

        tags_dict = self.storage.get_tags()

        # Clear existing tag buttons
        for btn in self._tag_buttons.values():
            btn.destroy()
        self._tag_buttons.clear()

        # If no tags exist yet
        if not tags_dict:
            lbl_empty = ctk.CTkLabel(
                self.tags_scroll,
                text="No tags yet",
                font=FONTS["small"],
                text_color=COLORS["text_muted"],
            )
            lbl_empty.pack(pady=8)
            self._tag_buttons["__empty__"] = lbl_empty
            return

        for tag, count in tags_dict.items():
            is_active = self.selected_tag == tag
            btn = ctk.CTkButton(
                self.tags_scroll,
                text=f"#{tag} ({count})",
                font=FONTS["small_bold"] if is_active else FONTS["small"],
                fg_color=COLORS["tag_active_bg"] if is_active else "transparent",
                text_color=COLORS["tag_active_text"] if is_active else COLORS["text"],
                hover_color=COLORS["secondary_hover"],
                anchor="w",
                height=28,
                corner_radius=4,
                command=lambda t=tag: self._on_tag_click(t),
            )
            btn.pack(fill="x", padx=4, pady=2)
            self._tag_buttons[tag] = btn
