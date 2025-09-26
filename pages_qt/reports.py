# pages_qt/reports.py
# GymPro — Reports (PyQt6 port). Period filters, KPI summary, and results list

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
    QPushButton,
    QLineEdit,
    QComboBox,
    QScrollArea,
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


class KPICard(QFrame):
    def __init__(self, label: str, value: str, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setStyleSheet(f"background-color:{PALETTE['card2']}; border-radius:12px;")
        v = QVBoxLayout(self); v.setContentsMargins(10,8,10,8)
        v.addWidget(_label(label, color=PALETTE['muted']))
        self.value_lbl = _label(value, bold=True, size=16)
        v.addWidget(self.value_lbl)


class ReportRow(QFrame):
    def __init__(self, r: Dict[str, Any], parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setStyleSheet(f"background-color:{PALETTE['card2']}; border-radius:10px;")
        g = QGridLayout(self); g.setContentsMargins(12,8,12,8); g.setHorizontalSpacing(8)
        g.setColumnStretch(0, 16); g.setColumnStretch(1, 12); g.setColumnStretch(2, 12); g.setColumnStretch(3, 12)
        g.addWidget(_label(r.get('date','—')), 0, 0)
        g.addWidget(_label(r.get('type','—'), color=PALETTE['muted']), 0, 1)
        g.addWidget(_label(f"{float(r.get('amount',0)):.0f} DA"), 0, 2)
        g.addWidget(_label(r.get('note',''), color=PALETTE['muted']), 0, 3)


class ReportsPage(QWidget):
    def __init__(self, services: Optional[object] = None, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.services = services

        self.setObjectName("ReportsPage")
        self.setStyleSheet(
            f"""
            QWidget#ReportsPage {{ background-color:{PALETTE['surface']}; }}
            QLabel {{ color:{PALETTE['text']}; }}
            QLineEdit, QComboBox {{ color:{PALETTE['text']}; background-color:{PALETTE['card2']}; border:1px solid {PALETTE['card2']}; border-radius:8px; padding:6px 8px; }}
            QComboBox::drop-down {{ width: 24px; }}
            QComboBox QAbstractItemView {{ background: {PALETTE['card2']}; color: {PALETTE['text']}; selection-background-color: {PALETTE['accent']}; }}
            QPushButton[cssClass='primary'] {{ background-color:{PALETTE['accent']}; color:{PALETTE['text']}; border-radius:14px; height:30px; padding:4px 12px; }}
            QPushButton[cssClass='primary']:hover {{ background-color:#3e74d6; }}
            QPushButton[cssClass='secondary'] {{ background-color:#2a3550; color:{PALETTE['text']}; border-radius:14px; height:30px; padding:4px 12px; }}
            QPushButton[cssClass='secondary']:hover {{ background-color:#334066; }}
            """
        )

        root = QGridLayout(self); root.setContentsMargins(12,12,12,12); root.setHorizontalSpacing(8); root.setVerticalSpacing(8)
        root.setColumnStretch(0, 3); root.setColumnStretch(1, 2)
        root.setRowStretch(2, 1)

        # Filters
        filt = QFrame(); fg = QGridLayout(filt); fg.setContentsMargins(12,10,12,10); fg.setHorizontalSpacing(8)
        fg.addWidget(_label("Period", color=PALETTE['muted']), 0, 0)
        self.opt_period = ComboBox(); self.opt_period.addItems(["Daily","Weekly","Monthly","Custom"]) ; fg.addWidget(self.opt_period, 0, 1)
        fg.addWidget(_label("From", color=PALETTE['muted']), 0, 2); self.ent_from = LineEdit(); self.ent_from.setPlaceholderText(dt.date.today().isoformat()); fg.addWidget(self.ent_from, 0, 3)
        fg.addWidget(_label("To", color=PALETTE['muted']), 0, 4); self.ent_to = LineEdit(); self.ent_to.setPlaceholderText(dt.date.today().isoformat()); fg.addWidget(self.ent_to, 0, 5)
        self.btn_refresh = PushButton("Refresh"); self.btn_refresh.setProperty("cssClass","secondary"); self.btn_refresh.clicked.connect(self._refresh)
        self.btn_export = PrimaryPushButton("Export CSV")
        fg.addWidget(self.btn_refresh, 0, 6); fg.addWidget(self.btn_export, 0, 7)
        head = SectionCard("Reports"); head.layout().addWidget(filt)  # type: ignore
        root.addWidget(head, 0, 0, 1, 2)

        # KPI Summary
        kpis = QFrame(); kg = QGridLayout(kpis); kg.setContentsMargins(0,0,0,0)
        self.k_total_sales = KPICard("Total Sales", "—"); self.k_refunds = KPICard("Refunds", "—"); self.k_net = KPICard("Net", "—")
        self.k_receipts = KPICard("Receipts", "—"); self.k_avg = KPICard("Avg Receipt", "—")
        for i, card in enumerate([self.k_total_sales, self.k_refunds, self.k_net, self.k_receipts, self.k_avg]):
            kg.addWidget(card, 0, i)
        root.addWidget(kpis, 1, 0, 1, 2)

        # Results list
        list_card = SectionCard("Results")
        header = QFrame(); header.setStyleSheet(f"background-color:{PALETTE['card2']}; border-radius:12px;")
        hg = QGridLayout(header); hg.setContentsMargins(10,8,10,8)
        for i, (txt, w) in enumerate([("Date",16),("Type",12),("Amount",12),("Note",32)]):
            hg.addWidget(_label(txt, color=PALETTE['muted']), 0, i); hg.setColumnStretch(i, w)
        list_card.layout().addWidget(header)  # type: ignore
        self.scroll = QScrollArea(); self.scroll.setWidgetResizable(True)
        self.wrap = QWidget(); self.vbox = QVBoxLayout(self.wrap); self.vbox.setContentsMargins(8,6,8,8); self.vbox.setSpacing(6)
        self.scroll.setWidget(self.wrap)
        list_card.layout().addWidget(self.scroll)  # type: ignore
        root.addWidget(list_card, 2, 0, 1, 2)

        self._refresh()

    # ----- data -----
    def _fetch(self) -> Dict[str, Any]:
        if self.services and hasattr(self.services, "reports") and hasattr(self.services.reports, "summary"):
            try:
                data = self.services.reports.summary(
                    period=self.opt_period.currentText(),
                    start=self.ent_from.text().strip() or None,
                    end=self.ent_to.text().strip() or None,
                )
                if data: return data
            except Exception:
                pass
        # demo
        rng = random.Random(2025)
        days = 14
        rows = []
        total = 0
        for i in range(days):
            d = (dt.date.today() - dt.timedelta(days=i)).isoformat()
            typ = rng.choice(["POS","Subscription","Refund"])
            amt = rng.randint(80, 4200)
            total += (amt if typ != "Refund" else -amt)
            rows.append({"date": d, "type": typ, "amount": amt, "note": ""})
        net = total
        refunds = sum(r.get("amount",0) for r in rows if r.get("type") == "Refund")
        receipts = len(rows)
        avg = int(total / max(1, receipts))
        return {"rows": rows, "total": total, "refunds": refunds, "net": net, "receipts": receipts, "avg": avg}

    def _refresh(self):
        data = self._fetch()
        self.k_total_sales.value_lbl.setText(f"{int(data.get('total',0)):,} DA")
        self.k_refunds.value_lbl.setText(f"{int(data.get('refunds',0)):,} DA")
        self.k_net.value_lbl.setText(f"{int(data.get('net',0)):,} DA")
        self.k_receipts.value_lbl.setText(str(int(data.get('receipts',0))))
        self.k_avg.value_lbl.setText(f"{int(data.get('avg',0)):,} DA")
        while self.vbox.count():
            it = self.vbox.takeAt(0); w = it.widget();
            if w: w.setParent(None)
        rows: List[Dict[str, Any]] = data.get("rows", [])
        for r in rows:
            self.vbox.addWidget(ReportRow(r))
        self.vbox.addStretch(1)


if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    try:
        setTheme(Theme.DARK)
    except Exception:
        pass
    root = QWidget(); root.setObjectName("Root"); root.setStyleSheet(f"QWidget#Root {{ background-color: {PALETTE['bg']}; }}"); root.resize(1400, 900)
    page = ReportsPage(services=None, parent=root)
    lay = QVBoxLayout(root); lay.setContentsMargins(0,0,0,0); lay.addWidget(page)
    root.show(); sys.exit(app.exec())
