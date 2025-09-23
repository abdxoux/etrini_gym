# /pages/reports.py
# GymPro — Reports: Daily / Monthly / Yearly (CustomTkinter + Matplotlib)
# Enhanced + FIXED: safe rebinding when switching tabs, robust debounce, toplevel shortcuts.

from __future__ import annotations

import csv
import datetime as dt
import random
from typing import Any, Dict, Iterable, List, Optional, Tuple

import customtkinter as ctk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

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

# ---------- atoms ----------
class SectionCard(ctk.CTkFrame):
    def __init__(self, master, title: str):
        super().__init__(master, fg_color=PALETTE["card"], corner_radius=16)
        self.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(self, text=title, text_color=PALETTE["text"],
                     font=("Segoe UI Semibold", 15)).grid(row=0, column=0, sticky="w", padx=16, pady=(14, 8))

class KpiCard(ctk.CTkFrame):
    def __init__(self, master, label: str, value: str = "—"):
        super().__init__(master, fg_color=PALETTE["card2"], corner_radius=14)
        self.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(self, text=label, text_color=PALETTE["muted"], font=("Segoe UI", 12))\
            .grid(row=0, column=0, sticky="w", padx=12, pady=(10,0))
        self.value = ctk.CTkLabel(self, text=value, text_color=PALETTE["text"], font=("Segoe UI Semibold", 16))
        self.value.grid(row=1, column=0, sticky="w", padx=12, pady=(0,10))

class Pill(ctk.CTkFrame):
    def __init__(self, master, text: str, *, fg: str = "#2b3344", text_color: str = PALETTE["text"]):
        super().__init__(master, fg_color=fg, corner_radius=100)
        ctk.CTkLabel(self, text=text, text_color=text_color, font=("Segoe UI", 12)).pack(padx=10, pady=4)

# ---------- charts ----------
def _apply_mpl_dark(fig: Figure):
    fig.set_facecolor(PALETTE["card2"])
    ax = fig.axes[0]
    ax.set_facecolor(PALETTE["card2"])
    ax.tick_params(colors=PALETTE["muted"])
    for spine in ax.spines.values():
        spine.set_color("#2a3245")
    ax.grid(True, linestyle="--", alpha=0.25, color="#2a3245")

