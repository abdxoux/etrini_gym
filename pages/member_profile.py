# pages/subscriptions.py
# GymPro — SubscriptionsPage (fast & complete UI; grid-only inside cards)

import customtkinter as ctk
from tkinter import messagebox

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
    "muted":    "#8b93a7",
    "text":     "#e8ecf5",
    "ok":       "#22c55e",
    "warn":     "#f59e0b",
    "danger":   "#ef4444",
}

# ---------- small helpers ----------
def _title(parent, text: str):
    return ctk.CTkLabel(parent, text=text, text_color=PALETTE["text"], font=("Segoe UI Semibold", 15))

class Card(ctk.CTkFrame):
    """Rounded card; uses GRID internally (important: children must grid)."""
    def __init__(self, master, title: str = "", *, corner_radius: int = 16, fg=None):
        super().__init__(master, fg_color=fg or PALETTE["card"], corner_radius=corner_radius)
        self.grid_columnconfigure(0, weight=1)
        if title:
            _title(self, title).grid(row=0, column=0, sticky="w", padx=12, pady=(12, 8))

class Pill(ctk.CTkFrame):
    """Status tag."""
    def __init__(self, master, text: str, kind: str = "muted"):
        colors = {
            "ok": ("#20321f", PALETTE["ok"]),
            "warn": ("#33240f", PALETTE["warn"]),
            "danger": ("#3a1418", PALETTE["danger"]),
            "muted": ("#2b3344", PALETTE["muted"]),
        }
        bg, fg = colors.get(kind, colors["muted"])
        super().__init__(master, fg_color=bg, corner_radius=999)
        ctk.CTkLabel(self, text=text, text_color=fg, font=("Segoe UI", 12)).grid(row=0, column=0, padx=10, pady=4)

