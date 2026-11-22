"""Every scenario's committed evidence must be exactly what its generator produces."""
import filecmp
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
