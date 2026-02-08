import asyncio
import httpx
from pathlib import Path


async def run_shell(command, timeout=30, working_dir=None):
    proc = await asyncio.create_subprocess_shell(
        command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=working_dir,
    )
    try:
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
    except asyncio.TimeoutError:
        proc.kill()
        return "Error: command timed out"
    result = ""
    if stdout:
        result += stdout.decode(errors="replace")
    if stderr:
        result += f"\nSTDERR:\n{stderr.decode(errors='replace')}"
    result += f"\n[exit code: {proc.returncode}]"
    return result.strip()


async def run_python(code, timeout=30):
    return await run_shell(f"python3 -c {repr(code)}", timeout=timeout)


async def read_file(path, max_lines=None):
    try:
        p = Path(path).expanduser()
        text = p.read_text()
        if max_lines:
            text = "\n".join(text.split("\n")[: int(max_lines)])
        return text
    except Exception as e:
        return f"Error: {e}"


async def write_file(path, content):
    try:
        p = Path(path).expanduser()
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content)
        return f"Written {len(content)} bytes to {path}"
    except Exception as e:
        return f"Error: {e}"


async def edit_file(path, old_str, new_str):
    try:
        p = Path(path).expanduser()
        text = p.read_text()
        count = text.count(old_str)
        if count == 0:
            return "Error: old_str not found in file"
        if count > 1:
            return f"Error: old_str found {count} times (must be unique)"
        p.write_text(text.replace(old_str, new_str, 1))
        return "File edited successfully"
    except Exception as e:
        return f"Error: {e}"


async def list_directory(path=".", recursive=False, max_depth=2):
    try:
        p = Path(path).expanduser()
        if not p.is_dir():
            return f"Error: {path} is not a directory"
        entries = []
        if recursive:
            for item in sorted(p.rglob("*")):
                rel = item.relative_to(p)
                if len(rel.parts) <= max_depth:
                    prefix = "  " * (len(rel.parts) - 1)
                    marker = "/" if item.is_dir() else ""
                    entries.append(f"{prefix}{item.name}{marker}")
        else:
            for item in sorted(p.iterdir()):
                marker = "/" if item.is_dir() else ""
                entries.append(f"{item.name}{marker}")
        return "\n".join(entries) or "(empty directory)"
    except Exception as e:
        return f"Error: {e}"


async def http_request(method="GET", url="", headers=None, body=None, timeout=15):
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            r = await client.request(method, url, headers=headers, content=body)
            return f"HTTP {r.status_code}\n{r.text[:5000]}"
    except Exception as e:
        return f"Error: {e}"


def get_builtin_tools(config):
    return {
        "run_shell": run_shell,
        "run_python": run_python,
        "read_file": read_file,
        "write_file": write_file,
        "edit_file": edit_file,
        "list_directory": list_directory,
        "http_request": http_request,
    }
