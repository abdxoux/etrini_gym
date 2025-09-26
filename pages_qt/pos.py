# pos_fluent_match.py
from __future__ import annotations
import sys
from dataclasses import dataclass
from typing import List, Dict

from PyQt6.QtCore import Qt, QSize, QTimer
from PyQt6.QtGui import QColor, QFont
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QGridLayout, QVBoxLayout, QHBoxLayout,
    QLabel, QScrollArea, QFrame, QSizePolicy, QSpacerItem, QGraphicsDropShadowEffect
)

# Fluent Widgets
from qfluentwidgets import (
    setTheme, Theme, setThemeColor, FluentIcon,
    LineEdit, ComboBox, PrimaryPushButton, PushButton, ToolButton,
    InfoBar, InfoBarPosition
)

# ---------------- Brand (old dark identity) ----------------
# Accent blue and dark surfaces to match the legacy style
PRIMARY = QColor("#4f8cff")
PRIMARY_PRESSED = QColor("#3e74d6")
BG = "#151a22"      # window/page surface
CARD = "#1b2130"    # cards/tiles
TEXT = "#e8ecf5"
MUTED = "#8b93a7"
BORDER = "#2a3550"


@dataclass
class Product:
    id: int
    name: str
    category: str
    price: float


# ---------------- Reusable widgets ----------------

