# pages/attendance.py
# GymPro — Attendance (Scan UID & History)
# CustomTkinter. Dark identity, snappy UI, toast feedback, Enter-to-scan.

from __future__ import annotations

import datetime as dt
import random
from typing import Any, Dict, List, Optional

import customtkinter as ctk

# Try to reuse the app PALETTE if the router exposes it
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
    def __init__(self, master, text: str, kind: str):
        colors = {
            "allowed": ("#1e3325", PALETTE["ok"]),
            "denied":  ("#3a1418", PALETTE["danger"]),
            "muted":   ("#2b3344", PALETTE["muted"]),
        }
        bg, fg = colors.get(kind, colors["muted"])
        super().__init__(master, fg_color=bg, corner_radius=999)
        ctk.CTkLabel(self, text=text, text_color=fg, font=("Segoe UI", 12)).grid(row=0, column=0, padx=10, pady=4)

class Toast(ctk.CTkFrame):
    """Ephemeral inline toast; .show(text, kind, ms). Uses transparent bg to avoid invalid hex."""
    def __init__(self, master):
        super().__init__(master, fg_color="transparent")  # FIX: was '#00000000'
        self._lbl = ctk.CTkLabel(self, text="", text_color=PALETTE["text"])
        self._lbl.grid(row=0, column=0, padx=12, pady=6)
        self._after = None

    def show(self, text: str, kind: str = "ok", ms: int = 1600):
        colors = {"ok": PALETTE["ok"], "warn": PALETTE["warn"], "danger": PALETTE["danger"]}
        self._lbl.configure(text=text, text_color=colors.get(kind, PALETTE["ok"]))
        if self._after:
            try: self.after_cancel(self._after)
            except Exception: pass
        self._after = self.after(ms, lambda: self._lbl.configure(text=""))

# ---------- rows ----------
class CheckinRow(ctk.CTkFrame):
    def __init__(self, master, rec: Dict[str, Any], on_open_member=None):
        super().__init__(master, fg_color=PALETTE["card"], corner_radius=10)
        self.rec = rec
        self.on_open_member = on_open_member

        # layout weights
        self.grid_columnconfigure(0, weight=14)  # time
        self.grid_columnconfigure(1, weight=20)  # uid
        self.grid_columnconfigure(2, weight=30)  # name
        self.grid_columnconfigure(3, weight=12)  # status
        self.grid_columnconfigure(4, weight=8)   # action

        # values
        t = rec.get("time","—")
        uid = rec.get("uid","—")
        name = rec.get("name","—")
        status = (rec.get("status") or "allowed").lower()
        member_id = rec.get("member_id")

        # render
        ctk.CTkLabel(self, text=t, text_color=PALETTE["text"]).grid(row=0, column=0, padx=(12,8), pady=8, sticky="w")
        ctk.CTkLabel(self, text=uid, text_color=PALETTE["muted"]).grid(row=0, column=1, padx=8, pady=8, sticky="w")
        ctk.CTkLabel(self, text=name, text_color=PALETTE["text"]).grid(row=0, column=2, padx=8, pady=8, sticky="w")
        pill = Pill(self, status.capitalize(), status); pill.grid(row=0, column=3, padx=8, pady=8, sticky="w")

        if on_open_member and member_id:
            ctk.CTkButton(self, text="Open", height=28, corner_radius=12,
                          fg_color="#2b3344", hover_color="#38445a",
                          command=lambda: on_open_member({"id": member_id, "name": name}))\
                .grid(row=0, column=4, padx=(8,12), pady=8, sticky="e")

