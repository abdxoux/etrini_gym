from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

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
    QSpinBox,
    QDoubleSpinBox,
    QSizePolicy,
)
from qfluentwidgets import setTheme, Theme, LineEdit, PrimaryPushButton, PushButton


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
        lay.addWidget(_label(title, bold=True, size=15))


class PlanRow(QFrame):
    def __init__(self, p: Dict[str, Any], on_edit, on_delete, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.p = p; self.on_edit = on_edit; self.on_delete = on_delete
        self.setStyleSheet(f"background-color:{PALETTE['card2']}; border-radius:10px;")
        g = QGridLayout(self); g.setContentsMargins(12,8,12,8); g.setHorizontalSpacing(8)
        cols = (28, 10, 12, 12, 12, 26)
        for i, w in enumerate(cols): g.setColumnStretch(i, w)
        name = p.get("name","—")
        months = int(p.get("months", 0) or 0)
        dpm = int(p.get("days_per_month", 0) or 0)
        dur = months * dpm if months and dpm else int(str(p.get("duration","0").split()[0] or 0)) if p.get("duration") else 0
        price = float(p.get("price",0) or 0)
        desc = p.get("description","")
        g.addWidget(_label(name), 0, 0)
        g.addWidget(_label(str(months), color=PALETTE["muted"]), 0, 1)
        g.addWidget(_label(str(dpm), color=PALETTE["muted"]), 0, 2)
        g.addWidget(_label(str(dur), color=PALETTE["muted"]), 0, 3)
        g.addWidget(_label(f"{price:.0f} DA"), 0, 4)
        g.addWidget(_label(desc, color=PALETTE["muted"]), 0, 5)
        btns = QFrame(); hb = QHBoxLayout(btns); hb.setContentsMargins(0,0,0,0); hb.setSpacing(6)
        b_edit = PushButton("Edit"); b_edit.setProperty("cssClass","secondary"); b_edit.clicked.connect(lambda: self.on_edit(self.p))
        b_del = PushButton("Delete"); b_del.setProperty("cssClass","secondary"); b_del.clicked.connect(lambda: self.on_delete(self.p))
        hb.addWidget(b_edit); hb.addWidget(b_del)
        g.addWidget(btns, 0, 6, alignment=Qt.AlignmentFlag.AlignRight)


class ManagePlansPage(QWidget):
    def __init__(self, services: Optional[object] = None, on_back=None, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.services = services
        self.on_back = on_back
        self._all: List[Dict[str, Any]] = []
        self._timer: Optional[QTimer] = None

        self.setObjectName("ManagePlansPage")
        self.setStyleSheet(
            f"""
            QWidget#ManagePlansPage {{ background-color:{PALETTE['surface']}; }}
            QLabel {{ color:{PALETTE['text']}; }}
            QLineEdit, QSpinBox, QDoubleSpinBox {{ color:{PALETTE['text']}; background-color:{PALETTE['card2']}; border:1px solid {PALETTE['card2']}; border-radius:8px; padding:6px 8px; }}
            QPushButton[cssClass='primary'] {{ background-color:{PALETTE['accent']}; color:{PALETTE['text']}; border-radius:14px; height:30px; padding:4px 12px; }}
            QPushButton[cssClass='primary']:hover {{ background-color:#3e74d6; }}
            QPushButton[cssClass='secondary'] {{ background-color:#2a3550; color:{PALETTE['text']}; border-radius:14px; height:30px; padding:4px 12px; }}
            QPushButton[cssClass='secondary']:hover {{ background-color:#334066; }}
            """
        )

        root = QGridLayout(self); root.setContentsMargins(12,12,12,12); root.setHorizontalSpacing(8); root.setVerticalSpacing(8)
        root.setColumnStretch(0, 1); root.setRowStretch(3, 1)

        # Header with Back and Add
        head = QFrame(); hg = QGridLayout(head); hg.setContentsMargins(0,0,0,0)
        btn_back = PushButton("◀ Back"); btn_back.setProperty("cssClass","secondary"); btn_back.clicked.connect(lambda: self.on_back() if self.on_back else None)
        title = _label("Manage Plans", size=16, bold=True)
        btn_add = PrimaryPushButton("+ Add Plan"); btn_add.clicked.connect(self._add_plan)
        hg.addWidget(btn_back, 0, 0, alignment=Qt.AlignmentFlag.AlignLeft)
        hg.addWidget(title, 0, 1, alignment=Qt.AlignmentFlag.AlignCenter)
        hg.addWidget(btn_add, 0, 2, alignment=Qt.AlignmentFlag.AlignRight)
        root.addWidget(head, 0, 0)

        # Filters
        filt = QFrame(); fg = QGridLayout(filt); fg.setContentsMargins(12,10,12,10); fg.setHorizontalSpacing(8)
        fg.addWidget(_label("Search", color=PALETTE['muted']), 0, 0)
        self.ent_q = LineEdit(); self.ent_q.setPlaceholderText("Name contains…"); self.ent_q.textChanged.connect(self._debounced_refresh)
        fg.addWidget(self.ent_q, 0, 1)
        fg.addWidget(_label("Price DA", color=PALETTE['muted']), 0, 2)
        self.min_price = QDoubleSpinBox(); self.min_price.setRange(0, 1_000_000); self.min_price.setDecimals(0); self.min_price.valueChanged.connect(self._debounced_refresh)
        self.max_price = QDoubleSpinBox(); self.max_price.setRange(0, 1_000_000); self.max_price.setDecimals(0); self.max_price.setValue(1_000_000); self.max_price.valueChanged.connect(self._debounced_refresh)
        fg.addWidget(self.min_price, 0, 3); fg.addWidget(self.max_price, 0, 4)
        fg.addWidget(_label("Months", color=PALETTE['muted']), 0, 5)
        self.min_months = QSpinBox(); self.min_months.setRange(0, 60); self.min_months.valueChanged.connect(self._debounced_refresh)
        self.max_months = QSpinBox(); self.max_months.setRange(0, 60); self.max_months.setValue(60); self.max_months.valueChanged.connect(self._debounced_refresh)
        fg.addWidget(self.min_months, 0, 6); fg.addWidget(self.max_months, 0, 7)
        fg.addWidget(_label("Days/Month", color=PALETTE['muted']), 0, 8)
        self.min_dpm = QSpinBox(); self.min_dpm.setRange(0, 60); self.min_dpm.valueChanged.connect(self._debounced_refresh)
        self.max_dpm = QSpinBox(); self.max_dpm.setRange(0, 60); self.max_dpm.setValue(60); self.max_dpm.valueChanged.connect(self._debounced_refresh)
        fg.addWidget(self.min_dpm, 0, 9); fg.addWidget(self.max_dpm, 0, 10)
        root.addWidget(filt, 1, 0)

        # Header row (table headings)
        hdr = QFrame(); hdr.setStyleSheet(f"background-color:{PALETTE['card2']}; border-radius:12px;")
        hg2 = QGridLayout(hdr); hg2.setContentsMargins(10,8,10,8)
        labels = ("Name", "Months", "Days/Month", "Duration (days)", "Price (DA)", "Description", "Actions")
        weights = (28, 10, 12, 12, 12, 26, 12)
        for i, (txt, w) in enumerate(zip(labels, weights)):
            hg2.addWidget(_label(txt, color=PALETTE["muted"]), 0, i); hg2.setColumnStretch(i, w)
        root.addWidget(hdr, 2, 0)

        # List
        self.scroll = QScrollArea(); self.scroll.setWidgetResizable(True)
        self.wrap = QWidget(); self.vbox = QVBoxLayout(self.wrap); self.vbox.setContentsMargins(8,6,8,8); self.vbox.setSpacing(6)
        self.scroll.setWidget(self.wrap)
        root.addWidget(self.scroll, 3, 0)

        self._load()

    # ----- debounce & data -----
    def _debounced_refresh(self, *args):
        if self._timer is None:
            self._timer = QTimer(self)
            self._timer.setSingleShot(True)
            self._timer.timeout.connect(self._refresh)
        self._timer.start(250)

    def _load(self):
        self._all = self._fetch_plans()
        self._refresh()

    def _fetch_plans(self) -> List[Dict[str, Any]]:
        if self.services and hasattr(self.services, "plans") and hasattr(self.services.plans, "list"):
            try:
                rows = list(self.services.plans.list()) or []
                out: List[Dict[str, Any]] = []
                for r in rows:
                    out.append({
                        "id": r.get("id") or r.get("plan_id") or r.get("name"),
                        "plan_id": r.get("plan_id") or r.get("id"),
                        "name": r.get("name",""),
                        "months": int(r.get("months") or 0),
                        "days_per_month": int(r.get("days_per_month") or 0),
                        "duration": r.get("duration",""),
                        "price": float(r.get("price",0) or 0),
                        "description": r.get("description",""),
                    })
                return out
            except Exception:
                pass
        # fallback demo
        return [
            {"id":"monthly30","name":"Monthly","months":1,"days_per_month":30,"price":1200.0,"description":"Standard"},
            {"id":"quarterly16","name":"Quarterly (16d/mo)","months":3,"days_per_month":16,"price":2400.0,"description":"Limited days"},
            {"id":"monthly16","name":"Monthly (16d/mo)","months":1,"days_per_month":16,"price":900.0,"description":"Budget"},
        ]

    def _apply_filters(self, rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        q = (self.ent_q.text() or "").strip().lower()
        pmin = float(self.min_price.value()); pmax = float(self.max_price.value())
        mmin = int(self.min_months.value()); mmax = int(self.max_months.value())
        dmin = int(self.min_dpm.value()); dmax = int(self.max_dpm.value())
        out = []
        for r in rows:
            name = (r.get("name","") or "").lower()
            price = float(r.get("price",0) or 0)
            months = int(r.get("months") or 0)
            dpm = int(r.get("days_per_month") or 0)
            if q and q not in name: continue
            if not (pmin <= price <= pmax): continue
            if not (mmin <= months <= mmax): continue
            if not (dmin <= dpm <= dmax): continue
            out.append(r)
        # sort: Name asc, then Price desc
        out.sort(key=lambda x: ((x.get("name") or "").lower(), -float(x.get("price",0) or 0)))
        return out

    def _refresh(self):
        # clear list
        while self.vbox.count():
            it = self.vbox.takeAt(0); w = it.widget();
            if w: w.setParent(None)
        items = self._apply_filters(self._all)
        if not items:
            self.vbox.addWidget(_label("No plans found", color=PALETTE["muted"]))
        else:
            for p in items:
                self.vbox.addWidget(PlanRow(p, on_edit=self._edit_plan, on_delete=self._delete_plan))
        self.vbox.addStretch(1)

    # ----- actions -----
    def _add_plan(self):
        self._open_editor(None)

    def _edit_plan(self, plan: Dict[str, Any]):
        self._open_editor(plan)

    def _delete_plan(self, plan: Dict[str, Any]):
        pid = plan.get("id") or plan.get("plan_id") or plan.get("name")
        if self.services and hasattr(self.services, "plans") and hasattr(self.services.plans, "delete"):
            try:
                self.services.plans.delete(pid)
                self._all = self._fetch_plans(); self._refresh(); return
            except Exception:
                pass
        self._all = [p for p in self._all if (p.get("id") or p.get("plan_id") or p.get("name")) != pid]
        self._refresh()

    # simple in-page editor using a small form card
    def _open_editor(self, initial: Optional[Dict[str, Any]]):
        editor = QFrame(); editor.setStyleSheet(f"background-color:{PALETTE['card']}; border-radius:16px;")
        eg = QGridLayout(editor); eg.setContentsMargins(12,10,12,10); eg.setHorizontalSpacing(8)
        eg.addWidget(_label("Name", color=PALETTE['muted']), 0, 0); ent_name = LineEdit(); eg.addWidget(ent_name, 0, 1)
        eg.addWidget(_label("Months", color=PALETTE['muted']), 0, 2); ent_months = QSpinBox(); ent_months.setRange(1, 60); eg.addWidget(ent_months, 0, 3)
        eg.addWidget(_label("Days/Month", color=PALETTE['muted']), 0, 4); ent_dpm = QSpinBox(); ent_dpm.setRange(1, 60); eg.addWidget(ent_dpm, 0, 5)
        eg.addWidget(_label("Price (DA)", color=PALETTE['muted']), 1, 0); ent_price = QDoubleSpinBox(); ent_price.setRange(0, 1_000_000); ent_price.setDecimals(0); eg.addWidget(ent_price, 1, 1)
        eg.addWidget(_label("Description", color=PALETTE['muted']), 1, 2); ent_desc = LineEdit(); eg.addWidget(ent_desc, 1, 3, 1, 3)
        btns = QFrame(); hb = QHBoxLayout(btns); hb.setContentsMargins(0,0,0,0)
        b_cancel = PushButton("Cancel"); b_cancel.setProperty("cssClass","secondary")
        b_save = PrimaryPushButton("Save")
        hb.addWidget(b_cancel); hb.addWidget(b_save)
        eg.addWidget(btns, 2, 0, 1, 6, alignment=Qt.AlignmentFlag.AlignRight)

        # prefill
        if initial:
            ent_name.setText(str(initial.get("name","")))
            ent_months.setValue(int(initial.get("months") or 1))
            ent_dpm.setValue(int(initial.get("days_per_month") or 30))
            ent_price.setValue(float(initial.get("price",0) or 0))
            ent_desc.setText(str(initial.get("description","")))

        # inject at top
        self.vbox.insertWidget(0, editor)

        def close_editor():
            editor.setParent(None)

        b_cancel.clicked.connect(close_editor)

        def save_editor():
            data = {
                "name": (ent_name.text() or "").strip(),
                "months": int(ent_months.value()),
                "days_per_month": int(ent_dpm.value()),
                "price": float(ent_price.value()),
                "description": (ent_desc.text() or "").strip(),
            }
            if not data["name"]:
                close_editor(); return
            if self.services and hasattr(self.services, "plans"):
                try:
                    if initial:
                        pid = initial.get("id") or initial.get("plan_id") or initial.get("name")
                        if hasattr(self.services.plans, "update"):
                            self.services.plans.update(pid, data); self._all = self._fetch_plans(); self._refresh(); close_editor(); return
                    elif hasattr(self.services.plans, "create"):
                        self.services.plans.create(data); self._all = self._fetch_plans(); self._refresh(); close_editor(); return
                except Exception:
                    pass
            # local
            if initial:
                pid = initial.get("id") or initial.get("plan_id") or initial.get("name")
                for i, p in enumerate(self._all):
                    if (p.get("id") or p.get("plan_id") or p.get("name")) == pid:
                        upd = dict(p); upd.update(data); self._all[i] = upd; break
            else:
                self._all.append({"id": data["name"], **data})
            self._refresh(); close_editor()

        b_save.clicked.connect(save_editor)


if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    try:
        setTheme(Theme.DARK)
    except Exception:
        pass
    root = QWidget(); root.setObjectName("Root"); root.setStyleSheet(f"QWidget#Root {{ background-color: {PALETTE['bg']}; }}"); root.resize(1200, 800)
    page = ManagePlansPage(services=None)
    lay = QVBoxLayout(root); lay.setContentsMargins(0,0,0,0); lay.addWidget(page)
    root.show(); sys.exit(app.exec())
