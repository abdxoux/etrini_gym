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
    QWidget, QVBoxLayout, QGridLayout, QFrame, QLabel, QPushButton, QLineEdit, QSpinBox, QDoubleSpinBox, QCheckBox
)
from qfluentwidgets import PrimaryPushButton


def _label(text: str, *, color: Optional[str] = None, size: int = 13, bold: bool = False) -> QLabel:
    lbl = QLabel(text)
    weight = 600 if bold else 400
    c = color or PALETTE["text"]
    lbl.setStyleSheet(f"color:{c}; font-family:'Segoe UI'; font-size:{size}px; font-weight:{weight};")
    return lbl


class SettingsDebtPolicyPage(QWidget):
    def __init__(self, services: Optional[object] = None, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.services = services
        self.setObjectName("SettingsDebtPolicyPage")
        self.setStyleSheet(
            f"""
            QWidget#SettingsDebtPolicyPage {{ background-color:{PALETTE['surface']}; }}
            QLabel {{ color:{PALETTE['text']}; }}
            QLineEdit, QSpinBox, QDoubleSpinBox {{ color:{PALETTE['text']}; background-color:{PALETTE['card2']}; border:1px solid {PALETTE['card2']}; border-radius:8px; padding:6px 8px; }}
            QPushButton[cssClass='primary'] {{ background-color:{PALETTE['accent']}; color:{PALETTE['text']}; border-radius:14px; height:30px; padding:4px 12px; }}
            """
        )

        root = QGridLayout(self); root.setContentsMargins(12,12,12,12); root.setHorizontalSpacing(8); root.setVerticalSpacing(8)
        root.addWidget(_label("Debt Policy", size=15, bold=True), 0, 0)

        card = QFrame(); card.setStyleSheet(f"background-color:{PALETTE['card']}; border-radius:16px;")
        g = QGridLayout(card); g.setContentsMargins(12,10,12,10); g.setHorizontalSpacing(8); g.setVerticalSpacing(8)

        g.addWidget(_label("Allow negative balance", color=PALETTE['muted']), 0, 0)
        self.chk_allow = QCheckBox(); self.chk_allow.setChecked(True)
        g.addWidget(self.chk_allow, 0, 1)

        g.addWidget(_label("Max debt (DA)", color=PALETTE['muted']), 1, 0)
        self.max_debt = QDoubleSpinBox(); self.max_debt.setRange(0, 1_000_000); self.max_debt.setValue(5000.0); self.max_debt.setDecimals(2)
        g.addWidget(self.max_debt, 1, 1)

        g.addWidget(_label("Grace days", color=PALETTE['muted']), 2, 0)
        self.grace_days = QSpinBox(); self.grace_days.setRange(0, 90); self.grace_days.setValue(7)
        g.addWidget(self.grace_days, 2, 1)

        self.btn_save = PrimaryPushButton("Save Changes")
        g.addWidget(self.btn_save, 3, 1)

        root.addWidget(card, 1, 0)
