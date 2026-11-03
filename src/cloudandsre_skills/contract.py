"""Turn a skill's markdown output into data, validate it, and enforce its guardrails."""

from __future__ import annotations

import re
from typing import Any

from jsonschema import Draft202012Validator

from .catalog import split_sections, strip_fence

LIST_ITEM_RE = re.compile(r"^\s*(?:[-*]|\d+[.)])\s+(.*)$")
CONFIDENCE_RE = re.compile(r"^Confidence:\s*(high|medium|low)\b\s*[—–-]?\s*(.*)$", re.IGNORECASE | re.MULTILINE)

# Imperative remediation phrasing an investigative skill must not use.
REMEDIATION_RE = re.compile(
    r"\b(restart|reboot|roll ?back|rollback|redeploy|re-deploy|scale (?:up|down|out|in)|"
    r"kill (?:the )?(?:pod|process|job)|delete (?:the )?(?:pod|node|deployment)|"
    r"fail ?over|drain (?:the )?node|terraform apply|kubectl (?:delete|scale|rollout restart))\b",
    re.IGNORECASE,
)
URL_RE = re.compile(r"https?://[^\s)>\]`'\"]+")
SPEAKER_RE = re.compile(r"^\s*\[?\d{1,2}:\d{2}(?::\d{2})?\]?\s+([A-Za-z][\w.-]{1,30}):", re.MULTILINE)
METRIC_RE = re.compile(r"\b([a-zA-Z_:][a-zA-Z0-9_:]*)(?=\{|\[\d)")
PROMQL_FUNCS = {"rate", "irate", "increase", "sum", "avg", "max", "min", "count", "histogram_quantile",
                "by", "without", "on", "ignoring", "and", "or", "unless", "delta", "deriv", "abs",
                "avg_over_time", "max_over_time", "min_over_time", "sum_over_time", "absent"}
SECRET_RE = re.compile(r"(?:AKIA|ASIA)[0-9A-Z]{16}|sk-ant-[\w-]{20,}|gh[pousr]_\w{36,}|xox[abposr]-[\w-]{10,}")


def _parse_table(block: str) -> list[dict[str, str]]:
    rows = [r.strip().strip("|").split("|") for r in block.splitlines() if r.strip().startswith("|")]
    rows = [[c.strip() for c in r] for r in rows if not all(set(c.strip()) <= set("-: ") for c in r)]
    if len(rows) < 2:
        return []
    header = rows[0]
    return [dict(zip(header, r, strict=False)) for r in rows[1:]]


def parse_output(markdown: str) -> dict[str, Any]:
    """Headings become keys. A section that is only a list becomes a list of strings; a table
    becomes a list of row dicts; anything else is a string. An H1 becomes `title`, and a
    `Confidence: <level> — <reason>` line becomes `confidence`."""
    markdown = strip_fence(markdown)
    out: dict[str, Any] = {}
    m = CONFIDENCE_RE.search(markdown)
    if m:
        out["confidence"] = {"level": m.group(1).lower(), "reason": m.group(2).strip()}
        markdown = CONFIDENCE_RE.sub("", markdown)
    for level, heading, content in split_sections(markdown):
        if level == 0:
            if content:
                out["preamble"] = content
            continue
        if level == 1:
            out["title"] = heading
            if content:
                out["preamble"] = content
            continue
        lines = [ln for ln in content.splitlines() if ln.strip()]
        if lines and all(ln.lstrip().startswith("|") for ln in lines):
            out[heading] = _parse_table(content)
        elif lines and all(LIST_ITEM_RE.match(ln) for ln in lines):
            out[heading] = [LIST_ITEM_RE.match(ln).group(1).strip() for ln in lines]
        else:
            out[heading] = content
    return out


def schema_errors(parsed: dict[str, Any], schema: dict[str, Any]) -> list[str]:
    validator = Draft202012Validator(schema)
    return [
        f"{'/'.join(map(str, e.absolute_path)) or '<root>'}: {e.message}"
        for e in sorted(validator.iter_errors(parsed), key=lambda e: list(e.absolute_path))
    ]


def guardrail_violations(guardrails: set[str], output: str, skill_input: str = "") -> list[str]:
    problems: list[str] = []
    if "no-remediation" in guardrails:
        # Section titles such as "Confirm before approving" are fine; imperative advice is not.
        for m in REMEDIATION_RE.finditer(output):
            problems.append(f"no-remediation: output suggests '{m.group(0)}'")
    if "no-fabricated-urls" in guardrails:
        allowed = set(URL_RE.findall(skill_input))
        for url in URL_RE.findall(output):
            if url.rstrip(".,;") not in {u.rstrip(".,;") for u in allowed}:
                problems.append(f"no-fabricated-urls: {url} is not in the input")
    if "no-proper-names" in guardrails:
        for name in sorted(set(SPEAKER_RE.findall(skill_input))):
            if re.search(rf"\b{re.escape(name)}\b", output, re.IGNORECASE):
                problems.append(f"no-proper-names: speaker '{name}' appears in the output")
    if "no-secret-echo" in guardrails:
        for secret in SECRET_RE.findall(output):
            problems.append(f"no-secret-echo: credential-shaped string {secret[:8]}… in output")
    if "no-invented-metrics" in guardrails:
        # Recommending a metric the user lacks is the job of a Gaps section, so skip it.
        scanned = "\n".join(
            content for _lvl, head, content in split_sections(output) if "gap" not in head.lower()
        )
        known = set(METRIC_RE.findall(skill_input)) | set(re.findall(r"\b[a-z_:][a-z0-9_:]+\b", skill_input))
        defined = set(re.findall(r"`([a-z_:][a-z0-9_:<>]*)`", output))
        for metric in sorted(set(METRIC_RE.findall(scanned))):
            if metric in PROMQL_FUNCS or metric in known:
                continue
            if any(metric.startswith(d.split("<")[0]) for d in defined if "<" in d) or metric in defined:
                continue
            problems.append(f"no-invented-metrics: '{metric}' is not in the input")
    return problems


def check_output(skill, output: str, skill_input: str = "") -> list[str]:
    problems: list[str] = []
    schema = skill.schema
    if schema is not None:
        problems += schema_errors(parse_output(output), schema)
    problems += guardrail_violations(skill.guardrails, output, skill_input)
    return problems
