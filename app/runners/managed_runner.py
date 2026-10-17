"""Runs 'managed' services: systemd units, user services and Docker containers.

They aren't children of the launcher, so we start/stop them with a one-shot
command and poll their real status every few seconds. While running, a follower
process (journalctl -f / docker logs -f) streams their live logs.

System services run plain `systemctl` first (polkit decides: silent if the
DevLauncher rule is installed, otherwise a graphical prompt). If that fails with
an authentication error we retry once through pkexec.
"""
import os
import shutil

from PySide6.QtCore import QObject, QProcess, QTimer, Signal

from app.constants import MANAGED_KINDS
from app.utils import strip_ansi

POLL_MS = 3000
MERGED = QProcess.ProcessChannelMode.MergedChannels
FAILED_TO_START = QProcess.ProcessError.FailedToStart
AUTH_WORDS = ("authentication", "authorization", "authorized", "access denied", "permission denied")


def _privileged(argv: list) -> list:
    if hasattr(os, "geteuid") and os.geteuid() == 0:
        return argv
    if shutil.which("pkexec"):          # graphical password prompt
        return ["pkexec", *argv]
    return ["sudo", "-n", *argv]


def _argv(s, action: str, elevate: bool) -> list:
    if s.kind == "systemd":
        units = [s.target]
        if action == "stop" and s.target in ("docker", "docker.service"):
            units.insert(0, "docker.socket")  # otherwise the socket restarts the engine
        argv = ["systemctl", action, *units]
        return _privileged(argv) if elevate else argv
    if s.kind == "systemd-user":
        return ["systemctl", "--user", action, s.target]
    return ["docker", action, s.target]


def probe_cmd(s) -> list:
    if s.kind == "systemd":
        return ["systemctl", "is-active", s.target]
    if s.kind == "systemd-user":
        return ["systemctl", "--user", "is-active", s.target]
    return ["docker", "inspect", "-f", "{{.State.Running}}", s.target]


def is_up(s, stdout: str) -> bool:
    out = stdout.strip()
    return out == "active" if s.kind in ("systemd", "systemd-user") else out == "true"


def follow_cmd(s) -> list:
    if s.kind == "systemd":
        return ["journalctl", "-u", s.target, "-f", "-n", "50", "--no-pager"]
    if s.kind == "systemd-user":
        return ["journalctl", "--user", "-u", s.target, "-f", "-n", "50", "--no-pager"]
    return ["docker", "logs", "-f", "--tail", "100", s.target]


