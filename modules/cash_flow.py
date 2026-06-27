"""
Cash Flow Monitor
=================
Two-tab view: Cash In | Cash Out
• Date range filter
• Detailed records with source, description, amount
• Export to PDF (separate for each tab)
• Running total at the bottom
"""

import sqlite3
import tkinter as tk
import tkinter.messagebox as messagebox
import tkinter.filedialog as filedialog
import customtkinter as ctk
from datetime import datetime, date, timedelta

import database.db_manager as db
from modules.pdf_export import build_table_html, export_html_to_pdf

try:
    from tkcalendar import Calendar
    CALENDAR_OK = True
except ImportError:
    CALENDAR_OK = False

# ─────────────────────────────────────────────────────────────────────────────
# COLOUR PALETTE  (matches the dark shell)
# ─────────────────────────────────────────────────────────────────────────────
BG_MAIN      = "#0c0c0e"
BG_PANEL     = "#16161a"
BG_CARD      = "#1c1c22"
BG_ROW_ALT  = "#18181e"
ACCENT_BLUE  = "#4a90e2"
ACCENT_GREEN = "#3dd68c"
ACCENT_RED   = "#ff5f5f"
ACCENT_GOLD  = "#f0c040"
TEXT_PRIMARY = "#e8e8f0"
TEXT_MUTED   = "#6e6e77"
BORDER       = "#2a2a33"


# ─────────────────────────────────────────────────────────────────────────────
# CALENDAR POPUP
# ─────────────────────────────────────────────────────────────────────────────
def _open_calendar(parent, entry_widget):
    if not CALENDAR_OK:
        messagebox.showwarning("Calendar", "tkcalendar install karein:\npip install tkcalendar")
        return
    popup = tk.Toplevel(parent)
    popup.title("Tarikh Chunein")
    popup.resizable(False, False)
    popup.transient(parent.winfo_toplevel())
    popup.grab_set()

    existing = entry_widget.get().strip()
    kw = dict(selectmode="day", date_pattern="yyyy-mm-dd",
              background="#1f293d", foreground="white",
              headersbackground="#121214", normalbackground="#16161a",
              weekendbackground="#16161a", selectbackground="#4a90e2")
    if existing:
        try:
            y, m, d_ = map(int, existing.split("-"))
            kw["year"] = y; kw["month"] = m; kw["day"] = d_
        except Exception:
            pass

    cal = Calendar(popup, **kw)
    cal.pack(padx=14, pady=14)

    def _pick():
        entry_widget.delete(0, "end")
        entry_widget.insert(0, cal.get_date())
        popup.destroy()

    ctk.CTkButton(popup, text="Theek Hai", command=_pick,
                  fg_color=ACCENT_BLUE, width=160).pack(pady=(0, 10))


