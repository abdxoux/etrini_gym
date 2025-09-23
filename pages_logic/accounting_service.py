# pages_logic/accounting_service.py
# GymPro — AccountingService for invoices search & Z-Report (SQLite)
from __future__ import annotations

import csv
import datetime as dt
import sqlite3
from typing import Any, Dict, List, Optional, Tuple

# -------- date helpers --------
def _iso(date_like: dt.date | dt.datetime | str) -> str:
    if isinstance(date_like, (dt.date, dt.datetime)):
        return date_like.strftime("%Y-%m-%d")
    return str(date_like)

def _day_bounds(day: dt.date) -> Tuple[str, str]:
    s = f"{day:%Y-%m-%d} 00:00:00"
    e = f"{day:%Y-%m-%d} 23:59:59"
    return s, e

def _week_bounds(anchor: dt.date) -> Tuple[str, str]:
    start = anchor - dt.timedelta(days=anchor.weekday())  # Monday
    end = start + dt.timedelta(days=6)
    return f"{start:%Y-%m-%d} 00:00:00", f"{end:%Y-%m-%d} 23:59:59"

def _month_bounds(anchor: dt.date) -> Tuple[str, str]:
    start = anchor.replace(day=1)
    if start.month == 12:
        end = start.replace(month=12, day=31)
    else:
        end = (start.replace(month=start.month + 1, day=1) - dt.timedelta(days=1))
    return f"{start:%Y-%m-%d} 00:00:00", f"{end:%Y-%m-%d} 23:59:59"

