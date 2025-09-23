# pages/login.py
import customtkinter as ctk
from tkinter import messagebox
from router import PALETTE  # reuse shared palette to keep identity consistent

class LoginDialog(ctk.CTkToplevel):
    """
    UI-only Login (larger & styled).
    Uses services.auth.verify(user, password) -> {'username','display','role'}|None if provided.
    Fallback: only admin/admin is accepted.
    """
    WIDTH  = 720
    HEIGHT = 420

    def __init__(self, master, services=None):
        super().__init__(master)
        self.services = services
        self.title("Sign in · GymPro")
        self.configure(fg_color=PALETTE["bg"])
        self.resizable(False, False)
        self.result = {"user": None, "role": None}

        # center on screen
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x = (sw - self.WIDTH)//2
        y = (sh - self.HEIGHT)//3
        self.geometry(f"{self.WIDTH}x{self.HEIGHT}+{x}+{y}")

        # outer layout
        root = ctk.CTkFrame(self, fg_color=PALETTE["surface"], corner_radius=18)
        root.pack(fill="both", expand=True, padx=16, pady=16)
        root.grid_columnconfigure(1, weight=1)
        root.grid_rowconfigure(0, weight=1)

        # LEFT banner (brand)
        banner = ctk.CTkFrame(root, fg_color=PALETTE["card"], corner_radius=14)
        banner.grid(row=0, column=0, sticky="nsw", padx=14, pady=14)
        banner.grid_rowconfigure(3, weight=1)

        stripe = ctk.CTkFrame(banner, fg_color=PALETTE["accent"], corner_radius=999, width=4, height=24)
        stripe.grid(row=0, column=0, padx=(14,6), pady=(16,6), sticky="w")

        brand = ctk.CTkLabel(banner, text="GymPro", text_color=PALETTE["text"], font=("Segoe UI Semibold", 24))
        brand.grid(row=0, column=1, padx=(0,16), pady=(16,6), sticky="w")

        subtitle = ctk.CTkLabel(
            banner,
            text="Manage members, POS & attendance\nfaster — in one place.",
            text_color=PALETTE["muted"], justify="left"
        )
        subtitle.grid(row=1, column=0, columnspan=2, padx=16, sticky="w")

        bullet = ctk.CTkFrame(banner, fg_color=PALETTE["card2"], corner_radius=12)
        bullet.grid(row=2, column=0, columnspan=2, padx=14, pady=(12,16), sticky="ew")
        for i, t in enumerate(("Role-aware access", "Lightning-fast search", "POS with low-stock alerts")):
            ctk.CTkLabel(bullet, text=f"• {t}", text_color=PALETTE["text"]).grid(
                row=i, column=0, padx=10, pady=(6 if i==0 else 2,2), sticky="w"
            )

        # RIGHT panel (form)
        form = ctk.CTkFrame(root, fg_color=PALETTE["card"], corner_radius=14)
        form.grid(row=0, column=1, sticky="nsew", padx=(6,14), pady=14)
        form.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(form, text="Sign in", text_color=PALETTE["text"], font=("Segoe UI Semibold", 20))\
            .grid(row=0, column=0, columnspan=3, padx=16, pady=(16,8), sticky="w")
        ctk.CTkLabel(form, text="Use your GymPro account to continue.", text_color=PALETTE["muted"])\
            .grid(row=1, column=0, columnspan=3, padx=16, pady=(0,10), sticky="w")

        # Username
        ctk.CTkLabel(form, text="Username", text_color=PALETTE["muted"])\
            .grid(row=2, column=0, padx=(16,8), pady=6, sticky="w")
        self.ent_user = ctk.CTkEntry(form, placeholder_text="e.g., cashier1")
        self.ent_user.grid(row=2, column=1, columnspan=2, padx=(0,16), pady=6, sticky="ew")

        # Password + show
        ctk.CTkLabel(form, text="Password", text_color=PALETTE["muted"])\
            .grid(row=3, column=0, padx=(16,8), pady=6, sticky="w")
        self.ent_pwd = ctk.CTkEntry(form, placeholder_text="••••••••", show="*")
        self.ent_pwd.grid(row=3, column=1, padx=(0,8), pady=6, sticky="ew")

        def toggle_pwd():
            # flip between masked/unmasked
            show_on = getattr(self, "_show_state", False)
            self.ent_pwd.configure(show="" if not show_on else "*")
            self._show_state = not show_on

        self._show_state = False
        ctk.CTkButton(form, text="Show", width=72, height=30, corner_radius=12,
                      fg_color="#2b3344", hover_color="#38445a",
                      command=toggle_pwd).grid(row=3, column=2, padx=(0,16), pady=6, sticky="e")

        # Remember me (logic later)
        self.chk_rem = ctk.CTkCheckBox(form, text="Remember me")
        self.chk_rem.grid(row=4, column=1, padx=0, pady=(0,6), sticky="w")

        ctk.CTkLabel(form, text="Role is assigned by the admin in Settings → Roles & Permissions.",
                     text_color=PALETTE["muted"], font=("Segoe UI", 11)).grid(
            row=5, column=0, columnspan=3, padx=16, pady=(0,2), sticky="w"
        )

        # Error label
        self.lbl_err = ctk.CTkLabel(form, text="", text_color=PALETTE["danger"])
        self.lbl_err.grid(row=6, column=0, columnspan=3, padx=16, pady=(0,4), sticky="w")

        # Buttons
        btns = ctk.CTkFrame(form, fg_color="transparent")
        btns.grid(row=7, column=0, columnspan=3, padx=16, pady=(6,16), sticky="e")
        ctk.CTkButton(btns, text="Login", fg_color=PALETTE["accent"], hover_color="#3e74d6",
                      height=36, corner_radius=18, command=self._ok).pack(side="left", padx=(0,8))
        ctk.CTkButton(btns, text="Quit", fg_color="#3a1418", hover_color="#4a1c22",
                      height=36, corner_radius=18, command=self._quit).pack(side="left")

        # modal
        self.grid_columnconfigure(0, weight=1)
        self.ent_user.focus_set()
        self.transient(master)
        self.grab_set()
        self.bind("<Return>", lambda e: self._ok())
        self.bind("<Escape>", lambda e: self._quit())

    def _quit(self):
        self.result = {"user": None, "role": None}
        self.grab_release()
        self.destroy()

    def _ok(self):
        self.lbl_err.configure(text="")
        user = (self.ent_user.get() or "").strip()
        pwd  = (self.ent_pwd.get() or "").strip()
        if not user or not pwd:
            self.lbl_err.configure(text="Enter both username and password.")
            return

        info = None
        auth = getattr(getattr(self.services, "auth", None), "verify", None)
        if callable(auth):
            try:
                info = auth(user, pwd)  # {'username','display','role'} | None
            except Exception as e:
                info = None
                self.lbl_err.configure(text=f"Auth error: {e}")

        if info is None:
            if user == "admin" and pwd == "admin":
                info = {"username": "admin", "display": "Administrator", "role": "Admin"}
            else:
                self.lbl_err.configure(text="Invalid credentials.")
                return

        self.result = {
            "user": info.get("display") or info.get("username") or user,
            "role": info.get("role") or "Admin"
        }
        self.grab_release()
        self.destroy()
