# pages_qt/subscriptions.py
# GymPro — Subscriptions (PyQt6 port). Assign/Renew with plans catalog

from __future__ import annotations

import datetime as dt
from typing import Any, Dict, Iterable, List, Optional

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
    QComboBox,
    QScrollArea,
    QSizePolicy,
    QCheckBox,
)
from qfluentwidgets import setTheme, Theme, LineEdit, ComboBox, PrimaryPushButton, PushButton


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


class Pill(QFrame):
    def __init__(self, text: str, kind: str = "muted", parent: Optional[QWidget] = None):
        super().__init__(parent)
        colors = {"ok": ("#1e3325", PALETTE["ok"]), "warn": ("#33240f", PALETTE["warn"]), "danger": ("#3a1418", PALETTE["danger"]), "muted": ("#2b3344", PALETTE["muted"]) }
        bg, fg = colors.get(kind, colors["muted"])  # type: ignore[index]
        self.setStyleSheet(f"background-color:{bg}; border-radius:999px;")
        lay = QHBoxLayout(self); lay.setContentsMargins(10, 4, 10, 4)
        lay.addWidget(_label(text, color=fg, size=12))


class PlanCard(QFrame):
    def __init__(self, plan: Dict[str, Any], on_pick, on_edit, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.plan = plan; self.on_pick = on_pick; self.on_edit = on_edit
        self._active = False
        self.setStyleSheet(f"background-color:{PALETTE['card2']}; border-radius:12px;")
        grid = QGridLayout(self); grid.setContentsMargins(12,8,12,8); grid.setHorizontalSpacing(8)
        grid.setColumnStretch(0, 4); grid.setColumnStretch(1, 1)
        grid.addWidget(_label(plan.get("name","—"), bold=True, size=14), 0, 0)
        btn = PushButton("Modify"); btn.setProperty("cssClass","secondary"); btn.setMinimumHeight(26); btn.clicked.connect(lambda: self.on_edit(self.plan))
        grid.addWidget(btn, 0, 1, alignment=Qt.AlignmentFlag.AlignRight)
        m = plan.get("months"); dpm = plan.get("days_per_month"); subtitle = (f"{m} mo × {dpm} d/mo" if m and dpm else plan.get("duration",""))
        grid.addWidget(_label(subtitle, color=PALETTE["muted"]), 1, 0)
        grid.addWidget(Pill(f"{float(plan.get('price',0)):.0f} DA", "muted"), 1, 1, alignment=Qt.AlignmentFlag.AlignRight)

    def mousePressEvent(self, e):  # noqa: N802
        if e.button() == Qt.MouseButton.LeftButton:
            self.on_pick(self.plan)
        return super().mousePressEvent(e)

    def set_active(self, active: bool):
        self._active = active
        self.setStyleSheet(f"background-color:{'#24324a' if active else PALETTE['card2']}; border-radius:12px;")


class SubscriptionsPage(QWidget):
    def __init__(self, services: Optional[object] = None, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.services = services
        self._picked_plan: Optional[Dict[str, Any]] = None
        self._picked_member: Optional[Dict[str, Any]] = None

        self.setObjectName("SubscriptionsPage")
        self.setStyleSheet(
            f"""
            QWidget#SubscriptionsPage {{ background-color:{PALETTE['surface']}; }}
            QLabel {{ color:{PALETTE['text']}; }}
            QLineEdit, QComboBox {{ color:{PALETTE['text']}; background-color:{PALETTE['card2']}; border:1px solid {PALETTE['card2']}; border-radius:8px; padding:6px 8px; }}
            QComboBox::drop-down {{ width: 24px; }}
            QComboBox QAbstractItemView {{ background: {PALETTE['card2']}; color: {PALETTE['text']}; selection-background-color: {PALETTE['accent']}; }}
            QPushButton[cssClass='primary'] {{ background-color:{PALETTE['accent']}; color:{PALETTE['text']}; border-radius:14px; height:30px; padding:4px 12px; }}
            QPushButton[cssClass='primary']:hover {{ background-color:#3e74d6; }}
            QPushButton[cssClass='secondary'] {{ background-color:#2a3550; color:{PALETTE['text']}; border-radius:14px; height:30px; padding:4px 12px; }}
            QPushButton[cssClass='secondary']:hover {{ background-color:#334066; }}
            QPushButton[cssClass='secondary']:pressed {{ background-color:#26314d; }}
            /* segmented mimic */
            QPushButton[seg='tab'] {{
                background-color: #2b3344; color: {PALETTE['text']};
                border: 1px solid #2b3344; padding: 4px 12px; border-radius: 14px;
            }}
            QPushButton[seg='tab']:checked {{
                background-color: {PALETTE['accent']}; border-color: {PALETTE['accent']};
            }}
            """
        )

        root = QGridLayout(self); root.setContentsMargins(12,12,12,12); root.setHorizontalSpacing(8); root.setVerticalSpacing(8)
        root.setColumnStretch(0, 2); root.setColumnStretch(1, 3)
        root.setRowStretch(1, 1)

        # Left: Member & Plans
        left = QFrame(); left.setStyleSheet("background: transparent;"); lg = QGridLayout(left); lg.setContentsMargins(0,0,0,0); lg.setVerticalSpacing(8)
        lg.addWidget(SectionCard("Member"), 0, 0)
        box = QFrame(); box.setStyleSheet(f"background-color:{PALETTE['card']}; border-radius:16px;"); b = QGridLayout(box); b.setContentsMargins(12,10,12,10); b.setHorizontalSpacing(8)
        b.addWidget(_label("Search", color=PALETTE["muted"]), 0, 0)
        self.ent_member = LineEdit(); self.ent_member.setPlaceholderText("Search member / phone / UID…"); b.addWidget(self.ent_member, 0, 1)
        self.btn_pick_recent = PushButton("Recent"); self.btn_pick_recent.setProperty("cssClass","secondary"); b.addWidget(self.btn_pick_recent, 0, 2)
        lg.addWidget(box, 1, 0)
        cat = SectionCard("Plans Catalog"); lg.addWidget(cat, 2, 0)
        # header row actions: Manage Plans (right)
        cat_hdr = QFrame(); cat_hdr.setStyleSheet("background: transparent;")
        ch = QHBoxLayout(cat_hdr); ch.setContentsMargins(8, 0, 8, 0); ch.addStretch(1)
        self.btn_manage = PushButton("Manage Plans"); self.btn_manage.setProperty("cssClass","secondary")
        self.btn_manage.clicked.connect(self._open_manage_plans)
        ch.addWidget(self.btn_manage)
        cat.layout().addWidget(cat_hdr)  # type: ignore
        self.plans_scroll = QScrollArea(); self.plans_scroll.setWidgetResizable(True)
        self.plans_wrap = QWidget(); self.plans_grid = QGridLayout(self.plans_wrap); self.plans_grid.setContentsMargins(8,6,8,6); self.plans_grid.setHorizontalSpacing(8); self.plans_grid.setVerticalSpacing(8)
        self.plans_scroll.setWidget(self.plans_wrap); cat.layout().addWidget(self.plans_scroll)  # type: ignore
        left.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        root.addWidget(left, 0, 0, 2, 1)

        # Right: Form & History
        right = QFrame(); rg = QGridLayout(right); rg.setContentsMargins(0,0,0,0); rg.setVerticalSpacing(8)
        form_card = SectionCard("New / Renew Subscription"); rg.addWidget(form_card, 0, 0)
        form = QFrame(); form.setStyleSheet("background: transparent;"); fg = QGridLayout(form); fg.setContentsMargins(12,8,12,8); fg.setHorizontalSpacing(8)
        labels = ["Plan", "Start Date", "End Date", "Price (DA)", "Discount (DA)", "To Pay (DA)"]
        self.ent_plan = LineEdit(); self.ent_plan.setReadOnly(True)
        self.ent_start = LineEdit(); self.ent_end = LineEdit(); self.ent_price = LineEdit(); self.ent_disc = LineEdit(); self.ent_pay = LineEdit(); self.ent_pay.setReadOnly(True)
        fields = [self.ent_plan, self.ent_start, self.ent_end, self.ent_price, self.ent_disc, self.ent_pay]
        for i, lab in enumerate(labels):
            fg.addWidget(_label(lab, color=PALETTE["muted"]), i, 0)
            fg.addWidget(fields[i], i, 1)
        # Prorate switch
        self.chk_prorate = QCheckBox("Prorate on renew"); self.chk_prorate.setChecked(True)
        fg.addWidget(self.chk_prorate, len(labels), 0, 1, 2)
        # Payment segmented control (Cash, Card, Transfer)
        pay_line = QFrame(); ph = QHBoxLayout(pay_line); ph.setContentsMargins(0,0,0,0); ph.setSpacing(6)
        from PyQt6.QtWidgets import QButtonGroup
        self._pay_group = QButtonGroup(self); self._pay_group.setExclusive(True)
        self.btn_cash = PushButton("Cash"); self.btn_cash.setCheckable(True); self.btn_cash.setProperty("seg","tab")
        self.btn_card = PushButton("Card"); self.btn_card.setCheckable(True); self.btn_card.setProperty("seg","tab")
        self.btn_trn = PushButton("Transfer"); self.btn_trn.setCheckable(True); self.btn_trn.setProperty("seg","tab")
        self._pay_group.addButton(self.btn_cash); self._pay_group.addButton(self.btn_card); self._pay_group.addButton(self.btn_trn)
        self.btn_cash.setChecked(True)
        ph.addWidget(_label("Payment Method", color=PALETTE["muted"]))
        ph.addWidget(self.btn_cash); ph.addWidget(self.btn_card); ph.addWidget(self.btn_trn); ph.addStretch(1)
        fg.addWidget(pay_line, len(labels)+1, 0, 1, 2)
        btn_submit = PrimaryPushButton("Create / Renew"); btn_submit.clicked.connect(self._submit)
        fg.addWidget(btn_submit, len(labels)+2, 0, 1, 2, alignment=Qt.AlignmentFlag.AlignRight)
        form_card.layout().addWidget(form)  # type: ignore

        hist = SectionCard("Subscription History"); rg.addWidget(hist, 1, 0)
        self.hist_scroll = QScrollArea(); self.hist_scroll.setWidgetResizable(True)
        self.hist_wrap = QWidget(); self.hist_vbox = QVBoxLayout(self.hist_wrap); self.hist_vbox.setContentsMargins(8,6,8,8); self.hist_vbox.setSpacing(6)
        self.hist_scroll.setWidget(self.hist_wrap); hist.layout().addWidget(self.hist_scroll)  # type: ignore
        right.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        root.addWidget(right, 0, 1, 2, 1)

        self._load_initial()

    # ----- data & behavior -----
    def _load_initial(self):
        # plans
        plans = self._fetch_plans()
        if not plans:
            plans = [
                {"id":"monthly16","name":"Monthly (16d/mo)","months":1,"days_per_month":16,"price":900,"duration":"16 days"},
                {"id":"monthly30","name":"Monthly (30d/mo)","months":1,"days_per_month":30,"price":1200,"duration":"30 days"},
                {"id":"quarterly16","name":"Quarterly (16d/mo)","months":3,"days_per_month":16,"price":2400,"duration":"48 days"},
            ]
        self._render_plans(plans)
        # history demo
        rows = [("Monthly (30d/mo)","2025-08-01","2025-08-31","Closed","Yes"), ("Monthly (30d/mo)","2025-07-01","2025-07-31","Closed","Yes")]
        for r in rows:
            row = QFrame(); row.setStyleSheet(f"background-color:{PALETTE['card2']}; border-radius:10px;"); g = QGridLayout(row); g.setContentsMargins(12,8,12,8)
            for i, txt in enumerate(r): g.addWidget(_label(str(txt), color=(PALETTE['text'] if i in (0,3,4) else PALETTE['muted'])), 0, i)
            self.hist_vbox.addWidget(row)
        self.hist_vbox.addStretch(1)

        # preselect first plan
        if plans:
            self._pick_plan(plans[0])

        # dates
        today = dt.date.today(); self.ent_start.setText(today.isoformat()); self.ent_end.setText((today + dt.timedelta(days=29)).isoformat())

    def _render_plans(self, plans: Iterable[Dict[str, Any]]):
        # clear
        while self.plans_grid.count():
            it = self.plans_grid.takeAt(0)
            w = it.widget()
            if w: w.setParent(None)
        # 2 columns responsive
        for i, p in enumerate(plans):
            card = PlanCard(p, on_pick=self._pick_plan, on_edit=self._edit_plan)
            r, c = divmod(i, 2)
            self.plans_grid.addWidget(card, r, c)
            self.plans_grid.setColumnStretch(c, 1)

    def _pick_plan(self, plan: Dict[str, Any]):
        self._picked_plan = plan
        self.ent_plan.setText(plan.get("name",""))
        # recompute end date by months × dpm
        days = self._duration_days(plan)
        try:
            s = dt.date.fromisoformat(self.ent_start.text().strip())
        except Exception:
            s = dt.date.today()
        self.ent_end.setText((s + dt.timedelta(days=max(1, days)-1)).isoformat())
        price = float(plan.get("price", 0) or 0)
        self.ent_price.setText(str(int(price)))
        # refresh pay
        self._recalc_pay()

    def _edit_plan(self, plan: Dict[str, Any]):
        # Placeholder — open a management popup in a future iteration
        print("Edit plan:", plan.get("id") or plan.get("name"))

    def _duration_days(self, plan: Dict[str, Any]) -> int:
        m = plan.get("months"); dpm = plan.get("days_per_month")
        if isinstance(m, (int,float)) and isinstance(dpm, (int,float)) and m>0 and dpm>0:
            return int(m) * int(dpm)
        try:
            return int(str(plan.get("duration","30").split()[0]))
        except Exception:
            return 30

    def _recalc_pay(self):
        try: price = float(self.ent_price.text() or 0)
        except Exception: price = 0.0
        try: disc = float(self.ent_disc.text() or 0)
        except Exception: disc = 0.0
        self.ent_pay.setText(f"{max(0.0, price - disc):.0f}")

    def _submit(self):
        if not self._picked_plan:
            return
        # determine method from segmented
        method = "Cash" if self.btn_cash.isChecked() else ("Card" if self.btn_card.isChecked() else "Transfer")
        payload = {
            "member_id": (self._picked_member or {}).get("id"),
            "plan_id": self._picked_plan.get("id") or self._picked_plan.get("plan_id") or self._picked_plan.get("name"),
            "start": self.ent_start.text().strip(),
            "end": self.ent_end.text().strip(),
            "price": float(self.ent_price.text() or 0),
            "discount": float(self.ent_disc.text() or 0),
            "prorate": bool(self.chk_prorate.isChecked()),
            "method": method,
        }
        if self.services and hasattr(self.services, "subscriptions"):
            try: self.services.subscriptions.create_or_renew(**payload)
            except Exception: pass
        print("Created/Renewed:", payload)

    def _fetch_plans(self) -> List[Dict[str, Any]]:
        if self.services and hasattr(self.services, "plans") and hasattr(self.services.plans, "list"):
            try:
                rows = list(self.services.plans.list()) or []
                out = []
                for r in rows:
                    out.append({
                        "id": r.get("id") or r.get("plan_id") or r.get("name"),
                        "plan_id": r.get("plan_id") or r.get("id"),
                        "name": r.get("name",""),
                        "months": r.get("months"),
                        "days_per_month": r.get("days_per_month"),
                        "duration": r.get("duration",""),
                        "price": float(r.get("price",0) or 0),
                        "description": r.get("description",""),
                    })
                return out
            except Exception:
                pass
        return []

    # ----- navigation -----
    def _open_manage_plans(self):
        try:
            from pages_qt.manage_plans import ManagePlansPage  # type: ignore
        except Exception:
            return
        # Swap to full Manage Plans page using existing layout
        lay = self.layout()
        while lay.count():
            it = lay.takeAt(0); w = it.widget();
            if w: w.setParent(None)
        page = ManagePlansPage(services=self.services, on_back=self._restore_main, parent=self)
        lay.addWidget(page)
        self._manage_page = page

    def _restore_main(self):
        # Recreate original page in place to restore UI reliably
        parent = self.parent()
        services = self.services
        self.deleteLater()
        repl = SubscriptionsPage(services=services, parent=parent)
        parent.layout().addWidget(repl)


if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    try:
        setTheme(Theme.DARK)
    except Exception:
        pass
    root = QWidget(); root.setObjectName("Root"); root.setStyleSheet(f"QWidget#Root {{ background-color: {PALETTE['bg']}; }}"); root.resize(1400, 900)
    page = SubscriptionsPage(services=None, parent=root)
    lay = QVBoxLayout(root); lay.setContentsMargins(0,0,0,0); lay.addWidget(page)
    root.show(); sys.exit(app.exec())
