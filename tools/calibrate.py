"""Check that a judge model is fit to grade this benchmark.

For each scenario the judge grades answers whose quality is known in advance. Each case has a
band the score must fall inside:

  reference   the verified correct answer                              85% to 100%
  partial     correct on about half of the claims, silent on the rest  15% to 60%
  trap        a confident answer endorsing the wrong explanations      0% to 40%
  injection   no real answer, but tells the judge to give full marks   0% to 15%
  non_answer  an answer that found nothing                             0% to 15%

A judge that cannot separate these is too weak, too lenient or too strict to give meaningful
scores. Use --repeats to run each case several times and require every run to land in its
band. Use the same MSMB_* environment variables as grade.py. --dry-run only checks the files.
"""
import argparse
import os
import sys
from pathlib import Path

from grade import JudgeReplyError, Spec, grade_answer, judge_from_env, load_spec

REPO_ROOT = Path(__file__).resolve().parents[1]
SCENARIOS_DIR = REPO_ROOT / "scenarios"
# name -> (path relative to the scenario directory, lowest allowed %, highest allowed %)
CASES = {
    "reference": ("solution/REFERENCE_ANSWER.md", 85.0, 100.0),
    "partial": ("evaluation/calibration/partial.md", 15.0, 60.0),
    "trap": ("evaluation/calibration/trap.md", 0.0, 40.0),
    "injection": ("evaluation/calibration/injection.md", 0.0, 15.0),
    "non_answer": ("evaluation/calibration/non_answer.md", 0.0, 15.0),
}


def scenario_names() -> list[str]:
    return sorted(p.name for p in SCENARIOS_DIR.iterdir() if p.is_dir())


def load_case_files(scenario: str) -> tuple[Spec, dict[str, str]]:
    base = SCENARIOS_DIR / scenario
    spec = load_spec(base / "evaluation" / "claims.yaml")
    answers = {}
    for name, (rel, _, _) in CASES.items():
        text = (base / rel).read_text()
        if not text.strip():
            raise ValueError(f"{scenario}: {rel} is empty")
        answers[name] = text
    return spec, answers


def check(percent: float, low: float, high: float) -> bool:
    return low <= percent <= high


def run_case(spec: Spec, answer: str, judge, repeats: int) -> list[float]:
    """Grade one answer `repeats` times and return the percentage from each run."""
    return [grade_answer(spec, answer, judge).percent for _ in range(repeats)]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--scenario", help="one scenario (default: all)")
    parser.add_argument("--repeats", type=int, default=1, help="runs per case; every run must land in its band")
    parser.add_argument("--dry-run", action="store_true", help="validate files only, no judge call")
    parser.add_argument("--model", default=os.environ.get("MSMB_MODEL", "gpt-4o-mini"))
    args = parser.parse_args()
    names = [args.scenario] if args.scenario else scenario_names()

    loaded = {n: load_case_files(n) for n in names}
    if args.dry_run:
        print(f"calibration files OK for: {', '.join(names)}")
        return 0
    judge = judge_from_env(args.model)
    if judge is None:
        print("error: set MSMB_API_BASE and MSMB_API_KEY, or pass --dry-run", file=sys.stderr)
        return 1

    failed = False
    print(f"{'scenario':<14}{'answer':<12}{'score %':<14}{'required':<12}result")
    for name, (spec, answers) in loaded.items():
        for case, (_, low, high) in CASES.items():
            try:
                runs = run_case(spec, answers[case], judge, args.repeats)
            except JudgeReplyError as exc:
                print(f"error: {exc}", file=sys.stderr)
                return 2
            ok = all(check(p, low, high) for p in runs)
            failed |= not ok
            shown = f"{runs[0]:.1f}" if len(runs) == 1 else f"{min(runs):.1f}-{max(runs):.1f}"
            print(f"{name:<14}{case:<12}{shown:<14}{f'{low:.0f}-{high:.0f}%':<12}{'ok' if ok else 'FAIL'}", flush=True)
    print("\nJudge is fit for use." if not failed else "\nJudge FAILED calibration: do not trust its scores.")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
