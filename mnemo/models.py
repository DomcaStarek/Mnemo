"""Data models for Mnemo."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


def current_iso_timestamp() -> str:
    """Return the current UTC time in ISO-8601 format."""
    return datetime.now(timezone.utc).isoformat()


def clean_tags(tags: Any) -> list[str]:
    """Clean and normalize a list or string of tags."""
    if tags is None:
        return []
    if isinstance(tags, str):
        raw_list = [t.strip() for t in tags.split(",") if t.strip()]
    elif isinstance(tags, (list, tuple, set)):
        raw_list = [str(t).strip() for t in tags if str(t).strip()]
    else:
        return []

    # Deduplicate while preserving order
    seen = set()
    cleaned = []
    for tag in raw_list:
        normalized = tag.lstrip("#").strip()
        if normalized and normalized.lower() not in seen:
            seen.add(normalized.lower())
            cleaned.append(normalized)
    return cleaned


@dataclass
class Note:
    """Represents a note, shell command, or code snippet."""

    title: str
    content: str = ""
    description: str = ""
    tags: list[str] = field(default_factory=list)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: str = field(default_factory=current_iso_timestamp)
    updated_at: str = field(default_factory=current_iso_timestamp)

    def __post_init__(self) -> None:
        if not self.id:
            self.id = str(uuid.uuid4())
        self.tags = clean_tags(self.tags)
        if not self.created_at:
            self.created_at = current_iso_timestamp()
        if not self.updated_at:
            self.updated_at = self.created_at

    def touch(self) -> None:
        """Update the updated_at timestamp to now."""
        self.updated_at = current_iso_timestamp()

    def to_dict(self) -> dict[str, Any]:
        """Convert to JSON-serializable dictionary matching exact schema."""
        return {
            "id": str(self.id),
            "title": str(self.title),
            "description": str(self.description),
            "tags": list(self.tags),
            "content": str(self.content),
            "created_at": str(self.created_at),
            "updated_at": str(self.updated_at),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Note:
        """Create a Note instance from a dictionary."""
        note_id = str(data.get("id") or str(uuid.uuid4()))
        title = str(data.get("title", "Untitled"))
        description = str(data.get("description", ""))
        content = str(data.get("content", ""))
        tags = clean_tags(data.get("tags", []))
        created_at = str(data.get("created_at") or current_iso_timestamp())
        updated_at = str(data.get("updated_at") or created_at)

        return cls(
            id=note_id,
            title=title,
            description=description,
            content=content,
            tags=tags,
            created_at=created_at,
            updated_at=updated_at,
        )

    def human_relative_time(self) -> str:
        """Return a human-readable relative time string for updated_at."""
        try:
            # Handle ISO string with or without Z/offset
            ts_str = self.updated_at.replace("Z", "+00:00")
            dt = datetime.fromisoformat(ts_str)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            now = datetime.now(timezone.utc)
            diff = now - dt

            seconds = int(diff.total_seconds())
            if seconds < 0:
                return "Just now"
            if seconds < 60:
                return "Just now"
            minutes = seconds // 60
            if minutes < 60:
                return f"{minutes}m ago"
            hours = minutes // 60
            if hours < 24:
                return f"{hours}h ago"
            days = hours // 24
            if days == 1:
                return "Yesterday"
            if days < 7:
                return f"{days}d ago"
            if days < 30:
                weeks = days // 7
                return f"{weeks}w ago"
            return dt.strftime("%b %d, %Y")
        except Exception:
            return (
                self.updated_at[:10] if len(self.updated_at) >= 10 else self.updated_at
            )
