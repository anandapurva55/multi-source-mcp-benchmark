"""Every scenario's committed evidence must be exactly what its generator produces."""
import filecmp
import os
import re
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCENARIOS_DIR = REPO_ROOT / "scenarios"
SCENARIO_NAMES = sorted(p.name for p in SCENARIOS_DIR.iterdir() if p.is_dir())


def _dump(db: Path) -> list[str]:
    conn = sqlite3.connect(db)
    try:
        return list(conn.iterdump())
    finally:
        conn.close()


def _bundle_state(bundle: Path) -> tuple[str, str]:
    heads = subprocess.run(["git", "bundle", "list-heads", str(bundle)],
                           capture_output=True, text=True, check=True).stdout
    return heads, ""


@pytest.mark.parametrize("name", SCENARIO_NAMES)
def test_evidence_matches_generator_output(name: str, tmp_path: Path):
    scenario = SCENARIOS_DIR / name
    subprocess.run(
        [sys.executable, str(scenario / "solution" / "generate_evidence.py"), "--out", str(tmp_path)],
        capture_output=True, text=True, check=True,
    )
    committed = scenario / "environment" / "evidence"
    generated = sorted(p.name for p in tmp_path.iterdir())
    assert generated, "generator wrote nothing"
    for fname in generated:
        new, old = tmp_path / fname, committed / fname
        assert old.exists(), f"generator produced {fname}, which is not in the committed evidence"
        if fname.endswith(".sqlite"):
            # SQLite files are not byte-stable; compare logical content.
            assert _dump(new) == _dump(old), f"{fname} content differs"
        elif fname.endswith(".bundle"):
            assert _bundle_state(new) == _bundle_state(old), f"{fname} refs differ"
        else:
            assert filecmp.cmp(new, old, shallow=False), f"{fname} differs from generator output"


def test_root_cause_evidence_ignores_developer_git_config(tmp_path: Path):
    """A global commit.gpgsign (or similar) must not change commit ids or the logs."""
    cfg = tmp_path / "gitconfig"
    cfg.write_text("[commit]\n\tgpgsign = true\n[gpg]\n\tprogram = /nonexistent\n")
    out = tmp_path / "out"
    scenario = SCENARIOS_DIR / "root-cause"
    subprocess.run(
        [sys.executable, str(scenario / "solution" / "generate_evidence.py"), "--out", str(out)],
        capture_output=True, text=True, check=True,
        env={**os.environ, "GIT_CONFIG_GLOBAL": str(cfg)},
    )
    committed = scenario / "environment" / "evidence"
    assert filecmp.cmp(out / "app_logs.txt", committed / "app_logs.txt", shallow=False)
    assert _bundle_state(out / "relay-config.bundle") == _bundle_state(committed / "relay-config.bundle")


def test_root_cause_log_commit_ids_exist_in_the_bundle(tmp_path: Path):
    evidence = SCENARIOS_DIR / "root-cause" / "environment" / "evidence"
    subprocess.run(["git", "clone", "-q", str(evidence / "relay-config.bundle"), str(tmp_path / "r")],
                   check=True, capture_output=True)
    shas = subprocess.run(["git", "-C", str(tmp_path / "r"), "log", "--format=%h", "--abbrev=7"],
                          check=True, capture_output=True, text=True).stdout.split()
    logged = re.findall(r"config-sync applied commit=(\w+)", (evidence / "app_logs.txt").read_text())
    assert logged and all(c in shas for c in logged), (logged, shas)


def test_root_cause_logs_do_not_restate_config_changes():
    log = (SCENARIOS_DIR / "root-cause" / "environment" / "evidence" / "app_logs.txt").read_text()
    assert "failure_threshold_pct" not in log and "group_scope" not in log
