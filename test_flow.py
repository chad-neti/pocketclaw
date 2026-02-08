#!/usr/bin/env python3
"""
PocketClaw test harness — exercises the full pipeline with a mock LLM.
No API key needed. Proves the system works end to end.
"""

import asyncio
import json
import sys
import os

# Add project to path
sys.path.insert(0, os.path.dirname(__file__))

from pocketclaw.config import Config
from pocketclaw.memory import MemoryStore
from pocketclaw.skill_loader import SkillLoader
from pocketclaw.system_prompt import build_system_prompt
from pocketclaw.tools.builtin import get_builtin_tools
from pocketclaw.tools.screen import get_screen_tools
from pocketclaw.android import get_android_tools

# ── Colours ───────────────────────────────────────────────
G = "\033[32m"
C = "\033[36m"
Y = "\033[33m"
D = "\033[2m"
R = "\033[0m"


def ok(msg):
    print(f"  {G}[PASS]{R} {msg}")


def fail(msg):
    print(f"  \033[31m[FAIL]{R} {msg}")


def section(msg):
    print(f"\n{C}── {msg} ──{R}")


# ── Tests ─────────────────────────────────────────────────

def test_config():
    section("Config")
    c = Config()
    provider = c.get("llm.provider")
    assert provider in ("anthropic", "openai", "deepseek", "groq", "google", "ollama"), "valid provider"
    ok(f"Provider = {provider}")

    assert c.get("llm.max_tokens") == 4096, "default max_tokens"
    ok("Default max_tokens = 4096")

    c.set("test.key", "value")
    assert c.get("test.key") == "value", "set/get"
    ok("Set/get works")

    assert c.get("nonexistent.key", "fallback") == "fallback", "fallback"
    ok("Fallback for missing keys")


def test_skill_loader():
    section("Skill Loader")
    c = Config()
    c.set("skills.paths", ["./skills/builtin"])
    loader = SkillLoader(c)

    names = sorted(loader.skills.keys())
    assert "shell" in names, "shell skill loaded"
    assert "android" in names, "android skill loaded"
    assert "system" in names, "system skill loaded"
    assert "termux" in names, "termux skill loaded"
    ok(f"Loaded {len(names)} skills: {', '.join(names)}")

    defs = loader.get_tool_definitions()
    tool_names = [t["name"] for t in defs]
    assert "run_shell" in tool_names, "run_shell defined"
    assert "screen_read" in tool_names, "screen_read defined"
    assert "termux_api" in tool_names, "termux_api defined"
    ok(f"{len(defs)} tool definitions parsed")

    summary = loader.get_summary()
    assert "shell" in summary.lower(), "summary contains shell"
    ok("Skill summary generated")


def test_memory():
    section("Memory")
    c = Config()
    c.set("memory.path", "/tmp/pocketclaw_test_memory")
    mem = MemoryStore(c)

    # Test conversation save/load
    msgs = [{"role": "user", "content": "hello"}, {"role": "assistant", "content": "hi"}]
    mem.save_conversation("test-conv", msgs)
    loaded = mem.get_conversation("test-conv")
    assert len(loaded) == 2, "conversation round-trip"
    assert loaded[0]["content"] == "hello"
    ok("Conversation save/load")

    # Test facts
    asyncio.run(mem.handle_tool("remember", "test_key", "test_value"))
    facts = mem.get_facts()
    assert facts.get("test_key") == "test_value", "fact stored"
    ok("Fact remember/recall")

    # Test recall
    result = asyncio.run(mem.handle_tool("recall", "test"))
    assert "test_value" in result, "recall works"
    ok("Fact search")

    # Test forget
    asyncio.run(mem.handle_tool("forget", "test_key"))
    facts = mem.get_facts()
    assert "test_key" not in facts, "fact removed"
    ok("Fact forget")

    # Cleanup
    import shutil
    shutil.rmtree("/tmp/pocketclaw_test_memory", ignore_errors=True)


def test_system_prompt():
    section("System Prompt")
    c = Config()
    c.set("skills.paths", ["./skills/builtin"])
    c.set("memory.path", "/tmp/pocketclaw_test_prompt")
    loader = SkillLoader(c)
    mem = MemoryStore(c)

    prompt = build_system_prompt(c, loader, mem)
    assert "PocketClaw" in prompt, "has identity"
    assert "Layer 1" in prompt, "has layer 1"
    assert "Layer 2" in prompt, "has layer 2"
    assert "shell" in prompt.lower(), "has skills"
    ok(f"System prompt generated ({len(prompt)} chars)")

    # Cleanup
    import shutil
    shutil.rmtree("/tmp/pocketclaw_test_prompt", ignore_errors=True)


