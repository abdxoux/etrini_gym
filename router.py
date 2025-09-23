# router.py
# GymPro — App Shell (Header + Sidebar) + Router + Role Switching (CustomTkinter)
from __future__ import annotations
import customtkinter as ctk
from dataclasses import dataclass
from typing import Dict, Optional, Type

# -------------------- Palette (shared) --------------------
PALETTE = {
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

ROLES = ["Admin", "Cashier", "Trainer", "Auditor"]

# -------------------- Utilities --------------------
class Pill(ctk.CTkFrame):
    def __init__(self, master, text: str, *, kind: str = "muted"):
        color_map = {
            "ok": ("#20321f", PALETTE["ok"]),
            "warn": ("#33240f", PALETTE["warn"]),
            "danger": ("#3a1418", PALETTE["danger"]),
            "muted": ("#2b3344", PALETTE["muted"]),
            "primary": (PALETTE["accent"], PALETTE["text"]),
        }
        bg, fg = color_map.get(kind, color_map["muted"])
        super().__init__(master, fg_color=bg, corner_radius=100)
        ctk.CTkLabel(self, text=text, text_color=fg, font=("Segoe UI", 12)).grid(row=0, column=0, padx=10, pady=4)

class SectionTitle(ctk.CTkFrame):
    def __init__(self, master, text: str):
        super().__init__(master, fg_color="transparent")
        ctk.CTkLabel(self, text=text, text_color=PALETTE["muted"], font=("Segoe UI", 12)).pack(anchor="w", padx=12, pady=(12, 6))

# -------------------- Header (Top Bar) --------------------
class HeaderBar(ctk.CTkFrame):
    """
    Top bar with brand, online indicator, language selector, Open Gate button, and user menu (role).
    """
    def __init__(self, master, *, on_open_gate=None, on_language_change=None, get_role=None, get_user=None, on_switch_role=None):
        super().__init__(master, fg_color=PALETTE["card"], corner_radius=0, height=56)
        self.grid_columnconfigure(1, weight=1)

        # Brand / title
        brand = ctk.CTkLabel(self, text="GymPro", text_color=PALETTE["text"], font=("Segoe UI Semibold", 18))
        brand.grid(row=0, column=0, padx=16, pady=10, sticky="w")

        # Center area — current page title
        self.center_title = ctk.CTkLabel(self, text="", text_color=PALETTE["muted"], font=("Segoe UI", 13))
        self.center_title.grid(row=0, column=1, padx=6, pady=10, sticky="w")

        # Right controls
        right = ctk.CTkFrame(self, fg_color="transparent")
        right.grid(row=0, column=2, sticky="e", padx=12, pady=8)

        Pill(right, "Online", kind="ok").pack(side="left", padx=6)

        # role + user
        self.role_pill = Pill(right, "Role: Admin", kind="primary")
        self.role_pill.pack(side="left", padx=6)

        self.user_btn = ctk.CTkButton(
            right, text="User ▾", height=30, corner_radius=16,
            fg_color="#2b3344", hover_color="#38445a",
            command=lambda: self._open_user_menu(get_user, get_role, on_switch_role)
        )
        self.user_btn.pack(side="left", padx=6)

        # Language + gate
        self.lang_menu = ctk.CTkOptionMenu(right, values=["EN", "FR", "AR"], width=70,
                                           command=lambda v: on_language_change(v) if on_language_change else None)
        self.lang_menu.set("EN")
        self.lang_menu.pack(side="left", padx=6)

        ctk.CTkButton(right, text="Open Gate", height=32, corner_radius=18,
                      fg_color="#263042", hover_color="#32405a",
                      command=lambda: on_open_gate() if on_open_gate else None).pack(side="left", padx=6)

        self._get_role = get_role
        self._get_user = get_user
        self._on_switch_role = on_switch_role

    def set_page_title(self, text: str):
        self.center_title.configure(text=text)

    def refresh_role(self):
        role = "Admin"
        if callable(self._get_role):
            try:
                role = self._get_role() or "Admin"
            except Exception:
                pass
        # rebuild pill
        for w in self.role_pill.winfo_children(): w.destroy()
        self.role_pill.destroy()
        container = list(self.children.values())[-1]  # right frame
        self.role_pill = Pill(container, f"Role: {role}", kind="primary")
        self.role_pill.pack(side="left", padx=6)

    def _open_user_menu(self, get_user, get_role, on_switch_role):
        win = ctk.CTkToplevel(self)
        win.title("User")
        win.configure(fg_color=PALETTE["card"])
        win.resizable(False, False)
        ctk.CTkLabel(win, text="Current user", text_color=PALETTE["muted"]).grid(row=0, column=0, padx=14, pady=(12,4), sticky="w")
        name = (get_user() if callable(get_user) else "user") or "user"
        ctk.CTkLabel(win, text=name, text_color=PALETTE["text"], font=("Segoe UI Semibold", 14)).grid(row=1, column=0, padx=14, sticky="w")
        ctk.CTkLabel(win, text="Role", text_color=PALETTE["muted"]).grid(row=2, column=0, padx=14, pady=(10,4), sticky="w")

        cur_role = (get_role() if callable(get_role) else "Admin") or "Admin"
        role_menu = ctk.CTkOptionMenu(win, values=ROLES, width=160)
        role_menu.set(cur_role)
        role_menu.grid(row=3, column=0, padx=14, pady=(0,10), sticky="w")

        def apply():
            new_role = role_menu.get()
            if callable(on_switch_role):
                on_switch_role(new_role)
            win.destroy()

        ctk.CTkButton(win, text="Apply", fg_color=PALETTE["accent"], hover_color="#3e74d6",
                      corner_radius=14, command=apply).grid(row=4, column=0, padx=14, pady=(0,14), sticky="e")

# -------------------- Sidebar (Left Nav) --------------------
@dataclass
class NavItem:
    label: str
    route: str

DEFAULT_NAV: Dict[str, str] = {
    "Dashboard": "Dashboard",
    "Members": "Members",
    "Member Profile": "Member Profile",
    "Subscriptions": "Subscriptions",
    "Attendance": "Attendance",
    "POS": "POS",
    "Inventory": "Inventory",
    "Accounting": "Accounting",
    "Reports": "Reports",
    "Settings – Debt Policy": "Settings – Debt Policy",
    "Settings – Roles & Permissions": "Settings – Roles & Permissions",
    "Settings – Gate TCP/IP": "Settings – Gate TCP/IP",
    "Settings – Language": "Settings – Language",
    "Settings – Equipment": "Settings – Equipment",
}

RBAC_ALLOW = {
    "Dashboard": {"Admin", "Cashier", "Trainer", "Auditor"},
    "Members": {"Admin", "Cashier", "Trainer", "Auditor"},
    "Member Profile": {"Admin", "Cashier", "Trainer", "Auditor"},
    "Subscriptions": {"Admin", "Cashier", "Trainer"},
    "Attendance": {"Admin", "Trainer"},
    "POS": {"Admin", "Cashier"},
    "Inventory": {"Admin"},
    "Accounting": {"Admin", "Auditor"},
    "Reports": {"Admin", "Auditor"},
    "Settings – Debt Policy": {"Admin"},
    "Settings – Roles & Permissions": {"Admin"},
    "Settings – Gate TCP/IP": {"Admin"},
    "Settings – Language": {"Admin"},
    "Settings – Equipment": {"Admin"},
}

class SidebarNav(ctk.CTkFrame):
    def __init__(self, master, *, on_nav, get_role, nav_map: Optional[Dict[str, str]]=None):
        super().__init__(master, fg_color=PALETTE["card"], corner_radius=0, width=220)
        self.grid_rowconfigure(99, weight=1)
        self.on_nav = on_nav
        self.get_role = get_role
        self.nav_map = nav_map or DEFAULT_NAV
        self._buttons: Dict[str, ctk.CTkButton] = {}

        SectionTitle(self, "Navigation").grid(row=0, column=0, sticky="ew")
        row = 1
        for label, route in self.nav_map.items():
            b = ctk.CTkButton(self, text=label, height=36, corner_radius=10,
                              fg_color="#2b3344", hover_color="#38445a",
                              command=lambda r=route: self._nav(r))
            b.grid(row=row, column=0, sticky="ew", padx=10, pady=4)
            self._buttons[route] = b
            row += 1

        self.ver = ctk.CTkLabel(self, text="v1.0", text_color=PALETTE["muted"])
        self.ver.grid(row=99, column=0, sticky="se", padx=12, pady=10)

    def _nav(self, route: str):
        role = self.get_role() or "Admin"
        if route in RBAC_ALLOW and role not in RBAC_ALLOW[route]:
            try:
                from tkinter import messagebox
                messagebox.showwarning("Access denied", f"{role} cannot open {route}")
            except Exception:
                pass
            return
        for r, btn in self._buttons.items():
            btn.configure(fg_color="#2b3344")
        if route in self._buttons:
            self._buttons[route].configure(fg_color=PALETTE["accent"])
        self.on_nav(route)

    def refresh_state(self):
        """Visually dim/enable pages depending on role (optional)."""
        role = self.get_role() or "Admin"
        for route, btn in self._buttons.items():
            allowed = route in RBAC_ALLOW and role in RBAC_ALLOW[route]
            btn.configure(state="normal" if allowed else "disabled")

# -------------------- Router --------------------
def _lazy_import_pages() -> Dict[str, Type[ctk.CTkFrame]]:
    pages: Dict[str, Type[ctk.CTkFrame]] = {}

    def try_many(route: str, candidates: list[tuple[str, str]]):
        """
        candidates = [(module_name_without_pages_dot, class_name), ...]
        The first import that works wins; otherwise a MissingPage placeholder is used.
        """
        for mod, cls in candidates:
            try:
                module = __import__(f"pages.{mod}", fromlist=[cls])
                pages[route] = getattr(module, cls)
                return
            except Exception:
                continue
        pages[route] = _MissingPageFactory(route)

    # Dashboard
    try_many("Dashboard", [("dashboard", "DashboardPage")])

    # Members (yours is members_list.py)
    try_many("Members", [("members", "MembersPage"), ("member_list", "membersPage")])

    # Member Profile (yours matches)
    try_many("Member Profile", [("member_profile", "MemberProfilePage")])

    # Subscriptions (yours is Subscriptions.py with capital S)
    try_many("Subscriptions", [("subscriptions", "SubscriptionsPage"), ("Subscriptions", "SubscriptionsPage")])

    # Attendance (yours is attendance_scan.py)
    try_many("Attendance", [("attendance", "AttendancePage"), ("attendance_scan", "attendancePage")])

    # POS
    try_many("POS", [("pos", "POSPage"), ("pos_new_sale", "POSPage")])

    # Inventory
    try_many("Inventory", [("inventory", "inventoryPage")])

    # Accounting
    try_many("Accounting", [("accounting", "AccountingPage")])

    # Reports
    try_many("Reports", [("reports", "ReportsPage")])

    # Settings
    try_many("Settings – Debt Policy",   [("settings_debt_policy", "SettingsDebtPolicyPage")])
    try_many("Settings – Roles & Permissions", [("settings_roles", "SettingsRolesPage")])
    try_many("Settings – Gate TCP/IP",   [("settings_gate", "SettingsGatePage")])
    try_many("Settings – Language",      [("settings_language", "SettingsLanguagePage")])
    try_many("Settings – Equipment",     [("settings_equipment", "SettingsEquipmentPage")])

    return pages

def _MissingPageFactory(name: str):
    class Missing(ctk.CTkFrame):
        def __init__(self, master, services=None):
            super().__init__(master, fg_color=PALETTE["surface"])
            ctk.CTkLabel(self, text=f"{name} (not implemented)", text_color=PALETTE["text"],
                         font=("Segoe UI Semibold", 18)).pack(pady=20)
            ctk.CTkLabel(self, text="Create pages/<module>.py with <ClassName>Page", text_color=PALETTE["muted"]).pack()
    return Missing

class Router:
    def __init__(self, container: ctk.CTkFrame, services=None):
        self.container = container
        self.services = services
        self.routes = _lazy_import_pages()
        self.current: Optional[ctk.CTkFrame] = None

    def goto(self, route: str):
        if self.current is not None:
            try:
                self.current.destroy()
            except Exception:
                for w in self.current.winfo_children():
                    w.destroy()
                self.current.pack_forget()
        page_cls = self.routes.get(route) or _MissingPageFactory(route)
        self.current = page_cls(self.container, services=self.services)
        self.current.pack(fill="both", expand=True)
        return self.current

# -------------------- App Shell (Header + Sidebar + Content) --------------------
class AppShell(ctk.CTkFrame):
    def __init__(self, master, services=None, *, start_route: str = "Dashboard"):
        super().__init__(master, fg_color=PALETTE["bg"])
        self.services = services or SimpleServices()
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self.header = HeaderBar(
            self,
            on_open_gate=self._open_gate,
            on_language_change=self._set_language,
            get_role=lambda: self.services.session_role,
            get_user=lambda: self.services.user_name,
            on_switch_role=self._switch_role,
        )
        self.header.grid(row=0, column=0, columnspan=2, sticky="ew")

        self.sidebar = SidebarNav(self, on_nav=self._navigate, get_role=lambda: self.services.session_role)
        self.sidebar.grid(row=1, column=0, sticky="nsw")

        self.content = ctk.CTkFrame(self, fg_color=PALETTE["surface"])
        self.content.grid(row=1, column=1, sticky="nsew")

        self.router = Router(self.content, services=self.services)
        self._navigate(start_route)

        top = self.winfo_toplevel()
        top.bind("<Control-1>", lambda e: self._navigate("Dashboard"), add="+")
        top.bind("<Control-2>", lambda e: self._navigate("Members"), add="+")
        top.bind("<Control-3>", lambda e: self._navigate("POS"), add="+")
        top.bind("<Control-4>", lambda e: self._navigate("Attendance"), add="+")

        # reflect access for current role
        self.sidebar.refresh_state()
        self.header.refresh_role()

    def _navigate(self, route: str):
        page = self.router.goto(route)
        self.header.set_page_title(route)

    def _switch_role(self, new_role: str):
        self.services.session_role = new_role
        self.sidebar.refresh_state()
        self.header.refresh_role()

    def _open_gate(self):
        try:
            getattr(getattr(self.services, "gate", None), "open", lambda: None)()
        except Exception:
            pass

    def _set_language(self, code: str):
        try:
            getattr(getattr(self.services, "settings", None), "set_language", lambda *_: None)(code.lower())
        except Exception:
            pass

# -------------------- Minimal Services Stub --------------------
class SimpleServices:
    def __init__(self):
        self.session_role = "Admin"
        self.user_name = "user"
        # attach your real services later
