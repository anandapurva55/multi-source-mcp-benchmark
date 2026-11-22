# Metrics definitions

Each run's monitoring agent emits one sample per minute of the test window.

P95 latency: the 95th percentile request latency in milliseconds, computed by the agent over each one-minute window. A run's reported P95 latency is the mean of its per-minute P95 samples.

Cache hit rate: the percentage of cache lookups that hit, computed by the agent over each one-minute window. A run's reported hit rate is the mean of its per-minute samples.

Known logging issue: the metrics agent occasionally double-emits a one-minute sample after an internal restart, producing a second row with the same minute_offset and identical values.
