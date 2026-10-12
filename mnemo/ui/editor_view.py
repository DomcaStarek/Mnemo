"""Editor and Detail view for viewing, modifying, copying, and running snippets."""

from __future__ import annotations

from collections.abc import Callable

import customtkinter as ctk

from mnemo.models import Note, clean_tags
from mnemo.template import extract_parameters
from mnemo.ui.theme import COLORS, FONTS


class EditorView(ctk.CTkFrame):
    """Right-side panel: Editor with toolbar, title, tags, and monospace content area."""

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

        # Top Action Bar
        top_bar = ctk.CTkFrame(self.editor_container, fg_color="transparent")
        top_bar.pack(fill="x", padx=20, pady=(16, 12))

        # Status & Meta info (Left)
        meta_frame = ctk.CTkFrame(top_bar, fg_color="transparent")
        meta_frame.pack(side="left")

        self.lbl_status = ctk.CTkLabel(
            meta_frame,
            text="✓ Saved",
            font=FONTS["small_bold"],
            text_color=COLORS["success"],
        )
        self.lbl_status.pack(side="left")

        self.lbl_timestamp = ctk.CTkLabel(
            meta_frame,
            text="",
            font=FONTS["small"],
            text_color=COLORS["text_muted"],
        )
        self.lbl_timestamp.pack(side="left", padx=(10, 0))

        # Action Buttons (Right)
        actions_frame = ctk.CTkFrame(top_bar, fg_color="transparent")
        actions_frame.pack(side="right")

        self.btn_copy = ctk.CTkButton(
            actions_frame,
            text="📋 Copy",
            font=FONTS["body_bold"],
            fg_color=COLORS["primary"],
            hover_color=COLORS["primary_hover"],
            height=32,
            width=85,
            command=self._on_copy_click,
        )
        self.btn_copy.pack(side="left", padx=(0, 6))

        self.btn_params = ctk.CTkButton(
            actions_frame,
            text="⚡ Fill Params",
            font=FONTS["body_bold"],
            fg_color=COLORS["secondary"],
            text_color=COLORS["text"],
            hover_color=COLORS["secondary_hover"],
            height=32,
            command=self._on_params_click,
        )
        self.btn_params.pack(side="left", padx=(0, 6))

        self.btn_run = ctk.CTkButton(
            actions_frame,
            text="▶ Run",
            font=FONTS["body_bold"],
            fg_color=COLORS["secondary"],
            text_color=COLORS["text"],
            hover_color=COLORS["secondary_hover"],
            height=32,
            width=70,
            command=self._on_run_click,
        )
        self.btn_run.pack(side="left", padx=(0, 6))

        self.btn_duplicate = ctk.CTkButton(
            actions_frame,
            text="✂ Duplicate",
            font=FONTS["body"],
            fg_color=COLORS["secondary"],
            text_color=COLORS["text"],
            hover_color=COLORS["secondary_hover"],
            height=32,
            width=90,
            command=self._on_duplicate_click,
        )
        self.btn_duplicate.pack(side="left", padx=(0, 6))

        self.btn_delete = ctk.CTkButton(
            actions_frame,
            text="🗑 Delete (Del)",
            font=FONTS["body"],
            fg_color=COLORS["danger"],
            hover_color=COLORS["danger_hover"],
            height=32,
            width=95,
            command=self._on_delete_click,
        )
        self.btn_delete.pack(side="left", padx=(0, 6))

        self.btn_save = ctk.CTkButton(
            actions_frame,
            text="💾 Save",
            font=FONTS["body_bold"],
            fg_color=COLORS["primary"],
            hover_color=COLORS["primary_hover"],
            height=32,
            width=80,
            command=self.save_current,
        )
        self.btn_save.pack(side="left")

        # Title Field
        self.title_entry = ctk.CTkEntry(
            self.editor_container,
            placeholder_text="Snippet or Note Title...",
            font=FONTS["title_entry"],
            height=38,
            corner_radius=6,
        )
        self.title_entry.pack(fill="x", padx=20, pady=(0, 6))
        self.title_entry.bind("<KeyRelease>", lambda e: self._mark_dirty())

        # Description Field
        self.desc_entry = ctk.CTkEntry(
            self.editor_container,
            placeholder_text="Short description of what this command/snippet does (optional)...",
            font=FONTS["body"],
            height=32,
            corner_radius=6,
        )
        self.desc_entry.pack(fill="x", padx=20, pady=(0, 8))
        self.desc_entry.bind("<KeyRelease>", lambda e: self._mark_dirty())

        # Tags Row
        tags_row = ctk.CTkFrame(self.editor_container, fg_color="transparent")
        tags_row.pack(fill="x", padx=20, pady=(0, 6))

        lbl_tags_icon = ctk.CTkLabel(
            tags_row,
            text="🏷️ Tags:",
            font=FONTS["small_bold"],
            text_color=COLORS["text_muted"],
        )
        lbl_tags_icon.pack(side="left", padx=(0, 6))

        self.tags_entry = ctk.CTkEntry(
            tags_row,
            placeholder_text="Comma-separated tags (e.g. git, shell, docker, python)",
            font=FONTS["body"],
            height=32,
            corner_radius=6,
        )
        self.tags_entry.pack(side="left", fill="x", expand=True)
        self.tags_entry.bind("<KeyRelease>", lambda e: self._on_tags_changed())

        # Tag badges preview row
        self.badges_frame = ctk.CTkFrame(self.editor_container, fg_color="transparent")
        self.badges_frame.pack(fill="x", padx=20, pady=(0, 8))

        # Content Textbox (Monospace)
        self.content_box = ctk.CTkTextbox(
            self.editor_container,
            font=FONTS["code"],
            wrap="none",
            corner_radius=6,
            border_width=1,
            border_color=COLORS["border"],
        )
        self.content_box.pack(fill="both", expand=True, padx=20, pady=(0, 8))
        self.content_box.bind("<KeyRelease>", lambda e: self._on_content_changed())
        # Intercept Tab key to insert 4 spaces
        self.content_box.bind("<Tab>", self._insert_tab_spaces)

        # Bottom Bar: Stats and parameters status
        bottom_bar = ctk.CTkFrame(self.editor_container, fg_color="transparent")
        bottom_bar.pack(fill="x", padx=20, pady=(0, 14))

        self.lbl_param_status = ctk.CTkLabel(
            bottom_bar,
            text="",
            font=FONTS["small"],
            text_color=COLORS["primary"],
            anchor="w",
        )
        self.lbl_param_status.pack(side="left")

        self.lbl_char_count = ctk.CTkLabel(
            bottom_bar,
            text="0 lines, 0 chars",
            font=FONTS["small"],
            text_color=COLORS["text_muted"],
            anchor="e",
        )
        self.lbl_char_count.pack(side="right")

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
            text_color=COLORS["primary"],
        )
        lbl_icon.pack(pady=(0, 8))

        lbl_title = ctk.CTkLabel(
            center_box,
            text="Mnemo Manager",
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
            fg_color=COLORS["secondary"],
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
                text_color=COLORS["primary"],
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
            badge = ctk.CTkLabel(
                self.badges_frame,
                text=f"#{tag}",
                font=FONTS["small"],
                fg_color=COLORS["tag_bg"],
                text_color=COLORS["tag_text"],
                corner_radius=4,
                padx=6,
                pady=1,
            )
            badge.pack(side="left", padx=(0, 4))

    def _on_content_changed(self) -> None:
        self._mark_dirty()
        self._update_stats_and_params()

    def _update_stats_and_params(self) -> None:
        content = self.content_box.get("1.0", "end-1c")
        lines = len(content.splitlines()) if content else 0
        chars = len(content)
        self.lbl_char_count.configure(text=f"{lines} lines, {chars} chars")

        params = extract_parameters(content)
        if params:
            param_names = ", ".join(f"{{{p}}}" for p in params[:4])
            if len(params) > 4:
                param_names += f" +{len(params) - 4}"
            self.lbl_param_status.configure(
                text=f"⚡ {len(params)} param(s): {param_names}"
            )
            self.btn_params.configure(state="normal", fg_color=COLORS["primary"])
        else:
            self.lbl_param_status.configure(text="")
            self.btn_params.configure(state="normal", fg_color=COLORS["secondary"])

    def _on_copy_click(self) -> None:
        content = self.content_box.get("1.0", "end-1c")
        self.clipboard_clear()
        self.clipboard_append(content)

        self.btn_copy.configure(text="✓ Copied!", fg_color=COLORS["success"])
        self.after(
            1600,
            lambda: self.btn_copy.configure(text="📋 Copy", fg_color=COLORS["primary"]),
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
