# Contributing to cloudandsre-skills

Thanks for considering a contribution. Skills here are meant to be *opinionated* — each one encodes a real production discipline (no remediation actions, no proper names in postmortems, no fabricated URLs). PRs that water down those guardrails will get pushed back; PRs that tighten them are welcome.

## Skill design principles

1. **One job per skill.** A skill that does "explain alerts and draft postmortems and review architectures" is three skills wearing a trench coat. Split it.
2. **Output contract is non-negotiable.** Every skill specifies the exact section structure of its output. The agent's job is to fill it in. Free-form output makes a skill useless to chain.
3. **Discipline section is mandatory.** Every skill must have a "Discipline" or "Rules" section that says what the skill *will not* do. The book this brand is built around is about reliability — these skills are reliability-shaped, not chat-shaped.
4. **No emoji, no boldface theater.** Operators are reading at 2 a.m. A skill that opens with 🚨🔥 is rude.
5. **Examples are mandatory.** Every skill ships with at least one tiny input → output example so a reader can verify the skill is doing what its description claims.
6. **Stay small.** A skill body that's longer than ~250 lines is doing too much. Either split it or move the long parts to a referenced doc.

## Adding a new skill

1. `mkdir skills/<your-skill-name>` (kebab-case).
2. Write `skills/<your-skill-name>/SKILL.md` with the frontmatter:
   ```yaml
   ---
   name: <your-skill-name>          # must match the directory name
   description: <when to invoke + one-line behavior, < 1024 chars>
   license: Apache-2.0
   version: 0.1.0
   tags: [comma-separated]
   ---
   ```
3. Body sections we expect (in this order): `When to invoke`, `Output contract`, `Discipline`, at least one `Example`.
4. Run `python scripts/lint_skills.py` locally — CI will too.
5. PR with a short rationale: what need does this skill cover, and what existing skill almost covered it.

## Compatibility

`SKILL.md` is portable across:
- **Claude Code** (drop into `.claude/skills/<name>/SKILL.md` or invoke directly via the Skill tool)
- **Claude Desktop** (via the Skills feature)
- **Codex** and most agent SDKs that consume markdown prompts (the body is the prompt)

When a runtime requires extra metadata, prefer adding optional frontmatter keys with sensible defaults rather than diverging the body.

## License

By contributing, you agree your contribution is licensed under Apache-2.0 (see `LICENSE`).
