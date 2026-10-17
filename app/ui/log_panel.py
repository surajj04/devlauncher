from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QFrame, QHBoxLayout, QLabel, QPlainTextEdit,
    QPushButton, QStackedWidget, QTabWidget, QVBoxLayout, QWidget,
)


class LogView(QWidget):
    """Log output of ONE service (one tab)."""

    clear_requested = Signal(str)
    close_requested = Signal(str)

    def __init__(self, service_id: str, parent=None):
        super().__init__(parent)
        self.service_id = service_id

        self.view = QPlainTextEdit()
        self.view.setObjectName("logView")
        self.view.setReadOnly(True)
        self.view.setMaximumBlockCount(5000)
        self.view.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)

        self.autoscroll = QCheckBox("Auto-scroll")
        self.autoscroll.setChecked(True)
        copy_btn = QPushButton("Copy")
        copy_btn.setObjectName("ghostBtn")
        copy_btn.clicked.connect(lambda: QApplication.clipboard().setText(self.view.toPlainText()))
        clear_btn = QPushButton("Clear")
        clear_btn.setObjectName("ghostBtn")
        clear_btn.clicked.connect(lambda: self.clear_requested.emit(self.service_id))
        close_btn = QPushButton("Close tab")
        close_btn.setObjectName("ghostBtn")
        close_btn.clicked.connect(lambda: self.close_requested.emit(self.service_id))

        toolbar = QHBoxLayout()
        toolbar.setContentsMargins(12, 6, 12, 0)
        toolbar.addStretch()
        toolbar.addWidget(self.autoscroll)
        toolbar.addWidget(copy_btn)
        toolbar.addWidget(clear_btn)
        toolbar.addWidget(close_btn)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addLayout(toolbar)
        layout.addWidget(self.view, 1)

    def set_text(self, text: str) -> None:
        self.view.setPlainText(text)
        self._scroll()

    def append(self, text: str) -> None:
        # write through our own cursor so the user's text selection isn't disturbed
        cursor = QTextCursor(self.view.document())
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertText(text)
        self._scroll()

    def clear(self) -> None:
        self.view.clear()

    def _scroll(self) -> None:
        if self.autoscroll.isChecked():
            bar = self.view.verticalScrollBar()
            bar.setValue(bar.maximum())


class LogPanel(QFrame):
    """Bottom panel: one tab per service, each with its own live log."""

    clear_requested = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("logPanel")
        self._views: dict = {}
        self._names: dict = {}

        placeholder = QLabel("Click “Logs” on a service - every app gets its own log tab.")
        placeholder.setObjectName("logPlaceholder")
        placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)

        self.stack = QStackedWidget()
        self.stack.addWidget(placeholder)
        self.stack.addWidget(self.tabs)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.stack)

    def open(self, sid: str, name: str, text: str) -> None:
        view = self._views.get(sid)
        if view is None:
            view = LogView(sid)
            view.set_text(text)
            view.clear_requested.connect(self.clear_requested)
            view.close_requested.connect(self.close_tab)
            self._views[sid] = view
            self._names[sid] = name
            self.tabs.addTab(view, name)
        self.tabs.setCurrentWidget(view)
        self.stack.setCurrentWidget(self.tabs)

    def append(self, sid: str, text: str) -> None:
        view = self._views.get(sid)
        if view:
            view.append(text)

    def clear_view(self, sid: str) -> None:
        view = self._views.get(sid)
        if view:
            view.clear()

    def set_status(self, sid: str, status: str) -> None:
        view = self._views.get(sid)
        if view:
            prefix = "● " if status == "running" else ""
            self.tabs.setTabText(self.tabs.indexOf(view), prefix + self._names[sid])

    def rename(self, sid: str, name: str, status: str) -> None:
        if sid in self._views:
            self._names[sid] = name
            self.set_status(sid, status)

    def close_tab(self, sid: str) -> None:
        view = self._views.pop(sid, None)
        self._names.pop(sid, None)
        if view:
            self.tabs.removeTab(self.tabs.indexOf(view))
            view.deleteLater()
        if not self._views:
            self.stack.setCurrentIndex(0)