# -------- service --------
class AccountingService:
    """
    Methods:
      - search_invoices(q, status, method, limit)
      - z_report(period, anchor_date)
      - export_z(period, anchor_date, path)

    Data model used:
      members(member_id, first_name, last_name)
      subscriptions(subscription_id, member_id, start_date, end_date, status, created_at, updated_at)
      payments(payment_id, subscription_id, amount, payment_date, method, status, created_at, updated_at)

      pos_orders(order_id, member_id, order_date, order_time, status, total_amount, created_at, updated_at)
      pos_order_lines(line_id, order_id, product_id, quantity, unit_price, line_total)
      pos_payments(pos_payment_id, order_id, amount, payment_date, method, status, created_at, updated_at)
    """
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._conn = sqlite3.connect(self.db_path, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
        self._conn.row_factory = sqlite3.Row
        self._ensure_indexes()

    # ---------- infra ----------
    def _ensure_indexes(self):
        cur = self._conn.cursor()
        cur.executescript(
            """
            -- POS
            CREATE INDEX IF NOT EXISTS idx_pos_orders_date ON pos_orders(order_date, order_time);
            CREATE INDEX IF NOT EXISTS idx_pos_orders_member ON pos_orders(member_id);
            CREATE INDEX IF NOT EXISTS idx_pos_payments_order ON pos_payments(order_id);
            CREATE INDEX IF NOT EXISTS idx_pos_payments_date ON pos_payments(payment_date, status, method);

            -- Subscriptions
            CREATE INDEX IF NOT EXISTS idx_payments_sub ON payments(subscription_id);
            CREATE INDEX IF NOT EXISTS idx_payments_date ON payments(payment_date, status, method);
            CREATE INDEX IF NOT EXISTS idx_subscriptions_member ON subscriptions(member_id);

            -- Members (for search joining)
            CREATE INDEX IF NOT EXISTS idx_members_name ON members(last_name, first_name);
            """
        )
        self._conn.commit()

    def _q(self) -> sqlite3.Cursor:
        return self._conn.cursor()

    # ---------- invoices search ----------
    def search_invoices(self, q: str = "", status: str = "Any", method: str = "Any", limit: int = 120) -> List[Dict[str, Any]]:
        """
        Returns a mixed list of POS orders and Subscription payments normalized to:
          {no, date, typ, who, method, total, paid, status}
        - POS "invoice" is an order (sum lines already stored in pos_orders.total_amount).
          paid = SUM(successful pos_payments.amount)
          status derived from paid vs total; method = 'Mixed' if >1 successful methods seen, else method
        - Subscription "invoice" is each payment row (payments table) with status mapping.
        """
        q = (q or "").strip()
        status = (status or "Any").lower()
        method = (method or "Any").capitalize()

        like = f"%{q}%"

        cur = self._q()

        # ---- POS block (aggregate by order) ----
        # paid_total & methods (distinct) computed from pos_payments (status=succeeded)
        pos_sql = """
        WITH pay AS (
          SELECT
            p.order_id,
            SUM(CASE WHEN p.status='succeeded' THEN p.amount ELSE 0 END) AS paid_total,
            COUNT(DISTINCT CASE WHEN p.status='succeeded' THEN p.method END) AS mcount,
            MIN(CASE WHEN p.status='succeeded' THEN p.method END) AS one_method -- if mcount=1 use this
          FROM pos_payments p
          GROUP BY p.order_id
        ),
        who AS (
          SELECT m.member_id,
                 TRIM(COALESCE(m.first_name,'')||' '||COALESCE(m.last_name,'')) AS full_name
          FROM members m
        )
        SELECT
          o.order_id AS no,
          (o.order_date || ' ' || COALESCE(o.order_time,'')) AS date,
          'POS' AS typ,
          COALESCE(NULLIF(w.full_name,''), 'Walk-in') AS who,
          CASE WHEN COALESCE(pay.mcount,0) > 1 THEN 'Mixed'
               WHEN COALESCE(pay.mcount,0) = 1 THEN pay.one_method
               ELSE '—' END AS method,
          COALESCE(o.total_amount, 0) AS total,
          COALESCE(pay.paid_total, 0) AS paid,
          CASE
            WHEN COALESCE(pay.paid_total,0) >= COALESCE(o.total_amount,0) AND COALESCE(o.total_amount,0) > 0 THEN 'paid'
            WHEN COALESCE(pay.paid_total,0) > 0 THEN 'partial'
            ELSE 'open'
          END AS status
        FROM pos_orders o
        LEFT JOIN pay ON pay.order_id = o.order_id
        LEFT JOIN who w ON w.member_id = o.member_id
        WHERE 1=1
          AND (
                :q = '' OR
                o.order_id LIKE :like OR
                COALESCE(w.full_name,'') LIKE :like
              )
        """

        pos_params = {"q": q, "like": like}

        if status != "any":
            pos_sql += " AND (CASE WHEN COALESCE(pay.paid_total,0) >= COALESCE(o.total_amount,0) AND COALESCE(o.total_amount,0) > 0 THEN 'paid' WHEN COALESCE(pay.paid_total,0) > 0 THEN 'partial' ELSE 'open' END) = :pstatus"
            pos_params["pstatus"] = status

        if method != "Any":
            # Include orders that have at least one succeeded payment in that method
            pos_sql += """
                AND EXISTS (
                    SELECT 1 FROM pos_payments pp
                    WHERE pp.order_id = o.order_id
                      AND pp.status = 'succeeded'
                      AND pp.method = :pmethod
                )
            """
            pos_params["pmethod"] = method

        pos_sql += " ORDER BY date DESC LIMIT :lim"
        pos_params["lim"] = int(limit)

        pos_rows = [dict(r) for r in cur.execute(pos_sql, pos_params).fetchall()]

        # ---- Subscriptions block (each succeeded/pending/failed/refunded payment row) ----
        # We treat each payment row as one invoice-like record.
        sub_sql = """
        WITH who AS (
          SELECT m.member_id,
                 TRIM(COALESCE(m.first_name,'')||' '||COALESCE(m.last_name,'')) AS full_name
          FROM members m
        )
        SELECT
          pay.payment_id AS no,
          pay.payment_date AS date,
          'Subscription' AS typ,
          COALESCE(NULLIF(w.full_name,''), '—') AS who,
          COALESCE(pay.method,'—') AS method,
          pay.amount AS total,
          CASE
            WHEN pay.status = 'succeeded' THEN pay.amount
            WHEN pay.status = 'pending' THEN 0
            WHEN pay.status = 'failed' THEN 0
            WHEN pay.status = 'refunded' THEN 0
            ELSE 0
          END AS paid,
          CASE
            WHEN pay.status = 'succeeded' THEN 'paid'
            WHEN pay.status = 'pending' THEN 'open'
            WHEN pay.status = 'failed' THEN 'open'
            WHEN pay.status = 'refunded' THEN 'open'
            ELSE 'open'
          END AS status
        FROM payments pay
        LEFT JOIN subscriptions s ON s.subscription_id = pay.subscription_id
        LEFT JOIN who w ON w.member_id = s.member_id
        WHERE 1=1
          AND (
                :q = '' OR
                pay.payment_id LIKE :like OR
                COALESCE(w.full_name,'') LIKE :like
              )
        """
        sub_params = {"q": q, "like": like}

        if status != "any":
            # map to our normalized 'status' alias above
            sub_sql += """
                AND (CASE
                       WHEN pay.status='succeeded' THEN 'paid'
                       WHEN pay.status='pending' THEN 'open'
                       WHEN pay.status='failed' THEN 'open'
                       WHEN pay.status='refunded' THEN 'open'
                       ELSE 'open'
                     END) = :sstatus
            """
            sub_params["sstatus"] = status

        if method != "Any":
            sub_sql += " AND COALESCE(pay.method,'—') = :smethod"
            sub_params["smethod"] = method

        sub_sql += " ORDER BY date DESC LIMIT :lim"
        sub_params["lim"] = int(limit)

        sub_rows = [dict(r) for r in cur.execute(sub_sql, sub_params).fetchall()]

        # Merge + top limit across both, sorted by date desc
        combined = pos_rows + sub_rows
        combined.sort(key=lambda r: r.get("date") or "", reverse=True)
        return combined[:limit]

    # ---------- Z-Report ----------
    def z_report(self, period: str, anchor_date: dt.date) -> Dict[str, Any]:
        """
        Returns totals split by POS and Subscriptions over the chosen range.
        - pos_gross: sum(pos_orders.total_amount) in range
        - sub_gross: sum(payments.amount WHERE status='succeeded') in range
        - refunds:   sum(refunded) across pos_payments + payments in range
        - cash/card/transfer: sum of succeeded payments across both sources grouped by method
        - count: number of receipts = (#pos_orders with any succeeded payment) + (#subscription payments succeeded)
        """
        period = (period or "Daily").capitalize()
        if period not in ("Daily", "Weekly", "Monthly"):
            period = "Daily"

        if period == "Weekly":
            start, end = _week_bounds(anchor_date)
        elif period == "Monthly":
            start, end = _month_bounds(anchor_date)
        else:
            start, end = _day_bounds(anchor_date)

        cur = self._q()

        # POS gross from orders in date window
        pos_gross = cur.execute(
            """
            SELECT COALESCE(SUM(o.total_amount),0)
            FROM pos_orders o
            WHERE (o.order_date || ' ' || COALESCE(o.order_time,'')) BETWEEN ? AND ?
            """,
            (start, end),
        ).fetchone()[0] or 0

        # Subscriptions gross from succeeded payments
        sub_gross = cur.execute(
            """
            SELECT COALESCE(SUM(p.amount),0)
            FROM payments p
            WHERE p.status='succeeded'
              AND (p.payment_date || ' 00:00:00') BETWEEN ? AND ?
            """,
            (start, end),
        ).fetchone()[0] or 0

        # Refunds (both sources)
        pos_refunds = cur.execute(
            """
            SELECT COALESCE(SUM(pp.amount),0)
            FROM pos_payments pp
            WHERE pp.status='refunded'
              AND (pp.payment_date || ' 00:00:00') BETWEEN ? AND ?
            """,
            (start, end),
        ).fetchone()[0] or 0

        sub_refunds = cur.execute(
            """
            SELECT COALESCE(SUM(p.amount),0)
            FROM payments p
            WHERE p.status='refunded'
              AND (p.payment_date || ' 00:00:00') BETWEEN ? AND ?
            """,
            (start, end),
        ).fetchone()[0] or 0

        refunds = (pos_refunds or 0) + (sub_refunds or 0)
        net = max(0, (pos_gross or 0) + (sub_gross or 0) - (refunds or 0))

        # Payment method totals (succeeded only)
        cash_pos = cur.execute(
            """
            SELECT COALESCE(SUM(pp.amount),0)
            FROM pos_payments pp
            WHERE pp.status='succeeded' AND pp.method='Cash'
              AND (pp.payment_date || ' 00:00:00') BETWEEN ? AND ?
            """, (start, end)
        ).fetchone()[0] or 0
        card_pos = cur.execute(
            """
            SELECT COALESCE(SUM(pp.amount),0)
            FROM pos_payments pp
            WHERE pp.status='succeeded' AND pp.method='Card'
              AND (pp.payment_date || ' 00:00:00') BETWEEN ? AND ?
            """, (start, end)
        ).fetchone()[0] or 0
        transfer_pos = cur.execute(
            """
            SELECT COALESCE(SUM(pp.amount),0)
            FROM pos_payments pp
            WHERE pp.status='succeeded' AND pp.method='Transfer'
              AND (pp.payment_date || ' 00:00:00') BETWEEN ? AND ?
            """, (start, end)
        ).fetchone()[0] or 0

        cash_sub = cur.execute(
            """
            SELECT COALESCE(SUM(p.amount),0)
            FROM payments p
            WHERE p.status='succeeded' AND p.method='Cash'
              AND (p.payment_date || ' 00:00:00') BETWEEN ? AND ?
            """, (start, end)
        ).fetchone()[0] or 0
        card_sub = cur.execute(
            """
            SELECT COALESCE(SUM(p.amount),0)
            FROM payments p
            WHERE p.status='succeeded' AND p.method='Card'
              AND (p.payment_date || ' 00:00:00') BETWEEN ? AND ?
            """, (start, end)
        ).fetchone()[0] or 0
        transfer_sub = cur.execute(
            """
            SELECT COALESCE(SUM(p.amount),0)
            FROM payments p
            WHERE p.status='succeeded' AND p.method='Transfer'
              AND (p.payment_date || ' 00:00:00') BETWEEN ? AND ?
            """, (start, end)
        ).fetchone()[0] or 0

        cash = (cash_pos or 0) + (cash_sub or 0)
        card = (card_pos or 0) + (card_sub or 0)
        transfer = (transfer_pos or 0) + (transfer_sub or 0)

        # Count of receipts:
        # - POS: only orders that have at least one succeeded payment in window
        pos_count = cur.execute(
            """
            SELECT COUNT(DISTINCT pp.order_id)
            FROM pos_payments pp
            WHERE pp.status='succeeded'
              AND (pp.payment_date || ' 00:00:00') BETWEEN ? AND ?
            """, (start, end)
        ).fetchone()[0] or 0

        # - Subscriptions: count of succeeded payment rows in window
        sub_count = cur.execute(
            """
            SELECT COUNT(1)
            FROM payments p
            WHERE p.status='succeeded'
              AND (p.payment_date || ' 00:00:00') BETWEEN ? AND ?
            """, (start, end)
        ).fetchone()[0] or 0

        count = (pos_count or 0) + (sub_count or 0)

        # Parse start/end back to dates for UI
        s_date = dt.date.fromisoformat(start[:10])
        e_date = dt.date.fromisoformat(end[:10])

        return {
            "period": period,
            "start": s_date,
            "end": e_date,
            "pos_gross": float(pos_gross or 0),
            "sub_gross": float(sub_gross or 0),
            "refunds": float(refunds or 0),
            "net": float(net or 0),
            "cash": float(cash or 0),
            "card": float(card or 0),
            "transfer": float(transfer or 0),
            "count": int(count or 0),
        }

    # ---------- export ----------
    def export_z(self, period: str, anchor_date: dt.date, path: str) -> None:
        data = self.z_report(period, anchor_date)
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["metric", "value"])
            for k in ("period", "start", "end",
                      "pos_gross", "sub_gross", "refunds", "net",
                      "cash", "card", "transfer", "count"):
                v = data.get(k)
                if isinstance(v, dt.date):
                    v = v.isoformat()
                w.writerow([k, v])
