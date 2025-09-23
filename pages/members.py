# pages/members.py
from __future__ import annotations
import datetime as dt
import random
import threading
from typing import Any, Dict, List, Optional
import customtkinter as ctk

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
                     font=("Segoe UI Semibold", 15)).grid(row=0, column=0, sticky="w", padx=16, pady=(14,8))

class Pill(ctk.CTkFrame):
    def __init__(self, master, text: str, kind: str = "muted"):
        colors = {
            "active":   ("#1e3325", PALETTE["ok"]),
            "suspended":("#33240f", PALETTE["warn"]),
            "expired":  ("#3a1418", PALETTE["danger"]),
            "blacklisted":("#3a1418", PALETTE["danger"]),
            "muted":    ("#2b3344", PALETTE["muted"]),
        }
        bg, fg = colors.get(kind, colors["muted"])
        super().__init__(master, fg_color=bg, corner_radius=999)
        ctk.CTkLabel(self, text=text, text_color=fg, font=("Segoe UI", 12)).grid(row=0, column=0, padx=10, pady=4)

# ---------- row widget ----------
class MemberRow(ctk.CTkFrame):
    """Lightweight list row."""
    def __init__(self, master, member: Dict[str, Any], on_open):
        super().__init__(master, fg_color=PALETTE["card"], corner_radius=10)
        self.member = member
        self.on_open = on_open

        self.grid_columnconfigure(0, weight=10)  # ID
        self.grid_columnconfigure(1, weight=28)  # Name
        self.grid_columnconfigure(2, weight=18)  # Phone
        self.grid_columnconfigure(3, weight=12)  # Join
        self.grid_columnconfigure(4, weight=12)  # Debt
        self.grid_columnconfigure(5, weight=12)  # Status
        self.grid_columnconfigure(6, weight=8)   # Action

        mid = str(member.get("id","—"))
        name = f"{member.get('first_name','')} {member.get('last_name','')}".strip() or "—"
        phone = member.get("phone","—")
        join = member.get("join_date","—")
        try:
            if isinstance(join, (dt.date, dt.datetime)):
                join = join.strftime("%Y-%m-%d")
        except Exception:
            pass
        debt_val = float(member.get("debt", 0) or 0)
        debt = f"{int(debt_val)} DA" if debt_val > 0 else "—"
        status_raw = (member.get("status") or "active").lower()
        status_kind = (
            "active" if status_raw == "active" else
            "suspended" if status_raw == "suspended" else
            "expired" if status_raw == "expired" else
            "blacklisted" if status_raw == "blacklisted" else
            "muted"
        )

        ctk.CTkLabel(self, text=mid, text_color=PALETTE["text"]).grid(row=0, column=0, padx=(12,8), pady=8, sticky="w")
        ctk.CTkLabel(self, text=name, text_color=PALETTE["text"]).grid(row=0, column=1, padx=8, pady=8, sticky="w")
        ctk.CTkLabel(self, text=phone, text_color=PALETTE["muted"]).grid(row=0, column=2, padx=8, pady=8, sticky="w")
        ctk.CTkLabel(self, text=join, text_color=PALETTE["muted"]).grid(row=0, column=3, padx=8, pady=8, sticky="w")
        ctk.CTkLabel(self, text=debt, text_color=PALETTE["muted"]).grid(row=0, column=4, padx=8, pady=8, sticky="w")

        self.pill = Pill(self, text=status_raw.capitalize(), kind=status_kind)
        self.pill.grid(row=0, column=5, padx=8, pady=8, sticky="w")

        btn = ctk.CTkButton(self, text="Open", height=28, corner_radius=12,
                            fg_color="#2b3344", hover_color="#38445a",
                            command=lambda: self.on_open(self.member))
        btn.grid(row=0, column=6, padx=(8,12), pady=8, sticky="e")

        # row-level click only (avoid double open)
        self.bind("<Button-1>", lambda _e: self.on_open(self.member))

