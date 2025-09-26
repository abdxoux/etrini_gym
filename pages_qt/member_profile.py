# pages_qt/member_profile.py
# GymPro — Member Profile (PyQt6 port). Overview, subscriptions, payments, attendance

from __future__ import annotations

import datetime as dt
from typing import Any, Dict, List, Optional

try:
    from router import PALETTE as SHARED_PALETTE  # type: ignore
except Exception:
    SHARED_PALETTE = None

PALETTE = SHARED_PALETTE or {
    "bg":       "#0f1218",
    "surface":  "#151a22",
    "card":     "#1b2130",
    "card2":    "#1e2636",
    "accent":   "#4f8cff",
    "muted":    "#8b93a7",
    "text":     "#e8ecf5",
    "ok":       "#22c55e",
    "warn":     "#f59e0b",
    "danger":   "#ef4444",
}

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
    QLabel,
    QGridLayout,
    QVBoxLayout,
    QHBoxLayout,
    QFrame,
    QPushButton,
    QLineEdit,
    QScrollArea,
)
from qfluentwidgets import setTheme, Theme, PrimaryPushButton, PushButton


def _label(text: str, *, color: str | None = None, size: int = 13, bold: bool = False) -> QLabel:
    lbl = QLabel(text)
    weight = 600 if bold else 400
    c = color or PALETTE["text"]
    lbl.setStyleSheet(f"color:{c}; font-family:'Segoe UI'; font-size:{size}px; font-weight:{weight};")
    return lbl


class SectionCard(QFrame):
    def __init__(self, title: str, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("SectionCard")
        self.setStyleSheet(f"QFrame#SectionCard {{ background-color: {PALETTE['card']}; border-radius: 16px; }}")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 14, 16, 12)
        lay.setSpacing(8)
        lay.addWidget(_label(title, bold=True, size=15))


