"""Regenerate every piece of root-cause's evidence deterministically.

Usage: python generate_evidence.py [--out DIR]
Writes app_logs.txt and relay-config.bundle into DIR (default ../environment/evidence/),
overwriting what's already there, and prints the figures the reference
answer and evaluation claims are built from.
"""
import argparse
import os
import random
import shutil
import subprocess
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

EVIDENCE_DIR = Path(__file__).resolve().parent.parent / "environment" / "evidence"

rng = random.Random(99)


def ts(s: str) -> datetime:
    return datetime.fromisoformat(s)


START = ts("2027-04-12T12:45:00+00:00")
END = ts("2027-04-12T14:15:00+00:00")


def phase(t: datetime) -> tuple[float, float]:
    """Target (circuit_open_rate, customer_timeout_rate) for a given minute."""
    if t < ts("2027-04-12T13:06:00+00:00"):
        return 0.0, 0.005    # baseline: no circuit_open, tiny genuine customer_timeout rate
    if t < ts("2027-04-12T13:09:00+00:00"):
        return 0.0, 0.02     # a few slow endpoints show up as traffic ramps
    if t < ts("2027-04-12T13:20:00+00:00"):
        return 0.34, 0.02    # breaker trips region-wide, circuit_open dominates
    if t < ts("2027-04-12T13:26:00+00:00"):
        return 0.03, 0.015   # brief relief after restart
    if t < ts("2027-04-12T13:32:00+00:00"):
        return 0.31, 0.02    # retrips
    if t < ts("2027-04-12T13:55:00+00:00"):
        return 0.11, 0.015   # partial relief after scaling workers
    if t < ts("2027-04-12T13:57:00+00:00"):
        return 0.005, 0.19   # overcorrection: breaker barely trips, retry storm
    if t < ts("2027-04-12T13:59:00+00:00"):
        return 0.01, 0.03    # settling after threshold corrected
    return 0.0, 0.004        # resolved / baseline


