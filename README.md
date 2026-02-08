# PocketClaw — AI Agent for Android

<p align="center">
  <strong>Your phone. Your agent. Your rules.</strong>
</p>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-blue.svg?style=for-the-badge" alt="MIT License"></a>
  <a href="https://github.com/pocketclaw/pocketclaw/releases"><img src="https://img.shields.io/github/v/release/pocketclaw/pocketclaw?include_prereleases&style=for-the-badge" alt="GitHub release"></a>
</p>

**PocketClaw** is a personal AI agent that runs on Android via [Termux](https://termux.dev). It gives any LLM full control of your phone and a Linux environment through natural language. Model-agnostic, lightweight, extensible, and installable in under 2 minutes.

No servers. No telemetry. No accounts. Everything runs locally on your device.

[Getting Started](#install) &middot; [Skills](#skills) &middot; [Creating Skills](#creating-a-skill) &middot; [Configuration](#configuration) &middot; [Architecture](#how-it-works) &middot; [Security](#security) &middot; [CLI Reference](#cli-reference)

---

## Install

**Prerequisites:** [Termux](https://f-droid.org/packages/com.termux/) + [Termux:API](https://f-droid.org/packages/com.termux.api/) from F-Droid (not the Play Store). An API key from any supported provider.

```bash
curl -sL https://raw.githubusercontent.com/pocketclaw/pocketclaw/main/install.sh | bash
```

Takes ~2 minutes. Then run `pocket` — the setup wizard asks for your provider and API key on first launch.

```bash
pocket                          # start interactive chat
pocket "check my texts"         # one-shot command
pocket doctor                   # verify everything works
```

## Quick start (TL;DR)

```bash
# Install
curl -sL https://raw.githubusercontent.com/pocketclaw/pocketclaw/main/install.sh | bash
source ~/.bashrc

# Configure (add your API key)
nano ~/.pocketclaw/config.yaml

# Go
pocket
```

Runtime: **Python 3.10+**, 2 dependencies (`httpx`, `pyyaml`). Runs on Android 7+ with 2 GB RAM.

## Supported models

Any model, any provider. Swap by changing one config value.

| Provider | Default model | Format |
|----------|---------------|--------|
| **Anthropic** | claude-sonnet-4-20250514 | native |
| **OpenAI** | gpt-4o | openai |
| **DeepSeek** | deepseek-chat | openai |
| **Google** | gemini-2.0-flash | google |
| **Groq** | llama-3.3-70b-versatile | openai |
| **Ollama** | llama3.2 (local) | openai |
| **Custom** | any OpenAI-compatible endpoint | openai |

Model recommendation: **Anthropic Claude** for best tool-use reliability and prompt-injection resistance. **Ollama** for fully offline, zero-cost local inference.

## How it works

```
┌──────────────────────────────────────────────────────┐
│                     PocketClaw                       │
│                                                      │
│  Terminal ───> Gateway (agentic loop) ───> LLM (any) │
│                    │                                  │
│         ┌──────────┼──────────┐                       │
│         ▼          ▼          ▼                       │
│     Layer 1     Layer 2    Layer 3                    │
│    Shell/API   Screen XML  Vision                    │
│    (instant)    (fast)     (slow)                    │
│                                                      │
│    Memory ─── Skills ─── Android Bridge              │
└──────────────────────────────────────────────────────┘
```

### Three execution layers

The agent always picks the fastest path. Screenshots are a last resort.

- **Layer 1 — APIs & Shell** (preferred): `run_shell`, `run_python`, `http_request`, `termux_api`. Direct programmatic access — file ops, git, SSH, SMS, calls, GPS, clipboard, camera, notifications, and any CLI or web API. Sub-100ms for most operations.
- **Layer 2 — Accessibility XML** (fast): `screen_read`, `screen_tap_element`, `screen_type_text`, `screen_scroll`. Reads the UI hierarchy as structured data. No screenshots, no vision model needed. For apps that don't expose APIs.
- **Layer 3 — Screenshots + Vision** (last resort): `screenshot`, `screen_tap_coordinates`. Takes a screenshot, sends to a vision-capable model. Only when Layer 2 can't parse the screen (games, image-heavy UIs).

### Key subsystems

- **Gateway** — the core agentic loop. Receives messages, sends to LLM with tools, executes tool calls, repeats until done. Stateless — all state lives in files. Kill and restart, lose nothing.
- **LLM Connector** — speaks Anthropic, OpenAI, and Google formats natively. Translates tools, messages, and responses between providers transparently. Handles vision inputs for Layer 3.
- **Memory** — persists conversations, user identity, and learned facts across sessions. The agent remembers your name, preferences, and context between conversations.
- **Skill Loader** — reads markdown skill files, extracts YAML tool definitions, loads optional Python handlers. Hot-reloads on change.
- **Android Bridge** — wraps Termux:API commands and screen control. Auto-detects device capabilities on startup.

## Skills

Skills define what tools the LLM has access to. A skill is a **markdown file** with YAML frontmatter — that's it. No code required for simple skills.

### Built-in skills

| Skill | What it does | Layer |
|-------|-------------|-------|
| **shell** | `run_shell`, `run_python`, `read_file`, `write_file`, `edit_file`, `list_directory`, `http_request` | 1 |
| **android** | `termux_api` — SMS, calls, GPS, battery, camera, clipboard, notifications, torch, TTS, vibrate | 1 |
| **system** | `screen_read`, `screen_tap_element`, `screen_type_text`, `screen_scroll`, `screenshot`, `screen_tap_coordinates` | 2 + 3 |
| **termux** | Termux environment knowledge — paths, packages, quirks | context |
| **web** | HTTP patterns, scraping, API usage | context |

### Skill directories

```
~/.pocketclaw/
├── app/skills/builtin/     # ships with PocketClaw
├── app/skills/official/    # maintained by PocketClaw team
├── skills/community/       # downloaded from Skill Hub
└── skills/custom/          # your own skills
```

Precedence: custom > community > official > builtin. A custom skill with the same name overrides a builtin.

## Creating a skill

Skills are markdown files with YAML frontmatter that declare tools. The LLM reads the skill description and uses built-in tools (`run_shell`, `http_request`, etc.) to accomplish the task. Most skills need **zero code**.

### Minimal skill (no handler)

Create `~/.pocketclaw/skills/custom/weather.md`:

```markdown
---
name: weather
version: 1.0.0
description: Get weather information for any location
layer: 1
category: utility
tools:
  - name: get_weather
    description: "Get current weather and forecast via wttr.in. No API key needed."
    parameters:
      location:
        type: string
        description: "City name or coordinates"
        required: true
      format:
        type: string
        description: "'brief' for one-line, 'detailed' for full forecast"
        required: false
---

# Weather Skill

Get weather using the free wttr.in service.

## How to execute

Use `run_shell` with: `curl -s "wttr.in/{location}?format=3"` for brief
or `curl -s "wttr.in/{location}"` for detailed.

## Examples

- "What's the weather in London?" -> `curl -s "wttr.in/London?format=3"`
- "3-day forecast for Tokyo?" -> `curl -s "wttr.in/Tokyo?3"`
```

That's a complete skill. The LLM reads it, understands that `get_weather` maps to a curl command, and executes via `run_shell`. No Python needed.

### Skill with a Python handler

For skills that need custom logic beyond shell commands, reference a handler file:

```markdown
---
name: gmail
version: 1.0.0
description: Read, search, and send Gmail
layer: 1
category: communication
requires:
  - termux-api
setup: |
  pip install google-auth google-auth-oauthlib google-api-python-client
config:
  credentials_path: ~/.pocketclaw/gmail_credentials.json
tools:
  - name: gmail_read
    description: "Read emails from Gmail."
    parameters:
      query:
        type: string
        description: "Gmail search query (e.g. 'is:unread', 'from:jane@example.com')"
        required: true
      max_results:
        type: integer
        description: "Max emails to return (default 10)"
        required: false
  - name: gmail_send
    description: "Send an email via Gmail."
    parameters:
      to:
        type: string
        description: "Recipient email"
        required: true
      subject:
        type: string
        description: "Subject line"
        required: true
      body:
        type: string
        description: "Email body"
        required: true
handler: gmail_handler.py
---

# Gmail Skill

Direct Gmail access via the Gmail API. Bypasses the Gmail app entirely.

## Setup

Run `pocket setup gmail` to authenticate with Google OAuth2.
```

The handler file (`gmail_handler.py`) sits next to the skill markdown and implements the tool functions:

```python
from pocketclaw.skill import SkillHandler

class GmailHandler(SkillHandler):
    async def gmail_read(self, query: str, max_results: int = 10) -> dict:
        service = self.get_gmail_service()
        results = service.users().messages().list(
            userId='me', q=query, maxResults=max_results
        ).execute()
        # ... process and return

    async def gmail_send(self, to: str, subject: str, body: str) -> dict:
        # ... compose and send
```

### Skill frontmatter reference

| Field | Required | Description |
|-------|----------|-------------|
| `name` | yes | Unique skill identifier |
| `version` | yes | Semver version |
| `description` | yes | What the skill does (shown in system prompt) |
| `layer` | no | Primary execution layer: `1`, `2`, or `3` |
| `category` | no | Grouping: `core`, `communication`, `utility`, `finance`, etc. |
| `tools` | yes | Array of tool definitions with `name`, `description`, `parameters` |
| `handler` | no | Python handler file (relative path). Omit for no-code skills. |
| `requires` | no | System requirements (e.g. `termux-api`) |
| `setup` | no | One-time setup commands |
| `config` | no | Config keys the skill reads |
| `permissions` | no | `shell`, `filesystem`, `network`, `sms`, `camera`, `location`, `screen` |

### Publishing to Skill Hub

```bash
pocket hub publish ~/.pocketclaw/skills/custom/my-skill.md
```

Skills are validated before publishing: valid YAML, required fields present, no hardcoded secrets, handler file exists (if referenced).

Treat third-party skills as **untrusted code**. Read them before enabling. Handler files run in the same Python environment.

## Configuration

Edit `~/.pocketclaw/config.yaml` directly, or use the CLI:

```bash
pocket config set llm.provider anthropic
pocket config set llm.model claude-sonnet-4-20250514
pocket config get llm.provider
```

### Minimal config

```yaml
llm:
  provider: anthropic
  api_key: sk-ant-xxxxx
  model: claude-sonnet-4-20250514
  max_tokens: 4096
  temperature: 0.3
```

API keys can also go in `~/.pocketclaw/.env`:

```
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
```

### Full config reference

```yaml
llm:
  provider: anthropic         # anthropic | openai | deepseek | google | groq | ollama | custom
  api_key: ""                 # or use .env file
  model: claude-sonnet-4-20250514
  max_tokens: 4096
  temperature: 0.3

interfaces:
  terminal: true

skills:
  paths:
    - ~/.pocketclaw/app/skills/builtin
    - ~/.pocketclaw/app/skills/official
    - ~/.pocketclaw/skills/community
    - ~/.pocketclaw/skills/custom
  disabled: []

memory:
  path: ~/.pocketclaw/memory
  max_conversation_messages: 50
  auto_summarise: true

confirm:
  file_delete: true           # confirm before deleting files
  send_messages: true         # confirm before sending SMS/email
  shell_commands: false       # don't nag on routine shell commands
  screen_actions: false
  money: true                 # always confirm money-related actions

display:
  color: true
  streaming: true
  show_tool_calls: true

advanced:
  max_tool_iterations: 50
  tool_timeout: 30
  screenshot_scale: 0.5
```

## Security

1. **Everything local.** No PocketClaw servers, no telemetry, no analytics.
2. **API keys stored in config.** Your responsibility to secure your device.
3. **Skills declare permissions.** User confirms on first use.
4. **Dangerous actions need confirmation.** `rm -rf`, sending messages, anything involving money. Configurable per category.
5. **No auto-updates.** User explicitly runs `pocket update`.

Skills declare required permissions in their frontmatter:

```yaml
permissions:
  - shell
  - network
  - sms
```

On first use:

```
Skill 'gmail' requires: [network, filesystem]
Allow? (y/n)
```

Power users can disable confirmation per category in `config.yaml` under `confirm:`.

## Memory

The agent remembers things across conversations. Memory lives in `~/.pocketclaw/memory/`:

```
memory/
├── identity.md              # your persona + preferences (user-editable)
├── facts.json               # learned facts (auto-populated)
├── conversations/           # chat history
└── summaries/               # compressed old conversations
```

Edit `identity.md` to shape how the agent behaves:

```bash
pocket memory edit            # open identity.md in your editor
pocket memory                 # see stored facts
pocket memory clear           # clear conversation history
```

The LLM has a `memory` tool — it can `remember`, `recall`, and `forget` facts during conversation.

## CLI reference

### Commands

```
pocket                          Start interactive chat
pocket "send sms to mum"       One-shot command (run and exit)
pocket start --daemon           Start background daemon
pocket stop                     Stop daemon
pocket status                   Running state + uptime

pocket skills                   List loaded skills
pocket skills enable <name>     Enable a skill
pocket skills disable <name>    Disable a skill

pocket hub search <query>       Search Skill Hub
pocket hub install <name>       Install community skill
pocket hub update               Update community skills

pocket setup <skill>            Run setup for a specific skill
pocket config                   Open config in editor
pocket config set <key> <val>   Set config value
pocket config get <key>         Get config value

pocket cost                     Today's API usage
pocket cost --week              This week
pocket cost --month             This month

pocket memory                   Show stored facts
pocket memory edit              Edit identity.md
pocket memory clear             Clear history

pocket doctor                   Run diagnostics
pocket update                   Update PocketClaw
pocket help                     Show help
```

### Slash commands (inside chat)

```
/help       Show commands
/clear      Clear conversation
/new        New conversation
/skills     List active skills
/cost       Session API cost
/memory     What the agent remembers
/export     Export conversation as markdown
/debug      Toggle debug mode
```

## Battery & persistence

Android kills background processes aggressively. PocketClaw handles this:

1. Auto-acquires Termux wake lock on startup
2. Runs as a foreground notification when in daemon mode
3. Disable battery optimisation for Termux in Android Settings

Manufacturer-specific guides (Xiaomi, Samsung, Huawei, Oppo) — ask PocketClaw: *"how do I stop Android killing Termux?"*

`pocket doctor` detects battery management issues and walks you through fixes.

## Requirements

| Requirement | Minimum | Recommended |
|------------|---------|-------------|
| Android | 7.0+ | 10+ |
| RAM | 2 GB | 4+ GB |
| Storage | 300 MB | 500 MB |
| Termux | F-Droid (not Play Store) | Latest |
| Termux:API | F-Droid | Latest |
| Python | 3.10+ | 3.11+ |
| Core deps | `httpx`, `pyyaml` | — |

## License

MIT
