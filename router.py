# router.py
from __future__ import annotations
import customtkinter as ctk
from typing import Dict, Optional, Type

# -------------------- Palette --------------------
PALETTE = {
    "bg": "#0f1218", "surface": "#151a22", "card": "#1b2130", "card2": "#1e2636",
    "accent": "#4f8cff", "accent2": "#8b6cff", "muted": "#8b93a7", "text": "#e8ecf5",
    "ok": "#22c55e", "warn": "#f59e0b", "danger": "#ef4444",
}
ROLES = ["Admin", "Cashier", "Trainer", "Auditor"]

# -------------------- UI Bits --------------------
class Pill(ctk.CTkFrame):
    def __init__(self, master, text: str, *, kind: str = "muted"):
        cmap = {
            "ok": ("#20321f", PALETTE["ok"]), "warn": ("#33240f", PALETTE["warn"]),
            "danger": ("#3a1418", PALETTE["danger"]), "muted": ("#2b3344", PALETTE["muted"]),
            "primary": (PALETTE["accent"], PALETTE["text"]),
        }
        bg, fg = cmap.get(kind, cmap["muted"])
        super().__init__(master, fg_color=bg, corner_radius=100)
        ctk.CTkLabel(self, text=text, text_color=fg, font=("Segoe UI", 12)).grid(padx=10, pady=4)

class HeaderBar(ctk.CTkFrame):
    def __init__(self, master, *, on_open_gate=None, on_language_change=None, get_role=None, get_user=None, on_switch_role=None):
        super().__init__(master, fg_color=PALETTE["card"], corner_radius=0, height=56)
        self.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(self, text="GymPro", text_color=PALETTE["text"], font=("Segoe UI Semibold", 18)).grid(row=0, column=0, padx=16, pady=10, sticky="w")
        self.center_title = ctk.CTkLabel(self, text="", text_color=PALETTE["muted"], font=("Segoe UI", 13))
        self.center_title.grid(row=0, column=1, padx=6, pady=10, sticky="w")

        right = ctk.CTkFrame(self, fg_color="transparent"); right.grid(row=0, column=2, sticky="e", padx=12, pady=8)
        Pill(right, "Online", kind="ok").pack(side="left", padx=6)
        self.role_pill = Pill(right, "Role: Admin", kind="primary"); self.role_pill.pack(side="left", padx=6)

        self.user_btn = ctk.CTkButton(right, text="User ▾", height=30, corner_radius=16, fg_color="#2b3344", hover_color="#38445a",
                                      command=lambda: self._open_user_menu(get_user, get_role, on_switch_role))
        self.user_btn.pack(side="left", padx=6)

        self.lang_menu = ctk.CTkOptionMenu(right, values=["EN","FR","AR"], width=70,
                                           command=lambda v: on_language_change(v) if on_language_change else None)
        self.lang_menu.set("EN"); self.lang_menu.pack(side="left", padx=6)

        ctk.CTkButton(right, text="Open Gate", height=32, corner_radius=18, fg_color="#263042", hover_color="#32405a",
                      command=lambda: on_open_gate() if on_open_gate else None).pack(side="left", padx=6)

        self._get_role = get_role; self._get_user = get_user; self._on_switch_role = on_switch_role

    def set_page_title(self, text: str): self.center_title.configure(text=text)
    def refresh_role(self):
        role = (self._get_role() if callable(self._get_role) else "Admin") or "Admin"
        for w in self.role_pill.winfo_children(): w.destroy()
        self.role_pill.destroy()
        container = list(self.children.values())[-1]
        self.role_pill = Pill(container, f"Role: {role}", kind="primary"); self.role_pill.pack(side="left", padx=6)

    def _open_user_menu(self, get_user, get_role, on_switch_role):
        win = ctk.CTkToplevel(self); win.title("User"); win.configure(fg_color=PALETTE["card"]); win.resizable(False, False)
        ctk.CTkLabel(win, text="Current user", text_color=PALETTE["muted"]).grid(row=0, column=0, padx=14, pady=(12,4), sticky="w")
        name = (get_user() if callable(get_user) else "user") or "user"
        ctk.CTkLabel(win, text=name, text_color=PALETTE["text"], font=("Segoe UI Semibold",14)).grid(row=1, column=0, padx=14, sticky="w")
        ctk.CTkLabel(win, text="Role", text_color=PALETTE["muted"]).grid(row=2, column=0, padx=14, pady=(10,4), sticky="w")
        cur_role = (get_role() if callable(get_role) else "Admin") or "Admin"
        role_menu = ctk.CTkOptionMenu(win, values=ROLES, width=160); role_menu.set(cur_role)
        role_menu.grid(row=3, column=0, padx=14, pady=(0,10), sticky="w")
        ctk.CTkButton(win, text="Apply", fg_color=PALETTE["accent"], hover_color="#3e74d6", corner_radius=14,
                      command=lambda:(on_switch_role(role_menu.get()) if callable(on_switch_role) else None, win.destroy())).grid(row=4, column=0, padx=14, pady=(0,14), sticky="e")

