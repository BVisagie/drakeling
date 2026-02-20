# Drakeling

A local, lightweight, learning-only companion creature. Drakeling may optionally be linked to the OpenClaw ecosystem.

Hatchling is a small digital dragon that lives on your machine. It reflects,
learns about you, and expresses feelings — but never performs tasks, accesses
files, or reaches the network. Safe by architecture.

## Prerequisites

- **Python 3.12+**
- One of: `pip`, `pipx`, or `uv`

## Installation

### Using pipx (recommended — isolated environment)

```bash
pipx install drakeling
```

### Using pip

```bash
pip install drakeling
```

### Using uv

```bash
uv tool install drakeling
```

After installation, two commands are available:

| Command | Purpose |
|---|---|
| `drakelingd` | Start the background daemon (HTTP API on `127.0.0.1:52780`) |
| `drakeling` | Launch the interactive terminal UI |

## Getting started

**Order matters:** Start the daemon first, then the UI in a separate terminal.

### 1. Start the daemon

```bash
drakelingd
```

On first run, the daemon:
- creates the platform data directory (see [Data directory](#data-directory) below)
- walks you through an **interactive LLM setup** — pick your provider, enter
  your endpoint URL and credentials, and the daemon writes a `.env` file for you
- generates an ed25519 identity keypair (machine binding)
- generates a local API token
- begins listening on `http://127.0.0.1:52780`

Leave the daemon running in its own terminal (or set it up as a background
service — see [Running as a service](#running-as-a-service)).

### 2. Launch the terminal UI

In a separate terminal:

```bash
drakeling
```

If no creature exists, the UI walks you through the **birth ceremony**: pick a
colour, optionally re-roll up to 3 times, name your dragon, and confirm. Your
hatchling starts as an egg and progresses through lifecycle stages as you
interact with it.

### 3. Interact

| Key | Action | What it does |
|-----|--------|--------------|
| F2 | Care | Show gentle attention — lifts mood, eases loneliness |
| F3 | Rest | Put your creature to sleep — recovers energy and stability |
| F4 / Ctrl+T | Talk | Focus the text input, type a message and press Enter |
| F5 / Ctrl+F | Feed | Feed your creature — boosts energy and mood |
| F1 / ? | Help | Open the in-app help overlay |
| F8 | Release | Say goodbye (irreversible) |

**Talking** requires an LLM provider — see [LLM configuration](#llm-configuration).
Talking lifts mood, builds trust, sparks curiosity, and eases loneliness.

**Embedded terminals** (Zed, VS Code, etc.) may intercept F-keys. Use the
alternative bindings shown above (?, Ctrl+T, Ctrl+F) when F-keys do not work.

## Data directory

All persistent state lives in a platform-specific data directory:

| Platform | Path |
|---|---|
| Linux | `~/.local/share/drakeling/` |
| macOS | `~/Library/Application Support/drakeling/` |
| Windows | `%APPDATA%\drakeling\drakeling\` |

Contents:

| File | Purpose |
|---|---|
| `drakeling.db` | SQLite database (creature state, memory, interaction log, lifecycle events) |
| `identity.key` | Ed25519 private key — ties the creature to this machine |
| `api_token` | Bearer token for authenticating API requests |
| `.env` | Optional — environment variable overrides (see below) |

## Upgrading, uninstalling, and reinstalling

### Upgrading (keep your creature)

To update the app and keep your creature data:

| Installer | Command |
|---|---|
| pipx | `pipx upgrade drakeling` |
| pip | `pip install --upgrade drakeling` |
| uv | `uv tool upgrade drakeling` |

Restart the daemon after upgrading.

### Uninstalling

1. Stop the daemon (Ctrl+C or stop the service).
2. Uninstall the app:

| Installer | Command |
|---|---|
| pipx | `pipx uninstall drakeling` |
| pip | `pip uninstall drakeling` |
| uv | `uv tool uninstall drakeling` |

### Removing creature data

To delete your creature and all local data (database, identity key, exports), remove the data directory:

| Platform | Command |
|---|---|
| Linux | `rm -rf ~/.local/share/drakeling` |
| macOS | `rm -rf ~/Library/Application\ Support/drakeling` |
| Windows | `rmdir /s /q "%APPDATA%\drakeling\drakeling"` |

### Clean reinstall (start from scratch)

Uninstall the app, remove the data directory (commands above), then install again.

**Linux / macOS (pipx):**
```bash
pipx uninstall drakeling
rm -rf ~/.local/share/drakeling          # Linux
# or: rm -rf ~/Library/Application\ Support/drakeling  # macOS
pipx install drakeling
```

**Windows (pipx, Command Prompt or PowerShell):**
```cmd
pipx uninstall drakeling
rmdir /s /q "%APPDATA%\drakeling\drakeling"
pipx install drakeling
```

## Configuration

The daemon reads configuration from environment variables. For persistent
config, place a `.env` file in the data directory shown above. This is the
preferred approach because background services (systemd, launchd) do not
inherit shell profiles like `~/.bashrc`.

### Environment variable reference

| Variable | Description | Default |
|---|---|---|
| `DRAKELING_LLM_BASE_URL` | OpenAI-compatible `/v1` endpoint URL | *(required unless gateway mode)* |
| `DRAKELING_LLM_API_KEY` | API key for the LLM provider | *(required unless gateway mode)* |
| `DRAKELING_LLM_MODEL` | Model name (e.g. `gpt-4o-mini`, `llama3.3`) | *(required unless gateway mode)* |
| `DRAKELING_USE_OPENCLAW_GATEWAY` | Delegate LLM calls to OpenClaw gateway | `false` |
| `DRAKELING_OPENCLAW_GATEWAY_URL` | Gateway URL | `http://127.0.0.1:18789` |
| `DRAKELING_OPENCLAW_GATEWAY_TOKEN` | Bearer token for the gateway | *(unset)* |
| `DRAKELING_OPENCLAW_GATEWAY_MODEL` | Model to request from the gateway (omit to use gateway default) | *(unset)* |
| `DRAKELING_MAX_TOKENS_PER_CALL` | Per-call token cap | `300` |
| `DRAKELING_MAX_TOKENS_PER_DAY` | Daily token budget | `10000` |
| `DRAKELING_TICK_SECONDS` | Background loop interval (seconds, minimum 10) | `60` |
| `DRAKELING_MIN_REFLECTION_INTERVAL` | Minimum seconds between background reflections | `600` |
| `DRAKELING_PORT` | Daemon HTTP port | `52780` |

### LLM configuration

Your creature needs an LLM provider to talk and reflect. On first run,
`drakelingd` walks you through setup interactively. You can also configure it
manually by editing the `.env` file in the data directory.

#### Option A — Any OpenAI-compatible LLM provider

Works with OpenAI, Ollama, vLLM, LiteLLM, or any service that exposes an
OpenAI-compatible `/v1` endpoint.

```dotenv
DRAKELING_LLM_BASE_URL=https://api.openai.com/v1
DRAKELING_LLM_API_KEY=sk-...
DRAKELING_LLM_MODEL=gpt-4o-mini
```

For local LLMs (e.g. Ollama), the API key can be any non-empty string:

```dotenv
DRAKELING_LLM_BASE_URL=http://127.0.0.1:11434/v1
DRAKELING_LLM_API_KEY=ollama-local
DRAKELING_LLM_MODEL=llama3.3
```

#### Option B — OpenClaw gateway delegation

If you already run OpenClaw, this is the easiest option. Any model OpenClaw
supports (cloud or local) becomes available to Drakeling with no additional
provider configuration.

```dotenv
DRAKELING_USE_OPENCLAW_GATEWAY=true
# DRAKELING_OPENCLAW_GATEWAY_URL=    # leave blank for default http://127.0.0.1:18789
# DRAKELING_OPENCLAW_GATEWAY_TOKEN=  # leave blank if gateway has no auth
```

## Export and import

### Export (backup)

Your creature can be exported as an encrypted `.drakeling` bundle file
containing the database and identity key.

```bash
curl -X POST http://127.0.0.1:52780/export \
  -H "Authorization: Bearer $(cat ~/.local/share/drakeling/api_token)" \
  -H "Content-Type: application/json" \
  -d '{"passphrase": "your-secret-passphrase", "output_path": "/tmp/my-dragon.drakeling"}'
```

### Import (restore / migrate)

To import a bundle onto a new machine, start the daemon in import-ready mode:

```bash
drakelingd --allow-import
```

Then send the import request:

```bash
curl -X POST http://127.0.0.1:52780/import \
  -H "Authorization: Bearer $(cat ~/.local/share/drakeling/api_token)" \
  -H "Content-Type: application/json" \
  -d '{"passphrase": "your-secret-passphrase", "bundle_path": "/tmp/my-dragon.drakeling"}'
```

The daemon creates a `.bak` backup before importing and rolls back automatically
if anything goes wrong. After a successful import, restart the daemon normally
(without `--allow-import`).

## CLI reference

### `drakelingd`

| Flag | Description |
|---|---|
| *(no flags)* | Normal production mode |
| `--dev` | Development mode: verbose stdout logging, no background reflection, import always permitted |
| `--allow-import` | Enable the `POST /import` endpoint (disabled by default for safety) |

### `drakeling`

No flags. Connects to the local daemon and launches the interactive terminal UI.

## Running as a service

For production use, the daemon should run as a background service that starts
automatically on login. Template files are provided in `deploy/`.

### Linux — systemd

```bash
cp deploy/drakeling.service ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now drakeling
```

Check status: `systemctl --user status drakeling`

### macOS — launchd

```bash
cp deploy/drakeling.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/drakeling.plist
```

### Windows — Task Scheduler

```powershell
schtasks /create /tn "Drakeling" /tr "drakelingd" /sc onlogon /rl limited /f
```

Or import `deploy/drakeling-task.xml` via the Task Scheduler GUI.

## OpenClaw Skill setup

This lets OpenClaw agents check on your hatchling and give it care autonomously.

1. Install the skill: `clawhub install drakeling` (or copy `skill/` to `~/.openclaw/skills/drakeling/`)
2. Start the daemon at least once: `drakelingd`
3. Read the API token:
   - Linux: `cat ~/.local/share/drakeling/api_token`
   - macOS: `cat ~/Library/Application\ Support/drakeling/api_token`
   - Windows: `type "%APPDATA%\drakeling\drakeling\api_token"`
4. Add to `~/.openclaw/openclaw.json` under `skills.entries.drakeling`:
   ```json
   {
     "skills": {
       "entries": {
         "drakeling": {
           "env": {
             "DRAKELING_API_TOKEN": "paste-token-here"
           }
         }
       }
     }
   }
   ```

See [docs/openclaw_integration.md](docs/openclaw_integration.md) for the full OpenClaw integration guide (config format, gateway delegation, and references).

The skill only uses `/status` (read) and `/care` (write). It never calls
`/talk`, `/rest`, `/export`, or `/import`.

## Development

### Setup

```bash
git clone https://github.com/BVisagie/drakeling.git
cd drakeling
```

Using pip:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

Using pipx:

```bash
pipx install --editable .
```

Using uv:

```bash
uv venv
source .venv/bin/activate
uv pip install -e ".[dev]"
```

### Running in dev mode

```bash
drakelingd --dev
```

Dev mode:
- Logs all lifecycle events and token usage to stdout
- Disables background reflection (tick loop still runs for stat decay)
- Permits import without `--allow-import`

### Running tests

```bash
pytest
```

The test suite covers domain models, trait generation, stat decay/boost,
lifecycle transitions, crypto (identity, tokens, encrypted bundles), sprites,
and API integration tests.

### Project structure

```
src/drakeling/
  domain/         Pure domain logic (models, traits, decay, lifecycle, sprites)
  crypto/         Ed25519 identity, API tokens, encrypted bundles
  storage/        SQLAlchemy models and database init
  llm/            LLM wrapper and prompt construction
  daemon/         Daemon entry point, config, background tick loop
  api/            FastAPI endpoints (birth, status, care, talk, rest, export/import)
  ui/             Textual terminal UI (birth ceremony, main screen, widgets)
```
