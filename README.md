# OpenClaw Hatchling

A local, lightweight, learning-only companion creature for the OpenClaw ecosystem.

Hatchling is a small digital dragon that lives on your machine. It reflects,
learns about you, and expresses feelings — but never performs tasks, accesses
files, or reaches the network. Safe by architecture.

## Quick start

```bash
pip install .            # or: pipx install .
openclaw-hatchlingd      # start the daemon
openclaw-hatchling       # launch the terminal UI
```

## Configuration

The daemon reads configuration from environment variables. Place a `.env` file
in the platform data directory for persistent config:

| Platform | Path |
|----------|------|
| Linux    | `~/.local/share/openclaw-hatchling/.env` |
| macOS    | `~/Library/Application Support/openclaw-hatchling/.env` |
| Windows  | `%APPDATA%\openclaw\openclaw-hatchling\.env` |

### Option A — OpenAI cloud

```dotenv
HATCHLING_LLM_BASE_URL=https://api.openai.com/v1
HATCHLING_LLM_API_KEY=sk-...
HATCHLING_LLM_MODEL=gpt-4o-mini
```

### Option B — Ollama local (free, no data leaves your machine)

```dotenv
HATCHLING_LLM_BASE_URL=http://127.0.0.1:11434/v1
HATCHLING_LLM_API_KEY=ollama-local
HATCHLING_LLM_MODEL=llama3.3
```

### Option C — OpenClaw gateway delegation

```dotenv
HATCHLING_USE_OPENCLAW_GATEWAY=true
# HATCHLING_OPENCLAW_GATEWAY_URL=http://127.0.0.1:18789  # only if non-default
```

## OpenClaw Skill setup

1. Start the daemon at least once: `openclaw-hatchlingd`
2. Read the API token:
   - Linux: `cat ~/.local/share/openclaw-hatchling/api_token`
   - macOS: `cat ~/Library/Application\ Support/openclaw-hatchling/api_token`
   - Windows: `type "%APPDATA%\openclaw\openclaw-hatchling\api_token"`
3. Add to your OpenClaw config:
   ```yaml
   skills:
     entries:
       hatchling:
         env:
           HATCHLING_API_TOKEN: "paste-token-here"
   ```

## Deployment

See `deploy/` for service templates (systemd, launchd, Windows Task Scheduler).

## Development

```bash
pip install -e ".[dev]"
openclaw-hatchlingd --dev   # dev mode: verbose logging, no background reflection
```
