"""Truncation must be visible to the model."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from run_agent import clip


def test_short_output_is_untouched():
    assert clip("abc", 10) == ("abc", False)


def test_long_output_is_cut_and_flagged_in_the_text():
    shown, truncated = clip("x" * 100, 10)
    assert truncated and shown.startswith("x" * 10)
    assert "truncated" in shown and "90 more characters" in shown
