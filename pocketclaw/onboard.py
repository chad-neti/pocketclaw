import asyncio
import os
from pathlib import Path
from .config import Config, POCKETCLAW_DIR

C = "\033[36m"
G = "\033[32m"
Y = "\033[33m"
R = "\033[0m"
B = "\033[1m"

PROVIDERS = [
    ("anthropic", "Anthropic (Claude)", "ANTHROPIC_API_KEY", "claude-sonnet-4-20250514"),
    ("openai", "OpenAI (GPT-4o)", "OPENAI_API_KEY", "gpt-4o"),
    ("deepseek", "DeepSeek", "DEEPSEEK_API_KEY", "deepseek-chat"),
    ("google", "Google (Gemini)", "GOOGLE_API_KEY", "gemini-2.0-flash"),
    ("groq", "Groq (Llama)", "GROQ_API_KEY", "llama-3.3-70b-versatile"),
    ("ollama", "Ollama (local - no key needed)", "OLLAMA_API_KEY", "llama3.2"),
]


def run():
    print(f"\n{C}{B}PocketClaw{R} setup\n")

    # -- Name ----------------------------------------------
    name = input(f"  What's your name? {B}>{R} ").strip() or "User"

    # -- Provider ------------------------------------------
    print(f"\n  Which AI provider?\n")
    for i, (_, label, _, _) in enumerate(PROVIDERS, 1):
        print(f"    {i}. {label}")
    print(f"    7. Custom endpoint")

    choice = input(f"\n  {B}>{R} ").strip()
    try:
        idx = int(choice) - 1
    except ValueError:
        idx = 0

    if idx == 6:
        # Custom
        provider = "custom"
        base_url = input(f"  Base URL: {B}>{R} ").strip()
        model = input(f"  Model name: {B}>{R} ").strip()
        api_key = input(f"  API key (blank if none): {B}>{R} ").strip()
    elif 0 <= idx < len(PROVIDERS):
        provider, _, env_name, model = PROVIDERS[idx]
        if provider == "ollama":
            api_key = ""
            print(f"\n  {G}[+]{R} Ollama - no API key needed.")
        else:
            api_key = input(f"\n  Paste your API key: {B}>{R} ").strip()
        base_url = None
    else:
        provider, _, _, model = PROVIDERS[0]
        api_key = input(f"\n  Paste your Anthropic API key: {B}>{R} ").strip()
        base_url = None

    # -- Test connection -----------------------------------
    if api_key and provider != "ollama":
        print(f"\n  Testing connection...", end=" ", flush=True)
        if _test_key(provider, api_key, model, base_url):
            print(f"{G}connected to {model}{R}")
        else:
            print(f"{Y}couldn't verify (may still work){R}")

    # -- Vibe ----------------------------------------------
    print(f"\n  Pick a vibe:\n")
    print(f"    1. Sharp & efficient (minimal chat, maximum action)")
    print(f"    2. Friendly & helpful (balanced)")
    print(f"    3. Custom (edit identity.md later)")

    vibe = input(f"\n  {B}>{R} ").strip()

    # -- Save everything -----------------------------------
    _save_config(provider, api_key, model, base_url)
    _save_identity(name, vibe)
    _save_env(provider, api_key)
    _save_facts(name)

    print(f"\n  {G}All set!{R} Type {B}pocket{R} to start chatting.\n")
    print(f"  Quick commands:")
    print(f"    pocket skills          List available skills")
    print(f"    pocket doctor          Check everything works")
    print(f"    pocket help            Full command reference\n")


def _test_key(provider, api_key, model, base_url=None):
    try:
        import httpx
        if provider == "anthropic":
            url = "https://api.anthropic.com/v1/messages"
            r = httpx.post(url, headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            }, json={
                "model": model, "max_tokens": 10,
                "messages": [{"role": "user", "content": "hi"}],
            }, timeout=10)
        else:
            urls = {
                "openai": "https://api.openai.com/v1",
                "deepseek": "https://api.deepseek.com/v1",
                "groq": "https://api.groq.com/openai/v1",
                "google": "https://generativelanguage.googleapis.com/v1beta",
            }
            burl = base_url or urls.get(provider, "https://api.openai.com/v1")
            r = httpx.post(f"{burl}/chat/completions", headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            }, json={
                "model": model, "max_tokens": 10,
                "messages": [{"role": "user", "content": "hi"}],
            }, timeout=10)
        return r.status_code == 200
    except Exception:
        return False


def _save_config(provider, api_key, model, base_url):
    config = Config()
    config.set("llm.provider", provider)
    config.set("llm.model", model)
    if base_url:
        config.set("llm.base_url", base_url)
    # Don't save API key to config - keep it in .env
    config.save()


def _save_env(provider, api_key):
    if not api_key:
        return
    env_names = {
        "anthropic": "ANTHROPIC_API_KEY",
        "openai": "OPENAI_API_KEY",
        "deepseek": "DEEPSEEK_API_KEY",
        "groq": "GROQ_API_KEY",
        "google": "GOOGLE_API_KEY",
    }
    env_var = env_names.get(provider, "API_KEY")
    env_path = POCKETCLAW_DIR / ".env"
    env_path.parent.mkdir(parents=True, exist_ok=True)
    env_path.write_text(f"{env_var}={api_key}\n", encoding='utf-8')


def _save_identity(name, vibe):
    mem_dir = POCKETCLAW_DIR / "memory"
    mem_dir.mkdir(parents=True, exist_ok=True)
    identity_path = mem_dir / "identity.md"

    # Read default template
    default = Path(__file__).parent.parent / "identity.default.md"
    if default.exists():
        template = default.read_text(encoding='utf-8')
    else:
        template = "# PocketClaw\n\n## About Me\n- Name: {name}\n"

    # Fill in name
    template = template.replace("- Name:", f"- Name: {name}")

    # Set voice based on vibe
    if vibe == "1":
        template = template.replace(
            "- Match the user's energy.",
            "- Match the user's energy.\n- Default to terse. One-liners preferred. Skip pleasantries.",
        )
    elif vibe == "2":
        template = template.replace(
            "- Match the user's energy.",
            "- Match the user's energy.\n- Be warm but not chatty. Light humour is fine.",
        )

    identity_path.write_text(template, encoding='utf-8')


def _save_facts(name):
    import json
    facts_path = POCKETCLAW_DIR / "memory" / "facts.json"
    facts_path.parent.mkdir(parents=True, exist_ok=True)
    facts = {}
    if facts_path.exists():
        facts = json.loads(facts_path.read_text(encoding='utf-8'))
    facts["user_name"] = name
    facts_path.write_text(json.dumps(facts, indent=2), encoding='utf-8')
