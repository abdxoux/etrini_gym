# pages_qt/mark_attendance.py
# GymPro — Manual Attendance (PyQt6). Full-page manual marking with filters and list

from __future__ import annotations

from typing import Any, Dict, List, Optional
import random

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

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPixmap, QPainter, QColor
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
    QComboBox,
    QScrollArea,
    QSizePolicy,
    QMessageBox,
)
from qfluentwidgets import setTheme, Theme, LineEdit, ComboBox, PrimaryPushButton, PushButton


def _label(text: str, *, color: Optional[str] = None, size: int = 13, bold: bool = False) -> QLabel:
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
        lay.addWidget(_label(title, bold=True, size=15), alignment=Qt.AlignmentFlag.AlignLeft)


def _initials(name: str) -> str:
    parts = [p for p in name.split() if p]
    if not parts:
        return "?"
    return (parts[0][0] + (parts[1][0] if len(parts) > 1 else "")).upper()


class Avatar(QFrame):
    def __init__(self, name: str, picture: Optional[QPixmap] = None, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setFixedSize(36, 36)
        self.setStyleSheet(f"background-color:{PALETTE['card2']}; border-radius:8px;")
        if picture is None:
            # draw initials on colored rect
            self.lbl = _label(_initials(name), bold=True)
            self.lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            l = QVBoxLayout(self); l.setContentsMargins(0,0,0,0); l.addWidget(self.lbl)
        else:
            lab = QLabel(); lab.setPixmap(picture.scaled(36,36))
            l = QVBoxLayout(self); l.setContentsMargins(0,0,0,0); l.addWidget(lab)


class MemberRow(QFrame):
    def __init__(self, m: Dict[str, Any], on_mark, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.m = m; self.on_mark = on_mark
        self.setStyleSheet(f"background-color:{PALETTE['card2']}; border-radius:10px;")
        g = QGridLayout(self); g.setContentsMargins(12,8,12,8); g.setHorizontalSpacing(8)
        cols = (6, 14, 20, 16, 10, 12, 10, 10)
        for i, w in enumerate(cols): g.setColumnStretch(i, w)
        name = m.get("name","—")
        uid = m.get("uid","—")
        phone = m.get("phone","—")
        status = m.get("status","Active")
        self.days_per_month = int(m.get("days_per_month") or 0)
        self.remaining = int(m.get("granted_left") or 0)
        g.addWidget(Avatar(name), 0, 0)
        g.addWidget(_label(uid, color=PALETTE["muted"]), 0, 1)
        g.addWidget(_label(name), 0, 2)
        g.addWidget(_label(phone, color=PALETTE["muted"]), 0, 3)
        self.lbl_dpm = _label(str(self.days_per_month or "—"), color=PALETTE["muted"])
        g.addWidget(self.lbl_dpm, 0, 4)
        self.lbl_left = _label(str(self.remaining), color=PALETTE["text"])
        g.addWidget(self.lbl_left, 0, 5)
        g.addWidget(_label(status, color=PALETTE["ok"] if status.lower()=="active" else PALETTE["warn"]), 0, 6)
        btn = PrimaryPushButton("Mark Attendance"); btn.setMinimumHeight(28)
        btn.clicked.connect(lambda: self.on_mark(self))
        g.addWidget(btn, 0, 7, alignment=Qt.AlignmentFlag.AlignRight)

    def set_remaining(self, value: int):
        self.remaining = max(0, int(value))
        self.lbl_left.setText(str(self.remaining))


class MarkAttendancePage(QWidget):
    def __init__(self, services: Optional[object] = None, on_back=None, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.services = services
        self.on_back = on_back or (lambda: None)
        self._all: List[Dict[str, Any]] = []
        self._timer: Optional[QTimer] = None

        self.setObjectName("MarkAttendancePage")
        self.setStyleSheet(
            f"""
            QWidget#MarkAttendancePage {{ background-color:{PALETTE['surface']}; }}
            QLabel {{ color:{PALETTE['text']}; }}
            QLineEdit, QComboBox {{ color:{PALETTE['text']}; background-color:{PALETTE['card2']}; border:1px solid {PALETTE['card2']}; border-radius:8px; padding:6px 8px; }}
            QPushButton[cssClass='primary'] {{ background-color:{PALETTE['accent']}; color:{PALETTE['text']}; border-radius:14px; height:30px; padding:4px 12px; }}
            QPushButton[cssClass='primary']:hover {{ background-color:#3e74d6; }}
            QPushButton[cssClass='secondary'] {{ background-color:#2a3550; color:{PALETTE['text']}; border-radius:14px; height:30px; padding:4px 12px; }}
            QPushButton[cssClass='secondary']:hover {{ background-color:#334066; }}
            """
        )

        root = QGridLayout(self); root.setContentsMargins(12,12,12,12); root.setVerticalSpacing(8); root.setHorizontalSpacing(8)
        root.setRowStretch(3, 1)

        # Header
        head = QFrame(); hg = QGridLayout(head); hg.setContentsMargins(0,0,0,0)
        btn_back = PushButton("◀ Back"); btn_back.setProperty("cssClass","secondary"); btn_back.clicked.connect(self.on_back)
        title = _label("Mark Attendance Manually", size=16, bold=True)
        hg.addWidget(btn_back, 0, 0, alignment=Qt.AlignmentFlag.AlignLeft)
        hg.addWidget(title, 0, 1, alignment=Qt.AlignmentFlag.AlignCenter)
        root.addWidget(head, 0, 0)

        # Filters
        filt = QFrame(); fg = QGridLayout(filt); fg.setContentsMargins(12,10,12,10); fg.setHorizontalSpacing(8)
        fg.addWidget(_label("Name", color=PALETTE['muted']), 0, 0)
        self.ent_name = LineEdit(); self.ent_name.setPlaceholderText("Contains…"); self.ent_name.textChanged.connect(self._debounced_refresh)
        fg.addWidget(self.ent_name, 0, 1)
        fg.addWidget(_label("UID", color=PALETTE['muted']), 0, 2)
        self.ent_uid = LineEdit(); self.ent_uid.setPlaceholderText("Starts with…"); self.ent_uid.textChanged.connect(self._debounced_refresh)
        fg.addWidget(self.ent_uid, 0, 3)
        fg.addWidget(_label("Status", color=PALETTE['muted']), 0, 4)
        self.cmb_status = ComboBox(); self.cmb_status.addItems(["Any", "Active", "Inactive"]) ; self.cmb_status.currentIndexChanged.connect(self._debounced_refresh)
        fg.addWidget(self.cmb_status, 0, 5)
        root.addWidget(filt, 1, 0)

        # Header row
        hdr = QFrame(); hdr.setStyleSheet(f"background-color:{PALETTE['card2']}; border-radius:12px;")
        hg2 = QGridLayout(hdr); hg2.setContentsMargins(10,8,10,8)
        labels = ("Avatar", "UID", "Name", "Phone", "Days/Month", "Granted Left", "Status", "Actions")
        weights = (6, 14, 20, 16, 10, 12, 10, 10)
        for i, (txt, w) in enumerate(zip(labels, weights)):
            hg2.addWidget(_label(txt, color=PALETTE["muted"]), 0, i); hg2.setColumnStretch(i, w)
        root.addWidget(hdr, 2, 0)

        # List
        self.scroll = QScrollArea(); self.scroll.setWidgetResizable(True)
        self.wrap = QWidget(); self.vbox = QVBoxLayout(self.wrap); self.vbox.setContentsMargins(8,6,8,8); self.vbox.setSpacing(6)
        self.scroll.setWidget(self.wrap)
        root.addWidget(self.scroll, 3, 0)

        self._load()

    # ----- data -----
    def _debounced_refresh(self, *args):
        if not hasattr(self, "_timer") or self._timer is None:
            self._timer = QTimer(self)
            self._timer.setSingleShot(True)
            self._timer.timeout.connect(self._refresh)
        self._timer.start(250)

    def _load(self):
        self._all = self._fetch_members()
        self._refresh()

    def _fetch_members(self) -> List[Dict[str, Any]]:
        if self.services and hasattr(self.services, "members") and hasattr(self.services.members, "list"):
            try:
                rows = list(self.services.members.list()) or []
                out: List[Dict[str, Any]] = []
                for r in rows:
                    out.append({
                        "id": r.get("id"),
                        "uid": r.get("uid") or r.get("card_uid") or f"UID{random.randint(10000,99999)}",
                        "name": r.get("name") or r.get("full_name") or "—",
                        "phone": r.get("phone") or r.get("mobile") or "",
                        "status": r.get("status") or ("Active" if r.get("active", True) else "Inactive"),
                        "avatar": None,
                        "days_per_month": r.get("days_per_month") or r.get("plan_days_per_month") or 30,
                        "granted_left": self._remaining_accesses(r.get("id"), r.get("uid") or r.get("card_uid")),
                    })
                return out
            except Exception:
                pass
        # fallback demo
        names = ["Nadia Karim","Hind Bel","Amine Mok","Karim Ali","Sara Lou"]
        demo: List[Dict[str, Any]] = []
        for i in range(24):
            demo.append({
                "id": 100+i,
                "uid": f"UID{random.randint(10000,99999)}",
                "name": random.choice(names),
                "phone": f"055{random.randint(1000000,9999999)}",
                "status": random.choice(["Active","Inactive"]),
                "avatar": None,
                "days_per_month": random.choice([16, 24, 30]),
                "granted_left": 2,
            })
        return demo

    def _apply_filters(self, rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        qn = (self.ent_name.text() or "").strip().lower()
        qu = (self.ent_uid.text() or "").strip().lower()
        st = self.cmb_status.currentText()
        out = []
        for r in rows:
            name = (r.get("name","") or "").lower()
            uid = (r.get("uid","") or "").lower()
            status = (r.get("status","Active") or "").lower()
            if qn and qn not in name: continue
            if qu and not uid.startswith(qu): continue
            if st != "Any" and status != st.lower(): continue
            out.append(r)
        # stable sort by name then uid
        out.sort(key=lambda x: ((x.get("name") or "").lower(), (x.get("uid") or "")))
        return out

    def _refresh(self):
        while self.vbox.count():
            it = self.vbox.takeAt(0); w = it.widget();
            if w: w.setParent(None)
        items = self._apply_filters(self._all)
        if not items:
            self.vbox.addWidget(_label("No members found", color=PALETTE["muted"]))
        else:
            for m in items:
                self.vbox.addWidget(MemberRow(m, on_mark=self._mark))
        self.vbox.addStretch(1)

    def _mark(self, row: MemberRow):
        # Try to mark attendance via services, fallback to print and update UI
        ok = False
        try:
            if self.services and hasattr(self.services, "attendance") and hasattr(self.services.attendance, "mark"):
                self.services.attendance.mark(row.m.get("id"), row.m.get("uid"))
                ok = True
        except Exception:
            ok = False
        # demo success if no service
        if not ok and not (self.services and hasattr(self.services, "attendance")):
            ok = True
        if ok:
            # decrement remaining (two accesses per 12h window demo)
            row.set_remaining(max(0, row.remaining - 1))
            QMessageBox.information(self, "Attendance", "Attendance marked successfully")
        else:
            QMessageBox.warning(self, "Attendance", "Failed to mark attendance")

    def _remaining_accesses(self, member_id: Any, uid: Optional[str]) -> int:
        # Attempt to query remaining accesses; fallback to 2 per 12h window
        try:
            if self.services and hasattr(self.services, "attendance") and hasattr(self.services.attendance, "remaining"):
                return int(self.services.attendance.remaining(member_id, uid))
        except Exception:
            pass
        return 2


if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    try:
        setTheme(Theme.DARK)
    except Exception:
        pass
    root = QWidget(); root.setObjectName("Root"); root.setStyleSheet(f"QWidget#Root {{ background-color: {PALETTE['bg']}; }}"); root.resize(1200, 800)
    page = MarkAttendancePage(services=None, parent=root)
    lay = QVBoxLayout(root); lay.setContentsMargins(0,0,0,0); lay.addWidget(page)
    root.show(); sys.exit(app.exec())
