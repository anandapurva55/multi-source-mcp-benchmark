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


def _sh(container: str, command: str) -> subprocess.CompletedProcess:
    return subprocess.run(["docker", "exec", container, "bash", "-c", command],
                          check=False, capture_output=True, text=True)


async def _execute_code(config: Path, container: str, code: str) -> str:
    params = load_server(str(config), "code-executor", container)
    async with stdio_client(params) as (r, w), ClientSession(r, w) as session:
        await session.initialize()
        result = await session.call_tool("execute_code", {"code": code})
        assert not result.is_error, result
        return "\n".join(c.text for c in result.content if hasattr(c, "text"))


def test_agent_runs_as_an_unprivileged_user(running: str):
    assert _sh(f"msmb-{running}", "id -u").stdout.strip() == "10001"


def test_only_scratch_is_writable(running: str):
    c = f"msmb-{running}"
    assert _sh(c, "touch /etc/x").returncode != 0, "root filesystem is writable"
    assert _sh(c, "touch /workspace/evidence/x").returncode != 0, "evidence is writable"
    assert _sh(c, "touch /workspace/scratch/ok").returncode == 0, "scratch is not writable"


# One check per scenario that exercises what the agent really does as the unprivileged user:
# read the evidence with code, and (root-cause) read the cloned git history.
SQLITE_CODE = """
import sqlite3
db = sqlite3.connect('file:/workspace/evidence/settlement_export.sqlite?mode=ro', uri=True)
print(db.execute('select count(*) from disbursements').fetchone()[0])
"""
CSV_CODE = """
import csv
rows = list(csv.DictReader(open('/workspace/evidence/run_1_baseline_steadystate.csv')))
print(len(rows))
"""
GIT_CODE = """
import subprocess
cmd = ['git', '-C', '/workspace/relay-config', 'rev-list', '--count', 'HEAD']
print(subprocess.run(cmd, capture_output=True, text=True).stdout.strip())
"""
CODE_CHECKS = {
    "ledger-drift": (SQLITE_CODE, "25"),
    "signal-check": (CSV_CODE, "30"),
    "root-cause": (GIT_CODE, "5"),
}


def test_code_executor_reads_the_evidence_as_the_unprivileged_user(running: str):
    code, expected = CODE_CHECKS[running]
    config = REPO_ROOT / "scenarios" / running / "mcp-servers.json"
    out = asyncio.run(_execute_code(config, f"msmb-{running}", code))
    # The tool replies with JSON; its "output" field holds exactly what the script printed.
    assert json.loads(out)["output"].strip() == expected, out
