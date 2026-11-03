"""Eval harness: golden fixtures per skill, checked offline or against a live model.

Fixtures live in `skills/<name>/evals/*.json`:

    {"input": "...", "golden_output": "...", "expect": {"contains": [...], "confidence": "low"}}

* Offline (default, runs in CI): the golden output must satisfy the skill's output schema,
  guardrails and `expect` assertions. This keeps fixtures and contracts honest.
* Live (`--live`, needs ANTHROPIC_API_KEY): the SKILL.md body is the system prompt, the
  fixture input is the user turn, and the *model's* output is held to the same checks.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path

from .catalog import Skill, load_all
from .contract import check_output, parse_output

DEFAULT_MODEL = "claude-sonnet-5-5"


def check_expectations(output: str, expect: dict) -> list[str]:
    problems = []
    for needle in expect.get("contains", []):
        if needle.lower() not in output.lower():
            problems.append(f"expected output to mention {needle!r}")
    for needle in expect.get("absent", []):
        if re.search(rf"\b{re.escape(needle)}\b", output, re.IGNORECASE):
            problems.append(f"expected output not to mention {needle!r}")
    if "confidence" in expect:
        got = (parse_output(output).get("confidence") or {}).get("level")
        if got != expect["confidence"]:
            problems.append(f"expected confidence {expect['confidence']!r}, got {got!r}")
    return problems


def run_model(skill: Skill, user_input: str, model: str) -> str:
    import anthropic  # only needed for --live

    client = anthropic.Anthropic()
    message = client.messages.create(
        model=model,
        max_tokens=8000,
        system=skill.body,
        messages=[{"role": "user", "content": user_input}],
        output_config={"effort": "low"},
    )
    if message.stop_reason == "refusal":
        return ""
    return "".join(b.text for b in message.content if b.type == "text")


def run(live: bool = False, model: str = DEFAULT_MODEL, only: str | None = None) -> int:
    total = failed = 0
    for skill in load_all():
        if only and skill.name != only:
            continue
        for fixture in sorted((skill.directory / "evals").glob("*.json")):
            case = json.loads(fixture.read_text(encoding="utf-8"))
            output = run_model(skill, case["input"], model) if live else case["golden_output"]
            problems = check_output(skill, output, case["input"])
            problems += check_expectations(output, case.get("expect", {}))
            total += 1
            label = f"{skill.name}/{fixture.stem}"
            if problems:
                failed += 1
                print(f"FAIL {label}")
                for p in problems:
                    print(f"     - {p}")
            else:
                print(f"  ok {label}")
    mode = f"live ({model})" if live else "offline (golden outputs)"
    print(f"\n{total - failed}/{total} eval cases passed, {mode}.")
    return 1 if failed or total == 0 else 0


def main(argv: list[str] | None = None) -> int:
    import argparse

    p = argparse.ArgumentParser(prog="cloudandsre-skills eval")
    p.add_argument("--live", action="store_true", help="run fixtures against a real model")
    p.add_argument("--model", default=os.environ.get("SKILLS_EVAL_MODEL", DEFAULT_MODEL))
    p.add_argument("--skill", help="only this skill")
    args = p.parse_args(argv)
    return run(args.live, args.model, args.skill)


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = ["Path", "check_expectations", "run"]
