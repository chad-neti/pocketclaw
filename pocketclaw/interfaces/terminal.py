from datetime import datetime


class TerminalInterface:
    def __init__(self, gateway, config):
        self.gateway = gateway
        self.config = config
        self.conv_id = f"terminal-{datetime.now():%Y%m%d-%H%M%S}"
        self.color = config.get("display.color", True)
        self.show_tools = config.get("display.show_tool_calls", True)

    def _c(self, code, text):
        return f"\033[{code}m{text}\033[0m" if self.color else text

    async def run(self):
        print(self._c("1;36", "PocketClaw") + " ready. Type /help for commands.\n")
        while True:
            try:
                user_input = input(self._c("1;32", "> "))
            except (EOFError, KeyboardInterrupt):
                print("\nBye!")
                break

            if not user_input.strip():
                continue

            if user_input.startswith("/"):
                if not self._slash(user_input):
                    break
                continue

            try:
                async for chunk in self.gateway.handle_message_stream(user_input, self.conv_id):
                    t = chunk["type"]
                    if t == "text":
                        print(chunk["text"], end="", flush=True)
                    elif t == "tool_call" and self.show_tools:
                        name = chunk["name"]
                        args = " ".join(f"{k}={v!r}" for k, v in chunk["arguments"].items())
                        print(self._c("2", f"\n  > {name} {args}"))
                    elif t == "tool_result" and self.show_tools:
                        result = chunk["result"]
                        if len(result) > 500:
                            result = result[:500] + "..."
                        for line in result.split("\n"):
                            print(self._c("2", f"    {line}"))
                print()
            except Exception as e:
                print(self._c("31", f"\nError: {e}\n"))

    def _slash(self, cmd):
        """Handle slash command. Returns False to exit."""
        cmd = cmd.strip().lower()
        if cmd == "/help":
            print(
                "/help     Show this help\n"
                "/clear    Clear conversation\n"
                "/new      Start new conversation\n"
                "/skills   List active skills\n"
                "/memory   Show stored facts\n"
                "/quit     Exit"
            )
        elif cmd in ("/clear", "/new"):
            self.conv_id = f"terminal-{datetime.now():%Y%m%d-%H%M%S}"
            print("New conversation started.\n")
        elif cmd == "/skills":
            print(self.gateway.skills.get_summary() or "No skills loaded.")
        elif cmd == "/memory":
            print(self.gateway.memory.get_context() or "No stored facts.")
        elif cmd in ("/quit", "/exit", "/q"):
            print("Bye!")
            return False
        else:
            print(f"Unknown command: {cmd}")
        return True
