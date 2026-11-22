"""The result charts must regenerate from the committed results file as valid SVG."""
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import plot_results


def test_every_chart_is_valid_svg_and_has_no_red():
    for fn in (plot_results.agent_scores, plot_results.judge_calibration, plot_results.tool_use):
        out = fn()
        ET.fromstring(out)
        assert "#ef4444" not in out and "#dc2626" not in out


def test_results_cover_every_model_and_scenario():
    runs = plot_results.DATA["agent_runs"]
    assert len(runs) == 9 and {r["scenario"] for r in runs} == {"ledger-drift", "signal-check", "root-cause"}
