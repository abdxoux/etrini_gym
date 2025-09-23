# pages/inventory.py
# GymPro — Inventory (Products & Stock Moves)
# CustomTkinter, dark identity. Fast lists, debounced search, safe service fallbacks.
from __future__ import annotations

import datetime as dt
import random
from typing import Any, Dict, List, Optional

import customtkinter as ctk

# Try to reuse global palette if available
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
            "ok":    ("#1e3325", PALETTE["ok"]),
            "warn":  ("#33240f", PALETTE["warn"]),
            "danger":("#3a1418", PALETTE["danger"]),
            "muted": ("#2b3344", PALETTE["muted"]),
        }
        bg, fg = colors.get(kind, colors["muted"])
        super().__init__(master, fg_color=bg, corner_radius=999)
        ctk.CTkLabel(self, text=text, text_color=fg, font=("Segoe UI", 12)).grid(row=0, column=0, padx=10, pady=4)

# ---------- product dialog ----------
class ProductDialog(ctk.CTkToplevel):
    """Small modal to add / edit a product. Calls on_submit(dict) on Save."""
    def __init__(self, master, title: str, initial: Optional[Dict[str, Any]], on_submit):
        super().__init__(master)
        self.title(title)
        self.configure(fg_color=PALETTE["surface"])
        self._on_submit = on_submit

        self.grid_columnconfigure(1, weight=1)

        # Fields
        ctk.CTkLabel(self, text="Name", text_color=PALETTE["muted"]).grid(row=0, column=0, padx=12, pady=(12,6), sticky="w")
        self.ent_name = ctk.CTkEntry(self, width=320, placeholder_text="e.g., Protein Bar")
        self.ent_name.grid(row=0, column=1, padx=12, pady=(12,6), sticky="ew")

        ctk.CTkLabel(self, text="Category", text_color=PALETTE["muted"]).grid(row=1, column=0, padx=12, pady=6, sticky="w")
        try:
            self.opt_cat = ctk.CTkOptionMenu(self, values=["Snacks","Supplements","Drinks","Merch"])
            self.opt_cat.set("Snacks")
        except Exception:
            self.opt_cat = ctk.CTkEntry(self)
            self.opt_cat.insert(0, "Snacks")
        self.opt_cat.grid(row=1, column=1, padx=12, pady=6, sticky="w")

        ctk.CTkLabel(self, text="Price (DA)", text_color=PALETTE["muted"]).grid(row=2, column=0, padx=12, pady=6, sticky="w")
        self.ent_price = ctk.CTkEntry(self, width=120); self.ent_price.grid(row=2, column=1, padx=12, pady=6, sticky="w")

        ctk.CTkLabel(self, text="Stock Qty", text_color=PALETTE["muted"]).grid(row=3, column=0, padx=12, pady=6, sticky="w")
        self.ent_stock = ctk.CTkEntry(self, width=120); self.ent_stock.grid(row=3, column=1, padx=12, pady=6, sticky="w")

        ctk.CTkLabel(self, text="Low Stock Threshold", text_color=PALETTE["muted"]).grid(row=4, column=0, padx=12, pady=6, sticky="w")
        self.ent_low = ctk.CTkEntry(self, width=120); self.ent_low.grid(row=4, column=1, padx=12, pady=6, sticky="w")

        self.sw_active = ctk.CTkSwitch(self, text="Active", onvalue=1, offvalue=0)
        self.sw_active.grid(row=5, column=1, padx=12, pady=6, sticky="w")

        # Buttons
        btns = ctk.CTkFrame(self, fg_color="transparent"); btns.grid(row=6, column=0, columnspan=2, sticky="e", padx=12, pady=(8,12))
        ctk.CTkButton(btns, text="Cancel", corner_radius=12, fg_color="#2b3344",
                      hover_color="#38445a", command=self.destroy).grid(row=0, column=0, padx=6)
        ctk.CTkButton(btns, text="Save", corner_radius=12, fg_color="#2a3550",
                      hover_color="#334066", command=self._save).grid(row=0, column=1, padx=6)

        # Fill initial
        if initial:
            self.ent_name.insert(0, initial.get("name",""))
            if hasattr(self.opt_cat, "set"):
                self.opt_cat.set(initial.get("category","Snacks"))
            else:
                self.opt_cat.delete(0, "end"); self.opt_cat.insert(0, initial.get("category","Snacks"))
            self.ent_price.insert(0, str(initial.get("price", 0)))
            self.ent_stock.insert(0, str(initial.get("stock_qty", 0)))
            self.ent_low.insert(0, str(initial.get("low_stock_threshold", 0)))
            self.sw_active.select() if initial.get("is_active", True) else self.sw_active.deselect()

        # make modal-ish
        self.grab_set()
        self.after(50, lambda: self.ent_name.focus_set())

    def _save(self):
        def _get_cat():
            try:
                return self.opt_cat.get()
            except Exception:
                return self.opt_cat.get().strip() or "Snacks"

        try:
            data = {
                "name": (self.ent_name.get() or "").strip(),
                "category": _get_cat(),
                "price": float(self.ent_price.get() or 0),
                "stock_qty": int(float(self.ent_stock.get() or 0)),
                "low_stock_threshold": int(float(self.ent_low.get() or 0)),
                "is_active": bool(self.sw_active.get()),
            }
        except Exception:
            # minimal guard
            data = {
                "name": (self.ent_name.get() or "").strip(),
                "category": _get_cat(), "price": 0.0, "stock_qty": 0,
                "low_stock_threshold": 0, "is_active": bool(self.sw_active.get()),
            }
        if not data["name"]:
            try:
                from tkinter import messagebox
                messagebox.showwarning("Validation", "Name is required.")
            except Exception:
                pass
            return
        try:
            self._on_submit(data)
        finally:
            self.destroy()

