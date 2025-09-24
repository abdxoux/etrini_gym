# main.py
import os
import customtkinter as ctk
from router import AppShell, PALETTE
from pages.login import LoginDialog  # your styled dialog

APP_TITLE    = "GymPro"
DEFAULT_SIZE = "1400x900"
DB_PATH      = "gym_management.db"

# ---------------- helpers ----------------
def ensure_sqlite_file(path: str):
    if not os.path.exists(path):
        open(path, "a", encoding="utf-8").close()

def try_load_auth_service(db_path: str):
    try:
        from pages_logic.auth_service import AuthService  # type: ignore
        return AuthService(db_path=db_path)
    except Exception:
        return None

# ---------------- stub services (UI demo-safe) ----------------
class StubServices:
    """
    Minimal shim so pages don't crash while logic isn't wired yet.
    Provides demo data + safe no-op fallbacks matching the signatures your pages use.
    """
    def __init__(self):
        # session fields (set by main() after login)
        self.session_role = "Admin"
        self.user_name = "user"


        # demo stores
        self._products = [
            {"product_id": 1, "name": "Water Bottle 500ml", "price": 2.50, "stock_qty": 3,  "low_stock_threshold": 5, "category": "Drinks"},
            {"product_id": 2, "name": "Protein Bar",        "price": 1.80, "stock_qty": 12, "low_stock_threshold": 6, "category": "Snacks"},
            {"product_id": 3, "name": "T-Shirt",            "price": 9.90, "stock_qty": 2,  "low_stock_threshold": 3, "category": "Merch"},
        ]
        self._orders = {}
        self._next_order_id = 1001

        self._members = [
            {"member_id": 100, "first_name": "Nadia", "last_name": "K.", "phone": "0550 000 000", "status": "active"},
            {"member_id": 101, "first_name": "Karim", "last_name": "B.", "phone": "0550 111 222", "status": "active"},
            {"member_id": 102, "first_name": "Hind",  "last_name": "M.", "phone": "0550 333 444", "status": "expired"},
        ]
        self._subs = [
            {"subscription_id": 5001, "member_id": 100, "plan": "Monthly", "status": "active"},
            {"subscription_id": 5002, "member_id": 101, "plan": "Monthly", "status": "active"},
        ]
        self._checkins = [
            {"member_id": 100, "date": "2025-09-20", "time": "09:03"},
            {"member_id": 101, "date": "2025-09-20", "time": "18:12"},
        ]

        # optional real auth service (injected by main)
        self.auth = None

    # ---- POS ----
    def create_order(self, member_id=None):
        oid = self._next_order_id; self._next_order_id += 1
        order = {"order_id": oid, "member_id": member_id, "lines": [], "total_amount": 0.0, "status": "open"}
        self._orders[oid] = order
        return order

    def list_products(self, q: str = ""):
        q = (q or "").lower()
        if not q: return list(self._products)
        return [p for p in self._products if q in p["name"].lower()]

    def find_products(self, q: str = "", category: str | None = None):
        items = self.list_products(q)
        if category: items = [p for p in items if p.get("category") == category]
        return items

    def add_order_line(self, order_id: int, product_id: int, quantity: int):
        order = self._orders.get(order_id)
        prod  = next((p for p in self._products if p["product_id"] == product_id), None)
        if not order or not prod: return None
        qty = max(1, int(quantity))
        take = min(qty, max(0, int(prod["stock_qty"])))
        if take == 0: return order
        line_total = round(take * float(prod["price"]), 2)
        order["lines"].append({
            "product_id": product_id, "name": prod["name"],
            "quantity": take, "unit_price": prod["price"], "line_total": line_total,
        })
        order["total_amount"] = round(sum(l["line_total"] for l in order["lines"]), 2)
        prod["stock_qty"] -= take
        return order

    def pay_order(self, order_id: int, amount: float, method: str = "cash"):
        order = self._orders.get(order_id)
        if not order: return None
        order["status"] = "paid" if amount >= order["total_amount"] else "partial"
        return {"order_id": order_id, "status": order["status"], "paid": float(amount)}

    # ---- Inventory ----
    def low_stock_alerts(self):
        alerts = []
        for p in self._products:
            if p["stock_qty"] <= p["low_stock_threshold"]:
                alerts.append(f"{p['name']} ({p['stock_qty']}≤{p['low_stock_threshold']})")
        return alerts

    def low_stock_items(self):
        return [p for p in self._products if p["stock_qty"] <= p["low_stock_threshold"]]

    # ---- Members / Profile / Subscriptions ----
    def list_members(self, q: str = ""):
        q = (q or "").lower()
        if not q: return list(self._members)
        return [m for m in self._members if q in f"{m['first_name']} {m['last_name']}".lower()]

    def get_member(self, member_id: int):
        return next((m for m in self._members if m["member_id"] == member_id), None)

    def list_subscriptions(self, member_id: int | None = None):
        if member_id is None: return list(self._subs)
        return [s for s in self._subs if s["member_id"] == member_id]

    def renew_subscription(self, *args, **kwargs): return True
    def freeze_subscription(self, *args, **kwargs): return True

    # ---- Attendance ----
    def scan_uid(self, uid: str):
        m = self._members[(hash(uid) % len(self._members))]
        self._checkins.append({"member_id": m["member_id"], "date": "2025-09-21", "time": "10:00"})
        return {"status": "allowed" if m["status"] == "active" else "denied", "member": m}

    def list_checkins(self, member_id: int | None = None):
        if member_id is None: return list(self._checkins)
        return [c for c in self._checkins if c["member_id"] == member_id]

    # ---- ultra-safe fallback ----
    def __getattr__(self, name):
        def _noop(*a, **k): return None
        return _noop

# ---------------- main ----------------
def main():
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")

    root = ctk.CTk()
    root.title(APP_TITLE)
    root.geometry(DEFAULT_SIZE)
    root.configure(fg_color=PALETTE["bg"])

    ensure_sqlite_file(DB_PATH)

    # build stub services
    services = StubServices()

    # try attach real auth service (optional)
    services.auth = try_load_auth_service(DB_PATH)
    if services.auth and hasattr(services.auth, "ensure_seed_admin"):
        try:
            services.auth.ensure_seed_admin()
        except Exception:
            pass

    # login
    dlg = LoginDialog(root, services=services)
    root.wait_window(dlg)
    if not dlg.result.get("user"):
        root.destroy()
        return

    # session into services
    services.user_name = dlg.result["user"]
    services.session_role = dlg.result["role"]

    # mount app — start at Home (header visible only on Home)
    app = AppShell(root, services=services, start_route="Home")
    app.pack(fill="both", expand=True)

    root.mainloop()

if __name__ == "__main__":
    main()