class HomeTile(ctk.CTkButton):
    def __init__(self, master, *, label: str, route: str, on_click):
        super().__init__(master, text=label, height=96, corner_radius=16,
                         fg_color="#263042", hover_color="#32405a", command=lambda: on_click(route),
                         font=("Segoe UI Semibold", 16))

# -------------------- Missing Page --------------------
def _MissingPageFactory(name: str):
    class Missing(ctk.CTkFrame):
        def __init__(self, master, services=None):
            super().__init__(master, fg_color=PALETTE["surface"])
            ctk.CTkLabel(self, text=f"{name} (not implemented)", text_color=PALETTE["text"],
                         font=("Segoe UI Semibold", 18)).pack(pady=20)
            ctk.CTkLabel(self, text="Create pages/<module>.py with <ClassName>Page", text_color=PALETTE["muted"]).pack()
    return Missing

# -------------------- Built-in Pages (no external files) --------------------
class SettingsHubPage(ctk.CTkFrame):
    def __init__(self, master, services=None):
        super().__init__(master, fg_color=PALETTE["bg"]); self.services = services
        tabs = ctk.CTkSegmentedButton(self, values=["roles","debt policy","gate","language","equipment"],
                                      command=self._switch_tab)
        tabs.grid(row=0, column=0, sticky="ew", padx=16, pady=(16,8)); tabs.set("debt policy")
        status = ctk.CTkFrame(self, fg_color="transparent"); status.grid(row=1, column=0, sticky="ew", padx=16)
        Pill(status, "Enabled", kind="ok").pack(side="left", padx=4)
        Pill(status, "Grace Active", kind="warn").pack(side="left", padx=4)
        self.content = ctk.CTkFrame(self, fg_color=PALETTE["surface"], corner_radius=12)
        self.content.grid(row=2, column=0, sticky="nsew", padx=16, pady=16)
        self.grid_rowconfigure(2, weight=1); self.grid_columnconfigure(0, weight=1)
        self._switch_tab("debt policy")

    def _clear(self): [w.destroy() for w in self.content.winfo_children()]
    def _switch_tab(self, name: str):
        self._clear()
        mapping = {
            "roles": ("settings_roles","SettingsRolesPage"),
            "debt policy": ("settings_debt_policy","SettingsDebtPolicyPage"),
            "gate": ("settings_gate","SettingsGatePage"),
            "language": ("settings_language","SettingsLanguagePage"),
            "equipment": ("settings_equipment","SettingsEquipmentPage"),
        }
        mod, cls = mapping.get(name, (None,None))
        if mod:
            try:
                module = __import__(f"pages.{mod}", fromlist=[cls])
                getattr(module, cls)(self.content, services=self.services).pack(fill="both", expand=True)
                return
            except Exception:
                pass
        ctk.CTkLabel(self.content, text=f"{name.title()} (not implemented)", text_color=PALETTE["text"],
                     font=("Segoe UI Semibold", 18)).pack(pady=20)
        ctk.CTkButton(self.content, text="Export Policy JSON", corner_radius=14,
                      fg_color=PALETTE["card2"], hover_color="#2a3346").pack(pady=10)
        ctk.CTkButton(self.content, text="Save Changes", corner_radius=14,
                      fg_color=PALETTE["accent"], hover_color="#3e74d6").pack(pady=10)

