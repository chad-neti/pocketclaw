import json
from pathlib import Path
from datetime import datetime


class MemoryStore:
    def __init__(self, config):
        self.base = Path(config.get("memory.path", "~/.pocketclaw/memory")).expanduser()
        self.base.mkdir(parents=True, exist_ok=True)
        (self.base / "conversations").mkdir(exist_ok=True)
        self.max_messages = config.get("memory.max_conversation_messages", 50)

    def get_conversation(self, conv_id):
        path = self.base / "conversations" / f"{conv_id}.json"
        if path.exists():
            msgs = json.loads(path.read_text(encoding='utf-8'))
            return msgs[-self.max_messages:]
        return []

    def save_conversation(self, conv_id, messages):
        path = self.base / "conversations" / f"{conv_id}.json"
        path.write_text(encoding='utf-8', data=json.dumps(messages, indent=2, default=str))

    def get_identity(self):
        path = self.base / "identity.md"
        return path.read_text(encoding='utf-8') if path.exists() else ""

    def get_facts(self):
        path = self.base / "facts.json"
        return json.loads(path.read_text(encoding='utf-8')) if path.exists() else {}

    def save_facts(self, facts):
        (self.base / "facts.json").write_text(encoding='utf-8', data=json.dumps(facts, indent=2))

    def get_context(self):
        parts = []
        identity = self.get_identity()
        if identity:
            parts.append(identity)
        facts = self.get_facts()
        if facts:
            items = [f"- {k}: {v}" for k, v in facts.items() if k != "facts_learned"]
            if items:
                parts.append("## Known Facts\n" + "\n".join(items))
        return "\n\n".join(parts)

    async def handle_tool(self, action, key, value=None):
        facts = self.get_facts()
        if action == "remember":
            facts[key] = value
            facts.setdefault("facts_learned", []).append({
                "fact": f"{key}: {value}",
                "date": datetime.now().isoformat()[:10],
            })
            self.save_facts(facts)
            return f"Remembered: {key} = {value}"
        elif action == "recall":
            matches = {
                k: v for k, v in facts.items()
                if key.lower() in k.lower() or key.lower() in str(v).lower()
            }
            return json.dumps(matches, indent=2) if matches else f"No facts matching '{key}'"
        elif action == "forget":
            if key in facts:
                del facts[key]
                self.save_facts(facts)
                return f"Forgot: {key}"
            return f"No fact '{key}' found"
        return f"Unknown action: {action}"
