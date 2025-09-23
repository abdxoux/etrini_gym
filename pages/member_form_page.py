# pages/member_form_page.py
from __future__ import annotations
import datetime as dt
from typing import Any, Dict, Optional
import customtkinter as ctk
from tkinter import messagebox, filedialog
# Optional camera support via OpenCV
try:
    import cv2
    HAS_CV2 = True
except Exception:
    HAS_CV2 = False

PALETTE = {
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


class MemberFormPage(ctk.CTkFrame):
    """
    Full-page member form (Create/Edit) with camera/photo capture.
    Required fields: First name, Last name, Card UID.
    """
    def __init__(self, master, services: Optional[object] = None,
                 on_done=None, member: Optional[Dict[str, Any]] = None):
        super().__init__(master, fg_color=PALETTE["surface"])
        self.services = services
        self.on_done = on_done
        self._closing = False         # guard to avoid double-callbacks
        self._cam = None
        self._cam_running = False
        self._stream_after = None     # after() id for camera streaming
        self._bind_ids: Dict[str, str] = {}  # toplevel keybinding ids

        self.member = member or {
            "id": None,
            "first_name": "",
            "last_name": "",
            "card_uid": "",
            "phone": "",
            "status": "active",
            "join_date": dt.date.today().strftime("%Y-%m-%d"),
            "debt": 0,
            "photo_path": "",
        }

        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # ----- Title bar -----
        title_bar = ctk.CTkFrame(self, fg_color=PALETTE["card"], corner_radius=12)
        title_bar.grid(row=0, column=0, sticky="ew", padx=12, pady=(12, 8))
        title_bar.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            title_bar,
            text=("Edit Member" if self.member.get("id") else "Add Member"),
            text_color=PALETTE["text"],
            font=("Segoe UI Semibold", 16),
        ).grid(row=0, column=0, sticky="w", padx=14, pady=10)

        btns = ctk.CTkFrame(title_bar, fg_color="transparent")
        btns.grid(row=0, column=1, sticky="e", padx=12)
        self.btn_back = ctk.CTkButton(btns, text="Back", height=32, corner_radius=12,
                                      fg_color="#2b3344", hover_color="#38445a",
                                      command=self._go_back_fast)
        self.btn_back.pack(side="left", padx=(0, 8))
        self.btn_save = ctk.CTkButton(btns, text="Save", height=32, corner_radius=12,
                                      fg_color=PALETTE["accent"], hover_color="#3f70cc",
                                      command=self._save)
        self.btn_save.pack(side="left")

        # ----- Main content -----
        body = ctk.CTkFrame(self, fg_color=PALETTE["card2"], corner_radius=12)
        body.grid(row=1, column=0, sticky="nsew", padx=12, pady=(0, 12))
        body.grid_columnconfigure(0, weight=4)
        body.grid_columnconfigure(1, weight=3)
        body.grid_rowconfigure(0, weight=1)

        # Left column: fields
        left = ctk.CTkFrame(body, fg_color=PALETTE["card"], corner_radius=12)
        left.grid(row=0, column=0, sticky="nsew", padx=12, pady=12)
        for i in range(8):
            left.grid_rowconfigure(i, weight=0)
        left.grid_rowconfigure(8, weight=1)
        left.grid_columnconfigure(1, weight=1)

        def add_row(r, label, widget):
            ctk.CTkLabel(left, text=label, text_color=PALETTE["muted"]).grid(
                row=r, column=0, sticky="w", padx=12, pady=8
            )
            widget.grid(row=r, column=1, sticky="ew", padx=(0, 12), pady=8)

        self.ent_first = ctk.CTkEntry(left, placeholder_text="First name")
        self.ent_first.insert(0, str(self.member.get("first_name") or ""))

        self.ent_last = ctk.CTkEntry(left, placeholder_text="Last name")
        self.ent_last.insert(0, str(self.member.get("last_name") or ""))

        self.ent_card = ctk.CTkEntry(left, placeholder_text="Card UID")
        self.ent_card.insert(0, str(self.member.get("card_uid") or ""))

        self.ent_phone = ctk.CTkEntry(left, placeholder_text="Phone (optional)")
        self.ent_phone.insert(0, str(self.member.get("phone") or ""))

        self.opt_status = ctk.CTkOptionMenu(left, values=STATUSES)
        cur_status = (self.member.get("status") or "active").lower()
        if cur_status not in STATUSES:
            cur_status = "active"
        self.opt_status.set(cur_status)

        self.ent_join = ctk.CTkEntry(left, placeholder_text="YYYY-MM-DD")
        jd = self.member.get("join_date") or dt.date.today().strftime("%Y-%m-%d")
        self.ent_join.insert(0, jd)

        self.ent_debt = ctk.CTkEntry(left, placeholder_text="0")
        try:
            self.ent_debt.insert(0, str(int(float(self.member.get("debt", 0) or 0))))
        except Exception:
            self.ent_debt.insert(0, "0")

        add_row(0, "First name *", self.ent_first)
        add_row(1, "Last name *", self.ent_last)
        add_row(2, "Card UID *", self.ent_card)
        add_row(3, "Phone", self.ent_phone)
        add_row(4, "Status", self.opt_status)
        add_row(5, "Join date", self.ent_join)
        add_row(6, "Debt (DA)", self.ent_debt)

        # Right column: photo / camera
        right = ctk.CTkFrame(body, fg_color=PALETTE["card"], corner_radius=12)
        right.grid(row=0, column=1, sticky="nsew", padx=(0, 12), pady=12)
        right.grid_columnconfigure(0, weight=1)
        right.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(right, text="Photo (optional)", text_color=PALETTE["muted"]).grid(
            row=0, column=0, sticky="w", padx=12, pady=(12, 4)
        )
        self.img_box = ctk.CTkLabel(
            right, text="No photo", width=320, height=240,
            fg_color=PALETTE["card2"], corner_radius=12,
            text_color=PALETTE["muted"]
        )
        self.img_box.grid(row=1, column=0, sticky="nsew", padx=12, pady=(0, 12))

        cam_bar = ctk.CTkFrame(right, fg_color="transparent")
        cam_bar.grid(row=2, column=0, sticky="ew", padx=12, pady=(0, 12))
        cam_bar.grid_columnconfigure(0, weight=1)
        cam_bar.grid_columnconfigure(1, weight=1)
        cam_bar.grid_columnconfigure(2, weight=1)
        self.btn_start = ctk.CTkButton(cam_bar, text="Start Cam", command=self._start_camera)
        self.btn_stop  = ctk.CTkButton(cam_bar, text="Stop Cam", command=self._stop_camera)
        self.btn_snap  = ctk.CTkButton(cam_bar, text="Capture",  command=self._capture_photo)
        self.btn_start.grid(row=0, column=0, padx=6)
        self.btn_stop.grid(row=0, column=1, padx=6)
        self.btn_snap.grid(row=0, column=2, padx=6)

        ctk.CTkButton(right, text="Upload image...", command=self._upload_photo)\
            .grid(row=3, column=0, sticky="e", padx=12, pady=(0, 12))

        self._photo_path = self.member.get("photo_path") or ""
        if self._photo_path:
            self.img_box.configure(text=self._photo_path)

        # Safe toplevel key bindings (NO bind_all)
        self._bind_keys()

    # ---------- Key binding management ----------
    def _bind_keys(self):
        """Bind keys on the toplevel and remember binding ids to unbind later."""
        try:
            top = self.winfo_toplevel()
            self._bind_ids["esc"]   = top.bind("<Escape>",     lambda e: self._go_back_fast(), add="+")
            self._bind_ids["ctrls"] = top.bind("<Control-s>",  lambda e: self._save(),         add="+")
        except Exception:
            # If binding fails (very rare), just ignore; UI still works via buttons
            self._bind_ids.clear()

    def _unbind_keys(self):
        """Unbind previously registered keys from the toplevel."""
        try:
            top = self.winfo_toplevel()
            bid = self._bind_ids.get("esc")
            if bid:   top.unbind("<Escape>", bid)
            bid = self._bind_ids.get("ctrls")
            if bid:   top.unbind("<Control-s>", bid)
        except Exception:
            pass
        self._bind_ids.clear()

    # ---------- Camera helpers ----------
    def _start_camera(self):
        if not HAS_CV2:
            messagebox.showwarning("Camera", "OpenCV (cv2) not installed.")
            return
        if self._cam_running:
            return
        try:
            self._cam = cv2.VideoCapture(0, cv2.CAP_DSHOW) if hasattr(cv2, "CAP_DSHOW") else cv2.VideoCapture(0)
            if not self._cam or not self._cam.isOpened():
                raise RuntimeError("No camera detected.")
            self._cam_running = True
            self._stream_frame()
        except Exception as e:
            messagebox.showwarning("Camera", f"Cannot start camera: {e}")

    def _stop_camera(self):
        self._cam_running = False
        try:
            if self._stream_after:
                self.after_cancel(self._stream_after)
        except Exception:
            pass
        self._stream_after = None
        try:
            if self._cam and self._cam.isOpened():
                self._cam.release()
        except Exception:
            pass
        self._cam = None
        try:
            self.img_box.configure(text="No photo")
        except Exception:
            pass

    def _stream_frame(self):
        if not (HAS_CV2 and self._cam_running and self._cam and self._cam.isOpened()):
            return
        # lightweight preview text (keeps UI smooth)
        try:
            self.img_box.configure(text="Camera streaming… (Capture to save)")
        except Exception:
            pass
        self._stream_after = self.after(120, self._stream_frame)

    def _capture_photo(self):
        if not (HAS_CV2 and self._cam and self._cam.isOpened()):
            messagebox.showwarning("Camera", "Camera not running.")
            return
        ret, frame = self._cam.read()
        if not ret:
            messagebox.showwarning("Camera", "Failed to capture.")
            return
        import os, time
        photos_dir = os.path.join(os.getcwd(), ".photos")
        os.makedirs(photos_dir, exist_ok=True)
        path = os.path.join(photos_dir, f"member_{int(time.time())}.jpg")
        try:
            cv2.imwrite(path, frame)
            self._photo_path = path
            self.img_box.configure(text=path)
            messagebox.showinfo("Captured", f"Saved: {path}")
        except Exception as e:
            messagebox.showwarning("Camera", f"Could not save photo: {e}")

    def _upload_photo(self):
        path = filedialog.askopenfilename(
            title="Choose image",
            filetypes=[("Image files", "*.png;*.jpg;*.jpeg;*.bmp;*.webp")]
        )
        if path:
            self._photo_path = path
            self.img_box.configure(text=path)

    # ---------- Actions ----------
    def _go_back_fast(self):
        if self._closing:
            return
        self._closing = True
        self._stop_camera()
        self._unbind_keys()
        if callable(self.on_done):
            try:
                self.on_done(None)
            finally:
                # ensure teardown even if callback raises
                try:
                    super().destroy()
                except Exception:
                    pass

    def _save(self):
        first = self.ent_first.get().strip()
        last = self.ent_last.get().strip()
        card_uid = self.ent_card.get().strip()
        phone = self.ent_phone.get().strip()
        status = (self.opt_status.get() or "active").lower().strip()
        join_date = self.ent_join.get().strip()
        debt_raw = self.ent_debt.get().strip() or "0"

        if not first or not last:
            messagebox.showwarning("Missing", "First and last name are required.")
            return
        if not card_uid:
            messagebox.showwarning("Missing", "Card UID is required.")
            return
        try:
            dt.datetime.strptime(join_date, "%Y-%m-%d")
        except Exception:
            messagebox.showwarning("Invalid", "Join date must be YYYY-MM-DD.")
            return
        try:
            debt = int(float(debt_raw))
        except Exception:
            messagebox.showwarning("Invalid", "Debt must be a number.")
            return
        if status not in STATUSES:
            status = "active"

        updated = {
            "id": self.member.get("id"),
            "first_name": first,
            "last_name": last,
            "card_uid": card_uid,
            "phone": phone,
            "status": status,
            "join_date": join_date,
            "debt": debt,
            "photo_path": self._photo_path,
        }

        try:
            if self.services and hasattr(self.services, "save_member"):
                self.services.save_member(updated)
        except Exception as e:
            messagebox.showwarning("Save", f"Could not save via services: {e}")

        messagebox.showinfo("Saved", "Member saved successfully.")
        self._stop_camera()
        self._unbind_keys()
        if callable(self.on_done):
            self.on_done(updated)

    # Make sure keys are unbound if widget is destroyed directly
    def destroy(self):
        try:
            self._stop_camera()
            self._unbind_keys()
        finally:
            super().destroy()

if __name__ == "__main__":
    ctk.set_appearance_mode("dark")
    root = ctk.CTk()
    root.title("Member Form")
    root.geometry("700x500")
    page = MemberFormPage(root)
    page.pack(fill="both", expand=True)
    root.mainloop()