"""Exercise the MCP server through the SDK's in-memory client."""

import json

import pytest
from mcp import Client

from cloudandsre_skills.catalog import load_all
from cloudandsre_skills.mcp_server import build_server

pytestmark = pytest.mark.anyio


@pytest.fixture
def anyio_backend():
    return "asyncio"


async def test_every_skill_is_a_prompt():
    async with Client(build_server()) as client:
        listed = await client.list_prompts()
        names = {p.name for p in listed.prompts}
        assert names == {s.name for s in load_all()}
        prompt = next(p for p in listed.prompts if p.name == "terraform-plan-review")
        assert [a.name for a in prompt.arguments] == ["request"]


async def test_get_prompt_embeds_the_skill_and_the_request():
    async with Client(build_server()) as client:
        result = await client.get_prompt("prometheus-alert-explain", {"request": "ALERT JSON"})
        text = result.messages[0].content.text
        assert "## Discipline" in text and text.rstrip().endswith("ALERT JSON")


async def test_schema_resource():
    async with Client(build_server()) as client:
        res = await client.read_resource("skill://slo-from-metrics-spec/output-schema.json")
        schema = json.loads(res.contents[0].text)
        assert "Burn-rate alerts" in schema["required"]