# ---------- product & move rows ----------
class ProductRow(ctk.CTkFrame):
    def __init__(self, master, p: Dict[str, Any], on_edit=None):
        super().__init__(master, fg_color=PALETTE["card"], corner_radius=10)
        self.p = p
        self.on_edit = on_edit

        self.grid_columnconfigure(0, weight=30)  # name
        self.grid_columnconfigure(1, weight=12)  # price
        self.grid_columnconfigure(2, weight=10)  # stock
        self.grid_columnconfigure(3, weight=14)  # status
        self.grid_columnconfigure(4, weight=8)   # action

        name = p.get("name", "—")
        price = float(p.get("price", 0) or 0)
        stock = int(p.get("stock_qty", 0) or 0)
        low = int(p.get("low_stock_threshold", 0) or 0)
        is_active = bool(p.get("is_active", True))

        ctk.CTkLabel(self, text=name, text_color=PALETTE["text"]).grid(row=0, column=0, padx=(12,8), pady=8, sticky="w")
        ctk.CTkLabel(self, text=f"{price:.0f} DA", text_color=PALETTE["muted"]).grid(row=0, column=1, padx=8, pady=8, sticky="w")
        ctk.CTkLabel(self, text=str(stock), text_color=PALETTE["text"]).grid(row=0, column=2, padx=8, pady=8, sticky="w")

        pill_kind = "ok" if stock > max(low, 0) else ("warn" if stock == low else "danger")
        pill_text = "Active" if is_active else "Inactive"
        line = ctk.CTkFrame(self, fg_color="transparent"); line.grid(row=0, column=3, padx=8, pady=8, sticky="w")
        Pill(line, f"Stock ≤ {low}" if pill_kind != "ok" else "Stock OK", pill_kind).grid(row=0, column=0, padx=(0,8))
        Pill(line, pill_text, "muted" if is_active else "danger").grid(row=0, column=1)

        ctk.CTkButton(self, text="Edit", height=28, corner_radius=12,
                      fg_color="#2b3344", hover_color="#38445a",
                      command=lambda: on_edit(self.p) if on_edit else None).grid(row=0, column=4, padx=(8,12), pady=8, sticky="e")

class MoveRow(ctk.CTkFrame):
    def __init__(self, master, m: Dict[str, Any]):
        super().__init__(master, fg_color=PALETTE["card"], corner_radius=10)
        self.grid_columnconfigure(0, weight=16)  # date
        self.grid_columnconfigure(1, weight=28)  # product
        self.grid_columnconfigure(2, weight=14)  # qty
        self.grid_columnconfigure(3, weight=32)  # note

        ctk.CTkLabel(self, text=m.get("date","—"), text_color=PALETTE["text"]).grid(row=0, column=0, padx=(12,8), pady=8, sticky="w")
        ctk.CTkLabel(self, text=m.get("product","—"), text_color=PALETTE["text"]).grid(row=0, column=1, padx=8, pady=8, sticky="w")
        qty = int(m.get("qty", 0) or 0)
        ctk.CTkLabel(self, text=str(qty), text_color=PALETTE["ok"] if qty>=0 else PALETTE["danger"]).grid(row=0, column=2, padx=8, pady=8, sticky="w")
        ctk.CTkLabel(self, text=m.get("note",""), text_color=PALETTE["muted"]).grid(row=0, column=3, padx=8, pady=8, sticky="w")

