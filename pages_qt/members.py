# pages_qt/members.py
# GymPro — MembersPage (PyQt6 port preserving UI identity, responsive layout)
# Requires: PyQt6 (pip install PyQt6)

from __future__ import annotations

import datetime as dt
import random
import threading
from typing import Any, Dict, List, Optional, Callable

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

from PyQt6.QtCore import Qt, QTimer, QSize, pyqtSignal
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
)
from qfluentwidgets import setTheme, Theme, LineEdit, ComboBox, PrimaryPushButton, PushButton


def _label(text: str, *, color: str | None = None, bold: bool = False, size: int = 13) -> QLabel:
    lbl = QLabel(text)
    weight = 600 if bold else 400
    c = color or PALETTE["text"]
    lbl.setStyleSheet(
        f"color: {c}; font-family: 'Segoe UI'; font-size: {size}px; font-weight: {weight};"
    )
    lbl.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
    return lbl


class SectionCard(QFrame):
    def __init__(self, title: str, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("SectionCard")
        self.setStyleSheet(
            f"QFrame#SectionCard {{ background-color: {PALETTE['card']}; border-radius: 16px; }}"
        )
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 14, 16, 12)
        lay.setSpacing(8)
        lay.addWidget(_label(title, bold=True, size=15), alignment=Qt.AlignmentFlag.AlignLeft)


class Pill(QFrame):
    def __init__(self, text: str, kind: str = "muted", parent: Optional[Widget] = None):  # type: ignore[name-defined]
        super().__init__(parent)
        colors: Dict[str, tuple[str, str]] = {
            "active": ("#1e3325", PALETTE["ok"]),
            "suspended": ("#33240f", PALETTE["warn"]),
            "expired": ("#3a1418", PALETTE["danger"]),
            "blacklisted": ("#3a1418", PALETTE["danger"]),
            "muted": ("#2b3344", PALETTE["muted"]),
        }
        bg, fg = colors.get(kind, colors["muted"])  # type: ignore[index]
        self.setStyleSheet(f"background-color: {bg}; border-radius: 999px;")
        lay = QHBoxLayout(self)
        lay.setContentsMargins(10, 4, 10, 4)
        lay.addWidget(_label(text, color=fg, size=12))


