# pages_qt/attendance.py
# GymPro — Attendance (PyQt6 port). Scan UID & History

from __future__ import annotations

import datetime as dt
import random
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
    QLineEdit,
    QScrollArea,
)
from qfluentwidgets import setTheme, Theme, LineEdit, PrimaryPushButton


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
        lay.addWidget(_label(title, bold=True, size=15), alignment=Qt.AlignmentFlag.AlignLeft)


class Pill(QFrame):
    def __init__(self, text: str, kind: str, parent: Optional[QWidget] = None):
        super().__init__(parent)
        colors = {
            "allowed": ("#1e3325", PALETTE["ok"]),
            "denied": ("#3a1418", PALETTE["danger"]),
            "muted": ("#2b3344", PALETTE["muted"]),
        }
        bg, fg = colors.get(kind, colors["muted"])  # type: ignore[index]
        self.setStyleSheet(f"background-color:{bg}; border-radius:999px;")
        lay = QHBoxLayout(self)
        lay.setContentsMargins(10, 4, 10, 4)
        lay.addWidget(_label(text, color=fg, size=12))


class Toast(QFrame):
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setStyleSheet("background: transparent;")
        self.lbl = _label("", color=PALETTE["text"])
        lay = QHBoxLayout(self); lay.setContentsMargins(12, 6, 12, 6)
        lay.addWidget(self.lbl)

    def show(self, text: str, kind: str = "ok"):
        colors = {"ok": PALETTE["ok"], "warn": PALETTE["warn"], "danger": PALETTE["danger"]}
        self.lbl.setText(text)
        self.lbl.setStyleSheet(f"color:{colors.get(kind, PALETTE['ok'])}; font-family:'Segoe UI'; font-size:13px;")


