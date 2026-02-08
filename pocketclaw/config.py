from pathlib import Path
import os
import yaml

POCKETCLAW_DIR = Path.home() / ".pocketclaw"

# env var name -> (config key, provider name)
_ENV_KEYS = {
    "ANTHROPIC_API_KEY": ("anthropic", "claude-sonnet-4-20250514"),
    "OPENAI_API_KEY": ("openai", "gpt-4o"),
    "DEEPSEEK_API_KEY": ("deepseek", "deepseek-chat"),
    "GROQ_API_KEY": ("groq", "llama-3.3-70b-versatile"),
    "GOOGLE_API_KEY": ("google", "gemini-2.0-flash"),
}


def _load_env(*search_paths):
    """Load .env file into os.environ. No dependencies."""
    for p in search_paths:
        path = Path(p).expanduser()
        if path.exists():
            for line in path.read_text().splitlines():
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())
            return

DEFAULTS = {
    "llm": {
        "provider": "anthropic",
        "model": "claude-sonnet-4-20250514",
        "max_tokens": 4096,
        "temperature": 0.3,
    },
    "interfaces": {"terminal": True},
    "skills": {
        "paths": [
            "~/.pocketclaw/app/skills/builtin",
            "~/.pocketclaw/app/skills/official",
            "~/.pocketclaw/skills/community",
            "~/.pocketclaw/skills/custom",
        ],
        "disabled": [],
    },
    "memory": {
        "path": "~/.pocketclaw/memory",
        "max_conversation_messages": 50,
        "auto_summarise": True,
    },
    "confirm": {
        "file_delete": True,
        "send_messages": True,
        "shell_commands": False,
        "screen_actions": False,
        "money": True,
    },
    "display": {"color": True, "streaming": True, "show_tool_calls": True},
    "advanced": {
        "max_tool_iterations": 50,
        "tool_timeout": 30,
        "screenshot_scale": 0.5,
    },
}


def _merge(base, over):
    out = base.copy()
    for k, v in over.items():
        if k in out and isinstance(out[k], dict) and isinstance(v, dict):
            out[k] = _merge(out[k], v)
        else:
            out[k] = v
    return out


class Config:
    def __init__(self, path=None):
        self.path = Path(path) if path else POCKETCLAW_DIR / "config.yaml"

        # Load .env from project dir, install dir, or cwd
        _load_env(".env", POCKETCLAW_DIR / ".env", Path.cwd() / ".env")

        raw = {}
        if self.path.exists():
            raw = yaml.safe_load(self.path.read_text()) or {}
        self._data = _merge(DEFAULTS, raw)

        # Auto-detect API key from env vars if not in config
        if not self.get("llm.api_key"):
            for env_var, (provider, model) in _ENV_KEYS.items():
                key = os.environ.get(env_var)
                if key:
                    self._data["llm"]["api_key"] = key
                    self._data["llm"]["provider"] = provider
                    self._data["llm"]["model"] = model
                    break

    def get(self, key, default=None):
        val = self._data
        for k in key.split("."):
            if not isinstance(val, dict):
                return default
            val = val.get(k)
            if val is None:
                return default
        return val

    def set(self, key, value):
        d = self._data
        keys = key.split(".")
        for k in keys[:-1]:
            d = d.setdefault(k, {})
        d[keys[-1]] = value

    def save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(yaml.dump(self._data, default_flow_style=False))

    @property
    def data(self):
        return self._data
