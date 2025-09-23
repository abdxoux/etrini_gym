# pages/accounting.py
# GymPro — Accounting: Invoices (left) & Z-Report (right) with Subscriptions and Daily/Weekly/Monthly periods
from __future__ import annotations

import datetime as dt
import random
from typing import Any, Dict, List, Optional, Tuple

import customtkinter as ctk

# Reuse shared palette if router exposes it
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

# ---------- atoms ----------
class SectionCard(ctk.CTkFrame):
    def __init__(self, master, title: str):
        super().__init__(master, fg_color=PALETTE["card"], corner_radius=16)
        self.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(self, text=title, text_color=PALETTE["text"],
                     font=("Segoe UI Semibold", 15)).grid(row=0, column=0, sticky="w", padx=16, pady=(12,8))

class Kpi(ctk.CTkFrame):
    def __init__(self, master, label: str, value: str = "—"):
        super().__init__(master, fg_color=PALETTE["card2"], corner_radius=12)
        ctk.CTkLabel(self, text=label, text_color=PALETTE["muted"], font=("Segoe UI", 12))\
            .grid(row=0, column=0, sticky="w", padx=10, pady=(8,0))
        self.val = ctk.CTkLabel(self, text=value, text_color=PALETTE["text"], font=("Segoe UI Semibold", 16))
        self.val.grid(row=1, column=0, sticky="w", padx=10, pady=(0,10))

class Pill(ctk.CTkFrame):
    def __init__(self, master, text: str, kind: str = "muted"):
        colors = {
            "ok":    ("#1e3325", PALETTE["ok"]),
            "warn":  ("#33240f", PALETTE["warn"]),
            "danger":("#3a1418", PALETTE["danger"]),
            "muted": ("#2b3344", PALETTE["muted"]),
        }
        bg, fg = colors.get(kind, colors["muted"])
        super().__init__(master, fg_color=bg, corner_radius=999)
        ctk.CTkLabel(self, text=text, text_color=fg, font=("Segoe UI", 12)).grid(row=0, column=0, padx=10, pady=4)

class Toast(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color=PALETTE["card2"], corner_radius=10)
        self._lbl = ctk.CTkLabel(self, text="", text_color=PALETTE["text"])
        self._lbl.grid(row=0, column=0, padx=12, pady=6)
        self.place_forget()
        self._after=None
    def show(self, text: str, kind: str = "ok", ms: int = 1400):
        colors = {"ok": PALETTE["ok"], "warn": PALETTE["warn"], "danger": PALETTE["danger"]}
        self._lbl.configure(text=text, text_color=colors.get(kind, PALETTE["ok"]))
        self.place(relx=1.0, rely=1.0, x=-14, y=-14, anchor="se")
        if self._after:
            try: self.after_cancel(self._after)
            except Exception: pass
        self._after = self.after(ms, self.place_forget)

# ---------- rows ----------
class InvoiceRow(ctk.CTkFrame):
    def __init__(self, master, inv: Dict[str, Any]):
        super().__init__(master, fg_color=PALETTE["card2"], corner_radius=10)
        self.inv = inv
        cols = ("No.", "Date", "Type", "Member/Walk-in", "Method", "Total", "Paid", "Status")
        weights = (10,16,10,26,12,12,12,10)
        for i, w in enumerate(weights): self.grid_columnconfigure(i, weight=w)

        vals = (
            inv.get("no","—"),
            inv.get("date","—"),
            inv.get("typ","—"),
            inv.get("who","—"),
            inv.get("method","—"),
            f"{float(inv.get('total',0)):.0f}",
            f"{float(inv.get('paid',0)):.0f}",
            inv.get("status","open"),
        )
        colors = [PALETTE["text"], PALETTE["muted"], PALETTE["muted"], PALETTE["text"],
                  PALETTE["muted"], PALETTE["text"], PALETTE["text"], PALETTE["ok"]]
        if vals[-1] == "partial": colors[-1] = PALETTE["warn"]
        if vals[-1] == "open":    colors[-1] = PALETTE["danger"]

        for i, (txt, col) in enumerate(zip(vals, colors)):
            ctk.CTkLabel(self, text=str(txt), text_color=col).grid(
                row=0, column=i, padx=(12 if i==0 else 8, 8), pady=6, sticky="w"
            )