# ─────────────────────────────────────────────────────────────────────────────
# DB QUERIES
# ─────────────────────────────────────────────────────────────────────────────
def _fetch_cash_in(date_from: str, date_to: str) -> list[dict]:
    """
    Cash In sources:
      1. invoices  – every paid invoice (net_amount)
      2. ledger_transactions ADVANCE_DEPOSIT – customer advances received
    """
    rows = []

    # 1. Invoices (main billing revenue)
    try:
        conn = db.get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT date, invoice_id, customer_name, payment_mode, net_amount
            FROM   invoices
            WHERE  DATE(date) BETWEEN ? AND ?
            ORDER  BY date ASC
        """, (date_from, date_to))
        for r in cur.fetchall():
            rows.append({
                "date":        r[0],
                "source":      "Invoice / Sale",
                "ref":         f"INV-{r[1]}",
                "party":       r[2] or "Walk-in Customer",
                "description": f"Payment Mode: {r[3] or 'Cash'}",
                "amount":      r[4] or 0.0,
            })
        conn.close()
    except Exception:
        pass

    # 2. Advance Deposits from Credit Ledger
    try:
        lconn = sqlite3.connect("database/pos_system.db")
        lcur  = lconn.cursor()
        lcur.execute("""
            SELECT lt.timestamp, lt.log_id, lc.customer_name, lt.amount, lt.description, lt.closing_balance
            FROM   ledger_transactions lt
            JOIN   ledger_customers    lc ON lt.khata_id = lc.khata_id
            WHERE  lt.action_type = 'ADVANCE_DEPOSIT'
              AND  DATE(lt.timestamp) BETWEEN ? AND ?
            ORDER  BY lt.timestamp ASC
        """, (date_from, date_to))
        for r in lcur.fetchall():
            rows.append({
                "date":        r[0][:10] if r[0] else "",
                "source":      "Advance / Deposit",
                "ref":         f"TXN-{r[1]}",
                "party":       r[2] or "—",
                "description": r[4] or "Customer advance received",
                "amount":      abs(r[3]) if r[3] else 0.0,
            })
        lconn.close()
    except Exception:
        pass

    rows.sort(key=lambda x: x["date"])
    return rows


def _fetch_cash_out(date_from: str, date_to: str) -> list[dict]:
    """
    Cash Out sources:
      1. household_expenses        – daily household / business expenses
      2. ledger_transactions CASH_WITHDRAWAL  – cash pulled out for customers
      3. ledger_transactions PURCHASE_DEBIT   – udhaar given (credit sales)
      4. ledger_transactions OVERDRAFT_CREDIT – overdraft credit extended
    """
    rows = []

    # 1. Household / Business Expenses
    try:
        conn = db.get_connection()
        cur  = conn.cursor()
        cur.execute("""
            SELECT expense_date, expense_id, category, description, amount
            FROM   household_expenses
            WHERE  DATE(expense_date) BETWEEN ? AND ?
            ORDER  BY expense_date ASC
        """, (date_from, date_to))
        for r in cur.fetchall():
            rows.append({
                "date":        r[0],
                "source":      "Household Expense",
                "ref":         f"EXP-{r[1]}",
                "party":       r[2] or "—",
                "description": r[3] or "No description",
                "amount":      abs(r[4]) if r[4] else 0.0,
            })
        conn.close()
    except Exception:
        pass

    # 2-4. Ledger outflows
    OUT_TYPES = ("CASH_WITHDRAWAL", "PURCHASE_DEBIT", "OVERDRAFT_CREDIT")
    SOURCE_LABELS = {
        "CASH_WITHDRAWAL":  "Cash Withdrawal",
        "PURCHASE_DEBIT":   "Credit Sale (Udhaar)",
        "OVERDRAFT_CREDIT": "Overdraft Credit",
    }
    try:
        lconn = sqlite3.connect("database/pos_system.db")
        lcur  = lconn.cursor()
        placeholders = ",".join("?" * len(OUT_TYPES))
        lcur.execute(f"""
            SELECT lt.timestamp, lt.log_id, lt.action_type, lc.customer_name,
                   lt.amount, lt.description, lt.closing_balance
            FROM   ledger_transactions lt
            JOIN   ledger_customers    lc ON lt.khata_id = lc.khata_id
            WHERE  lt.action_type IN ({placeholders})
              AND  DATE(lt.timestamp) BETWEEN ? AND ?
            ORDER  BY lt.timestamp ASC
        """, (*OUT_TYPES, date_from, date_to))
        for r in lcur.fetchall():
            rows.append({
                "date":        r[0][:10] if r[0] else "",
                "source":      SOURCE_LABELS.get(r[2], r[2]),
                "ref":         f"TXN-{r[1]}",
                "party":       r[3] or "—",
                "description": r[5] or r[2],
                "amount":      abs(r[4]) if r[4] else 0.0,
            })
        lconn.close()
    except Exception:
        pass

    rows.sort(key=lambda x: x["date"])
    return rows


# ─────────────────────────────────────────────────────────────────────────────
# REUSABLE TABLE WIDGET
# ─────────────────────────────────────────────────────────────────────────────
class _CashTable(ctk.CTkFrame):
    HEADERS    = ["#", "Date", "Source", "Ref", "Party / Category", "Description", "Amount (Rs)"]
    COL_WIDTHS = [30, 90, 140, 80, 170, 220, 110]
    PAGE_SIZE  = 12
    ROW_H      = 44   # actual rendered height per row in CTk

    def __init__(self, parent, accent_color, **kwargs):
        super().__init__(parent, fg_color=BG_PANEL, corner_radius=10, **kwargs)
        self._accent   = accent_color
        self._all_rows = []   # full dataset
        self._cur_page = 1
        self._build()

    # ── layout ──────────────────────────────────────────────────────────────
    def _build(self):
        # Column header
        hdr = ctk.CTkFrame(self, fg_color=BG_CARD, corner_radius=0, height=36)
        hdr.pack(fill="x", pady=(0, 1))
        hdr.pack_propagate(False)
        hdr_inner = ctk.CTkFrame(hdr, fg_color="transparent")
        hdr_inner.pack(fill="both", expand=True, padx=6)
        for h, w in zip(self.HEADERS, self.COL_WIDTHS):
            anchor = "e" if h == "Amount (Rs)" else "w"
            ctk.CTkLabel(hdr_inner, text=h, width=w,
                         font=ctk.CTkFont("Arial", 11, "bold"),
                         text_color=self._accent, anchor=anchor).pack(side="left", padx=(2, 4))

        # ── Pagination bar packed FIRST at bottom (Tkinter rule: side="bottom" must be packed before body)
        pg_bar = ctk.CTkFrame(self, fg_color=BG_CARD, corner_radius=0, height=38)
        pg_bar.pack(fill="x", pady=(1, 0), side="bottom")
        pg_bar.pack_propagate(False)
        pg_inner = ctk.CTkFrame(pg_bar, fg_color="transparent")
        pg_inner.pack(fill="both", expand=True, padx=10)

        self._btn_prev = ctk.CTkButton(pg_inner, text="◀  Prev", width=90, height=26,
                                        fg_color=BG_PANEL, hover_color=BORDER,
                                        text_color=TEXT_MUTED, border_color=BORDER, border_width=1,
                                        font=ctk.CTkFont("Arial", 11),
                                        command=self._prev_page)
        self._btn_prev.pack(side="left", padx=(0, 6))

        self._page_lbl = ctk.CTkLabel(pg_inner, text="Page 1 / 1",
                                       font=ctk.CTkFont("Arial", 11),
                                       text_color=TEXT_MUTED, width=120)
        self._page_lbl.pack(side="left")

        self._btn_next = ctk.CTkButton(pg_inner, text="Next  ▶", width=90, height=26,
                                        fg_color=BG_PANEL, hover_color=BORDER,
                                        text_color=TEXT_MUTED, border_color=BORDER, border_width=1,
                                        font=ctk.CTkFont("Arial", 11),
                                        command=self._next_page)
        self._btn_next.pack(side="left", padx=6)

        self._count_lbl = ctk.CTkLabel(pg_inner, text="0 records",
                                        font=ctk.CTkFont("Arial", 11),
                                        text_color=TEXT_MUTED)
        self._count_lbl.pack(side="left", padx=14)

        self._total_lbl = ctk.CTkLabel(pg_inner, text="Total: Rs 0",
                                        font=ctk.CTkFont("Arial", 13, "bold"),
                                        text_color=self._accent)
        self._total_lbl.pack(side="right", padx=10)

        self._page_total_lbl = ctk.CTkLabel(pg_inner, text="",
                                             font=ctk.CTkFont("Arial", 11),
                                             text_color=TEXT_MUTED)
        self._page_total_lbl.pack(side="right", padx=(0, 12))

        # ── Body frame — fills ALL remaining space between header and pagination bar
        self._body = ctk.CTkFrame(self, fg_color=BG_MAIN, corner_radius=0)
        self._body.pack(fill="both", expand=True, padx=0, pady=0)

    # ── pagination helpers ───────────────────────────────────────────────────
    def _total_pages(self):
        if not self._all_rows:
            return 1
        import math
        return math.ceil(len(self._all_rows) / self.PAGE_SIZE)

    def _prev_page(self):
        if self._cur_page > 1:
            self._cur_page -= 1
            self._render_page()

    def _next_page(self):
        if self._cur_page < self._total_pages():
            self._cur_page += 1
            self._render_page()

    def _render_page(self):
        # Clear body
        for w in self._body.winfo_children():
            w.destroy()

        tp    = self._total_pages()
        start = (self._cur_page - 1) * self.PAGE_SIZE
        page_rows = self._all_rows[start: start + self.PAGE_SIZE]

        page_total = 0.0
        for slot in range(self.PAGE_SIZE):
            bg = BG_ROW_ALT if slot % 2 == 0 else BG_PANEL
            row_frame = ctk.CTkFrame(self._body, fg_color=bg, corner_radius=0)
            row_frame.pack(fill="both", expand=True)
            inner = ctk.CTkFrame(row_frame, fg_color="transparent")
            inner.pack(fill="both", expand=True, padx=6)

            if slot < len(page_rows):
                r   = page_rows[slot]
                idx = start + slot    # global 0-based index
                page_total += r["amount"]
                cells = [
                    str(idx + 1),
                    r.get("date", "")[:10],
                    r.get("source", ""),
                    r.get("ref", ""),
                    r.get("party", ""),
                    r.get("description", ""),
                    f"Rs {r['amount']:,.0f}",
                ]
                for i, (val, w) in enumerate(zip(cells, self.COL_WIDTHS)):
                    anchor = "e" if i == 6 else "w"
                    color  = self._accent if i == 6 else TEXT_PRIMARY
                    ctk.CTkLabel(inner, text=val, width=w, anchor=anchor,
                                 font=ctk.CTkFont("Arial", 11),
                                 text_color=color).pack(side="left", padx=(2, 4))
            # empty slot → blank row (already bg-coloured, nothing to add)

        # Update pagination controls
        self._page_lbl.configure(text=f"Page {self._cur_page} / {tp}")
        self._btn_prev.configure(state="normal" if self._cur_page > 1 else "disabled",
                                  text_color=TEXT_PRIMARY if self._cur_page > 1 else TEXT_MUTED)
        self._btn_next.configure(state="normal" if self._cur_page < tp else "disabled",
                                  text_color=TEXT_PRIMARY if self._cur_page < tp else TEXT_MUTED)

        grand_total = sum(r["amount"] for r in self._all_rows)
        self._total_lbl.configure(text=f"Grand Total: Rs {grand_total:,.0f}")
        self._count_lbl.configure(text=f"{len(self._all_rows)} records")
        if tp > 1:
            self._page_total_lbl.configure(
                text=f"Page Total: Rs {page_total:,.0f}")
        else:
            self._page_total_lbl.configure(text="")

    # ── public ──────────────────────────────────────────────────────────────
    def load(self, rows: list[dict]):
        self._all_rows = rows
        self._cur_page = 1
        self._render_page()

    def get_rows(self):
        return self._all_rows

    def get_total(self):
        return sum(r["amount"] for r in self._all_rows)


# ─────────────────────────────────────────────────────────────────────────────
# MAIN VIEW
# ─────────────────────────────────────────────────────────────────────────────
class CashFlowView(ctk.CTkFrame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self._active_tab = "in"
        self._build()
        # Default: today
        today = date.today().strftime("%Y-%m-%d")
        self._date_from.insert(0, today)
        self._date_to.insert(0, today)
        self._load()

    # ── shell ────────────────────────────────────────────────────────────────
    def _build(self):
        # ── Filter bar ───────────────────────────────────────────────────────
        filter_bar = ctk.CTkFrame(self, fg_color=BG_PANEL, corner_radius=10, height=60)
        filter_bar.pack(fill="x", pady=(0, 10))
        filter_bar.pack_propagate(False)

        inner = ctk.CTkFrame(filter_bar, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=18, pady=10)

        ctk.CTkLabel(inner, text="From:", font=ctk.CTkFont("Arial", 12),
                     text_color=TEXT_MUTED).pack(side="left")
        self._date_from = ctk.CTkEntry(inner, width=110, placeholder_text="YYYY-MM-DD",
                                        fg_color=BG_CARD, border_color=BORDER,
                                        text_color=TEXT_PRIMARY)
        self._date_from.pack(side="left", padx=(4, 2))
        ctk.CTkButton(inner, text="📅", width=32, fg_color=BG_CARD, hover_color=BORDER,
                      command=lambda: _open_calendar(self, self._date_from)).pack(side="left", padx=(0, 14))

        ctk.CTkLabel(inner, text="To:", font=ctk.CTkFont("Arial", 12),
                     text_color=TEXT_MUTED).pack(side="left")
        self._date_to = ctk.CTkEntry(inner, width=110, placeholder_text="YYYY-MM-DD",
                                      fg_color=BG_CARD, border_color=BORDER,
                                      text_color=TEXT_PRIMARY)
        self._date_to.pack(side="left", padx=(4, 2))
        ctk.CTkButton(inner, text="📅", width=32, fg_color=BG_CARD, hover_color=BORDER,
                      command=lambda: _open_calendar(self, self._date_to)).pack(side="left", padx=(0, 14))

        # Quick-range shortcuts
        for label, delta in [("Today", 0), ("7 Days", 7), ("30 Days", 30), ("This Month", -1)]:
            ctk.CTkButton(inner, text=label, width=82, height=30,
                          fg_color=BG_CARD, hover_color=BORDER,
                          text_color=TEXT_MUTED, border_color=BORDER, border_width=1,
                          font=ctk.CTkFont("Arial", 11),
                          command=lambda d=delta: self._quick_range(d)).pack(side="left", padx=3)

        ctk.CTkButton(inner, text="🔍  Search", width=110, height=30,
                      fg_color=ACCENT_BLUE, hover_color="#3a7bc8",
                      font=ctk.CTkFont("Arial", 12, "bold"),
                      command=self._load).pack(side="left", padx=(12, 0))

        ctk.CTkButton(inner, text="⬇  Export PDF", width=120, height=30,
                      fg_color="#2a3d28", hover_color="#364d34", text_color=ACCENT_GREEN,
                      font=ctk.CTkFont("Arial", 12),
                      command=self._export_pdf).pack(side="right", padx=(0, 0))

        # ── Tabs ─────────────────────────────────────────────────────────────
        tab_bar = ctk.CTkFrame(self, fg_color=BG_PANEL, corner_radius=10, height=46)
        tab_bar.pack(fill="x", pady=(0, 8))
        tab_bar.pack_propagate(False)
        tb_inner = ctk.CTkFrame(tab_bar, fg_color="transparent")
        tb_inner.pack(fill="both", expand=True, padx=14, pady=6)

        self._btn_in = ctk.CTkButton(tb_inner, text="💰  Cash In", width=160, height=32,
                                      fg_color=ACCENT_GREEN, hover_color="#30b07a",
                                      text_color="#0a1f14",
                                      font=ctk.CTkFont("Arial", 13, "bold"),
                                      command=lambda: self._switch_tab("in"))
        self._btn_in.pack(side="left", padx=(0, 8))

        self._btn_out = ctk.CTkButton(tb_inner, text="💸  Cash Out", width=160, height=32,
                                       fg_color=BG_CARD, hover_color=BORDER,
                                       text_color=TEXT_MUTED,
                                       font=ctk.CTkFont("Arial", 13),
                                       command=lambda: self._switch_tab("out"))
        self._btn_out.pack(side="left")

        # Summary badges (update after load)
        self._badge_in  = ctk.CTkLabel(tb_inner, text="", font=ctk.CTkFont("Arial", 12),
                                        text_color=ACCENT_GREEN)
        self._badge_in.pack(side="right", padx=(0, 8))
        self._badge_out = ctk.CTkLabel(tb_inner, text="", font=ctk.CTkFont("Arial", 12),
                                        text_color=ACCENT_RED)
        self._badge_out.pack(side="right", padx=(0, 16))

        # ── Net Flow bar ─────────────────────────────────────────────────────
        # Pack BEFORE tables so it stays visible at bottom (pack order matters)
        net_bar = ctk.CTkFrame(self, fg_color=BG_CARD, corner_radius=10, height=44)
        net_bar.pack(fill="x", pady=(0, 0), side="bottom")
        net_bar.pack_propagate(False)
        nb_inner = ctk.CTkFrame(net_bar, fg_color="transparent")
        nb_inner.pack(fill="both", expand=True, padx=20)
        ctk.CTkLabel(nb_inner, text="Net Cash Flow (In − Out):",
                     font=ctk.CTkFont("Arial", 12), text_color=TEXT_MUTED).pack(side="left")
        self._net_lbl = ctk.CTkLabel(nb_inner, text="Rs 0",
                                      font=ctk.CTkFont("Arial", 14, "bold"),
                                      text_color=ACCENT_GREEN)
        self._net_lbl.pack(side="left", padx=10)
        self._net_in_lbl  = ctk.CTkLabel(nb_inner, text="", font=ctk.CTkFont("Arial", 11), text_color=ACCENT_GREEN)
        self._net_in_lbl.pack(side="right", padx=(0, 30))
        self._net_out_lbl = ctk.CTkLabel(nb_inner, text="", font=ctk.CTkFont("Arial", 11), text_color=ACCENT_RED)
        self._net_out_lbl.pack(side="right", padx=(0, 16))

        # ── Tables ───────────────────────────────────────────────────────────
        # Pack AFTER net_bar (which is side="bottom") so they fill remaining space
        self._tbl_in  = _CashTable(self, accent_color=ACCENT_GREEN)
        self._tbl_out = _CashTable(self, accent_color=ACCENT_RED)
        # Only one shown at a time — fill both so pagination bar is always visible
        self._tbl_in.pack(fill="both", expand=True, pady=(0, 0))

    # ── helpers ─────────────────────────────────────────────────────────────
    def _quick_range(self, delta):
        today = date.today()
        if delta == -1:           # This month
            df = today.replace(day=1).strftime("%Y-%m-%d")
            dt = today.strftime("%Y-%m-%d")
        elif delta == 0:
            df = dt = today.strftime("%Y-%m-%d")
        else:
            df = (today - timedelta(days=delta - 1)).strftime("%Y-%m-%d")
            dt = today.strftime("%Y-%m-%d")
        for e, v in [(self._date_from, df), (self._date_to, dt)]:
            e.delete(0, "end"); e.insert(0, v)
        self._load()

    def _switch_tab(self, tab: str):
        self._active_tab = tab
        if tab == "in":
            self._tbl_out.pack_forget()
            self._tbl_in.pack(fill="both", expand=True)
            self._btn_in.configure(fg_color=ACCENT_GREEN, text_color="#0a1f14",
                                   font=ctk.CTkFont("Arial", 13, "bold"))
            self._btn_out.configure(fg_color=BG_CARD, text_color=TEXT_MUTED,
                                    font=ctk.CTkFont("Arial", 13))
        else:
            self._tbl_in.pack_forget()
            self._tbl_out.pack(fill="both", expand=True)
            self._btn_out.configure(fg_color=ACCENT_RED, text_color="#1f0a0a",
                                    font=ctk.CTkFont("Arial", 13, "bold"))
            self._btn_in.configure(fg_color=BG_CARD, text_color=TEXT_MUTED,
                                   font=ctk.CTkFont("Arial", 13))

    def _load(self):
        df = self._date_from.get().strip() or date.today().strftime("%Y-%m-%d")
        dt = self._date_to.get().strip()   or date.today().strftime("%Y-%m-%d")

        in_rows  = _fetch_cash_in(df, dt)
        out_rows = _fetch_cash_out(df, dt)

        self._tbl_in.load(in_rows)
        self._tbl_out.load(out_rows)

        total_in  = sum(r["amount"] for r in in_rows)
        total_out = sum(r["amount"] for r in out_rows)
        net       = total_in - total_out

        self._badge_in.configure( text=f"IN: Rs {total_in:,.0f}")
        self._badge_out.configure(text=f"OUT: Rs {total_out:,.0f}")
        self._net_in_lbl.configure( text=f"Cash In: Rs {total_in:,.0f}")
        self._net_out_lbl.configure(text=f"Cash Out: Rs {total_out:,.0f}")

        color = ACCENT_GREEN if net >= 0 else ACCENT_RED
        sign  = "+" if net >= 0 else ""
        self._net_lbl.configure(text=f"{sign}Rs {net:,.0f}", text_color=color)

    def _export_pdf(self):
        tab    = self._active_tab
        table  = self._tbl_in if tab == "in" else self._tbl_out
        rows   = table.get_rows()
        total  = table.get_total()

        if not rows:
            messagebox.showinfo("Export", "Koi data nahi mila export karne ke liye.")
            return

        label   = "Cash In" if tab == "in" else "Cash Out"
        df      = self._date_from.get().strip()
        dt      = self._date_to.get().strip()
        acc_cls = "green" if tab == "in" else "red"

        headers = ["#", "Date", "Source", "Reference", "Party / Category", "Description", "Amount (Rs)"]
        col_cls = ["center", "center", "", "", "", "", "right"]
        col_w   = [4, 10, 13, 10, 18, 28, 13]

        pdf_rows = []
        for idx, r in enumerate(rows, 1):
            pdf_rows.append([
                str(idx),
                r.get("date", "")[:10],
                r.get("source", ""),
                r.get("ref", ""),
                r.get("party", ""),
                r.get("description", ""),
                (f"Rs {r['amount']:,.0f}", acc_cls),
            ])

        totals_row = ["", "", "", "", "", "TOTAL",
                      (f"Rs {total:,.0f}", acc_cls + " bold")]

        shop_name = db.get_setting("shop_name", "Nexus POS")
        subtitle  = f"{shop_name}  |  Period: {df} to {dt}  |  Records: {len(rows)}"

        html = build_table_html(
            title=f"{label} Report",
            subtitle=subtitle,
            headers=headers,
            rows=pdf_rows,
            col_classes=col_cls,
            col_widths=col_w,
            orientation="landscape",
            totals_row=totals_row,
            footer_note=f"Total {label}: Rs {total:,.0f}",
        )

        default_name = f"cash_{tab}_{df}_to_{dt}.pdf"
        save_path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF Files", "*.pdf")],
            initialfile=default_name,
            title=f"Save {label} Report",
        )
        if not save_path:
            return

        ok, msg = export_html_to_pdf(html, save_path)
        if ok:
            messagebox.showinfo("Export Successful", msg)
        else:
            messagebox.showerror("Export Failed", msg)