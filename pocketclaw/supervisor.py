import os
import signal
import subprocess
from pathlib import Path

PID_FILE = Path.home() / ".pocketclaw" / "pocketclaw.pid"


class Supervisor:
    def start(self):
        subprocess.run(["termux-wake-lock"], capture_output=True)
        PID_FILE.parent.mkdir(parents=True, exist_ok=True)
        PID_FILE.write_text(str(os.getpid()))

    def stop(self):
        subprocess.run(["termux-wake-unlock"], capture_output=True)
        if PID_FILE.exists():
            PID_FILE.unlink()

    @staticmethod
    def is_running():
        if not PID_FILE.exists():
            return False
        pid = int(PID_FILE.read_text().strip())
        try:
            os.kill(pid, 0)
            return True
        except OSError:
            PID_FILE.unlink()
            return False

    @staticmethod
    def get_pid():
        if PID_FILE.exists():
            return int(PID_FILE.read_text().strip())
        return None

    @staticmethod
    def kill():
        pid = Supervisor.get_pid()
        if pid:
            os.kill(pid, signal.SIGTERM)
            if PID_FILE.exists():
                PID_FILE.unlink()
