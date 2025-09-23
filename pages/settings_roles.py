# /pages/settings_roles.py
# GymPro — Settings: Roles & Permissions + Users Management (UI-only, service-ready)
from __future__ import annotations
from typing import Any, Dict, List, Optional
import customtkinter as ctk
from tkinter import messagebox

PALETTE = {
    "bg":"#0f1218","surface":"#151a22","card":"#1b2130","card2":"#1e2636",
    "accent":"#4f8cff","muted":"#8b93a7","text":"#e8ecf5",
    "ok":"#22c55e","warn":"#f59e0b","danger":"#ef4444"
}
ROLES = ["Admin", "Cashier", "Trainer", "Auditor"]

# ---------- common ----------
class SectionCard(ctk.CTkFrame):
    def __init__(self, master, title: str):
        super().__init__(master, fg_color=PALETTE["card"], corner_radius=16)
        # card uses GRID internally, so children must also use GRID
        self.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(self, text=title, text_color=PALETTE["text"], font=("Segoe UI Semibold", 15))\
            .grid(row=0, column=0, sticky="w", padx=16, pady=(14,8))

class Pill(ctk.CTkFrame):
    def __init__(self, master, text: str, *, kind: str = "muted"):
        colors = {
            "ok": ("#20321f", PALETTE["ok"]),
            "warn": ("#33240f", PALETTE["warn"]),
            "danger": ("#3a1418", PALETTE["danger"]),
            "muted": ("#2b3344", PALETTE["muted"]),
            "primary": (PALETTE["accent"], PALETTE["text"]),
        }
        bg, fg = colors.get(kind, colors["muted"])
        super().__init__(master, fg_color=bg, corner_radius=100)
        ctk.CTkLabel(self, text=text, text_color=fg, font=("Segoe UI", 12)).grid(row=0, column=0, padx=10, pady=4)

# ---------- matrix (placeholder kept minimal) ----------
class RolesMatrix(ctk.CTkScrollableFrame):
    COLS = ["Dashboard","Members","Subscriptions","Attendance","POS","Inventory","Accounting","Reports","Settings"]
    def __init__(self, master, on_toggle):
        super().__init__(master, fg_color="transparent")
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", padx=8, pady=(0,6))
        ctk.CTkLabel(hdr, text="Role", text_color=PALETTE["muted"]).grid(row=0, column=0, padx=10, sticky="w")
        for i, col in enumerate(self.COLS, start=1):
            ctk.CTkLabel(hdr, text=col, text_color=PALETTE["muted"]).grid(row=0, column=i, padx=8)
        self._rows=[]
        for role in ROLES:
            row = ctk.CTkFrame(self, fg_color=PALETTE["card2"], corner_radius=12)
            row.pack(fill="x", padx=8, pady=6)
            ctk.CTkLabel(row, text=role, text_color=PALETTE["text"]).grid(row=0, column=0, padx=10, pady=8, sticky="w")
            for i, col in enumerate(self.COLS, start=1):
                sw = ctk.CTkSwitch(row, text="", onvalue=True, offvalue=False,
                                   command=lambda rl=role, mod=col: on_toggle(rl, mod))
                sw.select() if role == "Admin" else sw.deselect()
                sw.grid(row=0, column=i, padx=8)
            self._rows.append(row)

# ---------- users UI ----------
class UsersTable(ctk.CTkScrollableFrame):
    COLS = ("Username","Display","Role","Status","Actions")
    def __init__(self, master, on_edit, on_reset_pw, on_delete):
        super().__init__(master, fg_color="transparent")
        hdr = ctk.CTkFrame(self, fg_color="transparent"); hdr.pack(fill="x", padx=8, pady=(0,6))
        for i, t in enumerate(self.COLS):
            ctk.CTkLabel(hdr, text=t, text_color=PALETTE["muted"]).grid(row=0, column=i, padx=(12 if i==0 else 8,8), sticky="w")
        self._rows=[]; self._data=[]
        self._on_edit = on_edit
        self._on_reset = on_reset_pw
        self._on_delete = on_delete

    def set_rows(self, rows: List[Dict[str,Any]]):
        for w in self._rows: w.destroy()
        self._rows.clear(); self._data = rows
        for u in rows:
            row = ctk.CTkFrame(self, fg_color=PALETTE["card2"], corner_radius=12)
            row.pack(fill="x", padx=8, pady=6)
            ctk.CTkLabel(row, text=u["username"], text_color=PALETTE["text"]).grid(row=0, column=0, padx=12, pady=8, sticky="w")
            ctk.CTkLabel(row, text=u.get("display",""), text_color=PALETTE["muted"]).grid(row=0, column=1, padx=8, sticky="w")
            Pill(row, u["role"], kind="primary").grid(row=0, column=2, padx=8)
            ctk.CTkLabel(row, text=("disabled" if u.get("disabled") else "active"), text_color=PALETTE["muted"]).grid(row=0, column=3, padx=8)

            actions = ctk.CTkFrame(row, fg_color="transparent"); actions.grid(row=0, column=4, padx=8, sticky="e")
            edit_btn = ctk.CTkButton(actions, text="Edit Role", width=90, height=28, corner_radius=8,
                                     command=lambda uid=u["id"]: self._on_edit(uid))
            reset_btn = ctk.CTkButton(actions, text="Reset PW", width=90, height=28, corner_radius=8,
                                      command=lambda uid=u["id"]: self._on_reset(uid))
            del_btn = ctk.CTkButton(actions, text="Delete", width=90, height=28, corner_radius=8,
                                    fg_color="#3a1418", hover_color="#4a1c22",
                                    command=lambda uid=u["id"]: self._on_delete(uid))
            edit_btn.pack(side="left", padx=4)
            reset_btn.pack(side="left", padx=4)
            if u["username"] == "admin":
                del_btn.configure(state="disabled")
            del_btn.pack(side="left", padx=4)

            self._rows.append(row)

