# cloudandsre-skills

> Opinionated, production-shaped skills for AI agents doing SRE and cloud-reliability work. Portable across Claude Code, Claude Desktop, Codex CLI, and any runtime that consumes a markdown prompt.

[![Lint](https://github.com/ajinb/cloudandsre-skills/actions/workflows/lint.yml/badge.svg)](https://github.com/ajinb/cloudandsre-skills/actions/workflows/lint.yml) [![License: Apache-2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)

A skill here is a single `SKILL.md` file with a YAML frontmatter block and a body that specifies *when to invoke*, an *output contract*, *discipline / guardrails*, and at least one example. Each skill encodes a real production discipline — no remediation actions, no proper names in postmortems, no fabricated runbook URLs — so the agent's output is something a senior SRE would sign off on, not something a chatbot generates.

## What's in here

| Skill | When to invoke | What it produces |
|---|---|---|
| [`prometheus-alert-explain`](skills/prometheus-alert-explain/SKILL.md) | User pastes Alertmanager JSON or asks "what does this alert mean" | Structured triage brief: summary, ranked likely causes, triage checklist, false-positive check, confidence |
| [`incident-postmortem-draft`](skills/incident-postmortem-draft/SKILL.md) | User pastes a Slack incident thread or message log | Blameless postmortem markdown: timeline (role-based attribution), contributing factors, detection gap, action items, open questions |
| [`waf-pattern-review`](skills/waf-pattern-review/SKILL.md) | User shares code, architecture, or a design doc and asks for a reliability review | Verdict + what it gets right + critical gaps (with specific failure modes) + nice-to-haves + two-way-door framing |

## How to use

### Claude Code

Drop the skills into your project's `.claude/skills/` directory:

```bash
git clone https://github.com/ajinb/cloudandsre-skills.git
mkdir -p .claude/skills
cp -r cloudandsre-skills/skills/* .claude/skills/
```

Claude Code will discover them on the next session start. Invoke via the Skill tool, or by asking the assistant something that matches the `description` field.

### Claude Desktop

Use the Desktop **Skills** feature: import each `SKILL.md` (or zip the `skills/` directory and import the bundle).

### Codex CLI / other agent runtimes

The body of each `SKILL.md` is plain markdown that doubles as a system prompt. Either:

- Reference the file directly as a prompt input, or
- Copy the body into your runtime's prompt-template format. The frontmatter is metadata; the body is the prompt.

### As a curl-able prompt

```bash
curl -sS https://raw.githubusercontent.com/ajinb/cloudandsre-skills/main/skills/prometheus-alert-explain/SKILL.md | sed -n '/^---$/,/^---$/!p'
```

(That strips the frontmatter and gives you just the prompt body.)

## Design principles

These are not chatbot prompts; they're operator tools. Every skill in this library obeys the same rules:

- **One job per skill.** A skill that does three things is three skills wearing a trench coat.
- **Output contract first.** Every skill specifies the *exact* sections it produces. The agent's job is to fill them in. Free-form output makes a skill useless to chain into a pipeline.
- **Discipline section is mandatory.** Every skill says what it *will not* do. No remediation actions in `prometheus-alert-explain`. No proper names in `incident-postmortem-draft`. No fabricated dashboards in either.
- **No emoji, no boldface theater.** Operators read these at 2 a.m. A skill that opens with 🚨🔥 is rude.
- **Examples are mandatory.** Every skill ships with at least one input → output example.
- **Stay simple.** A skill body longer than ~250 lines is doing too much. Split it.

## Adding a new skill

See [CONTRIBUTING.md](CONTRIBUTING.md). Short version:

```bash
mkdir skills/my-new-skill
$EDITOR skills/my-new-skill/SKILL.md     # frontmatter + body — see existing skills for shape
python scripts/lint_skills.py            # validates frontmatter and body before you push
```

CI lints every PR.

## Companion content

- The blog post explaining the philosophy: [cloudandsre.com/blog](https://cloudandsre.com/blog)
- Tools that pair with these skills:
  - [`alert-explainer`](https://github.com/ajinb/alert-explainer) — service form of `prometheus-alert-explain`
  - [`incident-scribe`](https://github.com/ajinb/incident-scribe) — service form of `incident-postmortem-draft`
  - [`sre-ai-toolkit`](https://github.com/ajinb/sre-ai-toolkit) — CLI scripts for the same family of jobs
- The book this brand is built around: *Self-Healing Infrastructure: Building Autonomous Cloud Systems with AI* (cloudandsre.com)

## License

[Apache-2.0](LICENSE).
