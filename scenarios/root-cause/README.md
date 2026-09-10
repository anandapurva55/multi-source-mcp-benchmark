# root-cause

An incident reconstruction scenario built around a genuinely common production failure: a circuit breaker configuration change that is more subtle than a straightforward capacity problem. A small, real degradation (a handful of slow customer endpoints under a traffic surge) gets amplified by a breaker that was accidentally reconfigured to a wider blast radius than it should have had, and the resulting errors look, on the surface, exactly like the customers themselves being down.

The evidence includes a real local git repository tracking the breaker and worker configuration commit by commit, structured logs with two distinct error signatures that must be told apart, a deploy record that is a red herring, and a support-queue note that is the actual evidence needed to rule out the "customers are down" theory, since that can't be settled from the relay's own logs alone.

## Layout

Same shape as the other scenarios, with one addition: `environment/evidence/relay-config.bundle` is a real git repository, shipped as a bundle so it stays a normal tracked file rather than a nested repository, and cloned into a working copy at `/workspace/relay-config` when the container starts (see `environment/docker-compose.yml`). The agent has to use git tooling (`git log`, `git show`) rather than just reading a file to reconstruct the configuration history.

## Running it

```bash
cd environment && docker compose up -d --build
python ../../../tools/mcp_probe.py list-tools --config ../mcp-servers.json --server git
```