class MemberProfilePage(QWidget):
    def __init__(self, member_id: Optional[int] = None, services: Optional[object] = None, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.services = services
        self.member_id = member_id or 1001

        self.setObjectName("MemberProfilePage")
        self.setStyleSheet(
            f"""
            QWidget#MemberProfilePage {{ background-color:{PALETTE['surface']}; }}
            QLabel {{ color:{PALETTE['text']}; }}
            QLineEdit {{ color:{PALETTE['text']}; background-color:{PALETTE['card2']}; border:1px solid {PALETTE['card2']}; border-radius:8px; padding:6px 8px; }}
            QPushButton[cssClass='primary'] {{ background-color:{PALETTE['accent']}; color:{PALETTE['text']}; border-radius:14px; height:30px; padding:4px 12px; }}
            QPushButton[cssClass='primary']:hover {{ background-color:#3e74d6; }}
            QPushButton[cssClass='secondary'] {{ background-color:#2a3550; color:{PALETTE['text']}; border-radius:14px; height:30px; padding:4px 12px; }}
            QPushButton[cssClass='secondary']:hover {{ background-color:#334066; }}
            """
        )

        root = QGridLayout(self); root.setContentsMargins(12,12,12,12); root.setHorizontalSpacing(8); root.setVerticalSpacing(8)
        root.setColumnStretch(0, 3); root.setColumnStretch(1, 2)
        root.setRowStretch(2, 1)

        # Header
        head = SectionCard("Member Profile")
        header = QFrame(); header.setStyleSheet(f"background-color:{PALETTE['card2']}; border-radius:12px;")
        hg = QGridLayout(header); hg.setContentsMargins(12,10,12,10)
        self.lbl_name = _label("—", bold=True, size=16)
        self.lbl_meta = _label("—", color=PALETTE["muted"])  
        btns = QFrame(); hb = QHBoxLayout(btns); hb.setContentsMargins(0,0,0,0);
        b_edit = PushButton("Edit"); b_edit.setProperty("cssClass","secondary"); b_edit.clicked.connect(self._edit)
        b_renew = PrimaryPushButton("Renew")
        hb.addWidget(b_edit); hb.addWidget(b_renew)
        hg.addWidget(self.lbl_name, 0, 0); hg.addWidget(self.lbl_meta, 1, 0); hg.addWidget(btns, 0, 1, 2, 1, alignment=Qt.AlignmentFlag.AlignRight)
        head.layout().addWidget(header)  # type: ignore
        root.addWidget(head, 0, 0, 1, 2)

        # Left column: Subscriptions
        left = SectionCard("Subscriptions")
        self.sub_scroll = QScrollArea(); self.sub_scroll.setWidgetResizable(True)
        self.sub_wrap = QWidget(); self.sub_vbox = QVBoxLayout(self.sub_wrap); self.sub_vbox.setContentsMargins(8,6,8,8); self.sub_vbox.setSpacing(6)
        self.sub_scroll.setWidget(self.sub_wrap)
        left.layout().addWidget(self.sub_scroll)  # type: ignore
        root.addWidget(left, 1, 0)

        # Right column: Payments & Attendance
        right = QFrame(); rg = QGridLayout(right); rg.setContentsMargins(0,0,0,0); rg.setVerticalSpacing(8)
        pay = SectionCard("Payments"); rg.addWidget(pay, 0, 0)
        self.pay_scroll = QScrollArea(); self.pay_scroll.setWidgetResizable(True)
        self.pay_wrap = QWidget(); self.pay_vbox = QVBoxLayout(self.pay_wrap); self.pay_vbox.setContentsMargins(8,6,8,8); self.pay_vbox.setSpacing(6)
        self.pay_scroll.setWidget(self.pay_wrap); pay.layout().addWidget(self.pay_scroll)  # type: ignore
        att = SectionCard("Attendance"); rg.addWidget(att, 1, 0)
        self.att_scroll = QScrollArea(); self.att_scroll.setWidgetResizable(True)
        self.att_wrap = QWidget(); self.att_vbox = QVBoxLayout(self.att_wrap); self.att_vbox.setContentsMargins(8,6,8,8); self.att_vbox.setSpacing(6)
        self.att_scroll.setWidget(self.att_wrap); att.layout().addWidget(self.att_scroll)  # type: ignore
        root.addWidget(right, 1, 1)

        self._load()

    def _load(self):
        m = self._fetch_member()
        self.lbl_name.setText(f"#{m.get('id','—')} — {m.get('name','—')}")
        self.lbl_meta.setText(f"{m.get('status','Active')} • {m.get('phone','')} • UID {m.get('uid','')} ")
        # subs
        for r in (m.get("subscriptions") or []):
            row = QFrame(); row.setStyleSheet(f"background-color:{PALETTE['card2']}; border-radius:10px;")
            g = QGridLayout(row); g.setContentsMargins(12,8,12,8)
            g.addWidget(_label(r.get('plan','—')), 0, 0)
            g.addWidget(_label(f"{r.get('start','—')} → {r.get('end','—')}", color=PALETTE['muted']), 0, 1)
            g.addWidget(_label(r.get('status','—')), 0, 2)
            self.sub_vbox.addWidget(row)
        self.sub_vbox.addStretch(1)
        # payments
        for p in (m.get("payments") or []):
            row = QFrame(); row.setStyleSheet(f"background-color:{PALETTE['card2']}; border-radius:10px;")
            g = QGridLayout(row); g.setContentsMargins(12,8,12,8)
            g.addWidget(_label(p.get('date','—')), 0, 0)
            g.addWidget(_label(p.get('method','—'), color=PALETTE['muted']), 0, 1)
            g.addWidget(_label(f"{int(p.get('amount',0)):,} DA"), 0, 2)
            self.pay_vbox.addWidget(row)
        self.pay_vbox.addStretch(1)
        # attendance
        for a in (m.get("attendance") or []):
            row = QFrame(); row.setStyleSheet(f"background-color:{PALETTE['card2']}; border-radius:10px;")
            g = QGridLayout(row); g.setContentsMargins(12,8,12,8)
            g.addWidget(_label(a.get('time','—')), 0, 0)
            g.addWidget(_label(a.get('status','—'), color=PALETTE['muted']), 0, 1)
            self.att_vbox.addWidget(row)
        self.att_vbox.addStretch(1)

    def _fetch_member(self) -> Dict[str, Any]:
        if self.services and hasattr(self.services, "member_profile"):
            try:
                d = self.services.member_profile(self.member_id)
                if d: return d
            except Exception:
                pass
        # demo
        today = dt.date.today()
        return {
            "id": self.member_id, "name": "Member 1001", "phone": "+213 6 12 34 56 78", "uid": "UID1001", "status": "Active",
            "subscriptions": [{"plan":"Monthly (30d/mo)", "start": str(today.replace(day=1)), "end": str(today.replace(day=1)+dt.timedelta(days=29)), "status":"Active"}],
            "payments": [{"date": str(today), "method": "Cash", "amount": 1200}],
            "attendance": [{"time": dt.datetime.now().strftime("%Y-%m-%d %H:%M"), "status": "check-in"}],
        }

    def _edit(self):
        print("Edit member", self.member_id)


if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    try:
        setTheme(Theme.DARK)
    except Exception:
        pass
    root = QWidget(); root.setObjectName("Root"); root.setStyleSheet(f"QWidget#Root {{ background-color: {PALETTE['bg']}; }}"); root.resize(1300, 860)
    page = MemberProfilePage(member_id=1001, services=None, parent=root)
    lay = QVBoxLayout(root); lay.setContentsMargins(0,0,0,0); lay.addWidget(page)
    root.show(); sys.exit(app.exec())
