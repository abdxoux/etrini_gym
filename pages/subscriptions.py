# /pages/subscriptions.py
# GymPro — Subscriptions (Assign/Renew) — CustomTkinter
# Keep original UI; add "Manage Plans" button and support for months * days_per_month plans.
from __future__ import annotations

import datetime as dt
from typing import Any, Dict, Iterable, List, Optional, Sequence

import customtkinter as ctk

PALETTE = {
    "bg":       "#0f1218",
    "surface":  "#151a22",
    "card":     "#1b2130",
    "card2":    "#1e2636",
    "accent":   "#4f8cff",
    "accent2":  "#8b6cff",
    "muted":    "#8b93a7",
    "text":     "#e8ecf5",
    "warn":     "#f59e0b",
    "ok":       "#22c55e",
    "danger":   "#ef4444",
}

# ---------------- atoms ----------------
class SectionCard(ctk.CTkFrame):
    def __init__(self, master, title: str):
        super().__init__(master, fg_color=PALETTE["card"], corner_radius=16)
        # header row (col 0 = title, col 1 = optional right actions)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0)
        ctk.CTkLabel(self, text=title, text_color=PALETTE["text"],
                     font=("Segoe UI Semibold", 15)).grid(row=0, column=0, sticky="w", padx=16, pady=(14, 8))

class Pill(ctk.CTkFrame):
    def __init__(self, master, text: str, *, fg: str = "#2b3344", text_color: str = PALETTE["text"]):
        super().__init__(master, fg_color=fg, corner_radius=100)
        ctk.CTkLabel(self, text=text, text_color=text_color, font=("Segoe UI", 12)).pack(padx=10, pady=4)

class Table(ctk.CTkScrollableFrame):
    def __init__(self, master, headers: Sequence[str]):
        super().__init__(master, fg_color="transparent")
        self._rows: List[ctk.CTkFrame] = []
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=8, pady=(0, 4))
        for i, text in enumerate(headers):
            ctk.CTkLabel(header, text=text, text_color=PALETTE["muted"]).grid(row=0, column=i, sticky="w",
                                                                              padx=(10 if i==0 else 6, 6))

    def set_rows(self, rows: Iterable[Sequence[str]]):
        for r in self._rows:
            r.destroy()
        self._rows.clear()
        for row_data in rows:
            row = ctk.CTkFrame(self, fg_color=PALETTE["card2"], corner_radius=10)
            row.pack(fill="x", padx=8, pady=6)
            for i, txt in enumerate(row_data):
                ctk.CTkLabel(row, text=str(txt),
                             text_color=PALETTE["text"] if i==0 else PALETTE["muted"]).grid(
                    row=0, column=i, sticky="w", padx=(12 if i==0 else 8, 8), pady=8
                )
            self._rows.append(row)

