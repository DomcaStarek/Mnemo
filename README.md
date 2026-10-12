# ⚡ Mnemo

**Mnemo** is a sleek, modern, offline-first desktop application built with Python and `customtkinter` designed as a local manager for notes, shell commands, and code snippets.

---

## ✨ Features

- **Modern Responsive GUI**: Clean 3-pane layout powered by `customtkinter` with full Dark / Light / System theme support.
- **Local JSON Storage**: Automatically persists all data to `mnemo_data.json` with atomic writes, corruption safeguards, and auto-creation of `[]` on first startup.
- **Instant Search & Tag Filtering**:
  - Full-text search across titles, content, and tags in real time.
  - Interactive sidebar tag cloud with per-tag counts and one-click filtering.
  - Multi-criteria sorting (Recently Updated, Recently Created, Title A-Z, Title Z-A).
- **One-Click Quick Copy**:
  - One-click copy buttons directly on each list card and in the editor toolbar with animated `✓ Copied!` visual confirmations.
- **Template Parameter Fill & Run (`{param}`, `<param>`, `{{param}}`)**:
  - Automatically identifies variables in command templates (e.g. `{port}`, `{image}`, `<repo>`).
  - Opens an interactive substitution modal to fill in parameter values and copy or execute the rendered command.
- **Built-in Terminal Command Runner**:
  - Safely test and run shell commands in PowerShell, CMD, or Bash with real-time streaming output, duration tracking, return codes, and termination controls.
- **Full Library Backup & Portability**:
  - Export and Import JSON files (with non-destructive merge support).
  - Export your entire snippet library to formatted Markdown (`.md`).
  - Optional "Load Starter Samples" button to quickly explore with pre-filled Git, Docker, PowerShell, Python, and Bash recipes.
- **Ergonomic Monospace Editor**:
  - Designed for code and shell scripts with monospace font (`Consolas`).
  - Proper `Tab` key handling (inserts 4 spaces instead of losing widget focus).
  - Character, word, and line count indicators.
  - Clear "● Unsaved changes" vs "✓ Saved" status badges.

---

## ⌨️ Keyboard Shortcuts

| Shortcut | Action |
| :--- | :--- |
| `Ctrl + N` | Create a new snippet |
| `Ctrl + S` | Save current snippet |
| `Ctrl + F` | Focus search bar |
| `Ctrl + Shift + C` | Copy current snippet content to clipboard |
| `Ctrl + D` | Duplicate current snippet |
| `Delete` / `Del` | Delete selected snippet (prompts confirmation) |
| `Enter` or `Y` | Confirm deletion in popup dialog |
| `Esc` or `N` | Cancel deletion in popup dialog |

---

## 🗄️ Data Schema

Data is stored in `mnemo_data.json`:

```json
[
  {
    "id": "e7b0e14d-91b5-4b05-a08e-f14d82f7c00e",
    "title": "Docker: Run PostgreSQL Container",
    "description": "Starts an isolated PostgreSQL 16 container with credentials and exposed port 5432.",
    "tags": [
      "docker",
      "database",
      "postgres"
    ],
    "content": "docker run -d --name {container_name} \\\n  -e POSTGRES_PASSWORD={password} \\\n  -p 5432:5432 \\\n  postgres:16-alpine",
    "created_at": "2026-10-12T11:42:00.000000+00:00",
    "updated_at": "2026-10-12T11:42:00.000000+00:00"
  }
]
```

---

## 🚀 Getting Started

### 1. Requirements
- Python 3.10+
- Dependencies: `customtkinter`, `darkdetect`, `Pillow`

### 2. Installation
```bash
pip install -r requirements.txt
```

### 3. Launching Mnemo
```bash
# Launch with default mnemo_data.json in current directory
python main.py

# Or specify a custom data file
python main.py --file path/to/my_notes.json
```

---

## 🧪 Running Tests

Mnemo includes a comprehensive automated test suite with pytest:

```bash
pytest
```
