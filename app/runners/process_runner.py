"""Runs foreground commands (npm run dev, uvicorn ..., python app.py)."""
import sys
from pathlib import Path

import psutil
from PySide6.QtCore import QObject, QProcess, QTimer, Signal

from app.environment import build_environment
from app.utils import strip_ansi

NOT_FOUND_CODES = (127, 9009)


class ProcessRunner(QObject):
    status_changed = Signal(str, str)  # service_id, state
    output = Signal(str, str)          # service_id, text

    def __init__(self, parent=None):
        super().__init__(parent)
        self._procs: dict = {}
        self._state: dict = {}
        self._stopping: set = set()

    def status(self, sid: str) -> str:
        return self._state.get(sid, "stopped")

    def _set_state(self, sid: str, state: str) -> None:
        if self._state.get(sid, "stopped") != state:
            self._state[sid] = state
            self.status_changed.emit(sid, state)

    # ---- start / stop --------------------------------------------------
    def start(self, s) -> None:
        sid = s.id
        if self.status(sid) in ("starting", "running", "stopping"):
            return

        cwd = str(Path(s.working_dir).expanduser()) if s.working_dir else ""
        self.output.emit(sid, f"\n$ {s.command}\n")
        if cwd and not Path(cwd).is_dir():
            self.output.emit(sid, f"[error] Working directory not found: {cwd}\n")
            self._set_state(sid, "error")
            return

        env, venv = build_environment(s)
        if cwd:
            self.output.emit(sid, f"[cwd]  {cwd}\n")
        if venv:
            self.output.emit(sid, f"[venv] {venv}\n")
        elif s.venv:
            self.output.emit(sid, f"[warn] venv not found at {s.venv} (no bin/python inside)\n")

        proc = QProcess(self)
        proc.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        proc.setProcessEnvironment(env)
        if cwd:
            proc.setWorkingDirectory(cwd)

        proc.readyReadStandardOutput.connect(lambda p=proc: self._read(sid, p))
        proc.started.connect(lambda: self._set_state(sid, "running"))
        proc.errorOccurred.connect(lambda err: self._on_error(sid, err))
        proc.finished.connect(lambda code, st, p=proc: self._on_finished(sid, code, p))

        self._procs[sid] = proc
        self._stopping.discard(sid)
        self._set_state(sid, "starting")

        if sys.platform == "win32":
            proc.start("cmd.exe", ["/c", s.command])
        else:
            proc.start("/bin/sh", ["-c", s.command])

    def stop(self, s) -> None:
        sid = s.id
        proc = self._procs.get(sid)
        if proc is None or self.status(sid) not in ("starting", "running"):
            return
        self._stopping.add(sid)
        self._set_state(sid, "stopping")
        self.output.emit(sid, "\n[stopping...]\n")
        self._kill_tree(proc, force=False)
        QTimer.singleShot(4000, lambda: self._force(sid))

    def stop_all_now(self) -> None:
        for proc in list(self._procs.values()):
            if proc.state() != QProcess.ProcessState.NotRunning:
                self._kill_tree(proc, force=True)
                proc.waitForFinished(1500)

    # ---- internals -----------------------------------------------------
    def _force(self, sid: str) -> None:
        proc = self._procs.get(sid)
        if proc is not None and proc.state() != QProcess.ProcessState.NotRunning:
            self._kill_tree(proc, force=True)

    @staticmethod
    def _kill_tree(proc: QProcess, force: bool) -> None:
        """Kill the shell AND everything it spawned (node, uvicorn workers...)."""
        pid = proc.processId()
        if not pid:
            return
        try:
            parent = psutil.Process(pid)
            targets = parent.children(recursive=True) + [parent]
        except psutil.NoSuchProcess:
            return
        for p in targets:
            try:
                p.kill() if force else p.terminate()
            except psutil.NoSuchProcess:
                pass

    def _read(self, sid: str, proc: QProcess) -> None:
        raw = bytes(proc.readAllStandardOutput()).decode("utf-8", errors="replace")
        self.output.emit(sid, strip_ansi(raw))

    def _on_error(self, sid: str, error) -> None:
        if error == QProcess.ProcessError.FailedToStart:
            self.output.emit(sid, "[error] Could not start the shell.\n")
            self._procs.pop(sid, None)
            self._set_state(sid, "error")

    def _on_finished(self, sid: str, code: int, proc: QProcess) -> None:
        by_user = sid in self._stopping
        self._stopping.discard(sid)
        if self._procs.get(sid) is proc:
            self._procs.pop(sid, None)
        proc.deleteLater()

        self.output.emit(sid, f"\n[process exited with code {code}]\n")
        if code in NOT_FOUND_CODES and not by_user:
            self.output.emit(
                sid,
                "[hint] Command not found. If it lives in a project venv, keep a .venv/venv folder "
                "inside the working directory or set the venv path via Edit.\n",
            )
        self._set_state(sid, "stopped" if (by_user or code == 0) else "error")
