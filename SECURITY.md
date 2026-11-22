# Security policy

## Reporting a vulnerability

Please report vulnerabilities privately through GitHub. Open the **Security** tab of this repository and choose **Report a vulnerability**, or use [the report form](https://github.com/anandapurva55/multi-source-mcp-benchmark/security/advisories/new).

Include what you found, the steps to reproduce it and what an attacker could gain. You can expect a reply within seven days, and a confirmed problem is fixed before it is discussed in public.

## Scope

This project runs model-chosen tool calls, including arbitrary code, so the parts that matter are the sandbox and the grader. Reports in these areas are the most useful:

- a way for code running in a scenario container to reach the network, the host, or anything outside the read-only `evidence/` mount, including the reference answers in `solution/`
- a way for a candidate answer to change its own score, for example by getting past the delimiting or the strict score parsing in `tools/grade.py`
- anything in the Dockerfile or compose files that weakens the isolation described below
- API keys such as `MSMB_API_KEY` appearing in output, logs or error messages

The scenario data is synthetic and contains no personal or real financial data.

## Using it safely

Containers run with networking disabled and with `no-new-privileges`, and the evidence is mounted read-only. The `code-executor` tool still runs arbitrary code inside the container, so treat the container as untrusted and do not mount anything else into it. Set judge credentials only through environment variables, and never commit them.
