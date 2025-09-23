
# /pages/settings_debt_policy.py
# GymPro — Settings: Debt Policy (CustomTkinter)
# Dark UI, matches mockup layout. Smooth & fast, service-ready.
from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

import customtkinter as ctk
from tkinter import filedialog, messagebox

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

# -------- atoms --------
class SectionCard(ctk.CTkFrame):
    def __init__(self, master, title: str):
        super().__init__(master, fg_color=PALETTE["card"], corner_radius=16)
        self.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(self, text=title, text_color=PALETTE["text"],
                     font=("Segoe UI Semibold", 15)).grid(row=0, column=0, sticky="w", padx=16, pady=(14, 8))

class Pill(ctk.CTkFrame):
    def __init__(self, master, text: str, *, bg: str, fg: str):
        super().__init__(master, fg_color=bg, corner_radius=100)
        ctk.CTkLabel(self, text=text, text_color=fg, font=("Segoe UI", 12)).grid(row=0, column=0, padx=10, pady=4)

# -------- title strip --------
class TitleStrip(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color=PALETTE["card"], corner_radius=16)
        self.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(self, text="Settings — Debt Policy", text_color=PALETTE["text"],
                     font=("Segoe UI Semibold", 16)).grid(row=0, column=0, sticky="w", padx=16, pady=16)
        self.status_area = ctk.CTkFrame(self, fg_color="transparent")
        self.status_area.grid(row=0, column=1, sticky="e", padx=12, pady=12)
        # create placeholder pills
        self.pill_enabled = Pill(self.status_area, "Enabled", bg="#20321f", fg=PALETTE["ok"])
        self.pill_enabled.grid(row=0, column=0, padx=6)
        self.pill_grace = Pill(self.status_area, "Grace Active", bg="#33240f", fg=PALETTE["warn"])
        self.pill_grace.grid(row=0, column=1, padx=6)

    def set_status(self, *, enabled: bool, grace_active: bool):
        self.pill_enabled.destroy()
        self.pill_grace.destroy()
        self.pill_enabled = Pill(self.status_area, "Enabled" if enabled else "Disabled",
                                 bg="#20321f" if enabled else "#3a1418",
                                 fg=PALETTE["ok"] if enabled else PALETTE["danger"])
        self.pill_enabled.grid(row=0, column=0, padx=6)
        self.pill_grace = Pill(self.status_area, "Grace Active" if grace_active else "Grace Off",
                               bg="#33240f" if grace_active else "#2b3344",
                               fg=PALETTE["warn"] if grace_active else PALETTE["muted"])
        self.pill_grace.grid(row=0, column=1, padx=6)

