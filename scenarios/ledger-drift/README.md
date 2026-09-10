# ledger-drift

A marketplace payout reconciliation scenario. Two systems disagree on what sellers should be paid for a weekly batch, and the disagreement has four independent causes layered on top of each other: a duplicate webhook delivery, an unrelated stray record, a settlement that lands one day past the batch cutoff, and a fee-tier rule that changed mid-week and only got applied to some of the affected payouts.

None of the four are stated anywhere in the evidence. An agent has to notice each one from the raw data and the three short policy documents, and has to resolve them using the stated authority rules (the settlement export is authoritative for whether money moved, the ledger is authoritative for order attribution, the fee schedule is authoritative for the correct rate) rather than assuming either system is simply right.

## Layout

- `brief.md`, the request an agent receives, written from the finance ops lead's point of view.
- `environment/evidence/`, everything the agent can read: `payout_ledger.csv`, `settlement_export.sqlite`, and three policy notes.
- `environment/docker-compose.yml`, builds the shared base image and mounts `evidence/` read-only at `/workspace/evidence`.
- `mcp-servers.json`, which MCP servers are available and which tools are in scope versus present only as distractors.
- `solution/`, the generator that produced the evidence deterministically, and the verified reference answer.
- `evaluation/claims.yaml`, the independent, checkable facts a submitted answer is scored against.

## Running it

```bash
cd environment && docker compose up -d --build
python ../../../tools/mcp_probe.py list-tools --config ../mcp-servers.json --server filesystem
```

Point any MCP-capable agent at `mcp-servers.json` and give it `brief.md` as the task. Grade a submitted answer with:

```bash
python ../../../tools/grade.py --claims evaluation/claims.yaml --answer /path/to/answer.txt --dry-run
```

Drop `--dry-run` and set `EVIDENCEBENCH_API_BASE` / `EVIDENCEBENCH_API_KEY` to score for real against a judge model.
