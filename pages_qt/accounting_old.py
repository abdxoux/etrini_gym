# pages_qt/accounting_old.py
# Legacy Accounting page (old visual identity: dark surface)

from __future__ import annotations

import datetime as dt
import random
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
    QDateEdit,
)


def _label(text: str, *, color: str | None = None, bold: bool = False, size: int = 13) -> QLabel:
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
        lay.setContentsMargins(16, 12, 16, 10)
        lay.setSpacing(8)
        lay.addWidget(_label(title, bold=True, size=15))


class Kpi(QFrame):
    def __init__(self, label: str, value: str = "—", parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setStyleSheet(f"background-color:{PALETTE['card2']}; border-radius:12px;")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(10, 8, 10, 8)
        lay.addWidget(_label(label, color=PALETTE["muted"], size=12))
        self.val = _label(value, bold=True, size=16)
        lay.addWidget(self.val)


class Pill(QFrame):
    def __init__(self, text: str, kind: str = "muted", parent: Optional[QWidget] = None):
        super().__init__(parent)
        colors = {
            "ok": PALETTE["ok"],
            "warn": PALETTE["warn"],
            "danger": PALETTE["danger"],
            "muted": PALETTE["muted"],
        }
        self.setStyleSheet("background: transparent;")
        self.h = QHBoxLayout(self)
        self.h.setContentsMargins(10, 4, 10, 4)
        self.h.setSpacing(0)
        self.lbl = QLabel(text)
        self.lbl.setStyleSheet(
            f"color:{colors.get(kind, PALETTE['muted'])}; font-family:'Segoe UI'; font-size:13px;"
        )
        self.h.addWidget(self.lbl)
    def setText(self, text: str, kind: str = "muted"):
        colors = {
            "ok": PALETTE["ok"],
            "warn": PALETTE["warn"],
            "danger": PALETTE["danger"],
            "muted": PALETTE["muted"],
        }
        self.lbl.setText(text)
        self.lbl.setStyleSheet(
            f"color:{colors.get(kind, PALETTE['muted'])}; font-family:'Segoe UI'; font-size:13px;"
        )

class InvoiceRow(QFrame):
    def __init__(self, inv: Dict[str, Any], parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setStyleSheet(f"background-color:{PALETTE['card2']}; border-radius:10px;")
        grid = QGridLayout(self)
        grid.setContentsMargins(12, 6, 12, 6)
        grid.setHorizontalSpacing(8)
        cols = ("no","date","typ","who","method","total","paid","status")
        colors = [PALETTE["text"], PALETTE["muted"], PALETTE["muted"], PALETTE["text"],
                  PALETTE["muted"], PALETTE["text"], PALETTE["text"], PALETTE["ok"]]
        status = (inv.get("status") or "open")
        if status == "partial": colors[-1] = PALETTE["warn"]
        if status == "open": colors[-1] = PALETTE["danger"]
        vals = (
            inv.get("no","—"), inv.get("date","—"), inv.get("typ","—"), inv.get("who","—"),
            inv.get("method","—"), f"{float(inv.get('total',0)):.0f}", f"{float(inv.get('paid',0)):.0f}", status
        )
        weights = (10,16,10,26,12,12,12,10)
        for i, (k, col, w) in enumerate(zip(vals, colors, weights)):
            grid.addWidget(_label(str(k), color=col), 0, i)
            grid.setColumnStretch(i, w)


def week_range(anchor: dt.date) -> Tuple[dt.date, dt.date]:
    start = anchor - dt.timedelta(days=(anchor.weekday()))
    end = start + dt.timedelta(days=6)
    return start, end


def month_range(anchor: dt.date) -> Tuple[dt.date, dt.date]:
    start = anchor.replace(day=1)
    if start.month == 12:
        end = start.replace(month=12, day=31)
    else:
        end = (start.replace(month=start.month+1, day=1) - dt.timedelta(days=1))
    return start, end


class AccountingPage(QWidget):
    def __init__(self, services: Optional[object] = None, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.services = services
        self._period = "Daily"
        self.setObjectName("AccountingPage")
        self.setStyleSheet(
            f"""
            QWidget#AccountingPage {{ background-color: {PALETTE['surface']}; }}
            QLabel {{ color: {PALETTE['text']}; }}
            QLineEdit, QComboBox {{
                color: {PALETTE['text']}; background-color: {PALETTE['card2']};
                border:1px solid {PALETTE['card2']}; border-radius:8px; padding:6px 8px;
            }}
            QComboBox::drop-down {{ width: 24px; }}
            QComboBox QAbstractItemView {{
                background: {PALETTE['card2']}; color: {PALETTE['text']};
                selection-background-color: {PALETTE['accent']};
            }}
            QPushButton[cssClass="primary"] {{ background-color:{PALETTE['accent']}; color:{PALETTE['text']}; border-radius:14px; height:26px; padding:4px 10px; }}
            QPushButton[cssClass="primary"]:hover {{ background-color:#3e74d6; }}
            QPushButton[cssClass="secondary"] {{ background-color:#2a3550; color:{PALETTE['text']}; border-radius:14px; height:26px; padding:4px 10px; }}
            QPushButton[cssClass="secondary"]:hover {{ background-color:#334066; }}
            """
        )

        root = QGridLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setHorizontalSpacing(12)
        root.setVerticalSpacing(12)
        root.setColumnStretch(0, 3)
        root.setColumnStretch(1, 2)
        root.setRowStretch(0, 1)

        # LEFT — Invoices
        left = QFrame()
        left.setStyleSheet("background: transparent;")
        lgrid = QGridLayout(left)
        lgrid.setContentsMargins(0, 0, 0, 0)
        lgrid.setVerticalSpacing(8)
        lgrid.setColumnStretch(0, 1)

        lgrid.addWidget(SectionCard("Invoices"), 0, 0)

        filters = QFrame()
        filters.setStyleSheet(f"background-color:{PALETTE['card']}; border-radius:16px;")
        fgrid = QGridLayout(filters)
        fgrid.setContentsMargins(12, 8, 12, 8)
        fgrid.setHorizontalSpacing(8)
        for i in range(8):
            fgrid.setColumnStretch(i, 1)

        fgrid.addWidget(_label("Search", color=PALETTE["muted"]), 0, 0)
        self.ent_q = QLineEdit(); self.ent_q.setPlaceholderText("Member, #, method…")
        self.ent_q.textChanged.connect(lambda _t: self._refresh_invoices())
        fgrid.addWidget(self.ent_q, 0, 1, 1, 3)

        fgrid.addWidget(_label("Status", color=PALETTE["muted"]), 0, 4)
        self.opt_status = QComboBox(); self.opt_status.addItems(["Any","open","partial","paid"]) ; self.opt_status.currentIndexChanged.connect(lambda _i: self._refresh_invoices())
        fgrid.addWidget(self.opt_status, 0, 5)

        fgrid.addWidget(_label("Method", color=PALETTE["muted"]), 0, 6)
        self.opt_method = QComboBox(); self.opt_method.addItems(["Any","Cash","Card","Mobile","Transfer"]) ; self.opt_method.currentIndexChanged.connect(lambda _i: self._refresh_invoices())
        fgrid.addWidget(self.opt_method, 0, 7)

        lgrid.addWidget(filters, 1, 0)

        list_card = SectionCard("Results")
        lgrid.addWidget(list_card, 2, 0)
        header = QFrame(); header.setStyleSheet(f"background-color:{PALETTE['card2']}; border-radius:12px;")
        hgrid = QGridLayout(header)
        hgrid.setContentsMargins(10, 6, 10, 6)
        labels = ("No.", "Date", "Type", "Member/Walk-in", "Method", "Total", "Paid", "Status")
        weights = (10,16,10,26,12,12,12,10)
        for i, (txt, w) in enumerate(zip(labels, weights)):
            hgrid.addWidget(_label(txt, color=PALETTE["muted"]), 0, i)
            hgrid.setColumnStretch(i, w)
        list_card.layout().addWidget(header)  # type: ignore

        self.inv_scroll = QScrollArea(); self.inv_scroll.setWidgetResizable(True)
        self.inv_wrap = QWidget(); self.inv_vbox = QVBoxLayout(self.inv_wrap)
        self.inv_vbox.setContentsMargins(8, 6, 8, 8); self.inv_vbox.setSpacing(6)
        self.inv_scroll.setWidget(self.inv_wrap)
        list_card.layout().addWidget(self.inv_scroll)  # type: ignore

        root.addWidget(left, 0, 0)

        # RIGHT — Z-Report
        right = QFrame(); rgrid = QGridLayout(right)
        rgrid.setContentsMargins(0, 0, 0, 0)
        rgrid.setVerticalSpacing(8)
        rgrid.setColumnStretch(0, 1)

        rgrid.addWidget(SectionCard("Z-Report — Sales Snapshot"), 0, 0)

        # Date range bar
        zbar = QFrame(); zbar.setStyleSheet(f"background-color:{PALETTE['card']}; border-radius:16px;")
        zb = QGridLayout(zbar); zb.setContentsMargins(12, 8, 12, 8); zb.setHorizontalSpacing(8)
        zb.addWidget(_label("From", color=PALETTE["muted"]), 0, 0)
        self.dt_from = QDateEdit(); self.dt_from.setCalendarPopup(True); self.dt_from.setDisplayFormat("yyyy-MM-dd")
        self.dt_from.setDate(dt.date.today().replace(day=1))
        zb.addWidget(self.dt_from, 0, 1)
        zb.addWidget(_label("To", color=PALETTE["muted"]), 0, 2)
        self.dt_to = QDateEdit(); self.dt_to.setCalendarPopup(True); self.dt_to.setDisplayFormat("yyyy-MM-dd")
        self.dt_to.setDate(dt.date.today())
        zb.addWidget(self.dt_to, 0, 3)
        btn_refresh = QPushButton("Refresh"); btn_refresh.setProperty("cssClass","secondary"); btn_refresh.clicked.connect(self._refresh_z); zb.addWidget(btn_refresh, 0, 5)
        rgrid.addWidget(zbar, 1, 0)

        # KPIs
        kwrap = QFrame(); kgrid = QGridLayout(kwrap); kgrid.setContentsMargins(0, 0, 0, 0)
        self.k_pos = Kpi("POS Gross"); self.k_sub = Kpi("Subscriptions Gross"); self.k_ref = Kpi("Refunds"); self.k_net = Kpi("Net")
        for i, k in enumerate((self.k_pos, self.k_sub, self.k_ref, self.k_net)):
            kgrid.addWidget(k, 0, i)
        rgrid.addWidget(kwrap, 2, 0)

        methods = QFrame(); mh = QHBoxLayout(methods); mh.setContentsMargins(0, 0, 0, 0); mh.setSpacing(8)
        self.k_cnt = Kpi("Receipts")
        mh.addWidget(self.k_cnt)
        wrap = QFrame(); wh = QHBoxLayout(wrap); wh.setContentsMargins(0,0,0,0); wh.setSpacing(6)
        self.p_cash = Pill("Cash 0", "muted")
        self.p_card = Pill("Card 0", "muted")
        self.p_trn = Pill("Transfer 0", "muted")
        wh.addWidget(self.p_cash); wh.addWidget(self.p_card); wh.addWidget(self.p_trn)
        mh.addWidget(wrap, alignment=Qt.AlignmentFlag.AlignRight)
        rgrid.addWidget(methods, 3, 0)

        notes = SectionCard("Notes")
        self.lbl_range = _label("", color=PALETTE["muted"]) ; notes.layout().addWidget(self.lbl_range)  # type: ignore
        rgrid.addWidget(notes, 4, 0)

        root.addWidget(right, 0, 1)

        # initial loads
        self._refresh_invoices()
        self._refresh_z()

    # ----- invoices -----
    def _fetch_invoices(self, q: str, status: Optional[str], method: Optional[str]) -> List[Dict[str, Any]]:
        if self.services and hasattr(self.services, "accounting"):
            try:
                return self.services.accounting.search_invoices(q, status or "Any", method or "Any", limit=120) or []
            except Exception:
                pass
        rng = random.Random(hash(q + (status or "") + (method or "")) & 0xffffffff)
        names = ["Walk-in","Jane Doe","Samir B.","A. Karim","John Lee"]
        meth  = ["Cash","Card","Transfer"]
        out=[]
        today = dt.date.today()
        for i in range(48):
            d = today - dt.timedelta(days=rng.randint(0,6))
            m = rng.choice(meth)
            st = rng.choice(["open","partial","paid"])
            if status and status!="Any" and st!=status: continue
            if method and method!="Any" and m!=method: continue
            who = rng.choice(names)
            if q and (q.lower() not in who.lower() and q.lower() not in str(i)): continue
            typ = rng.choice(["POS","Subscription"])
            base = rng.choice([80,250,600,1200,2200,3500,5400]) if typ=="POS" else rng.choice([1200,1800,2200,3500,4500])
            total = base; paid = total if st=="paid" else (total//2 if st=="partial" else 0)
            out.append({
                "no": f"INV-{d.strftime('%y%m%d')}-{i:03d}",
                "date": d.strftime("%Y-%m-%d"),
                "typ": typ,
                "who": who,
                "method": m,
                "total": total,
                "paid": paid,
                "status": st
            })
        return out

    def _refresh_invoices(self):
        q = (self.ent_q.text() or "").strip()
        status = self.opt_status.currentText().strip()
        method = self.opt_method.currentText().strip()
        data = self._fetch_invoices(q, None if status=="Any" else status, None if method=="Any" else method)
        # render
        while self.inv_vbox.count():
            item = self.inv_vbox.takeAt(0)
            w = item.widget()
            if w: w.setParent(None)
        if not data:
            self.inv_vbox.addWidget(_label("No invoices", color=PALETTE["muted"]))
        else:
            for inv in data[:24]:
                self.inv_vbox.addWidget(InvoiceRow(inv))

    # ----- z report -----
    def _on_period_change(self, val: str):
        # deprecated (kept for compatibility)
        self._refresh_z()

    def _parse_range(self) -> tuple[dt.date, dt.date]:
        try:
            s = self.dt_from.date().toPyDate()  # type: ignore[attr-defined]
            e = self.dt_to.date().toPyDate()    # type: ignore[attr-defined]
        except Exception:
            s = dt.date.today().replace(day=1)
            e = dt.date.today()
        if e < s:
            s, e = e, s
        return s, e

    def _resolve_range(self, anchor: dt.date) -> Tuple[dt.date, dt.date]:
        if self._period == "Weekly":
            return week_range(anchor)
        if self._period == "Monthly":
            return month_range(anchor)
        return anchor, anchor

    def _fetch_z_range(self, start: dt.date, end: dt.date) -> Dict[str, Any]:
        if self.services and hasattr(self.services, "accounting"):
            # prefer a range API if available
            try:
                if hasattr(self.services.accounting, "z_report_range"):
                    data = self.services.accounting.z_report_range(start, end)
                    if data: return data
            except Exception:
                pass
        rng = random.Random(hash((start.toordinal(), end.toordinal())) & 0xffffffff)
        days = (end - start).days + 1
        pos_gross = sum(rng.randint(8000, 30000) for _ in range(days))
        sub_gross = sum(rng.randint(4000, 18000) for _ in range(days))
        refunds = sum(rng.choice([0,0,0, rng.randint(0, 3000)]) for _ in range(days))
        gross = pos_gross + sub_gross
        net = max(0, gross - refunds)
        cash = int(net * rng.uniform(0.25, 0.55))
        card = int(net * rng.uniform(0.15, 0.35))
        transfer = max(0, net - cash - card)
        count = rng.randint(12*days, 80*days)
        return {"period": "Range", "start": start, "end": end,
                "pos_gross": pos_gross, "sub_gross": sub_gross, "refunds": refunds, "net": net,
                "cash": cash, "card": card, "transfer": transfer, "count": count}

    def _refresh_z(self):
        start, end = self._parse_range()
        data = self._fetch_z_range(start, end)
        self.k_pos.val.setText(f"{data.get('pos_gross',0):,} DA")
        self.k_sub.val.setText(f"{data.get('sub_gross',0):,} DA")
        self.k_ref.val.setText(f"{data.get('refunds',0):,} DA")
        self.k_net.val.setText(f"{data.get('net',0):,} DA")
        self.k_cnt.val.setText(str(data.get('count',0)))
        self.p_cash.setText(f"Cash {int(data.get('cash',0))}", "muted")
        self.p_card.setText(f"Card {int(data.get('card',0))}", "muted")
        self.p_trn.setText(f"Transfer {int(data.get('transfer',0))}", "muted")
        if start == end:
            self.lbl_range.setText(f"{start.isoformat()}")
        else:
            self.lbl_range.setText(f"{start.isoformat()} → {end.isoformat()}")


def main():
    import sys
    app = QApplication(sys.argv)
    root = QWidget(); root.setObjectName("Root"); root.setStyleSheet(f"QWidget#Root {{ background-color: {PALETTE['bg']}; }}")
    root.resize(1400, 860)
    page = AccountingPage(services=None, parent=root)
    lay = QVBoxLayout(root); lay.setContentsMargins(0,0,0,0); lay.addWidget(page)
    root.show(); sys.exit(app.exec())


if __name__ == "__main__":
    main()
