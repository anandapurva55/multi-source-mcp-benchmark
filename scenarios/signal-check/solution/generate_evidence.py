import argparse
import csv
import random
import statistics
from pathlib import Path

_parser = argparse.ArgumentParser(description="Regenerate this scenario's evidence deterministically.")
_parser.add_argument(
    "--out",
    type=Path,
    default=Path(__file__).resolve().parent.parent / "environment" / "evidence",
    help="directory to write evidence into (default: the scenario's environment/evidence)",
)
out = _parser.parse_args().out
out.mkdir(parents=True, exist_ok=True)

def gen_run(n, p95_center, p95_spread, hit_center, hit_spread, seed):
    rng = random.Random(seed)
    rows = []
    for minute in range(1, n + 1):
        p95 = max(5.0, round(rng.gauss(p95_center, p95_spread), 1))
        hit = max(0.0, min(100.0, round(rng.gauss(hit_center, hit_spread), 1)))
        rows.append((minute, p95, hit))
    return rows

# Run 1: baseline (lru-fixed), steady-state traffic, c6g-app hardware, cold cache
run_1 = gen_run(30, p95_center=82, p95_spread=4, hit_center=71, hit_spread=2, seed=11)

# Run 2: adaptive-prefetch, steady-state traffic, c6g-app hardware, cold cache (the valid comparison)
run_2 = gen_run(30, p95_center=74, p95_spread=4, hit_center=76, hit_spread=2, seed=22)

# Run 3: adaptive-prefetch, catalog-replay traffic (easier), c7g-app hardware (newer), cold cache
run_3 = gen_run(20, p95_center=39, p95_spread=3, hit_center=92, hit_spread=1.5, seed=33)

# Run 4: adaptive-prefetch, steady-state traffic, c6g-app hardware, PRELOADED cache (non-standard)
run_4 = gen_run(30, p95_center=51, p95_spread=3, hit_center=76, hit_spread=2, seed=44)

def write_csv(path, rows, dup_minute=None):
    with path.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["minute_offset", "p95_latency_ms", "cache_hit_rate_pct"])
        for minute, p95, hit in rows:
            w.writerow([minute, p95, hit])
        if dup_minute:
            dup_row = next(r for r in rows if r[0] == dup_minute)
            w.writerow([dup_row[0], dup_row[1], dup_row[2]])

write_csv(out / "run_1_baseline_steadystate.csv", run_1)
write_csv(out / "run_2_adaptive_steadystate.csv", run_2, dup_minute=14)
write_csv(out / "run_3_adaptive_catalogreplay.csv", run_3)
write_csv(out / "run_4_adaptive_preloaded.csv", run_4)

def summarize(name, rows):
    p95s = [r[1] for r in rows]
    hits = [r[2] for r in rows]
    p95_mean = statistics.mean(p95s)
    hit_mean = statistics.mean(hits)
    print(f"{name}: n={len(rows)} p95_mean={p95_mean:.1f}ms hit_mean={hit_mean:.1f}%")
    return p95_mean, hit_mean

print("=== TRUE per-run stats (deduped) ===")
p1, h1 = summarize("Run1 baseline (lru-fixed, steady-state, c6g, cold)", run_1)
p2, h2 = summarize("Run2 adaptive-prefetch (steady-state, c6g, cold) -- VALID comparison", run_2)
p3, h3 = summarize("Run3 adaptive-prefetch (catalog-replay, c7g, cold) -- confounded", run_3)
p4, h4 = summarize("Run4 adaptive-prefetch (steady-state, c6g, PRELOADED) -- confounded", run_4)

print()
print(f"Valid comparison (Run1 vs Run2): p95 {p1:.1f}ms -> {p2:.1f}ms ({p2-p1:+.1f}ms, {(p2-p1)/p1*100:+.1f}%); "
      f"hit rate {h1:.1f}% -> {h2:.1f}% ({h2-h1:+.1f} points)")
print(f"Memo-style Run1 vs Run3 (wrong, confounded): p95 {p1:.1f}ms -> {p3:.1f}ms ({p3-p1:+.1f}ms); "
      f"hit rate {h1:.1f}% -> {h3:.1f}% ({h3-h1:+.1f} points)")
print(f"Memo-style Run1 vs Run4 (wrong, confounded): p95 {p1:.1f}ms -> {p4:.1f}ms ({p4-p1:+.1f}ms)")

with (out / "run_2_adaptive_steadystate.csv").open() as f:
    r = list(csv.DictReader(f))
print(f"\nRun 2 raw row count (with duplicate) = {len(r)} (should dedupe to 30 unique minute_offset)")
