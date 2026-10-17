from PySide6.QtCore import Qt, QTimer, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QLineEdit, QMainWindow, QMessageBox, QPushButton,
    QScrollArea, QSplitter, QVBoxLayout, QWidget,
)

from app import polkit_setup, storage
from app.constants import ACTIVE_STATES
from app.service_manager import ServiceManager
from app.ui.detect_dialog import DetectDialog
from app.ui.log_panel import LogPanel
from app.ui.service_card import ServiceCard
from app.ui.service_dialog import ServiceDialog
from app.ui.sidebar import Sidebar


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DevLauncher")
        self.resize(1200, 780)

        self.manager = ServiceManager(self)
        self.services = storage.load_services()
        self.manager.sync(self.services)
        self.cards: dict = {}
        self.category_filter = "All"

        self._build_ui()
        self._connect_signals()
        self._render_cards()
        QTimer.singleShot(400, self.manager.start_auto)

    # ---- UI ------------------------------------------------------------
    def _build_ui(self) -> None:
        self.sidebar = Sidebar()

        page_title = QLabel("Services")
        page_title.setObjectName("pageTitle")
        self.search = QLineEdit()
        self.search.setPlaceholderText("Search services…")
        self.search.setFixedWidth(220)
        self.detect_btn = QPushButton("Detect installed")
        self.detect_btn.setToolTip("Find databases, Docker, Nginx... already installed on this machine")
        self.passwordless_btn = QPushButton("Passwordless…")
        self.passwordless_btn.setToolTip("One-time setup: start/stop your system services without typing the admin password")
        self.stop_all_btn = QPushButton("Stop all")
        self.stop_all_btn.setToolTip("Stops every running service: commands, containers and system services")
        self.add_btn = QPushButton("+ Add Service")
        self.add_btn.setObjectName("primaryBtn")

        header = QHBoxLayout()
        header.setSpacing(8)
        header.addWidget(page_title)
        header.addStretch()
        header.addWidget(self.search)
        header.addWidget(self.detect_btn)
        header.addWidget(self.passwordless_btn)
        header.addWidget(self.stop_all_btn)
        header.addWidget(self.add_btn)

        self.cards_container = QWidget()
        self.cards_layout = QVBoxLayout(self.cards_container)
        self.cards_layout.setContentsMargins(0, 0, 8, 0)
        self.cards_layout.setSpacing(10)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setWidget(self.cards_container)
        # QScrollArea paints a light background by default -> keep it transparent
        scroll.viewport().setAutoFillBackground(False)
        self.cards_container.setAutoFillBackground(False)

        top = QWidget()
        top_layout = QVBoxLayout(top)
        top_layout.setContentsMargins(24, 20, 16, 12)
        top_layout.setSpacing(16)
        top_layout.addLayout(header)
        top_layout.addWidget(scroll, 1)

        self.log_panel = LogPanel()

        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.addWidget(top)
        splitter.addWidget(self.log_panel)
        splitter.setChildrenCollapsible(False)
        splitter.setSizes([400, 340])

        central = QWidget()
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(self.sidebar)
        root.addWidget(splitter, 1)
        self.setCentralWidget(central)

    def _connect_signals(self) -> None:
        self.add_btn.clicked.connect(self._add_service)
        self.detect_btn.clicked.connect(self._detect_installed)
        self.passwordless_btn.clicked.connect(self._passwordless_setup)
        self.stop_all_btn.clicked.connect(self._stop_all)
        self.search.textChanged.connect(lambda _: self._render_cards())
        self.sidebar.category_changed.connect(self._set_category)
        self.log_panel.clear_requested.connect(self._clear_logs)
        self.manager.status_changed.connect(self._on_status_changed)
        self.manager.output.connect(self.log_panel.append)

    # ---- rendering -----------------------------------------------------
    def _matches(self, s) -> bool:
        if self.category_filter == "Running":
            if self.manager.status(s.id) not in ACTIVE_STATES:
                return False
        elif self.category_filter != "All" and s.category != self.category_filter:
            return False
        query = self.search.text().strip().lower()
        return not query or any(query in text.lower() for text in (s.name, s.command, s.target))

    def _render_cards(self) -> None:
        while self.cards_layout.count():
            item = self.cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.cards.clear()

        visible = [s for s in self.services if self._matches(s)]
        if not visible:
            text = ("Nothing here yet.\nClick “+ Add Service” or “Detect installed”."
                    if not self.services else "No services match this filter.")
            empty = QLabel(text)
            empty.setObjectName("emptyState")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.cards_layout.addWidget(empty)

        for s in visible:
            card = ServiceCard(s)
            card.set_status(self.manager.status(s.id))
            card.start_clicked.connect(self._start)
            card.stop_clicked.connect(self.manager.stop)
            card.open_clicked.connect(self._open_url)
            card.logs_clicked.connect(self._show_logs)
            card.edit_clicked.connect(self._edit)
            card.delete_clicked.connect(self._delete)
            self.cards[s.id] = card
            self.cards_layout.addWidget(card)

        self.cards_layout.addStretch()
        self._update_stats()

    def _update_stats(self) -> None:
        running = sum(self.manager.status(s.id) == "running" for s in self.services)
        self.sidebar.set_running_count(running, len(self.services))

    def _persist(self) -> None:
        storage.save_services(self.services)
        self.manager.sync(self.services)
        self._render_cards()

    # ---- actions -------------------------------------------------------
    def _find(self, sid: str):
        return next((s for s in self.services if s.id == sid), None)

    def _add_service(self) -> None:
        dialog = ServiceDialog(self)
        if dialog.exec():
            self.services.append(dialog.get_service())
            self._persist()

    def _detect_installed(self) -> None:
        dialog = DetectDialog(self.services, self)
        if dialog.exec():
            added = dialog.get_services()
            if added:
                self.services.extend(added)
                self._persist()

    def _passwordless_setup(self) -> None:
        if not polkit_setup.is_supported():
            QMessageBox.information(
                self, "Not available",
                "Passwordless setup works on Linux with polkit (pkexec) only.")
            return
        units = sorted({s.target for s in self.services if s.kind == "systemd"})
        installed = polkit_setup.is_installed()
        if not units and not installed:
            QMessageBox.information(
                self, "Nothing to set up",
                "Add a System service first (for example MySQL or PostgreSQL), then run this again.")
            return

        listing = "\n".join(f"  • {u}" for u in units) or "  (none)"
        box = QMessageBox(self)
        box.setWindowTitle("Passwordless service control")
        box.setText(
            "Enter your admin password ONE time. DevLauncher installs a small polkit rule that lets "
            "your user start/stop only these system services without a password:\n\n"
            f"{listing}\n\nNothing else is elevated. Run this again after adding new system services."
            + ("\n\nThe rule is currently installed." if installed else ""))
        enable = None
        if units:
            enable = box.addButton("Update rule" if installed else "Enable",
                                   QMessageBox.ButtonRole.AcceptRole)
        remove = None
        if installed:
            remove = box.addButton("Remove rule", QMessageBox.ButtonRole.DestructiveRole)
        box.addButton("Cancel", QMessageBox.ButtonRole.RejectRole)
        box.exec()

        clicked = box.clickedButton()
        if enable is not None and clicked is enable:
            ok, message = polkit_setup.install(units)
        elif remove is not None and clicked is remove:
            ok, message = polkit_setup.remove()
        else:
            return
        show = QMessageBox.information if ok else QMessageBox.warning
        show(self, "Passwordless setup", message)

    def _edit(self, sid: str) -> None:
        current = self._find(sid)
        if not current:
            return
        dialog = ServiceDialog(self, current)
        if dialog.exec():
            updated = dialog.get_service()
            self.services = [updated if s.id == sid else s for s in self.services]
            self.log_panel.rename(sid, updated.name, self.manager.status(sid))
            self._persist()

    def _start(self, sid: str) -> None:
        service = self._find(sid)
        if service:
            self._show_logs(sid)
            self.manager.start(sid)

    def _stop_all(self) -> None:
        active = [s for s in self.services if self.manager.is_active(s.id)]
        if not active:
            return
        system = [s for s in active if s.kind in ("systemd", "systemd-user")]
        if system:
            names = ", ".join(s.name for s in system)
            answer = QMessageBox.question(
                self, "Stop all",
                f"This will also stop system services: {names}.\n\nContinue?")
            if answer != QMessageBox.StandardButton.Yes:
                return
        for s in active:
            self.manager.stop(s.id)

    def _open_url(self, sid: str) -> None:
        service = self._find(sid)
        if service and service.port:
            QDesktopServices.openUrl(QUrl(f"http://localhost:{service.port}"))

    def _delete(self, sid: str) -> None:
        service = self._find(sid)
        if not service:
            return
        extra = "" if service.kind == "command" else "\n(The actual service/container is not removed or stopped.)"
        answer = QMessageBox.question(self, "Remove service", f"Remove “{service.name}” from DevLauncher?{extra}")
        if answer != QMessageBox.StandardButton.Yes:
            return
        if service.kind == "command":
            self.manager.stop(sid)
        self.log_panel.close_tab(sid)
        self.manager.discard_log(sid)
        self.services = [s for s in self.services if s.id != sid]
        self._persist()

    def _set_category(self, category: str) -> None:
        self.category_filter = category or "All"
        self._render_cards()

    def _show_logs(self, sid: str) -> None:
        service = self._find(sid)
        if service:
            self.log_panel.open(sid, service.name, self.manager.get_log(sid))
            self.log_panel.set_status(sid, self.manager.status(sid))

    def _clear_logs(self, sid: str) -> None:
        self.manager.clear_log(sid)
        self.log_panel.clear_view(sid)

    # ---- manager callbacks --------------------------------------------
    def _on_status_changed(self, sid: str, status: str) -> None:
        self.log_panel.set_status(sid, status)
        if self.category_filter == "Running":
            self._render_cards()
            return
        card = self.cards.get(sid)
        if card:
            card.set_status(status)
        self._update_stats()

    def closeEvent(self, event) -> None:
        self.manager.stop_all_now()
        event.accept()
