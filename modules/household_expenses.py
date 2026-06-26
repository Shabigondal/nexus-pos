import os
import tkinter as tk
import tkinter.messagebox as messagebox
import tkinter.filedialog as filedialog
import customtkinter as ctk
import database.db_manager as db
from datetime import datetime, date

try:
    from tkcalendar import Calendar
    CALENDAR_OK = True
except ImportError:
    CALENDAR_OK = False

try:
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib import colors
    from reportlab.lib.units import mm
    from reportlab.platypus import (SimpleDocTemplate, Table, TableStyle,
                                    Paragraph, Spacer, HRFlowable)
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
    REPORTLAB_OK = True
except ImportError:
    REPORTLAB_OK = False

# ══════════════════════════════════════════════════════════════════════════════
# CATEGORIES
# ══════════════════════════════════════════════════════════════════════════════
CATEGORIES = [
    "🛒  Grocery",
    "💡  Utility Bills",
    "🏫  Education & School",
    "🏥  Health & Medicine",
    "🚗  Transport & Fuel",
    "🍽️  Food & Dining",
    "👗  Clothing & Apparel",
    "🏠  Home & Maintenance",
    "📱  Mobile & Internet",
    "🎉  Events & Occasions",
    "💰  Savings & Investment",
    "📦  Other",
]

CATEGORY_COLORS = {
    "🛒  Grocery":             ("#1c3a27", "#4aff8e"),
    "💡  Utility Bills":       ("#2a2a10", "#f0e060"),
    "🏫  Education & School":  ("#1a2a4a", "#4ab0ff"),
    "🏥  Health & Medicine":   ("#3a1a1a", "#ff6b6b"),
    "🚗  Transport & Fuel":    ("#2a1a3a", "#c97bff"),
    "🍽️  Food & Dining":       ("#2a1a10", "#ffaa50"),
    "👗  Clothing & Apparel":  ("#3a1a2a", "#ff70b0"),
    "🏠  Home & Maintenance":  ("#1a2a2a", "#5de0d0"),
    "📱  Mobile & Internet":   ("#1a1a3a", "#70aaff"),
    "🎉  Events & Occasions":  ("#2a1a2a", "#ff90e0"),
    "💰  Savings & Investment":("#1c3a1c", "#80ff80"),
    "📦  Other":               ("#222227", "#a0a0b0"),
}


# ══════════════════════════════════════════════════════════════════════════════
# CALENDAR PICKER HELPER
# ══════════════════════════════════════════════════════════════════════════════
def _open_calendar(parent, target_entry):
    if not CALENDAR_OK:
        messagebox.showwarning("Calendar", "tkcalendar install karein:\npip install tkcalendar")
        return
    popup = tk.Toplevel(parent)
    popup.title("Tarikh Chunein")
    popup.resizable(False, False)
    popup.transient(parent.winfo_toplevel())
    popup.grab_set()

    existing = target_entry.get().strip()
    kw = dict(selectmode="day", date_pattern="yyyy-mm-dd",
              background="#1f293d", foreground="white",
              headersbackground="#121214", normalbackground="#16161a",
              weekendbackground="#16161a", selectbackground="#4a90e2")
    if existing:
        try:
            y, m, d = [int(p) for p in existing.split("-")]
            kw.update(year=y, month=m, day=d)
        except Exception:
            pass

    cal = Calendar(popup, **kw)
    cal.pack(padx=10, pady=10)

    def _pick():
        target_entry.delete(0, "end")
        target_entry.insert(0, cal.get_date())
        popup.destroy()

    ctk.CTkButton(popup, text="✔  Select", height=30, command=_pick).pack(pady=(0, 10))


