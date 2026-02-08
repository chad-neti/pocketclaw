import json
import httpx
from dataclasses import dataclass, field

PROVIDERS = {
    "anthropic": ("https://api.anthropic.com", "anthropic"),
    "openai": ("https://api.openai.com/v1", "openai"),
    "deepseek": ("https://api.deepseek.com/v1", "openai"),
    "google": ("https://generativelanguage.googleapis.com/v1beta", "google"),
    "groq": ("https://api.groq.com/openai/v1", "openai"),
    "ollama": ("http://localhost:11434/v1", "openai"),
}


@dataclass
class ToolCall:
    id: str
    name: str
    arguments: dict


@dataclass
class LLMResponse:
    text: str | None = None
    tool_calls: list[ToolCall] = field(default_factory=list)
    usage: dict = field(default_factory=dict)


class LLMConnector:
    def __init__(self, config: dict):
        self.provider = config.get("provider", "anthropic")
        self.api_key = config.get("api_key", "")
        self.model = config.get("model", "claude-sonnet-4-20250514")
        self.max_tokens = config.get("max_tokens", 4096)
        self.temperature = config.get("temperature", 0.3)
        base, self.fmt = PROVIDERS.get(self.provider, PROVIDERS["openai"])
        self.base_url = config.get("base_url", base)
        self.client = httpx.AsyncClient(timeout=120)

    async def chat(self, system, messages, tools=None) -> LLMResponse:
        if self.fmt == "anthropic":
            return await self._anthropic(system, messages, tools)
        return await self._openai(system, messages, tools)

    async def chat_stream(self, system, messages, tools=None):
        if self.fmt == "anthropic":
            async for c in self._stream_anthropic(system, messages, tools):
                yield c
        else:
            async for c in self._stream_openai(system, messages, tools):
                yield c

    # -- Anthropic ---------------------------------------------

    def _anth_headers(self):
        return {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }

    def _anth_body(self, system, messages, tools, stream=False):
        body = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "system": system,
            "messages": messages,
        }
        if tools:
            body["tools"] = [self._tool_anth(t) for t in tools]
        if stream:
            body["stream"] = True
        return body

    async def _anthropic(self, system, messages, tools):
        r = await self.client.post(
            f"{self.base_url}/v1/messages",
            headers=self._anth_headers(),
            json=self._anth_body(system, messages, tools),
        )
        r.raise_for_status()
        return self._parse_anth(r.json())

    async def _stream_anthropic(self, system, messages, tools):
        async with self.client.stream(
            "POST",
            f"{self.base_url}/v1/messages",
            headers=self._anth_headers(),
            json=self._anth_body(system, messages, tools, stream=True),
        ) as r:
            text, tcs, cur, cur_json = "", [], None, ""
            async for line in r.aiter_lines():
                if not line.startswith("data: "):
                    continue
                d = json.loads(line[6:])
                t = d.get("type")
                if t == "content_block_start":
                    b = d.get("content_block", {})
                    if b.get("type") == "tool_use":
                        cur = {"id": b["id"], "name": b["name"]}
                        cur_json = ""
                elif t == "content_block_delta":
                    delta = d.get("delta", {})
                    if delta.get("type") == "text_delta":
                        c = delta["text"]
                        text += c
                        yield {"type": "text", "text": c}
                    elif delta.get("type") == "input_json_delta":
                        cur_json += delta.get("partial_json", "")
                elif t == "content_block_stop" and cur:
                    args = json.loads(cur_json) if cur_json else {}
                    tcs.append(ToolCall(cur["id"], cur["name"], args))
                    cur = None
            if tcs:
                yield {"type": "tool_calls", "tool_calls": tcs}
            yield {"type": "done", "text": text}

    def _parse_anth(self, data) -> LLMResponse:
        text, tcs = None, []
        for b in data.get("content", []):
            if b["type"] == "text":
                text = b["text"]
            elif b["type"] == "tool_use":
                tcs.append(ToolCall(b["id"], b["name"], b.get("input", {})))
        return LLMResponse(text, tcs, data.get("usage", {}))

    def _tool_anth(self, t):
        props, req = {}, []
        for k, v in t.get("parameters", {}).items():
            prop = {"type": v.get("type", "string"), "description": v.get("description", "")}
            if prop["type"] == "array":
                prop["items"] = {"type": "string"}
            props[k] = prop
            if v.get("required"):
                req.append(k)
        return {
            "name": t["name"],
            "description": t["description"],
            "input_schema": {"type": "object", "properties": props, "required": req},
        }

    # -- OpenAI-compatible -------------------------------------

    def _oai_headers(self):
        return {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}

    def _to_oai_msgs(self, system, messages):
        """Translate canonical (Anthropic-like) messages to OpenAI format."""
        out = [{"role": "system", "content": system}]
        for msg in messages:
            if msg["role"] == "assistant" and isinstance(msg.get("content"), list):
                text_parts, tool_calls = [], []
                for block in msg["content"]:
                    if block.get("type") == "text":
                        text_parts.append(block["text"])
                    elif block.get("type") == "tool_use":
                        tool_calls.append({
                            "id": block["id"],
                            "type": "function",
                            "function": {
                                "name": block["name"],
                                "arguments": json.dumps(block.get("input", {})),
                            },
                        })
                m = {"role": "assistant"}
                if text_parts:
                    m["content"] = "\n".join(text_parts)
                if tool_calls:
                    m["tool_calls"] = tool_calls
                out.append(m)
            elif msg["role"] == "user" and isinstance(msg.get("content"), list):
                for block in msg["content"]:
                    if block.get("type") == "tool_result":
                        out.append({
                            "role": "tool",
                            "tool_call_id": block["tool_use_id"],
                            "content": str(block.get("content", "")),
                        })
            else:
                out.append(msg)
        return out

    async def _openai(self, system, messages, tools):
        body = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "messages": self._to_oai_msgs(system, messages),
        }
        if tools:
            body["tools"] = [self._tool_oai(t) for t in tools]
        r = await self.client.post(
            f"{self.base_url}/chat/completions",
            headers=self._oai_headers(),
            json=body,
        )
        r.raise_for_status()
        return self._parse_oai(r.json())

    async def _stream_openai(self, system, messages, tools):
        body = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "messages": self._to_oai_msgs(system, messages),
            "stream": True,
        }
        if tools:
            body["tools"] = [self._tool_oai(t) for t in tools]
        async with self.client.stream(
            "POST",
            f"{self.base_url}/chat/completions",
            headers=self._oai_headers(),
            json=body,
        ) as r:
            text, tc_data = "", {}
            async for line in r.aiter_lines():
                if not line.startswith("data: ") or line.strip() == "data: [DONE]":
                    continue
                d = json.loads(line[6:])
                delta = d.get("choices", [{}])[0].get("delta", {})
                if delta.get("content"):
                    text += delta["content"]
                    yield {"type": "text", "text": delta["content"]}
                for tc in delta.get("tool_calls", []):
                    i = tc["index"]
                    tc_data.setdefault(i, {"id": "", "name": "", "args": ""})
                    if "id" in tc:
                        tc_data[i]["id"] = tc["id"]
                    fn = tc.get("function", {})
                    if "name" in fn:
                        tc_data[i]["name"] = fn["name"]
                    if "arguments" in fn:
                        tc_data[i]["args"] += fn["arguments"]
            if tc_data:
                tcs = []
                for i in sorted(tc_data):
                    d = tc_data[i]
                    args = json.loads(d["args"]) if d["args"] else {}
                    tcs.append(ToolCall(d["id"], d["name"], args))
                yield {"type": "tool_calls", "tool_calls": tcs}
            yield {"type": "done", "text": text}

    def _parse_oai(self, data) -> LLMResponse:
        msg = data["choices"][0]["message"]
        tcs = []
        for tc in msg.get("tool_calls", []):
            args = json.loads(tc["function"]["arguments"]) if tc["function"].get("arguments") else {}
            tcs.append(ToolCall(tc["id"], tc["function"]["name"], args))
        return LLMResponse(msg.get("content"), tcs, data.get("usage", {}))

    def _tool_oai(self, t):
        props, req = {}, []
        for k, v in t.get("parameters", {}).items():
            prop = {"type": v.get("type", "string"), "description": v.get("description", "")}
            if prop["type"] == "array":
                prop["items"] = {"type": "string"}
            if v.get("required"):
                req.append(k)
            props[k] = prop
        return {
            "type": "function",
            "function": {
                "name": t["name"],
                "description": t["description"],
                "parameters": {"type": "object", "properties": props, "required": req},
            },
        }

    async def close(self):
        await self.client.aclose()