class LineChart(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color=PALETTE["card2"], corner_radius=12)
        self.fig = Figure(figsize=(5, 2.6), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew", padx=8, pady=8)
        self.grid_rowconfigure(0, weight=1); self.grid_columnconfigure(0, weight=1)

    def plot(self, x: List[Any], y: List[float], xlabel: str = "", ylabel: str = ""):
        self.ax.clear()
        self.ax.plot(x, y)
        self.ax.set_xlabel(xlabel); self.ax.set_ylabel(ylabel)
        _apply_mpl_dark(self.fig)
        self.fig.tight_layout()
        self.canvas.draw_idle()

class BarChart(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color=PALETTE["card2"], corner_radius=12)
        self.fig = Figure(figsize=(5, 2.6), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew", padx=8, pady=8)
        self.grid_rowconfigure(0, weight=1); self.grid_columnconfigure(0, weight=1)

    def plot(self, labels: List[str], values: List[float], xlabel: str = "", ylabel: str = ""):
        self.ax.clear()
        self.ax.bar(labels, values)
        self.ax.set_xlabel(xlabel); self.ax.set_ylabel(ylabel)
        _apply_mpl_dark(self.fig)
        self.fig.tight_layout()
        self.canvas.draw_idle()

# ---------- table ----------
class DetailTable(ctk.CTkFrame):
    COLS = ("Date", "Type", "Member / Walk-in", "Method", "Total", "Received", "Debt")

    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        self.grid_rowconfigure(1, weight=1); self.grid_columnconfigure(0, weight=1)

        hdr = ctk.CTkFrame(self, fg_color=PALETTE["card2"], corner_radius=12)
        hdr.grid(row=0, column=0, sticky="ew", padx=8, pady=(0,6))
        weights = (18, 10, 32, 12, 10, 10, 8)
        for i, (text, w) in enumerate(zip(self.COLS, weights)):
            btn = ctk.CTkButton(hdr, text=text, height=28, corner_radius=8,
                                fg_color="#2b3344", hover_color="#38445a",
                                command=lambda idx=i: self._sort_by(idx))
            btn.grid(row=0, column=i, padx=(10 if i==0 else 6, 6), pady=6, sticky="ew")
            hdr.grid_columnconfigure(i, weight=w)

        self.body = ctk.CTkScrollableFrame(self, fg_color=PALETTE["card2"], corner_radius=12)
        self.body.grid(row=1, column=0, sticky="nsew", padx=8, pady=(0,8))
        self._rows_widgets: List[ctk.CTkFrame] = []
        self._data: List[Dict[str, Any]] = []
        self._sort_state: Tuple[int, bool] = (0, False)

    def set_rows(self, rows: Iterable[Dict[str, Any]]):
        for w in self._rows_widgets: w.destroy()
        self._rows_widgets.clear()
        self._data = list(rows)
        for r in self._data:
            self._rows_widgets.append(self._mk_row(r))

    def _mk_row(self, r: Dict[str, Any]) -> ctk.CTkFrame:
        row = ctk.CTkFrame(self.body, fg_color=PALETTE["card"], corner_radius=10)
        row.pack(fill="x", padx=8, pady=6)
        for i, w in enumerate((18,10,32,12,10,10,8)): row.grid_columnconfigure(i, weight=w)
        vals = (
            r.get("date","—"),
            r.get("type","—"),
            r.get("member","—"),
            r.get("method","—"),
            f"{float(r.get('total',0)):.0f}",
            f"{float(r.get('received',0)):.0f}",
            ("—" if float(r.get("debt",0))<=0 else f"{float(r.get('debt',0)):.0f}")
        )
        for i, val in enumerate(vals):
            ctk.CTkLabel(row, text=str(val),
                         text_color=PALETTE["text"] if i in (0,2,4,5) else PALETTE["muted"])\
                .grid(row=0, column=i, sticky="w", padx=(12 if i==0 else 8, 8), pady=8)
        return row

    def _sort_by(self, col_idx: int):
        asc = not (self._sort_state[0] == col_idx and self._sort_state[1])
        self._sort_state = (col_idx, asc)
        key_map = {
            0: lambda r: r.get("date",""),
            1: lambda r: r.get("type",""),
            2: lambda r: r.get("member",""),
            3: lambda r: r.get("method",""),
            4: lambda r: float(r.get("total",0)),
            5: lambda r: float(r.get("received",0)),
            6: lambda r: float(r.get("debt",0)),
        }
        key = key_map.get(col_idx, lambda r: "")
        self._data.sort(key=key, reverse=not asc)
        self.set_rows(self._data)

    def export_csv(self, path: str, kpis: Dict[str, Any], mix: List[Dict[str, Any]]):
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["# KPIs"])
            for k, v in kpis.items(): w.writerow([k, v])
            w.writerow([])
            w.writerow(["# Product Mix"]); w.writerow(["Product", "Value"])
            for m in mix: w.writerow([m.get("name",""), m.get("value","")])
            w.writerow([])
            w.writerow(self.COLS)
            for r in self._data:
                w.writerow([
                    r.get("date",""), r.get("type",""), r.get("member",""), r.get("method",""),
                    r.get("total",""), r.get("received",""), r.get("debt",""),
                ])

# ---------- title strip ----------
class TitleStrip(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color=PALETTE["card"], corner_radius=16)
        self.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(self, text="Reports — Daily / Monthly / Yearly",
                     text_color=PALETTE["text"], font=("Segoe UI Semibold", 16))\
            .grid(row=0, column=0, sticky="w", padx=16, pady=16)
        kpis = ctk.CTkFrame(self, fg_color="transparent"); kpis.grid(row=0, column=1, sticky="e", padx=12, pady=10)
        self.k_total = KpiCard(kpis, "Total Sales", "—")
        self.k_new   = KpiCard(kpis, "New Members", "—")
        self.k_ref   = KpiCard(kpis, "Refunds", "—")
        for i, k in enumerate((self.k_total, self.k_new, self.k_ref)): k.grid(row=0, column=i, padx=8)

    def update(self, total: float, new_members: int, refunds: int):
        self.k_total.value.configure(text=f"{total:,.0f} DA")
        self.k_new.value.configure(text=str(new_members))
        self.k_ref.value.configure(text=str(refunds))

# ---------- page ----------
class ReportsPage(ctk.CTkFrame):
    def __init__(self, master, services: Optional[object] = None):
        super().__init__(master, fg_color=PALETTE["surface"])
        self.services = services
        self.mode = "Monthly"
        self._after_handle = None  # debounce handle
        self._last_kpis: Dict[str, Any] = {}
        self._last_mix: List[Dict[str, Any]] = []

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)

        self.title = TitleStrip(self); self.title.grid(row=0, column=0, sticky="ew", padx=16, pady=(16,8))

        bar = ctk.CTkFrame(self, fg_color=PALETTE["card"], corner_radius=16)
        bar.grid(row=1, column=0, sticky="ew", padx=16, pady=8)
        bar.grid_columnconfigure(0, weight=0); bar.grid_columnconfigure(1, weight=1); bar.grid_columnconfigure(2, weight=0)

        try:
            self.tabs = ctk.CTkSegmentedButton(bar, values=["Daily","Monthly","Yearly"], command=self._on_mode_change)
            self.tabs.set("Monthly"); self.tabs.grid(row=0, column=0, padx=12, pady=10)
        except Exception:
            self.tabs = None
            for i, m in enumerate(("Daily","Monthly","Yearly")):
                ctk.CTkButton(bar, text=m, height=26, corner_radius=14, fg_color="#2b3344",
                              command=lambda mm=m: self._on_mode_change(mm))\
                    .grid(row=0, column=i, padx=4, pady=10, sticky="w")

        self.filter_panel = ctk.CTkFrame(bar, fg_color="transparent")
        self.filter_panel.grid(row=0, column=1, sticky="ew")
        self.filter_panel.grid_columnconfigure(8, weight=1)
        self._build_filters_for_mode("Monthly")

        ctk.CTkButton(bar, text="Export CSV", height=30, corner_radius=18,
                      fg_color="#263042", hover_color="#32405a",
                      command=self._export_csv).grid(row=0, column=2, padx=12, pady=10)

        charts = ctk.CTkFrame(self, fg_color="transparent")
        charts.grid(row=2, column=0, sticky="nsew", padx=16, pady=8)
        charts.grid_columnconfigure(0, weight=3, uniform="chart"); charts.grid_columnconfigure(1, weight=2, uniform="chart")
        charts.grid_rowconfigure(0, weight=1)

        left = SectionCard(charts, "Sales Over Time"); left.grid(row=0, column=0, sticky="nsew", padx=(0,8))
        left.grid_rowconfigure(1, weight=1)
        self.chart_line = LineChart(left); self.chart_line.grid(row=1, column=0, sticky="nsew", padx=8, pady=(0,10))

        right = SectionCard(charts, "Product Mix (Top 6)"); right.grid(row=0, column=1, sticky="nsew", padx=(8,0))
        right.grid_rowconfigure(1, weight=1)
        self.chart_bar = BarChart(right); self.chart_bar.grid(row=1, column=0, sticky="nsew", padx=8, pady=(0,10))

        table_card = SectionCard(self, "Detail — Transactions")
        table_card.grid(row=3, column=0, sticky="nsew", padx=16, pady=(8,16))
        table_card.grid_rowconfigure(1, weight=1); table_card.grid_columnconfigure(0, weight=1)
        self.table = DetailTable(table_card); self.table.grid(row=1, column=0, sticky="nsew", padx=8, pady=(0,10))

        self._bind_shortcuts()
        self._refresh_data_now()

    # ---------- filters ----------
    def _clear_filter_panel(self):
        # destroy children
        for w in self.filter_panel.winfo_children():
            try: w.destroy()
            except Exception: pass
        # ensure old Entry attributes are removed to avoid binding destroyed widgets
        for name in ("ent_from","ent_to","ent_month","ent_year","seg_type"):
            if hasattr(self, name):
                try:
                    obj = getattr(self, name)
                    if hasattr(obj, "destroy"): obj.destroy()
                except Exception:
                    pass
                try: delattr(self, name)
                except Exception: pass

    def _build_filters_for_mode(self, mode: str):
        self._clear_filter_panel()
        self.mode = mode

        # Create fresh widgets for this mode
        if mode == "Daily":
            ctk.CTkLabel(self.filter_panel, text="From", text_color=PALETTE["muted"]).grid(row=0, column=0, padx=(8,6))
            self.ent_from = ctk.CTkEntry(self.filter_panel, width=140); self.ent_from.insert(0, dt.date.today().isoformat())
            self.ent_from.grid(row=0, column=1)
            ctk.CTkLabel(self.filter_panel, text="To", text_color=PALETTE["muted"]).grid(row=0, column=2, padx=(12,6))
            self.ent_to = ctk.CTkEntry(self.filter_panel, width=140); self.ent_to.insert(0, dt.date.today().isoformat())
            self.ent_to.grid(row=0, column=3)
        elif mode == "Monthly":
            ctk.CTkLabel(self.filter_panel, text="Period", text_color=PALETTE["muted"]).grid(row=0, column=0, padx=(8,6))
            self.ent_month = ctk.CTkEntry(self.filter_panel, width=120); self.ent_month.insert(0, dt.date.today().strftime("%Y-%m"))
            self.ent_month.grid(row=0, column=1)
        else:  # Yearly
            ctk.CTkLabel(self.filter_panel, text="Year", text_color=PALETTE["muted"]).grid(row=0, column=0, padx=(8,6))
            self.ent_year = ctk.CTkEntry(self.filter_panel, width=100); self.ent_year.insert(0, str(dt.date.today().year))
            self.ent_year.grid(row=0, column=1)

        # Type segmented (fresh instance each time)
        try:
            ctk.CTkLabel(self.filter_panel, text="Type", text_color=PALETTE["muted"]).grid(row=0, column=4, padx=(16,6))
            self.seg_type = ctk.CTkSegmentedButton(
                self.filter_panel, values=["All","POS","Subscription"],
                command=lambda _=None: self._refresh_data_debounced()
            )
            self.seg_type.set("All"); self.seg_type.grid(row=0, column=5, padx=(0,6))
        except Exception:
            self.seg_type = None

        ctk.CTkButton(self.filter_panel, text="Refresh", height=28, corner_radius=16,
                      fg_color="#2a3550", hover_color="#334066",
                      command=self._refresh_data_now).grid(row=0, column=7, padx=(12,0))

        # Bind to *new* widgets only (guard winfo_exists)
        for name in ("ent_from","ent_to","ent_month","ent_year"):
            if hasattr(self, name):
                try:
                    widget = getattr(self, name)
                    # winfo_exists returns 1 only for live widgets
                    if int(widget.winfo_exists()) == 1:
                        widget.bind("<KeyRelease>", lambda _e: self._refresh_data_debounced())
                except Exception:
                    pass

    def _on_mode_change(self, value: Optional[str] = None):
        if value is None and self.tabs:
            value = self.tabs.get()
        self._build_filters_for_mode(value or "Monthly")
        self._refresh_data_now()

    # ---------- keyboard shortcuts ----------
    def _bind_shortcuts(self):
        # bind on toplevel to avoid customtkinter bind_all restrictions
        try:
            top = self.winfo_toplevel()
            top.bind("<Control-r>", lambda e: self._refresh_data_now())
            top.bind("<Control-e>", lambda e: self._export_csv())
            top.bind("<Control-1>", lambda e: (self.tabs.set("Daily") if self.tabs else None) or self._on_mode_change("Daily"))
            top.bind("<Control-2>", lambda e: (self.tabs.set("Monthly") if self.tabs else None) or self._on_mode_change("Monthly"))
            top.bind("<Control-3>", lambda e: (self.tabs.set("Yearly") if self.tabs else None) or self._on_mode_change("Yearly"))
        except Exception:
            pass

    # ---------- debounce ----------
    def _refresh_data_debounced(self, delay_ms: int = 250):
        try:
            if self._after_handle is not None:
                self.after_cancel(self._after_handle)
        except Exception:
            pass
        self._after_handle = self.after(delay_ms, self._refresh_data_now)

    # ---------- period parsing ----------
    def _resolve_period(self) -> Tuple[dt.date, dt.date]:
        def safe_parse(s: str, default: dt.date) -> dt.date:
            try: return dt.date.fromisoformat(s.strip())
            except Exception: return default

        if self.mode == "Daily":
            today = dt.date.today()
            d1 = safe_parse(getattr(self, "ent_from", None).get() if hasattr(self, "ent_from") else "", today)
            d2 = safe_parse(getattr(self, "ent_to", None).get() if hasattr(self, "ent_to") else "", today)
            return (d1, d2) if d1 <= d2 else (d2, d1)
        if self.mode == "Monthly":
            today = dt.date.today()
            text = getattr(self, "ent_month", None).get().strip() if hasattr(self, "ent_month") else today.strftime("%Y-%m")
            try:
                y, m = map(int, text.split("-"))
                start = dt.date(y, m, 1)
                end = dt.date(y, 12, 31) if m == 12 else dt.date(y, m+1, 1) - dt.timedelta(days=1)
                return start, end
            except Exception:
                start = dt.date(today.year, today.month, 1)
                end = dt.date(today.year, 12, 31) if today.month == 12 else dt.date(today.year, today.month+1, 1) - dt.timedelta(days=1)
                return start, end
        # Yearly
        today = dt.date.today()
        try: y = int(getattr(self, "ent_year", None).get().strip()) if hasattr(self, "ent_year") else today.year
        except Exception: y = today.year
        return dt.date(y, 1, 1), dt.date(y, 12, 31)

    # ---------- data ----------
    def _refresh_data_now(self):
        start, end = self._resolve_period()
        typ = self.seg_type.get() if hasattr(self, "seg_type") and self.seg_type else "All"

        data = None
        if self.services and hasattr(self.services, "reports"):
            try:
                data = self.services.reports.fetch(self.mode, start, end, None if typ == "All" else typ)
            except Exception:
                data = None
        if not data:
            data = self._mock_data(start, end, typ)

        k = data["kpis"]; self._last_kpis = k; self._last_mix = data["mix"]
        self.title.update(k.get("total_sales", 0.0), k.get("new_members", 0), k.get("refunds", 0))

        xs = [p["x"] for p in data["series"]]; ys = [p["sales"] for p in data["series"]]
        self.chart_line.plot(xs, ys, xlabel="Time", ylabel="Sales (DA)")

        labels = [m["name"] for m in data["mix"]]; values = [m["value"] for m in data["mix"]]
        self.chart_bar.plot(labels, values, xlabel="Product", ylabel="Sales (DA)")

        self.table.set_rows(data["details"])

    # ---------- CSV export ----------
    def _export_csv(self):
        try:
            from tkinter import filedialog, messagebox
        except Exception:
            filedialog = messagebox = None
        default_name = f"report_{self.mode.lower()}_{dt.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        path = filedialog.asksaveasfilename(title="Export Report CSV", defaultextension=".csv",
                                            initialfile=default_name, filetypes=[("CSV","*.csv")]) if filedialog else default_name
        if not path: return
        try:
            self.table.export_csv(path, getattr(self, "_last_kpis", {}), getattr(self, "_last_mix", []))
            if messagebox: messagebox.showinfo("Export", f"Report exported to:\n{path}")
        except Exception as e:
            if messagebox: messagebox.showerror("Export", f"Failed to export: {e}")

    # ---------- mock data ----------
    def _mock_data(self, start: dt.date, end: dt.date, typ: str) -> Dict[str, Any]:
        rng = (end - start).days + 1
        series = []; total_sales = 0.0
        if self.mode == "Daily" and rng == 1:
            base = 8
            for h in range(12):
                val = random.randint(200, 2500)
                total_sales += val; series.append({"x": f"{base+h}:00", "sales": val})
        else:
            for i in range(rng):
                d = start + dt.timedelta(days=i)
                val = random.randint(500, 8000)
                total_sales += val; series.append({"x": d.strftime("%Y-%m-%d"), "sales": val})
        names = ["Water","Protein Bar","Creatine","Towel","Shaker","Energy"]
        mix = [{"name": n, "value": random.randint(1000, 20000)} for n in names]
        members = ["Jane Doe","John Lee","Walk-in","Samir B.","A. Karim"]; methods = ["Cash","Card","Mobile"]
        details: List[Dict[str, Any]] = []
        for d in (start + dt.timedelta(days=i) for i in range(rng)) if rng <= 10 else (start + dt.timedelta(days=i) for i in range(rng-10, rng)):
            for _ in range(random.randint(1, 3)):
                ttype = random.choice(["POS","Subscription"])
                if typ != "All" and ttype != typ: continue
                total = random.choice([80,180,250,600,1200,2200,3380,6000])
                received = total if random.random() > 0.2 else int(total*0.5)
                debt = max(0, total - received)
                details.append({
                    "date": d.strftime("%Y-%m-%d ") + random.choice(["09:20","10:14","16:18","17:40","18:02"]),
                    "type": ttype, "member": random.choice(members), "method": random.choice(methods),
                    "total": total, "received": received, "debt": debt,
                })
        return {
            "kpis": {"total_sales": total_sales, "new_members": random.randint(5, 30), "refunds": random.randint(0, 5)},
            "series": series, "mix": mix, "details": details[:50],
        }

# Local preview
if __name__ == "__main__":
    ctk.set_appearance_mode("dark"); ctk.set_default_color_theme("blue")
    root = ctk.CTk(); root.geometry("1400x900"); root.configure(fg_color=PALETTE["bg"])
    page = ReportsPage(root); page.pack(fill="both", expand=True)
    root.mainloop()
