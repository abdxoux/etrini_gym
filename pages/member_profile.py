# /pages/member_profile.py
# GymPro — Member Profile (CustomTkinter)
# Profile + screenshot-style form fields + subscription + visits (compact, no page scroll)

from __future__ import annotations
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple
import datetime as dt
import customtkinter as ctk
from tkinter import messagebox, filedialog

# ---- optional camera (safe if not installed) ----
try:
    import cv2
    HAS_CV2 = True
except Exception:
    HAS_CV2 = False

# ---- palette (keeps your visual ID) ----
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

STATUSES = ["active", "suspended", "expired", "blacklisted"]
SEXES = ["Male", "Female", "Other"]
PLANS = ["Monthly", "Quarterly", "Yearly"]

# ---------- atoms ----------
class SectionCard(ctk.CTkFrame):
    def __init__(self, master, title: str):
        super().__init__(master, fg_color=PALETTE["card"], corner_radius=16)
        self.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(self, text=title, text_color=PALETTE["text"],
                     font=("Segoe UI Semibold", 15)).grid(row=0, column=0, sticky="w", padx=14, pady=(10,6))

class Pill(ctk.CTkFrame):
    def __init__(self, master, text: str, bg: str, fg: str):
        super().__init__(master, fg_color=bg, corner_radius=999)
        ctk.CTkLabel(self, text=text, text_color=fg, font=("Segoe UI Semibold", 14)).grid(
            row=0, column=0, padx=12, pady=6
        )

class SmallIconBtn(ctk.CTkButton):
    def __init__(self, master, text="🗓", **kw):
        super().__init__(master, text=text, width=34, height=34, corner_radius=10,
                         fg_color="#2b3344", hover_color="#38445a", **kw)

# screenshot-style input + labeled row
class ScreenshotEntry(ctk.CTkEntry):
    def __init__(self, master, placeholder_text: str):
        super().__init__(
            master,
            placeholder_text=placeholder_text,
            height=40,
            corner_radius=10,
            fg_color="#2a313d",
            text_color=PALETTE["text"],
            placeholder_text_color="#9aa3b6",
            border_color="#455066",
            border_width=2,
        )

class FormRow(ctk.CTkFrame):
    """Label on the left + field on the right, full-width row."""
    def __init__(self, master, label_text: str, field_widget: ctk.CTkBaseClass):
        super().__init__(master, fg_color="transparent")
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(self, text=label_text, text_color=PALETTE["text"]).grid(
            row=0, column=0, sticky="w", padx=(0,12)
        )
        field_widget.grid(row=0, column=1, sticky="ew")
        self.field = field_widget

class BigOptionMenu(ctk.CTkOptionMenu):
    def __init__(self, master, values: Sequence[str]):
        super().__init__(master, values=list(values), height=36, corner_radius=12,
                         fg_color="#2b3344", button_color="#2b3344",
                         button_hover_color="#3a455e", text_color=PALETTE["text"])

class Table(ctk.CTkScrollableFrame):
    def __init__(self, master, headers: Sequence[str]):
        super().__init__(master, fg_color="transparent")
        self._rows: List[ctk.CTkFrame] = []
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", padx=8, pady=(0,2))
        for i, name in enumerate(headers):
            ctk.CTkLabel(hdr, text=name, text_color=PALETTE["muted"]).grid(
                row=0, column=i, sticky="w", padx=(12 if i==0 else 8, 8)
            )

    def set_rows(self, rows: Iterable[Sequence[str]]):
        for r in self._rows:
            r.destroy()
        self._rows.clear()
        for data in rows:
            row = ctk.CTkFrame(self, fg_color=PALETTE["card2"], corner_radius=10)
            row.pack(fill="x", padx=8, pady=4)
            for i, txt in enumerate(data):
                ctk.CTkLabel(row, text=str(txt),
                             text_color=PALETTE["text"] if i in (0, 3) else PALETTE["muted"]).grid(
                    row=0, column=i, sticky="w", padx=(12 if i==0 else 8, 8), pady=6
                )
            self._rows.append(row)

