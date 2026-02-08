import yaml
import importlib.util
from pathlib import Path


class Skill:
    def __init__(self, name, data, body, path):
        self.name = name
        self.data = data
        self.body = body
        self.path = path
        self.tools = data.get("tools", [])
        self.handler = None
        handler_path = data.get("handler")
        if handler_path:
            self._load_handler(self.path.parent / handler_path)

    def _load_handler(self, hp):
        if not hp.exists():
            return
        spec = importlib.util.spec_from_file_location(self.name, hp)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        for obj in vars(mod).values():
            if isinstance(obj, type) and obj.__module__ == mod.__name__:
                self.handler = obj()
                break


class SkillLoader:
    def __init__(self, config):
        self.skills = {}
        disabled = config.get("skills.disabled", [])
        for p in config.get("skills.paths", []):
            self._load_dir(Path(p).expanduser(), disabled)

    def _load_dir(self, path, disabled):
        if not path.is_dir():
            return
        for f in path.glob("*.md"):
            skill = self._parse(f)
            if skill and skill.name not in disabled:
                self.skills[skill.name] = skill

    def _parse(self, path):
        text = path.read_text()
        if not text.startswith("---"):
            return None
        try:
            end = text.index("---", 3)
            front = yaml.safe_load(text[3:end])
            body = text[end + 3:].strip()
            return Skill(front.get("name", path.stem), front, body, path)
        except (ValueError, yaml.YAMLError):
            return None

    def get_tool_definitions(self):
        defs = []
        for skill in self.skills.values():
            for tool in skill.tools:
                params = {}
                for k, v in tool.get("parameters", {}).items():
                    if isinstance(v, dict):
                        params[k] = {
                            "type": v.get("type", "string"),
                            "description": v.get("description", ""),
                            "required": v.get("required", False),
                        }
                defs.append({
                    "name": tool["name"],
                    "description": tool.get("description", ""),
                    "parameters": params,
                })
        return defs

    def get_handlers(self):
        handlers = {}
        for skill in self.skills.values():
            if skill.handler:
                for tool in skill.tools:
                    fn = getattr(skill.handler, tool["name"], None)
                    if fn:
                        handlers[tool["name"]] = fn
        return handlers

    def get_summary(self):
        lines = []
        for s in self.skills.values():
            tools = ", ".join(t["name"] for t in s.tools)
            desc = s.data.get("description", "")
            lines.append(f"- **{s.name}**: {desc} [{tools}]")
        return "\n".join(lines)
