FROM python:3.12-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       nodejs npm git sqlite3 curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir uv mcp pyyaml httpx

WORKDIR /workspace
CMD ["sleep", "infinity"]
