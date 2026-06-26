import os
import customtkinter as ctk
import database.db_manager as db
import tkinter.messagebox as messagebox
import tkinter.filedialog as filedialog
from datetime import datetime

# ─── PDF Export ───────────────────────────────────────────────────────────────
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

UNITS = ["Liter", "KG", "Piece", "Pack", "Ton", "Gallon", "Drum", "Bag", "Box", "Other"]


# ══════════════════════════════════════════════════════════════════════════════
# PDF EXPORT FUNCTION
# ══════════════════════════════════════════════════════════════════════════════
def export_dealers_pdf(dealers, shop_name="Nexus POS"):
    if not REPORTLAB_OK:
        messagebox.showerror("Error", "ReportLab library nahi mili. PDF export ke liye:\npip install reportlab")
        return

    path = filedialog.asksaveasfilename(
        defaultextension=".pdf",
        filetypes=[("PDF Files", "*.pdf")],
        title="PDF Save Karen",
        initialfile=f"Dealers_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    )
    if not path:
        return

    try:
        doc = SimpleDocTemplate(
            path,
            pagesize=landscape(A4),
            leftMargin=15*mm, rightMargin=15*mm,
            topMargin=15*mm, bottomMargin=15*mm
        )

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle("title", parent=styles["Normal"],
                                     fontSize=18, fontName="Helvetica-Bold",
                                     textColor=colors.HexColor("#1a3a5c"),
                                     alignment=TA_CENTER, spaceAfter=4)
        sub_style = ParagraphStyle("sub", parent=styles["Normal"],
                                   fontSize=10, fontName="Helvetica",
                                   textColor=colors.HexColor("#555555"),
                                   alignment=TA_CENTER, spaceAfter=2)
        cell_style = ParagraphStyle("cell", parent=styles["Normal"],
                                    fontSize=8.5, fontName="Helvetica",
                                    alignment=TA_LEFT)
        cell_center = ParagraphStyle("cellc", parent=styles["Normal"],
                                     fontSize=8.5, fontName="Helvetica",
                                     alignment=TA_CENTER)
        cell_right = ParagraphStyle("cellr", parent=styles["Normal"],
                                    fontSize=8.5, fontName="Helvetica",
                                    alignment=TA_RIGHT)

        elements = []

        # ── Header ─────────────────────────────────────────────
        elements.append(Paragraph(shop_name, title_style))
        elements.append(Paragraph("Dealer Management Report", sub_style))
        elements.append(Paragraph(
            f"Generated: {datetime.now().strftime('%d %B %Y  %I:%M %p')}  |  Total Dealers: {len(dealers)}",
            sub_style
        ))
        elements.append(Spacer(1, 4*mm))
        elements.append(HRFlowable(width="100%", thickness=1.5,
                                   color=colors.HexColor("#1a3a5c"), spaceAfter=4*mm))

        # ── Table ───────────────────────────────────────────────
        col_headers = ["#", "Dealer Name", "Contact", "Item", "Unit",
                       "Qty", "Total Cost (Rs)", "Per Item (Rs)", "Date Added"]
        # Widths in mm for landscape A4 (usable ~267mm)
        col_widths = [10*mm, 52*mm, 35*mm, 42*mm, 22*mm,
                      18*mm, 38*mm, 38*mm, 32*mm]

        hdr_row = [Paragraph(f"<b>{h}</b>", cell_center) for h in col_headers]
        table_data = [hdr_row]

        grand_total = 0.0
        for idx, row in enumerate(dealers):
            d_id, d_name, d_contact, item_name, unit, qty, total_cost, per_item, date_added, _ = row
            grand_total += total_cost or 0

            qty_str  = str(int(qty)) if qty and float(qty) == int(qty) else f"{qty:g}" if qty else "0"
            date_str = date_added[:10] if date_added else "—"
            bg = colors.HexColor("#f0f4f8") if idx % 2 == 0 else colors.white

            table_data.append([
                Paragraph(str(idx + 1), cell_center),
                Paragraph(d_name or "—", cell_style),
                Paragraph(d_contact or "—", cell_center),
                Paragraph(item_name or "—", cell_style),
                Paragraph(unit or "—", cell_center),
                Paragraph(qty_str, cell_center),
                Paragraph(f"{total_cost:,.2f}" if total_cost else "0.00", cell_right),
                Paragraph(f"{per_item:,.4f}" if per_item else "0.00", cell_right),
                Paragraph(date_str, cell_center),
            ])

        # Grand total row
        table_data.append([
            Paragraph("", cell_center),
            Paragraph("<b>GRAND TOTAL</b>", ParagraphStyle("gt", parent=styles["Normal"],
                      fontSize=9, fontName="Helvetica-Bold", alignment=TA_LEFT)),
            Paragraph("", cell_center),
            Paragraph("", cell_center),
            Paragraph("", cell_center),
            Paragraph("", cell_center),
            Paragraph(f"<b>Rs {grand_total:,.2f}</b>",
                      ParagraphStyle("gtr", parent=styles["Normal"],
                      fontSize=9, fontName="Helvetica-Bold", alignment=TA_RIGHT)),
            Paragraph("", cell_center),
            Paragraph("", cell_center),
        ])

        tbl = Table(table_data, colWidths=col_widths, repeatRows=1)

        # Base style
        ts = TableStyle([
            # Header
            ("BACKGROUND",   (0, 0), (-1, 0), colors.HexColor("#1a3a5c")),
            ("TEXTCOLOR",    (0, 0), (-1, 0), colors.white),
            ("FONTNAME",     (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE",     (0, 0), (-1, 0), 9),
            ("ROWBACKGROUNDS", (0, 1), (-1, -2),
             [colors.HexColor("#f0f4f8"), colors.white]),
            # Grand total row
            ("BACKGROUND",   (0, -1), (-1, -1), colors.HexColor("#d6e8f5")),
            ("FONTNAME",     (0, -1), (-1, -1), "Helvetica-Bold"),
            ("LINEABOVE",    (0, -1), (-1, -1), 1.2, colors.HexColor("#1a3a5c")),
            # Grid
            ("GRID",         (0, 0), (-1, -1), 0.4, colors.HexColor("#c0ccd8")),
            ("LINEBELOW",    (0, 0), (-1, 0),  1.2, colors.HexColor("#0e2540")),
            # Padding
            ("TOPPADDING",   (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING",(0, 0), (-1, -1), 4),
            ("LEFTPADDING",  (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
            ("VALIGN",       (0, 0), (-1, -1), "MIDDLE"),
        ])
        tbl.setStyle(ts)
        elements.append(tbl)

        # Footer note
        elements.append(Spacer(1, 6*mm))
        elements.append(HRFlowable(width="100%", thickness=0.5,
                                   color=colors.HexColor("#aaaaaa"), spaceBefore=2*mm))
        elements.append(Paragraph(
            f"Total Amount Paid to Dealers: <b>Rs {grand_total:,.2f}</b>",
            ParagraphStyle("footer", parent=styles["Normal"],
                           fontSize=10, fontName="Helvetica-Bold",
                           textColor=colors.HexColor("#1a3a5c"),
                           alignment=TA_RIGHT, spaceBefore=3*mm)
        ))

        doc.build(elements)
        messagebox.showinfo("PDF Ready", f"PDF successfully save ho gaya:\n{path}")
        # Auto-open
        try:
            os.startfile(path)
        except Exception:
            pass

    except Exception as e:
        messagebox.showerror("PDF Error", f"PDF generate nahi hui:\n{e}")


# ══════════════════════════════════════════════════════════════════════════════
# MAIN VIEW
# ══════════════════════════════════════════════════════════════════════════════
class DealerView(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")

        self.current_page    = 0
        self.items_per_page  = 10
        self.cached_dealers  = []

        # ── TOP BAR ───────────────────────────────────────────────────────────
        top_bar = ctk.CTkFrame(self, fg_color="transparent")
        top_bar.pack(fill="x", padx=20, pady=(10, 12))

        self.search_entry = ctk.CTkEntry(
            top_bar,
            placeholder_text="🔍  Search by dealer name, item, or contact...",
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
            top_bar, text="＋  Add Dealer", height=40, width=145,
            fg_color="#1f293d", hover_color="#2d3d5a",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            corner_radius=6, command=self.open_add_modal
        ).pack(side="right")

        # ── GRID CONTAINER ────────────────────────────────────────────────────
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

        self.lbl_page = ctk.CTkLabel(
            pag, text="Page 1 of 1",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color="gray"
        )
        self.lbl_page.pack(side="left", expand=True)

        self.btn_next = ctk.CTkButton(
            pag, text="Next  ➡", width=120, height=32,
            fg_color="#16161a", border_color="#222227", border_width=1,
            hover_color="#1f1f24", font=ctk.CTkFont(size=12, weight="bold"),
            command=self._next_page
        )
        self.btn_next.pack(side="right")

        self.refresh_grid()

    # ── PDF ───────────────────────────────────────────────────────────────────
    def _export_pdf(self):
        if not self.cached_dealers:
            messagebox.showwarning("No Data", "Export karne ke liye pehle koi dealer add karen.")
            return
        try:
            shop = db.get_setting("shop_name", "Nexus POS")
        except Exception:
            shop = "Nexus POS"
        export_dealers_pdf(self.cached_dealers, shop_name=shop)

    # ── DATA ──────────────────────────────────────────────────────────────────
    def refresh_grid(self, search_text=""):
        self.cached_dealers = db.get_all_dealers(search_text)
        self._render_rows()

    def _on_search(self, event=None):
        self.current_page = 0
        self.refresh_grid(self.search_entry.get().strip())

    # ── RENDER ────────────────────────────────────────────────────────────────
    def _render_rows(self):
        for w in self.grid_container.winfo_children():
            w.destroy()

        total     = len(self.cached_dealers)
        max_pages = max(1, (total + self.items_per_page - 1) // self.items_per_page)
        if self.current_page >= max_pages:
            self.current_page = max_pages - 1

        self.lbl_page.configure(text=f"Page {self.current_page + 1} of {max_pages}")
        self.btn_prev.configure(state="normal" if self.current_page > 0 else "disabled")
        self.btn_next.configure(
            state="normal" if (self.current_page + 1) < max_pages else "disabled"
        )

        start = self.current_page * self.items_per_page
        chunk = self.cached_dealers[start: start + self.items_per_page]

        # ── COLUMN CONFIG ─────────────────────────────────────────────────────
        # S.No | Dealer Name | Contact | Item Name | Unit | Qty | Total | Per Item | Date | Actions
        cols = [
            ("#",           38,  "center"),
            ("Dealer Name", 155, "w"),
            ("Contact",     105, "center"),
            ("Item Name",   140, "w"),
            ("Unit",         72, "center"),
            ("Qty",          58, "center"),
            ("Total Cost",  110, "center"),
            ("Per Item",    100, "center"),
            ("Date Added",  110, "center"),
            ("Actions",     110, "center"),
        ]
        widths = [c[1] for c in cols]

        # Header row
        hdr = ctk.CTkFrame(self.grid_container, fg_color="#16161a",
                           corner_radius=4, height=36)
        hdr.pack(fill="x", pady=(0, 6))
        hdr.pack_propagate(False)
        for label, w, anc in cols:
            ctk.CTkLabel(
                hdr, text=label, width=w, anchor=anc,
                font=ctk.CTkFont(size=11, weight="bold"), text_color="#4a90e2"
            ).pack(side="left", padx=3)

        # Empty state
        if not chunk:
            ctk.CTkLabel(
                self.grid_container,
                text="No dealers found. Click '＋ Add Dealer' to get started.",
                text_color="#555560", font=ctk.CTkFont(size=13)
            ).pack(pady=60)
            return

        for idx, row in enumerate(chunk):
            d_id, d_name, d_contact, item_name, unit, qty, total_cost, per_item, date_added, _ = row
            sno      = start + idx + 1
            qty_str  = str(int(qty)) if qty and float(qty) == int(qty) else f"{qty:g}" if qty else "0"
            con_str  = d_contact if d_contact else "—"
            date_str = date_added[:10] if date_added else "—"
            unit_str = unit if unit else "—"

            rf = ctk.CTkFrame(
                self.grid_container,
                fg_color="#18181f" if idx % 2 == 0 else "transparent",
                height=46, corner_radius=4
            )
            rf.pack(fill="x", pady=2)
            rf.pack_propagate(False)

            ctk.CTkLabel(rf, text=str(sno),         width=widths[0], anchor="center", text_color="gray").pack(side="left", padx=3)
            ctk.CTkLabel(rf, text=d_name,            width=widths[1], anchor="w",      text_color="#ffffff", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=3)
            ctk.CTkLabel(rf, text=con_str,           width=widths[2], anchor="center", text_color="#a0a0a9").pack(side="left", padx=3)
            ctk.CTkLabel(rf, text=item_name,         width=widths[3], anchor="w",      text_color="#8ed1fc").pack(side="left", padx=3)
            ctk.CTkLabel(rf, text=unit_str,          width=widths[4], anchor="center", text_color="#c792ea").pack(side="left", padx=3)
            ctk.CTkLabel(rf, text=qty_str,           width=widths[5], anchor="center", text_color="#ffffff").pack(side="left", padx=3)
            ctk.CTkLabel(rf, text=f"Rs {total_cost:,.2f}", width=widths[6], anchor="center", text_color="#f0ad4e").pack(side="left", padx=3)
            ctk.CTkLabel(rf, text=f"Rs {per_item:,.2f}",  width=widths[7], anchor="center", text_color="#4aff8e").pack(side="left", padx=3)
            ctk.CTkLabel(rf, text=date_str,          width=widths[8], anchor="center", text_color="#a0a0a9").pack(side="left", padx=3)

            # ── ACTION BUTTONS (fixed right side) ─────────────────────────────
            act = ctk.CTkFrame(rf, fg_color="transparent")
            act.pack(side="right", padx=6)

            ctk.CTkButton(
                act, text="📋", width=32, height=28, corner_radius=4,
                fg_color="#1c3a27", hover_color="#2a5a3b", text_color="#4aff4a",
                font=ctk.CTkFont(size=14),
                command=lambda did=d_id, dn=d_name: self.open_history_modal(did, dn)
            ).pack(side="left", padx=2)

            ctk.CTkButton(
                act, text="✏️", width=32, height=28, corner_radius=4,
                fg_color="#2b3a4a", hover_color="#3d5268",
                font=ctk.CTkFont(size=14),
                command=lambda r=row: self.open_edit_modal(r)
            ).pack(side="left", padx=2)

            ctk.CTkButton(
                act, text="🗑️", width=32, height=28, corner_radius=4,
                fg_color="#3a1c1c", hover_color="#542424", text_color="#ff8080",
                font=ctk.CTkFont(size=14),
                command=lambda did=d_id, dn=d_name: self._confirm_delete(did, dn)
            ).pack(side="left", padx=2)

    # ── PAGINATION ────────────────────────────────────────────────────────────
    def _prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self._render_rows()

    def _next_page(self):
        max_pages = (len(self.cached_dealers) + self.items_per_page - 1) // self.items_per_page
        if (self.current_page + 1) < max_pages:
            self.current_page += 1
            self._render_rows()

    # ── DELETE ────────────────────────────────────────────────────────────────
    def _confirm_delete(self, dealer_id, dealer_name):
        if messagebox.askyesno(
            "Confirm Delete",
            f"'{dealer_name}' ko permanently delete karna chahte hain?\nYe action undo nahi hogi."
        ):
            db.delete_dealer(dealer_id)
            self.refresh_grid(self.search_entry.get().strip())

    # ══════════════════════════════════════════════════════════════════════════
    # ADD / EDIT MODAL
    # ══════════════════════════════════════════════════════════════════════════
    def open_add_modal(self):
        self._dealer_modal(edit_row=None)

    def open_edit_modal(self, row):
        self._dealer_modal(edit_row=row)

    def _dealer_modal(self, edit_row=None):
        is_edit = edit_row is not None
        # Unpack — 10 columns: id,name,contact,item,unit,qty,total,per_item,date_added,last_updated
        d_id = edit_row[0] if is_edit else None

        modal = ctk.CTkToplevel(self)
        modal.title("Update Dealer" if is_edit else "Add New Dealer")
        modal.geometry("500x600")
        modal.resizable(False, False)
        modal.grab_set()
        modal.focus_force()

        sw, sh = modal.winfo_screenwidth(), modal.winfo_screenheight()
        modal.geometry(f"500x600+{(sw-500)//2}+{(sh-600)//2}")

        # ── Header ────────────────────────────────────────────────────────────
        hdr_f = ctk.CTkFrame(modal, fg_color="#16161a", corner_radius=0, height=58)
        hdr_f.pack(fill="x")
        hdr_f.pack_propagate(False)
        ctk.CTkLabel(
            hdr_f,
            text="✏️  Update Dealer" if is_edit else "🏭  Add New Dealer",
            font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"),
            text_color="#4a90e2"
        ).pack(anchor="w", padx=20, pady=16)

        # ── Scrollable form body ───────────────────────────────────────────────
        body = ctk.CTkScrollableFrame(modal, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=20, pady=12)

        def lbl(text):
            ctk.CTkLabel(body, text=text,
                         font=ctk.CTkFont(size=12, weight="bold"),
                         text_color="#8a8a96").pack(anchor="w", pady=(10, 2))

        def entry_field(placeholder, initial=""):
            e = ctk.CTkEntry(body, placeholder_text=placeholder, height=38,
                             fg_color="#16161a", border_color="#2a2a32", corner_radius=6)
            e.pack(fill="x")
            if initial:
                e.insert(0, str(initial))
            return e

        lbl("Dealer Name  *")
        ent_name = entry_field("e.g. Attock Petroleum Ltd", edit_row[1] if is_edit else "")

        lbl("Contact  (optional)")
        ent_contact = entry_field("e.g. 03001234567", edit_row[2] if is_edit else "")

        lbl("Item Name  *")
        ent_item = entry_field("e.g. HSD Diesel / Petrol", edit_row[3] if is_edit else "")

        # ── Unit Dropdown ──────────────────────────────────────────────────────
        lbl("Unit  *")
        current_unit = edit_row[4] if is_edit else "Liter"
        # Make sure current_unit is in list
        unit_options = UNITS if current_unit in UNITS else [current_unit] + UNITS

        unit_var = ctk.StringVar(value=current_unit)
        unit_menu = ctk.CTkOptionMenu(
            body, variable=unit_var, values=unit_options,
            height=38, fg_color="#16161a", button_color="#2b3a4a",
            button_hover_color="#3d5268", dropdown_fg_color="#16161a",
            font=ctk.CTkFont(size=12)
        )
        unit_menu.pack(fill="x")

        lbl("Quantity  *")
        ent_qty   = entry_field("e.g. 5000", edit_row[5] if is_edit else "")

        lbl("Total Cost (Rs)  *")
        ent_total = entry_field("e.g. 1250000", edit_row[6] if is_edit else "")

        # Auto per-item cost label
        lbl("Per Item Cost  (auto-calculated)")
        lbl_per = ctk.CTkLabel(
            body, text="—",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#4aff8e", fg_color="#16161a", corner_radius=6, height=36
        )
        lbl_per.pack(fill="x")

        def _recalc(*_):
            try:
                q = float(ent_qty.get().strip())
                t = float(ent_total.get().strip())
                lbl_per.configure(text=f"Rs {t/q:,.4f}" if q > 0 else "—")
            except Exception:
                lbl_per.configure(text="—")

        ent_qty.bind("<KeyRelease>", _recalc)
        ent_total.bind("<KeyRelease>", _recalc)
        if is_edit:
            _recalc()

        lbl("Notes / Reason  (history ke liye)")
        ent_notes = ctk.CTkTextbox(body, height=68, fg_color="#16161a",
                                   border_color="#2a2a32", border_width=1, corner_radius=6)
        ent_notes.pack(fill="x")

        # ── Footer Buttons ────────────────────────────────────────────────────
        foot = ctk.CTkFrame(modal, fg_color="#16161a", corner_radius=0, height=62)
        foot.pack(fill="x", side="bottom")
        foot.pack_propagate(False)

        def _save():
            name    = ent_name.get().strip()
            contact = ent_contact.get().strip()
            item    = ent_item.get().strip()
            unit    = unit_var.get().strip()
            qty_s   = ent_qty.get().strip()
            tot_s   = ent_total.get().strip()
            notes   = ent_notes.get("1.0", "end").strip()

            if not name:
                messagebox.showerror("Validation", "Dealer Name zaroori hai!", parent=modal); return
            if not item:
                messagebox.showerror("Validation", "Item Name zaroori hai!", parent=modal); return
            try:
                qty = float(qty_s)
                if qty <= 0: raise ValueError
            except ValueError:
                messagebox.showerror("Validation", "Quantity valid number honi chahiye (> 0)!", parent=modal); return
            try:
                total = float(tot_s)
                if total <= 0: raise ValueError
            except ValueError:
                messagebox.showerror("Validation", "Total Cost valid amount hona chahiye (> 0)!", parent=modal); return

            if is_edit:
                db.update_dealer(d_id, name, contact, item, unit, qty, total, notes)
                messagebox.showinfo("Updated", f"'{name}' update ho gaya!", parent=modal)
            else:
                db.add_dealer(name, contact, item, unit, qty, total, notes)
                messagebox.showinfo("Added", f"'{name}' add ho gaya!", parent=modal)

            modal.destroy()
            self.refresh_grid(self.search_entry.get().strip())

        ctk.CTkButton(
            foot, text="Cancel", height=40, width=90, corner_radius=6,
            fg_color="#2a2a32", hover_color="#3a3a42", font=ctk.CTkFont(size=13),
            command=modal.destroy
        ).pack(side="left", padx=18, pady=11)

        ctk.CTkButton(
            foot,
            text="💾  Save Changes" if is_edit else "✅  Add Dealer",
            height=40, corner_radius=6,
            fg_color="#1f3a4a", hover_color="#2a5268",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            command=_save
        ).pack(side="right", padx=18, pady=11)

    # ══════════════════════════════════════════════════════════════════════════
    # HISTORY MODAL
    # ══════════════════════════════════════════════════════════════════════════
    def open_history_modal(self, dealer_id, dealer_name):
        history = db.get_dealer_history(dealer_id)

        modal = ctk.CTkToplevel(self)
        modal.title(f"History — {dealer_name}")
        modal.geometry("780x500")
        modal.resizable(True, True)
        modal.grab_set()
        modal.focus_force()

        sw, sh = modal.winfo_screenwidth(), modal.winfo_screenheight()
        modal.geometry(f"780x500+{(sw-780)//2}+{(sh-500)//2}")

        # Header
        hdr = ctk.CTkFrame(modal, fg_color="#16161a", corner_radius=0, height=58)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        ctk.CTkLabel(
            hdr, text=f"📋  Audit History — {dealer_name}",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color="#4a90e2"
        ).pack(anchor="w", padx=20, pady=16)

        scroll = ctk.CTkScrollableFrame(
            modal, fg_color="#121214", border_color="#222227",
            border_width=1, corner_radius=6
        )
        scroll.pack(fill="both", expand=True, padx=14, pady=12)

        # History columns: Action | Item | Unit | Qty | Total | Per Item | Date | Notes
        hcols = [
            ("Action",    78,  "center"),
            ("Item",     110,  "w"),
            ("Unit",      68,  "center"),
            ("Qty",       60,  "center"),
            ("Total Cost",105, "center"),
            ("Per Item",  95,  "center"),
            ("Date / Time",148,"center"),
            ("Notes",     170, "w"),
        ]

        # Header row
        hrow = ctk.CTkFrame(scroll, fg_color="#16161a", corner_radius=4, height=33)
        hrow.pack(fill="x", pady=(0, 6))
        hrow.pack_propagate(False)
        for label, w, anc in hcols:
            ctk.CTkLabel(
                hrow, text=label, width=w, anchor=anc,
                font=ctk.CTkFont(size=11, weight="bold"), text_color="#4a90e2"
            ).pack(side="left", padx=3)

        if not history:
            ctk.CTkLabel(scroll, text="Koi history record nahi mila abhi tak.",
                         text_color="#555560", font=ctk.CTkFont(size=12)).pack(pady=40)
        else:
            for idx, h in enumerate(history):
                # 11 columns from DB
                (h_id, action, h_name, h_contact, h_item, h_unit,
                 h_qty, h_total, h_per, h_date, h_notes) = h

                rf = ctk.CTkFrame(
                    scroll,
                    fg_color="#18181f" if idx % 2 == 0 else "transparent",
                    height=40, corner_radius=4
                )
                rf.pack(fill="x", pady=2)
                rf.pack_propagate(False)

                # Action badge
                act_color = "#4aff4a" if action == "ADDED" else "#f0ad4e"
                act_bg    = "#1c3a27" if action == "ADDED" else "#3a2a10"
                badge_f = ctk.CTkFrame(rf, fg_color=act_bg, corner_radius=4,
                                       width=70, height=22)
                badge_f.pack(side="left", padx=6, pady=9)
                badge_f.pack_propagate(False)
                ctk.CTkLabel(badge_f, text=action, text_color=act_color,
                             font=ctk.CTkFont(size=9, weight="bold")).pack(expand=True)

                qty_s  = str(int(h_qty)) if h_qty and float(h_qty)==int(h_qty) else f"{h_qty:g}" if h_qty else "—"
                tot_s  = f"Rs {h_total:,.2f}" if h_total else "—"
                per_s  = f"Rs {h_per:,.4f}" if h_per else "—"
                dt_s   = h_date[:16] if h_date else "—"
                nt_s   = (h_notes[:26] + "…") if h_notes and len(h_notes) > 26 else (h_notes or "—")
                itm_s  = (h_item[:14] + "…") if h_item and len(h_item) > 14 else (h_item or "—")
                un_s   = h_unit or "—"

                for txt, (_, w, anc) in zip([itm_s, un_s, qty_s, tot_s, per_s, dt_s, nt_s], hcols[1:]):
                    ctk.CTkLabel(rf, text=txt, width=w, anchor=anc,
                                 text_color="#a0a0a9",
                                 font=ctk.CTkFont(size=11)).pack(side="left", padx=3)

        ctk.CTkButton(
            modal, text="Close", height=36, width=110, corner_radius=6,
            fg_color="#2a2a32", hover_color="#3a3a42", font=ctk.CTkFont(size=12),
            command=modal.destroy
        ).pack(pady=(0, 12))
