# pages/dashboard_qt.py
# GymPro — DashboardPage (PyQt6 port preserving UI identity)
# Requires: PyQt6 (pip install PyQt6)

from __future__ import annotations

from typing import List, Optional, Any
from datetime import date

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
    "accent2":  "#8b6cff",
    "muted":    "#8b93a7",
    "text":     "#e8ecf5",
    "ok":       "#22c55e",
    "warn":     "#f59e0b",
    "danger":   "#ef4444",
}

from PyQt6.QtCore import Qt, QRectF, QSize
from PyQt6.QtGui import QColor, QPainter
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
    QSizePolicy,
    QSplitter,
)
from qfluentwidgets import setTheme, Theme, LineEdit, PrimaryPushButton, PushButton


def _styled_label(text: str, size: int = 15, bold: bool = True) -> QLabel:
    lbl = QLabel(text)
    weight = 600 if bold else 400
    lbl.setStyleSheet(
        f"color: {PALETTE['text']}; font-family: 'Segoe UI'; font-size: {size}px; font-weight: {weight};"
    )
    return lbl


class Card(QFrame):
    def __init__(self, title: str = "", parent: Optional[QWidget] = None, *, corner_radius: int = 16, fg: Optional[str] = None):
        super().__init__(parent)
        self.setObjectName("Card")
        self.setStyleSheet(
            f"""
            QFrame#Card {{
                background-color: {fg or PALETTE['card']};
                border-radius: {corner_radius}px;
            }}
            """
        )
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self.layout_v = QVBoxLayout(self)
        self.layout_v.setContentsMargins(12, 12, 12, 12)
        self.layout_v.setSpacing(8)
        if title:
            self.layout_v.addWidget(_styled_label(title, size=15, bold=True))


class KPICard(Card):
    def __init__(self, label: str, value: str, *, pill: Optional[str] = None, parent: Optional[QWidget] = None):
        super().__init__(title="", parent=parent, fg=PALETTE["card"])  # keep same color identity
        # Title
        self.layout_v.addWidget(_styled_label(label, size=15, bold=True))
        # Value
        self.value_lbl = _styled_label(value, size=26, bold=True)
        self.layout_v.addWidget(self.value_lbl)
        # Optional pill/tag
        if pill:
            pill_frame = QFrame()
            pill_frame.setStyleSheet(
                f"background-color: {PALETTE['card2']}; border-radius: 999px;"
            )
            pill_layout = QHBoxLayout(pill_frame)
            pill_layout.setContentsMargins(12, 4, 12, 4)
            pill_layout.addWidget(_styled_label(pill, size=12, bold=False))
            self.layout_v.addWidget(pill_frame)


