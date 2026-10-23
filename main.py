import sys
import os
from pathlib import Path

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from app.styles import STYLESHEET
from app.ui.main_window import MainWindow

os.environ.setdefault("QT_QPA_PLATFORMTHEME", "generic")
os.environ.setdefault(
    "QT_LOGGING_RULES",
    "qt.qpa.wayland.textinput=false;qt.qpa.wayland.textinput*=false",
)   # 👈 add this

def _icon_path() -> Path | None:
    """Find the app icon in dev and frozen (PyInstaller) modes."""
    if getattr(sys, "frozen", False):
        # PyInstaller extracts bundled files to sys._MEIPASS
        base = Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
        candidates = [
            base / "assets" / "icon.png",
            base / "icon.png",
        ]
    else:
        # Dev mode — project root is main.py's folder
        base = Path(__file__).resolve().parent
        candidates = [
            base / "assets" / "icon.png",
            base / "icon.png",
        ]

    for p in candidates:
        if p.exists():
            return p
    return None


def main() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName("DevLauncher")
    app.setStyleSheet(STYLESHEET)

    # 👇 set window icon (taskbar, Alt+Tab, title bar)
    icon_path = _icon_path()
    if icon_path is not None:
        app.setWindowIcon(QIcon(str(icon_path)))

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()