class MemberRow(QFrame):
    def __init__(self, member: Dict[str, Any], on_open: Callable[[Dict[str, Any]], None], parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.member = member
        self.on_open = on_open
        self.setObjectName("MemberRow")
        self.setStyleSheet(f"QFrame#MemberRow {{ background-color: {PALETTE['card']}; border-radius: 10px; }}")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        grid = QGridLayout(self)
        grid.setContentsMargins(12, 8, 12, 8)
        grid.setHorizontalSpacing(8)
        weights = (10, 28, 18, 12, 12, 12, 8)
        for i, w in enumerate(weights):
            grid.setColumnStretch(i, w)

        mid = str(member.get("id", "—"))
        name = f"{member.get('first_name','')} {member.get('last_name','')}".strip() or "—"
        phone = member.get("phone", "—")
        join = member.get("join_date", "—")
        try:
            if isinstance(join, (dt.date, dt.datetime)):
                join = join.strftime("%Y-%m-%d")
        except Exception:
            pass
        debt_val = float(member.get("debt", 0) or 0)
        debt = f"{int(debt_val)} DA" if debt_val > 0 else "—"
        status_raw = (member.get("status") or "active").lower()
        status_kind = (
            "active" if status_raw == "active" else
            "suspended" if status_raw == "suspended" else
            "expired" if status_raw == "expired" else
            "blacklisted" if status_raw == "blacklisted" else
            "muted"
        )

        grid.addWidget(_label(mid), 0, 0)
        grid.addWidget(_label(name), 0, 1)
        grid.addWidget(_label(phone, color=PALETTE["muted"]), 0, 2)
        grid.addWidget(_label(str(join), color=PALETTE["muted"]), 0, 3)
        grid.addWidget(_label(debt, color=PALETTE["muted"]), 0, 4)

        pill = Pill(status_raw.capitalize(), kind=status_kind)
        grid.addWidget(pill, 0, 5)

        btn = PrimaryPushButton("Open")
        btn.setFixedHeight(30)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.clicked.connect(lambda: self.on_open(self.member))  # type: ignore[arg-type]
        grid.addWidget(btn, 0, 6, alignment=Qt.AlignmentFlag.AlignRight)

    def mousePressEvent(self, event):  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton:
            self.on_open(self.member)
        return super().mousePressEvent(event)


class MembersPage(QWidget):
    """
    FAST Members list:
      - Async data fetch (thread)
      - Pagination (page_size=50)
      - Debounced, cancelable refresh
    """
    # Signal to ensure thread-safe UI updates: carries (seq, data)
    dataReady = pyqtSignal(int, list)

    def __init__(self, services: Optional[object] = None, page_size: int = 50,
                 on_open_member: Optional[Callable[[Dict[str, Any] | None], None]] = None,
                 parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.services = services
        self.page_size = page_size
        self.on_open_member = on_open_member

        self.setObjectName("MembersPage")
        self.setStyleSheet(
            f"""
            QWidget#MembersPage {{ background-color: {PALETTE['surface']}; }}
            QLabel {{ color: {PALETTE['text']}; }}
            QLineEdit {{
                color: {PALETTE['text']};
                background-color: {PALETTE['card2']};
                border: 1px solid {PALETTE['card2']};
                border-radius: 8px; padding: 6px 8px;
            }}
            QComboBox {{
                color: {PALETTE['text']};
                background-color: {PALETTE['card2']};
                border: 1px solid {PALETTE['card2']};
                border-radius: 8px; padding: 4px 8px;
            }}
            QComboBox::drop-down {{ width: 24px; }}
            QComboBox QAbstractItemView {{
                background: {PALETTE['card2']}; color: {PALETTE['text']};
                selection-background-color: {PALETTE['accent']};
            }}
            QPushButton[cssClass="primary"] {{
                background-color: {PALETTE['accent']}; color: {PALETTE['text']};
                border-radius: 14px; height: 30px; padding: 4px 10px;
            }}
            QPushButton[cssClass="primary"]:hover {{ background-color: #3f70cc; }}
            QPushButton[cssClass="secondary"] {{
                background-color: #2a3550; color: {PALETTE['text']};
                border-radius: 14px; height: 30px; padding: 4px 10px;
            }}
            QPushButton[cssClass="secondary"]:hover {{ background-color: #334066; }}
            QFrame#HeaderRow {{ background-color: {PALETTE['card2']}; border-radius: 12px; }}
            QScrollArea {{ background: transparent; border: none; }}
            """
        )

        # state
        self._debounce_timer: Optional[QTimer] = None
        self._fetch_seq = 0
        self._rows: List[MemberRow] = []
        self._data: List[Dict[str, Any]] = []
        self._page = 0

        # connect signals
        self.dataReady.connect(self._on_data_ready)

        # root grid
        root = QGridLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setVerticalSpacing(8)
        root.setHorizontalSpacing(8)
        root.setColumnStretch(0, 1)
        root.setRowStretch(4, 1)

        # title
        title = SectionCard("Members — Live Search & List")
        root.addWidget(title, 0, 0)

        # toolbar
        bar = QFrame()
        bar.setStyleSheet(f"background-color: {PALETTE['card']}; border-radius: 16px;")
        bar_grid = QGridLayout(bar)
        bar_grid.setContentsMargins(12, 10, 12, 10)
        bar_grid.setHorizontalSpacing(8)
        for i in range(12):
            bar_grid.setColumnStretch(i, 1)

        bar_grid.addWidget(_label("Search", color=PALETTE["muted"]), 0, 0)
        self.ent_q = LineEdit()
        self.ent_q.setPlaceholderText("Name, phone, or ID…")
        self.ent_q.textChanged.connect(lambda _t: self._debounced_refresh())
        bar_grid.addWidget(self.ent_q, 0, 1, 1, 3)

        bar_grid.addWidget(_label("Status", color=PALETTE["muted"]), 0, 4)
        self.opt_status = ComboBox()
        self.opt_status.addItems(["All", "active", "suspended", "expired", "blacklisted"])
        self.opt_status.currentIndexChanged.connect(lambda _i: self._refresh())
        bar_grid.addWidget(self.opt_status, 0, 5)

        self.btn_refresh = PushButton("Refresh")
        self.btn_refresh.setProperty("cssClass", "secondary")
        self.btn_refresh.clicked.connect(self._refresh)
        bar_grid.addWidget(self.btn_refresh, 0, 8)

        self.btn_add = PrimaryPushButton("Add member")
        self.btn_add.clicked.connect(lambda: self._open_member_form(None))
        bar_grid.addWidget(self.btn_add, 0, 9)

        root.addWidget(bar, 1, 0)

        # header
        header = SectionCard("Results")
        header_lay = header.layout()  # type: ignore[assignment]
        hdr = QFrame()
        hdr.setObjectName("HeaderRow")
        hdr_grid = QGridLayout(hdr)
        hdr_grid.setContentsMargins(10, 8, 10, 8)
        labels = ("ID", "Name", "Phone", "Join", "Debt", "Status", "")
        weights = (10, 28, 18, 12, 12, 12, 8)
        for i, (txt, w) in enumerate(zip(labels, weights)):
            hdr_grid.addWidget(_label(txt, color=PALETTE["muted"]), 0, i)
            hdr_grid.setColumnStretch(i, w)
        header_lay.addWidget(hdr)  # type: ignore[arg-type]
        root.addWidget(header, 2, 0)

        # list (scroll)
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet(f"QWidget {{ background-color: {PALETTE['card2']}; border-radius: 12px; }}")
        self.list_container = QWidget()
        self.list_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.list_vbox = QVBoxLayout(self.list_container)
        self.list_vbox.setContentsMargins(10, 8, 10, 8)
        self.list_vbox.setSpacing(6)
        self.scroll.setWidget(self.list_container)
        root.addWidget(self.scroll, 4, 0)

        # pager
        pager = QFrame()
        pager.setStyleSheet("background: transparent;")
        pgrid = QGridLayout(pager)
        pgrid.setContentsMargins(12, 6, 12, 0)
        pgrid.setHorizontalSpacing(8)
        for i in range(3):
            pgrid.setColumnStretch(i, 1)
        self.btn_prev = QPushButton("◀ Prev")
        self.btn_prev.setProperty("cssClass", "secondary")
        self.btn_prev.setMinimumHeight(28)
        self.btn_prev.clicked.connect(self._prev_page)
        self.lbl_page = _label("Page 1 / 1", color=PALETTE["muted"])
        self.lbl_page.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.btn_next = QPushButton("Next ▶")
        self.btn_next.setProperty("cssClass", "secondary")
        self.btn_next.setMinimumHeight(28)
        self.btn_next.clicked.connect(self._next_page)
        pgrid.addWidget(self.btn_prev, 0, 0, alignment=Qt.AlignmentFlag.AlignLeft)
        pgrid.addWidget(self.lbl_page, 0, 1, alignment=Qt.AlignmentFlag.AlignCenter)
        pgrid.addWidget(self.btn_next, 0, 2, alignment=Qt.AlignmentFlag.AlignRight)
        root.addWidget(pager, 3, 0)

        # initial
        self._refresh()

    # ---------- behavior ----------
    def _debounced_refresh(self, ms: int = 350):
        if self._debounce_timer is None:
            self._debounce_timer = QTimer(self)
            self._debounce_timer.setSingleShot(True)
            self._debounce_timer.timeout.connect(self._refresh)
        self._debounce_timer.start(ms)

    def _get_status_value(self) -> Optional[str]:
        val = self.opt_status.currentText().strip()
        return None if val == "All" else val

    def _set_loading(self, is_loading: bool, note: str = "Loading…"):
        self.btn_refresh.setEnabled(not is_loading)
        self.btn_refresh.setText("Refreshing…" if is_loading else "Refresh")
        if is_loading:
            self._clear_list()
            self.list_vbox.addWidget(_label(note, color=PALETTE["muted"]))

    def _clear_list(self):
        for r in getattr(self, "_rows", []):
            try:
                r.setParent(None)
            except Exception:
                pass
        self._rows.clear()
        while self.list_vbox.count():
            item = self.list_vbox.takeAt(0)
            w = item.widget()
            if w is not None:
                w.setParent(None)

    def _refresh(self):
        if self._debounce_timer and self._debounce_timer.isActive():
            self._debounce_timer.stop()

        self._page = 0
        self._fetch_seq += 1
        seq = self._fetch_seq
        self._set_loading(True)

        q = (self.ent_q.text() or "").strip()
        status = self._get_status_value()

        def worker():
            data = self._fetch_rows(q, status)
            # Emit to main thread for safe UI update
            try:
                self.dataReady.emit(seq, data)  # type: ignore[arg-type]
            except Exception:
                pass
        threading.Thread(target=worker, daemon=True).start()

    def _on_data_ready(self, seq: int, data: list):  # slot
        if seq != self._fetch_seq:
            return
        self._data = data
        self._set_loading(False)
        self._render_page()

    def _fetch_rows(self, q: str, status: Optional[str]) -> List[Dict[str, Any]]:
        if self.services and hasattr(self.services, "find_members"):
            try:
                data = self.services.find_members(q, status) or []
                for m in data:
                    m.setdefault("debt", 0)
                return data
            except Exception:
                pass
        # 2) Example demo data (exactly 10 members)
        out: List[Dict[str, Any]] = [
            {"id": 1001, "first_name": "Nadia",  "last_name": "K.", "phone": "055 123 456", "status": "active",     "join_date": (dt.date.today() - dt.timedelta(days=30)).strftime("%Y-%m-%d"),  "debt": 0},
            {"id": 1002, "first_name": "Hind",   "last_name": "B.", "phone": "056 234 567", "status": "active",     "join_date": (dt.date.today() - dt.timedelta(days=120)).strftime("%Y-%m-%d"), "debt": 200},
            {"id": 1003, "first_name": "Amine",  "last_name": "M.", "phone": "057 345 678", "status": "suspended",  "join_date": (dt.date.today() - dt.timedelta(days=75)).strftime("%Y-%m-%d"),  "debt": 350},
            {"id": 1004, "first_name": "Karim",  "last_name": "A.", "phone": "058 456 789", "status": "expired",    "join_date": (dt.date.today() - dt.timedelta(days=400)).strftime("%Y-%m-%d"), "debt": 0},
            {"id": 1005, "first_name": "Sara",   "last_name": "L.", "phone": "059 567 890", "status": "active",     "join_date": (dt.date.today() - dt.timedelta(days=10)).strftime("%Y-%m-%d"),  "debt": 0},
            {"id": 1006, "first_name": "Yasmine","last_name": "D.", "phone": "055 678 901", "status": "expired",    "join_date": (dt.date.today() - dt.timedelta(days=260)).strftime("%Y-%m-%d"), "debt": 600},
            {"id": 1007, "first_name": "Omar",   "last_name": "T.", "phone": "056 789 012", "status": "active",     "join_date": (dt.date.today() - dt.timedelta(days=5)).strftime("%Y-%m-%d"),   "debt": 0},
            {"id": 1008, "first_name": "Samir",  "last_name": "R.", "phone": "057 890 123", "status": "suspended",  "join_date": (dt.date.today() - dt.timedelta(days=220)).strftime("%Y-%m-%d"), "debt": 0},
            {"id": 1009, "first_name": "Aya",    "last_name": "S.", "phone": "058 901 234", "status": "blacklisted","join_date": (dt.date.today() - dt.timedelta(days=540)).strftime("%Y-%m-%d"), "debt": 350},
            {"id": 1010, "first_name": "Mina",   "last_name": "N.", "phone": "059 012 345", "status": "active",     "join_date": (dt.date.today() - dt.timedelta(days=60)).strftime("%Y-%m-%d"),  "debt": 0},
            {"id": 1001, "first_name": "Nadia",  "last_name": "K.", "phone": "055 123 456", "status": "active",     "join_date": (dt.date.today() - dt.timedelta(days=30)).strftime("%Y-%m-%d"),  "debt": 0},
            {"id": 1002, "first_name": "Hind",   "last_name": "B.", "phone": "056 234 567", "status": "active",     "join_date": (dt.date.today() - dt.timedelta(days=120)).strftime("%Y-%m-%d"), "debt": 200},
            {"id": 1003, "first_name": "Amine",  "last_name": "M.", "phone": "057 345 678", "status": "suspended",  "join_date": (dt.date.today() - dt.timedelta(days=75)).strftime("%Y-%m-%d"),  "debt": 350},
            {"id": 1004, "first_name": "Karim",  "last_name": "A.", "phone": "058 456 789", "status": "expired",    "join_date": (dt.date.today() - dt.timedelta(days=400)).strftime("%Y-%m-%d"), "debt": 0},
            {"id": 1005, "first_name": "Sara",   "last_name": "L.", "phone": "059 567 890", "status": "active",     "join_date": (dt.date.today() - dt.timedelta(days=10)).strftime("%Y-%m-%d"),  "debt": 0},
            {"id": 1006, "first_name": "Yasmine","last_name": "D.", "phone": "055 678 901", "status": "expired",    "join_date": (dt.date.today() - dt.timedelta(days=260)).strftime("%Y-%m-%d"), "debt": 600},
            {"id": 1007, "first_name": "Omar",   "last_name": "T.", "phone": "056 789 012", "status": "active",     "join_date": (dt.date.today() - dt.timedelta(days=5)).strftime("%Y-%m-%d"),   "debt": 0},
            {"id": 1008, "first_name": "Samir",  "last_name": "R.", "phone": "057 890 123", "status": "suspended",  "join_date": (dt.date.today() - dt.timedelta(days=220)).strftime("%Y-%m-%d"), "debt": 0},
            {"id": 1009, "first_name": "Aya",    "last_name": "S.", "phone": "058 901 234", "status": "blacklisted","join_date": (dt.date.today() - dt.timedelta(days=540)).strftime("%Y-%m-%d"), "debt": 350},
            {"id": 1010, "first_name": "Mina",   "last_name": "N.", "phone": "059 012 345", "status": "active",     "join_date": (dt.date.today() - dt.timedelta(days=60)).strftime("%Y-%m-%d"),  "debt": 0},

        
        ]
    
        ql = q.lower()
        if ql:
            out = [m for m in out if ql in str(m["id"]).lower()
                   or ql in (m["first_name"] + " " + m["last_name"]).lower()
                   or ql in m["phone"].replace(" ","")]
        if status:
            out = [m for m in out if (m.get("status") or "").lower() == status.lower()]
        return out

    # ----- pagination -----
    def _page_slice(self) -> List[Dict[str, Any]]:
        start = self._page * self.page_size
        end = start + self.page_size
        return self._data[start:end]

    def _render_page(self):
        self._clear_list()
        rows = self._page_slice()
        if not rows:
            self.list_vbox.addWidget(_label("No members found", color=PALETTE["muted"]))
        else:
            for m in rows:
                row = MemberRow(m, on_open=self._open_member_form)
                self.list_vbox.addWidget(row)
                self._rows.append(row)
        # push content to top and allow growth
        self.list_vbox.addStretch(1)
        total = max(1, (len(self._data) + self.page_size - 1) // self.page_size)
        self.lbl_page.setText(f"Page {self._page+1} / {total}")
        self.btn_prev.setEnabled(self._page > 0)
        self.btn_next.setEnabled(self._page < total - 1)

        # ensure top
        self.scroll.verticalScrollBar().setValue(0)

    def _prev_page(self):
        if self._page <= 0:
            return
        self._page -= 1
        self._render_page()

    def _next_page(self):
        total = max(1, (len(self._data) + self.page_size - 1) // self.page_size)
        if self._page >= total - 1:
            return
        self._page += 1
        self._render_page()

    # ----- routing to full-page form -----
    def _open_member_form(self, member: Optional[Dict[str, Any]]):
        if self.on_open_member:
            self.on_open_member(member)
        else:
            # Placeholder: In integration, replace with your actual member form page
            print("Open member form:", member and member.get("id"))


if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    try:
        setTheme(Theme.DARK)
    except Exception:
        pass

    root = QWidget()
    root.setObjectName("Root")
    root.setStyleSheet(f"QWidget#Root {{ background-color: {PALETTE['bg']}; }}")
    root.resize(1200, 720)

    page = MembersPage(services=None, parent=root)

    lay = QVBoxLayout(root)
    lay.setContentsMargins(0, 0, 0, 0)
    lay.addWidget(page)

    root.show()
    sys.exit(app.exec())
