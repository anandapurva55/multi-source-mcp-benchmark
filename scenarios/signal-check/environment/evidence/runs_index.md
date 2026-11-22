# Load test run index

| run_id | cache strategy | traffic profile | hardware fleet | cache start state | samples | file |
| --- | --- | --- | --- | --- | --- | --- |
| run_1 | lru-fixed (current) | steady-state | c6g-app | cold | 30 | run_1_baseline_steadystate.csv |
| run_2 | adaptive-prefetch (candidate) | steady-state | c6g-app | cold | 30 | run_2_adaptive_steadystate.csv |
| run_3 | adaptive-prefetch (candidate) | catalog-replay | c7g-app | cold | 20 | run_3_adaptive_catalogreplay.csv |
| run_4 | adaptive-prefetch (candidate) | steady-state | c6g-app | preloaded | 30 | run_4_adaptive_preloaded.csv |

Notes:

- steady-state is a sampled replay of production traffic. catalog-replay is a synthetic replay of catalog-browsing sessions.
- c6g-app is the current production serving fleet. c7g-app is a newer hardware generation.
- A preloaded cache start state seeds the cache with the most popular keys before the measurement window starts. A cold start begins with an empty cache.
