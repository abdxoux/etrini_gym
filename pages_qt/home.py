from __future__ import annotations

from typing import Optional, List, Tuple

try:
    from router_qt import PALETTE
except Exception:
    PALETTE = {
        "bg": "#0f1218", "surface": "#151a22", "card": "#1b2130", "card2": "#1e2636",
        "accent": "#4f8cff", "muted": "#8b93a7", "text": "#e8ecf5",
    }

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QGridLayout, QFrame, QLabel, QPushButton
)
try:
    from qfluentwidgets import PushButton as FluentPushButton
except Exception:
    FluentPushButton = QPushButton  # fallback to native if qfluentwidgets not installed


def _label(text: str, *, color: Optional[str] = None, size: int = 13, bold: bool = False) -> QLabel:
    lbl = QLabel(text)
    weight = 600 if bold else 400
    c = color or PALETTE["text"]
    lbl.setStyleSheet(f"color:{c}; font-family:'Segoe UI'; font-size:{size}px; font-weight:{weight};")
    return lbl


class Tile(FluentPushButton):
    def __init__(self, label: str, route: str, on_click, parent: Optional[QWidget] = None):
        # qfluentwidgets.PushButton expects (parent) then setText();
        # native QPushButton accepts (label, parent). Support both.
        try:
            super().__init__(label, parent)
        except TypeError:
            super().__init__(parent)
            try:
                self.setText(label)
            except Exception:
                pass
        self.route = route
        self.on_click = on_click
        self.setProperty("cssClass", "tile")
        self.setMinimumHeight(96)
        self.clicked.connect(lambda: self.on_click(self.route))


class HomePage(QWidget):
    def __init__(self, services: Optional[object] = None, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.services = services
        self._nav_cb = None
        self.setObjectName("HomePage")
        self.setStyleSheet(
            f"""
            QWidget#HomePage {{ background-color:{PALETTE['surface']}; }}
            QLabel {{ color:{PALETTE['text']}; }}
            QPushButton[cssClass='tile'] {{
                background-color:#263042; color:{PALETTE['text']}; border:none; border-radius:16px;
                font-size:16px; font-weight:600; padding:10px 16px;
            }}
            QPushButton[cssClass='tile']:hover {{ background-color:#32405a; }}
            """
        )

        root = QVBoxLayout(self); root.setContentsMargins(12,12,12,12); root.setSpacing(10)

        self.grid_wrap = QFrame(); self.grid_wrap.setStyleSheet("background: transparent;")
        self.grid = QGridLayout(self.grid_wrap); self.grid.setContentsMargins(0,0,0,0); self.grid.setHorizontalSpacing(8); self.grid.setVerticalSpacing(8)
        root.addWidget(self.grid_wrap)
        # state: file-backed routes
        self._file_routes: dict[str, str] = {}
        self._tiles: list[Tile] = []
        # initial build with default static list
        self._rebuild_tiles()

    def set_nav_callback(self, cb):
        self._nav_cb = cb

    def _navigate(self, route: str):
        if callable(self._nav_cb):
            self._nav_cb(route)
        
    def set_file_routes(self, route_files: dict[str, str]):
        # route_files: {route_name: filename}
        self._file_routes = dict(route_files or {})
        self._rebuild_tiles()

    def _rebuild_tiles(self):
        # destroy previous tile widgets
        for t in getattr(self, "_tiles", []):
            try:
                t.setParent(None)
            except Exception:
                pass
        self._tiles = []
        # Determine tiles: if file_routes present, use them and label "filename – route"
        items: List[Tuple[str,str]]
        if self._file_routes:
            items = []
            for route, fname in self._file_routes.items():
                # hide Home route tile but keep all others
                if route == "Home":
                    continue
                label = f"{fname} – {route}" if fname else route
                items.append((label, route))
            # sort by filename (label starts with filename)
            items.sort(key=lambda t: (t[0] or '').lower())
        else:
            # fallback static
            items = [
                ("Dashboard", "Dashboard"),
                ("Members", "Members"),
                ("Member Profile", "Member Profile"),
                ("Subscriptions", "Subscriptions"),
                ("Attendance", "Attendance"),
                ("POS", "POS"),
                ("Inventory", "Inventory"),
                ("Accounting", "Accounting"),
                ("Reports", "Reports"),
                ("Settings", "Settings"),
            ]
        def nav_to(route: str): self._navigate(route)
        for label, route in items:
            self._tiles.append(Tile(label, route, nav_to))
        # initial layout
        self._relayout_tiles()

    def _relayout_tiles(self):
        # clear positions only
        while self.grid.count():
            it = self.grid.takeAt(0)
        width = max(1, self.width())
        cols = max(1, min(6, width // 260))
        for i in range(8):
            try:
                self.grid.setColumnStretch(i, 0)
            except Exception:
                pass
        for c in range(cols):
            self.grid.setColumnStretch(c, 1)
        r = c = 0
        for t in self._tiles:
            self.grid.addWidget(t, r, c)
            c += 1
            if c >= cols:
                c = 0
                r += 1

    def resizeEvent(self, event):
        super().resizeEvent(event)
        try:
            self._relayout_tiles()
        except Exception:
            pass


if __name__ == "__main__":
    # Standalone preview runner for HomePage design
    import sys
    from PyQt6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    try:
        # Apply Fluent dark theme if available
        from qfluentwidgets import setTheme, Theme
        setTheme(Theme.DARK)
    except Exception:
        pass
    root = QWidget(); root.setObjectName("Root"); root.setStyleSheet(f"QWidget#Root {{ background-color: {PALETTE['bg']}; }}")
    root.resize(1200, 720)
    page = HomePage(services=None, parent=root)
    lay = QVBoxLayout(root); lay.setContentsMargins(0,0,0,0); lay.addWidget(page)
    root.show(); sys.exit(app.exec())