# ---------- page ----------
class InventoryPage(ctk.CTkFrame):
    """
    Inventory with:
      - Products tab: search, low-stock highlighting, add/edit buttons (wired)
      - Stock Moves tab: recent adjustments (sales, restock, corrections)

    Optional services (used if present):
      services.find_products(q, category) -> list[dict]
      services.low_stock_alerts() -> list[dict]
      services.stock_moves(limit=100) -> list[dict]
      services.create_product(data) / services.edit_product(product_id, data)
    """
    def __init__(self, master, services: Optional[object] = None):
        super().__init__(master, fg_color=PALETTE["surface"])
        self.services = services
        self._after_handle = None
        self._tab = "Products"
        self._local_products: List[Dict[str, Any]] = []   # in-memory fallback list

        # root grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)

        # title
        title = SectionCard(self, "Inventory — Products & Stock Moves")
        title.grid(row=0, column=0, sticky="ew", padx=12, pady=(12,8))

        # top bar: segmented tabs + actions
        bar = ctk.CTkFrame(self, fg_color=PALETTE["card"], corner_radius=16)
        bar.grid(row=1, column=0, sticky="ew", padx=12, pady=8)
        bar.grid_columnconfigure(0, weight=0)
        bar.grid_columnconfigure(1, weight=1)
        bar.grid_columnconfigure(2, weight=0)

        try:
            self.tabs = ctk.CTkSegmentedButton(bar, values=["Products","Stock Moves"], command=self._on_tab)
            self.tabs.set("Products")
            self.tabs.grid(row=0, column=0, padx=12, pady=10)
        except Exception:
            self.tabs = None
            ctk.CTkButton(bar, text="Products", height=26, corner_radius=14, fg_color="#2b3344",
                          command=lambda: self._on_tab("Products")).grid(row=0, column=0, padx=(12,4), pady=10)
            ctk.CTkButton(bar, text="Stock Moves", height=26, corner_radius=14, fg_color="#2b3344",
                          command=lambda: self._on_tab("Stock Moves")).grid(row=0, column=1, padx=(0,4), pady=10, sticky="w")

        # right side actions
        actions = ctk.CTkFrame(bar, fg_color="transparent")
        actions.grid(row=0, column=2, sticky="e", padx=8, pady=8)
        self.btn_add = ctk.CTkButton(actions, text="Add Product", height=30, corner_radius=14,
                                     fg_color="#2a3550", hover_color="#334066",
                                     command=self._add_product)
        self.btn_add.grid(row=0, column=0, padx=6)
        self.btn_export = ctk.CTkButton(actions, text="Export CSV", height=30, corner_radius=14,
                                        fg_color="#263042", hover_color="#32405a",
                                        command=self._export_products_csv)
        self.btn_export.grid(row=0, column=1, padx=6)

        # filters area (changes per tab)
        self.filter_panel = ctk.CTkFrame(self, fg_color=PALETTE["card"], corner_radius=16)
        self.filter_panel.grid(row=2, column=0, sticky="ew", padx=12, pady=(0,8))
        self.filter_panel.grid_columnconfigure(6, weight=1)
        self._build_filters_products()

        # content area
        self.content = ctk.CTkFrame(self, fg_color="transparent")
        self.content.grid(row=3, column=0, sticky="nsew", padx=12, pady=(0,12))
        self.content.grid_columnconfigure(0, weight=1)
        self.content.grid_rowconfigure(1, weight=1)

        # header + list containers
        self.header_card = SectionCard(self.content, "Results")
        self.header_card.grid(row=0, column=0, sticky="new", padx=0, pady=(0,8))

        self.listbox = ctk.CTkScrollableFrame(self.content, fg_color=PALETTE["card2"], corner_radius=12)
        self.listbox.grid(row=1, column=0, sticky="nsew", padx=0, pady=(0,0))

        # initial render
        self._render_products_header()
        self._refresh_products()

    # ---------- filter builders ----------
    def _clear_filters(self):
        for w in self.filter_panel.winfo_children():
            try: w.destroy()
            except Exception: pass

    def _build_filters_products(self):
        self._clear_filters()
        ctk.CTkLabel(self.filter_panel, text="Search", text_color=PALETTE["muted"]).grid(row=0, column=0, padx=(12,8), pady=10, sticky="w")
        self.ent_q = ctk.CTkEntry(self.filter_panel, placeholder_text="Name or SKU…")
        self.ent_q.grid(row=0, column=1, sticky="ew", padx=(0,8), pady=10)
        self.ent_q.bind("<KeyRelease>", lambda _e: self._debounced(self._refresh_products))

        ctk.CTkLabel(self.filter_panel, text="Category", text_color=PALETTE["muted"]).grid(row=0, column=2, padx=(12,8), pady=10, sticky="w")
        try:
            self.opt_cat = ctk.CTkOptionMenu(self.filter_panel, values=["All","Snacks","Supplements","Drinks","Merch"],
                                             command=lambda _v: self._refresh_products())
            self.opt_cat.set("All")
        except Exception:
            self.opt_cat = ctk.CTkEntry(self.filter_panel); self.opt_cat.insert(0, "All")
        self.opt_cat.grid(row=0, column=3, padx=(0,8), pady=10, sticky="w")

        ctk.CTkButton(self.filter_panel, text="Refresh", height=28, corner_radius=14,
                      fg_color="#2a3550", hover_color="#334066",
                      command=self._refresh_products).grid(row=0, column=5, padx=(8,12), pady=10, sticky="e")

    def _build_filters_moves(self):
        self._clear_filters()
        ctk.CTkLabel(self.filter_panel, text="Limit", text_color=PALETTE["muted"]).grid(row=0, column=0, padx=(12,8), pady=10, sticky="w")
        self.ent_limit = ctk.CTkEntry(self.filter_panel, width=100)
        self.ent_limit.insert(0, "100")
        self.ent_limit.grid(row=0, column=1, padx=(0,8), pady=10, sticky="w")
        self.ent_limit.bind("<KeyRelease>", lambda _e: self._debounced(self._refresh_moves))

        ctk.CTkButton(self.filter_panel, text="Refresh", height=28, corner_radius=14,
                      fg_color="#2a3550", hover_color="#334066",
                      command=self._refresh_moves).grid(row=0, column=5, padx=(8,12), pady=10, sticky="e")

    # ---------- tab & debounce ----------
    def _on_tab(self, value: Optional[str] = None):
        name = value or (self.tabs.get() if self.tabs else self._tab)
        if name == "Products":
            self._build_filters_products()
            self._tab = "Products"
            self._render_products_header()
            self._refresh_products()
        else:
            self._build_filters_moves()
            self._tab = "Stock Moves"
            self._render_moves_header()
            self._refresh_moves()

    def _debounced(self, fn, ms: int = 250):
        try:
            if self._after_handle: self.after_cancel(self._after_handle)
        except Exception:
            pass
        self._after_handle = self.after(ms, fn)

    # ---------- headers ----------
    def _render_products_header(self):
        for w in self.header_card.winfo_children():
            if isinstance(w, ctk.CTkFrame): w.destroy()
        hdr = ctk.CTkFrame(self.header_card, fg_color=PALETTE["card2"], corner_radius=12)
        hdr.grid(row=1, column=0, sticky="ew", padx=10, pady=(0,8))
        labels = ("Product", "Price", "Stock", "Status", "")
        weights = (30,12,10,14,8)
        for i, (txt, w) in enumerate(zip(labels, weights)):
            ctk.CTkLabel(hdr, text=txt, text_color=PALETTE["muted"]).grid(
                row=0, column=i, padx=(12 if i==0 else 8, 8), pady=8, sticky="w"
            )
            hdr.grid_columnconfigure(i, weight=w)

    def _render_moves_header(self):
        for w in self.header_card.winfo_children():
            if isinstance(w, ctk.CTkFrame): w.destroy()
        hdr = ctk.CTkFrame(self.header_card, fg_color=PALETTE["card2"], corner_radius=12)
        hdr.grid(row=1, column=0, sticky="ew", padx=10, pady=(0,8))
        labels = ("Date", "Product", "Qty", "Note")
        weights = (16,28,14,32)
        for i, (txt, w) in enumerate(zip(labels, weights)):
            ctk.CTkLabel(hdr, text=txt, text_color=PALETTE["muted"]).grid(
                row=0, column=i, padx=(12 if i==0 else 8, 8), pady=8, sticky="w"
            )
            hdr.grid_columnconfigure(i, weight=w)

    # ---------- product actions (wired) ----------
    def _add_product(self):
        def submit(data: Dict[str, Any]):
            # Service path
            if self.services and hasattr(self.services, "create_product"):
                try:
                    self.services.create_product(data)
                    self._refresh_products(); return
                except Exception:
                    pass
            # Local fallback: create ID and append
            data = dict(data)
            data["id"] = (max([p.get("id", 0) for p in self._local_products], default=100) + 1)
            self._local_products.append(data)
            self._refresh_products()
        ProductDialog(self.winfo_toplevel(), "Add Product", None, submit)

    def _edit_product(self, p: Dict[str, Any]):
        def submit(data: Dict[str, Any]):
            pid = p.get("id")
            # Service path
            if self.services and hasattr(self.services, "edit_product"):
                try:
                    self.services.edit_product(pid, data)
                    self._refresh_products(); return
                except Exception:
                    pass
            # Local fallback
            for i, item in enumerate(self._local_products):
                if item.get("id") == pid:
                    upd = dict(item); upd.update(data); self._local_products[i] = upd
                    break
            else:
                # If not found in local cache, insert as new with same id
                data = dict(data); data["id"] = pid
                self._local_products.append(data)
            self._refresh_products()
        ProductDialog(self.winfo_toplevel(), "Edit Product", p, submit)

    def _export_products_csv(self):
        # quick export of currently listed products
        try:
            from tkinter import filedialog, messagebox
        except Exception:
            filedialog = messagebox = None
        default = f"products_{dt.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        path = filedialog.asksaveasfilename(title="Export Products CSV", defaultextension=".csv",
                                            initialfile=default, filetypes=[("CSV","*.csv")]) if filedialog else default
        if not path: return
        try:
            import csv
            with open(path, "w", newline="", encoding="utf-8") as f:
                w = csv.writer(f)
                w.writerow(["name","price","stock_qty","low_stock_threshold","is_active","category"])
                for p in getattr(self, "_last_products", []):
                    w.writerow([p.get("name",""), p.get("price",""), p.get("stock_qty",""),
                                p.get("low_stock_threshold",""), p.get("is_active",""), p.get("category","")])
            if messagebox: messagebox.showinfo("Export", f"Exported to:\n{path}")
        except Exception as e:
            if messagebox: messagebox.showerror("Export", f"Failed: {e}")

    # ---------- product data ----------
    def _fetch_products(self, q: str, category: Optional[str]) -> List[Dict[str, Any]]:
        # Service path
        if self.services and hasattr(self.services, "find_products"):
            try:
                data = self.services.find_products(q, category) or []
                out = []
                for p in data:
                    out.append({
                        "id": p.get("id"),
                        "name": p.get("name",""),
                        "price": float(p.get("price",0) or 0),
                        "stock_qty": int(p.get("stock_qty",0) or 0),
                        "low_stock_threshold": int(p.get("low_stock_threshold",0) or 0),
                        "is_active": bool(p.get("is_active", True)),
                        "category": p.get("category",""),
                    })
                return out
            except Exception:
                pass

        # Local cache preferred if available (user may have added/edited)
        if self._local_products:
            items = self._local_products.copy()
        else:
            # Mock initial dataset
            rng = random.Random(1337)
            names = [
                ("Water 500ml","Drinks"), ("Protein Bar","Snacks"), ("Creatine 300g","Supplements"),
                ("Gym Towel","Merch"), ("Shaker 600ml","Merch"), ("Energy Drink","Drinks"),
                ("Whey 1kg","Supplements"), ("BCAA 400g","Supplements"),
            ]
            items = []
            base_id = 100
            for i, (n, cat) in enumerate(names):
                items.append({
                    "id": base_id+i, "name": n, "category": cat,
                    "price": rng.choice([80,120,250,600,950,1800,2200,3500]),
                    "stock_qty": rng.randint(0, 30),
                    "low_stock_threshold": rng.choice([3,5,8,10]),
                    "is_active": rng.random() > 0.05,
                })
            self._local_products = items.copy()

        # Filter
        if category:
            items = [p for p in items if p.get("category") == category]
        ql = (q or "").lower().strip()
        if ql:
            items = [p for p in items if ql in p.get("name","").lower()]

        return items

    def _refresh_products(self):
        # header status strip (low stock)
        self._render_products_header()
        for w in self.listbox.winfo_children():
            try: w.destroy()
            except Exception: pass

        q = (self.ent_q.get() or "").strip() if hasattr(self, "ent_q") else ""
        if hasattr(self, "opt_cat"):
            try:
                v = self.opt_cat.get()
                cat = None if v == "All" else v
            except Exception:
                t = self.opt_cat.get().strip()
                cat = None if t.lower() in ("", "all") else t
        else:
            cat = None

        # low stock alerts via service (optional)
        alerts = []
        if self.services and hasattr(self.services, "low_stock_alerts"):
            try:
                data = self.services.low_stock_alerts() or []
                alerts = [f"{a.get('name','?')} ({int(a.get('stock_qty',0))}/{int(a.get('low_stock_threshold',0))})" for a in data][:3]
            except Exception:
                alerts = []
        if alerts:
            bar = ctk.CTkFrame(self.header_card, fg_color="transparent")
            bar.grid(row=2, column=0, sticky="w", padx=12, pady=(0,6))
            ctk.CTkLabel(bar, text="Low Stock:", text_color=PALETTE["warn"]).grid(row=0, column=0, padx=(0,8))
            ctk.CTkLabel(bar, text=" · ".join(alerts), text_color=PALETTE["muted"]).grid(row=0, column=1)

        products = self._fetch_products(q, cat)
        self._last_products = products
        if not products:
            ctk.CTkLabel(self.listbox, text="No products found", text_color=PALETTE["muted"]).pack(padx=10, pady=8, anchor="w")
            return

        for p in products:
            row = ProductRow(self.listbox, p, on_edit=self._edit_product)
            row.pack(fill="x", padx=10, pady=6)

    # ---------- moves data ----------
    def _fetch_moves(self, limit: int) -> List[Dict[str, Any]]:
        if self.services and hasattr(self.services, "stock_moves"):
            try:
                data = self.services.stock_moves(limit=limit) or []
                out = []
                for m in data:
                    out.append({
                        "date": m.get("date",""),
                        "product": m.get("product",""),
                        "qty": int(m.get("qty",0) or 0),
                        "note": m.get("note",""),
                    })
                return out[:max(1, limit)]
            except Exception:
                pass
        rng = random.Random(limit * 37 + 7)
        names = ["Water 500ml","Protein Bar","Creatine 300g","Shaker 600ml","Towel","Energy Drink"]
        out = []
        now = dt.datetime.now()
        for i in range(max(1, min(200, limit))):
            ts = (now - dt.timedelta(hours=i)).strftime("%Y-%m-%d %H:%M")
            qty = rng.choice([+12,+6,+3,-1,-2,-3,-5,-8])
            note = "restock" if qty>0 else "sale"
            out.append({"date": ts, "product": rng.choice(names), "qty": qty, "note": note})
        return out

    def _render_moves(self, moves: List[Dict[str, Any]]):
        for w in self.listbox.winfo_children():
            try: w.destroy()
            except Exception: pass
        if not moves:
            ctk.CTkLabel(self.listbox, text="No stock moves", text_color=PALETTE["muted"]).pack(padx=10, pady=8, anchor="w")
            return
        for m in moves:
            row = MoveRow(self.listbox, m)
            row.pack(fill="x", padx=10, pady=6)

    def _refresh_moves(self):
        self._render_moves_header()
        try:
            limit = int(self.ent_limit.get().strip()) if hasattr(self, "ent_limit") else 100
        except Exception:
            limit = 100
        self._render_moves(self._fetch_moves(limit))

# Local preview
if __name__ == "__main__":
    ctk.set_appearance_mode("dark"); ctk.set_default_color_theme("blue")
    root = ctk.CTk(); root.geometry("1200x720"); root.configure(fg_color=PALETTE["bg"])
    page = InventoryPage(root, services=None); page.pack(fill="both", expand=True)
    root.mainloop()