# ---------------- dialogs ----------------
class PlanDialog(ctk.CTkToplevel):
    """Add / Edit plan using Months × Days/Month. Calls on_submit(data) on Save."""
    def __init__(self, master, title: str, initial: Optional[Dict[str, Any]], on_submit):
        super().__init__(master)
        self.title(title)
        self.configure(fg_color=PALETTE["surface"])
        self._on_submit = on_submit
        self.grid_columnconfigure(1, weight=1)

        # Name
        ctk.CTkLabel(self, text="Name", text_color=PALETTE["muted"]).grid(row=0, column=0, padx=12, pady=(12,6), sticky="w")
        self.ent_name = ctk.CTkEntry(self, width=320); self.ent_name.grid(row=0, column=1, padx=12, pady=(12,6), sticky="ew")

        # Months
        ctk.CTkLabel(self, text="Months", text_color=PALETTE["muted"]).grid(row=1, column=0, padx=12, pady=6, sticky="w")
        self.ent_months = ctk.CTkEntry(self, width=120); self.ent_months.grid(row=1, column=1, padx=12, pady=6, sticky="w")

        # Days per Month
        ctk.CTkLabel(self, text="Days / Month", text_color=PALETTE["muted"]).grid(row=2, column=0, padx=12, pady=6, sticky="w")
        self.ent_dpm = ctk.CTkEntry(self, width=120); self.ent_dpm.grid(row=2, column=1, padx=12, pady=6, sticky="w")

        # Price
        ctk.CTkLabel(self, text="Price (DA)", text_color=PALETTE["muted"]).grid(row=3, column=0, padx=12, pady=6, sticky="w")
        self.ent_price = ctk.CTkEntry(self, width=160); self.ent_price.grid(row=3, column=1, padx=12, pady=6, sticky="w")

        # Description
        ctk.CTkLabel(self, text="Description", text_color=PALETTE["muted"]).grid(row=4, column=0, padx=12, pady=6, sticky="nw")
        self.txt_desc = ctk.CTkTextbox(self, width=360, height=90); self.txt_desc.grid(row=4, column=1, padx=12, pady=6, sticky="ew")

        # Buttons
        btns = ctk.CTkFrame(self, fg_color="transparent"); btns.grid(row=5, column=0, columnspan=2, sticky="e", padx=12, pady=(8,12))
        ctk.CTkButton(btns, text="Cancel", corner_radius=12, fg_color="#2b3344", hover_color="#38445a",
                      command=self.destroy).grid(row=0, column=0, padx=6)
        ctk.CTkButton(btns, text="Save", corner_radius=12, fg_color="#2a3550", hover_color="#334066",
                      command=self._save).grid(row=0, column=1, padx=6)

        # Fill from initial (compat: accept legacy fields)
        if initial:
            self.ent_name.insert(0, initial.get("name",""))
            # Prefer new schema months/dpm; fallback to duration string like "30 days"
            months = initial.get("months")
            dpm = initial.get("days_per_month")
            if months is None or dpm is None:
                # best effort from duration
                try:
                    dur_days = int(str(initial.get("duration","30").split()[0]))
                except Exception:
                    dur_days = 30
                months = 1
                dpm = dur_days
            self.ent_months.insert(0, str(months))
            self.ent_dpm.insert(0, str(dpm))
            self.ent_price.insert(0, str(initial.get("price", 0)))
            self.txt_desc.insert("1.0", initial.get("description",""))

        self.grab_set()
        self.after(50, self.ent_name.focus_set)

    def _save(self):
        try:
            months = int(float(self.ent_months.get() or 1))
        except Exception:
            months = 1
        try:
            dpm = int(float(self.ent_dpm.get() or 30))
        except Exception:
            dpm = 30
        try:
            price = float(self.ent_price.get() or 0)
        except Exception:
            price = 0.0
        data = {
            "name": (self.ent_name.get() or "").strip(),
            "months": max(1, months),
            "days_per_month": max(1, dpm),
            "price": price,
            "description": self.txt_desc.get("1.0", "end").strip(),
            # keep a legacy "duration" for older code: months*dpm days
            "duration": f"{max(1, months)*max(1, dpm)} days",
        }
        if not data["name"]:
            try:
                from tkinter import messagebox
                messagebox.showwarning("Validation", "Plan name is required.")
            except Exception:
                pass
            return
        try:
            self._on_submit(data)
        finally:
            self.destroy()

class ManagePlansDialog(ctk.CTkToplevel):
    """Popup listing plans with Delete button + Add Plan."""
    def __init__(self, master, fetch_plans, on_add, on_delete, on_edit):
        super().__init__(master)
        self.title("Manage Plans")
        self.configure(fg_color=PALETTE["surface"])
        self.geometry("540x520")
        self.resizable(False, True)
        self._fetch_plans = fetch_plans
        self._on_add = on_add
        self._on_delete = on_delete
        self._on_edit = on_edit

        head = ctk.CTkFrame(self, fg_color="transparent")
        head.pack(fill="x", padx=12, pady=(12,6))
        ctk.CTkLabel(head, text="Plans", text_color=PALETTE["text"], font=("Segoe UI Semibold", 15)).pack(side="left")
        ctk.CTkButton(head, text="+ Add Plan", height=28, corner_radius=12,
                      fg_color="#2a3550", hover_color="#334066",
                      command=self._add).pack(side="right")

        self.listbox = ctk.CTkScrollableFrame(self, fg_color=PALETTE["card2"], corner_radius=12, height=420)
        self.listbox.pack(fill="both", expand=True, padx=12, pady=(0,12))

        self._render()

    def _render(self):
        for w in self.listbox.winfo_children():
            try: w.destroy()
            except Exception: pass
        for p in self._fetch_plans():
            row = ctk.CTkFrame(self.listbox, fg_color=PALETTE["card"], corner_radius=10)
            row.pack(fill="x", padx=8, pady=6)
            ctk.CTkLabel(row, text=p.get("name","—"), text_color=PALETTE["text"]).grid(row=0, column=0, padx=(12,8), pady=6, sticky="w")
            # Display as M × DPM
            m = int(p.get("months") or 1); dpm = int(p.get("days_per_month") or 30)
            ctk.CTkLabel(row, text=f"{m}  {dpm} days", text_color=PALETTE["muted"]).grid(row=0, column=1, padx=8, pady=6, sticky="w")
            ctk.CTkLabel(row, text=f"{float(p.get('price',0)):.0f} DA", text_color=PALETTE["text"]).grid(row=0, column=2, padx=8, pady=6, sticky="w")
            row.grid_columnconfigure(3, weight=1)
            ctk.CTkButton(row, text="Edit", height=26, corner_radius=10,
                          fg_color="#2b3344", hover_color="#38445a",
                          command=lambda plan=p: self._on_edit(plan)).grid(row=0, column=3, padx=6, pady=6, sticky="e")
            ctk.CTkButton(row, text="Delete", height=26, corner_radius=10,
                          fg_color=PALETTE["danger"], hover_color="#cc3a3a",
                          command=lambda pid=p.get("id") or p.get("plan_id") or p.get("name"): self._delete(pid)).grid(row=0, column=4, padx=(6,12), pady=6)

    def _add(self):
        PlanDialog(self, "Add Plan", None, lambda data: (self._on_add(data), self._render()))

    def _delete(self, plan_id: Any):
        try:
            from tkinter import messagebox
            if not messagebox.askyesno("Delete Plan", "Delete this plan?"):
                return
        except Exception:
            pass
        self._on_delete(plan_id)
        self._render()

