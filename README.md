# PocketClaw

AI agent for Android. Runs in Termux. Controls your phone with natural language.

Model-agnostic — works with Claude, GPT-4o, DeepSeek, Gemini, Groq, Ollama, or any OpenAI-compatible API.

## What It Does

Talk to your phone like a person:

```
> what's my battery at?
73%, discharging.

> check my texts
3 messages — one from Mum: "Call me when you get a chance love x"

> create a python script that checks disk usage and run it
[writes file, executes it, returns output]

> check what packages are installed
Got it, remembered.
```

It has full access to your device through three layers:
- **Layer 1** — Shell commands, APIs, file ops, HTTP requests (fastest)
- **Layer 2** — Screen reading via accessibility XML (for apps without APIs)
- **Layer 3** — Screenshots + vision (last resort)

## Prerequisites

1. **Termux** — install from [F-Droid](https://f-droid.org/packages/com.termux/), NOT the Play Store
2. **Termux:API** — install from [F-Droid](https://f-droid.org/packages/com.termux.api/), then run:
   ```
   pkg install termux-api
   ```
3. An API key from any supported provider (Anthropic, OpenAI, DeepSeek, Google, Groq — or run local with Ollama)

## Install

Open Termux and run:

```bash
curl -sL https://raw.githubusercontent.com/pocketclaw/pocketclaw/main/install.sh | bash
```

Takes ~2 minutes. Then run `pocket` — the setup wizard will ask for your API key on first launch.

## Usage

```bash
pocket                          # interactive chat
pocket "send sms to mum"       # one-shot command
pocket onboard                  # re-run setup wizard
pocket skills                   # list loaded skills
pocket memory                   # see what it remembers
pocket doctor                   # check everything works
pocket help                     # full command list
```

## How It Works

```
┌──────────────────────────────────────────┐
│              PocketClaw                   │
│                                          │
│  Terminal ──> Gateway ──> LLM (any)      │
│                 │                         │
│          ┌──────┼──────┐                  │
│          ▼      ▼      ▼                  │
│       Shell   Screen  Vision              │
│       + API   (a11y)  (screenshot)        │
│                                          │
│       Memory    Skills    Android Bridge  │
└──────────────────────────────────────────┘
```

- **Gateway** — core agentic loop. Sends messages to LLM, executes tool calls, loops until done.
- **Skills** — markdown files that define tools. No code needed for simple skills.
- **Memory** — persists facts, conversations, and user identity across sessions.
- **LLM Connector** — speaks Anthropic and OpenAI formats. Swap providers by changing one config value.

## Skills

Skills are markdown files with YAML frontmatter. Built-in skills:

| Skill | Tools | Layer |
|-------|-------|-------|
| shell | `run_shell`, `run_python`, `read_file`, `write_file`, `edit_file`, `list_directory`, `http_request` | 1 |
| android | `termux_api` (SMS, calls, GPS, battery, camera, clipboard, notifications) | 1 |
| system | `screen_read`, `screen_tap_element`, `screen_type_text`, `screen_scroll`, `screenshot` | 2+3 |
| termux | Termux environment knowledge (paths, packages, gotchas) | context |
| web | HTTP request patterns and scraping | context |

Add your own in `~/.pocketclaw/skills/custom/`.

## Config

Edit `~/.pocketclaw/config.yaml` or use:

```bash
pocket config set llm.model gpt-4o
pocket config set llm.provider anthropic
```

API keys go in `~/.pocketclaw/.env`:

```
OPENAI_API_KEY=sk-...
# or
ANTHROPIC_API_KEY=sk-ant-...
```

## Requirements

- Android 7+ with Termux
- Python 3.10+
- 2 Python packages: `httpx`, `pyyaml`
- Internet (for cloud LLMs) or Ollama (for local)

## Battery Tip

Android kills background processes. To keep PocketClaw alive:

1. Disable battery optimisation for Termux in Android Settings
2. PocketClaw auto-acquires a wake lock on startup

Manufacturer-specific guides are in the `termux` skill — ask PocketClaw: *"how do I stop Android killing Termux?"*

## License

MIT
