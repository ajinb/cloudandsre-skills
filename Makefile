.PHONY: lint eval eval-live test mcp

lint:            ## Agent Skills spec + repository rules + example contracts
	python scripts/lint_skills.py

eval:            ## golden fixtures vs schemas, guardrails and expectations (offline)
	cloudandsre-skills-eval

eval-live:       ## the same fixtures against a real model (needs ANTHROPIC_API_KEY)
	cloudandsre-skills-eval --live

test:
	pytest -q

mcp:             ## serve every skill as an MCP prompt over stdio
	cloudandsre-skills-mcp