# -------- page --------
class SettingsDebtPolicyPage(ctk.CTkFrame):
    """
    Optional services (duck-typed):
      - settings.debt.get() -> policy: dict
      - settings.debt.save(policy: dict) -> None
      - settings.debt.export_json(policy: dict, path: str) -> None
    """
    def __init__(self, master, services: Optional[object] = None):
        super().__init__(master, fg_color=PALETTE["surface"])
        self.services = services
        self.policy: Dict[str, Any] = {}

        # overall layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Title
        self.title = TitleStrip(self)
        self.title.grid(row=0, column=0, columnspan=2, sticky="ew", padx=16, pady=(16,8))

        # Left column
        left = ctk.CTkFrame(self, fg_color="transparent")
        left.grid(row=1, column=0, sticky="nsew", padx=(16,8), pady=(8,16))
        left.grid_rowconfigure(1, weight=1)

        # Core Policy
        core = SectionCard(left, "Core Policy")
        core.grid(row=0, column=0, sticky="ew", pady=(0,8))
        core.grid_columnconfigure(1, weight=1)

        self.switch_enabled = ctk.CTkSwitch(core, text="Policy Enabled")
        self.switch_enabled.grid(row=1, column=0, columnspan=2, sticky="w", padx=14, pady=(6,6))

        self.switch_partial = ctk.CTkSwitch(core, text="Allow Partial Payments")
        self.switch_partial.grid(row=2, column=0, columnspan=2, sticky="w", padx=14, pady=6)

        ctk.CTkLabel(core, text="Max Debt per Member (DA)", text_color=PALETTE["muted"]).grid(row=3, column=0, sticky="w", padx=16, pady=(6,4))
        self.ent_max_debt = ctk.CTkEntry(core, placeholder_text="e.g., 5000")
        self.ent_max_debt.grid(row=3, column=1, sticky="ew", padx=(0,16), pady=(6,4))

        ctk.CTkLabel(core, text="Subscription Grace (days)", text_color=PALETTE["muted"]).grid(row=4, column=0, sticky="w", padx=16, pady=4)
        self.ent_grace_sub = ctk.CTkEntry(core, placeholder_text="e.g., 7")
        self.ent_grace_sub.grid(row=4, column=1, sticky="ew", padx=(0,16), pady=4)

        ctk.CTkLabel(core, text="POS Grace (days)", text_color=PALETTE["muted"]).grid(row=5, column=0, sticky="w", padx=16, pady=4)
        self.ent_grace_pos = ctk.CTkEntry(core, placeholder_text="e.g., 3")
        self.ent_grace_pos.grid(row=5, column=1, sticky="ew", padx=(0,16), pady=4)

        ctk.CTkLabel(core, text="Write-off After (days)", text_color=PALETTE["muted"]).grid(row=6, column=0, sticky="w", padx=16, pady=4)
        self.ent_writeoff_days = ctk.CTkEntry(core, placeholder_text="e.g., 60")
        self.ent_writeoff_days.grid(row=6, column=1, sticky="ew", padx=(0,16), pady=4)

        self.switch_writeoff_auto = ctk.CTkSwitch(core, text="Auto Write-off")
        self.switch_writeoff_auto.grid(row=7, column=0, columnspan=2, sticky="w", padx=14, pady=(6,12))

        # Enforcement at Check-in
        enforce = SectionCard(left, "Enforcement at Check-in")
        enforce.grid(row=1, column=0, sticky="nsew", pady=8)
        enforce.grid_rowconfigure(1, weight=1)

        # headers
        header = ctk.CTkFrame(enforce, fg_color="transparent")
        header.grid(row=1, column=0, sticky="ew", padx=12)
        labels = ["Membership Status", "Debt Age", "Remaining", "Gate Action", "Toast"]
        for i, t in enumerate(labels):
            ctk.CTkLabel(header, text=t, text_color=PALETTE["muted"]).grid(row=0, column=i, padx=(8,8), pady=(0,6), sticky="w")

        # rules container
        self.rules_frame = ctk.CTkScrollableFrame(enforce, fg_color="transparent", height=220)
        self.rules_frame.grid(row=2, column=0, sticky="nsew", padx=12, pady=(0,10))
        self._rule_rows: List[Dict[str, Any]] = []

        # add/remove row buttons
        actions = ctk.CTkFrame(enforce, fg_color="transparent")
        actions.grid(row=3, column=0, sticky="e", padx=12, pady=(0,10))
        ctk.CTkButton(actions, text="Add Rule", height=30, corner_radius=16, fg_color="#263042",
                      hover_color="#32405a", command=self._add_rule).grid(row=0, column=0, padx=6)
        ctk.CTkButton(actions, text="Reset Defaults", height=30, corner_radius=16, fg_color="#263042",
                      hover_color="#32405a", command=self._reset_rules).grid(row=0, column=1, padx=6)

        # Right column
        right = ctk.CTkFrame(self, fg_color="transparent")
        right.grid(row=1, column=1, sticky="nsew", padx=(8,16), pady=(8,16))
        right.grid_rowconfigure(2, weight=1)

        # Notifications & Messaging
        notif = SectionCard(right, "Notifications & Messaging")
        notif.grid(row=0, column=0, sticky="ew", pady=(0,8))
        notif.grid_columnconfigure(0, weight=1)
        self.switch_banner = ctk.CTkSwitch(notif, text="Show cashier debt banner on POS & Member pages")
        self.switch_banner.grid(row=1, column=0, sticky="w", padx=16, pady=(6,8))

        ctk.CTkLabel(notif, text="SMS Template for Overdue", text_color=PALETTE["muted"]).grid(row=2, column=0, sticky="w", padx=16)
        self.txt_sms = ctk.CTkTextbox(notif, height=80)
        self.txt_sms.grid(row=3, column=0, sticky="ew", padx=16, pady=(4,12))
        self.txt_sms.insert("1.0", "Hello {first_name}, your gym debt is {remaining_amount} DA. Please visit the desk.")

        # Aging Buckets (legend)
        legend = SectionCard(right, "Aging Buckets")
        legend.grid(row=1, column=0, sticky="ew", pady=8)
        row = ctk.CTkFrame(legend, fg_color="transparent")
        row.grid(row=1, column=0, sticky="w", padx=12, pady=(4,10))
        pills = [
            ("Current (0d)", "#20321f", PALETTE["ok"]),
            ("1–7d", "#33240f", PALETTE["warn"]),
            ("8–30d", "#3a1418", PALETTE["danger"]),
            ("31–60d", "#3a1418", PALETTE["danger"]),
            (">60d", "#3a1418", PALETTE["danger"]),
        ]
        for i, (label, bg, fg) in enumerate(pills):
            p = Pill(row, label, bg=bg, fg=fg); p.grid(row=0, column=i, padx=6)

        # Actions
        actions2 = SectionCard(right, "Actions")
        actions2.grid(row=2, column=0, sticky="nsew", pady=(8,0))
        area = ctk.CTkFrame(actions2, fg_color="transparent")
        area.grid(row=1, column=0, sticky="ew", padx=12, pady=(0,10))
        self.btn_save = ctk.CTkButton(area, text="Save Changes", height=36, corner_radius=20,
                                      fg_color=PALETTE["accent"], hover_color="#3e74d6", command=self._save)
        self.btn_reset_all = ctk.CTkButton(area, text="Reset to Defaults", height=36, corner_radius=20,
                                           fg_color="#263042", hover_color="#32405a", command=self._reset_all)
        self.btn_export = ctk.CTkButton(area, text="Export Policy JSON", height=32, corner_radius=18,
                                        fg_color="#263042", hover_color="#32405a", command=self._export_json)
        self.btn_save.grid(row=0, column=0, sticky="ew", pady=6)
        self.btn_reset_all.grid(row=1, column=0, sticky="ew", pady=6)
        self.btn_export.grid(row=0, column=1, rowspan=2, padx=(12,0))

        # Load data
        self._load_policy()
        self._apply_policy_to_ui()

        # reactive status pills
        self.switch_enabled.configure(command=lambda: self._update_title_pills())
        self.ent_grace_sub.bind("<KeyRelease>", lambda e: self._update_title_pills())
        self.ent_grace_pos.bind("<KeyRelease>", lambda e: self._update_title_pills())

    # -------- rules ui --------
    def _clear_rules(self):
        for child in list(self.rules_frame.winfo_children()):
            child.destroy()
        self._rule_rows.clear()

    def _add_rule(self, rule: Optional[Dict[str, str]] = None):
        row = ctk.CTkFrame(self.rules_frame, fg_color=PALETTE["card2"], corner_radius=10)
        row.grid(sticky="ew", padx=6, pady=6)
        # drop-downs
        st = ctk.CTkOptionMenu(row, values=["Active","Suspended","Blacklisted"], width=150)
        de = ctk.CTkOptionMenu(row, values=["≤ Grace","> Grace","Any"], width=120)
        re = ctk.CTkOptionMenu(row, values=["≤ Max","Any"], width=120)
        ga = ctk.CTkOptionMenu(row, values=["Allow","Deny"], width=120)
        to = ctk.CTkOptionMenu(row, values=["Warn","Explain","Contact Desk","Contact Admin"], width=150)

        st.grid(row=0, column=0, padx=8, pady=8, sticky="w")
        de.grid(row=0, column=1, padx=8, pady=8, sticky="w")
        re.grid(row=0, column=2, padx=8, pady=8, sticky="w")
        ga.grid(row=0, column=3, padx=8, pady=8, sticky="w")
        to.grid(row=0, column=4, padx=8, pady=8, sticky="w")

        if rule:
            st.set(rule.get("status","Active"))
            de.set(rule.get("debt_age","≤ Grace"))
            re.set(rule.get("remaining","≤ Max"))
            ga.set(rule.get("gate_action","Allow"))
            to.set(rule.get("toast","Warn"))

        # remove button
        rm = ctk.CTkButton(row, text="×", width=28, height=28, corner_radius=14, fg_color="#2b3344",
                           hover_color="#3a435a", command=lambda r=row: self._remove_rule(r))
        rm.grid(row=0, column=5, padx=6)

        self._rule_rows.append({"frame": row, "status": st, "debt_age": de, "remaining": re, "gate_action": ga, "toast": to})

    def _remove_rule(self, row_widget):
        for item in self._rule_rows:
            if item["frame"] is row_widget:
                item["frame"].destroy()
                self._rule_rows.remove(item)
                break

    def _reset_rules(self):
        defaults = [
            {"status":"Active","debt_age":"≤ Grace","remaining":"≤ Max","gate_action":"Allow","toast":"Warn"},
            {"status":"Active",">":"", "debt_age":"> Grace","remaining":"Any","gate_action":"Deny","toast":"Explain"},
            {"status":"Suspended","debt_age":"Any","remaining":"Any","gate_action":"Deny","toast":"Contact Desk"},
            {"status":"Blacklisted","debt_age":"Any","remaining":"Any","gate_action":"Deny","toast":"Contact Admin"},
        ]
        self._clear_rules()
        for r in defaults:
            self._add_rule(r)

    # -------- policy load/apply --------
    def _default_policy(self) -> Dict[str, Any]:
        return {
            "enabled": True,
            "allow_partial": True,
            "max_debt": 5000,
            "grace_subscription_days": 7,
            "grace_pos_days": 3,
            "writeoff_days": 60,
            "writeoff_auto": True,
            "enforcement_rules": [
                {"status":"Active","debt_age":"≤ Grace","remaining":"≤ Max","gate_action":"Allow","toast":"Warn"},
                {"status":"Active","debt_age":"> Grace","remaining":"Any","gate_action":"Deny","toast":"Explain"},
                {"status":"Suspended","debt_age":"Any","remaining":"Any","gate_action":"Deny","toast":"Contact Desk"},
                {"status":"Blacklisted","debt_age":"Any","remaining":"Any","gate_action":"Deny","toast":"Contact Admin"},
            ],
            "cashier_banner": True,
            "sms_overdue_template": "Hello {first_name}, your gym debt is {remaining_amount} DA. Please visit the desk."
        }

    def _load_policy(self):
        pol = None
        if self.services and hasattr(self.services, "settings") and hasattr(self.services.settings, "debt"):
            try:
                pol = self.services.settings.debt.get()
            except Exception:
                pol = None
        if not pol:
            pol = self._default_policy()
        self.policy = pol

    def _apply_policy_to_ui(self):
        p = self.policy
        self.switch_enabled.select() if p.get("enabled", True) else self.switch_enabled.deselect()
        self.switch_partial.select() if p.get("allow_partial", True) else self.switch_partial.deselect()
        self.ent_max_debt.delete(0, "end"); self.ent_max_debt.insert(0, str(p.get("max_debt", 0)))
        self.ent_grace_sub.delete(0, "end"); self.ent_grace_sub.insert(0, str(p.get("grace_subscription_days", 0)))
        self.ent_grace_pos.delete(0, "end"); self.ent_grace_pos.insert(0, str(p.get("grace_pos_days", 0)))
        self.ent_writeoff_days.delete(0, "end"); self.ent_writeoff_days.insert(0, str(p.get("writeoff_days", 0)))
        self.switch_writeoff_auto.select() if p.get("writeoff_auto", False) else self.switch_writeoff_auto.deselect()
        self.switch_banner.select() if p.get("cashier_banner", True) else self.switch_banner.deselect()
        self.txt_sms.delete("1.0", "end"); self.txt_sms.insert("1.0", p.get("sms_overdue_template",""))

        self._clear_rules()
        for r in p.get("enforcement_rules", []):
            self._add_rule(r)

        self._update_title_pills()

    def _collect_policy_from_ui(self) -> Dict[str, Any]:
        def _int(entry, default=0):
            try:
                return int(entry.get().strip())
            except Exception:
                return default
        def _float(entry, default=0.0):
            try:
                return float(entry.get().strip())
            except Exception:
                return default

        rules = []
        for it in self._rule_rows:
            rules.append({
                "status": it["status"].get(),
                "debt_age": it["debt_age"].get(),
                "remaining": it["remaining"].get(),
                "gate_action": it["gate_action"].get(),
                "toast": it["toast"].get(),
            })

        return {
            "enabled": bool(self.switch_enabled.get() == 1),
            "allow_partial": bool(self.switch_partial.get() == 1),
            "max_debt": _int(self.ent_max_debt, 0),
            "grace_subscription_days": _int(self.ent_grace_sub, 0),
            "grace_pos_days": _int(self.ent_grace_pos, 0),
            "writeoff_days": _int(self.ent_writeoff_days, 0),
            "writeoff_auto": bool(self.switch_writeoff_auto.get() == 1),
            "enforcement_rules": rules,
            "cashier_banner": bool(self.switch_banner.get() == 1),
            "sms_overdue_template": self.txt_sms.get("1.0", "end").strip(),
        }

    def _update_title_pills(self):
        enabled = bool(self.switch_enabled.get() == 1)
        try:
            gsub = int(self.ent_grace_sub.get() or "0")
            gpos = int(self.ent_grace_pos.get() or "0")
            grace_active = (gsub > 0) or (gpos > 0)
        except Exception:
            grace_active = False
        self.title.set_status(enabled=enabled, grace_active=grace_active)

    # -------- actions --------
    def _save(self):
        self.policy = self._collect_policy_from_ui()
        if self.services and hasattr(self.services, "settings") and hasattr(self.services.settings, "debt"):
            try:
                self.services.settings.debt.save(self.policy)
            except Exception:
                pass
        messagebox.showinfo("Debt Policy", "Policy saved successfully.")

    def _reset_all(self):
        self.policy = self._default_policy()
        self._apply_policy_to_ui()
        messagebox.showinfo("Debt Policy", "Policy reset to defaults.")

    def _export_json(self):
        pol = self._collect_policy_from_ui()
        path = filedialog.asksaveasfilename(title="Export Policy JSON", defaultextension=".json",
                                            filetypes=[("JSON","*.json")])
        if not path:
            return
        try:
            if self.services and hasattr(self.services, "settings") and hasattr(self.services.settings, "debt"):
                try:
                    self.services.settings.debt.export_json(pol, path)
                except Exception:
                    raise
            else:
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(pol, f, ensure_ascii=False, indent=2)
            messagebox.showinfo("Export", f"Policy exported to:\n{path}")
        except Exception as e:
            messagebox.showerror("Export Failed", str(e))

# Local preview
if __name__ == "__main__":
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    root = ctk.CTk()
    root.geometry("1400x900")
    root.configure(fg_color=PALETTE["bg"])
    page = SettingsDebtPolicyPage(root)
    page.pack(fill="both", expand=True)
    root.mainloop()
