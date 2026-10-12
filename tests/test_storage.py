"""Tests for StorageManager persistence, CRUD, search, and import/export."""

import json
from pathlib import Path

from mnemo.storage import StorageManager


def test_storage_auto_create_empty_list(tmp_path: Path):
    json_path = tmp_path / "test_data.json"
    assert not json_path.exists()

    storage = StorageManager(json_path)
    assert json_path.exists()

    with open(json_path, "r", encoding="utf-8") as f:
        content = json.load(f)
    assert content == []
    assert storage.notes == []


def test_storage_crud(tmp_path: Path):
    json_path = tmp_path / "test_data.json"
    storage = StorageManager(json_path)

    # 1. Add
    note1 = storage.add(
        title="Note 1",
        description="A test note",
        content="echo 'Hello'",
        tags=["shell"],
    )
    assert note1.id is not None
    assert note1.description == "A test note"
    assert len(storage.notes) == 1
    assert storage.get(note1.id) == note1

    # Reload from disk to verify persistence
    storage2 = StorageManager(json_path)
    assert len(storage2.notes) == 1
    assert storage2.notes[0].title == "Note 1"
    assert storage2.notes[0].description == "A test note"

    # 2. Update
    updated = storage.update(
        note1.id,
        title="Updated Note 1",
        description="Updated description",
        content="echo 'World'",
    )
    assert updated is not None
    assert updated.title == "Updated Note 1"
    assert updated.description == "Updated description"
    assert updated.content == "echo 'World'"

    # 3. Duplicate
    dup = storage.duplicate(note1.id)
    assert dup is not None
    assert "Copy" in dup.title
    assert dup.description == "Updated description"
    assert dup.id != note1.id
    assert len(storage.notes) == 2

    # 4. Delete
    deleted = storage.delete(note1.id)
    assert deleted is True
    assert len(storage.notes) == 1
    assert storage.get(note1.id) is None


def test_storage_search_and_filters(tmp_path: Path):
    json_path = tmp_path / "test_data.json"
    storage = StorageManager(json_path)

    storage.add(
        title="Git Rebase",
        description="Interactive rebase on main branch",
        content="git rebase -i HEAD~3",
        tags=["git", "vcs"],
    )
    storage.add(
        title="Docker Compose Up",
        description="Starts docker compose stack in background",
        content="docker compose up -d",
        tags=["docker", "dev"],
    )
    storage.add(
        title="Python Virtualenv",
        description="Creates virtual environment in current directory",
        content="python -m venv venv",
        tags=["python", "dev"],
    )

    # Search by text in title
    results = storage.search(query="rebase")
    assert len(results) == 1
    assert results[0].title == "Git Rebase"

    # Search by text in description
    results = storage.search(query="background")
    assert len(results) == 1
    assert results[0].title == "Docker Compose Up"

    # Search by text in content
    results = storage.search(query="compose up")
    assert len(results) == 1
    assert results[0].title == "Docker Compose Up"

    # Filter by tag
    results = storage.search(tag="dev")
    assert len(results) == 2

    # Combined query and tag
    results = storage.search(query="virtualenv", tag="dev")
    assert len(results) == 1
    assert results[0].title == "Python Virtualenv"

    # Tags dictionary with counts
    tags_count = storage.get_tags()
    assert tags_count["dev"] == 2
    assert tags_count["git"] == 1
    assert tags_count["docker"] == 1


def test_storage_export_import(tmp_path: Path):
    json_path = tmp_path / "test_data.json"
    storage = StorageManager(json_path)

    storage.add(title="N1", content="C1", tags=["t1"])
    storage.add(title="N2", content="C2", tags=["t2"])

    # Export JSON
    export_path = tmp_path / "exported.json"
    count = storage.export_json(export_path)
    assert count == 2
    assert export_path.exists()

    # Import into fresh storage
    new_json_path = tmp_path / "new_data.json"
    storage_new = StorageManager(new_json_path)
    assert len(storage_new.notes) == 0

    imported_count = storage_new.import_json(export_path)
    assert imported_count == 2
    assert len(storage_new.notes) == 2

    # Export Markdown
    md_path = tmp_path / "exported.md"
    md_count = storage.export_markdown(md_path)
    assert md_count == 2
    assert md_path.exists()
    with open(md_path, "r", encoding="utf-8") as f:
        md_text = f.read()
    assert "## N1" in md_text
    assert "## N2" in md_text
