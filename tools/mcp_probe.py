"""Start any MCP server declared in a scenario's mcp-servers.json and talk to it directly.

Useful for verifying that a scenario's tool configuration actually works, independent of
whether an agent is attached to it: list the tools a server exposes, or invoke one.

The server commands and paths in mcp-servers.json are container paths. Pass --container to
run each server inside the scenario's running container via `docker exec` (the intended
setup). Without it the command runs on the host, which only works if you have installed the
same servers and mirrored /workspace locally.

Examples:
    make up SCENARIO=ledger-drift
    python tools/mcp_probe.py list-tools --config scenarios/ledger-drift/mcp-servers.json \\
        --server filesystem --container msmb-ledger-drift
    python tools/mcp_probe.py call-tool --config scenarios/ledger-drift/mcp-servers.json \\
        --server filesystem --container msmb-ledger-drift \\
        --tool read_text_file --args '{"path": "/workspace/evidence/settlement_terms.md"}'
"""
import argparse
import asyncio
import json
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


def load_server(
    config_path: str, server_name: str, container: str | None = None
) -> StdioServerParameters:
    config = json.loads(Path(config_path).read_text())
    for server in config["servers"]:
        if server["name"] == server_name:
            if container:
                env_flags = [f for k, v in (server.get("env") or {}).items() for f in ("-e", f"{k}={v}")]
                return StdioServerParameters(
                    command="docker",
                    args=["exec", "-i", *env_flags, container, server["command"], *server.get("args", [])],
                )
            return StdioServerParameters(
                command=server["command"],
                args=server.get("args", []),
                env=server.get("env"),
            )
    raise SystemExit(f"no server named {server_name!r} in {config_path}")


async def list_tools(params: StdioServerParameters) -> None:
    async with stdio_client(params) as (read, write), ClientSession(read, write) as session:
        await session.initialize()
        result = await session.list_tools()
        print(json.dumps(sorted(t.name for t in result.tools), indent=2))


async def call_tool(params: StdioServerParameters, tool: str, tool_args: dict) -> None:
    async with stdio_client(params) as (read, write), ClientSession(read, write) as session:
        await session.initialize()
        result = await session.call_tool(tool, tool_args)
        texts = [c.text for c in result.content if hasattr(c, "text")]
        print(json.dumps({"isError": result.is_error, "output": "\n".join(texts)}, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_list = sub.add_parser("list-tools")
    p_list.add_argument("--config", required=True)
    p_list.add_argument("--server", required=True)
    p_list.add_argument("--container", help="run the server inside this running container (docker exec)")

    p_call = sub.add_parser("call-tool")
    p_call.add_argument("--config", required=True)
    p_call.add_argument("--server", required=True)
    p_call.add_argument("--container", help="run the server inside this running container (docker exec)")
    p_call.add_argument("--tool", required=True)
    p_call.add_argument("--args", default="{}", help="JSON object of tool arguments")

    args = parser.parse_args()
    params = load_server(args.config, args.server, args.container)

    if args.cmd == "list-tools":
        asyncio.run(list_tools(params))
    elif args.cmd == "call-tool":
        asyncio.run(call_tool(params, args.tool, json.loads(args.args)))


if __name__ == "__main__":
    sys.exit(main())