# ---------- page ----------
class AttendancePage(ctk.CTkFrame):
    """
    Attendance Scan + History
      - Enter UID and press Enter (or click Scan)
      - Shows toast feedback
      - Shows recent history list

    Optional services:
      services.scan_uid(uid) -> {'status':'allowed'|'denied','member_id':int|None,'name':str,'time':str}
      services.recent_checkins(limit=50) -> [{'time','uid','name','status','member_id'}]
      services.open_member(member_id)
    """
    def __init__(self, master, services: Optional[object] = None, on_open_member=None):
        super().__init__(master, fg_color=PALETTE["surface"])
        self.services = services
        self.on_open_member = on_open_member or self._default_open_member
        self._after_focus = None

        # grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)

        # title
        title = SectionCard(self, "Attendance — Scan UID & History")
        title.grid(row=0, column=0, sticky="ew", padx=12, pady=(12,8))

        # scan bar
        scan = ctk.CTkFrame(self, fg_color=PALETTE["card"], corner_radius=16)
        scan.grid(row=1, column=0, sticky="ew", padx=12, pady=8)
        for i in range(10): scan.grid_columnconfigure(i, weight=1)

        ctk.CTkLabel(scan, text="UID", text_color=PALETTE["muted"]).grid(row=0, column=0, padx=(12,8), pady=12, sticky="w")
        self.ent_uid = ctk.CTkEntry(scan, placeholder_text="Scan card / type UID…")
        self.ent_uid.grid(row=0, column=1, columnspan=5, sticky="ew", padx=(0,8), pady=12)
        self.ent_uid.bind("<Return>", lambda _e: self._scan())

        self.btn_scan = ctk.CTkButton(scan, text="Scan", height=32, corner_radius=14,
                                      fg_color="#2a3550", hover_color="#334066",
                                      command=self._scan)
        self.btn_scan.grid(row=0, column=6, padx=(8,6), pady=12, sticky="e")

        # stats strip
        stats = ctk.CTkFrame(self, fg_color=PALETTE["card"], corner_radius=16)
        stats.grid(row=2, column=0, sticky="ew", padx=12, pady=8)
        for i in range(6): stats.grid_columnconfigure(i, weight=1)
        self.lbl_today = ctk.CTkLabel(stats, text="Today: 0 check-ins", text_color=PALETTE["muted"])
        self.lbl_today.grid(row=0, column=0, padx=12, pady=10, sticky="w")
        self.lbl_allowed = ctk.CTkLabel(stats, text="Allowed: 0", text_color=PALETTE["ok"])
        self.lbl_allowed.grid(row=0, column=1, padx=12, pady=10, sticky="w")
        self.lbl_denied = ctk.CTkLabel(stats, text="Denied: 0", text_color=PALETTE["danger"])
        self.lbl_denied.grid(row=0, column=2, padx=12, pady=10, sticky="w")

        # toast (transparent frame → no invalid hex)
        self.toast = Toast(stats)
        self.toast.grid(row=0, column=5, sticky="e")

        # history header
        head = SectionCard(self, "Recent Check-ins")
        head.grid(row=3, column=0, sticky="new", padx=12, pady=(8,0))
        hdr = ctk.CTkFrame(head, fg_color=PALETTE["card2"], corner_radius=12)
        hdr.grid(row=1, column=0, sticky="ew", padx=10, pady=(0,8))
        labels = ("Time", "UID", "Member", "Status", "")
        weights = (14,20,30,12,8)
        for i, (txt, w) in enumerate(zip(labels, weights)):
            ctk.CTkLabel(hdr, text=txt, text_color=PALETTE["muted"]).grid(
                row=0, column=i, padx=(12 if i==0 else 8, 8), pady=8, sticky="w"
            )
            hdr.grid_columnconfigure(i, weight=w)

        # list
        self.listbox = ctk.CTkScrollableFrame(self, fg_color=PALETTE["card2"], corner_radius=12)
        self.listbox.grid(row=4, column=0, sticky="nsew", padx=12, pady=(8,12))
        self._rows: List[CheckinRow] = []
        self._stats = {"total": 0, "allowed": 0, "denied": 0}

        # initial history
        self._load_history()

        # focus the UID entry shortly after paint
        self.after(150, lambda: self.ent_uid.focus_set())

        # optional: shortcut on toplevel (focus only)
        try:
            self.winfo_toplevel().bind("<Control-i>", lambda e: self.ent_uid.focus_set())
        except Exception:
            pass

    # ---------- behaviors ----------
    def _default_open_member(self, payload: Dict[str, Any]):
        try:
            from tkinter import messagebox
            messagebox.showinfo("Member", f"Open member {payload.get('id')}")
        except Exception:
            pass

    def _update_stats_labels(self):
        self.lbl_today.configure(text=f"Today: {self._stats['total']} check-ins")
        self.lbl_allowed.configure(text=f"Allowed: {self._stats['allowed']}")
        self.lbl_denied.configure(text=f"Denied: {self._stats['denied']}")

    def _add_history_row(self, rec: Dict[str, Any], prepend: bool = True):
        row = CheckinRow(self.listbox, rec, on_open_member=self.on_open_member)
        if prepend and self._rows:
            row.pack(fill="x", padx=10, pady=6)
            row.lift(self._rows[0])
            self._rows.insert(0, row)
        else:
            row.pack(fill="x", padx=10, pady=6)
            self._rows.append(row)

    def _scan(self):
        uid = (self.ent_uid.get() or "").strip()
        if not uid:
            self.toast.show("Empty UID.", "warn"); return

        rec = None
        if self.services and hasattr(self.services, "scan_uid"):
            try:
                rec = self.services.scan_uid(uid) or None
            except Exception:
                rec = None

        if not rec:
            # Mock decision: 85% allowed unless ends with 0
            now = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            allowed = not uid.endswith("0") and random.random() > 0.15
            name = random.choice(["Nadia K.","Hind B.","Amine M.","Karim A.","Sara L.","Walk-in"])
            rec = {
                "time": now,
                "uid": uid,
                "name": name,
                "status": "allowed" if allowed else "denied",
                "member_id": random.choice([101, 202, 303, None]),
            }

        # Update stats
        self._stats["total"] += 1
        if (rec.get("status") or "allowed").lower() == "allowed":
            self._stats["allowed"] += 1
            self.toast.show(f"Allowed — {rec.get('name','')}", "ok")
        else:
            self._stats["denied"] += 1
            self.toast.show(f"Denied — {rec.get('name','')}", "danger")
        self._update_stats_labels()

        # Add to list (top)
        self._add_history_row(rec, prepend=True)

        # Reset entry
        self.ent_uid.delete(0, "end")
        self.ent_uid.focus_set()

    def _load_history(self):
        # Clear old
        for r in self._rows:
            try: r.destroy()
            except Exception: pass
        self._rows.clear()
        self._stats = {"total": 0, "allowed": 0, "denied": 0}

        data = None
        if self.services and hasattr(self.services, "recent_checkins"):
            try:
                data = self.services.recent_checkins(limit=50) or []
            except Exception:
                data = None

        if not data:
            # demo: last 15 entries
            data = []
            now = dt.datetime.now()
            for i in range(15):
                t = (now - dt.timedelta(minutes=4*i)).strftime("%Y-%m-%d %H:%M:%S")
                allowed = random.random() > 0.2
                data.append({
                    "time": t,
                    "uid": f"UID{random.randint(10000,99999)}",
                    "name": random.choice(["Nadia K.","Hind B.","Amine M.","Karim A.","Sara L.","Walk-in"]),
                    "status": "allowed" if allowed else "denied",
                    "member_id": random.choice([101, 202, 303, None]),
                })

        # render and compute stats
        for rec in data:
            self._add_history_row(rec, prepend=False)
            self._stats["total"] += 1
            if (rec.get("status") or "allowed").lower() == "allowed":
                self._stats["allowed"] += 1
            else:
                self._stats["denied"] += 1
        self._update_stats_labels()

# Local preview
if __name__ == "__main__":
    ctk.set_appearance_mode("dark"); ctk.set_default_color_theme("blue")
    root = ctk.CTk(); root.geometry("1200x720"); root.configure(fg_color=PALETTE["bg"])
    page = AttendancePage(root, services=None); page.pack(fill="both", expand=True)
    root.mainloop()
