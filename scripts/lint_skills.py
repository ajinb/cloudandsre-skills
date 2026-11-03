"""Lint every skills/<name>/SKILL.md. Kept for existing docs and CI; the logic lives in
src/cloudandsre_skills/lint.py. Run from the repo root: `python scripts/lint_skills.py`."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from cloudandsre_skills.lint import main

if __name__ == "__main__":
    sys.exit(main())
