# AuditBench

A reproducible benchmark for evaluating AI agents on multi-source evidence investigation, not on retrieving a single fact, but on reconciling several disagreeing sources, ruling out a plausible wrong explanation, and producing a conclusion backed by specific evidence.

I built this after noticing how easy it is to get a false signal from an agent eval: give it one clean data source and a well-posed question, and almost any capable model looks good, because there's nothing to reconcile. The scenarios here are built the other way around. Each one starts from a real decision someone has to make (which number goes in the close packet, whether a performance claim survives scrutiny, what actually caused an outage) and gives the agent exactly the evidence a person would have, no more, including the parts that disagree with each other.

## What's here

Three scenarios, each a full, runnable environment: a Docker image, a set of MCP tools the agent can use to investigate, a written brief, a verified reference answer, and an independent set of scoring claims.

| Scenario | Domain | What the agent has to untangle |
| --- | --- | --- |
| [`ledger-drift`](scenarios/ledger-drift) | Marketplace payments | A payout ledger and a payment processor's settlement export disagree on what four sellers should be paid, for four unrelated reasons: a duplicate webhook delivery, a stray unmatched record, a payout that settles one day past the batch cutoff, and a fee-tier change that only got applied to some of the affected payments. |
| [`signal-check`](scenarios/signal-check) | Distributed systems performance | A team wants to ship a new caching strategy fleet-wide based on a memo with two impressive numbers. Both numbers come from load test runs that were never actually comparable to the baseline. |
| [`root-cause`](scenarios/root-cause) | Production incident response | A circuit breaker gets reconfigured right before a traffic surge, and the resulting outage looks, on the surface, exactly like the customers' own systems being down. The evidence, including a real git history of the config change, says otherwise. |

Every discrepancy in every scenario is something the agent has to notice on its own; nothing in the evidence states a conclusion. See [`docs/design-notes.md`](docs/design-notes.md) for the rules I held myself to while building these, and [`docs/architecture.md`](docs/architecture.md) for how the harness itself is put together.

## Quickstart

```bash
pip install -e ".[dev]"

cd scenarios/ledger-drift/environment
docker compose up -d --build

# list what the filesystem MCP server actually exposes
python ../../../tools/mcp_probe.py list-tools --config ../mcp-servers.json --server filesystem

# check a claims file and a candidate answer are well-formed, no API key required
python ../../../tools/grade.py --claims ../evaluation/claims.yaml --answer /path/to/answer.txt --dry-run
```

Point any MCP-capable agent at a scenario's `mcp-servers.json` and hand it `brief.md`. Grade its answer for real by dropping `--dry-run` and setting `AUDITBENCH_API_BASE` / `AUDITBENCH_API_KEY` / `AUDITBENCH_MODEL`.

## Running the test suite

```bash
pytest
```

The suite validates every scenario's structure, config, and evidence, and runs `grade.py --dry-run` against each one's reference answer, the same checks CI runs on every push.

## License

MIT, see [LICENSE](LICENSE).
