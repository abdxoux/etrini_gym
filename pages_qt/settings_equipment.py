from __future__ import annotations

from typing import Optional

try:
    from router_qt import PALETTE
except Exception:
    PALETTE = {
        "bg": "#0f1218", "surface": "#151a22", "card": "#1b2130", "card2": "#1e2636",
        "accent": "#4f8cff", "muted": "#8b93a7", "text": "#e8ecf5",
    }

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QGridLayout, QFrame, QLabel, QPushButton, QLineEdit, QListWidget, QListWidgetItem
)


def _label(text: str, *, color: Optional[str] = None, size: int = 13, bold: bool = False) -> QLabel:
    lbl = QLabel(text)
    weight = 600 if bold else 400
    c = color or PALETTE["text"]
    lbl.setStyleSheet(f"color:{c}; font-family:'Segoe UI'; font-size:{size}px; font-weight:{weight};")
    return lbl


class SettingsEquipmentPage(QWidget):
    def __init__(self, services: Optional[object] = None, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.services = services
        self.setObjectName("SettingsEquipmentPage")
        self.setStyleSheet(
            f"""
            QWidget#SettingsEquipmentPage {{ background-color:{PALETTE['surface']}; }}
            QLabel {{ color:{PALETTE['text']}; }}
            QLineEdit {{ color:{PALETTE['text']}; background-color:{PALETTE['card2']}; border:1px solid {PALETTE['card2']}; border-radius:8px; padding:6px 8px; }}
            QPushButton[cssClass='primary'] {{ background-color:{PALETTE['accent']}; color:{PALETTE['text']}; border-radius:14px; height:30px; padding:4px 12px; }}
            """
        )

        root = QGridLayout(self); root.setContentsMargins(12,12,12,12); root.setHorizontalSpacing(8); root.setVerticalSpacing(8)
        root.addWidget(_label("Equipment", size=15, bold=True), 0, 0)

        card = QFrame(); card.setStyleSheet(f"background-color:{PALETTE['card']}; border-radius:16px;")
        g = QGridLayout(card); g.setContentsMargins(12,10,12,10); g.setHorizontalSpacing(8); g.setVerticalSpacing(8)

        g.addWidget(_label("Search", color=PALETTE['muted']), 0, 0)
        self.ent_q = QLineEdit(); self.ent_q.setPlaceholderText("Search equipment…"); g.addWidget(self.ent_q, 0, 1)

        self.list = QListWidget(); self.list.setStyleSheet(f"QListWidget {{ background:{PALETTE['card2']}; color:{PALETTE['text']}; border:none; border-radius:8px; }}")
        for name in ["Treadmill","Bench Press","Dumbbells","Rowing Machine","Elliptical"]:
            self.list.addItem(QListWidgetItem(name))
        g.addWidget(self.list, 1, 0, 1, 2)

        self.btn_add = QPushButton("Add Equipment"); self.btn_add.setProperty("cssClass","primary")
        g.addWidget(self.btn_add, 2, 1)

        root.addWidget(card, 1, 0)
