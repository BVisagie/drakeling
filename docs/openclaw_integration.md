# OpenClaw Integration Guide

**Correct as of:** February 2025  
**Upstream docs:** [docs.openclaw.ai](https://docs.openclaw.ai/)

This guide documents how to connect Drakeling with OpenClaw. It is based on the current OpenClaw documentation and may need updating if OpenClaw changes.

---

## Overview

Drakeling can integrate with OpenClaw in two ways:

1. **OpenClaw Skill** — Lets OpenClaw agents check your creature's status and send care (e.g. from WhatsApp, Telegram, the Control UI).
2. **Gateway delegation** — Lets the Drakeling daemon use OpenClaw's LLM gateway instead of calling an LLM provider directly. Model config stays in one place.

You can use one or both. They are independent.

---

## OpenClaw Configuration

All OpenClaw configuration lives in a **JSON5** file:

```
~/.openclaw/openclaw.json
```

- **Format:** JSON5 (JSON with comments and trailing commas allowed)
- **Hot reload:** The Gateway watches this file and applies most changes without restart
- **Override paths:** `OPENCLAW_CONFIG_PATH` env var can override the file location

---

## 1. OpenClaw Skill (Agent Integration)

The Drakeling skill lets OpenClaw agents check your creature's status and send care autonomously. The agent only uses `GET /status` and `POST /care`. It never calls `/talk`, `/rest`, `/export`, or `/import`.

### Install the Skill

**Option A: ClawHub (recommended)**

```bash
clawhub install drakeling
```

This installs into `./skills` (or your OpenClaw workspace). OpenClaw loads skills from workspace `/skills` on the next session.

**Option B: Manual copy**

Copy the Drakeling `skill/` directory to one of:

- **Workspace skills:** `<agent-workspace>/skills/drakeling/` (highest precedence)
- **Managed skills:** `~/.openclaw/skills/drakeling/` (visible to all agents on the machine)

Precedence: workspace → managed → bundled. If the same skill name exists in multiple places, workspace wins.

### Configure the API Token

The skill requires `DRAKELING_API_TOKEN`. Add it under `skills.entries.drakeling` in `~/.openclaw/openclaw.json`:

1. Start the Drakeling daemon at least once: `drakelingd`
2. Read the API token:
   - Linux: `cat ~/.local/share/drakeling/api_token`
   - macOS: `cat ~/Library/Application\ Support/drakeling/api_token`
   - Windows: `type "%APPDATA%\drakeling\drakeling\api_token"`
3. Add to `~/.openclaw/openclaw.json`:

```json5
{
  "skills": {
    "entries": {
      "drakeling": {
        "enabled": true,
        "env": {
          "DRAKELING_API_TOKEN": "paste-your-token-here"
        }
      }
    }
  }
}
```

If your config already has a `skills` object, merge the `entries.drakeling` block into it. Per-skill fields:

- `enabled`: `true` (default) or `false` to disable
- `env`: Environment variables injected for agent runs (only if not already set)
- `apiKey`: Optional shortcut for skills that declare `metadata.openclaw.primaryEnv`; Drakeling uses `env.DRAKELING_API_TOKEN` instead

### Daemon Address

The skill assumes the Drakeling daemon listens on `http://127.0.0.1:52780`. If you use a custom port via `DRAKELING_PORT`, the skill instructions would need to be updated or the agent must infer the URL. The current skill docs use the default; custom ports are a known limitation.

### Valid Care Types

For `POST /care`, the skill supports:

- `gentle_attention` — default, general check-ins
- `reassurance` — when the user seems worried
- `quiet_presence` — when the user just wants to be nearby
- `feed` — feeds the creature (boosts energy and mood)

---

## 2. Gateway Delegation (LLM Mode)

When Drakeling uses OpenClaw's gateway, it sends LLM requests to the Gateway's OpenAI-compatible endpoint. Model configuration lives in OpenClaw's `openclaw.json`; you configure nothing in Drakeling beyond pointing at the gateway.

### Enable the Chat Completions Endpoint (OpenClaw)

The Gateway's `/v1/chat/completions` endpoint is **disabled by default**. Enable it in `~/.openclaw/openclaw.json`:

```json5
{
  "gateway": {
    "http": {
      "endpoints": {
        "chatCompletions": { "enabled": true }
      }
    }
  }
}
```

### Gateway Authentication

The endpoint uses Gateway auth. Send a Bearer token in requests:

- `Authorization: Bearer <token>`

Token source depends on your Gateway auth mode:

- **`gateway.auth.mode="token"`:** Use `gateway.auth.token` or `OPENCLAW_GATEWAY_TOKEN`
- **`gateway.auth.mode="password"`:** Use `gateway.auth.password` or `OPENCLAW_GATEWAY_PASSWORD`

Find the token in your OpenClaw config or via `openclaw configure` / the Control UI Config tab.

### Configure Drakeling

Set these in Drakeling's `.env` file (in the platform data directory: `~/.local/share/drakeling/` on Linux, etc.):

```dotenv
DRAKELING_USE_OPENCLAW_GATEWAY=true
DRAKELING_OPENCLAW_GATEWAY_URL=http://127.0.0.1:18789
DRAKELING_OPENCLAW_GATEWAY_TOKEN=your-gateway-token-here
```

Optional:

- `DRAKELING_OPENCLAW_GATEWAY_MODEL` — Model to request (e.g. `anthropic/claude-sonnet-4-5`). If unset, the Gateway uses its default.
- `DRAKELING_OPENCLAW_GATEWAY_URL` — Only needed if the Gateway runs on a non-default port (default: `http://127.0.0.1:18789`).

### Behavior

- Drakeling sends `POST /v1/chat/completions` to the Gateway.
- The Gateway runs an agent (default `main`) and returns a completion.
- Drakeling's per-call token cap and daily budget are enforced by Drakeling, not OpenClaw.
- If the Gateway is unreachable at startup, Drakeling logs a warning but continues; LLM calls fail gracefully until the Gateway is available.

---

## Reference: Skills Config Schema

From [Skills Config](https://docs.openclaw.ai/tools/skills-config):

| Field | Purpose |
|-------|---------|
| `skills.entries.<skill>.enabled` | `true`/`false` — disable a skill even if installed |
| `skills.entries.<skill>.env` | Env vars injected for agent runs |
| `skills.entries.<skill>.apiKey` | Convenience for skills with `primaryEnv` |
| `skills.entries.<skill>.config` | Custom per-skill config bag |
| `skills.load.extraDirs` | Extra skill directories (lowest precedence) |
| `skills.load.watch` | Watch skill folders and refresh (default: true) |
| `skills.allowBundled` | Allowlist for bundled skills only |

Changes to skills config take effect on the next agent turn when the watcher is enabled.

---

## Reference: Skill Load Locations

OpenClaw loads skills from (highest to lowest precedence):

1. **Workspace skills:** `<agent-workspace>/skills/`
2. **Managed skills:** `~/.openclaw/skills/`
3. **Bundled skills:** Shipped with the OpenClaw install
4. **Extra dirs:** `skills.load.extraDirs` in config

Name conflicts: workspace overrides managed, which overrides bundled.

---

## Links

- [OpenClaw Skills](https://docs.openclaw.ai/skills)
- [Skills Config](https://docs.openclaw.ai/tools/skills-config)
- [ClawHub](https://docs.openclaw.ai/tools/clawhub) — skill registry and CLI
- [Gateway Configuration](https://docs.openclaw.ai/gateway/configuration)
- [OpenAI Chat Completions API](https://docs.openclaw.ai/gateway/openai-http-api)
- [ClawHub site](https://clawhub.ai/)
