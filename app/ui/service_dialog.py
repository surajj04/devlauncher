from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QDialog, QFileDialog, QFormLayout, QHBoxLayout, QLabel,
    QLineEdit, QPlainTextEdit, QPushButton, QSpinBox, QVBoxLayout, QWidget,
)

from app.constants import CATEGORIES, KIND_LABELS, PRESETS
from app.models import Service, format_env, parse_env


class ServiceDialog(QDialog):
    """Add a new service, or edit an existing one when `service` is given."""

    def __init__(self, parent=None, service: Service | None = None):
        super().__init__(parent)
        self._service = service
        editing = service is not None
        self.setWindowTitle("Edit Service" if editing else "Add Service")
        self.setMinimumWidth(560)

        self.preset = QComboBox()
        self.preset.addItems(PRESETS.keys())
        self.preset.currentTextChanged.connect(self._apply_preset)

        self.kind = QComboBox()
        for key, label in KIND_LABELS.items():
            self.kind.addItem(label, key)
        self.kind.currentIndexChanged.connect(self._update_visibility)

        self.name = QLineEdit()
        self.name.setPlaceholderText("e.g. My API")
        self.category = QComboBox()
        self.category.addItems(CATEGORIES)
        self.category.setCurrentText("Custom")

        self.command = QLineEdit()
        self.command.setPlaceholderText("e.g. npm run dev  /  uvicorn main:app --reload")
        self.working_dir = QLineEdit()
        self.working_dir.setPlaceholderText("Project folder (recommended)")
        self.venv = QLineEdit()
        self.venv.setPlaceholderText("Auto-detect (.venv / venv / env inside working dir)")
        self.env_edit = QPlainTextEdit()
        self.env_edit.setPlaceholderText("KEY=value  (one per line, optional)")
        self.env_edit.setFixedHeight(72)
        self.dir_row = self._with_browse(self.working_dir, self._browse_dir)
        self.venv_row = self._with_browse(self.venv, self._browse_venv)

        self.target = QLineEdit()
        self.port = QSpinBox()
        self.port.setRange(0, 65535)
        self.port.setSpecialValueText("None")
        self.auto_start = QCheckBox("Start automatically when DevLauncher opens")

        self.form = QFormLayout()
        self.form.setSpacing(12)
        if not editing:
            self.form.addRow("Preset", self.preset)
        self.form.addRow("Type", self.kind)
        self.form.addRow("Name", self.name)
        self.form.addRow("Category", self.category)
        self.form.addRow("Command", self.command)
        self.form.addRow("Working dir", self.dir_row)
        self.form.addRow("Python venv", self.venv_row)
        self.form.addRow("Env vars", self.env_edit)
        self.form.addRow("Target", self.target)
        self.form.addRow("Web port", self.port)
        self.form.addRow("", self.auto_start)

        self.error = QLabel("")
        self.error.setObjectName("formError")
        cancel = QPushButton("Cancel")
        cancel.clicked.connect(self.reject)
        save = QPushButton("Save" if editing else "Add Service")
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
        layout.addLayout(self.form)
        layout.addLayout(buttons)

        if editing:
            self._load(service)
        self._update_visibility()

    # ---- helpers -------------------------------------------------------
    def _with_browse(self, line_edit: QLineEdit, slot) -> QWidget:
        button = QPushButton("Browse")
        button.clicked.connect(slot)
        holder = QWidget()
        row = QHBoxLayout(holder)
        row.setContentsMargins(0, 0, 0, 0)
        row.addWidget(line_edit, 1)
        row.addWidget(button)
        return holder

    def _browse_dir(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Select working directory")
        if folder:
            self.working_dir.setText(folder)

    def _browse_venv(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Select the venv folder")
        if folder:
            self.venv.setText(folder)

    def _update_visibility(self) -> None:
        kind = self.kind.currentData()
        is_cmd = kind == "command"
        for widget in (self.command, self.dir_row, self.venv_row, self.env_edit):
            self.form.setRowVisible(widget, is_cmd)
        self.form.setRowVisible(self.target, not is_cmd)
        label = self.form.labelForField(self.target)
        if kind == "systemd":
            label.setText("Unit name")
            self.target.setPlaceholderText("e.g. mysql, postgresql, redis-server, nginx")
        elif kind == "systemd-user":
            label.setText("Unit name")
            self.target.setPlaceholderText("e.g. docker-desktop")
        else:
            label.setText("Container")
            self.target.setPlaceholderText("container name or id")
        self.adjustSize()

    def _apply_preset(self, key: str) -> None:
        name, kind, command, target, category, port = PRESETS[key]
        self.kind.setCurrentIndex(self.kind.findData(kind))
        self.name.setText(name)
        self.command.setText(command)
        self.target.setText(target)
        self.category.setCurrentText(category)
        self.port.setValue(port)

    def _load(self, s: Service) -> None:
        self.kind.setCurrentIndex(self.kind.findData(s.kind))
        self.name.setText(s.name)
        self.category.setCurrentText(s.category)
        self.command.setText(s.command)
        self.working_dir.setText(s.working_dir)
        self.venv.setText(s.venv)
        self.env_edit.setPlainText(format_env(s.env))
        self.target.setText(s.target)
        self.port.setValue(s.port)
        self.auto_start.setChecked(s.auto_start)

    def _on_save(self) -> None:
        kind = self.kind.currentData()
        if not self.name.text().strip():
            self.error.setText("Name is required.")
        elif kind == "command" and not self.command.text().strip():
            self.error.setText("Command is required.")
        elif kind != "command" and not self.target.text().strip():
            self.error.setText("Target is required.")
        else:
            self.accept()

    def get_service(self) -> Service:
        kind = self.kind.currentData()
        data = dict(
            name=self.name.text().strip(),
            kind=kind,
            category=self.category.currentText(),
            port=self.port.value(),
            auto_start=self.auto_start.isChecked(),
        )
        if kind == "command":
            data.update(
                command=self.command.text().strip(),
                working_dir=self.working_dir.text().strip(),
                venv=self.venv.text().strip(),
                env=parse_env(self.env_edit.toPlainText()),
            )
        else:
            data.update(target=self.target.text().strip())
        if self._service is not None:
            data["id"] = self._service.id
        return Service(**data)