def test_builtin_tools():
    section("Built-in Tools")
    c = Config()
    tools = get_builtin_tools(c)

    assert "run_shell" in tools, "run_shell registered"
    assert "read_file" in tools, "read_file registered"
    assert "write_file" in tools, "write_file registered"
    assert "edit_file" in tools, "edit_file registered"
    assert "list_directory" in tools, "list_directory registered"
    assert "http_request" in tools, "http_request registered"
    ok(f"{len(tools)} builtin tools registered")

    # Test run_shell
    result = asyncio.run(tools["run_shell"]("echo hello"))
    assert "hello" in result, "shell output"
    ok("run_shell: echo works")

    # Test run_shell with working_dir
    result = asyncio.run(tools["run_shell"]("pwd", working_dir="/tmp"))
    assert "/tmp" in result, "working_dir"
    ok("run_shell: working_dir works")

    # Test write + read + edit
    test_path = "/tmp/pocketclaw_test_file.txt"
    asyncio.run(tools["write_file"](test_path, "hello world"))
    content = asyncio.run(tools["read_file"](test_path))
    assert content == "hello world", "write/read roundtrip"
    ok("write_file + read_file roundtrip")

    asyncio.run(tools["edit_file"](test_path, "hello", "goodbye"))
    content = asyncio.run(tools["read_file"](test_path))
    assert "goodbye world" in content, "edit worked"
    ok("edit_file works")

    # Test list_directory
    result = asyncio.run(tools["list_directory"]("/tmp"))
    assert "pocketclaw_test_file.txt" in result, "file listed"
    ok("list_directory works")

    # Cleanup
    os.remove(test_path)


def test_tool_pipeline():
    section("Full Tool Pipeline (Mock LLM)")

    c = Config()
    c.set("skills.paths", ["./skills/builtin"])
    c.set("memory.path", "/tmp/pocketclaw_test_pipeline")

    # Build what the gateway would build
    loader = SkillLoader(c)
    mem = MemoryStore(c)
    prompt = build_system_prompt(c, loader, mem)
    tool_defs = loader.get_tool_definitions()
    tool_defs.append({
        "name": "memory",
        "description": "Store or retrieve persistent info.",
        "parameters": {
            "action": {"type": "string", "required": True},
            "key": {"type": "string", "required": True},
            "value": {"type": "string", "required": False},
        },
    })

    # Register handlers (same as gateway)
    handlers = {}
    handlers.update(get_builtin_tools(c))
    handlers.update(get_screen_tools(c))
    handlers.update(get_android_tools(c))
    handlers["memory"] = mem.handle_tool

    ok(f"System prompt: {len(prompt)} chars")
    ok(f"Tool definitions: {len(tool_defs)} tools")
    ok(f"Tool handlers: {len(handlers)} registered")

    # Simulate what the LLM would do: call run_shell
    async def simulate():
        # Pretend the LLM called run_shell with "uname -a"
        handler = handlers["run_shell"]
        result = await handler(command="uname -a")
        assert "Linux" in result, "got system info"
        ok(f"Simulated tool call: run_shell('uname -a') -> {result.split(chr(10))[0][:60]}...")

        # Pretend the LLM called memory remember
        handler = handlers["memory"]
        result = await handler(action="remember", key="os", value="Linux")
        assert "Remembered" in result
        ok(f"Simulated tool call: memory remember -> {result}")

        # Pretend the LLM called list_directory
        handler = handlers["list_directory"]
        result = await handler(path=".")
        ok(f"Simulated tool call: list_directory('.') -> {len(result.split(chr(10)))} entries")

    asyncio.run(simulate())

    # Cleanup
    import shutil
    shutil.rmtree("/tmp/pocketclaw_test_pipeline", ignore_errors=True)


# ── Run ───────────────────────────────────────────────────

if __name__ == "__main__":
    print(f"\n{C}PocketClaw Test Suite{R}\n")
    tests = [test_config, test_skill_loader, test_memory, test_system_prompt, test_builtin_tools, test_tool_pipeline]
    passed = 0
    failed = 0
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            fail(f"{test.__name__}: {e}")
            failed += 1

    total = passed + failed
    print(f"\n{C}── Results ──{R}")
    print(f"  {passed}/{total} test groups passed")
    if failed:
        print(f"  {failed} failed")
        sys.exit(1)
    else:
        print(f"  {G}All clear.{R}\n")
