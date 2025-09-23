# pages/dashboard.py
# GymPro — DashboardPage (fast & complete UI)
# Requires: customtkinter. Reuses router.PALETTE if available.

import customtkinter as ctk
from datetime import date

try:
    from router import PALETTE as SHARED_PALETTE
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

def _title(parent, text: str):
    return ctk.CTkLabel(parent, text=text, text_color=PALETTE["text"], font=("Segoe UI Semibold", 15))

class Card(ctk.CTkFrame):
    def __init__(self, master, title: str = "", *, corner_radius: int = 16, fg=None):
        super().__init__(master, fg_color=fg or PALETTE["card"], corner_radius=corner_radius)
        self.grid_columnconfigure(0, weight=1)
        if title:
            _title(self, title).grid(row=0, column=0, sticky="w", padx=12, pady=(12, 8))

class KPICard(Card):
    def __init__(self, master, label: str, value: str, *, pill=None):
        super().__init__(master, fg=PALETTE["card"])
        r = 0
        _title(self, label).grid(row=r, column=0, sticky="w", padx=12, pady=(12, 6)); r += 1
        self.value_lbl = ctk.CTkLabel(self, text=value, text_color=PALETTE["text"], font=("Segoe UI Semibold", 26))
        self.value_lbl.grid(row=r, column=0, sticky="w", padx=12, pady=(0, 12)); r += 1
        if pill:
            tag = ctk.CTkFrame(self, fg_color=PALETTE["card2"], corner_radius=999)
            ctk.CTkLabel(tag, text=pill, text_color=PALETTE["muted"]).pack(padx=12, pady=4)
            tag.grid(row=r, column=0, sticky="w", padx=12, pady=(0, 12))

class TinyBars(ctk.CTkCanvas):
    """Fast mini bar chart (Canvas)."""
    def __init__(self, master, values, *, w=540, h=160):
        super().__init__(master, width=w, height=h, highlightthickness=0, bg=PALETTE["card"])
        self._cw, self._ch = w, h   # avoid _w/_h (tk internal names)
        self._draw(values)

    def _draw(self, values):
        self.delete("all")
        self.create_rectangle(0, 0, self._cw, self._ch, fill=PALETTE["card"], width=0)
        if not values:
            return
        m = max(values) or 1
        n = len(values)
        pad, gap = 10, 4
        barw = (self._cw - pad*2 - gap*(n-1)) / n
        for i, v in enumerate(values):
            x0 = pad + i*(barw + gap)
            x1 = x0 + barw
            h = int((v / m) * (self._ch - 30))
            y0 = self._ch - 10 - h
            y1 = self._ch - 10
            self.create_rectangle(x0, y0, x1, y1, fill=PALETTE["accent2"], width=0)
            self.create_rectangle(x0, y0 + h*0.45, x1, y1, fill=PALETTE["accent"], width=0)

