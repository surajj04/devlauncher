from PySide6.QtCore import Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout

from app.models import Service

STATUS_TEXT = {
    "running": "Running",
    "stopped": "Stopped",
    "error": "Error",
    "starting": "Starting…",
    "stopping": "Stopping…",
}


def _repolish(widget) -> None:
    widget.style().unpolish(widget)
    widget.style().polish(widget)


class ServiceCard(QFrame):
    """One row in the services list."""

    start_clicked = Signal(str)
    stop_clicked = Signal(str)
    open_clicked = Signal(str)
    logs_clicked = Signal(str)
    edit_clicked = Signal(str)
    delete_clicked = Signal(str)

    def __init__(self, service: Service, parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self.service = service

        self.dot = QLabel()
        self.dot.setObjectName("statusDot")
        self.dot.setFixedSize(10, 10)

        name = QLabel(service.name)
        name.setObjectName("serviceName")
        title_row = QHBoxLayout()
        title_row.setSpacing(8)
        title_row.addWidget(name)
        for text, obj in (
            (service.category, "badge"),
            (service.kind if service.kind != "command" else "", "badgeKind"),
            ("auto-start" if service.auto_start else "", "badgeAuto"),
        ):
            if text:
                badge = QLabel(text)
                badge.setObjectName(obj)
                title_row.addWidget(badge)
        title_row.addStretch()

        subtitle = QLabel(service.subtitle)
        subtitle.setObjectName("serviceCommand")

        info = QVBoxLayout()
        info.setSpacing(3)
        info.addLayout(title_row)
        info.addWidget(subtitle)
        if service.kind == "command" and service.working_dir:
            folder = QLabel(service.working_dir)
            folder.setObjectName("serviceDir")
            info.addWidget(folder)

        self.status_text = QLabel("Stopped")
        self.status_text.setObjectName("statusText")

        self.start_btn = QPushButton("Start")
        self.start_btn.setObjectName("startBtn")
        self.stop_btn = QPushButton("Stop")
        self.stop_btn.setObjectName("stopBtn")
        self.open_btn = QPushButton("Open")
        self.open_btn.setToolTip(f"Open http://localhost:{service.port}")
        logs_btn = QPushButton("Logs")
        logs_btn.setObjectName("ghostBtn")
        edit_btn = QPushButton("Edit")
        edit_btn.setObjectName("ghostBtn")
        delete_btn = QPushButton("Delete")
        delete_btn.setObjectName("ghostBtn")

        sid = service.id
        self.start_btn.clicked.connect(lambda: self.start_clicked.emit(sid))
        self.stop_btn.clicked.connect(lambda: self.stop_clicked.emit(sid))
        self.open_btn.clicked.connect(lambda: self.open_clicked.emit(sid))
        logs_btn.clicked.connect(lambda: self.logs_clicked.emit(sid))
        edit_btn.clicked.connect(lambda: self.edit_clicked.emit(sid))
        delete_btn.clicked.connect(lambda: self.delete_clicked.emit(sid))

        row = QHBoxLayout(self)
        row.setContentsMargins(16, 14, 16, 14)
        row.setSpacing(10)
        row.addWidget(self.dot)
        row.addLayout(info, 1)
        row.addWidget(self.status_text)
        row.addWidget(self.start_btn)
        row.addWidget(self.stop_btn)
        row.addWidget(self.open_btn)
        row.addWidget(logs_btn)
        row.addWidget(edit_btn)
        row.addWidget(delete_btn)

        self.set_status("stopped")

    def set_status(self, status: str) -> None:
        running = status == "running"
        starting = status == "starting"
        stopping = status == "stopping"

        self.start_btn.setVisible(not (running or stopping))
        self.start_btn.setEnabled(not starting)
        self.start_btn.setText("Starting…" if starting else "Start")
        self.stop_btn.setVisible(running or stopping)
        self.stop_btn.setEnabled(not stopping)
        self.stop_btn.setText("Stopping…" if stopping else "Stop")
        self.open_btn.setVisible(running and bool(self.service.port))

        self.status_text.setText(STATUS_TEXT.get(status, status))
        for widget in (self.dot, self.status_text):
            widget.setProperty("status", status)
            _repolish(widget)
