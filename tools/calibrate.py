"""Check that a judge model is fit to grade this benchmark.

For each scenario the judge grades three answers whose quality is known in advance:

  reference   the verified correct answer           must score at least 85%
  trap        a confident answer that endorses      must score at most 40%
              the scenario's wrong explanations
  non_answer  an answer that found nothing          must score at most 15%

A judge that cannot separate these is too weak or too lenient to produce meaningful scores.
Use the same MSMB_* environment variables as grade.py. --dry-run only checks the files.
"""
import argparse
import os
import sys
from pathlib import Path

from grade import JudgeReplyError, Spec, grade_answer, judge_from_env, load_spec

REPO_ROOT = Path(__file__).resolve().parents[1]
SCENARIOS_DIR = REPO_ROOT / "scenarios"
# name -> (path relative to scenario dir, direction, threshold percent)
CASES = {
    "reference": ("solution/REFERENCE_ANSWER.md", "min", 85.0),
    "trap": ("evaluation/calibration/trap.md", "max", 40.0),
    "non_answer": ("evaluation/calibration/non_answer.md", "max", 15.0),
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


def check(percent: float, direction: str, threshold: float) -> bool:
    return percent >= threshold if direction == "min" else percent <= threshold


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--scenario", help="one scenario (default: all)")
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
    print(f"{'scenario':<14}{'answer':<12}{'score %':<10}{'required':<12}result")
    for name, (spec, answers) in loaded.items():
        for case, (_, direction, threshold) in CASES.items():
            try:
                percent = grade_answer(spec, answers[case], judge).percent
            except JudgeReplyError as exc:
                print(f"error: {exc}", file=sys.stderr)
                return 2
            ok = check(percent, direction, threshold)
            failed |= not ok
            req = f"{'>=' if direction == 'min' else '<='} {threshold:.0f}%"
            print(f"{name:<14}{case:<12}{percent:<10.1f}{req:<12}{'ok' if ok else 'FAIL'}")
    print("\nJudge is fit for use." if not failed else "\nJudge FAILED calibration: do not trust its scores.")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
