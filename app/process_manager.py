import re
import sys

import psutil
from PySide6.QtCore import QObject, QProcess, QTimer, Signal

from app.models import Service

ANSI_RE = re.compile(r"\x1b\[[0-9;?]*[A-Za-z]")
MAX_LOG_CHUNKS = 5000


class ProcessManager(QObject):
    """Starts/stops services as child processes and collects their output."""

    status_changed = Signal(str, str)  # service_id, "running" | "stopped" | "error"
    output = Signal(str, str)          # service_id, text

    def __init__(self, parent=None):
        super().__init__(parent)
        self._procs: dict[str, QProcess] = {}
        self._logs: dict[str, list[str]] = {}
        self._stopping: set[str] = set()

    # ---- queries -------------------------------------------------------
    def is_running(self, service_id: str) -> bool:
        proc = self._procs.get(service_id)
        return proc is not None and proc.state() != QProcess.ProcessState.NotRunning

    def get_log(self, service_id: str) -> str:
        return "".join(self._logs.get(service_id, []))

    def clear_log(self, service_id: str) -> None:
        self._logs[service_id] = []

    # ---- actions -------------------------------------------------------
    def start(self, service: Service) -> None:
        if self.is_running(service.id):
            return

        sid = service.id
        proc = QProcess(self)
        proc.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        if service.working_dir:
            proc.setWorkingDirectory(service.working_dir)

        proc.readyReadStandardOutput.connect(lambda p=proc: self._read(sid, p))
        proc.started.connect(lambda: self.status_changed.emit(sid, "running"))
        proc.errorOccurred.connect(lambda err: self._on_error(sid, err))
        proc.finished.connect(lambda code, status: self._on_finished(sid, code))

        self._procs[sid] = proc
        self._stopping.discard(sid)
        self._append(sid, f"$ {service.command}\n")

        if sys.platform == "win32":
            proc.start("cmd.exe", ["/c", service.command])
        else:
            proc.start("/bin/sh", ["-c", service.command])

    def stop(self, service_id: str) -> None:
        if not self.is_running(service_id):
            return
        self._stopping.add(service_id)
        self._append(service_id, "\n[stopping...]\n")
        self._kill_tree(self._procs[service_id], force=False)
        QTimer.singleShot(4000, lambda: self._force_stop(service_id))

    def stop_all_now(self) -> None:
        """Hard-stop everything (used when the app closes)."""
        for sid, proc in self._procs.items():
            if self.is_running(sid):
                self._kill_tree(proc, force=True)
                proc.waitForFinished(1500)

    # ---- internals -----------------------------------------------------
    def _force_stop(self, service_id: str) -> None:
        if self.is_running(service_id):
            self._kill_tree(self._procs[service_id], force=True)

    @staticmethod
    def _kill_tree(proc: QProcess, force: bool) -> None:
        """Kill the shell *and* everything it spawned (node, python, ...)."""
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

    def _read(self, service_id: str, proc: QProcess) -> None:
        raw = bytes(proc.readAllStandardOutput()).decode("utf-8", errors="replace")
        self._append(service_id, ANSI_RE.sub("", raw))

    def _append(self, service_id: str, text: str) -> None:
        chunks = self._logs.setdefault(service_id, [])
        chunks.append(text)
        if len(chunks) > MAX_LOG_CHUNKS:
            del chunks[: len(chunks) - MAX_LOG_CHUNKS]
        self.output.emit(service_id, text)

    def _on_error(self, service_id: str, error) -> None:
        if error == QProcess.ProcessError.FailedToStart:
            self._append(service_id, "[error] Failed to start. Check the command / PATH.\n")
            self.status_changed.emit(service_id, "error")

    def _on_finished(self, service_id: str, exit_code: int) -> None:
        was_stopped_by_user = service_id in self._stopping
        self._stopping.discard(service_id)
        self._append(service_id, f"\n[process exited with code {exit_code}]\n")
        ok = was_stopped_by_user or exit_code == 0
        self.status_changed.emit(service_id, "stopped" if ok else "error")
