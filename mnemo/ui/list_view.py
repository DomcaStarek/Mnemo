"""Snippet list view: Search bar, sorting, and scrollable card list."""

from __future__ import annotations

from collections.abc import Callable
from typing import ClassVar

import customtkinter as ctk

from mnemo.models import Note
from mnemo.storage import StorageManager
from mnemo.ui.theme import COLORS, FONTS


class NoteCard(ctk.CTkFrame):
    """Card widget representing a single note/snippet in the list."""

    def __init__(
        self,
        parent: ctk.CTkFrame,
        note: Note,
        is_selected: bool,
        on_select: Callable[[Note], None],
        on_copy_content: Callable[[Note, ctk.CTkButton], None],
        **kwargs,
    ) -> None:
        bg_col = COLORS["card_selected"] if is_selected else COLORS["card_bg"]
        super().__init__(
            parent,
            fg_color=bg_col,
            corner_radius=8,
            border_width=1,
            border_color=COLORS["border"],
            **kwargs,
        )

        self.note = note
        self.is_selected = is_selected
        self.on_select = on_select
        self.on_copy_content = on_copy_content

        self._build_card()

    def _build_card(self) -> None:
        # Enable clicking on container with focus
        self.bind("<Button-1>", self._on_card_click)

        inner = ctk.CTkFrame(self, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=12, pady=10)
        inner.bind("<Button-1>", self._on_card_click)

        # Top row: Title and quick-copy button
        top_row = ctk.CTkFrame(inner, fg_color="transparent")
        top_row.pack(fill="x", pady=(0, 4))
        top_row.bind("<Button-1>", self._on_card_click)

        # Title
        title_text = self.note.title if self.note.title else "Untitled"
        lbl_title = ctk.CTkLabel(
            top_row,
            text=title_text,
            font=FONTS["item_title"],
            text_color=COLORS["text"],
            anchor="w",
        )
        lbl_title.pack(side="left", fill="x", expand=True)
        lbl_title.bind("<Button-1>", self._on_card_click)

        # Quick Copy Button on Card
        btn_copy = ctk.CTkButton(
            top_row,
            text="📋",
            font=FONTS["body"],
            fg_color="transparent",
            hover_color=COLORS["secondary_hover"],
            width=28,
            height=24,
            corner_radius=4,
        )
        btn_copy.configure(command=lambda: self.on_copy_content(self.note, btn_copy))
        btn_copy.pack(side="right")

        # Description (if any)
        if self.note.description:
            desc_text = self.note.description.strip()
            if len(desc_text) > 85:
                desc_text = desc_text[:82] + "..."
            lbl_desc = ctk.CTkLabel(
                inner,
                text=desc_text,
                font=FONTS["small"],
                text_color=COLORS["text_muted"],
                anchor="w",
                justify="left",
            )
            lbl_desc.pack(fill="x", pady=(0, 4))
            lbl_desc.bind("<Button-1>", self._on_card_click)

        # Tags row (if any)
        if self.note.tags:
            tags_row = ctk.CTkFrame(inner, fg_color="transparent")
            tags_row.pack(fill="x", pady=(0, 4))
            tags_row.bind("<Button-1>", self._on_card_click)

            for tag in self.note.tags[:4]:  # Show up to 4 tags on card
                tag_badge = ctk.CTkLabel(
                    tags_row,
                    text=f"#{tag}",
                    font=FONTS["small"],
                    fg_color=COLORS["tag_bg"],
                    text_color=COLORS["tag_text"],
                    corner_radius=4,
                    padx=6,
                    pady=1,
                )
                tag_badge.pack(side="left", padx=(0, 4))
                tag_badge.bind("<Button-1>", self._on_card_click)

            if len(self.note.tags) > 4:
                more_lbl = ctk.CTkLabel(
                    tags_row,
                    text=f"+{len(self.note.tags) - 4}",
                    font=FONTS["small"],
                    text_color=COLORS["text_muted"],
                )
                more_lbl.pack(side="left")
                more_lbl.bind("<Button-1>", self._on_card_click)

        # Content Preview (1-2 lines)
        raw_content = self.note.content.strip()
        first_lines = [
            line.strip() for line in raw_content.splitlines() if line.strip()
        ][:2]
        preview_text = " ".join(first_lines) if first_lines else "(Empty)"
        if len(preview_text) > 85:
            preview_text = preview_text[:82] + "..."

        lbl_preview = ctk.CTkLabel(
            inner,
            text=preview_text,
            font=FONTS["code_small"],
            text_color=COLORS["text_muted"],
            anchor="w",
            justify="left",
        )
        lbl_preview.pack(fill="x", pady=(0, 6))
        lbl_preview.bind("<Button-1>", self._on_card_click)

        # Footer row: Timestamp
        footer_row = ctk.CTkFrame(inner, fg_color="transparent")
        footer_row.pack(fill="x")
        footer_row.bind("<Button-1>", self._on_card_click)

        time_str = self.note.human_relative_time()
        lbl_time = ctk.CTkLabel(
            footer_row,
            text=time_str,
            font=FONTS["small"],
            text_color=COLORS["text_muted"],
            anchor="w",
        )
        lbl_time.pack(side="left")
        lbl_time.bind("<Button-1>", self._on_card_click)

    def _on_card_click(self, event=None) -> None:
        self.focus_set()
        self.on_select(self.note)


