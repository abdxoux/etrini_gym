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
    QWidget, QVBoxLayout, QGridLayout, QFrame, QLabel, QPushButton, QLineEdit, QCheckBox, QComboBox
)


def _label(text: str, *, color: Optional[str] = None, size: int = 13, bold: bool = False) -> QLabel:
    lbl = QLabel(text)
    weight = 600 if bold else 400
    c = color or PALETTE["text"]
    lbl.setStyleSheet(f"color:{c}; font-family:'Segoe UI'; font-size:{size}px; font-weight:{weight};")
    return lbl


class SettingsGatePage(QWidget):
    def __init__(self, services: Optional[object] = None, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.services = services
        self.setObjectName("SettingsGatePage")
        self.setStyleSheet(
            f"""
            QWidget#SettingsGatePage {{ background-color:{PALETTE['surface']}; }}
            QLabel {{ color:{PALETTE['text']}; }}
            QLineEdit, QComboBox {{ color:{PALETTE['text']}; background-color:{PALETTE['card2']}; border:1px solid {PALETTE['card2']}; border-radius:8px; padding:6px 8px; }}
            QPushButton[cssClass='primary'] {{ background-color:{PALETTE['accent']}; color:{PALETTE['text']}; border-radius:14px; height:30px; padding:4px 12px; }}
            """
        )

        root = QGridLayout(self); root.setContentsMargins(12,12,12,12); root.setHorizontalSpacing(8); root.setVerticalSpacing(8)
        root.addWidget(_label("Gate Settings", size=15, bold=True), 0, 0)

        card = QFrame(); card.setStyleSheet(f"background-color:{PALETTE['card']}; border-radius:16px;")
        g = QGridLayout(card); g.setContentsMargins(12,10,12,10); g.setHorizontalSpacing(8); g.setVerticalSpacing(8)

        g.addWidget(_label("Serial Port", color=PALETTE['muted']), 0, 0)
        self.cmb_port = QComboBox(); self.cmb_port.addItems(["COM1","COM2","COM3","COM4"]) ; g.addWidget(self.cmb_port, 0, 1)

        g.addWidget(_label("Baud Rate", color=PALETTE['muted']), 1, 0)
        self.cmb_baud = QComboBox(); self.cmb_baud.addItems(["9600","19200","38400","57600","115200"]) ; self.cmb_baud.setCurrentText("115200"); g.addWidget(self.cmb_baud, 1, 1)

        g.addWidget(_label("Auto Open on Start", color=PALETTE['muted']), 2, 0)
        self.chk_auto = QCheckBox(); self.chk_auto.setChecked(True); g.addWidget(self.chk_auto, 2, 1)

        self.btn_save = QPushButton("Save"); self.btn_save.setProperty("cssClass","primary"); g.addWidget(self.btn_save, 3, 1)

        root.addWidget(card, 1, 0)
