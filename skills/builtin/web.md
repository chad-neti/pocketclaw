---
name: web
version: 1.0.0
description: Web requests and scraping
author: pocketclaw
layer: 1
category: core
---

# Web Tools

Use `http_request` from the shell skill for API calls and web requests.
Use `run_shell` with `curl` for quick web fetches.
Use `run_python` with `httpx` for complex request chains.

## Examples

- Quick fetch: `run_shell("curl -s https://api.example.com/data")`
- API call: `http_request(method="POST", url="...", headers={...}, body="...")`
- Scraping: `run_python("import httpx; r = httpx.get('...'); print(r.text[:1000])")`