class ListView(ctk.CTkFrame):
    """Middle panel: Search bar, filter pill, sorting, and items card feed."""

    SORT_MAP: ClassVar[dict[str, str]] = {
        "Updated (Newest)": "updated_desc",
        "Updated (Oldest)": "updated_asc",
        "Created (Newest)": "created_desc",
        "Created (Oldest)": "created_asc",
        "Title (A-Z)": "title_asc",
        "Title (Z-A)": "title_desc",
    }

    def __init__(
        self,
        parent: ctk.CTkFrame,
        storage: StorageManager,
        on_select_note: Callable[[Note], None],
        on_tag_cleared: Callable[[], None],
        **kwargs,
    ) -> None:
        super().__init__(parent, fg_color=COLORS["main_bg"], corner_radius=0, **kwargs)

        self.storage = storage
        self.on_select_note = on_select_note
        self.on_tag_cleared = on_tag_cleared

        self.selected_note_id: str | None = None
        self.active_tag: str | None = None
        self._cards: list[NoteCard] = []

        self._build_ui()

    def _build_ui(self) -> None:
        # Search & Sort Controls Header
        top_ctrl = ctk.CTkFrame(self, fg_color="transparent")
        top_ctrl.pack(fill="x", padx=14, pady=(14, 8))

        # Search Row
        search_row = ctk.CTkFrame(top_ctrl, fg_color="transparent")
        search_row.pack(fill="x", pady=(0, 6))

        self.search_entry = ctk.CTkEntry(
            search_row,
            placeholder_text="🔍 Search title, content, tags... (Ctrl+F)",
            font=FONTS["body"],
            height=34,
            corner_radius=6,
        )
        self.search_entry.pack(side="left", fill="x", expand=True)
        self.search_entry.bind("<KeyRelease>", lambda e: self._on_search_changed())

        self.btn_clear_search = ctk.CTkButton(
            search_row,
            text="✕",
            font=FONTS["small"],
            fg_color=COLORS["secondary"],
            text_color=COLORS["text"],
            hover_color=COLORS["secondary_hover"],
            width=28,
            height=34,
            corner_radius=6,
            command=self._clear_search,
        )
        self.btn_clear_search.pack(side="left", padx=(4, 0))

        # Sort and Count Row
        sort_row = ctk.CTkFrame(top_ctrl, fg_color="transparent")
        sort_row.pack(fill="x")

        self.lbl_count = ctk.CTkLabel(
            sort_row,
            text="0 items",
            font=FONTS["small"],
            text_color=COLORS["text_muted"],
            anchor="w",
        )
        self.lbl_count.pack(side="left")

        self.sort_menu = ctk.CTkOptionMenu(
            sort_row,
            values=list(self.SORT_MAP.keys()),
            font=FONTS["small"],
            height=26,
            width=140,
            command=lambda v: self.refresh_list(),
        )
        self.sort_menu.set("Updated (Newest)")
        self.sort_menu.pack(side="right")

        # Active Tag Filter Banner (Hidden by default)
        self.tag_banner = ctk.CTkFrame(
            self, fg_color=COLORS["tag_active_bg"], corner_radius=6, height=28
        )
        self.lbl_banner_tag = ctk.CTkLabel(
            self.tag_banner,
            text="",
            font=FONTS["small_bold"],
            text_color=COLORS["tag_active_text"],
        )
        self.lbl_banner_tag.pack(side="left", padx=(10, 6))

        btn_close_banner = ctk.CTkButton(
            self.tag_banner,
            text="✕ Clear Tag",
            font=FONTS["small"],
            fg_color="transparent",
            text_color=COLORS["tag_active_text"],
            hover_color=COLORS["secondary_hover"],
            height=22,
            width=65,
            command=self._clear_tag_filter,
        )
        btn_close_banner.pack(side="right", padx=(0, 6), pady=2)

        # Scrollable Cards Feed
        self.cards_scroll = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            corner_radius=0,
        )
        self.cards_scroll.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    def _on_search_changed(self) -> None:
        self.refresh_list()

    def _clear_search(self) -> None:
        self.search_entry.delete(0, "end")
        self.refresh_list()

    def _clear_tag_filter(self) -> None:
        self.set_active_tag(None)
        self.on_tag_cleared()

    def set_active_tag(self, tag: str | None) -> None:
        self.active_tag = tag
        if tag:
            self.lbl_banner_tag.configure(text=f"Filtered by #{tag}")
            self.tag_banner.pack(
                fill="x", padx=14, pady=(0, 8), after=self.search_entry.master.master
            )
        else:
            self.tag_banner.pack_forget()
        self.refresh_list()

    def focus_search(self) -> None:
        self.search_entry.focus_set()
        self.search_entry.select_range(0, "end")

    def _on_copy_card_content(self, note: Note, btn: ctk.CTkButton) -> None:
        self.clipboard_clear()
        self.clipboard_append(note.content)
        btn.configure(text="✓", fg_color=COLORS["success"])
        self.after(1400, lambda: btn.configure(text="📋", fg_color="transparent"))

    def set_selected_id(self, note_id: str | None) -> None:
        self.selected_note_id = note_id
        # Re-render selection highlight
        for card in self._cards:
            is_sel = card.note.id == note_id
            card.configure(
                fg_color=COLORS["card_selected"] if is_sel else COLORS["card_bg"]
            )

    def refresh_list(self) -> list[Note]:
        """Fetch filtered notes and populate card widgets."""
        query = self.search_entry.get().strip()
        sort_key = self.SORT_MAP.get(self.sort_menu.get(), "updated_desc")

        matching_notes = self.storage.search(
            query=query,
            tag=self.active_tag,
            sort_by=sort_key,
        )

        self.lbl_count.configure(
            text=f"{len(matching_notes)} item{'s' if len(matching_notes) != 1 else ''}"
        )

        # Clear existing cards
        for card in self._cards:
            card.destroy()
        self._cards.clear()

        # Empty state
        if not matching_notes:
            msg = (
                "No matching items" if (query or self.active_tag) else "No snippets yet"
            )
            sub = (
                "Try adjusting search or tag filter."
                if (query or self.active_tag)
                else "Press Ctrl+N to create your first note or snippet."
            )

            empty_frame = ctk.CTkFrame(self.cards_scroll, fg_color="transparent")
            empty_frame.pack(fill="both", expand=True, pady=40)

            lbl_e1 = ctk.CTkLabel(
                empty_frame,
                text=msg,
                font=FONTS["body_bold"],
                text_color=COLORS["text_muted"],
            )
            lbl_e1.pack()

            lbl_e2 = ctk.CTkLabel(
                empty_frame,
                text=sub,
                font=FONTS["small"],
                text_color=COLORS["text_muted"],
            )
            lbl_e2.pack(pady=(4, 0))
            return matching_notes

        # Create cards
        for note in matching_notes:
            is_sel = note.id == self.selected_note_id
            card = NoteCard(
                self.cards_scroll,
                note=note,
                is_selected=is_sel,
                on_select=self.on_select_note,
                on_copy_content=self._on_copy_card_content,
            )
            card.pack(fill="x", pady=4)
            self._cards.append(card)

        return matching_notes
