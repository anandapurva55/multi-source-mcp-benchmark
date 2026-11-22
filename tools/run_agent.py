"""Run a local Ollama model through a scenario using the scenario's MCP tools.

Starts nothing itself: bring the sandbox up first (`make up SCENARIO=<name>`). The agent
sees only the tools named in the scenario's tool_policy (required plus distractors), each
server launched inside the container with `docker exec`, and works from brief.md until it
stops calling tools or hits --max-steps. The final message is written to --out.

Example:
    make up SCENARIO=ledger-drift
    python tools/run_agent.py --scenario ledger-drift --model llama3.2 --out answer.md
    python tools/grade.py --claims scenarios/ledger-drift/evaluation/claims.yaml --answer answer.md --dry-run

Environment:
    OLLAMA_HOST   Ollama base URL (default http://localhost:11434)
"""
import argparse
import asyncio
import json
import os
import sys
from contextlib import AsyncExitStack
from pathlib import Path

import httpx
from mcp import ClientSession
from mcp.client.stdio import stdio_client
from mcp_probe import load_server

REPO_ROOT = Path(__file__).resolve().parents[1]
MAX_TOOL_OUTPUT = 6000
SYSTEM_PROMPT = (
    "You are an investigator. Use the provided tools to read the evidence and compute figures "
    "yourself; do not guess. Evidence lives under /workspace/evidence. When you are done, reply "
    "with your final written answer and no tool call."
)


def _tool_name(server: str, tool: str) -> str:
    return f"{server}__{tool}"


def _in_scope(policy: dict) -> set[str]:
    refs = [r for k in ("required", "distractors_same_server", "distractors_other_server")
            for r in policy.get(k, [])]
    return {_tool_name(*r.split(":", 1)) for r in refs}


async def run(scenario: str, model: str, max_steps: int, host: str) -> str:
    scenario_dir = REPO_ROOT / "scenarios" / scenario
    config_path = scenario_dir / "mcp-servers.json"
    config = json.loads(config_path.read_text())
    allowed = _in_scope(config["tool_policy"])
    container = f"msmb-{scenario}"

    async with AsyncExitStack() as stack:
        sessions: dict[str, ClientSession] = {}
        tools: list[dict] = []
        route: dict[str, tuple[str, str]] = {}
        for server in config["servers"]:
            params = load_server(str(config_path), server["name"], container)
            read, write = await stack.enter_async_context(stdio_client(params))
            session = await stack.enter_async_context(ClientSession(read, write))
            await session.initialize()
            sessions[server["name"]] = session
            for t in (await session.list_tools()).tools:
                name = _tool_name(server["name"], t.name)
                if name in allowed:
                    route[name] = (server["name"], t.name)
                    tools.append({"type": "function", "function": {
                        "name": name, "description": t.description or "", "parameters": t.input_schema}})

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": (scenario_dir / "brief.md").read_text()},
        ]
        async with httpx.AsyncClient(timeout=600) as client:
            for step in range(1, max_steps + 1):
                resp = await client.post(f"{host}/api/chat", json={
                    "model": model, "messages": messages, "tools": tools,
                    "stream": False, "options": {"temperature": 0, "num_ctx": 16384}})
                resp.raise_for_status()
                msg = resp.json()["message"]
                messages.append(msg)
                calls = msg.get("tool_calls") or []
                if not calls:
                    print(f"[step {step}] final answer ({len(msg.get('content', ''))} chars)", file=sys.stderr)
                    return msg.get("content", "")
                for call in calls:
                    fn = call["function"]
                    print(f"[step {step}] {fn['name']}({json.dumps(fn['arguments'])[:120]})", file=sys.stderr)
                    if fn["name"] not in route:
                        output = f"error: unknown tool {fn['name']!r}"
                    else:
                        server_name, tool = route[fn["name"]]
                        try:
                            result = await sessions[server_name].call_tool(tool, fn["arguments"])
                            output = "\n".join(c.text for c in result.content if hasattr(c, "text"))
                        except Exception as exc:  # noqa: BLE001  surface tool failures to the model instead of crashing
                            output = f"error: {exc}"
                    messages.append({"role": "tool", "tool_name": fn["name"], "content": output[:MAX_TOOL_OUTPUT]})
        print(f"warning: no final answer after {max_steps} steps; returning last message", file=sys.stderr)
        return next((m.get("content", "") for m in reversed(messages) if m["role"] == "assistant"
                     and m.get("content")), "")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--scenario", required=True)
    parser.add_argument("--model", default="llama3.2")
    parser.add_argument("--max-steps", type=int, default=20)
    parser.add_argument("--out", required=True, help="where to write the final answer")
    args = parser.parse_args()
    host = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
    answer = asyncio.run(run(args.scenario, args.model, args.max_steps, host))
    Path(args.out).write_text(answer)
    print(f"wrote {args.out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
