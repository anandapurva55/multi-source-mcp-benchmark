# INC-6014: notify-relay elevated delivery failures

| timestamp_utc | event |
| --- | --- |
| 2027-04-12T13:12:00Z | Alert fired: notify-relay failure rate above 10% sustained for 3 minutes |
| 2027-04-12T13:14:00Z | Acknowledged by Jordan E. |
| 2027-04-12T13:20:00Z | Action: rolling restart of notify-relay workers |
| 2027-04-12T13:32:00Z | Action: scaled notify-relay workers 6 -> 10 |
| 2027-04-12T13:55:00Z | Action: config-sync change reverting breaker grouping to per-endpoint |
| 2027-04-12T13:57:00Z | Action: config-sync change restoring standard breaker threshold |
| 2027-04-12T14:00:00Z | Alert resolved |

Handoff note: Stabilized for now. Need a written recommendation on how to safely handle the next large onboarding wave without repeating this. Holding off on any further live changes until we have a plan.

Jordan