def generate_logs(shas: dict[str, str]) -> list[tuple[datetime, str]]:
    lines: list[tuple[datetime, str]] = []

    t = START
    while t <= END:
        if t < ts("2027-04-12T13:00:00+00:00"):
            base_req = 640
        elif t < ts("2027-04-12T13:05:00+00:00"):
            frac = (t - ts("2027-04-12T13:00:00+00:00")).total_seconds() / 300
            base_req = int(640 + frac * (1500 - 640))
        else:
            base_req = 1500
        req = max(50, int(base_req + rng.gauss(0, 30)))
        co_rate, ct_rate = phase(t)
        co_rate = max(0.0, co_rate + rng.gauss(0, 0.01))
        ct_rate = max(0.0, ct_rate + rng.gauss(0, 0.003))
        circuit_open = int(round(req * co_rate))
        customer_timeout = int(round(req * ct_rate))
        p95 = int(140 + (co_rate + ct_rate) * 6000 + rng.gauss(0, 30))
        lines.append((t, f"INFO  notify-relay summary window=1m deliveries={req} "
                          f"circuit_open={circuit_open} customer_timeout={customer_timeout} "
                          f"p95_latency_ms={max(90, p95)}"))
        t += timedelta(minutes=1)

    markers = [
        ("2027-04-12T12:45:00+00:00", 'INFO  notify-relay deploy completed version=v3.9.0 rollout=canary->full healthy=true'),
        ("2027-04-12T13:05:00+00:00", f'INFO  config-sync applied commit={shas["CB-771"]} file=relay-config/circuit_breaker.yaml'),
        ("2027-04-12T13:20:00+00:00", 'INFO  notify-relay rolling restart initiated reason="on-call mitigation" workers=6'),
        ("2027-04-12T13:20:40+00:00", 'INFO  notify-relay rolling restart completed workers=6'),
        ("2027-04-12T13:32:00+00:00", f'INFO  config-sync applied commit={shas["workers"]} file=relay-config/workers.yaml'),
        ("2027-04-12T13:32:30+00:00", 'INFO  notify-relay scaled workers=10'),
        ("2027-04-12T13:55:00+00:00", f'INFO  config-sync applied commit={shas["CB-772"]} file=relay-config/circuit_breaker.yaml'),
        ("2027-04-12T13:57:00+00:00", f'INFO  config-sync applied commit={shas["CB-773"]} file=relay-config/circuit_breaker.yaml'),
    ]
    lines += [(ts(t), text) for t, text in markers]

    endpoints_ap_south = [f"ep-aps-{i:03d}.meridianretail.example" for i in range(1, 13)]
    slow_endpoints = endpoints_ap_south[:2]  # genuinely slow ones, independent of the breaker bug

    def add_samples(t0: datetime, t1: datetime, per_minute: int, kind: str) -> None:
        t = t0
        while t < t1:
            n = rng.randint(max(0, per_minute - 2), per_minute + 2)
            for _ in range(n):
                jitter = timedelta(seconds=rng.randint(0, 59))
                if kind == "circuit_open":
                    ep = rng.choice(endpoints_ap_south)
                    msg = f'ERROR notify-relay endpoint={ep} msg="delivery blocked: circuit open for group=ap-south"'
                else:
                    ep = rng.choice(slow_endpoints) if rng.random() < 0.85 else rng.choice(endpoints_ap_south)
                    msg = f'ERROR notify-relay endpoint={ep} msg="customer endpoint timeout after 8000ms"'
                lines.append((t + jitter, msg))
            t += timedelta(minutes=1)

    add_samples(ts("2027-04-12T12:45:00+00:00"), ts("2027-04-12T13:09:00+00:00"), 1, "customer_timeout")
    add_samples(ts("2027-04-12T13:09:00+00:00"), ts("2027-04-12T13:20:00+00:00"), 6, "circuit_open")
    add_samples(ts("2027-04-12T13:20:40+00:00"), ts("2027-04-12T13:26:00+00:00"), 1, "circuit_open")
    add_samples(ts("2027-04-12T13:26:00+00:00"), ts("2027-04-12T13:32:00+00:00"), 6, "circuit_open")
    add_samples(ts("2027-04-12T13:32:30+00:00"), ts("2027-04-12T13:55:00+00:00"), 2, "circuit_open")
    add_samples(ts("2027-04-12T13:55:00+00:00"), ts("2027-04-12T13:57:00+00:00"), 5, "customer_timeout")
    add_samples(ts("2027-04-12T13:59:00+00:00"), ts("2027-04-12T14:15:00+00:00"), 1, "customer_timeout")

    lines.sort(key=lambda x: x[0])
    return lines


def write_logs(lines: list[tuple[datetime, str]], evidence_dir: Path) -> None:
    out = evidence_dir / "app_logs.txt"
    with out.open("w") as f:
        for t, text in lines:
            f.write(f"{t.strftime('%Y-%m-%dT%H:%M:%SZ')} {text}\n")
    print(f"wrote {len(lines)} lines to {out}")

    co_count = sum(1 for _, l in lines if "circuit open" in l)
    ct_count = sum(1 for _, l in lines if "customer endpoint timeout" in l)
    print(f"raw ERROR sample ratio circuit_open:customer_timeout = {co_count}:{ct_count} ({co_count / ct_count:.1f}:1)")


GIT_ENV_OVERRIDES = {
    # Ignore the developer's git config (signing, templates, hooks) so commit ids are stable.
    "GIT_CONFIG_GLOBAL": os.devnull,
    "GIT_CONFIG_NOSYSTEM": "1",
}


def _git(repo: Path, *args: str, extra_env: dict[str, str] | None = None) -> str:
    env = {**os.environ, **GIT_ENV_OVERRIDES, **(extra_env or {})}
    result = subprocess.run(["git", "-c", "commit.gpgsign=false", *args], cwd=repo, env=env,
                            check=True, capture_output=True, text=True)
    return result.stdout.strip()


