# pages/pos.py
# GymPro — POS (Product Search & Payments), fixed-height layout (no scroll / no slide)
from __future__ import annotations

import random
from typing import Any, Dict, List, Optional, Tuple

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
                     font=("Segoe UI Semibold", 15)).grid(row=0, column=0, sticky="w", padx=16, pady=(12,8))

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

class Chip(ctk.CTkFrame):
    """Tiny chip used for method totals."""
    def __init__(self, master, label: str, value: str, fg="#263042", color=PALETTE["muted"]):
        super().__init__(master, fg_color=fg, corner_radius=999)
        ctk.CTkLabel(self, text=label, text_color=color, font=("Segoe UI Semibold", 11)).grid(row=0, column=0, padx=(10,6), pady=4)
        ctk.CTkLabel(self, text=value, text_color=PALETTE["text"], font=("Segoe UI", 11)).grid(row=0, column=1, padx=(0,10), pady=4)

class Toast(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        self._lbl = ctk.CTkLabel(self, text="", text_color=PALETTE["text"])
        self._lbl.grid(row=0, column=0, padx=12, pady=6)
        self._after = None
    def show(self, text: str, kind: str = "ok", ms: int = 1500):
        colors = {"ok": PALETTE["ok"], "warn": PALETTE["warn"], "danger": PALETTE["danger"]}
        self._lbl.configure(text=text, text_color=colors.get(kind, PALETTE["ok"]))
        if self._after:
            try: self.after_cancel(self._after)
            except Exception: pass
        self._after = self.after(ms, lambda: self._lbl.configure(text=""))

# ---------- product widgets ----------
class ProductTile(ctk.CTkFrame):
    def __init__(self, master, p: Dict[str, Any], on_add):
        super().__init__(master, fg_color=PALETTE["card2"], corner_radius=14)
        self.p = p; self.on_add = on_add
        self.grid_columnconfigure(0, weight=1)

        name = p.get("name","—")
        price = float(p.get("price",0) or 0)
        stock = int(p.get("stock_qty",0) or 0)
        low   = int(p.get("low_stock_threshold",0) or 0)
        is_low = stock <= low

        ctk.CTkLabel(self, text=name, text_color=PALETTE["text"], font=("Segoe UI Semibold", 13))\
            .grid(row=0, column=0, sticky="w", padx=12, pady=(8,0))
        row2 = ctk.CTkFrame(self, fg_color="transparent"); row2.grid(row=1, column=0, sticky="w", padx=12, pady=(2,6))
        ctk.CTkLabel(row2, text=f"{price:.0f} DA", text_color=PALETTE["muted"]).grid(row=0, column=0, padx=(0,10))
        Pill(row2, f"Stock {stock}", "warn" if is_low else "ok").grid(row=0, column=1)

        ctk.CTkButton(self, text="Add", height=26, corner_radius=10,
                      fg_color="#2a3550", hover_color="#334066",
                      command=lambda: self.on_add(self.p)).grid(row=2, column=0, sticky="e", padx=12, pady=(0,8))

class CartRow(ctk.CTkFrame):
    def __init__(self, master, line: Dict[str, Any], on_add, on_sub, on_del):
        super().__init__(master, fg_color=PALETTE["card2"], corner_radius=10)
        self.line=line; self.on_add=on_add; self.on_sub=on_sub; self.on_del=on_del
        self.grid_columnconfigure(0, weight=34)
        self.grid_columnconfigure(1, weight=10)
        self.grid_columnconfigure(2, weight=12)
        self.grid_columnconfigure(3, weight=12)
        self.grid_columnconfigure(4, weight=12)

        name=line.get("name","—"); qty=int(line.get("qty",1)); price=float(line.get("price",0)); total=qty*price
        small=("Segoe UI", 12)

        ctk.CTkLabel(self, text=name, text_color=PALETTE["text"], font=small).grid(row=0, column=0, padx=(10,6), pady=6, sticky="w")
        ctk.CTkLabel(self, text=str(qty), text_color=PALETTE["text"], font=small).grid(row=0, column=1, padx=6, pady=6, sticky="w")
        ctk.CTkLabel(self, text=f"{price:.0f}", text_color=PALETTE["muted"], font=small).grid(row=0, column=2, padx=6, pady=6, sticky="w")
        ctk.CTkLabel(self, text=f"{total:.0f}", text_color=PALETTE["text"], font=small).grid(row=0, column=3, padx=6, pady=6, sticky="w")

        actions = ctk.CTkFrame(self, fg_color="transparent")
        actions.grid(row=0, column=4, sticky="e", padx=(6,10))
        ctk.CTkButton(actions, text="-", width=28, height=24, corner_radius=8,
                      fg_color="#2b3344", hover_color="#38445a",
                      command=lambda: self.on_sub(self.line)).grid(row=0, column=0, padx=3)
        ctk.CTkButton(actions, text="+", width=28, height=24, corner_radius=8,
                      fg_color="#2b3344", hover_color="#38445a",
                      command=lambda: self.on_add(self.line)).grid(row=0, column=1, padx=3)
        ctk.CTkButton(actions, text="x", width=28, height=24, corner_radius=8,
                      fg_color="#3a1418", hover_color="#5a1e24",
                      command=lambda: self.on_del(self.line)).grid(row=0, column=2, padx=3)

# ---------- page ----------
class POSPage(ctk.CTkFrame):
    """
    Optional services hooks (used if present):
      - find_products(q, category)
      - pos_create_order(member_id)
      - pos_add_line(order_id, product_id, quantity, unit_price)
      - pos_pay(order_id, amount, method)
      - pos_finalize(order_id) -> {status:'paid'|'partial'|'open'}
    """
    def __init__(self, master, services: Optional[object] = None, member_id: Optional[int] = None):
        super().__init__(master, fg_color=PALETTE["surface"])
        self.services=services; self.member_id=member_id
        self._after=None
        self.order_id: Optional[Any] = None
        self.cart: List[Dict[str, Any]] = []
        self.payments: List[Tuple[str, float]] = []

        # Root grid: 2 columns, 1 row (everything is inside)
        self.grid_columnconfigure(0, weight=3, uniform="col")
        self.grid_columnconfigure(1, weight=2, uniform="col")
        self.grid_rowconfigure(0, weight=1)

        # LEFT — search (top) + products (fill)
        left = ctk.CTkFrame(self, fg_color="transparent")
        left.grid(row=0, column=0, sticky="nsew", padx=(12,6), pady=12)
        left.grid_rowconfigure(1, weight=1)
        left.grid_columnconfigure(0, weight=1)

        search = ctk.CTkFrame(left, fg_color=PALETTE["card"], corner_radius=16)
        search.grid(row=0, column=0, sticky="ew")
        for i in range(10): search.grid_columnconfigure(i, weight=1)
        ctk.CTkLabel(search, text="Search", text_color=PALETTE["muted"]).grid(row=0, column=0, padx=(12,8), pady=8, sticky="w")
        self.ent_q = ctk.CTkEntry(search, placeholder_text="Name or SKU… (Enter)")
        self.ent_q.grid(row=0, column=1, columnspan=6, sticky="ew", padx=(0,8), pady=8)
        self.ent_q.bind("<KeyRelease>", lambda _e: self._debounce(self._refresh_products))
        self.ent_q.bind("<Return>",    lambda _e: self._refresh_products())
        try:
            self.opt_cat = ctk.CTkOptionMenu(search, values=["All","Snacks","Supplements","Drinks","Merch"],
                                             command=lambda _v: self._refresh_products()); self.opt_cat.set("All")
        except Exception:
            self.opt_cat = ctk.CTkEntry(search); self.opt_cat.insert(0, "All")
        self.opt_cat.grid(row=0, column=8, sticky="e", padx=(8,8), pady=8)
        ctk.CTkButton(search, text="Refresh", height=26, corner_radius=12,
                      fg_color="#2a3550", hover_color="#334066",
                      command=self._refresh_products).grid(row=0, column=9, padx=(0,12), pady=8, sticky="e")

        prod_card = SectionCard(left, "Products")
        prod_card.grid(row=1, column=0, sticky="nsew", pady=(8,0))
        prod_card.grid_rowconfigure(1, weight=1)

        self.products_grid = ctk.CTkFrame(prod_card, fg_color=PALETTE["card2"], corner_radius=12)
        self.products_grid.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0,10))
        self.products_grid.bind("<Configure>", self._on_products_resize)

        # RIGHT — fixed layout (no scroll)
        right = ctk.CTkFrame(self, fg_color="transparent")
        right.grid(row=0, column=1, sticky="nsew", padx=(6,12), pady=12)
        right.grid_columnconfigure(0, weight=1)
        self._right = right
        right.bind("<Configure>", self._resize_right_parts)

        # Cart
        cart_card = SectionCard(right, "Cart")
        cart_card.grid(row=0, column=0, sticky="ew", padx=0, pady=(0,6))
        hdr = ctk.CTkFrame(cart_card, fg_color=PALETTE["card2"], corner_radius=12)
        hdr.grid(row=1, column=0, sticky="ew", padx=10, pady=(0,6))
        for i, txt in enumerate(("Item", "Qty", "Price", "Total", "")):
            ctk.CTkLabel(hdr, text=txt, text_color=PALETTE["muted"]).grid(row=0, column=i, padx=(12 if i==0 else 8, 8), pady=6, sticky="w")
            hdr.grid_columnconfigure(i, weight=[34,10,12,12,12][i])

        self.cart_list = ctk.CTkFrame(right, fg_color=PALETTE["card2"], corner_radius=12)
        self.cart_list.grid(row=1, column=0, sticky="nsew", padx=0, pady=(0,6))

        # Totals
        totals = ctk.CTkFrame(right, fg_color=PALETTE["card"], corner_radius=16)
        totals.grid(row=2, column=0, sticky="ew", padx=0, pady=(0,6))
        totals.grid_columnconfigure(0, weight=1)
        self.lbl_total = ctk.CTkLabel(totals, text="Total: 0 DA", text_color=PALETTE["text"], font=("Segoe UI Semibold", 14))
        self.lbl_total.grid(row=0, column=0, padx=12, pady=8, sticky="w")
        self.lbl_paid  = ctk.CTkLabel(totals, text="Paid: 0", text_color=PALETTE["muted"])
        self.lbl_paid.grid(row=0, column=1, padx=12, pady=8, sticky="w")
        self.lbl_due   = ctk.CTkLabel(totals, text="Due: 0", text_color=PALETTE["warn"])
        self.lbl_due.grid(row=0, column=2, padx=12, pady=8, sticky="w")

        # Payments (downsized + includes history)
        pay_card = SectionCard(right, "Payments")
        pay_card.grid(row=3, column=0, sticky="ew", padx=0, pady=(0,6))

        # Entry row
        pay_bar = ctk.CTkFrame(pay_card, fg_color=PALETTE["card2"], corner_radius=12)
        pay_bar.grid(row=1, column=0, sticky="ew", padx=10, pady=(0,6))
        pay_bar.grid_columnconfigure(3, weight=1)
        ctk.CTkLabel(pay_bar, text="Amount", text_color=PALETTE["muted"]).grid(row=0, column=0, padx=(12,8), pady=6, sticky="w")
        self.ent_amount = ctk.CTkEntry(pay_bar, width=110); self.ent_amount.insert(0, "0")
        self.ent_amount.grid(row=0, column=1, padx=(0,8), pady=6, sticky="w")
        ctk.CTkButton(pay_bar, text="Cash", height=24, corner_radius=10, fg_color="#2b3344", hover_color="#38445a",
                      command=lambda: self._add_payment("cash")).grid(row=0, column=2, padx=4, pady=6, sticky="w")
        ctk.CTkButton(pay_bar, text="Card", height=24, corner_radius=10, fg_color="#2b3344", hover_color="#38445a",
                      command=lambda: self._add_payment("card")).grid(row=0, column=3, padx=4, pady=6, sticky="w")
        ctk.CTkButton(pay_bar, text="Transfer", height=24, corner_radius=10, fg_color="#2b3344", hover_color="#38445a",
                      command=lambda: self._add_payment("transfer")).grid(row=0, column=4, padx=4, pady=6, sticky="w")

        # Method totals chips + short history list (fits in compact area)
        self.pay_meta = ctk.CTkFrame(pay_card, fg_color="transparent")
        self.pay_meta.grid(row=2, column=0, sticky="ew", padx=10, pady=(0,8))
        self.pay_meta.grid_columnconfigure(0, weight=1)

        self.payments_list = ctk.CTkFrame(pay_card, fg_color=PALETTE["card2"], corner_radius=12)
        self.payments_list.grid(row=3, column=0, sticky="ew", padx=10, pady=(0,10))

        # Buttons
        btns = ctk.CTkFrame(right, fg_color="transparent")
        btns.grid(row=4, column=0, sticky="ew", padx=0, pady=(0,0))
        ctk.CTkButton(btns, text="Finalize Sale", height=34, corner_radius=12,
                      fg_color=PALETTE["ok"], hover_color="#1a9b4c",
                      command=self._finalize).grid(row=0, column=0, padx=(0,8))
        ctk.CTkButton(btns, text="Clear", height=34, corner_radius=12,
                      fg_color="#2b3344", hover_color="#38445a",
                      command=self._clear_all).grid(row=0, column=1, padx=(8,0))

        # Toast
        self.toast = Toast(self)
        self.toast.place(relx=1.0, rely=1.0, anchor="se")

        # init
        self._ensure_order()
        self._refresh_products()
        self._refresh_totals()

    # ---------- layout sizing ----------
    def _resize_right_parts(self, _e=None):
        """Compute fixed heights so everything fits. Payments downsized."""
        h = max(0, self._right.winfo_height())
        # reserve small paddings + headers (~110 px total)
        avail = max(0, h - 110)
        cart_h     = int(avail * 0.50)   # a bit taller cart
        payments_h = int(avail * 0.22)   # downsized payments area
        cart_h     = max(120, cart_h)
        payments_h = max(100, payments_h)
        try:
            self.cart_list.configure(height=cart_h)
            # payments area is split: chips + history list; history gets most of the compact height
            self.payments_list.configure(height=max(60, payments_h - 36))
        except Exception:
            pass
        self._render_cart()
        self._render_payments()

    # ---------- utils ----------
    def _debounce(self, fn, ms: int = 220):
        try:
            if self._after: self.after_cancel(self._after)
        except Exception:
            pass
        self._after = self.after(ms, fn)

    def _ensure_order(self):
        if self.order_id is not None: return
        if self.services and hasattr(self.services, "pos_create_order"):
            try:
                order = self.services.pos_create_order(self.member_id)
                self.order_id = (order or {}).get("id")
            except Exception:
                self.order_id = None
        else:
            self.order_id = None

    def _get_category(self) -> Optional[str]:
        if hasattr(self.opt_cat, "get"):
            v = self.opt_cat.get()
            return None if v == "All" else v
        t = self.opt_cat.get().strip()
        return None if t.lower() in ("", "all") else t

    # ---------- products ----------
    def _fetch_products(self, q: str, cat: Optional[str]) -> List[Dict[str, Any]]:
        if self.services and hasattr(self.services, "find_products"):
            try:
                data = self.services.find_products(q, cat) or []
                out=[]
                for p in data:
                    out.append({
                        "id": p.get("id"),
                        "name": p.get("name",""),
                        "price": float(p.get("price",0) or 0),
                        "stock_qty": int(p.get("stock_qty",0) or 0),
                        "low_stock_threshold": int(p.get("low_stock_threshold",0) or 0),
                        "category": p.get("category",""),
                    })
                return out
            except Exception:
                pass

        rng = random.Random(hash(q + (cat or "")) & 0xffffffff)
        base = [
            ("Water 500ml","Drinks",80), ("Protein Bar","Snacks",250), ("Creatine 300g","Supplements",1800),
            ("Gym Towel","Merch",600), ("Shaker 600ml","Merch",950), ("Energy Drink","Drinks",220),
            ("Whey 1kg","Supplements",3500), ("BCAA 400g","Supplements",2200),
        ]
        out=[]
        for i,(n,c,price) in enumerate(base):
            if cat and c!=cat: continue
            if q and q.lower() not in n.lower(): continue
            out.append({
                "id": 100+i, "name": n, "price": price,
                "stock_qty": rng.randint(0,30),
                "low_stock_threshold": rng.choice([3,5,8,10]),
                "category": c
            })
        return out

    def _refresh_products(self):
        q = (self.ent_q.get() or "").strip()
        cat = self._get_category()
        self._products_cache = self._fetch_products(q, cat)
        self._render_products(self._auto_cols())

    def _render_products(self, cols: int):
        for w in self.products_grid.winfo_children():
            try: w.destroy()
            except Exception: pass
        items = getattr(self, "_products_cache", [])
        if not items:
            ctk.CTkLabel(self.products_grid, text="No products found", text_color=PALETTE["muted"])\
                .pack(padx=10, pady=8, anchor="w"); return
        for idx, p in enumerate(items):
            tile = ProductTile(self.products_grid, p, on_add=self._add_to_cart_from_product)
            r, c = divmod(idx, cols)
            tile.grid(row=r, column=c, padx=8, pady=8, sticky="nsew")
        for c in range(cols):
            self.products_grid.grid_columnconfigure(c, weight=1)

    def _auto_cols(self) -> int:
        w = max(0, self.products_grid.winfo_width())
        if w <= 700: return 2
        if w <= 1000: return 3
        return 4

    def _on_products_resize(self, _e):
        new_cols = self._auto_cols()
        if getattr(self, "_last_cols", None) != new_cols:
            self._last_cols = new_cols
            self._render_products(new_cols)

    # ---------- cart ops ----------
    def _add_to_cart_from_product(self, p: Dict[str, Any]):
        for line in self.cart:
            if line["id"] == p["id"]:
                line["qty"] += 1; break
        else:
            self.cart.append({"id": p["id"], "name": p["name"], "price": float(p["price"]), "qty": 1})
        if self.order_id and self.services and hasattr(self.services, "pos_add_line"):
            try: self.services.pos_add_line(self.order_id, p["id"], 1, float(p["price"]))
            except Exception: pass
        self.toast.show(f"Added {p['name']}")
        self._render_cart(); self._refresh_totals()

    def _cart_add(self, line: Dict[str, Any]):
        line["qty"] += 1
        if self.order_id and self.services and hasattr(self.services, "pos_add_line"):
            try: self.services.pos_add_line(self.order_id, line["id"], 1, float(line["price"]))
            except Exception: pass
        self._render_cart(); self._refresh_totals()

    def _cart_sub(self, line: Dict[str, Any]):
        line["qty"] -= 1
        if line["qty"] <= 0:
            self.cart = [l for l in self.cart if l is not line]
        self._render_cart(); self._refresh_totals()

    def _cart_del(self, line: Dict[str, Any]):
        self.cart = [l for l in self.cart if l is not line]
        self._render_cart(); self._refresh_totals()

    def _render_cart(self):
        for w in self.cart_list.winfo_children():
            try: w.destroy()
            except Exception: pass
        if not self.cart:
            ctk.CTkLabel(self.cart_list, text="Cart is empty", text_color=PALETTE["muted"])\
                .pack(padx=10, pady=8, anchor="w"); return

        # Compact rows to fit into cart_list height; if overflow, show “… +N more”
        h = max(1, self.cart_list.winfo_height())
        est_row = 36
        max_rows = max(1, (h - 8) // est_row)
        rows = self.cart[:max_rows]
        overflow = max(0, len(self.cart) - len(rows))

        for line in rows:
            CartRow(self.cart_list, line, on_add=self._cart_add, on_sub=self._cart_sub, on_del=self._cart_del)\
                .pack(fill="x", padx=8, pady=4)

        if overflow > 0:
            ctk.CTkLabel(self.cart_list, text=f"… +{overflow} more items",
                         text_color=PALETTE["muted"]).pack(padx=12, pady=4, anchor="w")

    def _totals(self) -> Tuple[float, float, float]:
        total = sum(float(l["price"]) * int(l["qty"]) for l in self.cart)
        paid = sum(a for _, a in self.payments)
        due = max(0.0, total - paid)
        return total, paid, due

    def _refresh_totals(self):
        t, p, d = self._totals()
        self.lbl_total.configure(text=f"Total: {t:.0f} DA")
        self.lbl_paid.configure(text=f"Paid: {p:.0f}")
        self.lbl_due.configure(text=f"Due: {d:.0f}")
        try:
            self.ent_amount.delete(0, "end"); self.ent_amount.insert(0, str(int(d)))
        except Exception:
            pass

    # ---------- payments ----------
    def _add_payment(self, method: str):
        try: amt = float(self.ent_amount.get() or 0)
        except Exception: amt = 0.0
        if amt <= 0:
            self.toast.show("Enter a valid amount", "warn"); return

        if self.order_id and self.services and hasattr(self.services, "pos_pay"):
            try: self.services.pos_pay(self.order_id, amt, method)
            except Exception: pass

        self.payments.append((method, amt))
        self._render_payments()
        self._refresh_totals()
        self._render_cart()  # instant cart refresh after payment

        # auto-finalize when fully paid
        _t, _p, d = self._totals()
        if d <= 0.01:
            self._finalize()
        else:
            self.toast.show(f"{method.capitalize()} +{int(amt)}")

    def _render_payments(self):
        # method totals chips
        for w in self.pay_meta.winfo_children():
            try: w.destroy()
            except Exception: pass

        totals = {"cash": 0.0, "card": 0.0, "transfer": 0.0}
        for m, a in self.payments:
            key = m.lower()
            if key in totals:
                totals[key] += float(a)

        chips = ctk.CTkFrame(self.pay_meta, fg_color="transparent")
        chips.pack(fill="x")
        Chip(chips, "Cash",     f"{int(totals['cash'])}",     fg="#213026", color=PALETTE["ok"]).pack(side="left", padx=4)
        Chip(chips, "Card",     f"{int(totals['card'])}",     fg="#262a38", color=PALETTE["muted"]).pack(side="left", padx=4)
        Chip(chips, "Transfer", f"{int(totals['transfer'])}", fg="#2a2630", color=PALETTE["muted"]).pack(side="left", padx=4)

        # compact history list (last 5)
        for w in self.payments_list.winfo_children():
            try: w.destroy()
            except Exception: pass

        h = max(1, self.payments_list.winfo_height())
        rows = self.payments[-5:]  # last 5 payments
        if not rows:
            ctk.CTkLabel(self.payments_list, text="No payments yet", text_color=PALETTE["muted"])\
                .pack(padx=10, pady=6, anchor="w"); return

        for i, (m, a) in enumerate(rows, 1):
            row = ctk.CTkFrame(self.payments_list, fg_color=PALETTE["card"], corner_radius=10)
            row.pack(fill="x", padx=8, pady=4)
            row.grid_columnconfigure(0, weight=1)
            ctk.CTkLabel(row, text=f"{m.capitalize()}", text_color=PALETTE["text"]).grid(row=0, column=0, padx=10, pady=6, sticky="w")
            ctk.CTkLabel(row, text=f"{int(a)}", text_color=PALETTE["muted"]).grid(row=0, column=1, padx=8, pady=6, sticky="e")

    # ---------- finalize ----------
    def _finalize(self):
        if not self.cart:
            self.toast.show("Cart is empty", "warn"); return

        if self.order_id and self.services and hasattr(self.services, "pos_finalize"):
            try:
                result = self.services.pos_finalize(self.order_id) or {}
                status = result.get("status","open")
                if status == "paid":
                    self.toast.show("Sale completed", "ok")
                elif status == "partial":
                    self.toast.show("Partial payment — debt recorded", "warn")
                else:
                    self.toast.show("Order left open", "warn")
                self._clear_all(); return
            except Exception:
                pass

        # local behavior
        _t, _p, d = self._totals()
        if d <= 0.01:
            self.toast.show("Sale completed", "ok")
        else:
            self.toast.show(f"Partial — debt {int(d)} recorded", "warn")
        self._clear_all()

    def _clear_all(self):
        self.cart.clear()
        self.payments.clear()
        self._render_cart()
        self._render_payments()
        self._refresh_totals()
        self.order_id = None
        self._ensure_order()

# Preview
if __name__ == "__main__":
    ctk.set_appearance_mode("dark"); ctk.set_default_color_theme("blue")
    root = ctk.CTk(); root.geometry("1400x860"); root.configure(fg_color=PALETTE["bg"])
    page = POSPage(root, services=None); page.pack(fill="both", expand=True)
    root.mainloop()
