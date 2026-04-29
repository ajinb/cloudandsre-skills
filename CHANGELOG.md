# Changelog

All notable changes to cloudandsre-skills are documented here. Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versioning follows [SemVer](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] — 2026-04-29

Initial release. Three production-shaped skills for SRE / cloud reliability work, portable across Claude Code, Claude Desktop, Codex CLI, and any agent runtime that consumes markdown prompts:

- **`prometheus-alert-explain`** — Alertmanager / Prometheus alert payload → structured triage brief (summary, ranked likely causes, ordered triage checklist, false-positive check). No remediation actions; no fabricated runbook URLs; lower confidence on sparse inputs.
- **`incident-postmortem-draft`** — Slack thread or message log → blameless postmortem markdown (timeline, contributing factors, detection gap, response patterns, action items, open questions). Schema-enforced blamelessness — role-based attribution only, no proper names.
- **`waf-pattern-review`** — code, architecture, or design notes → opinionated WAF reliability review (verdict, what it gets right, critical gaps with specific failure modes, nice-to-haves, two-way-vs-one-way-door framing).

Tooling: `scripts/lint_skills.py` validates every `SKILL.md` (frontmatter, required fields, name-matches-directory, description length, non-trivial body); CI runs the lint on every push and PR. Apache-2.0 licensed.
