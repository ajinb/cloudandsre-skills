"""Serve every skill over MCP: each skill is a prompt, and its SKILL.md and output schema
are resources. Any MCP client (Claude Desktop, IDE assistants, agent runtimes) can use the
skills without copying files into each project.

    cloudandsre-skills-mcp                       # stdio (local clients)
    cloudandsre-skills-mcp --transport streamable-http   # hosted
"""

from __future__ import annotations

import argparse
import json

from mcp.server import MCPServer
from mcp.server.mcpserver.prompts.base import Prompt

from .catalog import Skill, load_all


def _make_prompt(skill: Skill) -> Prompt:
    def render(request: str) -> list[dict]:
        return [{"role": "user", "content": f"{skill.body.strip()}\n\n---\n\n{request}"}]

    render.__doc__ = skill.meta.get("description", "")
    return Prompt.from_function(
        render,
        name=skill.name,
        title=skill.name.replace("-", " ").title(),
        description=skill.meta.get("description", ""),
    )


def build_server() -> MCPServer:
    server = MCPServer(
        "cloudandsre-skills",
        instructions="Production-shaped SRE skills. Each prompt takes `request`: the alert, "
        "thread, plan, design or metrics list to work on.",
    )
    skills = {s.name: s for s in load_all() if not s.errors}
    for skill in skills.values():
        server.add_prompt(_make_prompt(skill))

    @server.resource("skill://{name}/SKILL.md", mime_type="text/markdown")
    def skill_markdown(name: str) -> str:
        """The full SKILL.md for a skill."""
        return skills[name].path.read_text(encoding="utf-8")

    @server.resource("skill://{name}/output-schema.json", mime_type="application/json")
    def skill_schema(name: str) -> str:
        """JSON Schema (2020-12) of the skill's parsed output."""
        return json.dumps(skills[name].schema or {}, indent=2)

    return server


def main() -> None:
    parser = argparse.ArgumentParser(prog="cloudandsre-skills-mcp")
    parser.add_argument("--transport", choices=["stdio", "streamable-http"], default="stdio")
    args = parser.parse_args()
    build_server().run(args.transport)


if __name__ == "__main__":
    main()
