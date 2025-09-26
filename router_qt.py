from __future__ import annotations

from typing import Dict, Optional

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget,
    QMainWindow,
    QListWidget,
    QListWidgetItem,
    QStackedWidget,
    QHBoxLayout,
    QVBoxLayout,
    QFrame,
    QLabel,
)

PALETTE = {
    "bg": "#0f1218", "surface": "#151a22", "card": "#1b2130", "card2": "#1e2636",
    "accent": "#4f8cff", "accent2": "#8b6cff", "muted": "#8b93a7", "text": "#e8ecf5",
    "ok": "#22c55e", "warn": "#f59e0b", "danger": "#ef4444",
}


def _label(text: str, *, color: Optional[str] = None, bold: bool = False, size: int = 13) -> QLabel:
    lbl = QLabel(text)
    c = color or PALETTE["text"]
    weight = 600 if bold else 400
    lbl.setStyleSheet(f"color:{c}; font-family:'Segoe UI'; font-size:{size}px; font-weight:{weight};")
    return lbl


class MissingPage(QWidget):
    def __init__(self, name: str, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("MissingPage")
        self.setStyleSheet(f"QWidget#MissingPage {{ background-color:{PALETTE['surface']}; }}")
        lay = QVBoxLayout(self)
        card = QFrame(); card.setStyleSheet(f"background-color:{PALETTE['card']}; border-radius:16px;")
        g = QVBoxLayout(card); g.setContentsMargins(16,14,16,12)
        g.addWidget(_label(f"{name} (not implemented)", bold=True, size=16))
        g.addWidget(_label("Create pages_qt/<module>.py with <ClassName>Page", color=PALETTE["muted"]))
        lay.addWidget(card)


class RouterQt:
    def __init__(self, stack: QStackedWidget, services=None):
        self.stack = stack
        self.services = services
        self.route_to_index: Dict[str, int] = {}
        # Map route name -> filename for file-backed routes (for Home tiles)
        self.route_files: Dict[str, str] = {}
        self._build_routes()

    def _add_page(self, route: str, widget: QWidget):
        idx = self.stack.addWidget(widget)
        self.route_to_index[route] = idx

    def _build_routes(self):
        mapping = {
            "Home": ("pages_qt.home", "HomePage"),
            "Dashboard": ("pages_qt.dashboard_qt", "DashboardPage"),
            "Members": ("pages_qt.members", "MembersPage"),
            "Member Profile": ("pages_qt.member_profile", "MemberProfilePage"),
            "Subscriptions": ("pages_qt.subscriptions", "SubscriptionsPage"),
            "Attendance": ("pages_qt.attendance", "AttendancePage"),
            "POS": ("pages_qt.pos", "POSPage"),
            "Inventory": ("pages_qt.inventory", "InventoryPage"),
            "Accounting": ("pages_qt.accounting_old", "AccountingPage"),
            "Reports": ("pages_qt.reports", "ReportsPage"),
            "Settings": ("pages_qt.settings_hub", "SettingsHubPage"),
        }
        for route, (mod, cls) in mapping.items():
            selected_mod = mod
            try:
                module = __import__(mod, fromlist=[cls])
                page_cls = getattr(module, cls)
                w = page_cls(services=self.services)
            except Exception:
                # Fallbacks for specific routes
                if route == "POS":
                    try:
                        selected_mod = "pages_qt.pos_pyqt"
                        module = __import__(selected_mod, fromlist=[cls])
                        page_cls = getattr(module, cls)
                        w = page_cls(services=self.services)
                    except Exception:
                        w = MissingPage(route)
                else:
                    w = MissingPage(route)
            self._add_page(route, w)
            # record backing filename for tiles
            try:
                fname = f"{selected_mod.split('.')[-1]}.py"
                self.route_files[route] = fname
            except Exception:
                pass

        # If Home supports receiving file routes, pass them
        try:
            home_idx = self.route_to_index.get("Home")
            if home_idx is not None:
                home_w = self.stack.widget(home_idx)
                if hasattr(home_w, "set_file_routes") and callable(getattr(home_w, "set_file_routes")):
                    home_w.set_file_routes(self.route_files)
        except Exception:
            pass

    def goto(self, route: str):
        idx = self.route_to_index.get(route)
        if idx is None:
            return
        self.stack.setCurrentIndex(idx)
    
    def iter_pages(self):
        for route, idx in self.route_to_index.items():
            yield route, self.stack.widget(idx)


class AppShellQt(QMainWindow):
    def __init__(self, services=None, start_route: str = "Dashboard"):
        super().__init__()
        self.services = services
        self.setWindowTitle("GymPro")
        self.resize(1400, 900)
        center = QFrame(); center.setObjectName("AppRoot")
        center.setStyleSheet(f"QWidget#AppRoot {{ background-color:{PALETTE['bg']}; }}")
        self.setCentralWidget(center)

        root = QHBoxLayout(center); root.setContentsMargins(0,0,0,0)
        # Stack only (no sidebar)
        container = QFrame(); container.setStyleSheet(f"background-color:{PALETTE['surface']};")
        cv = QVBoxLayout(container); cv.setContentsMargins(8,8,8,8); cv.setSpacing(8)
        self.stack = QStackedWidget()
        self.router = RouterQt(self.stack, services=self.services)
        cv.addWidget(self.stack)

        root.addWidget(container, 1)

        # Navigation state & injection for pages
        self.current_route: Optional[str] = None
        self.history: list[str] = []
        # Inject navigation callbacks to pages that support it
        try:
            for route, widget in self.router.iter_pages():
                if hasattr(widget, "set_nav_callback") and callable(getattr(widget, "set_nav_callback")):
                    widget.set_nav_callback(self._navigate)
        except Exception:
            pass

        # Bind ESC to go back
        try:
            from PyQt6.QtGui import QShortcut, QKeySequence
            QShortcut(QKeySequence("Escape"), self, activated=self._go_back)
        except Exception:
            pass

        # Start on requested route
        self._navigate(start_route if start_route else "Home")

    def _navigate(self, route: str):
        if not route:
            return
        if self.current_route and self.current_route != route:
            self.history.append(self.current_route)
        try:
            self.router.goto(route)
            self.current_route = route
        except Exception:
            try:
                self.router.goto("Home")
                self.current_route = "Home"
            except Exception:
                pass

    def _go_back(self):
        if self.history:
            prev = self.history.pop()
            self.router.goto(prev)
            self.current_route = prev
