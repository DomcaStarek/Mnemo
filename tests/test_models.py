"""Tests for Note data model."""

from mnemo.models import Note, clean_tags


def test_clean_tags():
    assert clean_tags(None) == []
    assert clean_tags("") == []
    assert clean_tags("tag1, tag2, #tag3, tag1") == ["tag1", "tag2", "tag3"]
    assert clean_tags(["tag1", "#tag2", "  tag1  "]) == ["tag1", "tag2"]


def test_note_creation():
    note = Note(title="Git Status", content="git status", tags=["git", "vcs"])
    assert note.title == "Git Status"
    assert note.description == ""
    assert note.content == "git status"
    assert note.tags == ["git", "vcs"]
    assert note.id is not None
    assert len(note.id) > 0
    assert note.created_at is not None
    assert note.updated_at is not None

    note_with_desc = Note(title="A", description="Does something", content="B")
    assert note_with_desc.description == "Does something"


def test_note_to_and_from_dict():
    original = Note(
        id="test-uuid-1234",
        title="Docker PS",
        description="List active docker containers",
        content="docker ps -a",
        tags=["docker", "containers"],
        created_at="2026-10-12T10:00:00Z",
        updated_at="2026-10-12T11:00:00Z",
    )
    d = original.to_dict()
    assert d == {
        "id": "test-uuid-1234",
        "title": "Docker PS",
        "description": "List active docker containers",
        "tags": ["docker", "containers"],
        "content": "docker ps -a",
        "created_at": "2026-10-12T10:00:00Z",
        "updated_at": "2026-10-12T11:00:00Z",
    }

    reconstructed = Note.from_dict(d)
    assert reconstructed.id == original.id
    assert reconstructed.title == original.title
    assert reconstructed.description == original.description
    assert reconstructed.content == original.content
    assert reconstructed.tags == original.tags
    assert reconstructed.created_at == original.created_at
    assert reconstructed.updated_at == original.updated_at


def test_note_touch():
    note = Note(title="Test", updated_at="2020-01-01T00:00:00Z")
    old_time = note.updated_at
    note.touch()
    assert note.updated_at != old_time