class ManagedRunner(QObject):
    status_changed = Signal(str, str)
    output = Signal(str, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._services: dict = {}
        self._state: dict = {}
        self._actions: dict = {}
        self._action_ctx: dict = {}
        self._action_out: dict = {}
        self._probes: dict = {}
        self._followers: dict = {}
        self._timer = QTimer(self)
        self._timer.setInterval(POLL_MS)
        self._timer.timeout.connect(self.poll)
        self._timer.start()

    # ---- public --------------------------------------------------------
    def status(self, sid: str) -> str:
        return self._state.get(sid, "stopped")

    def sync(self, services: list) -> None:
        old = self._services
        self._services = {s.id: s for s in services if s.kind in MANAGED_KINDS}
        for sid in list(self._state):
            if sid not in self._services:
                self._state.pop(sid, None)
                self._stop_follower(sid)
        for sid, s in self._services.items():
            prev = old.get(sid)
            if prev and (prev.kind, prev.target) != (s.kind, s.target):
                self._stop_follower(sid)
                self._state[sid] = "stopped"
            self._probe(sid)

    def poll(self) -> None:
        for sid in list(self._services):
            self._probe(sid)

    def start(self, s) -> None:
        if self.status(s.id) in ("starting", "running", "stopping") or s.id in self._actions:
            return
        self._run_action(s, "start")

    def stop(self, s) -> None:
        if self.status(s.id) != "running" or s.id in self._actions:
            return
        self._run_action(s, "stop")

    # ---- one-shot start/stop ------------------------------------------
    def _run_action(self, s, action: str, elevate: bool = False) -> None:
        sid = s.id
        argv = _argv(s, action, elevate)
        self._set_state(sid, "starting" if action == "start" else "stopping")
        self.output.emit(sid, f"\n$ {' '.join(argv)}\n")
        proc = QProcess(self)
        proc.setProcessChannelMode(MERGED)
        proc.readyReadStandardOutput.connect(lambda p=proc: self._read_action(sid, p))
        proc.errorOccurred.connect(lambda err: self._on_action_error(sid, err, argv[0]))
        proc.finished.connect(lambda code, st: self._on_action_done(sid, code))
        self._actions[sid] = proc
        self._action_ctx[sid] = (s, action, elevate)
        self._action_out[sid] = ""
        proc.start(argv[0], argv[1:])

    def _read_action(self, sid: str, proc: QProcess) -> None:
        raw = bytes(proc.readAllStandardOutput()).decode("utf-8", errors="replace")
        text = strip_ansi(raw)
        self._action_out[sid] = self._action_out.get(sid, "") + text
        self.output.emit(sid, text)

    def _emit_from(self, sid: str, proc: QProcess) -> None:
        raw = bytes(proc.readAllStandardOutput()).decode("utf-8", errors="replace")
        self.output.emit(sid, strip_ansi(raw))

    def _on_action_error(self, sid: str, error, program: str) -> None:
        if error == FAILED_TO_START:
            self.output.emit(sid, f"[error] Could not run '{program}'. Is it installed?\n")
            proc = self._actions.pop(sid, None)
            if proc:
                proc.deleteLater()
            self._action_ctx.pop(sid, None)
            self._action_out.pop(sid, None)
            self._set_state(sid, "error")

    def _on_action_done(self, sid: str, code: int) -> None:
        proc = self._actions.pop(sid, None)
        if proc:
            proc.deleteLater()
        out = self._action_out.pop(sid, "").lower()
        ctx = self._action_ctx.pop(sid, None)
        if code != 0 and ctx:
            s, action, elevated = ctx
            if s.kind == "systemd" and not elevated and any(w in out for w in AUTH_WORDS):
                self.output.emit(sid, "[needs authentication - retrying with pkexec]\n")
                self._run_action(s, action, elevate=True)
                return
            self.output.emit(sid, f"[failed with exit code {code}]\n")
            self._set_state(sid, "error")
        self._probe(sid)

    # ---- status polling ------------------------------------------------
    def _probe(self, sid: str) -> None:
        s = self._services.get(sid)
        if s is None or sid in self._probes or sid in self._actions:
            return
        argv = probe_cmd(s)
        proc = QProcess(self)
        proc.finished.connect(lambda code, st, p=proc: self._probe_finished(sid, p))
        proc.errorOccurred.connect(lambda err: self._finish_probe(sid, False) if err == FAILED_TO_START else None)
        self._probes[sid] = proc
        proc.start(argv[0], argv[1:])

    def _probe_finished(self, sid: str, proc: QProcess) -> None:
        out = bytes(proc.readAllStandardOutput()).decode("utf-8", errors="replace")
        s = self._services.get(sid)
        self._finish_probe(sid, bool(s) and is_up(s, out))

    def _finish_probe(self, sid: str, up: bool) -> None:
        proc = self._probes.pop(sid, None)
        if proc is None:
            return
        proc.deleteLater()
        if sid in self._actions or sid not in self._services:
            return
        cur = self._state.get(sid, "stopped")
        if up:
            new = "running"
        elif cur == "error":
            new = "error"
        else:
            new = "stopped"
        self._set_state(sid, new)

    def _set_state(self, sid: str, new: str) -> None:
        old = self._state.get(sid, "stopped")
        if old == new:
            return
        self._state[sid] = new
        self.status_changed.emit(sid, new)
        s = self._services.get(sid)
        if new == "running" and s:
            self._start_follower(s)
        elif old == "running":
            self._stop_follower(sid)

    # ---- live log following -------------------------------------------
    def _start_follower(self, s) -> None:
        sid = s.id
        if sid in self._followers:
            return
        argv = follow_cmd(s)
        proc = QProcess(self)
        proc.setProcessChannelMode(MERGED)
        proc.readyReadStandardOutput.connect(lambda p=proc: self._emit_from(sid, p))
        proc.finished.connect(lambda code, st, p=proc: self._follower_done(sid, p))
        self._followers[sid] = proc
        self.output.emit(sid, f"\n[following logs] {' '.join(argv)}\n")
        proc.start(argv[0], argv[1:])

    def _follower_done(self, sid: str, proc: QProcess) -> None:
        if self._followers.get(sid) is proc:
            self._followers.pop(sid, None)
        proc.deleteLater()

    def _stop_follower(self, sid: str) -> None:
        proc = self._followers.pop(sid, None)
        if proc is not None and proc.state() != QProcess.ProcessState.NotRunning:
            proc.terminate()