class SectionCard(QFrame):
    """Large rounded card like the page container (soft border + radius)."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("SectionCard")
        self.setStyleSheet(f"""
            QFrame#SectionCard {{
                background: {CARD};
                border: 1px solid {BORDER};
                border-radius: 16px;
            }}
        """)
        # Subtle outer shadow to lift the whole panel
        sh = QGraphicsDropShadowEffect(self)
        sh.setBlurRadius(24)
        sh.setOffset(0, 8)
        sh.setColor(QColor(0, 0, 0, 120))
        self.setGraphicsEffect(sh)


class ProductCard(QFrame):
    """Product tile matching the screenshot look."""
    def __init__(self, p: Product, on_add, parent=None):
        super().__init__(parent)
        self.p = p
        self.setObjectName("ProductCard")
        self.setStyleSheet(f"""
            QFrame#ProductCard {{
                background: {CARD};
                border: 1px solid {BORDER};
                border-radius: 12px;
            }}
            QLabel {{ color: {TEXT}; }}
        """)

        # Soft card shadow like the mock
        cardShadow = QGraphicsDropShadowEffect(self)
        cardShadow.setBlurRadius(16)
        cardShadow.setOffset(0, 6)
        cardShadow.setColor(QColor(0, 0, 0, 120))
        self.setGraphicsEffect(cardShadow)

        g = QGridLayout(self)
        g.setContentsMargins(16, 14, 16, 14)
        g.setHorizontalSpacing(8)
        g.setVerticalSpacing(4)

        title = QLabel(p.name)
        title.setFont(QFont("Segoe UI", 11, QFont.Weight.DemiBold))
        sub = QLabel(p.category); sub.setStyleSheet(f"color:{MUTED}")
        price = QLabel(f"{int(p.price):,} DA")
        price.setStyleSheet(f"color:{PRIMARY.name()}; font-weight:600;")

        add = PrimaryPushButton("Add", self)
        add.setFixedHeight(36)
        add.setMinimumWidth(84)
        add.clicked.connect(lambda: on_add(self.p))

        g.addWidget(title, 0, 0, 1, 2)
        g.addWidget(sub,   1, 0, 1, 1)
        g.addWidget(price, 1, 1, 1, 1, alignment=Qt.AlignmentFlag.AlignRight)
        g.addWidget(add,   2, 1, 1, 1, alignment=Qt.AlignmentFlag.AlignRight)


class CartRow(QFrame):
    """Cart row matching the screenshot: name, price, green +/- steppers, and Remove action."""
    def __init__(self, item: Dict, on_inc, on_dec, on_del, parent=None):
        super().__init__(parent)
        self.item = item
        self.on_inc = on_inc
        self.on_dec = on_dec
        self.on_del = on_del

        self.setObjectName("CartRow")
        self.setStyleSheet(f"""
            QFrame#CartRow {{
                background: transparent;
                border: none;
                border-radius: 8px;
            }}
            QLabel {{ color: {TEXT}; }}
        """)
        row = QHBoxLayout(self)
        row.setContentsMargins(0, 12, 0, 12)
        row.setSpacing(10)

        name = QLabel(item["name"])
        name.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        price = QLabel(f"{int(item['price']):,} DA")
        price.setStyleSheet(f"color:{MUTED};")

        # minus
        minus = ToolButton(FluentIcon.REMOVE)
        minus.setFixedSize(QSize(32, 32))
        minus.clicked.connect(lambda: self.on_dec(self.item))
        minus.setStyleSheet(f"""
            QToolButton {{
                border-radius: 16px;
                border: 1px solid {PRIMARY.name()};
                background: {CARD};
                color: {PRIMARY.name()};
            }}
            QToolButton:hover {{ background:#243049; }}
        """)

        qty_lbl = QLabel(str(int(item.get("qty", 1))))
        qty_lbl.setFixedWidth(28)
        qty_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # plus
        plus = ToolButton(FluentIcon.ADD)
        plus.setFixedSize(QSize(32, 32))
        plus.clicked.connect(lambda: self.on_inc(self.item))
        plus.setStyleSheet(f"""
            QToolButton {{
                border-radius: 16px;
                border: 1px solid {PRIMARY.name()};
                background: {PRIMARY.name()};
                color: #FFFFFF;
            }}
            QToolButton:hover {{ background:{PRIMARY_PRESSED.name()}; }}
        """)

        remove = PushButton("Remove")
        remove.setStyleSheet(f"color:{PRIMARY.name()}; background: transparent; border: none;")
        remove.clicked.connect(lambda: self.on_del(self.item))

        row.addWidget(name)
        row.addWidget(price)
        row.addSpacing(6)
        row.addWidget(minus)
        row.addWidget(qty_lbl)
        row.addWidget(plus)
        row.addSpacing(6)
        row.addWidget(remove)


# ---------------- Main window ----------------

class POSWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # Theme
        setTheme(Theme.DARK)
        setThemeColor(PRIMARY)

        self.setWindowTitle("GymPro — POS (Dark)")
        self.resize(1180, 760)

        self._cart: List[Dict] = []

        # Page background
        self.setStyleSheet(f"QMainWindow {{ background: {BG}; }} QLabel {{ color:{TEXT}; }}")

        # Big container card (to get the rounded outer look)
        container = SectionCard(self)
        self.setCentralWidget(container)

        root = QGridLayout(container)
        root.setContentsMargins(20, 20, 20, 20)
        root.setHorizontalSpacing(0)         # thin divider column
        root.setVerticalSpacing(0)
        root.setColumnStretch(0, 65)         # ~65% / divider / 35%
        root.setColumnStretch(1, 0)
        root.setColumnStretch(2, 35)

        # LEFT panel ----------------------------------------------------------
        left = QWidget()
        lg = QGridLayout(left)
        lg.setContentsMargins(20, 20, 20, 20)
        lg.setHorizontalSpacing(16)
        lg.setVerticalSpacing(16)

        title = QLabel("Products")
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.DemiBold))
        lg.addWidget(title, 0, 0, 1, 2)

        # Filters row
        searchWrap = QWidget(); sw = QVBoxLayout(searchWrap); sw.setContentsMargins(0,0,0,0); sw.setSpacing(6)
        sw.addWidget(QLabel("Search"))
        self.search = LineEdit()
        self.search.setPlaceholderText("Name or SKU…")
        sw.addWidget(self.search)

        catWrap = QWidget(); cw = QVBoxLayout(catWrap); cw.setContentsMargins(0,0,0,0); cw.setSpacing(6)
        cw.addWidget(QLabel("Category"))
        self.category = ComboBox()
        self.category.addItems(["All", "Drinks", "Snacks", "Supplements", "Merch"])
        cw.addWidget(self.category)

        lg.addWidget(searchWrap, 1, 0)
        lg.addWidget(catWrap,    1, 1)

        # Products grid (scroll)
        self.prodScroll = QScrollArea()
        self.prodScroll.setWidgetResizable(True)
        self.prodWrap = QWidget()
        self.prodGrid = QGridLayout(self.prodWrap)
        self.prodGrid.setContentsMargins(0, 0, 0, 0)
        self.prodGrid.setHorizontalSpacing(16)
        self.prodGrid.setVerticalSpacing(16)
        self.prodScroll.setWidget(self.prodWrap)
        # Transparent background so the container card shows through
        self.prodScroll.viewport().setStyleSheet("background: transparent;")
        self.prodScroll.setStyleSheet("background: transparent; border: none;")
        lg.addWidget(self.prodScroll, 2, 0, 1, 2)

        # RIGHT panel ---------------------------------------------------------
        right = QWidget()
        rg = QGridLayout(right)
        rg.setContentsMargins(20, 20, 20, 20)
        rg.setHorizontalSpacing(16)
        rg.setVerticalSpacing(16)

        # “Cart” header
        cartTitle = QLabel("Cart")
        cartTitle.setFont(QFont("Segoe UI", 18, QFont.Weight.DemiBold))
        rg.addWidget(cartTitle, 0, 0, 1, 2)

        # Cart list
        self.cartScroll = QScrollArea()
        self.cartScroll.setWidgetResizable(True)
        self.cartWrap = QWidget()
        self.cartVBox = QVBoxLayout(self.cartWrap)
        self.cartVBox.setContentsMargins(0, 0, 0, 0)
        self.cartVBox.setSpacing(0)  # we’ll use dividers
        self.cartScroll.setWidget(self.cartWrap)
        # Transparent background for cart area as well
        self.cartScroll.viewport().setStyleSheet("background: transparent;")
        self.cartScroll.setStyleSheet("background: transparent; border: none;")
        rg.addWidget(self.cartScroll, 1, 0, 1, 2)

        # Horizontal divider before checkout (matches screenshot)
        div = QFrame()
        div.setFrameShape(QFrame.Shape.HLine)
        div.setStyleSheet(f"background:{BORDER}; color:{BORDER};")
        div.setFixedHeight(1)
        rg.addWidget(div, 2, 0, 1, 2)

        # Checkout section
        chkTitle = QLabel("Checkout")
        chkTitle.setFont(QFont("Segoe UI", 18, QFont.Weight.DemiBold))
        rg.addWidget(chkTitle, 3, 0, 1, 2)

        # Total + method
        totalRow = QHBoxLayout()
        totalRow.setContentsMargins(0, 0, 0, 0)
        totalRow.setSpacing(12)

        totalLblTitle = QLabel("Total:")
        totalLblTitle.setFont(QFont("Segoe UI", 12, QFont.Weight.DemiBold))
        self.totalLbl = QLabel("3,830 DA")  # live updated
        self.totalLbl.setFont(QFont("Segoe UI", 12))

        totalRow.addWidget(totalLblTitle)
        totalRow.addWidget(self.totalLbl)
        totalRow.addStretch(1)

        self.method = ComboBox()
        self.method.addItems(["Cash", "Card", "Mobile", "Transfer"])
        self.method.setFixedWidth(160)
        totalRow.addWidget(self.method)

        totalRowW = QWidget(); totalRowW.setLayout(totalRow)
        rg.addWidget(totalRowW, 4, 0, 1, 2)

        # Pay button (full width, green, 12px radius)
        self.payBtn = PrimaryPushButton("Pay")
        self.payBtn.setFixedHeight(46)
        rg.addWidget(self.payBtn, 5, 0, 1, 2)

        # Add both panels with a real divider column between them
        root.addWidget(left, 0, 0)
        vdiv = QFrame(); vdiv.setFrameShape(QFrame.Shape.VLine)
        vdiv.setStyleSheet(f"background:{BORDER}; color:{BORDER};")
        vdiv.setFixedWidth(1)
        root.addWidget(vdiv, 0, 1)
        root.addWidget(right, 0, 2)

        # Data + interactions
        self._products = self._seed_products()
        self._cart: List[Dict] = [
            {"id":100, "name":"Water 500ml",   "price":80,   "qty":1},
            {"id":101, "name":"Protein Bar",   "price":250,  "qty":1},
            {"id":104, "name":"Whey 1kg",      "price":3500, "qty":1},
        ]
        # Debounce search to avoid heavy rebuilds on every keystroke
        self._searchTimer = QTimer(self)
        self._searchTimer.setSingleShot(True)
        self._searchTimer.setInterval(220)
        self._searchTimer.timeout.connect(self.refreshProducts)
        self.search.textChanged.connect(lambda _t=None: self._searchTimer.start())
        self.category.currentIndexChanged.connect(lambda _i: self.refreshProducts())
        self.payBtn.clicked.connect(self.pay)

        self.refreshProducts()
        self.renderCart()

    # ---------------- Data ----------------
    def _seed_products(self) -> List[Product]:
        return [
            Product(100, "Wútter 500ml", "Drinks",       80),
            Product(101, "Protein Bar", "Snacks",       250),
            Product(102, "Energy Drink","Drinks",       220),
            Product(103, "Creatine 300g","Supplements", 1800),
            Product(104, "Whey 1kg",     "Supplements", 3500),
            Product(105, "Shaker 600ml", "Merch",        600),
        ]

    # ---------------- Products grid ----------------
    def refreshProducts(self):
        # clear grid
        while self.prodGrid.count():
            it = self.prodGrid.takeAt(0)
            w = it.widget()
            if w:
                w.setParent(None)

        q = self.search.text().strip().lower()
        cat = self.category.currentText()

        items = []
        for p in self._products:
            if cat != "All" and p.category != cat:
                continue
            if q and q not in p.name.lower():
                continue
            items.append(p)

        # Two columns like screenshot
        for i, p in enumerate(items):
            r, c = divmod(i, 2)
            self.prodGrid.addWidget(ProductCard(p, self.addToCart), r, c)

        # stretch
        self.prodGrid.setRowStretch(self.prodGrid.rowCount(), 1)

    # ---------------- Cart ----------------
    def renderCart(self):
        # clear
        while self.cartVBox.count():
            it = self.cartVBox.takeAt(0)
            w = it.widget()
            if w:
                w.setParent(None)

        total = 0.0
        for i, item in enumerate(self._cart):
            total += item["price"] * item["qty"]
            row = CartRow(item, self._inc, self._dec, self._del)
            self.cartVBox.addWidget(row)

            # thin divider between items
            if i < len(self._cart) - 1:
                div = QFrame(); div.setFrameShape(QFrame.Shape.HLine)
                div.setStyleSheet(f"background:{BORDER}; color:{BORDER};")
                div.setFixedHeight(1)
                self.cartVBox.addWidget(div)

        self.cartVBox.addItem(QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
        self.totalLbl.setText(f"{int(total):,} DA")

    def addToCart(self, p: Product):
        for it in self._cart:
            if it["id"] == p.id:
                it["qty"] += 1
                break
        else:
            self._cart.append({"id": p.id, "name": p.name, "price": p.price, "qty": 1})
        self.renderCart()
        InfoBar.success("Added", f"{p.name} added to cart", position=InfoBarPosition.TOP_RIGHT, parent=self)

    # ---------------- Actions ----------------
    def pay(self):
        if not self._cart:
            InfoBar.warning("Empty cart", "Add items before paying", position=InfoBarPosition.TOP_RIGHT, parent=self)
            return
        payload = {
            "items": self._cart.copy(),
            "total": sum(i["price"] * i["qty"] for i in self._cart),
            "method": self.method.currentText(),
        }
        print("POS Checkout:", payload)
        self._cart.clear()
        self.renderCart()
        InfoBar.success("Payment done", "Checkout completed successfully.", position=InfoBarPosition.TOP_RIGHT, parent=self)

    # ---- Cart quantity ops ----
    def _inc(self, item: Dict):
        item["qty"] += 1
        self.renderCart()

    def _dec(self, item: Dict):
        item["qty"] = max(0, item["qty"] - 1)
        if item["qty"] == 0:
            self._cart = [x for x in self._cart if x is not item]
        self.renderCart()

    def _del(self, item: Dict):
        self._cart = [x for x in self._cart if x is not item]
        self.renderCart()


def main():
    app = QApplication(sys.argv)
    w = POSWindow()
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
