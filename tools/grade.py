"""Score a submitted answer against a scenario's factual claims.

Each claim is graded independently on a 0-3 scale by a judge model, then combined into a
weighted mean. Claims are written so the judge can read the expected fact directly rather
than having to re-derive it, keeping scoring reproducible across judge models.

Run with --dry-run to validate a claims file and an answer without calling any model,
useful in CI, or for anyone trying the repo without configuring an API key.

Environment:
    EVIDENCEBENCH_API_BASE   OpenAI-compatible chat completions base URL
    EVIDENCEBENCH_API_KEY    API key for that endpoint
    EVIDENCEBENCH_MODEL      model name to use as judge (default: gpt-4o-mini)
"""
import argparse
import os
import sys
from dataclasses import dataclass
from pathlib import Path

import httpx
import yaml

JUDGE_SYSTEM_PROMPT = """You are grading a single factual claim about whether a candidate's \
answer correctly reports and explains a specific fact. Score strictly on the 0-3 scale below.

0 = the claim is not addressed, or the answer contradicts it
1 = the claim is partially addressed but materially incomplete or imprecise
2 = the claim is addressed correctly with minor imprecision
3 = the claim is addressed correctly and completely

Respond with only a single integer: 0, 1, 2, or 3."""


@dataclass
class Claim:
    id: str
    description: str
    points: int


def load_claims(path: str) -> list[Claim]:
    data = yaml.safe_load(Path(path).read_text())
    return [Claim(**c) for c in data["claims"]]


def grade_claim_live(claim: Claim, answer: str, model: str, api_base: str, api_key: str) -> int:
    resp = httpx.post(
        f"{api_base}/chat/completions",
        headers={"Authorization": f"Bearer {api_key}"},
        json={
            "model": model,
            "messages": [
                {"role": "system", "content": JUDGE_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": f"Claim: {claim.description}\n\nCandidate answer:\n{answer}",
                },
            ],
            "temperature": 0,
        },
        timeout=60,
    )
    resp.raise_for_status()
    content = resp.json()["choices"][0]["message"]["content"].strip()
    digits = "".join(ch for ch in content if ch.isdigit())
    return max(0, min(3, int(digits[0]))) if digits else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--claims", required=True, help="path to a claims.yaml file")
    parser.add_argument("--answer", required=True, help="path to the candidate's answer text")
    parser.add_argument("--dry-run", action="store_true", help="validate only, no judge call")
    parser.add_argument("--model", default=os.environ.get("EVIDENCEBENCH_MODEL", "gpt-4o-mini"))
    args = parser.parse_args()

    claims = load_claims(args.claims)
    answer_path = Path(args.answer)
    if not answer_path.exists() or not answer_path.read_text().strip():
        print(f"error: answer file {answer_path} is missing or empty", file=sys.stderr)
        return 1
    answer = answer_path.read_text()

    if args.dry_run:
        print(f"{len(claims)} claims loaded from {args.claims}, answer file is non-empty. Dry run OK.")
        for c in claims:
            print(f"  [{c.points} pts] {c.id}: {c.description}")
        return 0

    api_base = os.environ.get("EVIDENCEBENCH_API_BASE")
    api_key = os.environ.get("EVIDENCEBENCH_API_KEY")
    if not api_base or not api_key:
        print("error: set EVIDENCEBENCH_API_BASE and EVIDENCEBENCH_API_KEY, or pass --dry-run", file=sys.stderr)
        return 1

    total_points = sum(c.points for c in claims)
    earned = 0
    results = []
    for claim in claims:
        score = grade_claim_live(claim, answer, args.model, api_base, api_key)
        earned_points = round(claim.points * score / 3, 2)
        earned += earned_points
        results.append((claim, score, earned_points))

    print(f"{'claim':<24}{'score /3':<10}{'points':<10}description")
    for claim, score, earned_points in results:
        print(f"{claim.id:<24}{score:<10}{earned_points:<10}{claim.description}")
    print(f"\nWeighted total: {earned:.2f} / {total_points} ({100 * earned / total_points:.1f}%)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
