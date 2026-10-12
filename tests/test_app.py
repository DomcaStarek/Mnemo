"""Integration tests for Mnemo GUI and App lifecycle."""

from pathlib import Path

from mnemo.ui.app import MnemoApp


def test_app_lifecycle_and_creation(tmp_path: Path):
    json_path = tmp_path / "mnemo_test.json"
    assert not json_path.exists()

    # Instantiate MnemoApp
    app = MnemoApp(data_file=json_path)
    app.withdraw()  # keep hidden during test

    # Verify auto-creation of empty list []
    assert json_path.exists()
    assert len(app.storage.notes) == 0

    # Test creating a new snippet
    app.create_new_snippet()
    assert len(app.storage.notes) == 1
    new_note = app.storage.notes[0]
    assert new_note.title == "New Snippet"
    assert app.current_note is not None
    assert app.current_note.id == new_note.id

    # Test updating note via editor
    app.editor_view.title_entry.delete(0, "end")
    app.editor_view.title_entry.insert(0, "Docker Build Command")
    app.editor_view.desc_entry.delete(0, "end")
    app.editor_view.desc_entry.insert(0, "Builds Docker image from current directory")
    app.editor_view.tags_entry.delete(0, "end")
    app.editor_view.tags_entry.insert(0, "docker, devops")
    app.editor_view.content_box.delete("1.0", "end")
    app.editor_view.content_box.insert("1.0", "docker build -t {image_name}:{tag} .")

    app.editor_view.save_current()
    assert app.current_note.title == "Docker Build Command"
    assert app.current_note.description == "Builds Docker image from current directory"
    assert "docker" in app.current_note.tags
    assert "devops" in app.current_note.tags

    # Test duplication
    app._duplicate_note(app.current_note.id)
    assert len(app.storage.notes) == 2
    assert "Copy" in app.storage.notes[1].title

    # Test search filtering in ListView
    app.list_view.search_entry.delete(0, "end")
    app.list_view.search_entry.insert(0, "Docker")
    matching = app.list_view.refresh_list()
    assert len(matching) == 2

    # Test tag filtering in ListView
    app.list_view.set_active_tag("docker")
    matching = app.list_view.refresh_list()
    assert len(matching) == 2

    app.list_view.set_active_tag("nonexistent")
    matching = app.list_view.refresh_list()
    assert len(matching) == 0

    app.list_view.set_active_tag(None)

    # Test Delete shortcut
    initial_count = len(app.storage.notes)
    app.focus_set()
    app._on_shortcut_delete()
    # ConfirmDialog opened; confirm it
    for child in app.winfo_children():
        from mnemo.ui.dialogs import ConfirmDialog

        if isinstance(child, ConfirmDialog):
            child._confirm_and_close()
            break
    assert len(app.storage.notes) == initial_count - 1

    # Clean up app
    app.destroy()
