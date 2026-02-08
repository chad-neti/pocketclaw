import asyncio
import json
import shutil


class AndroidBridge:
    def __init__(self):
        self.has_termux_api = shutil.which("termux-battery-status") is not None
        self.has_root = self._check_root()

    def _check_root(self):
        try:
            import subprocess
            r = subprocess.run(["su", "-c", "id"], capture_output=True, timeout=2)
            return r.returncode == 0
        except Exception:
            return False

    async def termux_api(self, command, args=None):
        cmd = [command] + (args or [])
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        output = stdout.decode(errors="replace").strip()
        if proc.returncode != 0:
            err = stderr.decode(errors="replace").strip()
            return f"Error: {err or 'command failed'}"
        try:
            return json.dumps(json.loads(output), indent=2)
        except json.JSONDecodeError:
            return output

    def get_capabilities(self):
        return {
            "termux_api": self.has_termux_api,
            "root": self.has_root,
        }


def get_android_tools(config):
    bridge = AndroidBridge()

    async def termux_api_handler(command, args=None):
        return await bridge.termux_api(command, args)

    return {"termux_api": termux_api_handler}