# ---------- utilities ----------
def week_range(anchor: dt.date) -> Tuple[dt.date, dt.date]:
    # Monday..Sunday week
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

# ---------- page ----------
class AccountingPage(ctk.CTkFrame):
    """
    Optional services (duck-typed):
      - accounting.search_invoices(q:str, status:str, method:str, limit:int) -> list[{no,date,typ,who,method,total,paid,status}]
      - accounting.z_report(period:str, anchor:date) -> {
            'period': 'Daily'|'Weekly'|'Monthly',
            'start': date, 'end': date,
            'pos_gross': float, 'sub_gross': float, 'refunds': float, 'net': float,
            'cash': float, 'card': float, 'transfer': float, 'count': int
        }
      - accounting.export_z(period:str, anchor:date, path:str) -> None
    """
    def __init__(self, master, services: Optional[object] = None):
        super().__init__(master, fg_color=PALETTE["surface"])
        self.services = services
        self._after = None
        self._period = "Daily"

        # root split
        self.grid_columnconfigure(0, weight=3, uniform="col")
        self.grid_columnconfigure(1, weight=2, uniform="col")
        self.grid_rowconfigure(0, weight=1)

        # LEFT — Invoices
        left = ctk.CTkFrame(self, fg_color="transparent")
        left.grid(row=0, column=0, sticky="nsew", padx=(12,6), pady=12)
        left.grid_rowconfigure(2, weight=1)
        left.grid_columnconfigure(0, weight=1)

        title = SectionCard(left, "Invoices")
        title.grid(row=0, column=0, sticky="ew", pady=(0,6))

        filters = ctk.CTkFrame(left, fg_color=PALETTE["card"], corner_radius=16)
        filters.grid(row=1, column=0, sticky="ew", pady=(0,6))
        for i in range(8): filters.grid_columnconfigure(i, weight=1)

        ctk.CTkLabel(filters, text="Search", text_color=PALETTE["muted"]).grid(row=0, column=0, padx=(12,8), pady=8, sticky="w")
        self.ent_q = ctk.CTkEntry(filters, placeholder_text="Member, #, method…")
        self.ent_q.grid(row=0, column=1, columnspan=3, sticky="ew", padx=(0,8), pady=8)
        self.ent_q.bind("<KeyRelease>", lambda _e: self._debounce(self._refresh_invoices))

        try:
            self.opt_status = ctk.CTkOptionMenu(filters, values=["Any","open","partial","paid"],
                                                command=lambda _v: self._refresh_invoices()); self.opt_status.set("Any")
        except Exception:
            self.opt_status = ctk.CTkEntry(filters); self.opt_status.insert(0, "Any")
        self.opt_status.grid(row=0, column=4, padx=(8,8), pady=8, sticky="w")

        try:
            self.opt_method = ctk.CTkOptionMenu(filters, values=["Any","Cash","Card","Mobile","Transfer"],
                                                command=lambda _v: self._refresh_invoices()); self.opt_method.set("Any")
        except Exception:
            self.opt_method = ctk.CTkEntry(filters); self.opt_method.insert(0, "Any")
        self.opt_method.grid(row=0, column=5, padx=(0,8), pady=8, sticky="w")

        ctk.CTkButton(filters, text="Refresh", height=26, corner_radius=12,
                      fg_color="#2a3550", hover_color="#334066",
                      command=self._refresh_invoices).grid(row=0, column=7, padx=(0,12), pady=8, sticky="e")

        list_card = SectionCard(left, "Results")
        list_card.grid(row=2, column=0, sticky="nsew")
        list_card.grid_rowconfigure(1, weight=1)
        header = ctk.CTkFrame(list_card, fg_color=PALETTE["card2"], corner_radius=12)
        header.grid(row=0, column=0, sticky="ew", padx=10, pady=(0,6))
        labels = ("No.", "Date", "Type", "Member/Walk-in", "Method", "Total", "Paid", "Status")
        weights = (10,16,10,26,12,12,12,10)
        for i, (txt, w) in enumerate(zip(labels, weights)):
            ctk.CTkLabel(header, text=txt, text_color=PALETTE["muted"]).grid(
                row=0, column=i, padx=(12 if i==0 else 8,8), pady=6, sticky="w"
            ); header.grid_columnconfigure(i, weight=w)

        self.inv_list = ctk.CTkFrame(list_card, fg_color=PALETTE["card2"], corner_radius=12)
        self.inv_list.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0,10))
        self.inv_list.bind("<Configure>", lambda _e: self._render_invoices())

        # RIGHT — Z-Report (with periods)
        right = ctk.CTkFrame(self, fg_color="transparent")
        right.grid(row=0, column=1, sticky="nsew", padx=(6,12), pady=12)
        right.grid_columnconfigure(0, weight=1)

        z_title = SectionCard(right, "Z-Report — Sales Snapshot")
        z_title.grid(row=0, column=0, sticky="ew", pady=(0,6))

        z_bar = ctk.CTkFrame(right, fg_color=PALETTE["card"], corner_radius=16)
        z_bar.grid(row=1, column=0, sticky="ew", pady=(0,6))
        z_bar.grid_columnconfigure(4, weight=1)

        # period segmented
        try:
            self.seg_period = ctk.CTkSegmentedButton(z_bar, values=["Daily","Weekly","Monthly"],
                                                     command=self._on_period_change)
            self.seg_period.set("Daily")
            self.seg_period.grid(row=0, column=0, padx=12, pady=8, sticky="w")
        except Exception:
            self.seg_period = None
            ctk.CTkButton(z_bar, text="Daily", height=26, corner_radius=12, fg_color="#2b3344",
                          command=lambda: self._on_period_change("Daily")).grid(row=0, column=0, padx=(12,4), pady=8, sticky="w")
            ctk.CTkButton(z_bar, text="Weekly", height=26, corner_radius=12, fg_color="#2b3344",
                          command=lambda: self._on_period_change("Weekly")).grid(row=0, column=1, padx=(0,4), pady=8, sticky="w")
            ctk.CTkButton(z_bar, text="Monthly", height=26, corner_radius=12, fg_color="#2b3344",
                          command=lambda: self._on_period_change("Monthly")).grid(row=0, column=2, padx=(0,8), pady=8, sticky="w")

        # anchor day
        ctk.CTkLabel(z_bar, text="Anchor", text_color=PALETTE["muted"]).grid(row=0, column=3, padx=(8,8), pady=8, sticky="e")
        self.ent_day = ctk.CTkEntry(z_bar, width=120)
        self.ent_day.insert(0, dt.date.today().isoformat())
        self.ent_day.grid(row=0, column=4, padx=(0,8), pady=8, sticky="w")

        ctk.CTkButton(z_bar, text="Refresh", height=26, corner_radius=12, fg_color="#2a3550", hover_color="#334066",
                      command=self._refresh_z).grid(row=0, column=5, padx=(0,8), pady=8, sticky="e")
        ctk.CTkButton(z_bar, text="Export", height=26, corner_radius=12, fg_color="#263042", hover_color="#32405a",
                      command=self._export_z).grid(row=0, column=6, padx=(0,12), pady=8, sticky="e")

        # KPIs — include Subscriptions & POS
        z_kpis = ctk.CTkFrame(right, fg_color="transparent")
        z_kpis.grid(row=2, column=0, sticky="ew", pady=(0,6))
        # first row
        self.k_pos = Kpi(z_kpis, "POS Gross", "—")
        self.k_sub = Kpi(z_kpis, "Subscriptions Gross", "—")
        self.k_ref = Kpi(z_kpis, "Refunds", "—")
        self.k_net = Kpi(z_kpis, "Net", "—")
        for i,k in enumerate((self.k_pos, self.k_sub, self.k_ref, self.k_net)):
            k.grid(row=0, column=i, padx=6)
        # second row: count + payment methods
        z_methods = ctk.CTkFrame(right, fg_color="transparent")
        z_methods.grid(row=3, column=0, sticky="ew", pady=(0,6))
        self.k_cnt = Kpi(z_methods, "Receipts", "—"); self.k_cnt.grid(row=0, column=0, padx=6)
        wrap = ctk.CTkFrame(z_methods, fg_color="transparent"); wrap.grid(row=0, column=1, padx=6, sticky="e")
        self.p_cash = Pill(wrap, "Cash 0", "muted"); self.p_card = Pill(wrap, "Card 0", "muted"); self.p_trn = Pill(wrap, "Transfer 0", "muted")
        self.p_cash.grid(row=0, column=0, padx=4); self.p_card.grid(row=0, column=1, padx=4); self.p_trn.grid(row=0, column=2, padx=4)

        z_notes = SectionCard(right, "Notes")
        z_notes.grid(row=4, column=0, sticky="ew")
        self.lbl_range = ctk.CTkLabel(z_notes, text="", text_color=PALETTE["muted"])
        self.lbl_range.grid(row=1, column=0, sticky="w", padx=12, pady=(0,10))

        # Toast
        self.toast = Toast(self)

        # initial loads
        self._refresh_invoices()
        self._refresh_z()

    # ---------- invoices ----------
    def _debounce(self, fn, ms: int = 220):
        try:
            if self._after: self.after_cancel(self._after)
        except Exception:
            pass
        self._after = self.after(ms, fn)

    def _fetch_invoices(self, q: str, status: Optional[str], method: Optional[str]) -> List[Dict[str, Any]]:
        if self.services and hasattr(self.services, "accounting"):
            try:
                return self.services.accounting.search_invoices(q, status or "Any", method or "Any", limit=120) or []
            except Exception:
                pass
        # mock
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
            base = 0
            if typ == "POS":
                base = rng.choice([80,250,600,1200,2200,3500,5400])
            else:
                base = rng.choice([1200,1800,2200,3500,4500])
            total = base
            paid  = total if st=="paid" else (total//2 if st=="partial" else 0)
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
        q = (self.ent_q.get() or "").strip()
        try: status = self.opt_status.get()
        except Exception: status = self.opt_status.get().strip()
        try: method = self.opt_method.get()
        except Exception: method = self.opt_method.get().strip()

        self._invoices = self._fetch_invoices(q, None if status=="Any" else status,
                                                 None if method=="Any" else method)
        self._render_invoices()

    def _render_invoices(self):
        for w in self.inv_list.winfo_children():
            try: w.destroy()
            except Exception: pass
        items = getattr(self, "_invoices", [])
        if not items:
            ctk.CTkLabel(self.inv_list, text="No invoices", text_color=PALETTE["muted"]).pack(padx=10, pady=8, anchor="w"); return

        h = max(1, self.inv_list.winfo_height())
        est = 36
        max_rows = max(3, (h-8)//est)
        rows = items[:max_rows]
        overflow = max(0, len(items) - len(rows))
        for inv in rows:
            InvoiceRow(self.inv_list, inv).pack(fill="x", padx=8, pady=4)
        if overflow > 0:
            ctk.CTkLabel(self.inv_list, text=f"… +{overflow} more", text_color=PALETTE["muted"])\
                .pack(padx=12, pady=6, anchor="w")

    # ---------- z report ----------
    def _on_period_change(self, val: Optional[str] = None):
        if val is None and self.seg_period:
            val = self.seg_period.get()
        self._period = val or "Daily"
        self._refresh_z()

    def _parse_anchor(self) -> dt.date:
        try:
            return dt.date.fromisoformat(self.ent_day.get().strip())
        except Exception:
            d = dt.date.today()
            try:
                self.ent_day.delete(0, "end"); self.ent_day.insert(0, d.isoformat())
            except Exception:
                pass
            return d

    def _resolve_range(self, anchor: dt.date) -> Tuple[dt.date, dt.date]:
        if self._period == "Weekly":
            return week_range(anchor)
        if self._period == "Monthly":
            return month_range(anchor)
        return anchor, anchor

    def _fetch_z(self, period: str, anchor: dt.date) -> Dict[str, Any]:
        # If services are connected, prefer them
        if self.services and hasattr(self.services, "accounting"):
            try:
                data = self.services.accounting.z_report(period, anchor)
                if data: return data
            except Exception:
                pass
        # Mock generator: deterministic by (period, date)
        rng = random.Random(hash((period, anchor.toordinal())) & 0xffffffff)
        # derive range for volume scaling
        start, end = self._resolve_range(anchor)
        days = (end - start).days + 1
        # produce totals
        pos_gross = sum(rng.randint(8000, 30000) for _ in range(days))
        sub_gross = sum(rng.randint(4000, 18000) for _ in range(days))
        refunds = sum(rng.choice([0,0,0, rng.randint(0, 3000)]) for _ in range(days))
        gross = pos_gross + sub_gross
        net = max(0, gross - refunds)
        cash = int(net * rng.uniform(0.25, 0.55))
        card = int(net * rng.uniform(0.15, 0.35))
        transfer = max(0, net - cash - card)
        count = rng.randint(12*days, 80*days)
        return {
            "period": period, "start": start, "end": end,
            "pos_gross": pos_gross, "sub_gross": sub_gross,
            "refunds": refunds, "net": net,
            "cash": cash, "card": card, "transfer": transfer, "count": count,
        }

    def _refresh_z(self):
        anchor = self._parse_anchor()
        data = self._fetch_z(self._period, anchor)
        start, end = data.get("start", anchor), data.get("end", anchor)
        # KPIs
        self.k_pos.val.configure(text=f"{data.get('pos_gross',0):,} DA")
        self.k_sub.val.configure(text=f"{data.get('sub_gross',0):,} DA")
        self.k_ref.val.configure(text=f"{data.get('refunds',0):,} DA")
        self.k_net.val.configure(text=f"{data.get('net',0):,} DA")
        self.k_cnt.val.configure(text=str(data.get('count',0)))
        # Pills
        for holder, txt in ((self.p_cash, f"Cash {int(data.get('cash',0))}"),
                            (self.p_card, f"Card {int(data.get('card',0))}"),
                            (self.p_trn,  f"Transfer {int(data.get('transfer',0))}")):
            for w in holder.winfo_children(): w.destroy()
            Pill(holder, txt, "muted").grid(row=0, column=0)
        # Range label
        if start == end:
            self.lbl_range.configure(text=f"{self._period}: {start.isoformat()}")
        else:
            self.lbl_range.configure(text=f"{self._period}: {start.isoformat()} → {end.isoformat()}")

    def _export_z(self):
        try:
            from tkinter import filedialog, messagebox
        except Exception:
            filedialog = messagebox = None
        anchor = self._parse_anchor()
        default = f"z_report_{self._period.lower()}_{anchor.isoformat()}.csv"
        path = filedialog.asksaveasfilename(title="Export Z-Report", defaultextension=".csv",
                                            initialfile=default, filetypes=[("CSV","*.csv")]) if filedialog else default
        if not path: return
        # service override
        if self.services and hasattr(self.services, "accounting"):
            try:
                self.services.accounting.export_z(self._period, anchor, path)
                if messagebox: messagebox.showinfo("Export", f"Z-Report exported:\n{path}")
                else: self.toast.show("Z-Report exported", "ok")
                return
            except Exception:
                pass
        # local export
        import csv
        data = self._fetch_z(self._period, anchor)
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f); w.writerow(["metric","value"])
            for k in ("period","start","end","pos_gross","sub_gross","refunds","net","cash","card","transfer","count"):
                v = data.get(k)
                if isinstance(v, dt.date): v = v.isoformat()
                w.writerow([k, v])
        if messagebox: messagebox.showinfo("Export", f"Z-Report exported:\n{path}")
        else: self.toast.show("Z-Report exported", "ok")

# Local preview
if __name__ == "__main__":
    ctk.set_appearance_mode("dark"); ctk.set_default_color_theme("blue")
    root = ctk.CTk(); root.geometry("1400x860"); root.configure(fg_color=PALETTE["bg"])
    page = AccountingPage(root, services=None); page.pack(fill="both", expand=True)
    root.mainloop()
