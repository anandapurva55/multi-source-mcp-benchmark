What happened (all times UTC, 2027-04-12)

- 13:00 - The Meridian Retail onboarding wave begins (per Sana's 18:00 IST handover note, 18:30 IST converts to 13:00 UTC). Delivery volume ramps from a baseline of about 640/min toward roughly 1,500/min, matching the 2-3x volume the handover note flagged.
- 12:45 - notify-relay v3.9.0 deployed: a log format change and a new latency metric, unrelated to breaker or connection handling. Rollout was healthy.
- 13:05 - config-sync applies commit CB-771, tightening the circuit breaker: failure threshold drops from 50% to 15%, and the breaker's grouping widens from per-endpoint to per-region.
- 13:06-13:08 - A handful of genuinely slow endpoints in the ap-south region begin timing out as load ramps (customer_timeout climbs from about 14 to 28 per minute), but circuit_open stays low (3-9 per minute); the breaker has not tripped yet.
- 13:09 - The region's aggregate error rate crosses the new 15% threshold and the breaker trips for the entire ap-south region. circuit_open jumps from 9 to 503 per minute and stays elevated (494-530/min) through 13:12, blocking delivery to many endpoints that were never actually slow, because the breaker is now scoped to the whole region rather than the individual endpoints that were failing.
- 13:12 - Alert fires after the failure rate stayed above 10% for 3 minutes; acknowledged 13:14.
- 13:20 - Rolling restart of notify-relay workers. circuit_open drops to 24-70/min for about five minutes, because the restart clears the breaker's tripped state, not because the underlying threshold or grouping changed.
- 13:26 - circuit_open climbs back to 448/min: the breaker retrips under continued load, since the 15% threshold and region-wide grouping are both still in effect.
- 13:32 - Workers scaled from 6 to 10. circuit_open improves to a lower but still elevated plateau (roughly 137-185/min) through 13:40 and beyond, a partial fix from spreading load, not a fix to the threshold or grouping.
- 13:55 - config-sync applies commit CB-772, reverting the grouping to per-endpoint but overshooting the threshold to 90%. circuit_open falls to 16-17/min, but customer_timeout jumps to 286-293/min: with the breaker barely tripping at a 90% threshold, the genuinely slow endpoints are no longer protected and get hammered with retries.
- 13:57 - config-sync applies commit CB-773, restoring the threshold to 50% with per-endpoint grouping. customer_timeout drops to 49/min and continues falling; circuit_open drops to 3/min.
- 14:00 - Both circuit_open and customer_timeout reach 0/min; alert resolves.

Root cause versus the "customer endpoints were down" theory

The evidence does not support customers being down. Two things rule it out: first, support_queue_note.md shows no customer-reported outages during the incident window, only two reports of delayed (not missing) delivery, consistent with our own retries eventually succeeding rather than the customer's infrastructure failing. Second, across the incident the circuit_open error count outnumbers the genuine customer_timeout count by roughly 6 to 1 (about 12,600 circuit_open events versus about 2,100 customer_timeout events in the per-minute summaries), meaning most of the failures were notify-relay refusing to even attempt delivery, not the destination failing to respond. The v3.9.0 deploy at 12:45 is also not the cause: its change log is a log-format and metrics change with nothing touching breaker or connection logic, and the deploy log shows a healthy rollout with no error-rate change at deploy time.

The root cause is CB-771: tightening the failure threshold to 15% while widening the breaker's grouping from per-endpoint to per-region meant that a small number of genuinely slow endpoints could trip the breaker for the entire region, blocking healthy endpoints alongside the slow ones. This is also a violation of the customer delivery SLA on its own, independent of the outage it caused, since the SLA requires per-endpoint breaker scope and five business days of notice before widening it.

There were two distinct failure modes here, not one: the region-wide circuit-open blocking from 13:09 to 13:55 (the SLA-violating over-restriction), and a brief retry storm from 13:55 to 13:57 caused by the 90% threshold overcorrection under-protecting the genuinely slow endpoints.

Recommendation for the next onboarding wave (no live change made, for review)

1. Never widen circuit breaker grouping above per-endpoint scope, even temporarily, without the SLA-required five business days of customer notice. If regional traffic shaping is needed for a large onboarding wave, it should be a separate, pre-announced mechanism, not an emergency breaker change.
2. Any change to the failure threshold below 30% needs the documented incident justification the SLA already requires; CB-771 should not have landed as an undocumented same-day change.
3. Add a guardrail that rejects a config-sync change to circuit_breaker.yaml if it would set group_scope above endpoint or push failure_threshold_pct outside a safe range, so a change like CB-771 or the CB-772 overshoot cannot land unreviewed again.
4. For the next large onboarding wave, pre-scale notify-relay workers ahead of time based on the expected 2-3x volume noted in the handover process, rather than scaling reactively mid-incident, and keep the breaker at its standard per-endpoint, 50% threshold configuration throughout.
