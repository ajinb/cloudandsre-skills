# Changelog

## 1.1.0 — 2026-11

### Fixed
- All three skills put `version` and `tags` at the top level of their frontmatter, which the
  Agent Skills spec does not allow (the reference validator rejects them). They now live under
  `metadata`.
- `prometheus-alert-explain`'s example told the engineer to prepare a rollback, contradicting
  its own no-remediation rule (#1).

### Added
- `terraform-plan-review` (#6) and `slo-from-metrics-spec` (#7).
- Output schemas (JSON Schema 2020-12) per skill, referenced from `metadata.output-schema` (#3).
- Lint enforces the Agent Skills spec, required sections and metadata, and checks each skill's
  worked example against its schema and guardrails (#2).
- Guardrails as code: no-remediation, no-fabricated-urls, no-proper-names, no-secret-echo,
  no-invented-metrics.
- Eval harness with golden fixtures: `make eval` offline in CI, `make eval-live` against a model (#4).
- MCP server: every skill as a prompt, SKILL.md and schemas as resources; stdio and
  streamable HTTP (#5).
- Installable package (`cloudandsre-skills`) bundling the skills.

All notable changes to cloudandsre-skills are documented here. Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versioning follows [SemVer](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] — 2026-04-29

Initial release. Three production-shaped skills for SRE / cloud reliability work, portable across Claude Code, Claude Desktop, Codex CLI, and any agent runtime that consumes markdown prompts:

- **`prometheus-alert-explain`** — Alertmanager / Prometheus alert payload → structured triage brief (summary, ranked likely causes, ordered triage checklist, false-positive check). No remediation actions; no fabricated runbook URLs; lower confidence on sparse inputs.
- **`incident-postmortem-draft`** — Slack thread or message log → blameless postmortem markdown (timeline, contributing factors, detection gap, response patterns, action items, open questions). Schema-enforced blamelessness — role-based attribution only, no proper names.
- **`waf-pattern-review`** — code, architecture, or design notes → opinionated WAF reliability review (verdict, what it gets right, critical gaps with specific failure modes, nice-to-haves, two-way-vs-one-way-door framing).

Tooling: `scripts/lint_skills.py` validates every `SKILL.md` (frontmatter, required fields, name-matches-directory, description length, non-trivial body); CI runs the lint on every push and PR. Apache-2.0 licensed.