class HomePage(ctk.CTkFrame):
    def __init__(self, master, services=None):
        super().__init__(master, fg_color=PALETTE["bg"]); self.services = services
        self._grid = ctk.CTkFrame(self, fg_color=PALETTE["bg"])
        self._grid.pack(fill="both", expand=True, padx=14, pady=14)
        self._tiles: list[HomeTile] = []
        cols = 4
        for c in range(cols): self._grid.grid_columnconfigure(c, weight=1, uniform="tiles")
        r=c=0
        def nav_to(route: str):
            parent = self.master
            while parent is not None and not isinstance(parent, AppShell):
                parent = getattr(parent, "master", None)
            if isinstance(parent, AppShell):
                parent._navigate(route)
        # Build tiles dynamically from file-backed routes recorded by Router
        parent = self.master
        while parent is not None and not isinstance(parent, AppShell):
            parent = getattr(parent, "master", None)
        file_routes = {}
        if isinstance(parent, AppShell):
            try:
                file_routes = getattr(parent.router, "route_files", {}) or {}
            except Exception:
                file_routes = {}
        # file_routes: Dict[route_name, filename]
        # Show only buttons for routes that are backed by real files, labeled by filename
        for route, filename in sorted(file_routes.items(), key=lambda kv: (kv[1] or "").lower()):
            label = f"{filename} – {route}" if filename else route
            tile = HomeTile(self._grid, label=label, route=route, on_click=nav_to)
            self._tiles.append(tile)
        # Initial layout
        self._relayout_tiles()
        # Relayout on resize to keep it responsive
        self.bind("<Configure>", lambda e: self._relayout_tiles())

    def _relayout_tiles(self):
        width = max(1, self.winfo_width())
        # heuristic: each tile wants ~260px including gaps
        cols = max(1, min(6, width // 260))
        for i in range(8):
            try:
                self._grid.grid_columnconfigure(i, weight=0)
            except Exception:
                pass
        for c in range(cols):
            self._grid.grid_columnconfigure(c, weight=1, uniform="tiles")
        # clear existing positions
        r = c = 0
        for tile in self._tiles:
            tile.grid(row=r, column=c, sticky="nsew", padx=8, pady=8)
            c += 1
            if c >= cols:
                c = 0
                r += 1

# -------------------- Router --------------------
class Router:
    def __init__(self, container: ctk.CTkFrame, services=None, *, on_route_changed=None):
        self.container = container; self.services = services
        # Map route name -> page class
        self.routes: Dict[str, Type[ctk.CTkFrame]] = {}
        # Map route name -> filename (e.g., "members.py") for routes backed by a concrete file
        self.route_files: Dict[str, str] = {}
        # Cache created page instances to speed up navigation
        self._cache: Dict[str, ctk.CTkFrame] = {}
        # Optional callback invoked when route changes
        self._on_route_changed = on_route_changed
        self.routes = self._build_routes()
        self.current: Optional[ctk.CTkFrame] = None

    def _build_routes(self) -> Dict[str, Type[ctk.CTkFrame]]:
        pages: Dict[str, Type[ctk.CTkFrame]] = {"Home": HomePage, "Settings": SettingsHubPage}
        # Expose Settings on Home as a built-in (no external file)
        try:
            self.route_files["Settings"] = "(built-in)"
        except Exception:
            pass
        
        def try_many(route: str, candidates: list[tuple[str, str]]):
            for mod, cls in candidates:
                try:
                    module = __import__(f"pages.{mod}", fromlist=[cls])
                    pages[route] = getattr(module, cls)
                    # record the backing filename for Home tiles
                    try:
                        self.route_files[route] = f"{mod}.py"
                    except Exception:
                        pass
                    return
                except Exception:
                    continue
            pages[route] = _MissingPageFactory(route)

        # Dashboard
        try_many("Dashboard", [("dashboard", "DashboardPage"), ("dashboard", "Dashboard")])
        
        try_many("Members", [("members","MembersPage"), ("member_list","membersPage")])
        try_many("Member Profile", [("member_profile","MemberProfilePage")])
        try_many("Subscriptions", [("subscriptions","SubscriptionsPage"), ("Subscriptions","SubscriptionsPage")])
        try_many("Attendance", [("attendance","AttendancePage"), ("attendance_scan","attendancePage")])
        try_many("POS", [("pos","POSPage"), ("pos_new_sale","POSPage")])
        try_many("Inventory", [("inventory","inventoryPage")])
        try_many("Accounting", [("accounting","AccountingPage")])
        try_many("Reports", [("reports","ReportsPage")])
        return pages

    def goto(self, route: str):
        # hide current
        try:
            for child in list(self.container.winfo_children()):
                try: child.pack_forget()
                except Exception: pass
                try: child.grid_forget()
                except Exception: pass
                try: child.place_forget()
                except Exception: pass
        except Exception:
            pass
        # get or create target page
        page = self._cache.get(route)
        if page is None:
            page_cls = self.routes.get(route) or _MissingPageFactory(route)
            page = page_cls(self.container, services=self.services)
            self._cache[route] = page
        self.current = page
        self.current.pack(fill="both", expand=True)
        # Let the UI settle for smoother perception
        try:
            self.current.update_idletasks()
        except Exception:
            pass
        # notify
        try:
            if callable(self._on_route_changed):
                self._on_route_changed(route)
        except Exception:
            pass
        return self.current

# -------------------- App Shell (header only on Home) --------------------
class AppShell(ctk.CTkFrame):
    def __init__(self, master, services=None, *, start_route: str = "Home"):
        super().__init__(master, fg_color=PALETTE["bg"])
        self.services = services or SimpleServices()
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)

        # Navigation state
        self.current_route: Optional[str] = None
        self.history: list[str] = []

        self.header = HeaderBar(
            self,
            on_open_gate=self._open_gate,
            on_language_change=self._set_language,
            get_role=lambda: getattr(self.services, "session_role", "Admin"),
            get_user=lambda: getattr(self.services, "user_name", "user"),
            on_switch_role=self._switch_role,
        )
        # Header is only gridded when on Home

        self.content = ctk.CTkFrame(self, fg_color=PALETTE["surface"])
        self.content.grid(row=1, column=0, sticky="nsew")

        self.router = Router(self.content, services=self.services, on_route_changed=self._on_route_changed)
        self._navigate(start_route)

        top = self.winfo_toplevel()
        top.bind("<Control-h>", lambda e: self._navigate("Home"), add="+")
        top.bind("<Escape>", lambda e: self._go_back(), add="+")
        # widget scaling shortcuts for quick responsiveness tuning
        top.bind("<Control-plus>", lambda e: self._bump_scale(0.05), add="+")
        top.bind("<Control-minus>", lambda e: self._bump_scale(-0.05), add="+")
        top.bind("<Control-0>", lambda e: self._reset_scale(), add="+")

    def _show_header(self, show: bool):
        if show:
            if self.header not in self.grid_slaves():
                self.header.grid(row=0, column=0, sticky="ew")
        else:
            try: self.header.grid_forget()
            except Exception: pass

    def _navigate(self, route: str):
        # push current route to history if changing routes
        if self.current_route is not None and self.current_route != route:
            self.history.append(self.current_route)
        self._show_header(route == "Home")
        self.router.goto(route)
        if route == "Home":
            self.header.set_page_title("Home")
            self.header.refresh_role()
        self.current_route = route

    def _go_back(self):
        try:
            if self.history:
                prev = self.history.pop()
                self._navigate(prev)
        except Exception:
            pass

    def _on_route_changed(self, route: str):
        # Update header visibility even if navigation bypassed _navigate
        try:
            self._show_header(route == "Home")
            if route == "Home":
                self.header.set_page_title("Home")
                self.header.refresh_role()
        except Exception:
            pass

    def _switch_role(self, new_role: str):
        self.services.session_role = new_role; self.header.refresh_role()

    def _open_gate(self):
        try: getattr(getattr(self.services, "gate", None), "open", lambda: None)()
        except Exception: pass

    def _set_language(self, code: str):
        try: getattr(getattr(self.services, "settings", None), "set_language", lambda *_: None)(code.lower())
        except Exception: pass

# Minimal stub for safety if you instantiate AppShell alone
class SimpleServices:
    def __init__(self):
        self.session_role = "Admin"
        self.user_name = "user"
