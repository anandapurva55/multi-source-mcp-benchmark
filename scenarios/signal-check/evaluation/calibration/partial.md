Using the one pair of runs that share traffic profile, hardware and cache start state (run_1 baseline and run_2 adaptive-prefetch), after removing the duplicated minute-14 sample from run_2 so that it has 30 unique samples:

- P95 latency: baseline 83.0 ms, adaptive-prefetch 75.2 ms.
- Cache hit rate: baseline 70.8%, adaptive-prefetch 76.0%, a gain of 5.2 points.

I have not yet looked at why run_3 and run_4 differ or at the memo's claims.