def build_config_bundle(evidence_dir: Path) -> dict[str, str]:
    """Rebuild relay-config's commit history, export it as a portable bundle, return short SHAs.

    A git repository nested inside this repository would be recorded as a
    submodule gitlink rather than real files. Building it in a temp directory
    and exporting a bundle keeps the fixture a normal, clonable file.
    """
    shas: dict[str, str] = {}

    def commit(repo: Path, key: str, date: str, name: str, email: str, message: str) -> None:
        _git(repo, "commit", "-q", "-m", message, extra_env={
            "GIT_AUTHOR_DATE": date, "GIT_COMMITTER_DATE": date,
            "GIT_AUTHOR_NAME": name, "GIT_AUTHOR_EMAIL": email,
            "GIT_COMMITTER_NAME": name, "GIT_COMMITTER_EMAIL": email,
        })
        shas[key] = _git(repo, "rev-parse", "--short=7", "HEAD")

    def write(repo: Path, fname: str, text: str) -> None:
        (repo / fname).write_text(text)
        _git(repo, "add", fname)

    breaker = "service: notify-relay\nfailure_threshold_pct: {pct}\ngroup_scope: {scope}\nwindow_sec: 60\n"
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp) / "relay-config"
        repo.mkdir()
        _git(repo, "init", "-q", "-b", "main")

        write(repo, "circuit_breaker.yaml", breaker.format(pct=50, scope="endpoint"))
        write(repo, "workers.yaml", "service: notify-relay\nreplicas: 6\n")
        commit(repo, "initial", "2027-01-15T09:00:00+00:00", "Platform Reliability",
               "platform-reliability@fernbridge.example",
               "Initial notify-relay circuit breaker and worker config")

        write(repo, "circuit_breaker.yaml", breaker.format(pct=15, scope="region"))
        commit(repo, "CB-771", "2027-04-12T13:05:00+00:00", "Priya Deshmukh",
               "priya.deshmukh@fernbridge.example",
               "CB-771: tighten breaker sensitivity ahead of Meridian Retail onboarding wave")

        write(repo, "workers.yaml", "service: notify-relay\nreplicas: 10\n")
        commit(repo, "workers", "2027-04-12T13:32:00+00:00", "Jordan Ellery",
               "jordan.ellery@fernbridge.example", "Scale notify-relay workers for onboarding traffic")

        write(repo, "circuit_breaker.yaml", breaker.format(pct=90, scope="endpoint"))
        commit(repo, "CB-772", "2027-04-12T13:55:00+00:00", "Jordan Ellery",
               "jordan.ellery@fernbridge.example", "CB-772: revert breaker grouping to per-endpoint")

        write(repo, "circuit_breaker.yaml", breaker.format(pct=50, scope="endpoint"))
        commit(repo, "CB-773", "2027-04-12T13:57:00+00:00", "Jordan Ellery",
               "jordan.ellery@fernbridge.example", "CB-773: restore standard breaker threshold")

        bundle_path = evidence_dir / "relay-config.bundle"
        _git(repo, "bundle", "create", str(bundle_path), "--all")
        print(f"wrote 5-commit history to {bundle_path}")
    return shas


if __name__ == "__main__":
    if not shutil.which("git"):
        raise SystemExit("git is required to regenerate relay-config.bundle")
    parser = argparse.ArgumentParser(description="Regenerate this scenario's evidence deterministically.")
    parser.add_argument("--out", type=Path, default=EVIDENCE_DIR,
                        help="directory to write evidence into (default: the scenario's environment/evidence)")
    out = parser.parse_args().out
    out.mkdir(parents=True, exist_ok=True)
    shas = build_config_bundle(out)
    write_logs(generate_logs(shas), out)
