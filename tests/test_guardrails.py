"""The checks must catch the violations they exist for, including the one issue #1 found."""

import copy
from pathlib import Path

from cloudandsre_skills.catalog import load_all, load_skill
from cloudandsre_skills.contract import guardrail_violations, parse_output, schema_errors
from cloudandsre_skills.lint import lint_skill

SKILLS = {s.name: s for s in load_all()}


def test_original_rollback_example_is_caught():
    old = "4. If the regression is in v412, prepare a rollback; do not execute without IC sign-off."
    assert guardrail_violations({"no-remediation"}, old)
    assert not guardrail_violations({"no-remediation"}, "4. Compare the v412 deploy diff.")


def test_fabricated_url_is_caught_but_input_urls_are_fine():
    inp = 'annotations: {"runbook_url": "https://runbooks.example.com/a"}'
    assert not guardrail_violations({"no-fabricated-urls"}, "Open https://runbooks.example.com/a", inp)
    assert guardrail_violations({"no-fabricated-urls"}, "See https://wiki.example.com/b", inp)


def test_speaker_names_must_not_leak_into_a_postmortem():
    thread = "[14:22] sarah: paged\n[14:24] mike: deploying fix"
    assert guardrail_violations({"no-proper-names"}, "Sarah acknowledged the page.", thread)
    assert not guardrail_violations({"no-proper-names"}, "The on-call engineer acked.", thread)


def test_invented_metric_is_caught_outside_gaps():
    inp = 'http_requests_total{code="..."}'
    out = "### SLIs\n- `sum(rate(made_up_total[5m]))`\n\n### Gaps\n- add `latency_bucket{le}`"
    problems = guardrail_violations({"no-invented-metrics"}, out, inp)
    assert problems == ["no-invented-metrics: 'made_up_total' is not in the input"]


def test_secret_echo_is_caught():
    assert guardrail_violations({"no-secret-echo"}, "password is AKIAIOSFODNN7EXAMPLE")


def test_parse_output_handles_lists_tables_title_and_confidence():
    parsed = parse_output(
        "# Incident Postmortem — x\n\n## Timeline\n| Time (UTC) | Event |\n|---|---|\n"
        "| 14:10 | fired |\n\n### Likely causes\n1. a\n2. b\n\nConfidence: low — sparse"
    )
    assert parsed["title"] == "Incident Postmortem — x"
    assert parsed["Timeline"] == [{"Time (UTC)": "14:10", "Event": "fired"}]
    assert parsed["Likely causes"] == ["a", "b"]
    assert parsed["confidence"] == {"level": "low", "reason": "sparse"}


def test_schema_rejects_missing_sections():
    schema = SKILLS["prometheus-alert-explain"].schema
    errors = schema_errors(parse_output("### Summary\nonly this"), schema)
    assert any("Likely causes" in e for e in errors)


def test_non_spec_frontmatter_field_fails_lint(tmp_path: Path):
    src = SKILLS["waf-pattern-review"]
    d = tmp_path / "waf-pattern-review"
    (d / "assets").mkdir(parents=True)
    (d / "assets" / "output-schema.json").write_text((src.directory / "assets/output-schema.json").read_text())
    (d / "SKILL.md").write_text(src.path.read_text().replace("license:", "tags: [x]\nlicense:", 1))
    errors = lint_skill(load_skill(d / "SKILL.md"))
    assert any("`tags` is not in the Agent Skills spec" in e for e in errors)


def test_every_shipped_skill_passes_lint():
    for skill in SKILLS.values():
        assert lint_skill(copy.deepcopy(skill)) == [], skill.name
