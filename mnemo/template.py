"""Template parameter detection and substitution for shell commands and snippets."""

from __future__ import annotations

import re

# Matches {param}, {{param}}, and <param> (where param is an identifier)
PARAM_PATTERN = re.compile(
    r"\{\{([a-zA-Z0-9_\-]+)\}\}|\{([a-zA-Z0-9_\-]+)\}|<([a-zA-Z0-9_\-]+)>"
)


def extract_parameters(text: str) -> list[str]:
    """Extract ordered unique parameter names from a text snippet.

    Recognizes formats: {var}, {{var}}, <var>.
    """
    if not text:
        return []

    seen: set[str] = set()
    params: list[str] = []

    for match in PARAM_PATTERN.finditer(text):
        name = match.group(1) or match.group(2) or match.group(3)
        if name and name not in seen:
            seen.add(name)
            params.append(name)

    return params


def substitute_parameters(text: str, values: dict[str, str]) -> str:
    """Replace parameter occurrences with their assigned values."""
    if not text or not values:
        return text

    def replacer(match: re.Match[str]) -> str:
        name = match.group(1) or match.group(2) or match.group(3)
        if name in values and values[name] != "":
            return values[name]
        return match.group(0)

    return PARAM_PATTERN.sub(replacer, text)
