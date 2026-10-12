"""Storage manager for Mnemo.

Handles JSON persistence, atomic writes, searching, filtering, and import/export.
"""

from __future__ import annotations

import json
import logging
import os
import shutil
import tempfile
from collections import Counter
from collections.abc import Callable
from pathlib import Path
from typing import Any

from mnemo.models import Note, clean_tags, current_iso_timestamp

logger = logging.getLogger(__name__)

DEFAULT_FILENAME = "mnemo_data.json"


class StorageManager:
    """Manages local JSON persistence for notes and snippets."""

    def __init__(self, file_path: Path | str | None = None) -> None:
        if file_path is None:
            # Default to mnemo_data.json in the current working directory
            self.file_path = Path.cwd() / DEFAULT_FILENAME
        else:
            self.file_path = Path(file_path).resolve()

        self._notes: list[Note] = []
        self._listeners: list[Callable[[], None]] = []
        self.initialize_storage()

    @property
    def notes(self) -> list[Note]:
        """Return a shallow copy of loaded notes."""
        return list(self._notes)

    def add_change_listener(self, callback: Callable[[], None]) -> None:
        """Register a callback that fires whenever data changes."""
        self._listeners.append(callback)

    def _notify_listeners(self) -> None:
        """Notify all registered listeners of a change."""
        for callback in self._listeners:
            try:
                callback()
            except Exception:
                logger.exception("Error in storage change listener")

    def initialize_storage(self) -> None:
        """Ensure the storage file exists; if not, create it with an empty list []."""
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.file_path.exists():
            self._write_raw_data([])
            self._notes = []
        else:
            self.load()

    def _write_raw_data(self, data: list[dict[str, Any]]) -> None:
        """Atomically write raw JSON data to the file."""
        parent_dir = self.file_path.parent
        fd, temp_file_path = tempfile.mkstemp(
            prefix="mnemo_", suffix=".tmp", dir=parent_dir
        )
        try:
            with open(fd, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            os.replace(temp_file_path, self.file_path)
        except Exception:
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
            raise

    def load(self) -> list[Note]:
        """Load notes from the JSON file."""
        if not self.file_path.exists():
            self.initialize_storage()
            return []

        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if not content:
                    data = []
                else:
                    data = json.loads(content)

            if not isinstance(data, list):
                logger.warning("JSON content is not a list. Backing up and resetting.")
                self._create_backup()
                data = []
                self._write_raw_data(data)

            self._notes = [
                Note.from_dict(item) for item in data if isinstance(item, dict)
            ]
        except Exception as e:
            logger.error("Failed to load JSON storage: %s. Creating backup.", e)
            self._create_backup()
            self._notes = []
            self._write_raw_data([])

        return self.notes

    def save(self) -> None:
        """Save the current in-memory notes to the JSON file atomically."""
        raw_list = [note.to_dict() for note in self._notes]
        self._write_raw_data(raw_list)
        self._notify_listeners()

    def _create_backup(self) -> Path | None:
        """Create a backup of the corrupted or existing storage file."""
        if self.file_path.exists():
            backup_path = self.file_path.with_suffix(
                f".bak_{int(os.path.getmtime(self.file_path))}"
            )
            try:
                shutil.copy2(self.file_path, backup_path)
                return backup_path
            except Exception as e:
                logger.error("Failed to create backup: %s", e)
        return None

    def add(
        self,
        title: str,
        content: str = "",
        description: str = "",
        tags: list[str] | str | None = None,
        note_id: str | None = None,
    ) -> Note:
        """Add a new note/snippet and save."""
        note = Note(
            id=note_id or "",
            title=title.strip() or "Untitled",
            description=description.strip(),
            content=content,
            tags=clean_tags(tags) if tags is not None else [],
        )
        self._notes.insert(0, note)
        self.save()
        return note

    def get(self, note_id: str) -> Note | None:
        """Get a note by its ID."""
        for note in self._notes:
            if note.id == note_id:
                return note
        return None

    def update(
        self,
        note_id: str,
        title: str | None = None,
        description: str | None = None,
        content: str | None = None,
        tags: list[str] | str | None = None,
    ) -> Note | None:
        """Update an existing note and save."""
        note = self.get(note_id)
        if not note:
            return None

        changed = False
        if title is not None and title.strip() != note.title:
            note.title = title.strip() or "Untitled"
            changed = True
        if description is not None and description.strip() != note.description:
            note.description = description.strip()
            changed = True
        if content is not None and content != note.content:
            note.content = content
            changed = True
        if tags is not None:
            new_tags = clean_tags(tags)
            if new_tags != note.tags:
                note.tags = new_tags
                changed = True

        if changed:
            note.touch()
            self.save()
        return note

    def delete(self, note_id: str) -> bool:
        """Delete a note by its ID."""
        initial_len = len(self._notes)
        self._notes = [n for n in self._notes if n.id != note_id]
        if len(self._notes) < initial_len:
            self.save()
            return True
        return False

    def duplicate(self, note_id: str) -> Note | None:
        """Duplicate an existing note with a new ID and timestamp."""
        existing = self.get(note_id)
        if not existing:
            return None

        dup_title = f"{existing.title} (Copy)"
        dup_note = Note(
            title=dup_title,
            description=existing.description,
            content=existing.content,
            tags=list(existing.tags),
        )
        # Insert right after the duplicated note or at the top
        index = self._notes.index(existing)
        self._notes.insert(index + 1, dup_note)
        self.save()
        return dup_note

    def get_tags(self) -> dict[str, int]:
        """Return a dictionary of all unique tags with their item counts."""
        counter: Counter[str] = Counter()
        for note in self._notes:
            for tag in note.tags:
                counter[tag] += 1
        return dict(sorted(counter.items(), key=lambda x: (-x[1], x[0].lower())))

    def search(
        self,
        query: str = "",
        tag: str | None = None,
        sort_by: str = "updated_desc",
    ) -> list[Note]:
        """Search and filter notes based on text query, tag filter, and sort order.

        Parameters:
            query: Substring search matching title, description, content, or tags (case-insensitive).
            tag: Exact tag match (case-insensitive).
            sort_by: 'updated_desc', 'updated_asc', 'created_desc', 'created_asc',
                     'title_asc', 'title_desc'.
        """
        results = list(self._notes)

        # 1. Tag filter
        if tag and tag.strip():
            normalized_tag = tag.lstrip("#").strip().lower()
            results = [
                n for n in results if any(t.lower() == normalized_tag for t in n.tags)
            ]

        # 2. Text query filter
        q = query.strip().lower()
        if q:
            results = [
                n
                for n in results
                if (
                    q in n.title.lower()
                    or q in n.description.lower()
                    or q in n.content.lower()
                    or any(q in t.lower() for t in n.tags)
                )
            ]

        # 3. Sorting
        if sort_by == "updated_desc":
            results.sort(key=lambda n: n.updated_at, reverse=True)
        elif sort_by == "updated_asc":
            results.sort(key=lambda n: n.updated_at, reverse=False)
        elif sort_by == "created_desc":
            results.sort(key=lambda n: n.created_at, reverse=True)
        elif sort_by == "created_asc":
            results.sort(key=lambda n: n.created_at, reverse=False)
        elif sort_by == "title_asc":
            results.sort(key=lambda n: n.title.lower(), reverse=False)
        elif sort_by == "title_desc":
            results.sort(key=lambda n: n.title.lower(), reverse=True)

        return results

    def export_json(self, target_path: Path | str) -> int:
        """Export all notes to a specified JSON file path."""
        target = Path(target_path).resolve()
        target.parent.mkdir(parents=True, exist_ok=True)
        data = [note.to_dict() for note in self._notes]
        with open(target, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return len(data)

    def import_json(self, source_path: Path | str, merge: bool = True) -> int:
        """Import notes from an external JSON file.

        If merge is True, appends and updates without wiping existing items.
        If merge is False, replaces all current items.
        Returns the number of imported items.
        """
        source = Path(source_path).resolve()
        with open(source, "r", encoding="utf-8") as f:
            data = json.load(f)

        if not isinstance(data, list):
            raise TypeError("Import file must contain a JSON array of notes.")

        imported_notes = [
            Note.from_dict(item) for item in data if isinstance(item, dict)
        ]

        if not merge:
            self._notes = imported_notes
        else:
            existing_ids = {n.id for n in self._notes}
            for note in imported_notes:
                if note.id in existing_ids:
                    # Update existing
                    for i, cur in enumerate(self._notes):
                        if cur.id == note.id:
                            self._notes[i] = note
                            break
                else:
                    self._notes.append(note)
                    existing_ids.add(note.id)

        self.save()
        return len(imported_notes)

    def export_markdown(self, target_path: Path | str) -> int:
        """Export notes as a consolidated Markdown document."""
        target = Path(target_path).resolve()
        target.parent.mkdir(parents=True, exist_ok=True)

        lines = [
            "# Mnemo Library Export",
            f"*Generated on {current_iso_timestamp()}*",
            f"*Total Items: {len(self._notes)}*",
            "\n---\n",
        ]

        for note in self._notes:
            tags_str = (
                " ".join(f"`#{t}`" for t in note.tags) if note.tags else "_No tags_"
            )
            lines.append(f"## {note.title}")
            if note.description:
                lines.append(f"> {note.description}\n")
            lines.append(f"**Tags:** {tags_str} | **Updated:** {note.updated_at}\n")
            lines.append("```")
            lines.append(note.content)
            lines.append("```\n")
            lines.append("---\n")

        with open(target, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        return len(self._notes)

    def load_starter_samples(self) -> int:
        """Load a curated set of sample shell commands and snippets."""
        samples = [
            {
                "title": "Git: Revert Last Commit Keeping Changes",
                "description": "Undoes the last commit while keeping modified files staged in your working directory.",
                "tags": ["git", "vcs", "workflow"],
                "content": "git reset --soft HEAD~1",
            },
            {
                "title": "Docker: Run PostgreSQL Container",
                "description": "Spins up an isolated PostgreSQL 16 Alpine container with credentials and exposed port 5432.",
                "tags": ["docker", "database", "postgres"],
                "content": (
                    "docker run -d --name {container_name} \\\n"
                    "  -e POSTGRES_PASSWORD={password} \\\n"
                    "  -e POSTGRES_DB={dbname} \\\n"
                    "  -p 5432:5432 \\\n"
                    "  postgres:16-alpine"
                ),
            },
            {
                "title": "PowerShell: Search Files by Extension Recursively",
                "description": "Recursively searches directory tree for matching file patterns and lists paths and sizes.",
                "tags": ["powershell", "windows", "shell"],
                "content": "Get-ChildItem -Path {folder_path} -Recurse -Filter *.{ext} | Select-Object FullName, Length",
            },
            {
                "title": "Python: Quick Local HTTP Server",
                "description": "Spins up a lightweight local static web server in the current working directory.",
                "tags": ["python", "server", "utility"],
                "content": "python -m http.server {port}",
            },
            {
                "title": "cURL: POST JSON Request with Bearer Auth",
                "description": "Sends an authenticated HTTP POST request with JSON payload and bearer authorization token.",
                "tags": ["curl", "api", "network"],
                "content": (
                    'curl -X POST "{url}" \\\n'
                    '  -H "Content-Type: application/json" \\\n'
                    '  -H "Authorization: Bearer {token}" \\\n'
                    '  -d \'{"key": "value"}\''
                ),
            },
            {
                "title": "Bash: Kill Process on Specific Port",
                "description": "Finds PID listening on a specified network port and forcefully terminates it.",
                "tags": ["bash", "linux", "network"],
                "content": "lsof -ti:{port} | xargs kill -9",
            },
        ]

        count = 0
        for s in samples:
            self.add(
                title=s["title"],
                description=s.get("description", ""),
                content=s["content"],
                tags=s["tags"],
            )
            count += 1
        return count
