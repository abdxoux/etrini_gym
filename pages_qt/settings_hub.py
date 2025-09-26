from __future__ import annotations

from typing import Optional

try:
    from router_qt import PALETTE  # shared palette
except Exception:
    PALETTE = {
        "bg": "#0f1218", "surface": "#151a22", "card": "#1b2130", "card2": "#1e2636",
        "accent": "#4f8cff", "muted": "#8b93a7", "text": "#e8ecf5",
    }

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QGridLayout, QFrame, QLabel, QPushButton, QStackedWidget, QHBoxLayout
)


def _label(text: str, *, color: Optional[str] = None, size: int = 13, bold: bool = False) -> QLabel:
    lbl = QLabel(text)
    weight = 600 if bold else 400
    c = color or PALETTE["text"]
    lbl.setStyleSheet(f"color:{c}; font-family:'Segoe UI'; font-size:{size}px; font-weight:{weight};")
    return lbl


class SegmentedTabs(QFrame):
    def __init__(self, values: list[str], on_change, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setStyleSheet("background: transparent;")
        self.h = QHBoxLayout(self); self.h.setContentsMargins(0,0,0,0); self.h.setSpacing(6)
        self.btns: list[QPushButton] = []
        for v in values:
            b = QPushButton(v); b.setCheckable(True); b.setProperty("seg","tab")
            b.clicked.connect(lambda _, vv=v: on_change(vv))
            self.btns.append(b); self.h.addWidget(b)
        # default select first
        if self.btns:
            self.btns[0].setChecked(True)


class SettingsHubPage(QWidget):
    def __init__(self, services: Optional[object] = None, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.services = services
        self.setObjectName("SettingsHubPage")
        self.setStyleSheet(
            f"""
            QWidget#SettingsHubPage {{ background-color:{PALETTE['surface']}; }}
            QLabel {{ color:{PALETTE['text']}; }}
            QPushButton[cssClass='primary'] {{ background-color:{PALETTE['accent']}; color:{PALETTE['text']}; border-radius:14px; height:30px; padding:4px 12px; }}
            QPushButton[cssClass='secondary'] {{ background-color:#2a3550; color:{PALETTE['text']}; border-radius:14px; height:30px; padding:4px 12px; }}
            QPushButton[cssClass='secondary']:hover {{ background-color:#334066; }}
            QPushButton[cssClass='secondary']:pressed {{ background-color:#26314d; }}
            QPushButton[seg='tab'] {{ background-color:#2b3344; color:{PALETTE['text']}; border:1px solid #2b3344; padding:4px 12px; border-radius:14px; }}
            QPushButton[seg='tab']:checked {{ background-color:{PALETTE['accent']}; border-color:{PALETTE['accent']}; }}
            """
        )

        root = QGridLayout(self); root.setContentsMargins(12,12,12,12); root.setVerticalSpacing(8)
        root.addWidget(_label("Settings", size=16, bold=True), 0, 0)

        # Tabs
        tabs = SegmentedTabs(["Roles","Debt Policy","Gate","Language","Equipment"], self._switch)
        root.addWidget(tabs, 1, 0)

        # Content card
        wrap = QFrame(); wrap.setStyleSheet(f"background-color:{PALETTE['card']}; border-radius:16px;")
        wg = QVBoxLayout(wrap); wg.setContentsMargins(12,10,12,10); wg.setSpacing(8)
        self.stack = QStackedWidget()
        wg.addWidget(self.stack)
        root.addWidget(wrap, 2, 0)

        # Build pages
        self._pages: dict[str, QWidget] = {}
        self._add_page("Roles", "pages_qt.settings_roles", "SettingsRolesPage")
        self._add_page("Debt Policy", "pages_qt.settings_debt_policy", "SettingsDebtPolicyPage")
        self._add_page("Gate", "pages_qt.settings_gate", "SettingsGatePage")
        self._add_page("Language", "pages_qt.settings_language", "SettingsLanguagePage")
        self._add_page("Equipment", "pages_qt.settings_equipment", "SettingsEquipmentPage")
        self.stack.setCurrentIndex(1)  # default Debt Policy

    def _add_page(self, key: str, mod: str, cls: str):
        try:
            module = __import__(mod, fromlist=[cls])
            page_cls = getattr(module, cls)
            w = page_cls(services=self.services)
        except Exception:
            w = self._placeholder(key)
        self._pages[key] = w
        self.stack.addWidget(w)

    def _placeholder(self, title: str) -> QWidget:
        box = QFrame(); box.setStyleSheet(f"background-color:{PALETTE['card2']}; border-radius:12px;")
        g = QVBoxLayout(box); g.setContentsMargins(16,14,16,14)
        g.addWidget(_label(f"{title} (not implemented)", bold=True))
        return box

    def _switch(self, name: str):
        mapping = ["Roles","Debt Policy","Gate","Language","Equipment"]
        idx = mapping.index(name) if name in mapping else 0
        self.stack.setCurrentIndex(idx)
