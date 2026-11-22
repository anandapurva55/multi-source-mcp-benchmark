# Shared investigation sandbox. Everything the MCP servers need is installed at build
# time so the container can run with networking disabled (see the scenario compose files).
FROM node:26-bookworm-slim@sha256:5df79989ed685e09f0a98019db4cebfb22fb9df1a53c0161664a011f7ff6b0f1 AS node

FROM python:3.12-slim-bookworm@sha256:935c3c5b12357a7e10caa9c1e6ca5692344d97cf229832ef584be2cec9fc03df

RUN apt-get update \
    && apt-get install -y --no-install-recommends git sqlite3 ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Node runtime, copied from the pinned node image above
COPY --from=node /usr/local/bin/node /usr/local/bin/node
COPY --from=node /usr/local/lib/node_modules /usr/local/lib/node_modules
RUN ln -s ../lib/node_modules/npm/bin/npm-cli.js /usr/local/bin/npm \
    && ln -s ../lib/node_modules/npm/bin/npx-cli.js /usr/local/bin/npx

RUN pip install --no-cache-dir uv==0.13.9 pyyaml==6.0.4

# MCP servers, pinned and preinstalled
RUN npm install -g --no-fund --no-audit \
      @modelcontextprotocol/server-filesystem@2026.7.10 \
      @geobio/code_execution_server@0.2.1
ENV UV_TOOL_DIR=/opt/uv-tools UV_TOOL_BIN_DIR=/usr/local/bin
RUN uv tool install --with "mcp<2" mcp-server-git==2026.7.10 \
    && uv tool install --with "mcp<2" mcp-server-calculator==0.2.0

# The agent runs as an unprivileged user. Writable areas are tmpfs mounts set in compose.
RUN useradd --uid 10001 --no-create-home --shell /usr/sbin/nologin agent \
    && mkdir -p /workspace
USER agent
ENV HOME=/home/agent UV_CACHE_DIR=/tmp/uv-cache
WORKDIR /workspace
CMD ["sleep", "infinity"]
