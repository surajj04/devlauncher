from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication, QDialog, QHBoxLayout, QLabel, QListWidget, QListWidgetItem,
    QPushButton, QVBoxLayout,
)

from app import detector
from app.models import Service


class DetectDialog(QDialog):
    """Scans this machine for installed apps and lets you import them."""

    def __init__(self, existing: list, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Detect installed apps")
        self.setMinimumSize(560, 460)

        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        try:
            found, notes = detector.detect_all()
        finally:
            QApplication.restoreOverrideCursor()

        known = {(s.kind, s.command if s.kind == "command" else s.target) for s in existing}
        new_items = [d for d in found if d.key not in known]
        skipped = len(found) - len(new_items)

        intro = QLabel("Found on this machine - tick the ones you want to manage:")
        self.list = QListWidget()
        for d in new_items:
            item = QListWidgetItem(f"{d.name}    ·    {d.detail}")
            item.setData(Qt.ItemDataRole.UserRole, d)
            item.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
            item.setCheckState(Qt.CheckState.Unchecked)
            self.list.addItem(item)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)
        layout.addWidget(intro)
        layout.addWidget(self.list, 1)

        if not new_items:
            empty = QLabel("Nothing new found." if found else "No supported apps were detected.")
            empty.setObjectName("hintLabel")
            layout.addWidget(empty)
        if skipped:
            hint = QLabel(f"{skipped} detected app(s) are already in your list.")
            hint.setObjectName("hintLabel")
            layout.addWidget(hint)
        for note in notes:
            label = QLabel(note)
            label.setObjectName("noteLabel")
            label.setWordWrap(True)
            layout.addWidget(label)

        select_all = QPushButton("Select all")
        select_all.clicked.connect(self._select_all)
        cancel = QPushButton("Cancel")
        cancel.clicked.connect(self.reject)
        add = QPushButton("Add selected")
        add.setObjectName("primaryBtn")
        add.clicked.connect(self.accept)

        buttons = QHBoxLayout()
        buttons.addWidget(select_all)
        buttons.addStretch()
        buttons.addWidget(cancel)
        buttons.addWidget(add)
        layout.addLayout(buttons)

    def _select_all(self) -> None:
        for i in range(self.list.count()):
            self.list.item(i).setCheckState(Qt.CheckState.Checked)

    def get_services(self) -> list:
        services = []
        for i in range(self.list.count()):
            item = self.list.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                d = item.data(Qt.ItemDataRole.UserRole)
                services.append(Service(name=d.name, kind=d.kind, category=d.category,
                                        command=d.command, target=d.target))
        return services
