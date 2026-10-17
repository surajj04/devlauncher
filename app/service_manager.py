from PySide6.QtCore import QObject, QTimer, Signal

from app import storage
from app.constants import ACTIVE_STATES, MANAGED_KINDS
from app.runners.managed_runner import ManagedRunner
from app.runners.process_runner import ProcessRunner

MAX_LOG_CHUNKS = 5000
FLUSH_MS = 2000
PREVIOUS_SESSION_MARK = "\n──────── previous session ────────\n"


class ServiceManager(QObject):
    """Single entry point for the UI. Picks the right runner and keeps per-service logs
    (in memory + saved to SQLite so they survive a restart)."""

    status_changed = Signal(str, str)
    output = Signal(str, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._services: dict = {}
        self._logs: dict = storage.load_all_logs()
        for chunks in self._logs.values():
            if chunks:
                chunks.append(PREVIOUS_SESSION_MARK)
        self._pending: list = []

        self._process = ProcessRunner(self)
        self._managed = ManagedRunner(self)
        for runner in (self._process, self._managed):
            runner.status_changed.connect(self.status_changed)
            runner.output.connect(self._on_output)

        self._flush_timer = QTimer(self)
        self._flush_timer.setInterval(FLUSH_MS)
        self._flush_timer.timeout.connect(self.flush_logs)
        self._flush_timer.start()

    def _runner(self, service):
        return self._managed if service.kind in MANAGED_KINDS else self._process

    def sync(self, services: list) -> None:
        self._services = {s.id: s for s in services}
        self._managed.sync(services)

    # ---- state ---------------------------------------------------------
    def status(self, sid: str) -> str:
        s = self._services.get(sid)
        return self._runner(s).status(sid) if s else "stopped"

    def is_active(self, sid: str) -> bool:
        return self.status(sid) in ACTIVE_STATES

    # ---- actions -------------------------------------------------------
    def start(self, sid: str) -> None:
        s = self._services.get(sid)
        if s:
            self._runner(s).start(s)

    def stop(self, sid: str) -> None:
        s = self._services.get(sid)
        if s:
            self._runner(s).stop(s)

    def start_auto(self) -> None:
        for s in list(self._services.values()):
            if s.auto_start:
                self.start(s.id)

    def stop_all_now(self) -> None:
        """On app close: stop only apps launched as our children.
        systemd services and Docker containers keep running."""
        self._process.stop_all_now()
        self.flush_logs()

    # ---- logs ----------------------------------------------------------
    def get_log(self, sid: str) -> str:
        return "".join(self._logs.get(sid, []))

    def clear_log(self, sid: str) -> None:
        self._logs[sid] = []
        self._pending = [(s, t) for s, t in self._pending if s != sid]
        storage.clear_logs(sid)

    def discard_log(self, sid: str) -> None:
        self._logs.pop(sid, None)
        self._pending = [(s, t) for s, t in self._pending if s != sid]
        storage.clear_logs(sid)

    def flush_logs(self) -> None:
        if self._pending:
            rows, self._pending = self._pending, []
            storage.append_logs(rows)

    def _on_output(self, sid: str, text: str) -> None:
        chunks = self._logs.setdefault(sid, [])
        chunks.append(text)
        if len(chunks) > MAX_LOG_CHUNKS:
            del chunks[: len(chunks) - MAX_LOG_CHUNKS]
        self._pending.append((sid, text))
        self.output.emit(sid, text)