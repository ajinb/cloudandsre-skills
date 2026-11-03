"""Lint every skill against the Agent Skills spec and this repository's production rules.

Spec (agentskills.io): `name` 1-64 chars of [a-z0-9-], no leading/trailing/double hyphen,
matches its directory; `description` 1-1024 chars; `compatibility` <= 500 chars; `metadata`
a string-to-string map; no other top-level fields.

Repository rules: `license` and `metadata.version`/`tags`/`guardrails`/`output-schema` set;
sections When to invoke, Output contract, Discipline and Example present; the example's output
validates against the skill's output schema and obeys the skill's guardrails.
"""

from __future__ import annotations

import re

from .catalog import Skill, load_all
from .contract import check_output

SPEC_FIELDS = {"name", "description", "license", "compatibility", "metadata", "allowed-tools"}
NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
REQUIRED_SECTIONS = ("When to invoke", "Output contract", "Discipline", "Example")
REQUIRED_METADATA = ("version", "tags", "guardrails", "output-schema")
KNOWN_GUARDRAILS = {"no-remediation", "no-fabricated-urls", "no-proper-names", "no-secret-echo",
                    "no-invented-metrics"}


def lint_skill(skill: Skill) -> list[str]:
    errors = list(skill.errors)
    if errors:
        return errors
    meta = skill.meta

    for extra in sorted(set(meta) - SPEC_FIELDS):
        errors.append(f"frontmatter field `{extra}` is not in the Agent Skills spec; move it under `metadata`")
    name = meta.get("name", "")
    if not name:
        errors.append("frontmatter missing `name`")
    elif len(name) > 64 or not NAME_RE.match(name):
        errors.append(f"`name: {name}` must be 1-64 chars of a-z, 0-9 and single hyphens")
    elif name != skill.name:
        errors.append(f"`name: {name}` does not match directory `{skill.name}`")
    desc = meta.get("description", "")
    if not desc:
        errors.append("frontmatter missing `description`")
    elif len(desc) > 1024:
        errors.append(f"description is {len(desc)} chars; max is 1024")
    if len(str(meta.get("compatibility", ""))) > 500:
        errors.append("compatibility exceeds 500 chars")
    md = meta.get("metadata") or {}
    if not isinstance(md, dict) or not all(isinstance(v, str) for v in md.values()):
        errors.append("`metadata` must map string keys to string values (quote versions)")
        md = {}

    if not meta.get("license"):
        errors.append("repository rule: `license` is required")
    for key in REQUIRED_METADATA:
        if not md.get(key):
            errors.append(f"repository rule: `metadata.{key}` is required")
    unknown = skill.guardrails - KNOWN_GUARDRAILS
    if unknown:
        errors.append(f"unknown guardrail(s) {sorted(unknown)}; known: {sorted(KNOWN_GUARDRAILS)}")
    for section in REQUIRED_SECTIONS:
        if skill.section(section) is None:
            errors.append(f"repository rule: missing a `## {section}` section")
    if len(skill.body.strip()) < 400:
        errors.append("body is too short to be a production skill")

    if md.get("output-schema") and not (skill.directory / md["output-schema"]).exists():
        errors.append(f"output schema {md['output-schema']} does not exist")
        return errors
    example = skill.example()
    if example is None:
        errors.append("could not find **Input** / **Output** in the example section")
    else:
        errors += [f"example: {p}" for p in check_output(skill, example[1], example[0])]
    return errors


def main() -> int:
    skills = load_all()
    if not skills:
        print("error: no skills found under skills/")
        return 2
    failed = 0
    for skill in skills:
        errs = lint_skill(skill)
        if errs:
            failed += 1
            print(f"FAIL {skill.name}")
            for e in errs:
                print(f"     - {e}")
        else:
            print(f"  ok {skill.name}")
    print(f"\n{len(skills) - failed}/{len(skills)} skills passed lint.")
    return 1 if failed else 0