class DashboardPage(ctk.CTkFrame):
    def __init__(self, master, services=None):
        super().__init__(master, fg_color=PALETTE["surface"])
        self.services = services

        # 12-column grid
        self.grid_rowconfigure(3, weight=1)
        for i in range(12):
            self.grid_columnconfigure(i, weight=1, uniform="cols")

        self._add_kpis()
        self._add_charts()
        self._add_z_and_alerts()

    def _add_kpis(self):
        kpi = self._get_kpis()
        specs = [
            ("Active Members", str(kpi["active_members"])),
            ("Today's Revenue", f"{kpi['today_revenue']:,} DA"),
            ("Unpaid Invoices", str(kpi["unpaid_invoices"])),
            ("Low Stock",       str(kpi["low_stock"])),
        ]
        for i, (label, value) in enumerate(specs):
            KPICard(self, label, value).grid(row=0, column=i*3, columnspan=3, sticky="nsew", padx=8, pady=(12,8))

    def _add_charts(self):
        # Daily Revenue
        card_daily = Card(self, "Daily Revenue (30 days)")
        card_daily.grid(row=1, column=0, columnspan=7, sticky="nsew", padx=8, pady=8)
        TinyBars(card_daily, self._get_daily_revenue(), w=780, h=200)\
            .grid(row=1, column=0, sticky="nsew", padx=10, pady=(0,12))
        # Monthly Breakdown
        card_month = Card(self, "Monthly Breakdown")
        card_month.grid(row=1, column=7, columnspan=5, sticky="nsew", padx=8, pady=8)
        TinyBars(card_month, self._get_monthly_breakdown(), w=520, h=200)\
            .grid(row=1, column=0, sticky="nsew", padx=10, pady=(0,12))

    def _add_z_and_alerts(self):
        # Z-Report
        card_z = Card(self, "Z-Report (Close Day)")
        card_z.grid(row=2, column=0, columnspan=7, sticky="nsew", padx=8, pady=(8,12))
        r = 1
        ctk.CTkEntry(card_z, placeholder_text=str(date.today())).grid(row=r, column=0, sticky="w", padx=12, pady=(6,6)); r += 1
        btns = ctk.CTkFrame(card_z, fg_color="transparent")
        btns.grid(row=r, column=0, sticky="w", padx=10, pady=(0,6)); r += 1
        ctk.CTkButton(btns, text="Export CSV", corner_radius=14, height=32, fg_color="#2b3344", hover_color="#38445a")\
            .pack(side="left", padx=(0,8))
        ctk.CTkButton(btns, text="Export PDF", corner_radius=14, height=32, fg_color=PALETTE["accent"], hover_color="#3e74d6")\
            .pack(side="left", padx=(0,8))
        ctk.CTkLabel(card_z, text=self._z_totals_text(), text_color=PALETTE["text"])\
            .grid(row=r, column=0, sticky="w", padx=12, pady=(4,10))

        # Low Stock alerts
        card_alerts = Card(self, "Low Stock Alerts")
        card_alerts.grid(row=2, column=7, columnspan=4, sticky="nsew", padx=8, pady=(8,12))
        self._render_low_stock(card_alerts)

        # Quick Actions (FIX: use enumerate for integer rows)
        qa = Card(self, "Quick Actions")
        qa.grid(row=2, column=11, columnspan=1, sticky="nsew", padx=(8,8), pady=(8,12))
        qa.grid_columnconfigure(0, weight=1)
        for i, t in enumerate(("New Member", "Renew", "Take Payment", "Open Gate"), start=0):
            ctk.CTkButton(qa, text=t, height=36, corner_radius=12, fg_color="#2b3344", hover_color="#38445a")\
                .grid(row=i, column=0, padx=12, pady=6, sticky="ew")

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
                    }
        except Exception:
            pass
        low_stock = 0
        if self.services and hasattr(self.services, "low_stock_items"):
            try:
                low_stock = len(self.services.low_stock_items() or [])
            except Exception:
                low_stock = 0
        return {"active_members": 312, "today_revenue": 4250, "unpaid_invoices": 7, "low_stock": low_stock}

    def _get_daily_revenue(self):
        try:
            if self.services and hasattr(self.services, "daily_revenue_30"):
                v = self.services.daily_revenue_30()
                if v: return list(v)
        except Exception:
            pass
        base = 15
        return [base + ((i * 7) % 30) for i in range(30)]

    def _get_monthly_breakdown(self):
        try:
            if self.services and hasattr(self.services, "monthly_breakdown_12"):
                v = self.services.monthly_breakdown_12()
                if v: return list(v)
        except Exception:
            pass
        return [20 + ((i * 11) % 40) for i in range(12)]

    def _z_totals_text(self):
        try:
            if self.services and hasattr(self.services, "zreport_totals"):
                t = self.services.zreport_totals()
                if isinstance(t, str):
                    return t
        except Exception:
            pass
        return "Payments Total: 152,000 DA   ·   By Method — Cash: 92k · Card: 44k · Mobile: 16k"

    def _render_low_stock(self, parent):
        items_str = []
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

        listbox = ctk.CTkScrollableFrame(parent, fg_color=PALETTE["card2"], corner_radius=12, height=120)
        listbox.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 12))
        for s in items_str:
            row = ctk.CTkFrame(listbox, fg_color="transparent")
            row.pack(fill="x", padx=8, pady=4)
            ctk.CTkLabel(row, text=s, text_color=PALETTE["text"]).pack(side="left")


if __name__ == "__main__":
    ctk.set_appearance_mode("dark"); ctk.set_default_color_theme("blue")
    root = ctk.CTk(); root.geometry("1100x720"); root.configure(fg_color=PALETTE["bg"])
    page = DashboardPage(root, services=None); page.pack(fill="both", expand=True)
    root.mainloop()