# ══════════════════════════════════════════════════════════════════════════════
# PDF EXPORT
# ══════════════════════════════════════════════════════════════════════════════
def export_expenses_pdf(rows, shop_name="Nexus POS", date_from=None, date_to=None):
    if not REPORTLAB_OK:
        messagebox.showerror("Error", "ReportLab library nahi mili.\npip install reportlab")
        return
    if not rows:
        messagebox.showwarning("No Data", "Export ke liye koi record nahi hai.")
        return

    path = filedialog.asksaveasfilename(
        defaultextension=".pdf",
        filetypes=[("PDF Files", "*.pdf")],
        title="PDF Save Karen",
        initialfile=f"Household_Expenses_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    )
    if not path:
        return

    try:
        doc = SimpleDocTemplate(
            path, pagesize=landscape(A4),
            leftMargin=15*mm, rightMargin=15*mm,
            topMargin=15*mm, bottomMargin=15*mm
        )
        styles = getSampleStyleSheet()

        def sty(name, **kw):
            return ParagraphStyle(name, parent=styles["Normal"], **kw)

        title_sty  = sty("t",  fontSize=18, fontName="Helvetica-Bold",
                         textColor=colors.HexColor("#1a3a5c"), alignment=TA_CENTER, spaceAfter=3)
        sub_sty    = sty("s",  fontSize=10, fontName="Helvetica",
                         textColor=colors.HexColor("#555555"), alignment=TA_CENTER, spaceAfter=2)
        cell_l     = sty("cl", fontSize=8.5, fontName="Helvetica", alignment=TA_LEFT)
        cell_c     = sty("cc", fontSize=8.5, fontName="Helvetica", alignment=TA_CENTER)
        cell_r     = sty("cr", fontSize=8.5, fontName="Helvetica", alignment=TA_RIGHT)

        elems = []
        date_range_str = ""
        if date_from and date_to:
            date_range_str = f"  |  Period: {date_from}  to  {date_to}"
        elif date_from:
            date_range_str = f"  |  From: {date_from}"
        elif date_to:
            date_range_str = f"  |  To: {date_to}"

        elems.append(Paragraph(shop_name, title_sty))
        elems.append(Paragraph("Household Expenses Report", sub_sty))
        elems.append(Paragraph(
            f"Generated: {datetime.now().strftime('%d %B %Y  %I:%M %p')}"
            f"  |  Total Records: {len(rows)}{date_range_str}",
            sub_sty
        ))
        elems.append(Spacer(1, 4*mm))
        elems.append(HRFlowable(width="100%", thickness=1.5,
                                color=colors.HexColor("#1a3a5c"), spaceAfter=4*mm))

        # Table
        col_hdrs   = ["#", "ID", "Category", "Description", "Amount (Rs)", "Date", "Added On"]
        col_widths = [10*mm, 18*mm, 48*mm, 100*mm, 36*mm, 30*mm, 35*mm]

        hdr_row = [Paragraph(f"<b>{h}</b>", cell_c) for h in col_hdrs]
        tdata = [hdr_row]

        grand = 0.0
        for idx, row in enumerate(rows):
            exp_id, cat, desc, amount, exp_date, created_at = row
            grand += amount or 0
            cat_clean = cat.split("  ", 1)[-1] if "  " in cat else cat
            desc_short = (desc[:60] + "…") if desc and len(desc) > 60 else (desc or "—")
            date_str = exp_date[:10] if exp_date else "—"
            created_str = created_at[:10] if created_at else "—"

            tdata.append([
                Paragraph(str(idx + 1), cell_c),
                Paragraph(f"HE-{exp_id:04d}", cell_c),
                Paragraph(cat_clean, cell_l),
                Paragraph(desc_short, cell_l),
                Paragraph(f"{amount:,.2f}" if amount else "0.00", cell_r),
                Paragraph(date_str, cell_c),
                Paragraph(created_str, cell_c),
            ])

        # Grand total row
        bold_r = sty("br", fontSize=9, fontName="Helvetica-Bold", alignment=TA_RIGHT)
        bold_l = sty("bl", fontSize=9, fontName="Helvetica-Bold", alignment=TA_LEFT)
        tdata.append([
            Paragraph("", cell_c),
            Paragraph("", cell_c),
            Paragraph("", cell_c),
            Paragraph("<b>GRAND TOTAL</b>", bold_l),
            Paragraph(f"<b>Rs {grand:,.2f}</b>", bold_r),
            Paragraph("", cell_c),
            Paragraph("", cell_c),
        ])

        tbl = Table(tdata, colWidths=col_widths, repeatRows=1)
        tbl.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, 0), colors.HexColor("#1a3a5c")),
            ("TEXTCOLOR",     (0, 0), (-1, 0), colors.white),
            ("FONTNAME",      (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE",      (0, 0), (-1, 0), 9),
            ("ROWBACKGROUNDS",(0, 1), (-1, -2), [colors.HexColor("#f0f4f8"), colors.white]),
            ("BACKGROUND",    (0, -1), (-1, -1), colors.HexColor("#d6e8f5")),
            ("FONTNAME",      (0, -1), (-1, -1), "Helvetica-Bold"),
            ("LINEABOVE",     (0, -1), (-1, -1), 1.2, colors.HexColor("#1a3a5c")),
            ("GRID",          (0, 0), (-1, -1), 0.4, colors.HexColor("#c0ccd8")),
            ("LINEBELOW",     (0, 0), (-1, 0),  1.2, colors.HexColor("#0e2540")),
            ("TOPPADDING",    (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING",   (0, 0), (-1, -1), 5),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 5),
            ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ]))
        elems.append(tbl)
        elems.append(Spacer(1, 6*mm))
        elems.append(HRFlowable(width="100%", thickness=0.5,
                                color=colors.HexColor("#aaaaaa"), spaceBefore=2*mm))
        elems.append(Paragraph(
            f"Total Household Expenses: <b>Rs {grand:,.2f}</b>",
            sty("ft", fontSize=10, fontName="Helvetica-Bold",
                textColor=colors.HexColor("#1a3a5c"),
                alignment=TA_RIGHT, spaceBefore=3*mm)
        ))

        doc.build(elems)
        messagebox.showinfo("PDF Ready", f"PDF save ho gaya:\n{path}")
        try:
            os.startfile(path)
        except Exception:
            pass

    except Exception as e:
        messagebox.showerror("PDF Error", f"PDF generate nahi hui:\n{e}")


# ══════════════════════════════════════════════════════════════════════════════
# MAIN VIEW
# ══════════════════════════════════════════════════════════════════════════════
class HouseholdExpensesView(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")

        self.current_page       = 0
        self.items_per_page     = 12
        self.cached_rows        = []
        self._date_filter_active = False

        db.init_household_expense_tables()

        # ── TOP BAR ──────────────────────────────────────────────────────────
        top_bar = ctk.CTkFrame(self, fg_color="transparent")
        top_bar.pack(fill="x", padx=20, pady=(10, 6))

        self.search_entry = ctk.CTkEntry(
            top_bar,
            placeholder_text="🔍  Category ya description se search karein...",
            height=40, fg_color="#16161a", border_color="#222227", corner_radius=6
        )
        self.search_entry.pack(side="left", fill="x", expand=True, padx=(0, 12))
        self.search_entry.bind("<KeyRelease>", self._on_search)

        ctk.CTkButton(
            top_bar, text="📄  Export PDF", height=40, width=140,
            fg_color="#1c3a27", hover_color="#2a5a3b", text_color="#4aff8e",
            border_color="#2d5a3b", border_width=1,
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            corner_radius=6, command=self._export_pdf
        ).pack(side="right", padx=(6, 0))

        ctk.CTkButton(
            top_bar, text="＋  Add Expense", height=40, width=148,
            fg_color="#1f293d", hover_color="#2d3d5a",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            corner_radius=6, command=self._open_add_modal
        ).pack(side="right")

        # ── DATE FILTER BAR ───────────────────────────────────────────────────
        date_bar = ctk.CTkFrame(self, fg_color="transparent")
        date_bar.pack(fill="x", padx=20, pady=(0, 8))

        ctk.CTkLabel(date_bar, text="From:",
                     font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
                     text_color="#a0a0b0").pack(side="left", padx=(0, 5))

        self.ent_from = ctk.CTkEntry(date_bar, placeholder_text="YYYY-MM-DD",
                                     width=118, height=32,
                                     fg_color="#16161a", border_color="#222227", corner_radius=6)
        self.ent_from.pack(side="left", padx=(0, 4))
        ctk.CTkButton(date_bar, text="📅", width=32, height=32,
                      fg_color="#16161a", hover_color="#1f1f24", border_color="#222227", border_width=1,
                      corner_radius=6, command=lambda: _open_calendar(self, self.ent_from)
                      ).pack(side="left", padx=(0, 14))

        ctk.CTkLabel(date_bar, text="To:",
                     font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
                     text_color="#a0a0b0").pack(side="left", padx=(0, 5))

        self.ent_to = ctk.CTkEntry(date_bar, placeholder_text="YYYY-MM-DD",
                                   width=118, height=32,
                                   fg_color="#16161a", border_color="#222227", corner_radius=6)
        self.ent_to.pack(side="left", padx=(0, 4))
        ctk.CTkButton(date_bar, text="📅", width=32, height=32,
                      fg_color="#16161a", hover_color="#1f1f24", border_color="#222227", border_width=1,
                      corner_radius=6, command=lambda: _open_calendar(self, self.ent_to)
                      ).pack(side="left", padx=(0, 10))

        ctk.CTkButton(date_bar, text="🔎  Filter", height=32, width=100,
                      fg_color="#1f293d", hover_color="#2d3d5a",
                      font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
                      corner_radius=6, command=self._apply_date_filter
                      ).pack(side="left", padx=(0, 6))

        ctk.CTkButton(date_bar, text="✖  Clear", height=32, width=88,
                      fg_color="#2a2a32", hover_color="#3a3a42",
                      font=ctk.CTkFont(family="Segoe UI", size=12),
                      corner_radius=6, command=self._clear_date_filter
                      ).pack(side="left")

        # ── SUMMARY STRIP ─────────────────────────────────────────────────────
        self.summary_strip = ctk.CTkFrame(self, fg_color="#0f0f12",
                                          border_color="#222227", border_width=1,
                                          corner_radius=6, height=42)
        self.summary_strip.pack(fill="x", padx=20, pady=(0, 6))
        self.summary_strip.pack_propagate(False)
        self.lbl_total_records = ctk.CTkLabel(
            self.summary_strip, text="Total: 0 records  |  Amount: Rs 0.00",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color="#4aff8e"
        )
        self.lbl_total_records.pack(side="left", padx=16, pady=10)

        # ── GRID ──────────────────────────────────────────────────────────────
        self.grid_container = ctk.CTkScrollableFrame(
            self, fg_color="#121214", border_color="#222227",
            border_width=1, corner_radius=6
        )
        self.grid_container.pack(fill="both", expand=True, padx=20, pady=(0, 5))

        # ── PAGINATOR ─────────────────────────────────────────────────────────
        pag = ctk.CTkFrame(self, fg_color="transparent", height=40)
        pag.pack(fill="x", padx=20, pady=(8, 14))

        self.btn_prev = ctk.CTkButton(
            pag, text="⬅  Previous", width=120, height=32,
            fg_color="#16161a", border_color="#222227", border_width=1,
            hover_color="#1f1f24", font=ctk.CTkFont(size=12, weight="bold"),
            command=self._prev_page
        )
        self.btn_prev.pack(side="left")

        self.lbl_page = ctk.CTkLabel(pag, text="Page 1 of 1",
                                     font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
                                     text_color="gray")
        self.lbl_page.pack(side="left", expand=True)

        self.btn_next = ctk.CTkButton(
            pag, text="Next  ➡", width=120, height=32,
            fg_color="#16161a", border_color="#222227", border_width=1,
            hover_color="#1f1f24", font=ctk.CTkFont(size=12, weight="bold"),
            command=self._next_page
        )
        self.btn_next.pack(side="right")

        self.refresh_grid()

    # ── PAGINATION ────────────────────────────────────────────────────────────
    def _prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self._render_rows()

    def _next_page(self):
        max_p = max(1, (len(self.cached_rows) + self.items_per_page - 1) // self.items_per_page)
        if self.current_page + 1 < max_p:
            self.current_page += 1
            self._render_rows()

    # ── FILTER ────────────────────────────────────────────────────────────────
    def _apply_date_filter(self):
        self._date_filter_active = True
        self.current_page = 0
        self.refresh_grid(self.search_entry.get().strip())

    def _clear_date_filter(self):
        self.ent_from.delete(0, "end")
        self.ent_to.delete(0, "end")
        self._date_filter_active = False
        self.current_page = 0
        self.refresh_grid(self.search_entry.get().strip())

    def _on_search(self, event=None):
        self.current_page = 0
        self.refresh_grid(self.search_entry.get().strip())

    # ── PDF ───────────────────────────────────────────────────────────────────
    def _export_pdf(self):
        try:
            shop = db.get_setting("shop_name", "Nexus POS")
        except Exception:
            shop = "Nexus POS"
        df = self.ent_from.get().strip() if self._date_filter_active else None
        dt = self.ent_to.get().strip()   if self._date_filter_active else None
        export_expenses_pdf(self.cached_rows, shop_name=shop, date_from=df, date_to=dt)

    # ── DATA ──────────────────────────────────────────────────────────────────
    def refresh_grid(self, search_text=""):
        df = self.ent_from.get().strip() if self._date_filter_active else None
        dt = self.ent_to.get().strip()   if self._date_filter_active else None
        self.cached_rows = db.get_all_household_expenses(search_text, df, dt)
        self._render_rows()

    # ── RENDER ────────────────────────────────────────────────────────────────
    def _render_rows(self):
        for w in self.grid_container.winfo_children():
            w.destroy()

        total     = len(self.cached_rows)
        max_pages = max(1, (total + self.items_per_page - 1) // self.items_per_page)
        if self.current_page >= max_pages:
            self.current_page = max_pages - 1

        self.lbl_page.configure(text=f"Page {self.current_page + 1} of {max_pages}")
        self.btn_prev.configure(state="normal" if self.current_page > 0 else "disabled")
        self.btn_next.configure(
            state="normal" if (self.current_page + 1) < max_pages else "disabled")

        # Summary
        grand = sum((r[3] or 0) for r in self.cached_rows)
        self.lbl_total_records.configure(
            text=f"Total: {total} record{'s' if total != 1 else ''}  |  Amount: Rs {grand:,.2f}"
        )

        start = self.current_page * self.items_per_page
        chunk = self.cached_rows[start: start + self.items_per_page]

        # ── COLUMN CONFIG ─────────────────────────────────────────────────────
        cols = [
            ("#",           38,  "center"),
            ("ID",          68,  "center"),
            ("Category",   158,  "w"),
            ("Description",320,  "w"),
            ("Amount",     110,  "center"),
            ("Date",       105,  "center"),
            ("Actions",    110,  "center"),
        ]

        # Header
        hdr = ctk.CTkFrame(self.grid_container, fg_color="#16161a", corner_radius=4, height=36)
        hdr.pack(fill="x", pady=(0, 6))
        hdr.pack_propagate(False)

        ctk.CTkLabel(hdr, text="Actions", width=112, anchor="center",
                     font=ctk.CTkFont(size=11, weight="bold"),
                     text_color="#4a90e2").pack(side="right", padx=8)

        for label, w, anc in cols[:-1]:
            ctk.CTkLabel(hdr, text=label, width=w, anchor=anc,
                         font=ctk.CTkFont(size=11, weight="bold"),
                         text_color="#4a90e2").pack(side="left", padx=3)

        if not chunk:
            ctk.CTkLabel(
                self.grid_container,
                text="Koi record nahi mila. '＋ Add Expense' se naya entry karein.",
                text_color="#555560", font=ctk.CTkFont(size=12)
            ).pack(pady=50)
            return

        for idx, row in enumerate(chunk):
            exp_id, cat, desc, amount, exp_date, created_at = row
            global_idx = start + idx

            bg = "#18181f" if global_idx % 2 == 0 else "transparent"
            rf = ctk.CTkFrame(self.grid_container, fg_color=bg, height=44, corner_radius=4)
            rf.pack(fill="x", pady=2)
            rf.pack_propagate(False)

            # Actions (pack right first)
            act_f = ctk.CTkFrame(rf, fg_color="transparent", width=112)
            act_f.pack(side="right", padx=8, pady=6)
            act_f.pack_propagate(False)

            ctk.CTkButton(
                act_f, text="✏", width=42, height=28, corner_radius=4,
                fg_color="#1f2d4a", hover_color="#2a3d60",
                font=ctk.CTkFont(size=13),
                command=lambda r=row: self._open_edit_modal(r)
            ).pack(side="left", padx=(0, 4))

            ctk.CTkButton(
                act_f, text="🗑", width=42, height=28, corner_radius=4,
                fg_color="#3a1a1a", hover_color="#5a2020",
                font=ctk.CTkFont(size=13),
                command=lambda eid=exp_id: self._delete_expense(eid)
            ).pack(side="left")

            # S.No
            ctk.CTkLabel(rf, text=str(global_idx + 1), width=38, anchor="center",
                         font=ctk.CTkFont(size=11), text_color="#a0a0a9"
                         ).pack(side="left", padx=3)

            # ID badge
            ctk.CTkLabel(rf, text=f"HE-{exp_id:04d}", width=68, anchor="center",
                         font=ctk.CTkFont(family="Consolas", size=10, weight="bold"),
                         text_color="#6090d0"
                         ).pack(side="left", padx=3)

            # Category badge
            bg_c, fg_c = CATEGORY_COLORS.get(cat, ("#222227", "#a0a0b0"))
            badge_outer = ctk.CTkFrame(rf, fg_color="transparent", width=158)
            badge_outer.pack(side="left", padx=3, pady=6)
            badge_outer.pack_propagate(False)
            badge = ctk.CTkFrame(badge_outer, fg_color=bg_c, corner_radius=4, height=26)
            badge.pack(fill="x", padx=2)
            badge.pack_propagate(False)
            cat_short = cat.split("  ", 1)[-1] if "  " in cat else cat
            ctk.CTkLabel(badge, text=cat_short, text_color=fg_c,
                         font=ctk.CTkFont(size=10, weight="bold"),
                         anchor="w").pack(side="left", padx=6, expand=True)

            # Description
            desc_disp = (desc[:42] + "…") if desc and len(desc) > 42 else (desc or "—")
            ctk.CTkLabel(rf, text=desc_disp, width=320, anchor="w",
                         font=ctk.CTkFont(size=11), text_color="#c0c0cc"
                         ).pack(side="left", padx=3)

            # Amount
            ctk.CTkLabel(rf, text=f"Rs {amount:,.2f}" if amount else "—",
                         width=110, anchor="center",
                         font=ctk.CTkFont(size=11, weight="bold"), text_color="#4aff8e"
                         ).pack(side="left", padx=3)

            # Date
            date_disp = exp_date[:10] if exp_date else "—"
            ctk.CTkLabel(rf, text=date_disp, width=105, anchor="center",
                         font=ctk.CTkFont(size=11), text_color="#a0a0a9"
                         ).pack(side="left", padx=3)

    # ══════════════════════════════════════════════════════════════════════════
    # ADD / EDIT MODAL
    # ══════════════════════════════════════════════════════════════════════════
    def _open_add_modal(self):
        self._expense_modal()

    def _open_edit_modal(self, row):
        self._expense_modal(row=row)

    def _expense_modal(self, row=None):
        is_edit = row is not None
        if is_edit:
            exp_id, cat, desc, amount, exp_date, _ = row

        modal = ctk.CTkToplevel(self)
        modal.title("Expense Edit Karen" if is_edit else "Naya Expense Add Karen")
        modal.geometry("520x580")
        modal.resizable(False, False)
        modal.grab_set()
        modal.focus_force()

        sw, sh = modal.winfo_screenwidth(), modal.winfo_screenheight()
        modal.geometry(f"520x580+{(sw - 520)//2}+{(sh - 580)//2}")

        # Header
        hdr = ctk.CTkFrame(modal, fg_color="#16161a", corner_radius=0, height=54)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        ctk.CTkLabel(
            hdr,
            text=f"✏  Expense Edit — HE-{exp_id:04d}" if is_edit else "＋  Naya Household Expense",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color="#4a90e2"
        ).pack(anchor="w", padx=20, pady=14)

        # Body
        body = ctk.CTkScrollableFrame(modal, fg_color="#0f0f12",
                                      border_color="#222227", border_width=0)
        body.pack(fill="both", expand=True, padx=16, pady=(10, 0))

        def lbl(text):
            ctk.CTkLabel(body, text=text,
                         font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
                         text_color="#6080a0", anchor="w"
                         ).pack(fill="x", pady=(10, 2))

        # Category
        lbl("Category  *")
        cat_var = ctk.StringVar(value=cat if is_edit else CATEGORIES[0])
        ctk.CTkOptionMenu(
            body, variable=cat_var, values=CATEGORIES,
            height=36, fg_color="#16161a", button_color="#1f293d",
            button_hover_color="#2d3d5a", dropdown_fg_color="#16161a",
            font=ctk.CTkFont(size=12), corner_radius=6
        ).pack(fill="x")

        # Description
        lbl("Description  (detail likhen — kia kia liya, kahan se, etc.)")
        ent_desc = ctk.CTkTextbox(body, height=110, fg_color="#16161a",
                                  border_color="#2a2a32", border_width=1, corner_radius=6,
                                  font=ctk.CTkFont(size=12))
        ent_desc.pack(fill="x")
        if is_edit and desc:
            ent_desc.insert("1.0", desc)

        # Amount
        lbl("Total Amount  (Rs)  *")
        ent_amount = ctk.CTkEntry(body, height=36, fg_color="#16161a",
                                  border_color="#2a2a32", border_width=1, corner_radius=6,
                                  font=ctk.CTkFont(size=12),
                                  placeholder_text="Jaise: 2500")
        ent_amount.pack(fill="x")
        if is_edit and amount is not None:
            ent_amount.insert(0, str(amount))

        # Date
        lbl("Expense Date  *")
        date_row = ctk.CTkFrame(body, fg_color="transparent")
        date_row.pack(fill="x")
        ent_date = ctk.CTkEntry(date_row, height=36, fg_color="#16161a",
                                border_color="#2a2a32", border_width=1, corner_radius=6,
                                font=ctk.CTkFont(size=12), placeholder_text="YYYY-MM-DD")
        ent_date.pack(side="left", fill="x", expand=True, padx=(0, 6))
        if is_edit and exp_date:
            ent_date.insert(0, exp_date[:10])
        else:
            ent_date.insert(0, date.today().strftime("%Y-%m-%d"))

        ctk.CTkButton(
            date_row, text="📅", width=36, height=36,
            fg_color="#16161a", hover_color="#1f1f24",
            border_color="#2a2a32", border_width=1, corner_radius=6,
            command=lambda: _open_calendar(modal, ent_date)
        ).pack(side="left")

        # Footer
        foot = ctk.CTkFrame(modal, fg_color="#16161a", corner_radius=0, height=62)
        foot.pack(fill="x", side="bottom")
        foot.pack_propagate(False)

        def _save():
            category   = cat_var.get().strip()
            description = ent_desc.get("1.0", "end").strip()
            amt_s      = ent_amount.get().strip()
            exp_date_s = ent_date.get().strip()

            if not category:
                messagebox.showerror("Validation", "Category zaroori hai!", parent=modal); return
            try:
                amt = float(amt_s)
                if amt <= 0: raise ValueError
            except ValueError:
                messagebox.showerror("Validation", "Amount valid number hona chahiye (> 0)!", parent=modal); return
            if not exp_date_s:
                messagebox.showerror("Validation", "Date zaroori hai!", parent=modal); return
            try:
                datetime.strptime(exp_date_s, "%Y-%m-%d")
            except ValueError:
                messagebox.showerror("Validation", "Date format YYYY-MM-DD hona chahiye!", parent=modal); return

            if is_edit:
                db.update_household_expense(exp_id, category, description, amt, exp_date_s)
                messagebox.showinfo("Updated", "Expense update ho gaya!", parent=modal)
            else:
                db.add_household_expense(category, description, amt, exp_date_s)
                messagebox.showinfo("Added", "Expense add ho gaya!", parent=modal)

            modal.destroy()
            self.refresh_grid(self.search_entry.get().strip())

        ctk.CTkButton(
            foot, text="Cancel", height=40, width=90, corner_radius=6,
            fg_color="#2a2a32", hover_color="#3a3a42", font=ctk.CTkFont(size=13),
            command=modal.destroy
        ).pack(side="left", padx=18, pady=11)

        ctk.CTkButton(
            foot,
            text="💾  Save Changes" if is_edit else "✅  Add Expense",
            height=40, corner_radius=6,
            fg_color="#1f3a4a", hover_color="#2a5268",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            command=_save
        ).pack(side="right", padx=18, pady=11)

    # ══════════════════════════════════════════════════════════════════════════
    # DELETE
    # ══════════════════════════════════════════════════════════════════════════
    def _delete_expense(self, exp_id):
        confirm = messagebox.askyesno(
            "Delete Confirm",
            f"HE-{exp_id:04d} delete karna chahte hain?\nYeh action wapas nahi hoga.",
        )
        if confirm:
            db.delete_household_expense(exp_id)
            self.refresh_grid(self.search_entry.get().strip())
