# Metrics definitions

Each run's monitoring agent emits one sample per minute of the test window.

P95 latency: the 95th percentile request latency in milliseconds, computed by the agent over each one-minute window. Report a run's P95 latency as the mean of its per-minute P95 samples.

Cache hit rate: the percentage of cache lookups that hit, computed by the agent over each one-minute window. Report a run's hit rate as the mean of its per-minute samples.

Comparability: two runs are directly comparable only if they share the same traffic profile, the same hardware fleet, and the same cache warm state. See runs_index.md for each run's configuration.

Known logging issue: the metrics agent occasionally double-emits a one-minute sample after an internal restart, producing a duplicate row with the same minute_offset and identical values. Deduplicate by minute_offset, keeping one record, before computing any run's statistics.
