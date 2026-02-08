import asyncio
import sys
from .config import Config
from .gateway import Gateway
from .supervisor import Supervisor


def _needs_setup(config):
    return not config.get("llm.api_key")


async def main(args=None):
    args = args or sys.argv[1:]
    config = Config()

    # Auto-trigger onboarding if no API key configured
    if _needs_setup(config) and (not args or args[0] not in ("help", "--help", "version", "--version", "doctor", "onboard")):
        print("No API key found. Let's set up PocketClaw.\n")
        from .onboard import run as onboard
        onboard()
        config = Config()  # reload after onboarding
        if _needs_setup(config):
            print("Setup incomplete - run 'pocket onboard' to try again.")
            return

    if not args:
        await _interactive(config)
        return

    cmd = args[0]

    if cmd in ("help", "--help", "-h"):
        _print_help()
    elif cmd in ("version", "--version", "-v"):
        from . import __version__
        print(f"PocketClaw v{__version__}")
    elif cmd == "onboard":
        from .onboard import run as onboard
        onboard()
    elif cmd == "status":
        if Supervisor.is_running():
            print(f"PocketClaw is running (PID {Supervisor.get_pid()})")
        else:
            print("PocketClaw is not running")
    elif cmd == "stop":
        if Supervisor.is_running():
            Supervisor.kill()
            print("PocketClaw stopped")
        else:
            print("PocketClaw is not running")
    elif cmd == "config":
        _handle_config(config, args[1:])
    elif cmd == "skills":
        from .skill_loader import SkillLoader
        print(SkillLoader(config).get_summary() or "No skills loaded.")
    elif cmd == "memory":
        _handle_memory(config, args[1:])
    elif cmd == "doctor":
        _doctor(config)
    else:
        # One-shot mode
        gateway = Gateway(config)
        sup = Supervisor()
        sup.start()
        try:
            response = await gateway.handle_message(" ".join(args))
            print(response)
        finally:
            await gateway.close()
            sup.stop()


async def _interactive(config):
    gateway = Gateway(config)
    sup = Supervisor()
    sup.start()
    try:
        from .interfaces.terminal import TerminalInterface
        await TerminalInterface(gateway, config).run()
    finally:
        await gateway.close()
        sup.stop()


def _handle_config(config, args):
    if len(args) >= 2 and args[0] == "set":
        key = args[1]
        val = args[2] if len(args) > 2 else ""
        config.set(key, val)
        config.save()
        print(f"Set {key} = {val}")
    elif len(args) >= 2 and args[0] == "get":
        print(config.get(args[1], "(not set)"))
    else:
        print(f"Config: {config.path}")


def _handle_memory(config, args):
    from .memory import MemoryStore
    mem = MemoryStore(config)
    if args and args[0] == "clear":
        import shutil
        conv_dir = mem.base / "conversations"
        if conv_dir.exists():
            shutil.rmtree(conv_dir)
            conv_dir.mkdir()
        print("Conversations cleared.")
    else:
        print(mem.get_context() or "No stored facts.")


def _print_help():
    print("""PocketClaw - AI agent for Android

Usage:
  pocket                      Start interactive chat
  pocket "do something"       One-shot command
  pocket onboard              Run setup wizard
  pocket status               Show running state
  pocket stop                 Stop daemon
  pocket skills               List loaded skills
  pocket memory               Show stored facts
  pocket memory clear         Clear conversations
  pocket config set KEY VAL   Set config value
  pocket config get KEY       Get config value
  pocket doctor               Run diagnostics
  pocket version              Show version
  pocket help                 Show this help
""")


def _doctor(config):
    import shutil
    print("PocketClaw Diagnostics\n")
    checks = [
        ("Python", True, f"{sys.version_info.major}.{sys.version_info.minor}"),
        ("Termux:API", shutil.which("termux-battery-status") is not None, ""),
        ("Config", config.path.exists(), str(config.path)),
        ("API key", bool(config.get("llm.api_key")), config.get("llm.provider", "?")),
    ]
    for name, ok, detail in checks:
        sym = "+" if ok else "!"
        status = "ok" if ok else "MISSING"
        extra = f" ({detail})" if detail else ""
        print(f"  [{sym}] {name}{extra}: {status}")
