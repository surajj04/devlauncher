import sys
import os
from PySide6.QtWidgets import QApplication

from app.styles import STYLESHEET
from app.ui.main_window import MainWindow

os.environ.setdefault("QT_QPA_PLATFORMTHEME", "generic")

def main() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName("DevLauncher")
    app.setStyleSheet(STYLESHEET)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
