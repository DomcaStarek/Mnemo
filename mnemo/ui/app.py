"""Main application window for Mnemo."""

from __future__ import annotations

import os
from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk

from mnemo.models import Note
from mnemo.storage import DEFAULT_FILENAME, StorageManager
from mnemo.ui.dialogs import CommandRunnerDialog, ConfirmDialog, ParameterFillDialog
from mnemo.ui.editor_view import EditorView
from mnemo.ui.list_view import ListView
from mnemo.ui.sidebar import SidebarView


class MnemoApp(ctk.CTk):
    """Main Mnemo desktop window."""

    def __init__(self, data_file: Path | str | None = None) -> None:
        super().__init__()

        # Appearance configuration
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # Window settings
        self.title("Mnemo — Notes, Snippets & Command Manager")
        self.geometry("1200x750")
        self.minsize(920, 560)

        # Storage initialization
        self.storage = StorageManager(data_file or DEFAULT_FILENAME)

        # Active state tracking
        self.current_note: Note | None = None

        self._build_layout()
        self._bind_shortcuts()

        # Initial data population
        self._refresh_all()

        # If notes exist, select the first one; otherwise show empty placeholder
        if self.storage.notes:
            self._select_note(self.storage.notes[0])
        else:
            self.editor_view.show_empty_placeholder()

    def _build_layout(self) -> None:
        # Main root layout container
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=0)  # Sidebar
        self.grid_columnconfigure(1, weight=0)  # List View
        self.grid_columnconfigure(2, weight=1)  # Editor View

        # 1. Sidebar (Col 0)
        self.sidebar_view = SidebarView(
            self,
            storage=self.storage,
            on_new_snippet=self.create_new_snippet,
            on_select_tag=self._on_sidebar_tag_selected,
            on_import_json=self._handle_import_json,
            on_export_json=self._handle_export_json,
            on_export_markdown=self._handle_export_markdown,
            on_load_samples=self._handle_load_samples,
            width=250,
        )
        self.sidebar_view.grid(row=0, column=0, sticky="nsew")

        # 2. List View (Col 1)
        self.list_view = ListView(
            self,
            storage=self.storage,
            on_select_note=self._select_note,
            on_tag_cleared=lambda: self.sidebar_view._clear_tag_filter(),
            width=360,
        )
        self.list_view.grid(row=0, column=1, sticky="nsew")

        # 3. Editor View (Col 2)
        self.editor_view = EditorView(
            self,
            on_save=self._save_note,
            on_delete=self._prompt_delete_note,
            on_duplicate=self._duplicate_note,
            on_open_params=self._open_parameter_dialog,
            on_run_command=self._open_command_runner,
        )
        self.editor_view.grid(row=0, column=2, sticky="nsew")

    def _bind_shortcuts(self) -> None:
        """Register application-wide keyboard shortcuts."""
        self.bind("<Control-n>", lambda e: self.create_new_snippet())
        self.bind("<Control-N>", lambda e: self.create_new_snippet())

        self.bind("<Control-s>", lambda e: self._on_shortcut_save())
        self.bind("<Control-S>", lambda e: self._on_shortcut_save())

        self.bind("<Control-f>", lambda e: self._on_shortcut_search())
        self.bind("<Control-F>", lambda e: self._on_shortcut_search())

        self.bind("<Control-Shift-C>", lambda e: self._on_shortcut_copy())
        self.bind("<Control-Shift-c>", lambda e: self._on_shortcut_copy())

        self.bind("<Control-d>", lambda e: self._on_shortcut_duplicate())
        self.bind("<Control-D>", lambda e: self._on_shortcut_duplicate())

        # Delete shortcut bindings
        self.bind("<Delete>", lambda e: self._on_shortcut_delete())
        self.bind("<KP_Delete>", lambda e: self._on_shortcut_delete())
        self.bind("<Alt-Delete>", lambda e: self._force_shortcut_delete())
        self.bind("<Shift-Delete>", lambda e: self._force_shortcut_delete())
        self.bind("<Escape>", lambda e: self._on_shortcut_escape())

    def _is_text_editing_widget(self, widget) -> bool:
        """Check if the given widget is an editable Entry or Text widget."""
        import tkinter as tk

        return isinstance(widget, (tk.Entry, tk.Text))

    def _on_shortcut_delete(self) -> None:
        """Trigger note deletion via Delete key if user is not actively editing text."""
        if not self.current_note:
            return

        focused = self.focus_get()
        if self._is_text_editing_widget(focused):
            # Allow default forward character delete in entry / textbox
            return

        self._prompt_delete_note(self.current_note.id)

    def _force_shortcut_delete(self) -> None:
        """Force trigger note deletion (e.g. Shift+Delete or Alt+Delete) even if inside text fields."""
        if self.current_note:
            self._prompt_delete_note(self.current_note.id)

    def _on_shortcut_escape(self) -> None:
        """Escape blurs focus back to main window."""
        focused = self.focus_get()
        if self._is_text_editing_widget(focused):
            self.focus_set()

    def _on_shortcut_save(self) -> None:
        self.editor_view.save_current()

    def _on_shortcut_search(self) -> None:
        self.list_view.focus_search()

    def _on_shortcut_copy(self) -> None:
        if self.current_note:
            self.clipboard_clear()
            self.clipboard_append(self.current_note.content)

    def _on_shortcut_duplicate(self) -> None:
        if self.current_note:
            self._duplicate_note(self.current_note.id)

    def _refresh_all(self) -> None:
        """Synchronize both list view and sidebar with current storage state."""
        self.list_view.refresh_list()
        self.sidebar_view.refresh_tags()

    def _select_note(self, note: Note) -> None:
        """Select a note, update card selection, and display in editor."""
        self.current_note = note
        self.list_view.set_selected_id(note.id)
        self.editor_view.load_note(note)

    def create_new_snippet(self) -> None:
        """Create a new blank snippet, select it, and focus editor."""
        active_tag = self.sidebar_view.selected_tag
        initial_tags = [active_tag] if active_tag else []

        new_note = self.storage.add(
            title="New Snippet",
            description="",
            content="",
            tags=initial_tags,
        )
        self._refresh_all()
        self._select_note(new_note)
        self.editor_view.title_entry.focus_set()
        self.editor_view.title_entry.select_range(0, "end")

    def _save_note(
        self,
        note_id: str,
        title: str,
        description: str,
        content: str,
        tags: list[str],
    ) -> None:
        """Save changes to the current note and refresh cards/tags."""
        updated = self.storage.update(
            note_id=note_id,
            title=title,
            description=description,
            content=content,
            tags=tags,
        )
        if updated:
            self.current_note = updated
            self._refresh_all()
            self.list_view.set_selected_id(updated.id)

    def _prompt_delete_note(self, note_id: str) -> None:
        """Confirm and delete a note."""
        note = self.storage.get(note_id)
        if not note:
            return

        def do_delete():
            self.storage.delete(note_id)
            self._refresh_all()
            remaining = self.storage.notes
            if remaining:
                self._select_note(remaining[0])
            else:
                self.current_note = None
                self.list_view.set_selected_id(None)
                self.editor_view.show_empty_placeholder()

        ConfirmDialog(
            self,
            title="Delete Snippet",
            message=f'Are you sure you want to permanently delete "{note.title}"?',
            confirm_text="Yes",
            cancel_text="No",
            is_destructive=True,
            on_confirm=do_delete,
        )

    def _duplicate_note(self, note_id: str) -> None:
        """Duplicate a snippet and select the duplicate."""
        dup = self.storage.duplicate(note_id)
        if dup:
            self._refresh_all()
            self._select_note(dup)

    def _on_sidebar_tag_selected(self, tag: str | None) -> None:
        """Handle tag filter selection from the sidebar."""
        self.list_view.set_active_tag(tag)

    def _open_parameter_dialog(self, content: str) -> None:
        """Open the parameter filler modal."""
        ParameterFillDialog(
            self,
            template_content=content,
            on_run_command=self._open_command_runner,
        )

    def _open_command_runner(self, command: str) -> None:
        """Open the command runner modal."""
        CommandRunnerDialog(self, command=command)

    def _handle_import_json(self) -> None:
        """Import notes from an external JSON file."""
        file_path = filedialog.askopenfilename(
            parent=self,
            title="Import Snippets from JSON",
            filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")],
        )
        if not file_path:
            return

        try:
            count = self.storage.import_json(file_path, merge=True)
            self._refresh_all()
            if self.storage.notes:
                self._select_note(self.storage.notes[0])
            messagebox.showinfo(
                "Import Successful", f"Successfully imported {count} items."
            )
        except Exception as e:
            messagebox.showerror("Import Failed", f"Could not import JSON: {e}")

    def _handle_export_json(self) -> None:
        """Export all notes to a JSON file."""
        file_path = filedialog.asksaveasfilename(
            parent=self,
            title="Export Snippets to JSON",
            defaultextension=".json",
            filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")],
            initialfile="mnemo_export.json",
        )
        if not file_path:
            return

        try:
            count = self.storage.export_json(file_path)
            messagebox.showinfo(
                "Export Successful",
                f"Exported {count} items to {os.path.basename(file_path)}.",
            )
        except Exception as e:
            messagebox.showerror("Export Failed", f"Could not export JSON: {e}")

    def _handle_export_markdown(self) -> None:
        """Export all notes to a Markdown file."""
        file_path = filedialog.asksaveasfilename(
            parent=self,
            title="Export Snippets to Markdown",
            defaultextension=".md",
            filetypes=[("Markdown Files", "*.md"), ("All Files", "*.*")],
            initialfile="mnemo_library.md",
        )
        if not file_path:
            return

        try:
            count = self.storage.export_markdown(file_path)
            messagebox.showinfo(
                "Export Successful",
                f"Exported {count} items to {os.path.basename(file_path)}.",
            )
        except Exception as e:
            messagebox.showerror("Export Failed", f"Could not export Markdown: {e}")

    def _handle_load_samples(self) -> None:
        """Load starter sample snippets."""

        def do_load():
            count = self.storage.load_starter_samples()
            self._refresh_all()
            if self.storage.notes:
                self._select_note(self.storage.notes[0])
            messagebox.showinfo(
                "Samples Loaded", f"Added {count} sample shell commands and snippets."
            )

        ConfirmDialog(
            self,
            title="Load Starter Samples",
            message="Would you like to add curated starter snippets (Git, Docker, PowerShell, Python, Bash) to your library?",
            confirm_text="Load Samples",
            is_destructive=False,
            on_confirm=do_load,
        )