# ---------- page ----------
class MemberProfilePage(ctk.CTkFrame):
    """
    services (optional):
      - members.get(id), members.update(id, data)
      - subscriptions.current(id)
      - checkins.history(id, limit)
    """
    def __init__(self, master, services: Optional[object] = None,
                 member_id: Optional[str] = None, on_back=None):
        super().__init__(master, fg_color=PALETTE["surface"])
        self.services = services
        self.member_id = member_id or "mem_demo_001"
        self.on_back = on_back

        # camera state
        self._photo_path = ""
        self._cam = None
        self._cam_running = False
        self._stream_after = None

        # ===== Top-level grid (NO page scrolling) =====
        # Row 0: Title (fixed)     -> weight 0
        # Row 1: Upper (two cols)  -> weight 3  (shrinks first)
        # Row 2: Bottom row        -> weight 1  (kept visible)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=3)
        self.grid_rowconfigure(2, weight=1)

        # ===== Title bar =====
        title = SectionCard(self, "Member Details")
        title.grid(row=0, column=0, sticky="ew", padx=10, pady=(10,6))
        title.grid_columnconfigure(0, weight=1)
        ctk.CTkButton(title, text="Save", height=30, corner_radius=16,
                      fg_color=PALETTE["accent"], hover_color="#3e74d6",
                      command=self._save).grid(row=0, column=1, sticky="e", padx=10)

        # ===== Upper composite (2 columns) =====
        upper = ctk.CTkFrame(self, fg_color="transparent")
        upper.grid(row=1, column=0, sticky="nsew", padx=10, pady=4)
        upper.grid_columnconfigure(0, weight=1, uniform="u")
        upper.grid_columnconfigure(1, weight=1, uniform="u")
        upper.grid_rowconfigure(0, weight=1)

        # ---- LEFT: Profile Card
        left = SectionCard(upper, "Profile")
        left.grid(row=0, column=0, sticky="nsew", padx=(0,6))
        left.grid_rowconfigure(1, weight=1)
        left.grid_columnconfigure(0, weight=1)

        pf = ctk.CTkFrame(left, fg_color="transparent")
        pf.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0,8))
        pf.grid_columnconfigure(0, weight=1)

        # photo + capture/upload
        photo_row = ctk.CTkFrame(pf, fg_color="transparent")
        photo_row.grid(row=0, column=0, sticky="ew")
        self.photo_box = ctk.CTkFrame(photo_row, width=130, height=150, fg_color=PALETTE["card2"], corner_radius=12)
        self.photo_box.grid(row=0, column=0, rowspan=3, sticky="w", padx=(0,10))
        self.photo_box.grid_propagate(False)
        ctk.CTkLabel(self.photo_box, text="Photo", text_color=PALETTE["muted"]).place(relx=0.5, rely=0.5, anchor="center")
        ctk.CTkButton(photo_row, text="capture", height=38, corner_radius=20,
                      fg_color="#2b3344", hover_color="#38445a",
                      command=self._capture_photo).grid(row=0, column=1, sticky="ew", pady=(6,6))
        ctk.CTkButton(photo_row, text="upload", height=38, corner_radius=20,
                      fg_color="#2b3344", hover_color="#38445a",
                      command=self._upload_photo).grid(row=1, column=1, sticky="ew")

        # screenshot-style LEFT form rows (ALL in same container, correct order)
        rows = ctk.CTkFrame(pf, fg_color="transparent")
        rows.grid(row=2, column=0, sticky="nsew", pady=(8,0))
        rows.grid_columnconfigure(0, weight=1)

        self.ent_first = ScreenshotEntry(rows, "First name")
        FormRow(rows, "First name *", self.ent_first).grid(row=0, column=0, sticky="ew", pady=6)

        self.ent_last = ScreenshotEntry(rows, "Last name")
        FormRow(rows, "Last name *", self.ent_last).grid(row=1, column=0, sticky="ew", pady=6)

        self.ent_card = ScreenshotEntry(rows, "Card UID")
        FormRow(rows, "Card UID *", self.ent_card).grid(row=2, column=0, sticky="ew", pady=6)

        self.ent_phone_left = ScreenshotEntry(rows, "Phone (optional)")
        FormRow(rows, "Phone", self.ent_phone_left).grid(row=3, column=0, sticky="ew", pady=6)

        # inline: Active pill + Status dropdown (same line)
        inline = ctk.CTkFrame(rows, fg_color="transparent")
        inline.grid(row=4, column=0, sticky="ew", pady=(6,6))
        inline.grid_columnconfigure(0, weight=0)
        inline.grid_columnconfigure(1, weight=1)
        self.active_pill = Pill(inline, "Active", bg="#1e3325", fg=PALETTE["ok"])
        self.active_pill.grid(row=0, column=0, padx=(0,10))
        self.opt_status = BigOptionMenu(inline, STATUSES); self.opt_status.set("active")
        self.opt_status.grid(row=0, column=1, sticky="w")

        self.ent_join = ScreenshotEntry(rows, dt.date.today().isoformat())
        FormRow(rows, "Join date", self.ent_join).grid(row=5, column=0, sticky="ew", pady=6)

        # ✅ Debt fixed: aligned properly under Join date
        self.ent_debt = ScreenshotEntry(rows, "0")
        FormRow(rows, "Debt (DA)", self.ent_debt).grid(row=6, column=0, sticky="ew", pady=6)

        # text feedback
        self.lbl_join = ctk.CTkLabel(left, text="Joined —", text_color=PALETTE["muted"])
        self.lbl_join.grid(row=2, column=0, sticky="w", padx=10, pady=(0,8))

        # ---- RIGHT: Subscription + Visits
        right = ctk.CTkFrame(upper, fg_color="transparent")
        right.grid(row=0, column=1, sticky="nsew", padx=(6,0))
        right.grid_rowconfigure(1, weight=1)
        right.grid_columnconfigure(0, weight=1)

        card_sub = SectionCard(right, "Current Subscription")
        card_sub.grid(row=0, column=0, sticky="ew")
        card_sub.grid_columnconfigure(0, weight=1)

        self.lbl_planline = ctk.CTkLabel(
            card_sub,
            text="Plan: Monthly   •   Start: 2025-09-01   •   End: 2025-09-30   •   Status: active",
            text_color=PALETTE["muted"])
        self.lbl_planline.grid(row=1, column=0, sticky="w", padx=10, pady=(0,6))

        act = ctk.CTkFrame(card_sub, fg_color="transparent")
        act.grid(row=2, column=0, sticky="w", padx=10, pady=(0,8))
        ctk.CTkButton(act, text="black list", height=30, corner_radius=18,
                      fg_color="#2b3344", hover_color="#3a455e").grid(row=0, column=0, padx=(0,10))
        ctk.CTkButton(act, text="Renew", height=30, corner_radius=18,
                      fg_color=PALETTE["accent"], hover_color="#3e74d6").grid(row=0, column=1, padx=6)
        ctk.CTkButton(act, text="Freeze", height=30, corner_radius=18,
                      fg_color="#263042", hover_color="#32405a").grid(row=0, column=2, padx=6)
        ctk.CTkButton(act, text="Block", height=30, corner_radius=18,
                      fg_color="#3a1418", hover_color="#5a1d22").grid(row=0, column=3, padx=6)

        card_visits = SectionCard(right, "Last Visits")
        card_visits.grid(row=1, column=0, sticky="nsew", pady=(6,0))
        card_visits.grid_rowconfigure(1, weight=1)
        self.table = Table(card_visits, headers=("Date","Status","Reason","Gate"))
        self.table.grid(row=1, column=0, sticky="nsew", padx=6, pady=(0,6))

        # ===== Bottom section (screenshot-style, always visible) =====
        bottom = ctk.CTkFrame(self, fg_color=PALETTE["card"], corner_radius=16)
        bottom.grid(row=2, column=0, sticky="nsew", padx=10, pady=(6,10))
        bottom.grid_columnconfigure((0,1), weight=1, uniform="b")

        # Left column
        col_left = ctk.CTkFrame(bottom, fg_color="transparent")
        col_left.grid(row=0, column=0, sticky="nsew", padx=8, pady=10)
        col_left.grid_columnconfigure(0, weight=1)

        self.ent_start_date_l = ScreenshotEntry(col_left, dt.date.today().isoformat())
        FormRow(col_left, "Start date", self.ent_start_date_l).grid(row=0, column=0, sticky="ew", pady=6)

        self.ent_phone_bottom = ScreenshotEntry(col_left, "Phone number")
        FormRow(col_left, "Phone number", self.ent_phone_bottom).grid(row=1, column=0, sticky="ew", pady=6)

        self.opt_sex = BigOptionMenu(col_left, SEXES); self.opt_sex.set(SEXES[0])
        FormRow(col_left, "Sex", self.opt_sex).grid(row=2, column=0, sticky="ew", pady=6)

        # Right column
        col_right = ctk.CTkFrame(bottom, fg_color="transparent")
        col_right.grid(row=0, column=1, sticky="nsew", padx=8, pady=10)
        col_right.grid_columnconfigure(0, weight=1)

        self.ent_start_date_r = ScreenshotEntry(col_right, dt.date.today().isoformat())
        FormRow(col_right, "Start date", self.ent_start_date_r).grid(row=0, column=0, sticky="ew", pady=6)

        self.ent_plan = BigOptionMenu(col_right, PLANS); self.ent_plan.set(PLANS[0])
        FormRow(col_right, "Plan", self.ent_plan).grid(row=1, column=0, sticky="ew", pady=6)

        self.ent_end_date = ScreenshotEntry(col_right, (dt.date.today() + dt.timedelta(days=30)).isoformat())
        FormRow(col_right, "Expiration date", self.ent_end_date).grid(row=2, column=0, sticky="ew", pady=6)

        # ---- load mock data ----
        self._load_member(self.member_id)
        self._load_visits(self.member_id)

    # ---------- helpers ----------
    def _upload_photo(self):
        path = filedialog.askopenfilename(
            title="Choose image",
            filetypes=[("Image files", "*.png;*.jpg;*.jpeg;*.bmp;*.webp")])
        if path:
            ctk.CTkLabel(self.photo_box, text=path, text_color=PALETTE["muted"], wraplength=110)\
                .place(relx=0.5, rely=0.5, anchor="center")
            self._photo_path = path

    def _capture_photo(self):
        if not HAS_CV2:
            messagebox.showwarning("Camera", "OpenCV (cv2) not installed.")
            return
        try:
            cam = cv2.VideoCapture(0, cv2.CAP_DSHOW) if hasattr(cv2, "CAP_DSHOW") else cv2.VideoCapture(0)
            if not cam or not cam.isOpened():
                raise RuntimeError("No camera detected.")
            ret, frame = cam.read()
            cam.release()
            if not ret:
                raise RuntimeError("Capture failed.")
            import os, time
            photos_dir = os.path.join(os.getcwd(), ".photos"); os.makedirs(photos_dir, exist_ok=True)
            path = os.path.join(photos_dir, f"member_{int(time.time())}.jpg")
            cv2.imwrite(path, frame)
            ctk.CTkLabel(self.photo_box, text=path, text_color=PALETTE["muted"], wraplength=110)\
                .place(relx=0.5, rely=0.5, anchor="center")
            self._photo_path = path
            messagebox.showinfo("Captured", f"Saved: {path}")
        except Exception as e:
            messagebox.showwarning("Camera", f"{e}")

    def _load_member(self, member_id: str):
        m = self._fetch_member(member_id)
        # left form
        self.ent_first.delete(0, "end"); self.ent_first.insert(0, m.get("first_name",""))
        self.ent_last.delete(0, "end");  self.ent_last.insert(0, m.get("last_name",""))
        self.ent_card.delete(0, "end");  self.ent_card.insert(0, m.get("card_uid",""))
        self.ent_phone_left.delete(0, "end"); self.ent_phone_left.insert(0, m.get("phone",""))
        self.opt_status.set((m.get("status") or "active").lower())
        self.ent_join.delete(0, "end");  self.ent_join.insert(0, m.get("join_date", dt.date.today().isoformat()))
        self.ent_debt.delete(0, "end");  self.ent_debt.insert(0, str(int(float(m.get("debt", 0) or 0))))
        self.lbl_join.configure(text=f"Joined {m.get('join_date', dt.date.today().isoformat())}")
        pp = m.get("photo_path","")
        if pp:
            ctk.CTkLabel(self.photo_box, text=pp, text_color=PALETTE["muted"], wraplength=110)\
                .place(relx=0.5, rely=0.5, anchor="center")
            self._photo_path = pp
        # bottom
        self.ent_phone_bottom.delete(0, "end"); self.ent_phone_bottom.insert(0, m.get("phone",""))
        self.opt_sex.set(m.get("sex","Male"))
        self.ent_start_date_l.delete(0, "end"); self.ent_start_date_l.insert(0, m.get("start_left", dt.date.today().isoformat()))
        self.ent_start_date_r.delete(0, "end"); self.ent_start_date_r.insert(0, m.get("start_right", dt.date.today().isoformat()))
        self.ent_end_date.delete(0, "end");    self.ent_end_date.insert(0, m.get("end_date", (dt.date.today()+dt.timedelta(days=30)).isoformat()))
        self.ent_plan.set(m.get("plan","Monthly"))

    def _load_visits(self, member_id: str):
        rows = self._fetch_visits(member_id)
        self.table.set_rows(rows)

    def _fetch_member(self, member_id: str) -> Dict[str, Any]:
        if self.services and hasattr(self.services, "members") and hasattr(self.services.members, "get"):
            try:
                data = self.services.members.get(member_id)
                if data: return data
            except Exception:
                pass
        today = dt.date.today().isoformat()
        return {
            "id": member_id, "first_name": "Omar", "last_name": "K.",
            "card_uid": "ABCD1234", "status": "active", "join_date": today,
            "phone": "05 700 111 22", "sex": "Male", "plan": "Monthly",
            "start_left": today, "start_right": today, "end_date": (dt.date.today()+dt.timedelta(days=30)).isoformat(),
            "debt": 0, "photo_path": ""
        }

    def _fetch_visits(self, member_id: str) -> List[Sequence[str]]:
        if self.services and hasattr(self.services, "checkins") and hasattr(self.services.checkins, "history"):
            try:
                rows = list(self.services.checkins.history(member_id, limit=10))
                return [(r.get("date","—"), r.get("status","—"), r.get("reason","—"), r.get("gate","—")) for r in rows]
            except Exception:
                pass
        now = dt.datetime.now()
        out = []
        for i in range(3):
            d = (now - dt.timedelta(days=i)).strftime("%Y-%m-%d")
            out.append((d, "allowed", "-", "A"))
        return out

    def _save(self):
        # required
        card  = self.ent_card.get().strip()
        first = self.ent_first.get().strip()
        last  = self.ent_last.get().strip()
        if not card:  messagebox.showwarning("Missing", "Card UID is required."); return
        if not first: messagebox.showwarning("Missing", "First name is required."); return
        if not last:  messagebox.showwarning("Missing", "Last name is required."); return

        # validate dates
        for val in (self.ent_join.get().strip(),
                    self.ent_start_date_l.get().strip(),
                    self.ent_start_date_r.get().strip(),
                    self.ent_end_date.get().strip()):
            if val:
                try: dt.datetime.strptime(val, "%Y-%m-%d")
                except Exception:
                    messagebox.showwarning("Invalid date", "Use YYYY-MM-DD."); return

        # validate debt
        debt_raw = self.ent_debt.get().strip() or "0"
        try:
            debt = int(float(debt_raw))
        except Exception:
            messagebox.showwarning("Invalid", "Debt must be a number."); return

        status = (self.opt_status.get() or "active").lower()
        if status not in STATUSES: status = "active"

        data = {
            "card_uid": card,
            "first_name": first,
            "last_name": last,
            "phone": self.ent_phone_left.get().strip() or self.ent_phone_bottom.get().strip(),
            "status": status,
            "join_date": self.ent_join.get().strip() or dt.date.today().isoformat(),
            "debt": debt,
            "photo_path": self._photo_path,
            # bottom details
            "sex": self.opt_sex.get(),
            "plan": self.ent_plan.get(),
            "start_left": self.ent_start_date_l.get().strip(),
            "start_right": self.ent_start_date_r.get().strip(),
            "end_date": self.ent_end_date.get().strip(),
        }

        try:
            if self.services and hasattr(self.services, "members") and hasattr(self.services.members, "update"):
                self.services.members.update(self.member_id, data)
        except Exception as e:
            messagebox.showwarning("Save", f"Could not save: {e}"); return

        # Update pill
        if status == "active":
            self.active_pill.configure(fg_color="#1e3325")
            for w in self.active_pill.winfo_children():
                if isinstance(w, ctk.CTkLabel): w.configure(text="Active", text_color=PALETTE["ok"])
        else:
            col = {"suspended":"#33240f","expired":"#3a1418","blacklisted":"#3a1418"}.get(status, "#3a1418")
            fg  = {"suspended":PALETTE["warn"],"expired":PALETTE["danger"],"blacklisted":PALETTE["danger"]}.get(status, PALETTE["danger"])
            self.active_pill.configure(fg_color=col)
            for w in self.active_pill.winfo_children():
                if isinstance(w, ctk.CTkLabel): w.configure(text=status.capitalize(), text_color=fg)

        messagebox.showinfo("Saved", "Member saved.")

# --- local preview
if __name__ == "__main__":
    ctk.set_appearance_mode("dark"); ctk.set_default_color_theme("blue")
    root = ctk.CTk(); root.geometry("1200x720"); root.configure(fg_color=PALETTE["bg"])
    page = MemberProfilePage(root, services=None, member_id="mem_demo_001")
    page.pack(fill="both", expand=True)
    root.mainloop()