# ---------------- specialized widgets ----------------
class MemberMiniCard(ctk.CTkFrame):
    def __init__(self, master, member: Dict[str, Any], on_select):
        super().__init__(master, fg_color=PALETTE["card2"], corner_radius=10)
        self.member = member
        self.on_select = on_select
        self.bind("<Button-1>", lambda _e: self.on_select(self.member))
        self.grid_columnconfigure(0, weight=1)
        title = f"Member #{member.get('id','—')} — {member.get('name','—')}"
        ctk.CTkLabel(self, text=title, text_color=PALETTE["text"],
                     font=("Segoe UI Semibold", 14)).grid(row=0, column=0, sticky="w", padx=12, pady=(8,0))
        meta = f"{member.get('status','Active')} • {member.get('phone','')}"
        ctk.CTkLabel(self, text=meta, text_color=PALETTE["muted"]).grid(row=1, column=0, sticky="w", padx=12, pady=(0,8))

class MemberPicker(SectionCard):
    def __init__(self, master, on_select):
        super().__init__(master, "Member")
        self.on_select = on_select
        self.search = ctk.CTkEntry(self, placeholder_text="Search member / phone / UID...")
        self.search.grid(row=1, column=0, columnspan=2, sticky="ew", padx=16, pady=(0,8))
        self.search.bind("<KeyRelease>", lambda _e: self._filter())
        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.grid(row=2, column=0, columnspan=2, sticky="nsew", padx=8, pady=(0,8))
        self.grid_rowconfigure(2, weight=1)
        self._all: List[Dict[str, Any]] = []
        self._rows: List[MemberMiniCard] = []
        self.selected_box = ctk.CTkLabel(self, text="Selected: —", text_color=PALETTE["muted"])
        self.selected_box.grid(row=3, column=0, columnspan=2, sticky="w", padx=16, pady=(0,12))

    def set_members(self, items: Iterable[Dict[str, Any]]):
        self._all = list(items)
        self._render(self._all)

    def _render(self, items: List[Dict[str, Any]]):
        for r in self._rows:
            r.destroy()
        self._rows.clear()
        for m in items:
            row = MemberMiniCard(self.scroll, m, on_select=self._select)
            row.pack(fill="x", padx=8, pady=6)
            self._rows.append(row)

    def _filter(self):
        q = self.search.get().strip().lower()
        if not q:
            self._render(self._all); return
        hits = [m for m in self._all if q in str(m.get("name","")).lower()
                or q in str(m.get("phone","")).lower()
                or q in str(m.get("uid","")).lower()]
        self._render(hits)

    def _select(self, m: Dict[str, Any]):
        self.selected_box.configure(text=f"Selected: #{m.get('id','—')} — {m.get('name','—')}")
        self.on_select(m)

