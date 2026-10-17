from PySide6.QtCore import Signal
from PySide6.QtWidgets import QFrame, QLabel, QListWidget, QVBoxLayout

from app.constants import CATEGORIES


class Sidebar(QFrame):
    """Left navigation: filters + running counter."""

    category_changed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("sidebar")
        self.setFixedWidth(210)

        title = QLabel("DevLauncher")
        title.setObjectName("appTitle")
        subtitle = QLabel("Run everything from one place")
        subtitle.setObjectName("appSubtitle")

        self.nav = QListWidget()
        self.nav.addItems(["All", "Running"] + CATEGORIES)
        self.nav.currentTextChanged.connect(self.category_changed.emit)
        self.nav.setCurrentRow(0)

        self.stats = QLabel("0 running")
        self.stats.setObjectName("statsLabel")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 20, 16, 16)
        layout.setSpacing(4)
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(18)
        layout.addWidget(self.nav, 1)
        layout.addWidget(self.stats)

    def set_running_count(self, running: int, total: int) -> None:
        self.stats.setText(f"{running} running · {total} total")