# ---------- page ----------
class MembersPage(ctk.CTkFrame):
    """
    FAST Members list:
      - Async data fetch (thread)
      - Pagination (page_size=50)
      - Debounced, cancelable refresh
    """
    def __init__(self, master, services: Optional[object] = None, page_size: int = 50):
        super().__init__(master, fg_color=PALETTE["surface"])
        self.services = services
        self.page_size = page_size

        # state
        self._after_handle = None      # debounce
        self._fetch_seq = 0            # cancel stale fetches
        self._rows: List[MemberRow] = []
        self._data: List[Dict[str, Any]] = []
        self._page = 0

        # root grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(4, weight=1)

        # title
        title = SectionCard(self, "Members — Live Search & List")
        title.grid(row=0, column=0, sticky="ew", padx=12, pady=(12,8))

        # toolbar
        bar = ctk.CTkFrame(self, fg_color=PALETTE["card"], corner_radius=16)
        bar.grid(row=1, column=0, sticky="ew", padx=12, pady=8)
        for i in range(12): bar.grid_columnconfigure(i, weight=1)

        ctk.CTkLabel(bar, text="Search", text_color=PALETTE["muted"]).grid(row=0, column=0, padx=(12,8), pady=10, sticky="w")
        self.ent_q = ctk.CTkEntry(bar, placeholder_text="Name, phone, or ID…")
        self.ent_q.grid(row=0, column=1, columnspan=3, sticky="ew", padx=(0,8), pady=10)
        self.ent_q.bind("<KeyRelease>", lambda _e: self._debounced_refresh())

        ctk.CTkLabel(bar, text="Status", text_color=PALETTE["muted"]).grid(row=0, column=4, padx=(12,8), pady=10, sticky="w")
        try:
            self.opt_status = ctk.CTkOptionMenu(bar, values=["All","active","suspended","expired","blacklisted"],
                                                command=lambda _v: self._refresh())
            self.opt_status.set("All")
        except Exception:
            self.opt_status = ctk.CTkEntry(bar); self.opt_status.insert(0, "All")
        self.opt_status.grid(row=0, column=5, sticky="w", pady=10)

        self.btn_refresh = ctk.CTkButton(bar, text="Refresh", height=30, corner_radius=14,
                                         fg_color="#2a3550", hover_color="#334066",
                                         command=self._refresh)
        self.btn_refresh.grid(row=0, column=8, padx=(8,6), pady=10, sticky="e")

        ctk.CTkButton(bar, text="Add member", height=30, corner_radius=14,
                      fg_color=PALETTE["accent"], hover_color="#3f70cc",
                      command=lambda: self._open_member_form(None)).grid(row=0, column=9, padx=(6,12), pady=10, sticky="e")

        # header
        header = SectionCard(self, "Results")
        header.grid(row=2, column=0, sticky="new", padx=12, pady=(8,0))
        hdr = ctk.CTkFrame(header, fg_color=PALETTE["card2"], corner_radius=12)
        hdr.grid(row=1, column=0, sticky="ew", padx=10, pady=(0,8))
        labels = ("ID", "Name", "Phone", "Join", "Debt", "Status", "")
        weights = (10, 28, 18, 12, 12, 12, 8)
        for i, (txt, w) in enumerate(zip(labels, weights)):
            ctk.CTkLabel(hdr, text=txt, text_color=PALETTE["muted"]).grid(
                row=0, column=i, padx=(12 if i==0 else 8, 8), pady=8, sticky="w"
            )
            hdr.grid_columnconfigure(i, weight=w)

        # list
        self.listbox = ctk.CTkScrollableFrame(self, fg_color=PALETTE["card2"], corner_radius=12)
        self.listbox.grid(row=4, column=0, sticky="nsew", padx=12, pady=(8,12))

        # pager
        pager = ctk.CTkFrame(self, fg_color="transparent")
        pager.grid(row=3, column=0, sticky="ew", padx=12, pady=(6,0))
        pager.grid_columnconfigure(0, weight=1)
        pager.grid_columnconfigure(1, weight=1)
        pager.grid_columnconfigure(2, weight=1)
        self.btn_prev = ctk.CTkButton(pager, text="◀ Prev", command=self._prev_page, height=28, corner_radius=10)
        self.lbl_page = ctk.CTkLabel(pager, text="Page 1 / 1", text_color=PALETTE["muted"])
        self.btn_next = ctk.CTkButton(pager, text="Next ▶", command=self._next_page, height=28, corner_radius=10)
        self.btn_prev.grid(row=0, column=0, sticky="w")
        self.lbl_page.grid(row=0, column=1)
        self.btn_next.grid(row=0, column=2, sticky="e")

        # initial
        self._refresh()

    # ---------- behavior ----------
    def _debounced_refresh(self, ms: int = 350):
        try:
            if self._after_handle: self.after_cancel(self._after_handle)
        except Exception:
            pass
        self._after_handle = self.after(ms, self._refresh)

    def _get_status_value(self) -> Optional[str]:
        try:
            val = self.opt_status.get()
            return None if val == "All" else val
        except Exception:
            txt = self.opt_status.get().strip().lower()
            return None if txt in ("", "all") else txt

    def _set_loading(self, is_loading: bool, note: str = "Loading…"):
        try:
            self.btn_refresh.configure(state=("disabled" if is_loading else "normal"),
                                       text=("Refreshing…" if is_loading else "Refresh"))
        except Exception:
            pass
        # wipe list when loading
        if is_loading:
            self._clear_list()
            ctk.CTkLabel(self.listbox, text=note, text_color=PALETTE["muted"]).pack(padx=12, pady=12, anchor="w")

    def _clear_list(self):
        for r in getattr(self, "_rows", []):
            try: r.destroy()
            except Exception: pass
        self._rows.clear()
        for child in self.listbox.winfo_children():
            try: child.destroy()
            except Exception: pass

    def _refresh(self):
        # cancel debounce
        try:
            if self._after_handle: self.after_cancel(self._after_handle)
        except Exception:
            pass
        self._after_handle = None

        self._page = 0  # reset to first page
        self._fetch_seq += 1
        seq = self._fetch_seq
        self._set_loading(True)

        q = (self.ent_q.get() or "").strip()
        status = self._get_status_value()

        # run fetch off the UI thread
        def worker():
            data = self._fetch_rows(q, status)
            # switch back to UI thread only if still current
            def finish():
                if seq != self._fetch_seq:
                    return
                self._data = data
                self._set_loading(False)
                self._render_page()
            try:
                self.after(0, finish)
            except Exception:
                pass
        threading.Thread(target=worker, daemon=True).start()

    def _fetch_rows(self, q: str, status: Optional[str]) -> List[Dict[str, Any]]:
        # 1) Try backend (may be slow—hence thread)
        if self.services and hasattr(self.services, "find_members"):
            try:
                data = self.services.find_members(q, status) or []
                for m in data: m.setdefault("debt", 0)
                return data
            except Exception:
                pass

        # 2) Demo data (fast, deterministic)
        rng = random.Random(hash(q + (status or "")) & 0xffffffff)
        first = ["Nadia","Hind","Amine","Karim","Sara","Yasmine","Omar","Samir","Aya","Mina"]
        last  = ["K.","B.","M.","A.","L.","D.","T.","R.","S.","N."]
        out = []
        # simulate 800 to stress-test; pagination keeps UI fast
        for i in range(1, 801):
            st = status or rng.choice(["active","active","suspended","expired"])
            out.append({
                "id": 1000 + i,
                "first_name": rng.choice(first),
                "last_name":  rng.choice(last),
                "phone": f"05{rng.randint(5,9)} {rng.randint(100,999)} {rng.randint(100,999)}",
                "status": st,
                "join_date": (dt.date.today() - dt.timedelta(days=rng.randint(1, 800))).strftime("%Y-%m-%d"),
                "debt": rng.choice([0,0,0,200,350,600]),
            })
        ql = q.lower()
        if ql:
            out = [m for m in out if ql in str(m["id"]).lower()
                   or ql in (m["first_name"] + " " + m["last_name"]).lower()
                   or ql in m["phone"].replace(" ","")]
        if status:
            out = [m for m in out if (m.get("status") or "").lower() == status.lower()]
        return out

    # ----- pagination -----
    def _page_slice(self) -> List[Dict[str, Any]]:
        start = self._page * self.page_size
        end = start + self.page_size
        return self._data[start:end]

    def _render_page(self):
        self._clear_list()

        rows = self._page_slice()
        if not rows:
            ctk.CTkLabel(self.listbox, text="No members found", text_color=PALETTE["muted"]).pack(
                padx=12, pady=12, anchor="w"
            )
        else:
            for m in rows:
                row = MemberRow(self.listbox, m, on_open=self._open_member_form)
                row.pack(fill="x", padx=10, pady=6)
                self._rows.append(row)

        # page label + buttons
        total = max(1, (len(self._data) + self.page_size - 1) // self.page_size)
        try:
            self.lbl_page.configure(text=f"Page {self._page+1} / {total}")
            self.btn_prev.configure(state=("disabled" if self._page <= 0 else "normal"))
            self.btn_next.configure(state=("disabled" if self._page >= total-1 else "normal"))
        except Exception:
            pass

        # ensure top
        try:
            self.listbox._parent_canvas.yview_moveto(0.0)
        except Exception:
            pass

    def _prev_page(self):
        if self._page <= 0:
            return
        self._page -= 1
        self._render_page()

    def _next_page(self):
        total = max(1, (len(self._data) + self.page_size - 1) // self.page_size)
        if self._page >= total - 1:
            return
        self._page += 1
        self._render_page()

    # ----- routing to full-page form -----
    def _open_member_form(self, member: Optional[Dict[str, Any]]):
        from pages.member_form_page import MemberFormPage

        # hide self
        try: self.pack_forget()
        except Exception: self.grid_forget()

        def _back_or_saved(_member_or_none):
            try: form.destroy()
            except Exception: pass
            try: self.pack(fill="both", expand=True)
            except Exception: self.grid(row=0, column=0, sticky="nsew")
            # refresh current page quickly (don’t re-fetch unless you want to)
            self._render_page()

        form = MemberFormPage(self.master, services=self.services, on_done=_back_or_saved, member=member)
        form.pack(fill="both", expand=True)


# Local preview
if __name__ == "__main__":
    ctk.set_appearance_mode("dark"); ctk.set_default_color_theme("blue")
    root = ctk.CTk(); root.geometry("1200x720"); root.configure(fg_color=PALETTE["bg"])
    page = MembersPage(root, services=None); page.pack(fill="both", expand=True)
    root.mainloop()
