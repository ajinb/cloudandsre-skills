"""Validate every skills/<name>/SKILL.md is well-formed.

Checks:
- File exists at skills/<name>/SKILL.md
- Frontmatter parses as YAML
- Required keys present: name, description
- `name` matches the directory name (single source of truth)
- `description` is non-empty and under 1024 chars (Anthropic skills limit)
- Body has non-trivial content after frontmatter

Run: `python scripts/lint_skills.py` from the repo root.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

try:
    import yaml
except ModuleNotFoundError:
    print("error: PyYAML is required. Install with: pip install pyyaml", file=sys.stderr)
    sys.exit(2)

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = REPO_ROOT / "skills"
FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n(.*)$", re.DOTALL)
DESCRIPTION_MAX = 1024


def lint_one(skill_dir: Path) -> list[str]:
    errors: list[str] = []
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        return [f"{skill_dir.name}: missing SKILL.md"]

    text = skill_md.read_text()
    m = FRONTMATTER_RE.match(text)
    if not m:
        return [f"{skill_dir.name}: SKILL.md must start with YAML frontmatter (--- delimiters)"]

    try:
        meta = yaml.safe_load(m.group(1)) or {}
    except yaml.YAMLError as e:
        return [f"{skill_dir.name}: invalid YAML frontmatter: {e}"]

    body = m.group(2).strip()

    for required in ("name", "description"):
        if not meta.get(required):
            errors.append(f"{skill_dir.name}: frontmatter missing required field `{required}`")

    if meta.get("name") and meta["name"] != skill_dir.name:
        errors.append(
            f"{skill_dir.name}: frontmatter `name: {meta['name']}` does not match directory name"
        )

    desc = meta.get("description", "")
    if desc and len(desc) > DESCRIPTION_MAX:
        errors.append(
            f"{skill_dir.name}: description is {len(desc)} chars; max is {DESCRIPTION_MAX}"
        )

    if len(body) < 100:
        errors.append(f"{skill_dir.name}: body is too short ({len(body)} chars); skills should have substantive instructions")

    return errors


def main() -> int:
    if not SKILLS_DIR.is_dir():
        print(f"error: {SKILLS_DIR} is not a directory", file=sys.stderr)
        return 2

    skill_dirs = sorted(d for d in SKILLS_DIR.iterdir() if d.is_dir())
    if not skill_dirs:
        print("error: no skills found under skills/", file=sys.stderr)
        return 2

    all_errors: list[str] = []
    for d in skill_dirs:
        errs = lint_one(d)
        if errs:
            all_errors.extend(errs)
        else:
            print(f"  ok  {d.name}")

    if all_errors:
        print("\nLint failed:", file=sys.stderr)
        for e in all_errors:
            print(f"  - {e}", file=sys.stderr)
        return 1

    print(f"\nAll {len(skill_dirs)} skills passed lint.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
