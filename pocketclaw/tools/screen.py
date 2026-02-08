import asyncio
import json
import re


async def screen_read():
    proc = await asyncio.create_subprocess_shell(
        "uiautomator dump /dev/tty 2>/dev/null",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, _ = await proc.communicate()
    return _parse_ui_xml(stdout.decode(errors="replace"))


async def screen_tap_element(text, element_type=None, index=0):
    raw = await screen_read()
    elements = json.loads(raw).get("elements", [])
    matches = []
    for el in elements:
        haystack = (el.get("text", "") + " " + el.get("description", "")).lower()
        if text.lower() in haystack:
            if element_type is None or el.get("type", "").lower().endswith(element_type.lower()):
                matches.append(el)
    if not matches:
        return f"Element '{text}' not found on screen"
    if index >= len(matches):
        return f"Only {len(matches)} matches, index {index} out of range"
    b = matches[index]["bounds"]
    x, y = (b[0] + b[2]) // 2, (b[1] + b[3]) // 2
    await _tap(x, y)
    return f"Tapped '{text}' at ({x}, {y})"


async def screen_type_text(text, clear_first=False):
    if clear_first:
        await asyncio.create_subprocess_shell("input keyevent KEYCODE_CTRL_LEFT+KEYCODE_A")
        await asyncio.create_subprocess_shell("input keyevent KEYCODE_DEL")
    escaped = text.replace(" ", "%s").replace("&", "\\&")
    await asyncio.create_subprocess_shell(f'input text "{escaped}"')
    return f"Typed: {text}"


async def screen_scroll(direction="down", amount=500):
    cx, cy = 540, 960
    moves = {
        "up": (cx, cy + amount, cx, cy - amount),
        "down": (cx, cy - amount, cx, cy + amount),
        "left": (cx + amount, cy, cx - amount, cy),
        "right": (cx - amount, cy, cx + amount, cy),
    }
    x1, y1, x2, y2 = moves.get(direction, moves["down"])
    await asyncio.create_subprocess_shell(f"input swipe {x1} {y1} {x2} {y2} 300")
    return f"Scrolled {direction}"


async def screenshot(scale=0.5):
    path = "/tmp/pocketclaw_screen.png"
    await asyncio.create_subprocess_shell(f"screencap -p {path}")
    if scale < 1.0:
        try:
            from PIL import Image
            img = Image.open(path)
            new_size = (int(img.width * scale), int(img.height * scale))
            img.resize(new_size).save(path)
        except ImportError:
            pass
    return path


async def screen_tap_coordinates(x, y):
    await _tap(x, y)
    return f"Tapped ({x}, {y})"


async def _tap(x, y):
    await asyncio.create_subprocess_shell(f"input tap {x} {y}")


def _parse_ui_xml(xml):
    elements = []
    pattern = re.compile(
        r'<node[^>]*?'
        r'class="([^"]*)"[^>]*?'
        r'text="([^"]*)"[^>]*?'
        r'content-desc="([^"]*)"[^>]*?'
        r'clickable="([^"]*)"[^>]*?'
        r'bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"',
        re.DOTALL,
    )
    for m in pattern.finditer(xml):
        cls, text, desc, clickable, x1, y1, x2, y2 = m.groups()
        if text or desc:
            elements.append({
                "type": cls.split(".")[-1],
                "text": text,
                "description": desc,
                "clickable": clickable == "true",
                "bounds": [int(x1), int(y1), int(x2), int(y2)],
            })
    return json.dumps({"elements": elements}, indent=2)


def get_screen_tools(config):
    return {
        "screen_read": screen_read,
        "screen_tap_element": screen_tap_element,
        "screen_type_text": screen_type_text,
        "screen_scroll": screen_scroll,
        "screenshot": screenshot,
        "screen_tap_coordinates": screen_tap_coordinates,
    }
