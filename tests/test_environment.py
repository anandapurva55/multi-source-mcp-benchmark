"""End-to-end check of the environment layer: image builds, MCP servers launch in the
container, evidence is readable, and the container has no network.

Needs a running Docker daemon, so it is skipped by default. Run with: pytest -m docker
"""
import asyncio
import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "tools"))
from mcp import ClientSession
from mcp.client.stdio import stdio_client
from mcp_probe import load_server

pytestmark = pytest.mark.docker

SCENARIOS = sorted(p.name for p in (REPO_ROOT / "scenarios").iterdir() if p.is_dir())


async def _tools(config: Path, server: str, container: str) -> set[str]:
    params = load_server(str(config), server, container)
    async with stdio_client(params) as (r, w), ClientSession(r, w) as session:
        await session.initialize()
        return {t.name for t in (await session.list_tools()).tools}


@pytest.fixture(params=SCENARIOS, scope="module")
def running(request):
    name = request.param
    env_dir = REPO_ROOT / "scenarios" / name / "environment"
    subprocess.run(["docker", "compose", "up", "-d", "--build", "--wait"], cwd=env_dir, check=True)
    try:
        yield name
    finally:
        subprocess.run(["docker", "compose", "down", "-v"], cwd=env_dir, check=False)


def test_declared_tools_exist_in_the_container(running: str):
    config = REPO_ROOT / "scenarios" / running / "mcp-servers.json"
    cfg = json.loads(config.read_text())
    exposed = {s["name"]: asyncio.run(_tools(config, s["name"], f"msmb-{running}")) for s in cfg["servers"]}
    policy = cfg["tool_policy"]
    for key in ("required", "distractors_same_server", "distractors_other_server"):
        for ref in policy.get(key, []):
            server, tool = ref.split(":")
            assert tool in exposed[server], f"{ref} is declared but not exposed"


def test_container_has_no_network(running: str):
    probe = "import urllib.request as u; u.urlopen('https://github.com', timeout=3)"
    result = subprocess.run(["docker", "exec", f"msmb-{running}", "python", "-c", probe],
                            check=False, capture_output=True, text=True)
    assert result.returncode != 0, "container can reach the internet"
