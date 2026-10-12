"""Editor and Detail view matching idea.jpg with styled action buttons and inputs."""

from __future__ import annotations

from collections.abc import Callable

import customtkinter as ctk

from mnemo.models import Note, clean_tags
from mnemo.template import extract_parameters
from mnemo.ui.theme import COLORS, FONTS, get_tag_colors


class EditorView(ctk.CTkFrame):
    """Right-side panel: Editor with inputs, monospace content box, and idea.jpg action buttons."""

    def __init__(
        self,
        parent: ctk.CTkFrame,
        on_save: Callable[[str, str, str, str, list[str]], None],
        on_delete: Callable[[str], None],
        on_duplicate: Callable[[str], None],
        on_open_params: Callable[[str], None],
        on_run_command: Callable[[str], None],
        **kwargs,
    ) -> None:
        super().__init__(parent, fg_color=COLORS["panel_bg"], corner_radius=0, **kwargs)

        self.on_save = on_save
        self.on_delete = on_delete
        self.on_duplicate = on_duplicate
        self.on_open_params = on_open_params
        self.on_run_command = on_run_command

        self.current_note: Note | None = None
        self.is_dirty: bool = False

        self._build_ui()
        self.show_empty_placeholder()

    def _build_ui(self) -> None:
        # Container for active editor
        self.editor_container = ctk.CTkFrame(self, fg_color="transparent")

        # Top Bar: Status and metadata
        meta_bar = ctk.CTkFrame(self.editor_container, fg_color="transparent")
        meta_bar.pack(fill="x", padx=24, pady=(16, 8))

        self.lbl_status = ctk.CTkLabel(
            meta_bar,
            text="✓ Saved",
            font=FONTS["small_bold"],
            text_color=COLORS["success"],
        )
        self.lbl_status.pack(side="left")

        self.lbl_timestamp = ctk.CTkLabel(
            meta_bar,
            text="",
            font=FONTS["small"],
            text_color=COLORS["text_dim"],
        )
        self.lbl_timestamp.pack(side="left", padx=(10, 0))

        # Secondary utility buttons (Duplicate, Terminal Run, Param Filler) on top right
        top_actions = ctk.CTkFrame(meta_bar, fg_color="transparent")
        top_actions.pack(side="right")

        self.btn_params = ctk.CTkButton(
            top_actions,
            text="⚡ Fill Params",
            font=FONTS["small_bold"],
            fg_color=COLORS["input_bg"],
            border_width=1,
            border_color=COLORS["border"],
            text_color=COLORS["accent_cyan"],
            hover_color=COLORS["card_bg_hover"],
            height=28,
            command=self._on_params_click,
        )
        self.btn_params.pack(side="left", padx=(0, 6))

        self.btn_run = ctk.CTkButton(
            top_actions,
            text="▶ Run",
            font=FONTS["small_bold"],
            fg_color=COLORS["input_bg"],
            border_width=1,
            border_color=COLORS["border"],
            text_color=COLORS["success"],
            hover_color=COLORS["card_bg_hover"],
            height=28,
            width=65,
            command=self._on_run_click,
        )
        self.btn_run.pack(side="left", padx=(0, 6))

        self.btn_duplicate = ctk.CTkButton(
            top_actions,
            text="✂ Duplicate",
            font=FONTS["small"],
            fg_color=COLORS["input_bg"],
            border_width=1,
            border_color=COLORS["border"],
            text_color=COLORS["text_muted"],
            hover_color=COLORS["card_bg_hover"],
            height=28,
            width=85,
            command=self._on_duplicate_click,
        )
        self.btn_duplicate.pack(side="left")

        # 1. Title Input (matching idea.jpg)
        lbl_title_tag = ctk.CTkLabel(
            self.editor_container,
            text="Title",
            font=FONTS["body_bold"],
            text_color=COLORS["text_muted"],
            anchor="w",
        )
        lbl_title_tag.pack(fill="x", padx=24, pady=(2, 2))

        self.title_entry = ctk.CTkEntry(
            self.editor_container,
            placeholder_text="Note or Snippet Title...",
            font=FONTS["title_entry"],
            fg_color=COLORS["input_bg"],
            border_color=COLORS["border"],
            height=40,
            corner_radius=8,
        )
        self.title_entry.pack(fill="x", padx=24, pady=(0, 10))
        self.title_entry.bind("<KeyRelease>", lambda e: self._mark_dirty())

        # 2. Tags Section (matching idea.jpg)
        lbl_tags = ctk.CTkLabel(
            self.editor_container,
            text="Tags",
            font=FONTS["body_bold"],
            text_color=COLORS["text_muted"],
            anchor="w",
        )
        lbl_tags.pack(fill="x", padx=24, pady=(0, 2))

        self.tags_entry = ctk.CTkEntry(
            self.editor_container,
            placeholder_text="e.g. ssh, servers, prod, template",
            font=FONTS["body"],
            fg_color=COLORS["input_bg"],
            border_color=COLORS["border"],
            height=36,
            corner_radius=8,
        )
        self.tags_entry.pack(fill="x", padx=24, pady=(0, 6))
        self.tags_entry.bind("<KeyRelease>", lambda e: self._on_tags_changed())

        # Tag badges live preview
        self.badges_frame = ctk.CTkFrame(self.editor_container, fg_color="transparent")
        self.badges_frame.pack(fill="x", padx=24, pady=(0, 8))

        # 3. Description Section
        lbl_desc = ctk.CTkLabel(
            self.editor_container,
            text="Description",
            font=FONTS["body_bold"],
            text_color=COLORS["text_muted"],
            anchor="w",
        )
        lbl_desc.pack(fill="x", padx=24, pady=(0, 2))

        self.desc_entry = ctk.CTkEntry(
            self.editor_container,
            placeholder_text="Short description of what this command/snippet does...",
            font=FONTS["body"],
            fg_color=COLORS["input_bg"],
            border_color=COLORS["border"],
            height=34,
            corner_radius=8,
        )
        self.desc_entry.pack(fill="x", padx=24, pady=(0, 10))
        self.desc_entry.bind("<KeyRelease>", lambda e: self._mark_dirty())

        # 4. Content Textbox (Monospace dark terminal surface from idea.jpg)
        lbl_content = ctk.CTkLabel(
            self.editor_container,
            text="Snippet / Command Content",
            font=FONTS["body_bold"],
            text_color=COLORS["text_muted"],
            anchor="w",
        )
        lbl_content.pack(fill="x", padx=24, pady=(0, 2))

        self.content_box = ctk.CTkTextbox(
            self.editor_container,
            font=FONTS["code"],
            fg_color=COLORS["editor_bg"],
            text_color=COLORS["text"],
            wrap="none",
            corner_radius=8,
            border_width=1,
            border_color=COLORS["border"],
        )
        self.content_box.pack(fill="both", expand=True, padx=24, pady=(0, 10))
        self.content_box.bind("<KeyRelease>", lambda e: self._on_content_changed())
        self.content_box.bind("<Tab>", self._insert_tab_spaces)

        # 5. Bottom Action Bar matching idea.jpg
        # [Copy to Clipboard]  [Save Changes]  [Revert / Reset]  [Delete Note]
        action_bar = ctk.CTkFrame(self.editor_container, fg_color="transparent")
        action_bar.pack(fill="x", padx=24, pady=(0, 16))

        # Copy to Clipboard (Cyan border)
        self.btn_copy = ctk.CTkButton(
            action_bar,
            text="📋 Copy to Clipboard",
            font=FONTS["body_bold"],
            fg_color="transparent",
            border_width=1,
            border_color=COLORS["accent_cyan"],
            text_color=COLORS["accent_cyan"],
            hover_color="#0e2a3b",
            height=38,
            corner_radius=8,
            command=self._on_copy_click,
        )
        self.btn_copy.pack(side="left", padx=(0, 10))

        # Save Changes (Emerald Green border)
        self.btn_save = ctk.CTkButton(
            action_bar,
            text="Save Changes",
            font=FONTS["body_bold"],
            fg_color="transparent",
            border_width=1,
            border_color=COLORS["success"],
            text_color=COLORS["success"],
            hover_color="#0e3328",
            height=38,
            corner_radius=8,
            command=self.save_current,
        )
        self.btn_save.pack(side="left", padx=(0, 10))

        # Revert / Reset button
        self.btn_revert = ctk.CTkButton(
            action_bar,
            text="Revert / Reset",
            font=FONTS["body"],
            fg_color=COLORS["card_bg"],
            border_width=1,
            border_color=COLORS["border"],
            text_color=COLORS["text_muted"],
            hover_color=COLORS["card_bg_hover"],
            height=38,
            corner_radius=8,
            command=self.revert_changes,
        )
        self.btn_revert.pack(side="left", padx=(0, 10))

        # Delete Note (Red Danger border)
        self.btn_delete = ctk.CTkButton(
            action_bar,
            text="Delete Note",
            font=FONTS["body"],
            fg_color="transparent",
            border_width=1,
            border_color=COLORS["danger"],
            text_color=COLORS["danger"],
            hover_color="#361519",
            height=38,
            corner_radius=8,
            command=self._on_delete_click,
        )
        self.btn_delete.pack(side="right")

        # Stats info label in bottom corner
        self.lbl_stats = ctk.CTkLabel(
            self.editor_container,
            text="",
            font=FONTS["small"],
            text_color=COLORS["text_dim"],
            anchor="e",
        )
        self.lbl_stats.pack(fill="x", padx=24, pady=(0, 4))

        # Empty State Placeholder Frame
        self.placeholder_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._build_placeholder()

    def _build_placeholder(self) -> None:
        center_box = ctk.CTkFrame(self.placeholder_frame, fg_color="transparent")
        center_box.place(relx=0.5, rely=0.45, anchor="center")

        lbl_icon = ctk.CTkLabel(
            center_box,
            text="⚡",
            font=("Segoe UI", 48),
            text_color=COLORS["accent_cyan"],
        )
        lbl_icon.pack(pady=(0, 8))

        lbl_title = ctk.CTkLabel(
            center_box,
            text="Mnemo",
            font=FONTS["app_title"],
            text_color=COLORS["text"],
        )
        lbl_title.pack(pady=(0, 4))

        lbl_sub = ctk.CTkLabel(
            center_box,
            text="Select an item from the list or create a new snippet.",
            font=FONTS["body"],
            text_color=COLORS["text_muted"],
        )
        lbl_sub.pack(pady=(0, 20))

        # Shortcuts quick table
        sc_frame = ctk.CTkFrame(
            center_box,
            fg_color=COLORS["input_bg"],
            corner_radius=8,
            border_width=1,
            border_color=COLORS["border"],
        )
        sc_frame.pack(padx=20, pady=10)

        shortcuts = [
            ("Ctrl + N", "New Snippet / Note"),
            ("Ctrl + S", "Save Current Snippet"),
            ("Ctrl + F", "Search Library"),
            ("Ctrl + Shift + C", "Copy Snippet Content"),
            ("Ctrl + D", "Duplicate Snippet"),
            ("Delete / Del", "Delete Current Snippet"),
        ]

        for key, desc in shortcuts:
            row = ctk.CTkFrame(sc_frame, fg_color="transparent")
            row.pack(fill="x", padx=16, pady=4)
            lbl_k = ctk.CTkLabel(
                row,
                text=key,
                font=FONTS["code_small"],
                text_color=COLORS["accent_cyan"],
                width=130,
                anchor="w",
            )
            lbl_k.pack(side="left")
            lbl_d = ctk.CTkLabel(
                row,
                text=desc,
                font=FONTS["small"],
                text_color=COLORS["text"],
                anchor="w",
            )
            lbl_d.pack(side="left")

    def _insert_tab_spaces(self, event) -> str:
        """Insert 4 spaces instead of cycling focus."""
        self.content_box.insert("insert", "    ")
        self._on_content_changed()
        return "break"

    def show_empty_placeholder(self) -> None:
        self.editor_container.pack_forget()
        self.placeholder_frame.pack(fill="both", expand=True)
        self.current_note = None
        self.is_dirty = False

    def load_note(self, note: Note) -> None:
        """Display and populate a note in the editor."""
        self.placeholder_frame.pack_forget()
        self.editor_container.pack(fill="both", expand=True)

        self.current_note = note
        self.is_dirty = False

        self.title_entry.delete(0, "end")
        self.title_entry.insert(0, note.title)

        self.desc_entry.delete(0, "end")
        self.desc_entry.insert(0, note.description)

        self.tags_entry.delete(0, "end")
        self.tags_entry.insert(0, ", ".join(note.tags))

        self.content_box.delete("1.0", "end")
        self.content_box.insert("1.0", note.content)

        self.lbl_timestamp.configure(
            text=f"Updated: {note.updated_at[:19].replace('T', ' ')}"
        )
        self._update_saved_status(False)
        self._update_badges()
        self._update_stats_and_params()

    def revert_changes(self) -> None:
        """Revert changes back to the saved state of the current note."""
        if self.current_note:
            self.load_note(self.current_note)

    def _mark_dirty(self) -> None:
        if not self.is_dirty:
            self.is_dirty = True
            self._update_saved_status(True)

    def _update_saved_status(self, is_dirty: bool) -> None:
        if is_dirty:
            self.lbl_status.configure(
                text="● Unsaved changes", text_color=COLORS["warning"]
            )
        else:
            self.lbl_status.configure(text="✓ Saved", text_color=COLORS["success"])

    def _on_tags_changed(self) -> None:
        self._mark_dirty()
        self._update_badges()

    def _update_badges(self) -> None:
        for w in self.badges_frame.winfo_children():
            w.destroy()

        raw_tags = self.tags_entry.get()
        tags_list = clean_tags(raw_tags)
        for tag in tags_list[:8]:
            col = get_tag_colors(tag)
            badge = ctk.CTkLabel(
                self.badges_frame,
                text=f"#{tag}",
                font=FONTS["small_bold"],
                fg_color=col["bg"],
                text_color=col["text"],
                corner_radius=5,
                padx=7,
                pady=2,
            )
            badge.pack(side="left", padx=(0, 5))

    def _on_content_changed(self) -> None:
        self._mark_dirty()
        self._update_stats_and_params()

    def _update_stats_and_params(self) -> None:
        content = self.content_box.get("1.0", "end-1c")
        lines = len(content.splitlines()) if content else 0
        chars = len(content)

        params = extract_parameters(content)
        if params:
            param_names = ", ".join(f"{{{p}}}" for p in params[:4])
            if len(params) > 4:
                param_names += f" +{len(params) - 4}"
            self.lbl_stats.configure(
                text=f"⚡ {len(params)} param(s): {param_names}  |  {lines} lines, {chars} chars"
            )
            self.btn_params.configure(border_color=COLORS["accent_cyan"])
        else:
            self.lbl_stats.configure(text=f"{lines} lines, {chars} chars")
            self.btn_params.configure(border_color=COLORS["border"])

    def _on_copy_click(self) -> None:
        content = self.content_box.get("1.0", "end-1c")
        self.clipboard_clear()
        self.clipboard_append(content)

        self.btn_copy.configure(
            text="✓ Copied!",
            border_color=COLORS["success"],
            text_color=COLORS["success"],
        )
        self.after(
            1600,
            lambda: self.btn_copy.configure(
                text="📋 Copy to Clipboard",
                border_color=COLORS["accent_cyan"],
                text_color=COLORS["accent_cyan"],
            ),
        )

    def _on_params_click(self) -> None:
        content = self.content_box.get("1.0", "end-1c")
        self.on_open_params(content)

    def _on_run_click(self) -> None:
        content = self.content_box.get("1.0", "end-1c")
        self.on_run_command(content)

    def _on_duplicate_click(self) -> None:
        if self.current_note:
            self.on_duplicate(self.current_note.id)

    def _on_delete_click(self) -> None:
        if self.current_note:
            self.on_delete(self.current_note.id)

    def save_current(self) -> None:
        """Save the currently active snippet."""
        if not self.current_note:
            return

        title = self.title_entry.get().strip() or "Untitled"
        description = self.desc_entry.get().strip()
        raw_tags = self.tags_entry.get()
        tags = clean_tags(raw_tags)
        content = self.content_box.get("1.0", "end-1c")

        self.on_save(self.current_note.id, title, description, content, tags)
        self.is_dirty = False
        self._update_saved_status(False)
        if self.current_note:
            self.lbl_timestamp.configure(
                text=f"Updated: {self.current_note.updated_at[:19].replace('T', ' ')}"
            )