class PlanCard(ctk.CTkFrame):
    """Plan card: click selects; double-click opens edit."""
    def __init__(self, master, plan: Dict[str, Any], on_pick, on_edit):
        super().__init__(master, fg_color=PALETTE["card2"], corner_radius=12)
        self.plan = plan
        self.on_pick = on_pick
        self.on_edit = on_edit
        self._active = False

        self.bind("<Button-1>", lambda _e: self.on_pick(self.plan))
        self.bind("<Double-Button-1>", lambda _e: self.on_edit(self.plan))

        for i in range(2): self.grid_columnconfigure(i, weight=1)
        ctk.CTkLabel(self, text=plan["name"], text_color=PALETTE["text"],
                     font=("Segoe UI Semibold", 14)).grid(row=0, column=0, sticky="w", padx=12, pady=(10,0))
        ctk.CTkButton(self, text="Modify", height=24, corner_radius=10,
                      fg_color="#2b3344", hover_color="#38445a",
                      command=lambda: self.on_edit(self.plan)).grid(row=0, column=1, sticky="e", padx=10, pady=(8,0))
        # show as M × DPM if provided; else show legacy duration
        m = plan.get("months"); dpm = plan.get("days_per_month")
        subtitle = f"{m} mo × {dpm} d/mo" if m and dpm else plan.get("duration","")
        ctk.CTkLabel(self, text=subtitle, text_color=PALETTE["muted"]).grid(row=1, column=0, sticky="w", padx=12, pady=(0,10))
        Pill(self, f"{plan.get('price','')} DA", fg="#2b3344").grid(row=1, column=1, sticky="e", padx=10, pady=(0,10))

    def set_active(self, active: bool):
        self._active = active
        self.configure(fg_color="#24324a" if active else PALETTE["card2"])  # solid highlight (no alpha)

class PlansCatalog(SectionCard):
    """Catalog with a header button (Manage Plans)."""
    def __init__(self, master, on_pick, on_add, on_edit, on_delete, fetch_plans_callable):
        super().__init__(master, "Plans Catalog")
        # header button on the same row/area (no layout change)
        ctk.CTkButton(self, text="Manage Plans", height=28, corner_radius=12,
                      fg_color="#2a3550", hover_color="#334066",
                      command=lambda: self._open_manage(self.winfo_toplevel())).grid(row=0, column=1, sticky="e", padx=12, pady=(10,8))

        self._on_pick = on_pick
        self._on_add = on_add
        self._on_edit = on_edit
        self._on_delete = on_delete
        self._fetch_plans = fetch_plans_callable

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.inner = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.inner.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=8, pady=(0,8))
        self._cards: List[PlanCard] = []
        self._picked_id = None

    def _open_manage(self, top):
        ManagePlansDialog(
            top,
            fetch_plans=self._fetch_plans,
            on_add=self._on_add,
            on_delete=self._on_delete,
            on_edit=self._on_edit
        )

    def set_plans(self, plans: Iterable[Dict[str, Any]]):
        for c in self._cards:
            c.destroy()
        self._cards.clear()
        col_w = 2
        for i, p in enumerate(plans):
            card = PlanCard(self.inner, p, on_pick=self._pick, on_edit=self._on_edit)
            r, c = divmod(i, col_w)
            card.grid(row=r, column=c, sticky="ew", padx=8, pady=8)
            self.inner.grid_columnconfigure(c, weight=1)
            self._cards.append(card)

    def _pick(self, plan: Dict[str, Any]):
        key = plan.get("id") or plan.get("plan_id") or plan.get("name")
        self._picked_id = key
        for c in self._cards:
            c.set_active((c.plan.get("id") or c.plan.get("plan_id") or c.plan.get("name")) == key)
        self._on_pick(plan)

