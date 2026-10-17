from PySide6.QtWidgets import (
    QComboBox, QDialog, QFileDialog, QFormLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QVBoxLayout,
)

from app.constants import CATEGORIES, PRESETS
from app.models import Service


class AddServiceDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Service")
        self.setMinimumWidth(480)

        self.preset = QComboBox()
        self.preset.addItems(PRESETS.keys())
        self.preset.currentTextChanged.connect(self._apply_preset)

        self.name = QLineEdit()
        self.name.setPlaceholderText("e.g. My API")
        self.command = QLineEdit()
        self.command.setPlaceholderText("e.g. npm run dev  /  python app.py")
        self.working_dir = QLineEdit()
        self.working_dir.setPlaceholderText("Optional - folder to run the command in")
        browse = QPushButton("Browse")
        browse.clicked.connect(self._browse)
        self.category = QComboBox()
        self.category.addItems(CATEGORIES)
        self.category.setCurrentText("Custom")

        dir_row = QHBoxLayout()
        dir_row.addWidget(self.working_dir, 1)
        dir_row.addWidget(browse)

        form = QFormLayout()
        form.setSpacing(12)
        form.addRow("Preset", self.preset)
        form.addRow("Name", self.name)
        form.addRow("Command", self.command)
        form.addRow("Working dir", dir_row)
        form.addRow("Category", self.category)

        self.error = QLabel("")
        self.error.setObjectName("formError")

        cancel = QPushButton("Cancel")
        cancel.clicked.connect(self.reject)
        save = QPushButton("Add Service")
        save.setObjectName("primaryBtn")
        save.setDefault(True)
        save.clicked.connect(self._on_save)

        buttons = QHBoxLayout()
        buttons.addWidget(self.error, 1)
        buttons.addWidget(cancel)
        buttons.addWidget(save)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        layout.addLayout(form)
        layout.addLayout(buttons)

    def _apply_preset(self, key: str) -> None:
        name, command, category = PRESETS[key]
        self.name.setText(name)
        self.command.setText(command)
        self.category.setCurrentText(category)

    def _browse(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Select working directory")
        if folder:
            self.working_dir.setText(folder)

    def _on_save(self) -> None:
        if not self.name.text().strip() or not self.command.text().strip():
            self.error.setText("Name and command are required.")
            return
        self.accept()

    def get_service(self) -> Service:
        return Service(
            name=self.name.text().strip(),
            command=self.command.text().strip(),
            working_dir=self.working_dir.text().strip(),
            category=self.category.currentText(),
        )
