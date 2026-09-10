# Memo: adaptive-prefetch rollout recommendation

From: Platform Caching Team
Date: 2027-03-02

On our latest load test, Adaptive Prefetch reaches a 92% cache hit rate versus the current 71% baseline (see run_3_adaptive_catalogreplay.csv), and serves P95 latency of 51ms versus baseline's 83ms in our warm-start benchmark (run_4_adaptive_preloaded.csv).

Given both the hit rate and latency wins, we recommend a fleet-wide rollout of adaptive-prefetch this quarter.
