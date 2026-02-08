import logging
from .llm import LLMConnector
from .memory import MemoryStore
from .skill_loader import SkillLoader
from .system_prompt import build_system_prompt

log = logging.getLogger(__name__)


class Gateway:
    def __init__(self, config):
        self.config = config
        self.llm = LLMConnector(config.get("llm"))
        self.memory = MemoryStore(config)
        self.skills = SkillLoader(config)
        self.tools = {}
        self._register_tools()

    def _register_tools(self):
        from .tools.builtin import get_builtin_tools
        from .tools.screen import get_screen_tools
        from .android import get_android_tools

        for src in [get_builtin_tools, get_screen_tools, get_android_tools]:
            self.tools.update(src(self.config))

        self.tools["memory"] = self.memory.handle_tool
        self.tools["confirm"] = self._handle_confirm

        for name, handler in self.skills.get_handlers().items():
            self.tools[name] = handler

    def get_tool_definitions(self):
        defs = self.skills.get_tool_definitions()
        defs.append({
            "name": "memory",
            "description": "Store or retrieve persistent info. 'remember' to save, 'recall' to search, 'forget' to remove.",
            "parameters": {
                "action": {"type": "string", "description": "'remember', 'recall', or 'forget'", "required": True},
                "key": {"type": "string", "description": "What to remember/recall/forget", "required": True},
                "value": {"type": "string", "description": "Value to remember", "required": False},
            },
        })
        defs.append({
            "name": "confirm",
            "description": "Ask user to confirm before destructive or sensitive actions.",
            "parameters": {
                "action": {"type": "string", "description": "What's about to happen", "required": True},
                "risk_level": {"type": "string", "description": "'low', 'medium', or 'high'", "required": False},
            },
        })
        return defs

    async def handle_message(self, user_input, conv_id="default"):
        messages = self.memory.get_conversation(conv_id)
        system = build_system_prompt(self.config, self.skills, self.memory)
        tools = self.get_tool_definitions()
        messages.append({"role": "user", "content": user_input})
        max_iter = self.config.get("advanced.max_tool_iterations", 50)

        for _ in range(max_iter):
            response = await self.llm.chat(system, messages, tools)

            if not response.tool_calls:
                if response.text:
                    messages.append({"role": "assistant", "content": response.text})
                self.memory.save_conversation(conv_id, messages)
                return response.text or ""

            # Build assistant message with tool use blocks
            content = []
            if response.text:
                content.append({"type": "text", "text": response.text})
            for tc in response.tool_calls:
                content.append({
                    "type": "tool_use", "id": tc.id,
                    "name": tc.name, "input": tc.arguments,
                })
            messages.append({"role": "assistant", "content": content})

            # Execute tools and collect results
            tool_results = []
            for tc in response.tool_calls:
                result = await self._exec_tool(tc)
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tc.id,
                    "content": result,
                })
            messages.append({"role": "user", "content": tool_results})

        self.memory.save_conversation(conv_id, messages)
        return "[max tool iterations reached]"

    async def handle_message_stream(self, user_input, conv_id="default"):
        messages = self.memory.get_conversation(conv_id)
        system = build_system_prompt(self.config, self.skills, self.memory)
        tools = self.get_tool_definitions()
        messages.append({"role": "user", "content": user_input})
        max_iter = self.config.get("advanced.max_tool_iterations", 50)

        for _ in range(max_iter):
            full_text = ""
            tool_calls = []

            async for chunk in self.llm.chat_stream(system, messages, tools):
                if chunk["type"] == "text":
                    yield chunk
                    full_text += chunk["text"]
                elif chunk["type"] == "tool_calls":
                    tool_calls = chunk["tool_calls"]

            if not tool_calls:
                if full_text:
                    messages.append({"role": "assistant", "content": full_text})
                self.memory.save_conversation(conv_id, messages)
                return

            content = []
            if full_text:
                content.append({"type": "text", "text": full_text})
            for tc in tool_calls:
                content.append({
                    "type": "tool_use", "id": tc.id,
                    "name": tc.name, "input": tc.arguments,
                })
            messages.append({"role": "assistant", "content": content})

            tool_results = []
            for tc in tool_calls:
                yield {"type": "tool_call", "name": tc.name, "arguments": tc.arguments}
                result = await self._exec_tool(tc)
                yield {"type": "tool_result", "name": tc.name, "result": result}
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tc.id,
                    "content": result,
                })
            messages.append({"role": "user", "content": tool_results})

        self.memory.save_conversation(conv_id, messages)

    async def _exec_tool(self, tool_call):
        handler = self.tools.get(tool_call.name)
        if not handler:
            return f"Error: unknown tool '{tool_call.name}'"
        try:
            return await handler(**tool_call.arguments)
        except Exception as e:
            log.error(f"Tool {tool_call.name} failed: {e}")
            return f"Error: {e}"

    async def _handle_confirm(self, action, risk_level="medium"):
        return f"Confirmation needed: {action} (risk: {risk_level})"

    async def close(self):
        await self.llm.close()
