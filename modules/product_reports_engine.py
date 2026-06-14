"""
Product Daily/Period Report
-----------------------------
Generates a day-by-day breakdown for every product, showing:
    Date | Product Name | Available | Sold | Remaining | Revenue | Profit

Logic:
- "Sold" for a given day = sum of invoice_items.quantity for that product
  where the invoice date falls on that day.
- "Adjustment" for a given day = sum of stock_adjustments.quantity_change
  for that product on that day (manual quantity edits).
- "Remaining" (closing stock at end of that day) is computed backwards from
  the CURRENT live stock in inventory:
        remaining(day) = current_qty
                          - sum(sold on days AFTER this day)
                          + sum(adjustments on days AFTER this day)
  (subtracting later sales adds them back; reversing later adjustments
   removes their effect, giving the stock level as it stood at end of `day`)
- "Available" (opening stock for that day) = remaining(day) + sold(day) - adjustment(day)
- Revenue = sum(line_total) for that day
- Cost    = sum(cost_price * quantity) for that day
- Profit  = Revenue - Cost
"""

import sqlite3
from datetime import datetime, timedelta

from database.db_manager import DB_PATH, get_all_products


def _daterange(start_date, end_date):
    """Yields date strings (YYYY-MM-DD) from start_date to end_date inclusive."""
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")
    cur = start
    while cur <= end:
        yield cur.strftime("%Y-%m-%d")
        cur += timedelta(days=1)


def get_product_daily_report(start_date, end_date, product_id=None):
    """
    Returns a list of dicts, one per (date, product) combination, sorted by
    date then product name.

    start_date, end_date: 'YYYY-MM-DD' strings, inclusive.
    product_id: optional - filter to a single product. If None, all products.

    Each dict has keys:
        date, product_id, product_name, available, sold, remaining,
        revenue, cost, profit
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    today_str = datetime.now().strftime("%Y-%m-%d")

    # 1. Fetch product list (id, name, current quantity)
    if product_id:
        cursor.execute(
            "SELECT product_id, name, quantity FROM inventory WHERE product_id=?",
            (int(product_id),)
        )
    else:
        cursor.execute("SELECT product_id, name, quantity FROM inventory ORDER BY name ASC")
    products = cursor.fetchall()  # list of (product_id, name, current_qty)

    # 2. Fetch all sold quantities grouped by (product_id, date)
    cursor.execute("""
        SELECT ii.product_id, date(i.date) as d, SUM(ii.quantity), SUM(ii.line_total),
               SUM(ii.cost_price * ii.quantity)
        FROM invoice_items ii
        JOIN invoices i ON ii.invoice_id = i.invoice_id
        GROUP BY ii.product_id, d
    """)
    sold_rows = cursor.fetchall()

    # 3. Fetch all stock adjustments grouped by (product_id, date)
    cursor.execute("""
        SELECT product_id, date(timestamp) as d, SUM(quantity_change)
        FROM stock_adjustments
        GROUP BY product_id, d
    """)
    adj_rows = cursor.fetchall()

    conn.close()

    # Build lookup dicts: sold_map[(pid, date)] = (qty, revenue, cost)
    sold_map = {}
    for pid, d, qty, revenue, cost in sold_rows:
        sold_map[(pid, d)] = (qty or 0, revenue or 0.0, cost or 0.0)

    adj_map = {}
    for pid, d, qty_change in adj_rows:
        adj_map[(pid, d)] = qty_change or 0

    dates = list(_daterange(start_date, end_date))

    results = []

    for pid, pname, current_qty in products:
        # We reconstruct the closing stock level at the end of each day by
        # walking backwards from today's live stock down to the earliest
        # date needed for this report.
        closing_stock_at = {}
        running_qty = current_qty

        earliest_needed = min(dates + [today_str])
        cursor_date = datetime.strptime(today_str, "%Y-%m-%d")
        earliest_dt = datetime.strptime(earliest_needed, "%Y-%m-%d")

        while cursor_date >= earliest_dt:
            d_str = cursor_date.strftime("%Y-%m-%d")
            closing_stock_at[d_str] = running_qty

            # Step back one day: closing(d-1) = closing(d) - sold(d) + adjustment(d)
            sold_qty_today, _, _ = sold_map.get((pid, d_str), (0, 0.0, 0.0))
            adj_qty_today = adj_map.get((pid, d_str), 0)
            running_qty = running_qty - sold_qty_today + adj_qty_today

            cursor_date -= timedelta(days=1)

        # Build the final per-day rows for the requested range
        for d in dates:
            sold_qty, revenue, cost = sold_map.get((pid, d), (0, 0.0, 0.0))
            adj_qty = adj_map.get((pid, d), 0)
            remaining = closing_stock_at.get(d, current_qty)
            available = remaining + sold_qty - adj_qty
            profit = revenue - cost

            results.append({
                "date": d,
                "product_id": pid,
                "product_name": pname,
                "available": available,
                "sold": sold_qty,
                "remaining": remaining,
                "revenue": round(revenue, 2),
                "cost": round(cost, 2),
                "profit": round(profit, 2),
            })

    # Sort by date then product name
    results.sort(key=lambda r: (r["date"], r["product_name"]))
    return results


def get_period_presets():
    """
    Returns a dict of preset label -> (start_date, end_date) as 'YYYY-MM-DD'
    strings, based on today's date. Includes:
        - This Month
        - Last 3 Months
        - Last 6 Months
        - This Year
        - Available Years (for year-based selection, e.g. 2025, 2026...)
    """
    today = datetime.now()
    presets = {}

    # This month
    month_start = today.replace(day=1)
    presets["This Month"] = (month_start.strftime("%Y-%m-%d"), today.strftime("%Y-%m-%d"))

    # Last 3 months (approx 90 days back, normalized to 1st of month)
    three_months_ago = (month_start - timedelta(days=62)).replace(day=1)
    presets["Last 3 Months"] = (three_months_ago.strftime("%Y-%m-%d"), today.strftime("%Y-%m-%d"))

    # Last 6 months
    six_months_ago = (month_start - timedelta(days=153)).replace(day=1)
    presets["Last 6 Months"] = (six_months_ago.strftime("%Y-%m-%d"), today.strftime("%Y-%m-%d"))

    # This year
    presets["This Year"] = (f"{today.year}-01-01", today.strftime("%Y-%m-%d"))

    return presets


def get_available_years():
    """
    Returns a sorted list of years (int) that have any invoice or stock
    adjustment activity, plus the current year (always included).
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    years = set()
    years.add(datetime.now().year)

    cursor.execute("SELECT DISTINCT strftime('%Y', date) FROM invoices WHERE date IS NOT NULL")
    for (y,) in cursor.fetchall():
        if y:
            years.add(int(y))

    cursor.execute("SELECT DISTINCT strftime('%Y', timestamp) FROM stock_adjustments WHERE timestamp IS NOT NULL")
    for (y,) in cursor.fetchall():
        if y:
            years.add(int(y))

    conn.close()
    return sorted(years, reverse=True)


def get_year_range(year):
    """Returns (start_date, end_date) for a full calendar year as 'YYYY-MM-DD'."""
    return f"{year}-01-01", f"{year}-12-31"
