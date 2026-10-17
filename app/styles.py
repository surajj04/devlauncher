STYLESHEET = """
* { font-family: "Segoe UI", "Inter", "Helvetica Neue", sans-serif; font-size: 13px; color: #e5e7eb; }
QMainWindow, QDialog { background: #0f1115; }
QToolTip { background: #1c2128; color: #e5e7eb; border: 1px solid #2d3544; padding: 4px; }

/* Sidebar */
#sidebar { background: #14171d; border-right: 1px solid #232831; }
#appTitle { font-size: 18px; font-weight: 700; }
#appSubtitle { color: #8b93a1; font-size: 11px; }
#statsLabel { color: #8b93a1; font-size: 12px; }
QListWidget { background: transparent; border: none; outline: none; }
QListWidget::item { padding: 10px 12px; border-radius: 8px; margin: 2px 0; color: #aab1be; }
QListWidget::item:hover { background: #1c2128; }
QListWidget::item:selected { background: #2b3350; color: #ffffff; }

/* Header */
#pageTitle { font-size: 20px; font-weight: 700; }

/* Inputs */
QLineEdit, QComboBox, QSpinBox, QPlainTextEdit {
    background: #171a21; border: 1px solid #2d3544; border-radius: 8px; padding: 8px 10px;
}
QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QPlainTextEdit:focus { border-color: #4f6ef7; }
QComboBox QAbstractItemView { background: #171a21; selection-background-color: #2b3350; border: 1px solid #2d3544; }
QComboBox::drop-down { border: none; width: 24px; }
QCheckBox { spacing: 8px; }
QCheckBox::indicator, QListWidget::indicator {
    width: 16px; height: 16px; border: 1px solid #3a4457; border-radius: 4px; background: #171a21;
}
QCheckBox::indicator:checked, QListWidget::indicator:checked { background: #4f6ef7; border-color: #4f6ef7; }

/* Buttons */
QPushButton { background: #222834; border: 1px solid #2d3544; border-radius: 8px; padding: 7px 14px; }
QPushButton:hover { background: #2a3140; }
QPushButton:disabled { color: #6b7280; background: #1a1f29; }
#primaryBtn { background: #4f6ef7; border: none; color: #ffffff; font-weight: 600; }
#primaryBtn:hover { background: #637dff; }
#startBtn { background: #16a34a; border: none; color: #ffffff; font-weight: 600; }
#startBtn:hover { background: #22b85a; }
#startBtn:disabled { background: #14532d; color: #9ca3af; }
#stopBtn { background: #dc2626; border: none; color: #ffffff; font-weight: 600; }
#stopBtn:hover { background: #ef4444; }
#stopBtn:disabled { background: #7f1d1d; color: #9ca3af; }
#ghostBtn { background: transparent; border: none; color: #8b93a1; padding: 7px 10px; }
#ghostBtn:hover { color: #ffffff; background: #1c2128; }

/* Service card */
#card { background: #171a21; border: 1px solid #242a35; border-radius: 12px; }
#card:hover { border-color: #3b4560; }
#serviceName { font-size: 15px; font-weight: 600; }
#serviceCommand { color: #9aa3b2; font-family: Consolas, "JetBrains Mono", monospace; font-size: 12px; }
#serviceDir { color: #6b7280; font-size: 11px; }
#badge { background: #232a3a; color: #9db0ff; border-radius: 6px; padding: 2px 8px; font-size: 11px; }
#badgeKind { background: #1f3a2e; color: #6ee7b7; border-radius: 6px; padding: 2px 8px; font-size: 11px; }
#badgeAuto { background: #3a2f1a; color: #fcd34d; border-radius: 6px; padding: 2px 8px; font-size: 11px; }
#statusDot { border-radius: 5px; background: #6b7280; }
#statusDot[status="running"] { background: #22c55e; }
#statusDot[status="error"] { background: #ef4444; }
#statusDot[status="starting"], #statusDot[status="stopping"] { background: #f59e0b; }
#statusText { color: #6b7280; font-size: 12px; min-width: 70px; }
#statusText[status="running"] { color: #22c55e; }
#statusText[status="error"] { color: #ef4444; }
#statusText[status="starting"], #statusText[status="stopping"] { color: #f59e0b; }
#emptyState { color: #6b7280; font-size: 14px; padding: 40px; }

/* Logs */
#logPanel { background: #0b0d11; border-top: 1px solid #232831; }
#logPlaceholder { color: #6b7280; }
#logView {
    background: #0b0d11; border: none; border-radius: 0; padding: 4px;
    color: #c9d1d9; font-family: Consolas, "JetBrains Mono", monospace; font-size: 12px;
}
QTabWidget::pane { border: none; }
QTabBar::tab { background: transparent; color: #8b93a1; padding: 9px 16px; border-bottom: 2px solid transparent; }
QTabBar::tab:hover { color: #ffffff; }
QTabBar::tab:selected { color: #ffffff; border-bottom: 2px solid #4f6ef7; }

/* Misc */
QScrollArea { border: none; background: transparent; }
QScrollBar:vertical { background: transparent; width: 10px; }
QScrollBar::handle:vertical { background: #2d3544; border-radius: 5px; min-height: 30px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar:horizontal { background: transparent; height: 10px; }
QScrollBar::handle:horizontal { background: #2d3544; border-radius: 5px; min-width: 30px; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }
QSplitter::handle { background: #232831; }
#formError { color: #f87171; }
#noteLabel { color: #fbbf24; }
#hintLabel { color: #8b93a1; }
"""