# ---------------- page ----------------
class SubscriptionsPage(ctk.CTkFrame):
    """
    services (optional):
      - members.list_recent()
      - subscriptions.current(member_id), subscriptions.history(member_id, limit)
      - subscriptions.create_or_renew(member_id, plan_id, start, end, price, discount, prorate, method)
      - plans.list() / create(data) / update(id,data) / delete(id)
    """
    def __init__(self, master, services: Optional[object] = None, on_submit=None):
        super().__init__(master, fg_color=PALETTE["surface"])
        self.services = services
        self.on_submit = on_submit
        self._plans_cache: List[Dict[str, Any]] = []

        self.grid_columnconfigure(0, weight=2, uniform="col")
        self.grid_columnconfigure(1, weight=3, uniform="col")
        self.grid_rowconfigure(0, weight=1)

        # Left split (unchanged layout)
        left = ctk.CTkFrame(self, fg_color="transparent")
        left.grid(row=0, column=0, sticky="nsew", padx=(16,8), pady=16)
        left.grid_rowconfigure(1, weight=1)
        left.grid_columnconfigure(0, weight=1)

        self.member_picker = MemberPicker(left, on_select=self._select_member)
        self.member_picker.grid(row=0, column=0, sticky="nsew", pady=(0,8))

        self.plans_catalog = PlansCatalog(
            left,
            on_pick=self._pick_plan,
            on_add=self._add_plan,
            on_edit=self._edit_plan,
            on_delete=self._delete_plan,
            fetch_plans_callable=self._fetch_plans,
        )
        self.plans_catalog.grid(row=1, column=0, sticky="nsew", pady=(8,0))

        # Right split (unchanged)
        right = ctk.CTkFrame(self, fg_color="transparent")
        right.grid(row=0, column=1, sticky="nsew", padx=(8,16), pady=16)
        right.grid_rowconfigure(3, weight=1)
        right.grid_columnconfigure(0, weight=1)

        # Form
        self.card_form = SectionCard(right, "New / Renew Subscription")
        self.card_form.grid(row=0, column=0, sticky="ew", pady=(0,8))
        form = ctk.CTkFrame(self.card_form, fg_color="transparent")
        form.grid(row=1, column=0, sticky="ew", padx=12, pady=(0,10))
        form.grid_columnconfigure(1, weight=1)
        labels = ["Plan", "Start Date", "End Date", "Price (DA)", "Discount (DA)", "To Pay (DA)"]
        self.ent_plan = ctk.CTkEntry(form, state="readonly")
        self.ent_start = ctk.CTkEntry(form); self.ent_end = ctk.CTkEntry(form)
        self.ent_price = ctk.CTkEntry(form); self.ent_discount = ctk.CTkEntry(form); self.ent_topay = ctk.CTkEntry(form)
        fields = [self.ent_plan, self.ent_start, self.ent_end, self.ent_price, self.ent_discount, self.ent_topay]
        for i, lab in enumerate(labels):
            ctk.CTkLabel(form, text=lab, text_color=PALETTE["muted"]).grid(row=i, column=0, sticky="w", padx=6, pady=6)
            fields[i].grid(row=i, column=1, sticky="ew", padx=(6,8), pady=6)

        self.switch_prorate = ctk.CTkSwitch(form, text="Prorate on renew", onvalue=True, offvalue=False)
        self.switch_prorate.grid(row=len(labels), column=0, sticky="w", padx=6, pady=(6,0))

        ctk.CTkLabel(form, text="Payment Method", text_color=PALETTE["muted"]).grid(row=len(labels)+1, column=0, sticky="w", padx=6, pady=(10,4))
        try:
            self.segment_payment = ctk.CTkSegmentedButton(form, values=["Cash", "Card", "Mobile"])
            self.segment_payment.set("Cash")
            self.segment_payment.grid(row=len(labels)+1, column=1, sticky="w", padx=(6,8), pady=(6,0))
        except Exception:
            self.segment_payment = ctk.CTkEntry(form)
            self.segment_payment.insert(0, "Cash")
            self.segment_payment.grid(row=len(labels)+1, column=1, sticky="w", padx=(6,8), pady=(6,0))

        self.btn_submit = ctk.CTkButton(self.card_form, text="Create / Renew", height=36, corner_radius=20,
                                        fg_color=PALETTE["accent"], hover_color="#3e74d6",
                                        command=self._submit)
        self.btn_submit.grid(row=2, column=0, sticky="e", padx=12, pady=(0,12))

        # Current
        self.card_current = SectionCard(right, "Current Subscription")
        self.card_current.grid(row=1, column=0, sticky="ew", pady=8)
        self.lbl_current = ctk.CTkLabel(self.card_current, text="Plan: —  •  Start: —  •  End: —  •  Status: —", text_color=PALETTE["muted"])
        self.lbl_current.grid(row=1, column=0, sticky="w", padx=16, pady=(0,10))
        actions = ctk.CTkFrame(self.card_current, fg_color="transparent")
        actions.grid(row=1, column=1, sticky="e", padx=12)
        self.btn_renew = ctk.CTkButton(actions, text="Renew", height=30, corner_radius=18, fg_color=PALETTE["accent"], hover_color="#3e74d6")
        self.btn_freeze = ctk.CTkButton(actions, text="Freeze", height=30, corner_radius=18, fg_color="#263042", hover_color="#32405a")
        self.btn_cancel = ctk.CTkButton(actions, text="Cancel", height=30, corner_radius=18, fg_color="#263042", hover_color="#32405a")
        self.btn_renew.grid(row=0, column=0, padx=6); self.btn_freeze.grid(row=0, column=1, padx=6); self.btn_cancel.grid(row=0, column=2, padx=6)

        # History
        self.card_hist = SectionCard(right, "Subscription History")
        self.card_hist.grid(row=2, column=0, sticky="nsew", pady=8)
        self.card_hist.grid_rowconfigure(1, weight=1)
        self.table_hist = Table(self.card_hist, headers=("Plan","Start","End","Status","Paid"))
        self.table_hist.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=8, pady=(0,10))

        # seed
        self._selected_member: Optional[Dict[str, Any]] = None
        self._selected_plan: Optional[Dict[str, Any]] = None
        self._load_initial()

    # ---------- init data ----------
    def _load_initial(self):
        # members
        items = None
        if self.services and hasattr(self.services, "members"):
            try:
                items = list(self.services.members.list_recent())
            except Exception:
                items = None
        if not items:
            items = [{"id": 1024+i, "name": f"Member {i:04d}", "phone": "+213 6 12 34 56 78", "uid": f"UID{i:04d}", "status": "Active"}
                     for i in range(1, 8)]
        self.member_picker.set_members(items)
        self._select_member(items[0])

        # plans
        plans = self._fetch_plans()
        if not plans:
            plans = [
                {"id":"monthly16", "name":"Monthly (16d/mo)", "months":1, "days_per_month":16, "price":900, "duration":"16 days"},
                {"id":"monthly30", "name":"Monthly (30d/mo)", "months":1, "days_per_month":30, "price":1200, "duration":"30 days"},
                {"id":"quarterly16", "name":"Quarterly (16d/mo)", "months":3, "days_per_month":16, "price":2400, "duration":"48 days"},
            ]
            self._plans_cache = plans.copy()
        self.plans_catalog.set_plans(plans)
        self._pick_plan(plans[0])

        # history mock
        self.table_hist.set_rows([("Monthly (30d/mo)","2025-08-01","2025-08-31","Closed","Yes"),
                                  ("Monthly (30d/mo)","2025-07-01","2025-07-31","Closed","Yes")])

    # ---------- plan CRUD / fetch ----------
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
                        "duration": r.get("duration",""),  # legacy
                        "price": float(r.get("price",0) or 0),
                        "description": r.get("description",""),
                    })
                return out
            except Exception:
                pass
        return list(self._plans_cache)

    def _add_plan(self, data: Dict[str, Any]):
        if self.services and hasattr(self.services, "plans") and hasattr(self.services.plans, "create"):
            try:
                self.services.plans.create(data)
                self.plans_catalog.set_plans(self._fetch_plans()); return
            except Exception:
                pass
        new_id = (len(self._plans_cache) + 1) * 100
        self._plans_cache.append({"id": f"P-{new_id}", **data})
        self.plans_catalog.set_plans(self._fetch_plans())

    def _edit_plan(self, plan: Dict[str, Any]):
        def submit(upd: Dict[str, Any]):
            pid = plan.get("id") or plan.get("plan_id") or plan.get("name")
            if self.services and hasattr(self.services, "plans") and hasattr(self.services.plans, "update"):
                try:
                    self.services.plans.update(pid, upd)
                    self.plans_catalog.set_plans(self._fetch_plans()); return
                except Exception:
                    pass
            for i, p in enumerate(self._plans_cache):
                if (p.get("id") or p.get("plan_id") or p.get("name")) == pid:
                    merged = dict(p); merged.update(upd); self._plans_cache[i] = merged; break
            self.plans_catalog.set_plans(self._fetch_plans())
        PlanDialog(self.winfo_toplevel(), "Edit Plan", plan, submit)

    def _delete_plan(self, plan_id: Any):
        if self.services and hasattr(self.services, "plans") and hasattr(self.services.plans, "delete"):
            try:
                self.services.plans.delete(plan_id)
                self.plans_catalog.set_plans(self._fetch_plans()); return
            except Exception:
                pass
        self._plans_cache = [p for p in self._plans_cache if (p.get("id") or p.get("plan_id") or p.get("name")) != plan_id]
        self.plans_catalog.set_plans(self._fetch_plans())

    # ---------- member & history ----------
    def _select_member(self, m: Dict[str, Any]):
        self._selected_member = m
        info = None
        if self.services and hasattr(self.services, "subscriptions"):
            try:
                info = self.services.subscriptions.current(m["id"])
            except Exception:
                info = None
        if not info:
            today = dt.date.today()
            info = {"plan":"Monthly (30d/mo)","start": today.replace(day=1), "end": today.replace(day=1)+dt.timedelta(days=29), "status":"Active"}
        self._set_current(info)

        hist = None
        if self.services and hasattr(self.services, "subscriptions"):
            try:
                hist = self.services.subscriptions.history(m["id"], limit=20)
            except Exception:
                hist = None
        if hist:
            rows = [(h["plan"], str(h["start"]), str(h["end"]), h["status"], "Yes" if h.get("paid", True) else "No") for h in hist]
            self.table_hist.set_rows(rows)

    def _set_current(self, info: Dict[str, Any]):
        self.lbl_current.configure(text=f"Plan: {info.get('plan','—')}  •  Start: {info.get('start','—')}  •  End: {info.get('end','—')}  •  Status: {info.get('status','—')}")

    # ---------- helpers ----------
    def _duration_days(self, plan: Dict[str, Any]) -> int:
        """Compute duration days from months × days_per_month; fallback to legacy 'duration' string."""
        m = plan.get("months"); dpm = plan.get("days_per_month")
        if isinstance(m, (int, float)) and isinstance(dpm, (int, float)) and m > 0 and dpm > 0:
            return int(m) * int(dpm)
        # legacy: "30 days"
        try:
            return int(str(plan.get("duration","30").split()[0]))
        except Exception:
            return 30

    # ---------- selection & form ----------
    def _pick_plan(self, plan: Dict[str, Any]):
        self._selected_plan = plan
        self.ent_plan.configure(state="normal"); self.ent_plan.delete(0,"end"); self.ent_plan.insert(0, plan["name"]); self.ent_plan.configure(state="readonly")
        today = dt.date.today()
        self.ent_start.delete(0,"end"); self.ent_start.insert(0, today.isoformat())
        end = today + dt.timedelta(days=self._duration_days(plan)-1)
        self.ent_end.delete(0,"end"); self.ent_end.insert(0, end.isoformat())
        price = plan.get("price", 0)
        self.ent_price.delete(0,"end"); self.ent_price.insert(0, str(price))
        self.ent_discount.delete(0,"end"); self.ent_discount.insert(0, "0")
        self._recalc_topay()
        self.ent_price.bind("<KeyRelease>", lambda _e: self._recalc_topay())
        self.ent_discount.bind("<KeyRelease>", lambda _e: self._recalc_topay())

    def _recalc_topay(self):
        try: price = float(self.ent_price.get() or 0)
        except Exception: price = 0.0
        try: disc = float(self.ent_discount.get() or 0)
        except Exception: disc = 0.0
        self.ent_topay.delete(0,"end"); self.ent_topay.insert(0, f"{max(0.0, price - disc):.0f}")

    def _submit(self):
        if not getattr(self, "_selected_member", None) or not getattr(self, "_selected_plan", None):
            return
        member_id = self._selected_member["id"]
        plan_id = self._selected_plan.get("id") or self._selected_plan.get("plan_id") or self._selected_plan["name"]
        start = self.ent_start.get(); end = self.ent_end.get()
        price = float(self.ent_price.get() or 0); discount = float(self.ent_discount.get() or 0)
        prorate = bool(self.switch_prorate.get())
        method = self.segment_payment.get() if hasattr(self.segment_payment, "get") else "Cash"
        payload = dict(member_id=member_id, plan_id=plan_id, start=start, end=end,
                       price=price, discount=discount, prorate=prorate, method=method)
        if self.services and hasattr(self.services, "subscriptions"):
            try: self.services.subscriptions.create_or_renew(**payload)
            except Exception: pass
        if self.on_submit: self.on_submit(payload)

# Local preview
if __name__ == "__main__":
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    root = ctk.CTk()
    root.geometry("1400x900")
    root.configure(fg_color=PALETTE["bg"])
    page = SubscriptionsPage(root)
    page.pack(fill="both", expand=True)
    root.mainloop()
