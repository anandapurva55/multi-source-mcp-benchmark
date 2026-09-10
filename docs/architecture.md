# Architecture

## Layout

```
multi-source-mcp-benchmark/
  docker/base.Dockerfile        shared image: python3.12-slim + node + uv + the mcp client library
  tools/mcp_probe.py            spawn any declared MCP server and list or call its tools directly
  tools/grade.py                score a submitted answer against a scenario's claims
  scenarios/<name>/
    brief.md                    the request an agent receives
    mcp-servers.json            which MCP servers are available, and which tools are in scope
    environment/
      docker-compose.yml        builds the base image, mounts evidence/ read-only
      evidence/                 everything the agent can read
    solution/
      generate_evidence.py      deterministic generator that produced evidence/
      REFERENCE_ANSWER.md       the verified correct answer
    evaluation/
      claims.yaml               independent, checkable facts the answer is scored against
```

## Why evidence is mounted, not baked in

Every scenario's `docker-compose.yml` builds the same `docker/base.Dockerfile` and bind-mounts that scenario's `evidence/` directory at `/workspace/evidence` at runtime, rather than each scenario shipping its own Dockerfile that copies data in at build time. One image, many scenarios. Rebuilding a scenario after tweaking a fixture is a file edit, not a rebuild.

## Why the generator lives next to the answer, not next to the evidence

`solution/generate_evidence.py` computes every figure that ends up in `REFERENCE_ANSWER.md` and `evaluation/claims.yaml`, so numbers are derived, not hand-typed, and a change to the scenario can be regenerated and re-verified rather than hand-edited in three places. It lives in `solution/`, not `environment/evidence/`, because an agent working the scenario should have to derive those same facts from the raw evidence, not read the answer key.

## Grading: claims, not string matching

`evaluation/claims.yaml` lists independent factual claims, each with a point value. `tools/grade.py` sends each claim to a judge model alongside the candidate's answer and asks for a 0-3 score, then reports a weighted mean. Two things follow from that design:

- Claims are written as complete, checkable facts ("states X as $24,460.80, within $1") rather than instructions to the judge to go figure out the right number itself. That keeps grading reproducible across judge models and cheap to audit by eye.
- `--dry-run` validates a claims file and an answer's presence without calling any model. Building an eval harness that hard-requires a paid API key for every invocation, including CI and a first-time clone, is a common and avoidable friction point; this one doesn't.

## Shipping a git fixture inside a git repository

`root-cause` needs an agent to investigate an actual git history, not a description of one. A git repository nested directly inside this repository would be recorded as a submodule gitlink, a bare commit pointer with no remote to fetch from, so a clone of this repo would silently hand out an empty directory. Instead, that fixture is committed as `relay-config.bundle` (`git bundle create relay-config.bundle --all`), an ordinary file, and `environment/docker-compose.yml` clones it into a real working repository at container start. Cheap to store, survives a normal git clone, and the agent still gets a real `.git` history to run `git log` against.

## Verifying an MCP configuration without an agent attached

`tools/mcp_probe.py` speaks the MCP protocol directly: it can start any server declared in `mcp-servers.json`, list the tools it actually exposes, and call one. That's how each scenario in this repo was checked, listing tools and confirming they match what's declared, then calling `read_text_file`, `execute_code`, and `git_log` against the real fixtures and confirming the output matches the reference answer, all without a coding agent or a model API key in the loop.