class SettingsRolesPage(ctk.CTkFrame):
    """
    UI-only.
    Expects optional services.auth with methods:
      ensure_seed_admin(), list_users(), create_user(), update_user_role(), reset_password(), delete_user()
    """
    def __init__(self, master, services: Optional[object]=None):
        super().__init__(master, fg_color=PALETTE["surface"])
        self.services = services
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        title = SectionCard(self, "Settings — Roles & Permissions")
        title.grid(row=0, column=0, sticky="ew", padx=16, pady=(16,8))

        tabs = ctk.CTkTabview(self, segmented_button_selected_color=PALETTE["accent"])
        tabs.grid(row=1, column=0, sticky="nsew", padx=16, pady=(8,16))
        tab_roles = tabs.add("Roles Matrix")
        tab_users = tabs.add("Users")

        # ----- Roles Matrix
        card_roles = SectionCard(tab_roles, "Permissions by Role")
        # place the SectionCard into the tab — we can use PACK here (different parent)
        card_roles.pack(fill="both", expand=True, padx=8, pady=8)
        # BUT: inside SectionCard we must use GRID
        card_roles.grid_rowconfigure(1, weight=1)
        card_roles.grid_columnconfigure(0, weight=1)

        matrix = RolesMatrix(card_roles, on_toggle=self._on_toggle_perm)
        matrix.grid(row=1, column=0, sticky="nsew", padx=8, pady=(0,8))  # << was pack()

        # ----- Users Management
        card_users = SectionCard(tab_users, "Users Management")
        card_users.pack(fill="both", expand=True, padx=8, pady=(8,6))
        card_users.grid_columnconfigure(0, weight=1)

        form = ctk.CTkFrame(card_users, fg_color="transparent")
        form.grid(row=1, column=0, sticky="ew", padx=12, pady=(0,8))
        form.grid_columnconfigure(5, weight=1)

        ctk.CTkLabel(form, text="Username", text_color=PALETTE["text"]).grid(row=0, column=0, padx=6, pady=6, sticky="w")
        self.ent_user = ctk.CTkEntry(form, placeholder_text="e.g., cashier1")
        self.ent_user.grid(row=0, column=1, padx=6, pady=6)

        ctk.CTkLabel(form, text="Password", text_color=PALETTE["text"]).grid(row=0, column=2, padx=6, pady=6, sticky="w")
        self.ent_pwd = ctk.CTkEntry(form, placeholder_text="••••••••", show="*")
        self.ent_pwd.grid(row=0, column=3, padx=6, pady=6)

        self.chk_show = ctk.CTkCheckBox(form, text="Show", onvalue=True, offvalue=False,
                                        command=lambda: self.ent_pwd.configure(show="" if self.chk_show.get() else "*"))
        self.chk_show.grid(row=0, column=4, padx=6, pady=6, sticky="w")

        ctk.CTkLabel(form, text="Display", text_color=PALETTE["text"]).grid(row=1, column=0, padx=6, pady=6, sticky="w")
        self.ent_disp = ctk.CTkEntry(form, placeholder_text="e.g., Cashier One")
        self.ent_disp.grid(row=1, column=1, padx=6, pady=6, sticky="w")

        ctk.CTkLabel(form, text="Role", text_color=PALETTE["text"]).grid(row=1, column=2, padx=6, pady=6, sticky="w")
        self.opt_role = ctk.CTkOptionMenu(form, values=ROLES, width=140)
        self.opt_role.set("Cashier")
        self.opt_role.grid(row=1, column=3, padx=6, pady=6, sticky="w")

        ctk.CTkButton(form, text="Add User", fg_color=PALETTE["accent"], hover_color="#3e74d6",
                      command=self._add_user).grid(row=1, column=5, padx=6, pady=6, sticky="e")

        # table
        table_card = SectionCard(card_users, "Users")
        table_card.grid(row=2, column=0, sticky="nsew", padx=8, pady=(0,8))
        table_card.grid_rowconfigure(1, weight=1)
        table_card.grid_columnconfigure(0, weight=1)

        self.tbl_users = UsersTable(table_card, on_edit=self._edit_role, on_reset_pw=self._reset_pw, on_delete=self._delete_user)
        self.tbl_users.grid(row=1, column=0, sticky="nsew", padx=8, pady=(0,10))  # << was pack()

        # initial load
        self._seed_admin_if_needed()
        self._refresh_users()

    # ----- matrix toggle (UI stub)
    def _on_toggle_perm(self, role: str, module: str):
        pass

    # ----- Users actions -----
    def _seed_admin_if_needed(self):
        func = getattr(getattr(self.services, "auth", None), "ensure_seed_admin", None)
        if callable(func):
            try: func()
            except Exception: pass

    def _refresh_users(self):
        lister = getattr(getattr(self.services, "auth", None), "list_users", None)
        if callable(lister):
            try:
                users = list(lister())
            except Exception:
                users = []
        else:
            users = [{"id":1, "username":"admin", "display":"Administrator", "role":"Admin", "disabled":False}]
        for i,u in enumerate(users):
            u.setdefault("id", i+1)
        self.tbl_users.set_rows(users)

    def _add_user(self):
        u = (self.ent_user.get() or "").strip()
        p = (self.ent_pwd.get() or "").strip()
        d = (self.ent_disp.get() or "").strip()
        r = self.opt_role.get()
        if not u or not p:
            messagebox.showwarning("Users", "Username and Password are required.")
            return
        creator = getattr(getattr(self.services, "auth", None), "create_user", None)
        ok = True
        if callable(creator):
            try:
                creator(u, p, r, display=d or None)
            except Exception as e:
                ok = False
                messagebox.showerror("Users", str(e))
        if ok:
            self.ent_user.delete(0, "end"); self.ent_pwd.delete(0, "end"); self.ent_disp.delete(0, "end")
            self.opt_role.set("Cashier")
            self._refresh_users()

    def _edit_role(self, user_id: int):
        win = ctk.CTkToplevel(self); win.title("Edit Role"); win.configure(fg_color=PALETTE["card"])
        ctk.CTkLabel(win, text="New Role", text_color=PALETTE["muted"]).grid(row=0, column=0, padx=12, pady=(12,6), sticky="w")
        opt = ctk.CTkOptionMenu(win, values=ROLES, width=160); opt.set("Cashier"); opt.grid(row=1, column=0, padx=12, pady=(0,8), sticky="w")
        def apply():
            updater = getattr(getattr(self.services, "auth", None), "update_user_role", None)
            if callable(updater):
                try: updater(user_id, opt.get())
                except Exception as e: messagebox.showerror("Users", str(e))
            win.destroy(); self._refresh_users()
        ctk.CTkButton(win, text="Apply", fg_color=PALETTE["accent"], hover_color="#3e74d6", command=apply)\
            .grid(row=2, column=0, padx=12, pady=(0,12), sticky="e")

    def _reset_pw(self, user_id: int):
        win = ctk.CTkToplevel(self); win.title("Reset Password"); win.configure(fg_color=PALETTE["card"])
        ctk.CTkLabel(win, text="New Password", text_color=PALETTE["muted"]).grid(row=0, column=0, padx=12, pady=(12,6), sticky="w")
        ent = ctk.CTkEntry(win, placeholder_text="••••••••", show="*"); ent.grid(row=1, column=0, padx=12, pady=(0,8), sticky="ew")
        def apply():
            newp = ent.get().strip()
            if not newp:
                messagebox.showwarning("Users", "Password required."); return
            do = getattr(getattr(self.services, "auth", None), "reset_password", None)
            if callable(do):
                try: do(user_id, newp)
                except Exception as e: messagebox.showerror("Users", str(e))
            win.destroy()
        ctk.CTkButton(win, text="Apply", fg_color=PALETTE["accent"], hover_color="#3e74d6", command=apply)\
            .grid(row=2, column=0, padx=12, pady=(0,12), sticky="e")

    def _delete_user(self, user_id: int):
        if not messagebox.askyesno("Users", "Delete this user?"): return
        deleter = getattr(getattr(self.services, "auth", None), "delete_user", None)
        ok = True
        if callable(deleter):
            try:
                deleter(user_id)
            except Exception as e:
                ok = False
                messagebox.showerror("Users", str(e))
        if ok:
            self._refresh_users()


if __name__ == "__main__":
    ctk.set_appearance_mode("dark"); ctk.set_default_color_theme("blue")
    root = ctk.CTk(); root.geometry("1100x700"); root.configure(fg_color=PALETTE["bg"])
    page = SettingsRolesPage(root); page.pack(fill="both", expand=True)
    root.mainloop()
