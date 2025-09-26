# pages_qt/inventory.py
# GymPro — Inventory (PyQt6 port). Products & Stock Moves

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
    QDialog,
    QFormLayout,
    QSpinBox,
    QDoubleSpinBox,
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
        lay.setContentsMargins(16, 14, 16, 12); lay.setSpacing(8)
        lay.addWidget(_label(title, bold=True, size=15))


class Pill(QFrame):
    def __init__(self, text: str, kind: str = "muted", parent: Optional[QWidget] = None):
        super().__init__(parent)
        colors = {"ok": ("#1e3325", PALETTE["ok"]), "warn": ("#33240f", PALETTE["warn"]), "danger": ("#3a1418", PALETTE["danger"]), "muted": ("#2b3344", PALETTE["muted"]) }
        bg, fg = colors.get(kind, colors["muted"])  # type: ignore[index]
        self.setStyleSheet(f"background-color:{bg}; border-radius:999px;")
        lay = QHBoxLayout(self); lay.setContentsMargins(10, 4, 10, 4)
        lay.addWidget(_label(text, color=fg, size=12))


class ProductRow(QFrame):
    def __init__(self, p: Dict[str, Any], on_edit=None, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.p = p; self.on_edit = on_edit
        self.setStyleSheet(f"background-color:{PALETTE['card']}; border-radius:10px;")
        grid = QGridLayout(self); grid.setContentsMargins(12, 8, 12, 8); grid.setHorizontalSpacing(8)
        weights = (30,12,10,14,8)
        for i, w in enumerate(weights): grid.setColumnStretch(i, w)
        name = p.get("name","—"); price = float(p.get("price",0) or 0); stock = int(p.get("stock_qty",0) or 0)
        low = int(p.get("low_stock_threshold",0) or 0); is_active = bool(p.get("is_active", True))
        grid.addWidget(_label(name), 0, 0)
        grid.addWidget(_label(f"{price:.0f} DA", color=PALETTE["muted"]), 0, 1)
        grid.addWidget(_label(str(stock)), 0, 2)
        line = QFrame(); l = QHBoxLayout(line); l.setContentsMargins(0,0,0,0); l.setSpacing(6)
        kind = "ok" if stock > max(low,0) else ("warn" if stock == low else "danger")
        l.addWidget(Pill("Stock ≤ %d" % low if kind != "ok" else "Stock OK", kind))
        l.addWidget(Pill("Active" if is_active else "Inactive", "muted" if is_active else "danger"))
        grid.addWidget(line, 0, 3)
        btn = PushButton("Edit"); btn.setProperty("cssClass","secondary"); btn.setMinimumHeight(28); btn.clicked.connect(lambda: on_edit(p) if on_edit else None)
        grid.addWidget(btn, 0, 4, alignment=Qt.AlignmentFlag.AlignRight)


class MoveRow(QFrame):
    def __init__(self, m: Dict[str, Any], parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setStyleSheet(f"background-color:{PALETTE['card']}; border-radius:10px;")
        grid = QGridLayout(self); grid.setContentsMargins(12,8,12,8); grid.setHorizontalSpacing(8)
        weights = (16,28,14,32)
        for i, w in enumerate(weights): grid.setColumnStretch(i, w)
        grid.addWidget(_label(m.get("date","—")), 0, 0)
        grid.addWidget(_label(m.get("product","—")), 0, 1)
        qty = int(m.get("qty",0) or 0)
        grid.addWidget(_label(str(qty), color=(PALETTE["ok"] if qty>=0 else PALETTE["danger"])), 0, 2)
        grid.addWidget(_label(m.get("note",""), color=PALETTE["muted"]), 0, 3)


class ProductDialog(QDialog):
    def __init__(self, title: str, initial: Optional[Dict[str, Any]], on_submit, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setStyleSheet(f"QDialog {{ background-color:{PALETTE['surface']}; }} QLabel {{ color:{PALETTE['text']}; }}")
        form = QFormLayout(self); form.setContentsMargins(12,12,12,12)
        self.ent_name = LineEdit(); self.ent_name.setPlaceholderText("e.g., Protein Bar"); form.addRow(_label("Name", color=PALETTE["muted"]), self.ent_name)
        self.opt_cat = ComboBox(); self.opt_cat.addItems(["Snacks","Supplements","Drinks","Merch"]); form.addRow(_label("Category", color=PALETTE["muted"]), self.opt_cat)
        self.ent_price = QDoubleSpinBox(); self.ent_price.setRange(0, 10_000_000); self.ent_price.setDecimals(0); form.addRow(_label("Price (DA)", color=PALETTE["muted"]), self.ent_price)
        self.ent_stock = QSpinBox(); self.ent_stock.setRange(0, 1_000_000); form.addRow(_label("Stock Qty", color=PALETTE["muted"]), self.ent_stock)
        self.ent_low = QSpinBox(); self.ent_low.setRange(0, 1_000_000); form.addRow(_label("Low Stock Threshold", color=PALETTE["muted"]), self.ent_low)
        # active toggle as combo for simplicity
        self.opt_active = ComboBox(); self.opt_active.addItems(["Active","Inactive"]); form.addRow(_label("Status", color=PALETTE["muted"]), self.opt_active)
        # buttons
        btns = QHBoxLayout();
        btn_cancel = PushButton("Cancel"); btn_cancel.setProperty("cssClass","secondary"); btn_cancel.clicked.connect(self.reject)
        btn_save = PrimaryPushButton("Save"); btn_save.clicked.connect(lambda: self._submit(on_submit))
        btns.addWidget(btn_cancel); btns.addWidget(btn_save)
        form.addRow(btns)
        # initial
        if initial:
            self.ent_name.setText(str(initial.get("name","")))
            self.opt_cat.setCurrentText(str(initial.get("category","Snacks")))
            self.ent_price.setValue(float(initial.get("price",0) or 0))
            self.ent_stock.setValue(int(initial.get("stock_qty",0) or 0))
            self.ent_low.setValue(int(initial.get("low_stock_threshold",0) or 0))
            self.opt_active.setCurrentText("Active" if bool(initial.get("is_active", True)) else "Inactive")
        self.ent_name.setFocus()

    def _submit(self, on_submit):
        data = {
            "name": (self.ent_name.text() or "").strip(),
            "category": self.opt_cat.currentText(),
            "price": float(self.ent_price.value()),
            "stock_qty": int(self.ent_stock.value()),
            "low_stock_threshold": int(self.ent_low.value()),
            "is_active": (self.opt_active.currentText() == "Active"),
        }
        if not data["name"]:
            return self.reject()
        try:
            on_submit(data)
        finally:
            self.accept()


class InventoryPage(QWidget):
    def __init__(self, services: Optional[object] = None, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.services = services
        self._tab = "Products"
        self._local_products: List[Dict[str, Any]] = []

        self.setObjectName("InventoryPage")
        self.setStyleSheet(
            f"""
            QWidget#InventoryPage {{ background-color:{PALETTE['surface']}; }}
            QLabel {{ color:{PALETTE['text']}; }}
            QLineEdit, QComboBox {{ color:{PALETTE['text']}; background-color:{PALETTE['card2']}; border:1px solid {PALETTE['card2']}; border-radius:8px; padding:6px 8px; }}
            QComboBox::drop-down {{ width: 24px; }}
            QComboBox QAbstractItemView {{ background: {PALETTE['card2']}; color: {PALETTE['text']}; selection-background-color: {PALETTE['accent']}; }}
            QPushButton[cssClass='primary'] {{ background-color:{PALETTE['accent']}; color:{PALETTE['text']}; border-radius:14px; height:30px; padding:4px 12px; }}
            QPushButton[cssClass='primary']:hover {{ background-color:#3e74d6; }}
            QPushButton[cssClass='secondary'] {{ background-color:#2a3550; color:{PALETTE['text']}; border-radius:14px; height:30px; padding:4px 12px; }}
            QPushButton[cssClass='secondary']:hover {{ background-color:#334066; }}
            /* segmented tabs mimic */
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
        root.setColumnStretch(0, 1); root.setRowStretch(3, 1)

        root.addWidget(SectionCard("Inventory — Products & Stock Moves"), 0, 0)

        # top bar
        bar = QFrame(); bar.setStyleSheet(f"background-color:{PALETTE['card']}; border-radius:16px;")
        bgrid = QGridLayout(bar); bgrid.setContentsMargins(12,10,12,10); bgrid.setHorizontalSpacing(8)
        # left: segmented tabs
        tabs = QFrame(); th = QHBoxLayout(tabs); th.setContentsMargins(0,0,0,0); th.setSpacing(6)
        from PyQt6.QtWidgets import QButtonGroup
        self._tab_group = QButtonGroup(self); self._tab_group.setExclusive(True)
        self.btn_products = QPushButton("Products"); self.btn_products.setCheckable(True); self.btn_products.setProperty("seg","tab")
        self.btn_moves = QPushButton("Stock Moves"); self.btn_moves.setCheckable(True); self.btn_moves.setProperty("seg","tab")
        self._tab_group.addButton(self.btn_products); self._tab_group.addButton(self.btn_moves)
        self.btn_products.setChecked(True if self._tab == "Products" else False)
        self.btn_moves.setChecked(True if self._tab == "Stock Moves" else False)
        self.btn_products.clicked.connect(lambda: self._on_tab("Products"))
        self.btn_moves.clicked.connect(lambda: self._on_tab("Stock Moves"))
        th.addWidget(self.btn_products); th.addWidget(self.btn_moves)
        bgrid.addWidget(tabs, 0, 0)
        bgrid.setColumnStretch(1, 1)
        # right: actions
        actions = QFrame(); act = QHBoxLayout(actions); act.setContentsMargins(0,0,0,0)
        self.btn_add = QPushButton("Add Product"); self.btn_add.setProperty("cssClass","primary"); self.btn_add.clicked.connect(self._add_product)
        self.btn_export = QPushButton("Export CSV"); self.btn_export.setProperty("cssClass","secondary"); self.btn_export.clicked.connect(self._export_products_csv)
        act.addWidget(self.btn_add); act.addWidget(self.btn_export)
        bgrid.addWidget(actions, 0, 2, alignment=Qt.AlignmentFlag.AlignRight)
        root.addWidget(bar, 1, 0)

        # filter panel (changes per tab)
        self.filter_panel = QFrame(); self.filter_panel.setStyleSheet(f"background-color:{PALETTE['card']}; border-radius:16px;")
        root.addWidget(self.filter_panel, 2, 0)
        self._build_filters_products()

        # content area
        self.content = QFrame(); cgrid = QGridLayout(self.content); cgrid.setContentsMargins(0,0,0,0)
        root.addWidget(self.content, 3, 0)

        self.header_card = SectionCard("Results")
        cgrid.addWidget(self.header_card, 0, 0)
        self.scroll = QScrollArea(); self.scroll.setWidgetResizable(True)
        self.list_container = QWidget(); self.list_vbox = QVBoxLayout(self.list_container); self.list_vbox.setContentsMargins(0,0,0,0); self.list_vbox.setSpacing(6)
        self.scroll.setWidget(self.list_container)
        cgrid.addWidget(self.scroll, 1, 0)

        # initial
        self._render_products_header(); self._refresh_products()

    def _clear_filters(self):
        layout = self.filter_panel.layout()
        if layout is None:
            layout = QGridLayout(self.filter_panel)
        else:
            while layout.count():
                item = layout.takeAt(0); w = item.widget();
                if w: w.setParent(None)
        return layout

    def _build_filters_products(self):
        grid = self._clear_filters(); grid.setContentsMargins(12,10,12,10); grid.setHorizontalSpacing(8)
        grid.addWidget(_label("Search", color=PALETTE["muted"]), 0, 0)
        self.ent_q = LineEdit(); self.ent_q.setPlaceholderText("Name or SKU…"); self.ent_q.textChanged.connect(lambda _t: self._refresh_products())
        grid.addWidget(self.ent_q, 0, 1)
        grid.addWidget(_label("Category", color=PALETTE["muted"]), 0, 2)
        self.opt_cat = ComboBox(); self.opt_cat.addItems(["All","Snacks","Supplements","Drinks","Merch"]); self.opt_cat.currentIndexChanged.connect(lambda _i: self._refresh_products())
        grid.addWidget(self.opt_cat, 0, 3)
        btn = PushButton("Refresh"); btn.setProperty("cssClass","secondary"); btn.clicked.connect(self._refresh_products)
        grid.addWidget(btn, 0, 4, alignment=Qt.AlignmentFlag.AlignRight)
        grid.setColumnStretch(1, 1); grid.setColumnStretch(4, 1)

    def _build_filters_moves(self):
        grid = self._clear_filters(); grid.setContentsMargins(12,10,12,10); grid.setHorizontalSpacing(8)
        grid.addWidget(_label("Limit", color=PALETTE["muted"]), 0, 0)
        self.ent_limit = LineEdit(); self.ent_limit.setText("100"); self.ent_limit.textChanged.connect(lambda _t: self._refresh_moves())
        grid.addWidget(self.ent_limit, 0, 1)
        btn = PushButton("Refresh"); btn.setProperty("cssClass","secondary"); btn.clicked.connect(self._refresh_moves)
        grid.addWidget(btn, 0, 4, alignment=Qt.AlignmentFlag.AlignRight)
        grid.setColumnStretch(1, 1); grid.setColumnStretch(4, 1)

    def _on_tab(self, name: str):
        if name == self._tab:
            return
        self._tab = name
        if name == "Products":
            self._build_filters_products(); self._render_products_header(); self._refresh_products()
        else:
            self._build_filters_moves(); self._render_moves_header(); self._refresh_moves()

    def _render_products_header(self):
        # clear header rows
        while self.header_card.layout().count() > 1:
            item = self.header_card.layout().takeAt(1); w = item.widget();
            if w: w.setParent(None)
        hdr = QFrame(); hdr.setStyleSheet(f"background-color:{PALETTE['card2']}; border-radius:12px;")
        h = QGridLayout(hdr); h.setContentsMargins(10,8,10,8)
        labels = ("Product", "Price", "Stock", "Status", ""); weights = (30,12,10,14,8)
        for i, (txt, w) in enumerate(zip(labels, weights)):
            h.addWidget(_label(txt, color=PALETTE["muted"]), 0, i); h.setColumnStretch(i, w)
        self.header_card.layout().addWidget(hdr)  # type: ignore

    def _render_moves_header(self):
        while self.header_card.layout().count() > 1:
            item = self.header_card.layout().takeAt(1); w = item.widget();
            if w: w.setParent(None)
        hdr = QFrame(); hdr.setStyleSheet(f"background-color:{PALETTE['card2']}; border-radius:12px;")
        h = QGridLayout(hdr); h.setContentsMargins(10,8,10,8)
        labels = ("Date", "Product", "Qty", "Note"); weights = (16,28,14,32)
        for i, (txt, w) in enumerate(zip(labels, weights)):
            h.addWidget(_label(txt, color=PALETTE["muted"]), 0, i); h.setColumnStretch(i, w)
        self.header_card.layout().addWidget(hdr)  # type: ignore

    # ----- product actions -----
    def _add_product(self):
        def submit(data: Dict[str, Any]):
            if self.services and hasattr(self.services, "create_product"):
                try:
                    self.services.create_product(data); self._refresh_products(); return
                except Exception:
                    pass
            data = dict(data); data["id"] = (max([p.get("id", 0) for p in self._local_products], default=100) + 1)
            self._local_products.append(data); self._refresh_products()
        dlg = ProductDialog("Add Product", None, submit, self)
        dlg.exec()

    def _edit_product(self, p: Dict[str, Any]):
        def submit(data: Dict[str, Any]):
            pid = p.get("id")
            if self.services and hasattr(self.services, "edit_product"):
                try:
                    self.services.edit_product(pid, data); self._refresh_products(); return
                except Exception:
                    pass
            for i, item in enumerate(self._local_products):
                if item.get("id") == pid:
                    upd = dict(item); upd.update(data); self._local_products[i] = upd; break
            else:
                data = dict(data); data["id"] = pid; self._local_products.append(data)
            self._refresh_products()
        dlg = ProductDialog("Edit Product", p, submit, self)
        dlg.exec()

    def _export_products_csv(self):
        # This is a placeholder; implement using QFileDialog if needed
        print("Export CSV clicked; implement QFileDialog flow as needed.")

    # ----- product data -----
    def _fetch_products(self, q: str, category: Optional[str]) -> List[Dict[str, Any]]:
        if self.services and hasattr(self.services, "find_products"):
            try:
                data = self.services.find_products(q, category) or []
                out: List[Dict[str, Any]] = []
                for p in data:
                    out.append({
                        "id": p.get("id"),
                        "name": p.get("name",""),
                        "price": float(p.get("price",0) or 0),
                        "stock_qty": int(p.get("stock_qty",0) or 0),
                        "low_stock_threshold": int(p.get("low_stock_threshold",0) or 0),
                        "is_active": bool(p.get("is_active", True)),
                        "category": p.get("category",""),
                    })
                return out
            except Exception:
                pass
        if self._local_products:
            items = self._local_products.copy()
        else:
            rng = random.Random(1337)
            names = [
                ("Water 500ml","Drinks"), ("Protein Bar","Snacks"), ("Creatine 300g","Supplements"),
                ("Gym Towel","Merch"), ("Shaker 600ml","Merch"), ("Energy Drink","Drinks"),
                ("Whey 1kg","Supplements"), ("BCAA 400g","Supplements"),
            ]
            items = []
            base_id = 100
            for i, (n, cat) in enumerate(names):
                items.append({
                    "id": base_id+i, "name": n, "category": cat,
                    "price": random.choice([80,120,250,600,950,1800,2200,3500]),
                    "stock_qty": random.randint(0, 30),
                    "low_stock_threshold": random.choice([3,5,8,10]),
                    "is_active": random.random() > 0.05,
                })
            self._local_products = items.copy()
        if category:
            items = [p for p in items if p.get("category") == category]
        ql = (q or "").lower().strip()
        if ql:
            items = [p for p in items if ql in p.get("name", "").lower()]
        return items

    def _refresh_products(self):
        # clear list
        while self.list_vbox.count():
            it = self.list_vbox.takeAt(0); w = it.widget();
            if w: w.setParent(None)
        # low stock alerts via service (optional)
        alerts = []
        if self.services and hasattr(self.services, "low_stock_alerts"):
            try:
                data = self.services.low_stock_alerts() or []
                alerts = [f"{a.get('name','?')} ({int(a.get('stock_qty',0))}/{int(a.get('low_stock_threshold',0))})" for a in data][:3]
            except Exception:
                alerts = []
        if alerts:
            bar = QFrame(); hb = QHBoxLayout(bar); hb.setContentsMargins(12,0,12,0)
            hb.addWidget(_label("Low Stock:", color=PALETTE["warn"]))
            hb.addWidget(_label(" · ".join(alerts), color=PALETTE["muted"]))
            self.list_vbox.addWidget(bar)
        # header
        self._render_products_header()
        # list
        q = (self.ent_q.text() or "").strip()
        v = self.opt_cat.currentText().strip(); cat = None if v == "All" else v
        products = self._fetch_products(q, cat)
        if not products:
            self.list_vbox.addWidget(_label("No products found", color=PALETTE["muted"]))
            return
        for p in products:
            self.list_vbox.addWidget(ProductRow(p, on_edit=self._edit_product))

    # ----- moves data -----
    def _fetch_moves(self, limit: int) -> List[Dict[str, Any]]:
        if self.services and hasattr(self.services, "stock_moves"):
            try:
                data = self.services.stock_moves(limit=limit) or []
                out: List[Dict[str, Any]] = []
                for m in data:
                    out.append({"date": m.get("date",""), "product": m.get("product",""), "qty": int(m.get("qty",0) or 0), "note": m.get("note","")})
                return out[:max(1, limit)]
            except Exception:
                pass
        rng = random.Random(limit * 37 + 7)
        names = ["Water 500ml","Protein Bar","Creatine 300g","Shaker 600ml","Towel","Energy Drink"]
        out = []
        now = dt.datetime.now()
        for i in range(max(1, min(200, limit))):
            ts = (now - dt.timedelta(hours=i)).strftime("%Y-%m-%d %H:%M")
            qty = rng.choice([+12,+6,+3,-1,-2,-3,-5,-8])
            note = "restock" if qty>0 else "sale"
            out.append({"date": ts, "product": rng.choice(names), "qty": qty, "note": note})
        return out

    def _render_moves(self, moves: List[Dict[str, Any]]):
        while self.list_vbox.count():
            it = self.list_vbox.takeAt(0); w = it.widget();
            if w: w.setParent(None)
        self._render_moves_header()
        if not moves:
            self.list_vbox.addWidget(_label("No stock moves", color=PALETTE["muted"]))
            return
        for m in moves:
            self.list_vbox.addWidget(MoveRow(m))

    def _refresh_moves(self):
        try:
            limit = int((self.ent_limit.text() or "100").strip())
        except Exception:
            limit = 100
        self._render_moves(self._fetch_moves(limit))


if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    try:
        setTheme(Theme.DARK)
    except Exception:
        pass
    root = QWidget(); root.setObjectName("Root"); root.setStyleSheet(f"QWidget#Root {{ background-color: {PALETTE['bg']}; }}")
    root.resize(1200, 720)
    page = InventoryPage(services=None, parent=root)
    lay = QVBoxLayout(root); lay.setContentsMargins(0,0,0,0); lay.addWidget(page)
    root.show(); sys.exit(app.exec())
