# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install dependencies
uv sync

# Run server in dev mode (MCP Inspector UI)
uv run mcp dev mcp_gmail/server.py

# Install into Claude Desktop
uv run mcp install --with-editable . --name gmail \
    --env-var MCP_GMAIL_CREDENTIALS_PATH=$(pwd)/credentials.json \
    --env-var MCP_GMAIL_TOKEN_PATH=$(pwd)/token.json \
    mcp_gmail/server.py

# Lint and format
uv run ruff format .
uv run ruff check --fix .

# Tests
uv run pytest tests/

# Pre-commit (install once, then runs on every commit)
pre-commit install
pre-commit run --all-files
```

## Architecture

The project is a thin MCP server wrapping the Gmail REST API. Three layers:

- **`mcp_gmail/server.py`** — MCP tool/resource definitions using `FastMCP`. The `service` object and `mcp` instance are module-level singletons initialized at import time. Tools call `gmail.py` functions and format results as strings returned to the LLM.
- **`mcp_gmail/gmail.py`** — Low-level Gmail API wrappers (auth, CRUD on messages/threads/labels/drafts). `get_gmail_service()` handles OAuth flow, token refresh, and optional 1Password storage.
- **`mcp_gmail/config.py`** — Pydantic `Settings` with `MCP_GMAIL_` env prefix, also reads from `.env`. The singleton `settings` object is imported by `server.py`.
- **`mcp_gmail/onepassword.py`** — Thin wrapper around the `op` CLI for reading/writing credentials to 1Password. Used only when `MCP_GMAIL_OP_VAULT` and `MCP_GMAIL_OP_ITEM` are set.

## Token storage design

OAuth tokens are stored in a layered cache to avoid repeated authentication prompts:

**Read order:** macOS Keychain → 1Password → local file
- The first source that has a token wins. If the token comes from 1Password or a file, it is immediately bootstrapped into the Keychain for future reads.

**Write on token refresh:** Keychain only
- The Gmail access token expires every hour and is refreshed automatically. Refreshes only update the Keychain. 1Password is intentionally not updated — it remains a durable backup that holds a valid *refresh token*, which never expires (unless revoked). If the Keychain is ever wiped, falling back to 1Password gives enough to re-establish a session.

**Write on initial OAuth grant:** Keychain + 1Password (if configured), or Keychain + local file (if not)
- 1Password is written once at setup and thereafter serves only as a cross-machine backup.

**Touch ID fires only:**
- On first run
- After a Keychain wipe or on a new machine (falls back to 1Password, which re-bootstraps Keychain)

## Configuration

All settings use the `MCP_GMAIL_` prefix (env var or `.env` file):

| Variable | Default | Purpose |
|---|---|---|
| `MCP_GMAIL_CREDENTIALS_PATH` | `credentials.json` | OAuth client credentials from Google Cloud |
| `MCP_GMAIL_TOKEN_PATH` | `token.json` | Stored OAuth token (auto-generated on first auth) |
| `MCP_GMAIL_USER_ID` | `me` | Gmail user ID |
| `MCP_GMAIL_OP_VAULT` | — | 1Password vault name (enables OP mode) |
| `MCP_GMAIL_OP_ITEM` | — | 1Password item name (enables OP mode) |

When both `OP_VAULT` and `OP_ITEM` are set, credentials and tokens are read/written via the `op` CLI instead of local files.