class CheckinRow(QFrame):
    def __init__(self, rec: Dict[str, Any], on_open_member=None, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setStyleSheet(f"background-color:{PALETTE['card']}; border-radius:10px;")
        grid = QGridLayout(self)
        grid.setContentsMargins(12, 8, 12, 8)
        grid.setHorizontalSpacing(8)
        weights = (14, 20, 30, 12, 8)
        for i, w in enumerate(weights):
            grid.setColumnStretch(i, w)

        t = rec.get("time", "—")
        uid = rec.get("uid", "—")
        name = rec.get("name", "—")
        status = (rec.get("status") or "allowed").lower()
        member_id = rec.get("member_id")

        grid.addWidget(_label(t), 0, 0)
        grid.addWidget(_label(uid, color=PALETTE["muted"]), 0, 1)
        grid.addWidget(_label(name), 0, 2)
        grid.addWidget(Pill(status.capitalize(), status), 0, 3)

        if on_open_member:
            btn = PrimaryPushButton("Open")
            btn.setFixedHeight(32)
            # Always provide a payload; include uid/name even if member_id is None
            btn.clicked.connect(lambda: on_open_member({
                "id": member_id,
                "uid": uid,
                "name": name
            }))
            grid.addWidget(btn, 0, 4, alignment=Qt.AlignmentFlag.AlignRight)


class AttendancePage(QWidget):
    def __init__(self, services: Optional[object] = None, on_open_member=None, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.services = services
        self.on_open_member = on_open_member or (lambda payload: print("Open member", payload))
        self._rows: List[CheckinRow] = []
        self._stats = {"total": 0, "allowed": 0, "denied": 0}

        self.setObjectName("AttendancePage")
        self.setStyleSheet(
            f"""
            QWidget#AttendancePage {{ background-color: {PALETTE['surface']}; }}
            QLabel {{ color: {PALETTE['text']}; }}
            QLineEdit, QComboBox {{ color:{PALETTE['text']}; background-color:{PALETTE['card2']}; border:1px solid {PALETTE['card2']}; border-radius:8px; padding:6px 8px; }}
            QComboBox::drop-down {{ width: 24px; }}
            QComboBox QAbstractItemView {{ background: {PALETTE['card2']}; color: {PALETTE['text']}; selection-background-color: {PALETTE['accent']}; }}
            QPushButton[cssClass="primary"] {{ background-color:{PALETTE['accent']}; color:{PALETTE['text']}; border-radius:14px; height:32px; padding:4px 12px; }}
            QPushButton[cssClass="primary"]:hover {{ background-color:#3e74d6; }}
            QPushButton[cssClass="secondary"] {{ background-color:#2a3550; color:{PALETTE['text']}; border-radius:14px; height:32px; padding:4px 12px; }}
            QPushButton[cssClass="secondary"]:hover {{ background-color:#334066; }}
            QPushButton[cssClass="secondary"]:pressed {{ background-color:#26314d; }}
            """
        )

        root = QGridLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setHorizontalSpacing(8)
        root.setVerticalSpacing(8)
        root.setColumnStretch(0, 1)
        root.setRowStretch(4, 1)

        root.addWidget(SectionCard("Attendance — Scan UID & History"), 0, 0)

        # search / scan bar
        scan = QFrame(); scan.setStyleSheet(f"background-color:{PALETTE['card']}; border-radius:16px;")
        sgrid = QGridLayout(scan); sgrid.setContentsMargins(12, 12, 12, 12); sgrid.setHorizontalSpacing(8)
        for i in range(10): sgrid.setColumnStretch(i, 1)
        sgrid.addWidget(_label("Search", color=PALETTE["muted"]), 0, 0)
        self.ent_uid = LineEdit(); self.ent_uid.setPlaceholderText("Search by UID or name…")
        self.ent_uid.textChanged.connect(self._filter_history)
        self.ent_uid.returnPressed.connect(self._scan)
        sgrid.addWidget(self.ent_uid, 0, 1, 1, 5)
        self.btn_manual = PrimaryPushButton("Mark Attendance Manually"); self.btn_manual.clicked.connect(self._open_manual_attendance)
        sgrid.addWidget(self.btn_manual, 0, 6)
        root.addWidget(scan, 1, 0)

        # stats strip
        stats = QFrame(); stats.setStyleSheet(f"background-color:{PALETTE['card']}; border-radius:16px;")
        stg = QGridLayout(stats); stg.setContentsMargins(12, 10, 12, 10)
        for i in range(6): stg.setColumnStretch(i, 1)
        self.lbl_today = _label("Today: 0 check-ins", color=PALETTE["muted"]) ; stg.addWidget(self.lbl_today, 0, 0)
        self.lbl_allowed = _label("Allowed: 0", color=PALETTE["ok"]) ; stg.addWidget(self.lbl_allowed, 0, 1)
        self.lbl_denied = _label("Denied: 0", color=PALETTE["danger"]) ; stg.addWidget(self.lbl_denied, 0, 2)
        self.toast = Toast(); stg.addWidget(self.toast, 0, 5, alignment=Qt.AlignmentFlag.AlignRight)
        root.addWidget(stats, 2, 0)

        # header
        header = SectionCard("Recent Check-ins")
        hwrap = QFrame(); hwrap.setStyleSheet(f"background-color:{PALETTE['card2']}; border-radius:12px;")
        hg = QGridLayout(hwrap); hg.setContentsMargins(10, 8, 10, 8)
        labels = ("Time", "UID", "Member", "Status", "")
        weights = (14, 20, 30, 12, 8)
        for i, (txt, w) in enumerate(zip(labels, weights)):
            hg.addWidget(_label(txt, color=PALETTE["muted"]), 0, i); hg.setColumnStretch(i, w)
        header.layout().addWidget(hwrap)  # type: ignore
        root.addWidget(header, 3, 0)

        # list
        self.scroll = QScrollArea(); self.scroll.setWidgetResizable(True)
        self.list_container = QWidget(); self.list_vbox = QVBoxLayout(self.list_container)
        self.list_vbox.setContentsMargins(10, 8, 10, 8); self.list_vbox.setSpacing(6)
        self.scroll.setWidget(self.list_container)
        root.addWidget(self.scroll, 4, 0)

        # initial history
        self._load_history()
        self.ent_uid.setFocus()

    def _update_stats_labels(self):
        self.lbl_today.setText(f"Today: {self._stats['total']} check-ins")
        self.lbl_allowed.setText(f"Allowed: {self._stats['allowed']}")
        self.lbl_denied.setText(f"Denied: {self._stats['denied']}")

    def _add_history_row(self, rec: Dict[str, Any], prepend: bool = True):
        row = CheckinRow(rec, on_open_member=self.on_open_member)
        if prepend and self._rows:
            self.list_vbox.insertWidget(0, row)
            self._rows.insert(0, row)
        else:
            self.list_vbox.addWidget(row)
            self._rows.append(row)

    def _scan(self):
        uid = (self.ent_uid.text() or "").strip()
        if not uid:
            self.toast.show("Empty UID.", "warn"); return
        rec = None
        if self.services and hasattr(self.services, "scan_uid"):
            try:
                rec = self.services.scan_uid(uid) or None
            except Exception:
                rec = None
        if not rec:
            now = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            allowed = random.random() > 0.15
            name = random.choice(["Nadia K.","Hind B.","Amine M.","Karim A.","Sara L."])
            rec = {"time": now, "uid": uid, "name": name, "status": "allowed" if allowed else "denied", "member_id": random.choice([101,202,303,None])}
        self._stats["total"] += 1
        if (rec.get("status") or "allowed").lower() == "allowed":
            self._stats["allowed"] += 1; self.toast.show(f"Allowed — {rec.get('name','')}", "ok")
        else:
            self._stats["denied"] += 1; self.toast.show(f"Denied — {rec.get('name','')}", "danger")
        self._update_stats_labels()
        self._add_history_row(rec, prepend=True)
        self.ent_uid.setText(""); self.ent_uid.setFocus()

    def _load_history(self):
        # clear
        while self.list_vbox.count():
            item = self.list_vbox.takeAt(0)
            w = item.widget()
            if w: w.setParent(None)
        self._rows.clear(); self._stats = {"total": 0, "allowed": 0, "denied": 0}

        data = None
        if self.services and hasattr(self.services, "recent_checkins"):
            try:
                data = self.services.recent_checkins(limit=50) or []
            except Exception:
                data = None
        if not data:
            data = []
            now = dt.datetime.now()
            for i in range(15):
                t = (now - dt.timedelta(minutes=4*i)).strftime("%Y-%m-%d %H:%M:%S")
                allowed = random.random() > 0.2
                data.append({
                    "time": t,
                    "uid": f"UID{random.randint(10000,99999)}",
                    "name": random.choice(["Nadia K.","Hind B.","Amine M.","Karim A.","Sara L."]),
                    "status": "allowed" if allowed else "denied",
                    "member_id": random.choice([101,202,303,None]),
                })
        for rec in data:
            self._add_history_row(rec, prepend=False)
            self._stats["total"] += 1
            if (rec.get("status") or "allowed").lower() == "allowed":
                self._stats["allowed"] += 1
            else:
                self._stats["denied"] += 1
        self._update_stats_labels()

    def _filter_history(self):
        q = (self.ent_uid.text() or "").strip().lower()
        for row in self._rows:
            # extract labels from grid: time (0), uid (1), name (2)
            uid_lbl: QLabel = row.layout().itemAtPosition(0,1).widget()  # type: ignore
            name_lbl: QLabel = row.layout().itemAtPosition(0,2).widget()  # type: ignore
            match = True
            if q:
                uid_txt = uid_lbl.text().lower() if uid_lbl else ""
                name_txt = name_lbl.text().lower() if name_lbl else ""
                match = (q in uid_txt) or (q in name_txt)
            row.setVisible(bool(match))

    def _open_manual_attendance(self):
        try:
            from pages_qt.mark_attendance import MarkAttendancePage  # type: ignore
        except Exception:
            return
        # Swap to manual attendance full page using existing layout
        lay = self.layout()
        while lay.count():
            it = lay.takeAt(0); w = it.widget();
            if w: w.setParent(None)
        page = MarkAttendancePage(services=self.services, on_back=self._rebuild_main, parent=self)
        lay.addWidget(page)

    def _rebuild_main(self):
        # Recreate the page to restore widgets
        parent = self.parent()
        services = self.services
        self.deleteLater()
        repl = AttendancePage(services=services, on_open_member=self.on_open_member, parent=parent)
        parent.layout().addWidget(repl)


if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    try:
        setTheme(Theme.DARK)
    except Exception:
        pass
    root = QWidget(); root.setObjectName("Root"); root.setStyleSheet(f"QWidget#Root {{ background-color: {PALETTE['bg']}; }}")
    root.resize(1200, 720)
    page = AttendancePage(services=None, parent=root)
    lay = QVBoxLayout(root); lay.setContentsMargins(0,0,0,0); lay.addWidget(page)
    root.show(); sys.exit(app.exec())
