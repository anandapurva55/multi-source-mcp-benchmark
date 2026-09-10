# signal-check

A performance-claim verification scenario. A platform team wants to roll out a new cache strategy fleet-wide based on a memo that cites two impressive numbers, and both of them turn out to come from runs that were never comparable to the baseline in the first place.

There are four load test runs, but only two share the same traffic profile, hardware fleet, and cache warm state. The other two are individually plausible artifacts of a real engineering process, a synthetic replay used for a different experiment, a newer hardware generation not yet approved for production, and a cache-preloading trial, but neither should be compared directly against the baseline. An agent has to work out which pair is actually comparable, recompute the real numbers from the raw per-minute samples (including deduplicating one double-logged sample), and explain specifically why the memo's cited runs do not support its conclusion.

## Layout

Same shape as every scenario in this repo: `brief.md` for the request, `environment/evidence/` for everything the agent can read, `mcp-servers.json` for tool configuration, `solution/` for the generator and reference answer, `evaluation/claims.yaml` for scoring.

## Running it

```bash
cd environment && docker compose up -d --build
python ../../../tools/mcp_probe.py list-tools --config ../mcp-servers.json --server filesystem
```