# ---------- page ----------
class SubscriptionsPage(ctk.CTkFrame):
    """
    Subscriptions with:
      - Search (member name / plan)
      - Filters (status, plan)
      - Results table (scrollable)
      - Actions: New, Renew, Freeze, Cancel
    Expected optional services:
      - list_subscriptions(member_id: int|None=None) -> list[dict]
      - renew_subscription(subscription_id)
      - freeze_subscription(subscription_id)
      - cancel_subscription(subscription_id)
    Subscription dict fields used: subscription_id, member_id, plan, status, start_date, end_date,
                                   member_name(optional)
    """
    def __init__(self, master, services=None):
        super().__init__(master, fg_color=PALETTE["surface"])
        self.services = services
        self._cache = []
        self._filtered = []
        self._selection = None

        # 12-col root grid
        for i in range(12):
            self.grid_columnconfigure(i, weight=1, uniform="cols")
        self.grid_rowconfigure(2, weight=1)

        self._build_toolbar()
        self._build_table()
        self._build_side_panel()

        self._refresh()

    # ---------- UI builders ----------
    def _build_toolbar(self):
        bar = Card(self, "Subscriptions")
        bar.grid(row=0, column=0, columnspan=12, sticky="ew", padx=10, pady=(12,8))
        for i in range(8): bar.grid_columnconfigure(i, weight=1)
        bar.grid_columnconfigure(8, weight=0)
        bar.grid_columnconfigure(9, weight=0)
        bar.grid_columnconfigure(10, weight=0)

        # search
        ctk.CTkLabel(bar, text="Search", text_color=PALETTE["muted"]).grid(row=1, column=0, padx=(12,8), pady=(0,10), sticky="w")
        self.ent_q = ctk.CTkEntry(bar, placeholder_text="Member or plan…")
        self.ent_q.grid(row=1, column=1, columnspan=3, sticky="ew", padx=(0,8), pady=(0,10))
        self.ent_q.bind("<KeyRelease>", lambda e: self._apply_filters())

        # status filter
        ctk.CTkLabel(bar, text="Status", text_color=PALETTE["muted"]).grid(row=1, column=4, padx=(12,8), pady=(0,10), sticky="w")
        self.opt_status = ctk.CTkOptionMenu(bar, values=["All", "active", "expired", "frozen", "cancelled"], width=140)
        self.opt_status.set("All")
        self.opt_status.grid(row=1, column=5, sticky="w", pady=(0,10))
        self.opt_status.configure(command=lambda *_: self._apply_filters())

        # plan filter
        ctk.CTkLabel(bar, text="Plan", text_color=PALETTE["muted"]).grid(row=1, column=6, padx=(12,8), pady=(0,10), sticky="w")
        self.opt_plan = ctk.CTkOptionMenu(bar, values=["All", "Monthly", "Quarterly", "Yearly"], width=140)
        self.opt_plan.set("All")
        self.opt_plan.grid(row=1, column=7, sticky="w", pady=(0,10))
        self.opt_plan.configure(command=lambda *_: self._apply_filters())

        # actions
        ctk.CTkButton(bar, text="New Subscription", height=34, corner_radius=12,
                      fg_color=PALETTE["accent"], hover_color="#3e74d6",
                      command=self._new_sub).grid(row=1, column=9, padx=(10,6), pady=(0,10), sticky="e")
        ctk.CTkButton(bar, text="Renew", height=34, corner_radius=12,
                      fg_color="#2b3344", hover_color="#38445a",
                      command=self._renew).grid(row=1, column=10, padx=(6,10), pady=(0,10), sticky="e")

    def _build_table(self):
        table = Card(self, "Results")
        table.grid(row=1, column=0, columnspan=8, sticky="nsew", padx=10, pady=8)
        table.grid_rowconfigure(2, weight=1)
        table.grid_columnconfigure(0, weight=1)

        # header
        hdr = ctk.CTkFrame(table, fg_color=PALETTE["card2"], corner_radius=12)
        hdr.grid(row=1, column=0, sticky="ew", padx=10, pady=(0,8))
        cols = ("Member", "Plan", "Period", "Status")
        weights = (35, 20, 28, 17)
        for i, (t, w) in enumerate(zip(cols, weights)):
            ctk.CTkLabel(hdr, text=t, text_color=PALETTE["muted"]).grid(row=0, column=i, padx=(12 if i==0 else 8,8), pady=8, sticky="w")
            hdr.grid_columnconfigure(i, weight=w)

        # list
        self.listbox = ctk.CTkScrollableFrame(table, fg_color=PALETTE["card2"], corner_radius=12)
        self.listbox.grid(row=2, column=0, sticky="nsew", padx=10, pady=(0,10))

    def _build_side_panel(self):
        side = Card(self, "Details & Actions")
        side.grid(row=1, column=8, columnspan=4, sticky="nsew", padx=10, pady=8)
        side.grid_columnconfigure(0, weight=1)

        # member + plan
        self.lbl_member = ctk.CTkLabel(side, text="—", text_color=PALETTE["text"], font=("Segoe UI Semibold", 18))
        self.lbl_member.grid(row=1, column=0, sticky="w", padx=12, pady=(6,2))
        self.lbl_plan = ctk.CTkLabel(side, text="", text_color=PALETTE["muted"])
        self.lbl_plan.grid(row=2, column=0, sticky="w", padx=12, pady=(0,2))
        self.lbl_period = ctk.CTkLabel(side, text="", text_color=PALETTE["muted"])
        self.lbl_period.grid(row=3, column=0, sticky="w", padx=12, pady=(0,8))

        # status pill
        self.pill_status = Pill(side, "status", "muted")
        self.pill_status.grid(row=4, column=0, sticky="w", padx=12, pady=(0,10))

        # action buttons
        btns = ctk.CTkFrame(side, fg_color="transparent")
        btns.grid(row=5, column=0, sticky="ew", padx=12, pady=(2,12))
        btns.grid_columnconfigure(0, weight=1)
        ctk.CTkButton(btns, text="Renew", height=36, corner_radius=12,
                      fg_color=PALETTE["accent"], hover_color="#3e74d6",
                      command=self._renew).grid(row=0, column=0, sticky="ew", pady=(0,8))
        ctk.CTkButton(btns, text="Freeze", height=34, corner_radius=12,
                      fg_color="#2b3344", hover_color="#38445a",
                      command=self._freeze).grid(row=1, column=0, sticky="ew", pady=6)
        ctk.CTkButton(btns, text="Cancel", height=34, corner_radius=12,
                      fg_color=PALETTE["danger"], hover_color="#c03131",
                      command=self._cancel).grid(row=2, column=0, sticky="ew", pady=6)

    # ---------- data & filtering ----------
    def _refresh(self):
        data = []
        try:
            if self.services and hasattr(self.services, "list_subscriptions"):
                data = self.services.list_subscriptions(None) or []
        except Exception:
            data = []
        if not data:
            data = [
                {"subscription_id": 7001, "member_id": 100, "member_name":"Nadia K.", "plan":"Monthly",   "status":"active",   "start_date":"2025-09-01", "end_date":"2025-09-30"},
                {"subscription_id": 7002, "member_id": 101, "member_name":"Karim B.", "plan":"Monthly",   "status":"active",   "start_date":"2025-09-05", "end_date":"2025-10-04"},
                {"subscription_id": 7003, "member_id": 102, "member_name":"Hind M.",  "plan":"Monthly",   "status":"expired",  "start_date":"2025-07-01", "end_date":"2025-07-31"},
                {"subscription_id": 7004, "member_id": 103, "member_name":"Leila R.", "plan":"Quarterly", "status":"frozen",   "start_date":"2025-06-01", "end_date":"2025-08-31"},
                {"subscription_id": 7005, "member_id": 104, "member_name":"Amine S.", "plan":"Yearly",    "status":"cancelled","start_date":"2025-01-01", "end_date":"2025-12-31"},
            ]
        self._cache = data
        self._apply_filters()

    def _apply_filters(self):
        q = (self.ent_q.get() if hasattr(self, "ent_q") else "").strip().lower()
        fstatus = self.opt_status.get() if hasattr(self, "opt_status") else "All"
        fplan   = self.opt_plan.get() if hasattr(self, "opt_plan") else "All"

        res = []
        for s in self._cache:
            name = (s.get("member_name") or "").lower()
            plan = (s.get("plan") or "").lower()
            status = (s.get("status") or "").lower()

            if fstatus != "All" and status != fstatus:
                continue
            if fplan != "All" and (s.get("plan") != fplan):
                continue
            if q and q not in name and q not in plan:
                continue
            res.append(s)

        self._filtered = res
        self._render_rows()

    # ---------- render ----------
    def _render_rows(self):
        for w in list(self.listbox.children.values()):
            w.destroy()

        if not self._filtered:
            ctk.CTkLabel(self.listbox, text="No results", text_color=PALETTE["muted"]).pack(padx=12, pady=8, anchor="w")
            return

        for s in self._filtered:
            row = ctk.CTkFrame(self.listbox, fg_color=PALETTE["card"], corner_radius=10)
            row.pack(fill="x", padx=8, pady=6)

            row.grid_columnconfigure(0, weight=35)
            row.grid_columnconfigure(1, weight=20)
            row.grid_columnconfigure(2, weight=28)
            row.grid_columnconfigure(3, weight=17)

            nm = s.get("member_name") or f"#{s.get('member_id','')}"
            ctk.CTkLabel(row, text=nm, text_color=PALETTE["text"]).grid(row=0, column=0, padx=(12,8), pady=8, sticky="w")
            ctk.CTkLabel(row, text=s.get("plan","—"), text_color=PALETTE["muted"]).grid(row=0, column=1, padx=8, sticky="w")
            ctk.CTkLabel(row, text=f"{s.get('start_date','—')} → {s.get('end_date','—')}", text_color=PALETTE["muted"]).grid(row=0, column=2, padx=8, sticky="w")

            st = (s.get("status") or "").lower()
            kind = "ok" if st == "active" else ("warn" if st == "frozen" else ("danger" if st in ("expired","cancelled") else "muted"))
            Pill(row, st or "—", kind=kind).grid(row=0, column=3, padx=8, sticky="w")

            # selection
            row.bind("<Button-1>", lambda e, sub=s: self._select(sub))
            for child in row.winfo_children():
                child.bind("<Button-1>", lambda e, sub=s: self._select(sub))

    def _select(self, sub: dict):
        self._selection = sub
        nm = sub.get("member_name") or f"#{sub.get('member_id','')}"
        self.lbl_member.configure(text=nm)
        self.lbl_plan.configure(text=sub.get("plan","—"))
        self.lbl_period.configure(text=f"{sub.get('start_date','—')} → {sub.get('end_date','—')}")
        st = (sub.get("status") or "").lower()
        kind = "ok" if st == "active" else ("warn" if st == "frozen" else ("danger" if st in ("expired","cancelled") else "muted"))
        # replace pill
        self.pill_status.destroy()
        self.pill_status = Pill(self, st or "—", kind=kind)
        # Put it back where it belongs (row 4 of side panel)
        self.pill_status.grid(in_=self.lbl_member.master, row=4, column=0, sticky="w", padx=12, pady=(0,10))

    # ---------- actions (UI stubs unless services provided) ----------
    def _new_sub(self):
        messagebox.showinfo("Subscriptions", "UI-only: New Subscription dialog will be added later.")

    def _renew(self):
        if not self._selection:
            messagebox.showwarning("Subscriptions", "Select a subscription first.")
            return
        fn = getattr(self.services, "renew_subscription", None)
        if callable(fn):
            try:
                fn(self._selection.get("subscription_id"))
                messagebox.showinfo("Renew", "Subscription renewed.")
                self._refresh(); return
            except Exception as e:
                messagebox.showerror("Renew", str(e)); return
        messagebox.showinfo("Renew", "UI-only; logic will be wired later.")

    def _freeze(self):
        if not self._selection:
            messagebox.showwarning("Subscriptions", "Select a subscription first.")
            return
        fn = getattr(self.services, "freeze_subscription", None)
        if callable(fn):
            try:
                fn(self._selection.get("subscription_id"))
                messagebox.showinfo("Freeze", "Subscription frozen.")
                self._refresh(); return
            except Exception as e:
                messagebox.showerror("Freeze", str(e)); return
        messagebox.showinfo("Freeze", "UI-only; logic will be wired later.")

    def _cancel(self):
        if not self._selection:
            messagebox.showwarning("Subscriptions", "Select a subscription first.")
            return
        fn = getattr(self.services, "cancel_subscription", None)
        if callable(fn):
            try:
                fn(self._selection.get("subscription_id"))
                messagebox.showinfo("Cancel", "Subscription cancelled.")
                self._refresh(); return
            except Exception as e:
                messagebox.showerror("Cancel", str(e)); return
        messagebox.showinfo("Cancel", "UI-only; logic will be wired later.")


# local quick test
if __name__ == "__main__":
    ctk.set_appearance_mode("dark"); ctk.set_default_color_theme("blue")
    root = ctk.CTk(); root.geometry("1200x720"); root.configure(fg_color=PALETTE["bg"])
    page = SubscriptionsPage(root, services=None); page.pack(fill="both", expand=True)
    root.mainloop()
