"""Minimal YAML front-matter parsing for OpenWiki pages.

Avoids adding a new runtime dependency (e.g. `python-frontmatter`) by
reusing `pyyaml`, which is already an `agilev` dependency.
"""

from __future__ import annotations

import yaml

_DELIMITER = "---"


def parse_frontmatter(text: str) -> tuple[dict, str]:
    """Split a Markdown document into (front-matter dict, body).

    Args:
        text: Full contents of a Markdown file.

    Returns:
        Tuple of (front_matter, body). `front_matter` is an empty dict if
        the document has no `---`-delimited YAML front-matter block.
    """
    stripped = text.lstrip("\ufeff")
    if not stripped.startswith(_DELIMITER):
        return {}, text

    lines = stripped.splitlines()
    if not lines or lines[0].strip() != _DELIMITER:
        return {}, text

    end_index = None
    for i in range(1, len(lines)):
        if lines[i].strip() == _DELIMITER:
            end_index = i
            break

    if end_index is None:
        return {}, text

    front_matter_text = "\n".join(lines[1:end_index])
    body = "\n".join(lines[end_index + 1 :])

    try:
        data = yaml.safe_load(front_matter_text) or {}
    except yaml.YAMLError:
        return {}, text

    if not isinstance(data, dict):
        return {}, text

    return data, body
