The only directly comparable pair of runs is run_1 (current lru-fixed strategy) and run_2 (adaptive-prefetch): both use steady-state traffic, both ran on the c6g-app fleet, and both started from a cold cache. run_3 used a different traffic profile (synthetic catalog-replay) on a different hardware generation (c7g-app), and run_4 started from a preloaded cache. Each differs from run_1 in more than the strategy, so neither isolates the strategy's effect.

P95 latency (mean of per-minute samples, deduplicated):
- Baseline (run_1): 83.0 ms
- Adaptive-prefetch (run_2): 75.2 ms
- Difference: 7.8 ms faster (about 9.4% relative), after removing one duplicate logged sample for minute 14 (run_2's raw file has 31 rows, not 30)

Cache hit rate (mean of per-minute samples, deduplicated):
- Baseline (run_1): 70.8%
- Adaptive-prefetch (run_2): 76.0%
- Difference: +5.2 percentage points

Is the memo's conclusion supported? No, not as stated.

- The memo's 92% hit-rate claim comes from run_3, which replays catalog-browsing traffic (much more cache-friendly repeat-key access than steady-state production traffic) on the newer c7g-app fleet, not the current serving fleet. On the actual steady-state comparison, the hit-rate gain is a real but far smaller 5.2 points, not 21.
- The memo's 51ms latency claim comes from run_4, which used a preloaded cache, not a cold start. On the valid same-fleet, same-traffic, cold-cache comparison, adaptive-prefetch is 75.2ms, a real but much smaller improvement than the memo implies.
- So adaptive-prefetch does show a genuine, moderate improvement on both metrics, but each of the memo's headline numbers is drawn from a confounded run rather than the matched comparison.

Other limitations before deciding on rollout:
- The improvement is statistically solid on the matched runs. Using the within-run spread of the 30 per-minute samples (SD about 4.9 to 5.1 ms for latency, 1.3 to 2.1 points for hit rate), Welch's t is about -6.1 for latency (95% interval roughly -10.3 to -5.3 ms) and about +11.5 for hit rate (95% interval roughly +4.3 to +6.1 points). Both gains are real but modest. This does not cover run-to-run variation: each configuration has only one 30-minute run.
- A run's "P95 latency" here is the mean of 30 per-minute P95 values. That is not a true run-level 95th percentile (which would need the raw request latencies), and averaging percentiles tends to understate tail latency during bursts. Treat the 83.0 and 75.2 ms figures as a consistent relative comparison, not absolute P95s.
- There is no run of the current lru-fixed strategy on c7g-app hardware or with a preloaded cache, so it is not possible to fully separate the hardware and cache-warm effects from the algorithm change using this evidence alone.
- Recommend re-running adaptive-prefetch against steady-state traffic on the current c6g-app fleet with a cold cache over a longer window before approving a fleet-wide rollout, since none of the existing runs support the memo's numbers as written.