class TinyBars(QWidget):
    """Fast mini bar chart (Painter) that responds to parent resize."""
    def __init__(self, values: List[float], *, min_h: int = 160, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.values = values
        self.setAutoFillBackground(False)
        # responsive sizing
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMinimumHeight(min_h)

    def sizeHint(self) -> QSize:
        return QSize(400, max(160, self.minimumHeight()))

    def paintEvent(self, event):  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        # background
        painter.fillRect(self.rect(), QColor(PALETTE["card"]))

        if not self.values:
            painter.end(); return

        w = max(0, self.width())
        h_total = max(0, self.height())
        m = max(self.values) if max(self.values) != 0 else 1
        n = len(self.values)
        pad, gap = 10.0, 4.0
        barw = (w - pad * 2 - gap * (n - 1)) / max(n, 1)
        max_h = max(0.0, h_total - 30)
        base_y = h_total - 10

        color_top = QColor(PALETTE["accent2"])
        color_bottom = QColor(PALETTE["accent"]) 

        for i, v in enumerate(self.values):
            x0 = pad + i * (barw + gap)
            h = int((v / m) * max_h)
            y0 = base_y - h
            painter.fillRect(QRectF(x0, y0, barw, h * 0.55), color_top)
            painter.fillRect(QRectF(x0, y0 + h * 0.45, barw, h * 0.55), color_bottom)

        painter.end()


class DashboardPage(QWidget):
    def __init__(self, services: Optional[Any] = None, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.services = services
        self.setObjectName("DashboardPage")

        self.setStyleSheet(
            f"""
            QWidget#DashboardPage {{ background-color: {PALETTE['surface']}; }}
            QLabel {{ color: {PALETTE['text']}; }}
            QLineEdit {{
                color: {PALETTE['text']};
                background-color: {PALETTE['card2']};
                border: 1px solid {PALETTE['card2']};
                border-radius: 8px; padding: 6px 8px;
            }}
            QComboBox {{
                color: {PALETTE['text']}; background-color: {PALETTE['card2']};
                border: 1px solid {PALETTE['card2']}; border-radius: 8px; padding: 4px 8px;
            }}
            QComboBox::drop-down {{ width: 24px; }}
            QComboBox QAbstractItemView {{
                background: {PALETTE['card2']}; color: {PALETTE['text']};
                selection-background-color: {PALETTE['accent']};
            }}
            QPushButton[cssClass="primary"] {{
                background-color: {PALETTE['accent']}; color: {PALETTE['text']};
                border-radius: 14px; height: 32px; padding: 4px 12px;
            }}
            QPushButton[cssClass="primary"]:hover {{ background-color: #3e74d6; }}
            QPushButton[cssClass="secondary"] {{
                background-color: #2b3344; color: {PALETTE['text']};
                border-radius: 14px; height: 32px; padding: 4px 12px;
            }}
            QPushButton[cssClass="secondary"]:hover {{ background-color: #38445a; }}
            """
        )

        # 12-column grid (top-level)
        grid = QGridLayout(self)
        grid.setContentsMargins(8, 12, 8, 12)
        grid.setHorizontalSpacing(8)
        grid.setVerticalSpacing(8)
        for i in range(12):
            grid.setColumnStretch(i, 1)

        # KPIs row (row 0)
        self._add_kpis(grid)

        # Splitter for charts (top pane) and bottom section (bottom pane)
        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.setChildrenCollapsible(False)
        charts_pane = self._build_charts_pane()
        bottom_pane = self._build_bottom_pane()
        splitter.addWidget(charts_pane)
        splitter.addWidget(bottom_pane)
        splitter.setSizes([500, 400])  # initial weights
        grid.addWidget(splitter, 1, 0, 1, 12)

    # ----- UI composition -----
    def _add_kpis(self, grid: QGridLayout):
        kpi = self._get_kpis()
        specs = [
            ("Active Members", str(kpi["active_members"])),
            ("Today's Revenue", f"{kpi['today_revenue']:,} DA"),
            ("Unpaid Invoices", str(kpi["unpaid_invoices"])),
            ("Low Stock",       str(kpi["low_stock"])),
            ("In Gym Now",      str(kpi.get("in_gym_now", 0))),
        ]
        # Dedicated container with its own 5-column grid for KPIs
        kpi_container = QFrame()
        kpi_layout = QGridLayout(kpi_container)
        kpi_layout.setContentsMargins(0, 0, 0, 0)
        kpi_layout.setHorizontalSpacing(8)
        for i in range(5):
            kpi_layout.setColumnStretch(i, 1)
        for i, (label, value) in enumerate(specs):
            card = KPICard(label, value, parent=self)
            kpi_layout.addWidget(card, 0, i)
        grid.addWidget(kpi_container, 0, 0, 1, 12)

    def _add_charts(self, grid: QGridLayout):
        # Daily Revenue (30 days)
        card_daily = Card("Daily Revenue (30 days)", parent=self)
        daily_wrap = QVBoxLayout()
        daily_wrap.setContentsMargins(0, 0, 0, 0)
        daily_wrap.setSpacing(0)
        chart1 = TinyBars(self._get_daily_revenue(), min_h=200, parent=card_daily)
        daily_wrap.addWidget(chart1)
        # place into card
        card_daily.layout_v.addLayout(daily_wrap)
        grid.addWidget(card_daily, 1, 0, 1, 7)

        # Monthly Breakdown
        card_month = Card("Monthly Breakdown", parent=self)
        month_wrap = QVBoxLayout()
        month_wrap.setContentsMargins(0, 0, 0, 0)
        month_wrap.setSpacing(0)
        chart2 = TinyBars(self._get_monthly_breakdown(), min_h=200, parent=card_month)
        month_wrap.addWidget(chart2)
        card_month.layout_v.addLayout(month_wrap)
        grid.addWidget(card_month, 1, 7, 1, 5)

    def _add_z_and_alerts(self, grid: QGridLayout):
        # Z-Report (Close Day)
        card_z = Card("Z-Report (Close Day)", parent=self)
        vbox = card_z.layout_v

        date_input = LineEdit()
        date_input.setPlaceholderText(str(date.today()))
        vbox.addWidget(date_input)

        btns = QFrame()
        btns.setStyleSheet("background: transparent;")
        btns_layout = QHBoxLayout(btns)
        btns_layout.setContentsMargins(0, 0, 0, 0)
        btns_layout.setSpacing(8)

        btn_csv = PushButton("Export CSV")
        btn_csv.setProperty("cssClass", "secondary")
        btn_csv.setObjectName("btn_csv")
        btn_csv.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_csv.setMinimumHeight(32)
        btns_layout.addWidget(btn_csv)

        btn_pdf = PrimaryPushButton("Export PDF")
        btn_pdf.setObjectName("btn_pdf")
        btn_pdf.setCursor(Qt.CursorShape.PointingHandCursor)
        btns_layout.addWidget(btn_pdf)

        vbox.addWidget(btns)

        totals_lbl = QLabel(self._z_totals_text())
        totals_lbl.setStyleSheet(f"color: {PALETTE['text']};")
        vbox.addWidget(totals_lbl)

        grid.addWidget(card_z, 2, 0, 1, 7)

        # Low Stock Alerts
        card_alerts = Card("Low Stock Alerts", parent=self)
        self._render_low_stock(card_alerts)
        grid.addWidget(card_alerts, 2, 7, 1, 4)

        # Quick Actions
        qa = Card("Quick Actions", parent=self)
        qa.layout_v.setSpacing(6)
        for t in ("New Member", "Renew", "Take Payment", "Open Gate"):
            b = PushButton(t)
            b.setProperty("cssClass", "secondary")
            b.setMinimumHeight(36)
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            qa.layout_v.addWidget(b)
        grid.addWidget(qa, 2, 11, 1, 1)

    # ----- panes for splitter -----
    def _build_charts_pane(self) -> QWidget:
        wrap = QWidget()
        grid = QGridLayout(wrap)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(8)
        grid.setVerticalSpacing(8)
        for i in range(12):
            grid.setColumnStretch(i, 1)
        # reuse composition
        self._add_charts(grid)
        return wrap

    def _build_bottom_pane(self) -> QWidget:
        wrap = QWidget()
        grid = QGridLayout(wrap)
        grid.setContentsMargins(0, 8, 0, 0)
        grid.setHorizontalSpacing(8)
        grid.setVerticalSpacing(8)
        for i in range(12):
            grid.setColumnStretch(i, 1)
        # reuse composition
        self._add_z_and_alerts(grid)
        return wrap

    # ----- data adapters -----
    def _get_kpis(self):
        try:
            if self.services and hasattr(self.services, "dashboard_summary"):
                v = self.services.dashboard_summary()
                if isinstance(v, dict):
                    return {
                        "active_members": int(v.get("active_members", 0)),
                        "today_revenue":  int(v.get("today_revenue", 0)),
                        "unpaid_invoices": int(v.get("unpaid_invoices", 0)),
                        "low_stock":      int(v.get("low_stock", 0)),
                        "in_gym_now":     int(v.get("in_gym_now", v.get("present_now", 0))),
                    }
        except Exception:
            pass
        low_stock = 0
        if self.services and hasattr(self.services, "low_stock_items"):
            try:
                low_stock = len(self.services.low_stock_items() or [])
            except Exception:
                low_stock = 0
        # demo fallback
        return {"active_members": 312, "today_revenue": 4250, "unpaid_invoices": 7, "low_stock": low_stock, "in_gym_now": 37}

    def _get_daily_revenue(self) -> List[int]:
        try:
            if self.services and hasattr(self.services, "daily_revenue_30"):
                v = self.services.daily_revenue_30()
                if v:
                    return list(v)
        except Exception:
            pass
        base = 15
        return [base + ((i * 7) % 30) for i in range(30)]

    def _get_monthly_breakdown(self) -> List[int]:
        try:
            if self.services and hasattr(self.services, "monthly_breakdown_12"):
                v = self.services.monthly_breakdown_12()
                if v:
                    return list(v)
        except Exception:
            pass
        return [20 + ((i * 11) % 40) for i in range(12)]

    def _z_totals_text(self) -> str:
        try:
            if self.services and hasattr(self.services, "zreport_totals"):
                t = self.services.zreport_totals()
                if isinstance(t, str):
                    return t
        except Exception:
            pass
        return "Payments Total: 152,000 DA   ·   By Method — Cash: 92k · Card: 44k · Mobile: 16k"

    def _render_low_stock(self, parent: Card):
        items_str: List[str] = []
        try:
            if self.services and hasattr(self.services, "low_stock_alerts"):
                items_str = self.services.low_stock_alerts() or []
        except Exception:
            items_str = []
        if not items_str:
            try:
                items = []
                if self.services and hasattr(self.services, "low_stock_items"):
                    items = self.services.low_stock_items() or []
                items_str = [f"{x['name']}  ≤ {x['stock_qty']}" for x in items]
            except Exception:
                items_str = []
        if not items_str:
            items_str = ["No alerts"]

        # Scrollable list
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(
            f"QScrollArea {{ background: transparent; }} QWidget {{ background-color: {PALETTE['card2']}; border-radius: 12px; }}"
        )
        container = QWidget()
        vbox = QVBoxLayout(container)
        vbox.setContentsMargins(8, 8, 8, 8)
        vbox.setSpacing(4)
        for s in items_str:
            row = QFrame()
            row.setStyleSheet("background: transparent;")
            rlayout = QHBoxLayout(row)
            rlayout.setContentsMargins(8, 2, 8, 2)
            rlayout.addWidget(QLabel(s))
            vbox.addWidget(row)
        vbox.addStretch(1)
        scroll.setWidget(container)
        parent.layout_v.addWidget(scroll)


if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    try:
        setTheme(Theme.DARK)
    except Exception:
        pass

    # Set app-level background to match original bg color
    root = QWidget()
    root.setObjectName("Root")
    root.setStyleSheet(f"QWidget#Root {{ background-color: {PALETTE['bg']}; }}")
    root.resize(1100, 720)

    page = DashboardPage(services=None, parent=root)

    lay = QVBoxLayout(root)
    lay.setContentsMargins(0, 0, 0, 0)
    lay.addWidget(page)

    root.show()
    sys.exit(app.exec())
