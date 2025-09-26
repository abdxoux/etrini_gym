from __future__ import annotations

import sys
from PyQt6.QtWidgets import QApplication
from router_qt import AppShellQt, PALETTE  # type: ignore
from qfluentwidgets import setTheme, Theme, setThemeColor


def main():
    app = QApplication(sys.argv)
    # Apply Fluent Material theme in dark mode to match existing visual identity
    try:
        setTheme(Theme.DARK)
        if isinstance(PALETTE, dict) and 'accent' in PALETTE:
            # Use app accent from router palette
            from PyQt6.QtGui import QColor
            setThemeColor(QColor(PALETTE['accent']))
    except Exception:
        pass
    shell = AppShellQt(services=None, start_route="Home")
    shell.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
