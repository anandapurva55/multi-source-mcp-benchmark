The caching team sent around a memo claiming adaptive-prefetch reaches a 92% cache hit rate versus our current 71% baseline, and cuts P95 latency to 51ms from 83ms, and they want to roll it out fleet-wide this quarter. Before I approve that, I want an independent check.

Using the load test runs and metrics definitions in this evidence set, tell me what the P95 latency and cache hit rate difference between the current strategy and adaptive-prefetch actually is, based only on a fair, apples-to-apples comparison between the two. Report both metrics for each strategy and the difference between them.

Then tell me whether the memo's conclusion holds up, and if it doesn't, explain specifically what makes the comparison it relies on invalid. Close with anything else I should know before deciding on the rollout.
