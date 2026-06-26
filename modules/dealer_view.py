import customtkinter as ctk
import database.db_manager as db
import tkinter.messagebox as messagebox
from datetime import datetime


class DealerView(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")

        self.current_page = 0
        self.items_per_page = 10
        self.cached_dealers = []

        # ── TOP BAR ──────────────────────────────────────────────
        top_bar = ctk.CTkFrame(self, fg_color="transparent")
        top_bar.pack(fill="x", padx=20, pady=(10, 15))

        self.search_entry = ctk.CTkEntry(
            top_bar,
            placeholder_text="🔍 Search by dealer name, item, or contact...",
            height=40, fg_color="#16161a", border_color="#222227", corner_radius=6
        )
        self.search_entry.pack(side="left", fill="x", expand=True, padx=(0, 15))
        self.search_entry.bind("<KeyRelease>", self._on_search)

        ctk.CTkButton(
            top_bar, text="+ Add Dealer", height=40, width=150,
            fg_color="#1f293d", hover_color="#2d3d5a",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            corner_radius=6, command=self.open_add_modal
        ).pack(side="right")

        # ── GRID ─────────────────────────────────────────────────
        self.grid_container = ctk.CTkScrollableFrame(
            self, fg_color="#121214", border_color="#222227",
            border_width=1, corner_radius=6
        )
        self.grid_container.pack(fill="both", expand=True, padx=20, pady=(0, 5))

        # ── PAGINATOR ────────────────────────────────────────────
        pag = ctk.CTkFrame(self, fg_color="transparent", height=40)
        pag.pack(fill="x", padx=20, pady=(10, 15))

        self.btn_prev = ctk.CTkButton(
            pag, text="⬅️ Previous", width=120, height=32,
            fg_color="#16161a", border_color="#222227", border_width=1,
            hover_color="#1f1f24", font=ctk.CTkFont(size=12, weight="bold"),
            command=self._prev_page
        )
        self.btn_prev.pack(side="left")

        self.lbl_page = ctk.CTkLabel(
            pag, text="Page 1 of 1",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"), text_color="gray"
        )
        self.lbl_page.pack(side="left", expand=True)

        self.btn_next = ctk.CTkButton(
            pag, text="Next ➡️", width=120, height=32,
            fg_color="#16161a", border_color="#222227", border_width=1,
            hover_color="#1f1f24", font=ctk.CTkFont(size=12, weight="bold"),
            command=self._next_page
        )
        self.btn_next.pack(side="right")

        self.refresh_grid()

    # ─────────────────────────────────────────────────────────────
    # DATA REFRESH
    # ─────────────────────────────────────────────────────────────
    def refresh_grid(self, search_text=""):
        self.cached_dealers = db.get_all_dealers(search_text)
        self._render_rows()

    def _on_search(self, event=None):
        self.current_page = 0
        self.refresh_grid(self.search_entry.get().strip())

    # ─────────────────────────────────────────────────────────────
    # RENDER ROWS
    # ─────────────────────────────────────────────────────────────
    def _render_rows(self):
        for w in self.grid_container.winfo_children():
            w.destroy()

        total = len(self.cached_dealers)
        max_pages = max(1, (total + self.items_per_page - 1) // self.items_per_page)
        if self.current_page >= max_pages:
            self.current_page = max_pages - 1

        self.lbl_page.configure(text=f"Page {self.current_page + 1} of {max_pages}")
        self.btn_prev.configure(state="normal" if self.current_page > 0 else "disabled")
        self.btn_next.configure(state="normal" if (self.current_page + 1) < max_pages else "disabled")

        start = self.current_page * self.items_per_page
        chunk = self.cached_dealers[start: start + self.items_per_page]

        # Column widths: S.No | Name | Contact | Item | Qty | Total Cost | Per Item | Date | Actions
        widths = [40, 160, 120, 160, 65, 110, 110, 140, 135]

        # Header
        hdr = ctk.CTkFrame(self.grid_container, fg_color="#16161a", corner_radius=4, height=35)
        hdr.pack(fill="x", pady=(0, 8))
        hdr.pack_propagate(False)

        headers = ["#", "Dealer Name", "Contact", "Item Name", "Qty",
                   "Total Cost", "Per Item", "Date Added", "Actions"]
        anchors = ["center", "w", "center", "w", "center",
                   "center", "center", "center", "center"]
        for i, (text, anc, w) in enumerate(zip(headers, anchors, widths)):
            ctk.CTkLabel(
                hdr, text=text, width=w, anchor=anc,
                font=ctk.CTkFont(size=12, weight="bold"), text_color="#4a90e2"
            ).pack(side="left", padx=4)

        if not chunk:
            ctk.CTkLabel(
                self.grid_container,
                text="No dealers found. Click '+ Add Dealer' to get started.",
                text_color="#555560", font=ctk.CTkFont(size=14)
            ).pack(pady=60)
            return

        for idx, row in enumerate(chunk):
            d_id, d_name, d_contact, item_name, qty, total_cost, per_item, date_added, last_updated = row
            global_sno = start + idx + 1

            rf = ctk.CTkFrame(
                self.grid_container,
                fg_color="#18181f" if idx % 2 == 0 else "transparent",
                height=46, corner_radius=4
            )
            rf.pack(fill="x", pady=2)
            rf.pack_propagate(False)

            # Qty display — no trailing zeros
            qty_str = str(int(qty)) if float(qty) == int(qty) else f"{qty:g}"
            contact_str = d_contact if d_contact else "—"
            date_str = date_added[:10] if date_added else "—"

            ctk.CTkLabel(rf, text=str(global_sno), width=widths[0], text_color="gray",
                         anchor="center").pack(side="left", padx=4)
            ctk.CTkLabel(rf, text=d_name, width=widths[1], anchor="w",
                         text_color="#ffffff", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=4)
            ctk.CTkLabel(rf, text=contact_str, width=widths[2], anchor="center",
                         text_color="#a0a0a9").pack(side="left", padx=4)
            ctk.CTkLabel(rf, text=item_name, width=widths[3], anchor="w",
                         text_color="#8ed1fc").pack(side="left", padx=4)
            ctk.CTkLabel(rf, text=qty_str, width=widths[4], anchor="center",
                         text_color="#ffffff").pack(side="left", padx=4)
            ctk.CTkLabel(rf, text=f"Rs {total_cost:,.2f}", width=widths[5], anchor="center",
                         text_color="#f0ad4e").pack(side="left", padx=4)
            ctk.CTkLabel(rf, text=f"Rs {per_item:,.2f}", width=widths[6], anchor="center",
                         text_color="#4aff8e").pack(side="left", padx=4)
            ctk.CTkLabel(rf, text=date_str, width=widths[7], anchor="center",
                         text_color="#a0a0a9").pack(side="left", padx=4)

            # Action buttons
            act = ctk.CTkFrame(rf, fg_color="transparent", width=widths[8])
            act.pack(side="right", padx=4)

            ctk.CTkButton(
                act, text="📋", width=30, height=28, corner_radius=4,
                fg_color="#1c3a27", hover_color="#2a5a3b", text_color="#4aff4a",
                font=ctk.CTkFont(size=13),
                command=lambda did=d_id, dn=d_name: self.open_history_modal(did, dn)
            ).pack(side="left", padx=2)

            ctk.CTkButton(
                act, text="✏️", width=30, height=28, corner_radius=4,
                fg_color="#2b3a4a", hover_color="#3d5268",
                font=ctk.CTkFont(size=13),
                command=lambda r=row: self.open_edit_modal(r)
            ).pack(side="left", padx=2)

            ctk.CTkButton(
                act, text="🗑️", width=30, height=28, corner_radius=4,
                fg_color="#3a1c1c", hover_color="#542424", text_color="#ff8080",
                font=ctk.CTkFont(size=13),
                command=lambda did=d_id, dn=d_name: self._confirm_delete(did, dn)
            ).pack(side="left", padx=2)

    # ─────────────────────────────────────────────────────────────
    # PAGINATION
    # ─────────────────────────────────────────────────────────────
    def _prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self._render_rows()

    def _next_page(self):
        total = len(self.cached_dealers)
        max_pages = (total + self.items_per_page - 1) // self.items_per_page
        if (self.current_page + 1) < max_pages:
            self.current_page += 1
            self._render_rows()

    # ─────────────────────────────────────────────────────────────
    # DELETE
    # ─────────────────────────────────────────────────────────────
    def _confirm_delete(self, dealer_id, dealer_name):
        if messagebox.askyesno(
            "Confirm Delete",
            f"'{dealer_name}' ko permanently delete karna chahte hain?\n\nYe action undo nahi hogi."
        ):
            db.delete_dealer(dealer_id)
            self.refresh_grid(self.search_entry.get().strip())

    # ─────────────────────────────────────────────────────────────
    # ADD MODAL
    # ─────────────────────────────────────────────────────────────
    def open_add_modal(self):
        self._open_dealer_modal(edit_row=None)

    def open_edit_modal(self, row):
        self._open_dealer_modal(edit_row=row)

    def _open_dealer_modal(self, edit_row=None):
        is_edit = edit_row is not None

        modal = ctk.CTkToplevel(self)
        modal.title("Update Dealer" if is_edit else "Add New Dealer")
        modal.geometry("480x560")
        modal.resizable(False, False)
        modal.grab_set()
        modal.focus_force()

        # Center modal
        modal.update_idletasks()
        sw = modal.winfo_screenwidth()
        sh = modal.winfo_screenheight()
        modal.geometry(f"480x560+{(sw-480)//2}+{(sh-560)//2}")

        # ── MODAL HEADER ─────────────────────────────────────────
        hdr_frame = ctk.CTkFrame(modal, fg_color="#16161a", corner_radius=0, height=60)
        hdr_frame.pack(fill="x")
        hdr_frame.pack_propagate(False)
        ctk.CTkLabel(
            hdr_frame,
            text="✏️  Update Dealer Record" if is_edit else "🏭  Register New Dealer",
            font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"),
            text_color="#4a90e2"
        ).pack(anchor="w", padx=20, pady=18)

        # ── FORM BODY ────────────────────────────────────────────
        body = ctk.CTkScrollableFrame(modal, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=20, pady=15)

        def field(parent, label, placeholder, initial=""):
            ctk.CTkLabel(parent, text=label,
                         font=ctk.CTkFont(size=12, weight="bold"),
                         text_color="#a0a0a9").pack(anchor="w", pady=(10, 2))
            e = ctk.CTkEntry(parent, placeholder_text=placeholder, height=38,
                             fg_color="#16161a", border_color="#2a2a32", corner_radius=6)
            e.pack(fill="x")
            if initial:
                e.insert(0, str(initial))
            return e

        d_id = edit_row[0] if is_edit else None

        ent_name    = field(body, "Dealer Name *", "e.g. Attock Petroleum Ltd", edit_row[1] if is_edit else "")
        ent_contact = field(body, "Contact (Optional)", "e.g. 03001234567", edit_row[2] if is_edit else "")
        ent_item    = field(body, "Item Name *", "e.g. HSD Diesel", edit_row[3] if is_edit else "")
        ent_qty     = field(body, "Quantity *", "e.g. 5000", edit_row[4] if is_edit else "")
        ent_total   = field(body, "Total Cost (Rs) *", "e.g. 1250000", edit_row[5] if is_edit else "")

        # Auto-calculated per-item display
        ctk.CTkLabel(body, text="Per Item Cost (Auto-calculated)",
                     font=ctk.CTkFont(size=12, weight="bold"),
                     text_color="#a0a0a9").pack(anchor="w", pady=(10, 2))
        lbl_per_item = ctk.CTkLabel(
            body, text="—",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#4aff8e",
            fg_color="#16161a", corner_radius=6, height=38
        )
        lbl_per_item.pack(fill="x")

        def _recalc(*args):
            try:
                q = float(ent_qty.get().strip())
                t = float(ent_total.get().strip())
                if q > 0:
                    lbl_per_item.configure(text=f"Rs {t/q:,.4f}")
                else:
                    lbl_per_item.configure(text="—")
            except Exception:
                lbl_per_item.configure(text="—")

        ent_qty.bind("<KeyRelease>", _recalc)
        ent_total.bind("<KeyRelease>", _recalc)
        if is_edit:
            _recalc()

        # Notes field (for history)
        ctk.CTkLabel(body, text="Notes / Reason (for history log)",
                     font=ctk.CTkFont(size=12, weight="bold"),
                     text_color="#a0a0a9").pack(anchor="w", pady=(10, 2))
        ent_notes = ctk.CTkTextbox(body, height=70, fg_color="#16161a",
                                   border_color="#2a2a32", border_width=1, corner_radius=6)
        ent_notes.pack(fill="x")

        # ── SAVE BUTTON ──────────────────────────────────────────
        def _save():
            name    = ent_name.get().strip()
            contact = ent_contact.get().strip()
            item    = ent_item.get().strip()
            qty_str = ent_qty.get().strip()
            tot_str = ent_total.get().strip()
            notes   = ent_notes.get("1.0", "end").strip()

            # Validation
            if not name:
                messagebox.showerror("Validation", "Dealer Name compulsory hai!", parent=modal)
                return
            if not item:
                messagebox.showerror("Validation", "Item Name compulsory hai!", parent=modal)
                return
            try:
                qty = float(qty_str)
                if qty <= 0:
                    raise ValueError
            except ValueError:
                messagebox.showerror("Validation", "Quantity valid number honi chahiye (> 0)!", parent=modal)
                return
            try:
                total = float(tot_str)
                if total <= 0:
                    raise ValueError
            except ValueError:
                messagebox.showerror("Validation", "Total Cost valid amount hona chahiye (> 0)!", parent=modal)
                return

            if is_edit:
                db.update_dealer(d_id, name, contact, item, qty, total, notes)
                messagebox.showinfo("Success", f"'{name}' update ho gaya!", parent=modal)
            else:
                db.add_dealer(name, contact, item, qty, total, notes)
                messagebox.showinfo("Success", f"'{name}' successfully add ho gaya!", parent=modal)

            modal.destroy()
            self.refresh_grid(self.search_entry.get().strip())

        btn_frame = ctk.CTkFrame(modal, fg_color="#16161a", corner_radius=0, height=65)
        btn_frame.pack(fill="x", side="bottom")
        btn_frame.pack_propagate(False)

        ctk.CTkButton(
            btn_frame,
            text="💾  Save Changes" if is_edit else "✅  Add Dealer",
            height=42, corner_radius=6,
            fg_color="#1f3a4a", hover_color="#2a5268",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            command=_save
        ).pack(side="right", padx=20, pady=12)

        ctk.CTkButton(
            btn_frame, text="Cancel", height=42, width=100, corner_radius=6,
            fg_color="#2a2a32", hover_color="#3a3a42",
            font=ctk.CTkFont(size=13), command=modal.destroy
        ).pack(side="left", padx=20, pady=12)

    # ─────────────────────────────────────────────────────────────
    # HISTORY MODAL
    # ─────────────────────────────────────────────────────────────
    def open_history_modal(self, dealer_id, dealer_name):
        history = db.get_dealer_history(dealer_id)

        modal = ctk.CTkToplevel(self)
        modal.title(f"History — {dealer_name}")
        modal.geometry("720x520")
        modal.resizable(True, True)
        modal.grab_set()
        modal.focus_force()

        # Center
        modal.update_idletasks()
        sw = modal.winfo_screenwidth()
        sh = modal.winfo_screenheight()
        modal.geometry(f"720x520+{(sw-720)//2}+{(sh-520)//2}")

        # Header
        hdr = ctk.CTkFrame(modal, fg_color="#16161a", corner_radius=0, height=60)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        ctk.CTkLabel(
            hdr,
            text=f"📋  Audit History — {dealer_name}",
            font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"),
            text_color="#4a90e2"
        ).pack(anchor="w", padx=20, pady=18)

        # Column widths for history: Action | Item | Qty | Total | Per Item | Date | Notes
        col_w = [80, 140, 65, 110, 110, 155, 180]
        col_headers = ["Action", "Item", "Qty", "Total Cost", "Per Item", "Date", "Notes"]

        scroll = ctk.CTkScrollableFrame(modal, fg_color="#121214",
                                        border_color="#222227", border_width=1, corner_radius=6)
        scroll.pack(fill="both", expand=True, padx=15, pady=15)

        # Header row
        hrow = ctk.CTkFrame(scroll, fg_color="#16161a", corner_radius=4, height=34)
        hrow.pack(fill="x", pady=(0, 8))
        hrow.pack_propagate(False)
        for txt, w in zip(col_headers, col_w):
            ctk.CTkLabel(hrow, text=txt, width=w, anchor="center",
                         font=ctk.CTkFont(size=11, weight="bold"),
                         text_color="#4a90e2").pack(side="left", padx=3)

        if not history:
            ctk.CTkLabel(scroll, text="Koi history record nahi mili.",
                         text_color="#555560", font=ctk.CTkFont(size=13)).pack(pady=40)
        else:
            for idx, h in enumerate(history):
                (h_id, action, h_name, h_contact, h_item,
                 h_qty, h_total, h_per, h_date, h_notes) = h

                row_bg = "#18181f" if idx % 2 == 0 else "transparent"
                rf = ctk.CTkFrame(scroll, fg_color=row_bg, height=40, corner_radius=4)
                rf.pack(fill="x", pady=2)
                rf.pack_propagate(False)

                # Action badge color
                if action == "ADDED":
                    act_color = "#4aff4a"
                    act_bg    = "#1c3a27"
                else:
                    act_color = "#f0ad4e"
                    act_bg    = "#3a2a10"

                badge = ctk.CTkFrame(rf, fg_color=act_bg, corner_radius=4, width=col_w[0]-8, height=24)
                badge.pack(side="left", padx=6, pady=8)
                badge.pack_propagate(False)
                ctk.CTkLabel(badge, text=action, text_color=act_color,
                             font=ctk.CTkFont(size=10, weight="bold")).pack(expand=True)

                qty_str = str(int(h_qty)) if h_qty and float(h_qty) == int(h_qty) else f"{h_qty:g}" if h_qty else "—"
                total_str   = f"Rs {h_total:,.2f}" if h_total else "—"
                per_str     = f"Rs {h_per:,.4f}" if h_per else "—"
                date_str    = h_date[:16] if h_date else "—"
                notes_str   = (h_notes[:22] + "…") if h_notes and len(h_notes) > 22 else (h_notes or "—")
                item_str    = (h_item[:16] + "…") if h_item and len(h_item) > 16 else (h_item or "—")

                for txt, w in zip([item_str, qty_str, total_str, per_str, date_str, notes_str],
                                   col_w[1:]):
                    ctk.CTkLabel(rf, text=txt, width=w, anchor="center",
                                 text_color="#a0a0a9",
                                 font=ctk.CTkFont(size=11)).pack(side="left", padx=3)

        ctk.CTkButton(
            modal, text="Close", height=38, width=120, corner_radius=6,
            fg_color="#2a2a32", hover_color="#3a3a42", font=ctk.CTkFont(size=13),
            command=modal.destroy
        ).pack(pady=(0, 15))
