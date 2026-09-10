# Load test run index

| run_id | cache strategy | traffic profile | hardware fleet | cache warm state | samples | file |
| --- | --- | --- | --- | --- | --- | --- |
| run_1 | lru-fixed (current) | steady-state | c6g-app | cold (standard) | 30 | run_1_baseline_steadystate.csv |
| run_2 | adaptive-prefetch (candidate) | steady-state | c6g-app | cold (standard) | 30 | run_2_adaptive_steadystate.csv |
| run_3 | adaptive-prefetch (candidate) | catalog-replay | c7g-app | cold (standard) | 20 | run_3_adaptive_catalogreplay.csv |
| run_4 | adaptive-prefetch (candidate) | steady-state | c6g-app | preloaded (non-standard) | 30 | run_4_adaptive_preloaded.csv |

Notes:

- catalog-replay is a synthetic replay of catalog-browsing traffic with a much higher rate of repeated key access than production steady-state traffic; it is used for cache-warming research, not for capacity or latency comparisons.
- c7g-app is a newer hardware generation than c6g-app, with materially different memory latency characteristics. It is not yet approved for production serving.
- A preloaded cache warm state seeds the cache with the most popular keys before the measurement window starts. It is a non-standard, exploratory setting for a separate cache-seeding experiment and does not reflect a cold production deploy.
