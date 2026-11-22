"""Run a local Ollama model through a scenario using the scenario's MCP tools.

Starts nothing itself: bring the sandbox up first (`make up SCENARIO=<name>`). The agent
sees only the tools named in the scenario's tool_policy (required plus distractors), each
server launched inside the container with `docker exec`, and works from brief.md until it
stops calling tools or hits --max-steps. The final message is written to --out, and every
tool call (name, arguments, the exact output text the model saw, and whether it was truncated) is written to
--trajectory as JSON lines, so you can inspect which tools the agent chose.

Example:
    make up SCENARIO=ledger-drift
    python tools/run_agent.py --scenario ledger-drift --model qwen2.5:7b --out answer.md
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
MAX_CALLS_PER_TURN = 8  # small models sometimes emit hundreds of repeated calls in one turn
SYSTEM_PROMPT = (
    "You are an investigator. Use the provided tools to read the evidence and compute figures "
    "yourself; do not guess. Evidence lives under /workspace/evidence. Some files are not plain "
    "text (for example SQLite databases), so use the code execution tool to read them. Do not "
    "reply with a plan or a description of what you would do: keep using tools until you have "
    "the actual figures, then reply with your final written answer and no tool call."
)


def _tool_name(server: str, tool: str) -> str:
    return f"{server}__{tool}"


def clip(output: str, limit: int) -> tuple[str, bool]:
    """Cut a tool result to `limit` characters and say so, so the model knows it is partial."""
    if len(output) <= limit:
        return output, False
    note = (f"\n[output truncated: {len(output) - limit} more characters not shown. "
            "Request a narrower range, or process the file with code.]")
    return output[:limit] + note, True


def _in_scope(policy: dict) -> set[str]:
    refs = [r for k in ("required", "distractors_same_server", "distractors_other_server")
            for r in policy.get(k, [])]
    return {_tool_name(*r.split(":", 1)) for r in refs}


async def run(scenario: str, model: str, max_steps: int, host: str, num_ctx: int,
              max_tool_output: int, max_tokens: int, trajectory: list[dict]) -> str:
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
                    "stream": False, "options": {"temperature": 0, "num_ctx": num_ctx, "num_predict": max_tokens}})
                resp.raise_for_status()
                msg = resp.json()["message"]
                messages.append(msg)
                calls = msg.get("tool_calls") or []
                if not calls:
                    print(f"[step {step}] final answer ({len(msg.get('content', ''))} chars)", file=sys.stderr)
                    return msg.get("content", "")
                if len(calls) > MAX_CALLS_PER_TURN:
                    print(f"[step {step}] model sent {len(calls)} tool calls; running the first {MAX_CALLS_PER_TURN}", file=sys.stderr)
                    trajectory.append({"step": step, "note": f"{len(calls)} calls requested, {MAX_CALLS_PER_TURN} run"})
                    dropped = len(calls) - MAX_CALLS_PER_TURN
                    calls = calls[:MAX_CALLS_PER_TURN]
                else:
                    dropped = 0
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
                    shown, truncated = clip(output, max_tool_output)
                    trajectory.append({"step": step, "tool": fn["name"], "arguments": fn["arguments"],
                                       "output_chars": len(output), "truncated": truncated,
                                       "output_shown": shown})
                    messages.append({"role": "tool", "tool_name": fn["name"], "content": shown})
                if dropped:
                    messages.append({"role": "user", "content": (
                        f"Notice: you sent {dropped + MAX_CALLS_PER_TURN} tool calls in one turn. Only the first "
                        f"{MAX_CALLS_PER_TURN} were run; the other {dropped} were not. Send fewer calls per turn.")})
        print(f"warning: no final answer after {max_steps} steps; returning last message", file=sys.stderr)
        return next((m.get("content", "") for m in reversed(messages) if m["role"] == "assistant"
                     and m.get("content")), "")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--scenario", required=True)
    parser.add_argument("--model", default="qwen2.5:7b")
    parser.add_argument("--max-steps", type=int, default=20)
    parser.add_argument("--out", required=True, help="where to write the final answer")
    parser.add_argument("--trajectory", help="where to write tool calls as JSON lines (default: <out>.trajectory.jsonl)")
    parser.add_argument("--num-ctx", type=int, default=32768, help="model context window in tokens")
    parser.add_argument("--max-tokens", type=int, default=4096, help="most tokens the model may generate per turn")
    parser.add_argument("--max-tool-output", type=int, default=12000,
                        help="characters of a tool result shown to the model before truncation")
    args = parser.parse_args()
    host = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
    trajectory: list[dict] = []
    try:
        answer = asyncio.run(run(args.scenario, args.model, args.max_steps, host, args.num_ctx,
                                 args.max_tool_output, args.max_tokens, trajectory))
    finally:
        traj_path = Path(args.trajectory or f"{args.out}.trajectory.jsonl")
        traj_path.write_text("".join(json.dumps(t) + "\n" for t in trajectory))
        print(f"wrote {traj_path} ({len(trajectory)} tool calls)", file=sys.stderr)
    Path(args.out).write_text(answer)
    print(f"wrote {args.out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
