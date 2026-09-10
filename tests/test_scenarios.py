"""Structural and dry-run checks for every scenario, run in CI on every push."""
import json
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
SCENARIOS_DIR = REPO_ROOT / "scenarios"
SCENARIO_NAMES = sorted(p.name for p in SCENARIOS_DIR.iterdir() if p.is_dir())


@pytest.fixture(params=SCENARIO_NAMES)
def scenario_dir(request) -> Path:
    return SCENARIOS_DIR / request.param


def test_brief_is_present_and_nonempty(scenario_dir: Path):
    brief = scenario_dir / "brief.md"
    assert brief.exists()
    assert len(brief.read_text().strip()) > 0


def test_mcp_servers_config_is_well_formed(scenario_dir: Path):
    config = json.loads((scenario_dir / "mcp-servers.json").read_text())
    assert config["servers"], "at least one MCP server must be declared"
    for server in config["servers"]:
        assert "name" in server and "command" in server and "args" in server
    policy = config["tool_policy"]
    assert policy["required"], "at least one required tool must be declared"


def test_environment_has_docker_compose_and_evidence(scenario_dir: Path):
    env_dir = scenario_dir / "environment"
    assert (env_dir / "docker-compose.yml").exists()
    evidence_dir = env_dir / "evidence"
    assert evidence_dir.is_dir()
    assert any(evidence_dir.iterdir()), "evidence/ must not be empty"


def test_reference_answer_is_present_and_nonempty(scenario_dir: Path):
    answer = scenario_dir / "solution" / "REFERENCE_ANSWER.md"
    assert answer.exists()
    assert len(answer.read_text().strip()) > 0


def test_generator_script_is_present(scenario_dir: Path):
    assert (scenario_dir / "solution" / "generate_evidence.py").exists()


def test_claims_are_well_formed_and_equally_weighted(scenario_dir: Path):
    data = yaml.safe_load((scenario_dir / "evaluation" / "claims.yaml").read_text())
    claims = data["claims"]
    assert len(claims) >= 5, "a scenario should have enough claims for real partial credit"
    ids = [c["id"] for c in claims]
    assert len(ids) == len(set(ids)), "claim ids must be unique"
    for claim in claims:
        assert claim["description"].strip()
        assert claim["points"] == 3, "claims should carry the repo's standard equal weight"


def test_grade_dry_run_succeeds_against_the_reference_answer(scenario_dir: Path):
    result = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "tools" / "grade.py"),
            "--claims", str(scenario_dir / "evaluation" / "claims.yaml"),
            "--answer", str(scenario_dir / "solution" / "REFERENCE_ANSWER.md"),
            "--dry-run",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
