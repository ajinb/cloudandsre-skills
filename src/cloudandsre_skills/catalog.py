"""Discover and parse SKILL.md files (Agent Skills format: YAML frontmatter + markdown body)."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from functools import cached_property
from pathlib import Path
from typing import Any

import yaml

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n(.*)$", re.DOTALL)
HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*#*\s*$")
FENCE_RE = re.compile(r"^\s*(```|~~~)")


def skills_root() -> Path:
    """`skills/` in a source checkout, or the copy bundled into the wheel."""
    here = Path(__file__).resolve()
    for candidate in (here.parent / "skills", here.parents[2] / "skills"):
        if candidate.is_dir():
            return candidate
    raise FileNotFoundError("cannot locate the skills/ directory")


def split_sections(markdown: str) -> list[tuple[int, str, str]]:
    """Fence-aware split into (level, heading, content). Text before the first heading is
    returned with level 0 and an empty heading."""
    sections: list[tuple[int, str, list[str]]] = [(0, "", [])]
    in_fence = False
    for line in markdown.splitlines():
        if FENCE_RE.match(line):
            in_fence = not in_fence
        m = None if in_fence else HEADING_RE.match(line)
        if m:
            sections.append((len(m.group(1)), m.group(2).strip(), []))
        else:
            sections[-1][2].append(line)
    return [(lvl, head, "\n".join(body).strip()) for lvl, head, body in sections]


def strip_fence(text: str) -> str:
    lines = text.strip().splitlines()
    if lines and FENCE_RE.match(lines[0]) and FENCE_RE.match(lines[-1]):
        return "\n".join(lines[1:-1])
    return text.strip()


@dataclass
class Skill:
    path: Path
    meta: dict[str, Any]
    body: str
    errors: list[str] = field(default_factory=list)

    @property
    def name(self) -> str:
        return self.path.parent.name

    @property
    def directory(self) -> Path:
        return self.path.parent

    @cached_property
    def sections(self) -> list[tuple[int, str, str]]:
        return split_sections(self.body)

    @property
    def guardrails(self) -> set[str]:
        return set(str((self.meta.get("metadata") or {}).get("guardrails", "")).split())

    @property
    def schema(self) -> dict[str, Any] | None:
        ref = (self.meta.get("metadata") or {}).get("output-schema")
        if not ref:
            return None
        return json.loads((self.directory / ref).read_text(encoding="utf-8"))

    def section(self, contains: str) -> tuple[int, str, str] | None:
        for sec in self.sections:
            if sec[0] == 2 and contains.lower() in sec[1].lower():
                return sec
        return None

    def example(self) -> tuple[str, str] | None:
        """(input, output) from the `## ... example ...` section, or None."""
        start = next(
            (i for i, s in enumerate(self.sections) if s[0] == 2 and "example" in s[1].lower()),
            None,
        )
        if start is None:
            return None
        # The example runs until the next level-2 heading; deeper headings belong to the output.
        chunk = []
        for lvl, head, content in self.sections[start:]:
            if lvl == 2 and chunk:
                break
            chunk.append(content if not chunk else f"{'#' * lvl} {head}\n{content}")
        text = "\n".join(chunk)
        m = re.search(r"\*\*Input[^*]*\*\*:?\s*(.*?)\*\*Output[^*]*\*\*:?\s*(.*)", text, re.DOTALL)
        if not m:
            return None
        return strip_fence(m.group(1).strip().strip('"')), strip_fence(m.group(2))


def load_skill(skill_md: Path) -> Skill:
    text = skill_md.read_text(encoding="utf-8")
    m = FRONTMATTER_RE.match(text)
    if not m:
        return Skill(skill_md, {}, text, ["SKILL.md must start with YAML frontmatter (--- delimiters)"])
    try:
        meta = yaml.safe_load(m.group(1)) or {}
    except yaml.YAMLError as e:
        return Skill(skill_md, {}, m.group(2), [f"invalid YAML frontmatter: {e}"])
    return Skill(skill_md, meta, m.group(2))


def load_all(root: Path | None = None) -> list[Skill]:
    root = root or skills_root()
    return [load_skill(d / "SKILL.md") for d in sorted(p for p in root.iterdir() if p.is_dir())
            if (d / "SKILL.md").exists()]
