import customtkinter as ctk
import database.db_manager as db
import tkinter.messagebox as messagebox

# =====================================================================
# 🎨 PROFESSIONAL THEME PALETTE
# =====================================================================
COL_BG_CARD     = "#1a1d24"
COL_BG_CARD_ALT = "#15171d"
COL_BG_INPUT    = "#11131a"
COL_BORDER      = "#2a2e38"
COL_ACCENT      = "#3b82f6"   # primary blue
COL_ACCENT_SOFT = "#1e293b"
COL_SUCCESS     = "#22c55e"
COL_SUCCESS_BG  = "#14241c"
COL_DANGER      = "#ef4444"
COL_DANGER_BG   = "#2a1518"
COL_TEXT_MAIN   = "#f1f5f9"
COL_TEXT_MUTED  = "#94a3b8"
COL_TEXT_SOFT   = "#64748b"


class BillingView(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")

        # --- APP STATE MANAGEMENT MATRICES ---
        self.cart_items = {}            # {product_id: {name, rate, qty, total}}
        self.selected_khata_id = None   # Track linked running wallet context
        self.linked_customer_name = None  # Name of linked khata customer
        self.subtotal = 0.0
        self.net_total = 0.0

        # Base layout parent allocations splitting
        self.grid_columnconfigure(0, weight=5)
        self.grid_columnconfigure(1, weight=3)
        self.grid_rowconfigure(0, weight=1)

        # =================================================================
        # 🛒 LEFT MAIN PANEL: CTkScrollableFrame so cart is always visible
        # =================================================================
        left_pane = ctk.CTkScrollableFrame(self, fg_color="transparent")
        left_pane.grid(row=0, column=0, sticky="nsew", padx=(0, 14))
        left_pane.grid_columnconfigure(0, weight=1)

        # -----------------------------------------------------------
        # SECTION 1 — CUSTOMER
        # -----------------------------------------------------------
        id_group = ctk.CTkFrame(left_pane, fg_color=COL_BG_CARD, border_color=COL_BORDER,
                                 border_width=1, corner_radius=10)
        id_group.pack(fill="x", pady=(0, 12))

        id_header = ctk.CTkFrame(id_group, fg_color="transparent")
        id_header.pack(fill="x", padx=18, pady=(10, 4))
        ctk.CTkLabel(id_header, text="👤 Customer", font=ctk.CTkFont(size=14, weight="bold"),
                     text_color=COL_TEXT_MAIN).pack(side="left")
        ctk.CTkLabel(id_header, text="Walk-in or linked khata account", font=ctk.CTkFont(size=11),
                     text_color=COL_TEXT_SOFT).pack(side="left", padx=(8, 0))

        search_row = ctk.CTkFrame(id_group, fg_color="transparent")
        search_row.pack(fill="x", padx=18, pady=(0, 6))

        self.inp_cust_search = ctk.CTkEntry(
            search_row, placeholder_text="Customer name, phone, or Khata No. (e.g. KH-0004 or 4)...",
            height=36, fg_color=COL_BG_INPUT, border_color=COL_BORDER,
            corner_radius=8, font=ctk.CTkFont(size=13)
        )
        self.inp_cust_search.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.inp_cust_search.bind("<KeyRelease>", self.on_customer_search_keypress)

        self.btn_clear_cust = ctk.CTkButton(
            search_row, text="Unlink", width=90, height=36, corner_radius=8,
            fg_color=COL_BG_INPUT, hover_color=COL_BORDER, text_color=COL_TEXT_MUTED,
            border_color=COL_BORDER, border_width=1, font=ctk.CTkFont(size=12, weight="bold"),
            state="disabled", command=self.unlink_customer_profile
        )
        self.btn_clear_cust.pack(side="right")

        self.lbl_wallet_badge = ctk.CTkLabel(
            id_group, text="🔒  Walk-in customer  ·  Standard cash invoice",
            font=ctk.CTkFont(size=11), text_color=COL_TEXT_SOFT, anchor="w"
        )
        self.lbl_wallet_badge.pack(anchor="w", padx=18, pady=(0, 10))

        # -----------------------------------------------------------
        # SECTION 2 — PRODUCT CATALOG
        # -----------------------------------------------------------
        prod_engine_group = ctk.CTkFrame(left_pane, fg_color=COL_BG_CARD, border_color=COL_BORDER,
                                          border_width=1, corner_radius=10)
        prod_engine_group.pack(fill="x", pady=(0, 12))

        prod_header = ctk.CTkFrame(prod_engine_group, fg_color="transparent")
        prod_header.pack(fill="x", padx=18, pady=(10, 4))
        ctk.CTkLabel(prod_header, text="📦 Products", font=ctk.CTkFont(size=14, weight="bold"),
                     text_color=COL_TEXT_MAIN).pack(side="left")
        ctk.CTkLabel(prod_header, text="Search and add items to the invoice", font=ctk.CTkFont(size=11),
                     text_color=COL_TEXT_SOFT).pack(side="left", padx=(8, 0))

        self.inp_prod_search = ctk.CTkEntry(
            prod_engine_group, placeholder_text="🔍  Search by product name or code...",
            height=36, fg_color=COL_BG_INPUT, border_color=COL_BORDER,
            corner_radius=8, font=ctk.CTkFont(size=13)
        )
        self.inp_prod_search.pack(fill="x", padx=18, pady=(0, 8))
        self.inp_prod_search.bind("<KeyRelease>", lambda e: self.render_product_search_results())

        self.catalog_scroll = ctk.CTkScrollableFrame(
            prod_engine_group, fg_color=COL_BG_INPUT, height=110,
            border_color=COL_BORDER, border_width=1, corner_radius=8
        )
        self.catalog_scroll.pack(fill="x", padx=18, pady=(0, 10))

        # -----------------------------------------------------------
        # SECTION 3 — LIVE CART
        # -----------------------------------------------------------
        cart_group = ctk.CTkFrame(left_pane, fg_color=COL_BG_CARD, border_color=COL_BORDER,
                                   border_width=1, corner_radius=10)
        cart_group.pack(fill="x", pady=(0, 4))
        cart_group.grid_columnconfigure(0, weight=1)

        cart_header = ctk.CTkFrame(cart_group, fg_color="transparent")
        cart_header.pack(fill="x", padx=18, pady=(10, 6))
        ctk.CTkLabel(cart_header, text="🧾 Invoice Items", font=ctk.CTkFont(size=14, weight="bold"),
                     text_color=COL_TEXT_MAIN).pack(side="left")
        ctk.CTkLabel(cart_header, text="Items added to this invoice", font=ctk.CTkFont(size=11),
                     text_color=COL_TEXT_SOFT).pack(side="left", padx=(8, 0))

        # Column header row
        h_frame = ctk.CTkFrame(cart_group, fg_color=COL_BG_CARD_ALT, corner_radius=8, height=38)
        h_frame.pack(fill="x", padx=14, pady=(0, 8))

        self.cart_widths = [170, 80, 210, 110, 40]
        headers = ["Item", "Rate", "Quantity", "Total", ""]

        for idx, txt in enumerate(headers):
            anchor_pos = "w" if idx == 0 else "center"
            ctk.CTkLabel(h_frame, text=txt, width=self.cart_widths[idx],
                         font=ctk.CTkFont(size=11, weight="bold"), text_color=COL_TEXT_SOFT,
                         anchor=anchor_pos).pack(side="left", padx=5, pady=8)

        self.cart_scroll = ctk.CTkScrollableFrame(cart_group, fg_color="transparent", height=220)
        self.cart_scroll.pack(fill="x", padx=14, pady=(0, 14))

        # =================================================================
        # 📊 RIGHT PANEL: CHECKOUT SUMMARY
        # =================================================================
        right_pane = ctk.CTkFrame(self, fg_color=COL_BG_CARD, border_color=COL_BORDER,
                                   border_width=1, corner_radius=10)
        right_pane.grid(row=0, column=1, sticky="nsew", padx=(14, 0))

        ctk.CTkLabel(right_pane, text="💵 Checkout Summary", font=ctk.CTkFont(size=16, weight="bold"),
                     text_color=COL_TEXT_MAIN).pack(anchor="w", padx=20, pady=(20, 16))

        # Tax row
        tax_row = ctk.CTkFrame(right_pane, fg_color=COL_BG_INPUT, corner_radius=8, border_color=COL_BORDER, border_width=1)
        tax_row.pack(fill="x", padx=20, pady=(0, 14))

        ctk.CTkLabel(tax_row, text="Tax / Surcharge", font=ctk.CTkFont(size=12), text_color=COL_TEXT_MUTED).pack(side="left", padx=(14, 0), pady=10)
        tax_input_holder = ctk.CTkFrame(tax_row, fg_color="transparent")
        tax_input_holder.pack(side="right", padx=(0, 10), pady=6)
        self.inp_tax_percent = ctk.CTkEntry(tax_input_holder, width=60, height=32, fg_color=COL_BG_CARD,
                                             border_color=COL_BORDER, corner_radius=6, justify="center",
                                             font=ctk.CTkFont(size=13, weight="bold"))
        self.inp_tax_percent.insert(0, "0")
        self.inp_tax_percent.pack(side="left")
        ctk.CTkLabel(tax_input_holder, text="%", font=ctk.CTkFont(size=13, weight="bold"), text_color=COL_TEXT_MUTED).pack(side="left", padx=(6, 0))
        self.inp_tax_percent.bind("<KeyRelease>", lambda e: self.refresh_cart_display_grid())

        # Totals breakdown card
        totals_box = ctk.CTkFrame(right_pane, fg_color=COL_BG_INPUT, border_color=COL_BORDER,
                                   border_width=1, corner_radius=10)
        totals_box.pack(fill="x", padx=20, pady=(0, 18))

        row_subtotal = ctk.CTkFrame(totals_box, fg_color="transparent")
        row_subtotal.pack(fill="x", padx=16, pady=(16, 6))
        ctk.CTkLabel(row_subtotal, text="Subtotal", font=ctk.CTkFont(size=13), text_color=COL_TEXT_MUTED).pack(side="left")
        self.lbl_subtotal_val = ctk.CTkLabel(row_subtotal, text="Rs. 0.00", font=ctk.CTkFont(size=13, weight="bold"), text_color=COL_TEXT_MAIN)
        self.lbl_subtotal_val.pack(side="right")

        row_tax = ctk.CTkFrame(totals_box, fg_color="transparent")
        row_tax.pack(fill="x", padx=16, pady=(0, 12))
        self.lbl_tax_label = ctk.CTkLabel(row_tax, text="Tax (0%)", font=ctk.CTkFont(size=13), text_color=COL_TEXT_MUTED)
        self.lbl_tax_label.pack(side="left")
        self.lbl_tax_val = ctk.CTkLabel(row_tax, text="Rs. 0.00", font=ctk.CTkFont(size=13, weight="bold"), text_color=COL_TEXT_MAIN)
        self.lbl_tax_val.pack(side="right")

        # Divider
        ctk.CTkFrame(totals_box, fg_color=COL_BORDER, height=1).pack(fill="x", padx=16)

        row_total = ctk.CTkFrame(totals_box, fg_color="transparent")
        row_total.pack(fill="x", padx=16, pady=(12, 16))
        ctk.CTkLabel(row_total, text="Net Payable", font=ctk.CTkFont(size=14, weight="bold"), text_color=COL_TEXT_MAIN).pack(side="left")
        self.lbl_total_val = ctk.CTkLabel(row_total, text="Rs. 0.00", font=ctk.CTkFont(size=22, weight="bold"), text_color=COL_ACCENT)
        self.lbl_total_val.pack(side="right")

        # Action buttons
        self.btn_pay_cash = ctk.CTkButton(
            right_pane, text="⚡  Generate Cash Invoice", height=46, corner_radius=8,
            fg_color=COL_ACCENT, hover_color="#2563eb", text_color="#ffffff",
            font=ctk.CTkFont(size=13, weight="bold"),
            command=lambda: self.commit_invoice(payment_mode="CASH")
        )
        self.btn_pay_cash.pack(fill="x", padx=20, pady=(0, 8))

        self.btn_pay_wallet = ctk.CTkButton(
            right_pane, text="💳  Deduct from Khata / Wallet", height=46, corner_radius=8,
            fg_color=COL_SUCCESS_BG, hover_color="#1c3328", text_color=COL_SUCCESS,
            border_color="#2d5a3b", border_width=1, font=ctk.CTkFont(size=13, weight="bold"),
            state="disabled", command=lambda: self.commit_invoice(payment_mode="WALLET")
        )
        self.btn_pay_wallet.pack(fill="x", padx=20, pady=(0, 8))

        ctk.CTkButton(
            right_pane, text="Reset Cart", height=40, corner_radius=8, fg_color="transparent",
            border_color=COL_BORDER, border_width=1, text_color=COL_TEXT_SOFT,
            hover_color=COL_BG_CARD_ALT, font=ctk.CTkFont(size=12),
            command=self.clear_entire_session
        ).pack(fill="x", padx=20, pady=(8, 20))

        self.render_product_search_results()

    # =================================================================
    # 📦 PRODUCT CATALOG RENDERING
    # =================================================================
    def render_product_search_results(self):
        for w in self.catalog_scroll.winfo_children(): w.destroy()
        query = self.inp_prod_search.get().strip()

        products_list = []
        try:
            if hasattr(db, 'get_all_products'): products_list = db.get_all_products(query)
            elif hasattr(db, 'get_products'): products_list = db.get_products(query)
        except Exception as e:
            print(f"Database Unpack Error Context: {e}")

        if not products_list:
            ctk.CTkLabel(self.catalog_scroll, text="No products found.", text_color=COL_TEXT_SOFT,
                         font=ctk.CTkFont(size=12)).pack(pady=12)
            return

        for row_data in products_list:
            try:
                if len(row_data) >= 7:
                    p_id, p_name, p_price = row_data[0], row_data[1], row_data[6]
                else:
                    p_id, p_name, p_price = row_data[0], row_data[1], row_data[2]

                row = ctk.CTkFrame(self.catalog_scroll, fg_color="transparent")
                row.pack(fill="x", padx=6, pady=4)

                ctk.CTkLabel(row, text=p_name, font=ctk.CTkFont(size=12, weight="bold"),
                             text_color=COL_TEXT_MAIN, anchor="w").pack(side="left", padx=(2, 8))
                ctk.CTkLabel(row, text=f"Rs. {float(p_price):.2f}", font=ctk.CTkFont(size=12),
                             text_color=COL_ACCENT).pack(side="left", padx=10)

                pass_item = {"id": str(p_id), "name": p_name, "price": float(p_price)}
                ctk.CTkButton(row, text="+ Add", width=70, height=26, corner_radius=6,
                               fg_color=COL_ACCENT_SOFT, hover_color=COL_BORDER,
                               text_color=COL_ACCENT, font=ctk.CTkFont(size=11, weight="bold"),
                               command=lambda p=pass_item: self.add_or_increment_cart(p)).pack(side="right", padx=5)
            except Exception:
                continue

    def add_or_increment_cart(self, product):
        p_id = product['id']
        if p_id in self.cart_items:
            self.cart_items[p_id]['qty'] += 1
            self.cart_items[p_id]['total'] = self.cart_items[p_id]['qty'] * product['price']
        else:
            self.cart_items[p_id] = {
                'name': product['name'],
                'rate': product['price'],
                'qty': 1,
                'total': product['price']
            }
        self.refresh_cart_display_grid()

    def modify_qty_counter(self, p_id, offset):
        if p_id in self.cart_items:
            self.cart_items[p_id]['qty'] += offset
            if self.cart_items[p_id]['qty'] <= 0:
                del self.cart_items[p_id]
            else:
                self.cart_items[p_id]['total'] = self.cart_items[p_id]['qty'] * self.cart_items[p_id]['rate']
            self.refresh_cart_display_grid()

    def set_qty_manual(self, p_id, value):
        if p_id not in self.cart_items:
            return
        try:
            raw = str(value).strip()
            new_qty = round(float(raw), 4) if raw else 0.0
        except ValueError:
            new_qty = self.cart_items[p_id]['qty']

        if new_qty <= 0:
            del self.cart_items[p_id]
        else:
            self.cart_items[p_id]['qty'] = new_qty
            self.cart_items[p_id]['total'] = round(new_qty * self.cart_items[p_id]['rate'], 2)
            self.cart_items[p_id]['mode'] = self.cart_items[p_id].get('mode', 'qty')
        self.refresh_cart_display_grid()

    def set_qty_from_amount(self, p_id, amount_str):
        """Amount mode: user types Rs. amount → auto-calculate qty."""
        if p_id not in self.cart_items:
            return
        try:
            amount = round(float(str(amount_str).strip()), 2)
        except ValueError:
            return
        if amount <= 0:
            return
        rate = self.cart_items[p_id]['rate']
        if rate <= 0:
            return
        new_qty = round(amount / rate, 4)
        self.cart_items[p_id]['qty']    = new_qty
        self.cart_items[p_id]['total']  = amount
        self.cart_items[p_id]['amount'] = amount
        self.refresh_cart_display_grid()
    def refresh_cart_display_grid(self):
        for w in self.cart_scroll.winfo_children(): w.destroy()
        self.subtotal = 0.0

        if not self.cart_items:
            ctk.CTkLabel(self.cart_scroll, text="No items added yet — search a product above to begin.",
                         font=ctk.CTkFont(size=12), text_color=COL_TEXT_SOFT).pack(pady=20)

        for idx, (p_id, item) in enumerate(self.cart_items.items()):
            self.subtotal += item['total']

            row_bg = COL_BG_CARD_ALT if idx % 2 == 0 else COL_BG_CARD
            row = ctk.CTkFrame(self.cart_scroll, fg_color=row_bg, corner_radius=8, height=44)
            row.pack(fill="x", pady=3, padx=2)

            ctk.CTkLabel(row, text=item['name'], width=self.cart_widths[0], anchor="w",
                         font=ctk.CTkFont(size=12, weight="bold"), text_color=COL_TEXT_MAIN).pack(side="left", padx=(10, 5), pady=8)
            ctk.CTkLabel(row, text=f"Rs. {item['rate']:.2f}", width=self.cart_widths[1],
                         font=ctk.CTkFont(size=12), text_color=COL_TEXT_MUTED).pack(side="left", padx=5)

            qty_control_box = ctk.CTkFrame(row, fg_color="transparent", width=self.cart_widths[2])
            qty_control_box.pack(side="left", padx=4)

            # ── Mode toggle pill: QTY | AMT ──────────────────────
            item_mode = item.get('mode', 'qty')

            mode_frame = ctk.CTkFrame(qty_control_box, fg_color=COL_BG_INPUT,
                                      corner_radius=8, border_color=COL_BORDER, border_width=1)
            mode_frame.pack(side="left", padx=(0, 4))

            btn_qty_mode = ctk.CTkButton(
                mode_frame, text="QTY", width=34, height=22, corner_radius=6,
                fg_color=COL_ACCENT if item_mode == 'qty' else "transparent",
                hover_color=COL_ACCENT_SOFT,
                text_color=COL_TEXT_MAIN if item_mode == 'qty' else COL_TEXT_SOFT,
                font=ctk.CTkFont(size=10, weight="bold"),
                command=lambda k=p_id: self._set_cart_mode(k, 'qty')
            )
            btn_qty_mode.pack(side="left", padx=2, pady=2)

            btn_amt_mode = ctk.CTkButton(
                mode_frame, text="AMT", width=34, height=22, corner_radius=6,
                fg_color="#854F0B" if item_mode == 'amt' else "transparent",
                hover_color=COL_ACCENT_SOFT,
                text_color="#FAC775" if item_mode == 'amt' else COL_TEXT_SOFT,
                font=ctk.CTkFont(size=10, weight="bold"),
                command=lambda k=p_id: self._set_cart_mode(k, 'amt')
            )
            btn_amt_mode.pack(side="left", padx=2, pady=2)

            # ── QTY controls (shown in qty mode) ─────────────────
            if item_mode == 'qty':
                ctk.CTkButton(qty_control_box, text="−", width=24, height=26, corner_radius=6,
                              fg_color=COL_BG_INPUT, hover_color=COL_BORDER, text_color=COL_TEXT_MAIN,
                              font=ctk.CTkFont(size=13, weight="bold"),
                              command=lambda k=p_id: self.modify_qty_counter(k, -1)).pack(side="left", padx=1)

                # Format qty: show integer if whole, else show decimal
                qty_display = str(int(item['qty'])) if item['qty'] == int(item['qty']) else f"{item['qty']:g}"
                qty_var = ctk.StringVar(value=qty_display)
                qty_entry = ctk.CTkEntry(qty_control_box, textvariable=qty_var, width=46, height=26,
                                          justify="center", fg_color=COL_BG_INPUT, border_color=COL_BORDER,
                                          corner_radius=6, font=ctk.CTkFont(size=12, weight="bold"),
                                          text_color=COL_TEXT_MAIN)
                qty_entry.pack(side="left", padx=1)
                qty_entry.bind("<Return>",   lambda e, k=p_id, v=qty_var: self.set_qty_manual(k, v.get()))
                qty_entry.bind("<FocusOut>", lambda e, k=p_id, v=qty_var: self.set_qty_manual(k, v.get()))

                ctk.CTkButton(qty_control_box, text="+", width=24, height=26, corner_radius=6,
                              fg_color=COL_BG_INPUT, hover_color=COL_BORDER, text_color=COL_TEXT_MAIN,
                              font=ctk.CTkFont(size=13, weight="bold"),
                              command=lambda k=p_id: self.modify_qty_counter(k, 1)).pack(side="left", padx=1)

            else:
                # ── AMT mode: show Rs. input, qty shown as read-only ──
                saved_amt = item.get('amount', round(item['qty'] * item['rate'], 2))
                amt_var = ctk.StringVar(value=str(int(saved_amt)) if saved_amt == int(saved_amt) else f"{saved_amt:g}")
                amt_entry = ctk.CTkEntry(qty_control_box, textvariable=amt_var, width=70, height=26,
                                          justify="center", fg_color=COL_BG_INPUT,
                                          border_color="#BA7517", corner_radius=6,
                                          font=ctk.CTkFont(size=12, weight="bold"),
                                          text_color="#FAC775",
                                          placeholder_text="Rs. amount")
                amt_entry.pack(side="left", padx=2)
                amt_entry.bind("<Return>",   lambda e, k=p_id, v=amt_var: self.set_qty_from_amount(k, v.get()))
                amt_entry.bind("<FocusOut>", lambda e, k=p_id, v=amt_var: self.set_qty_from_amount(k, v.get()))

                # Calculated qty display (read-only badge)
                qty_display = f"{item['qty']:g}"
                ctk.CTkLabel(qty_control_box, text=f"={qty_display}",
                             font=ctk.CTkFont(size=11), text_color=COL_TEXT_SOFT,
                             width=40).pack(side="left", padx=(2, 0))

            ctk.CTkLabel(row, text=f"Rs. {item['total']:,.2f}", width=self.cart_widths[3],
                         font=ctk.CTkFont(size=12, weight="bold"), text_color=COL_SUCCESS,
                         anchor="center").pack(side="left", padx=5)

            ctk.CTkButton(row, text="✕", width=30, height=28, corner_radius=6,
                          fg_color=COL_DANGER_BG, hover_color="#3a1c1c", text_color=COL_DANGER,
                          font=ctk.CTkFont(size=12, weight="bold"),
                          command=lambda k=p_id: self.drop_cart_item(k)).pack(side="right", padx=(5, 10))

        try:
            tax_percent = float(self.inp_tax_percent.get().strip() or 0)
        except ValueError:
            tax_percent = 0.0

        tax_amount = self.subtotal * tax_percent / 100
        self.net_total = self.subtotal + tax_amount

        self.lbl_subtotal_val.configure(text=f"Rs. {self.subtotal:,.2f}")
        self.lbl_tax_label.configure(text=f"Tax ({tax_percent:g}%)")
        self.lbl_tax_val.configure(text=f"Rs. {tax_amount:,.2f}")
        self.lbl_total_val.configure(text=f"Rs. {self.net_total:,.2f}")

    def _set_cart_mode(self, p_id, mode):
        """Switch a cart item between 'qty' and 'amt' input mode."""
        if p_id not in self.cart_items:
            return
        self.cart_items[p_id]['mode'] = mode
        # When switching to qty mode, clear stored amount so it recalculates cleanly
        if mode == 'qty' and 'amount' in self.cart_items[p_id]:
            del self.cart_items[p_id]['amount']
        self.refresh_cart_display_grid()

    def drop_cart_item(self, target_key):
        if target_key in self.cart_items:
            del self.cart_items[target_key]
            self.refresh_cart_display_grid()

    # =================================================================
    # 🎛️ CUSTOMER SEARCH / KHATA LINKING
    # =================================================================
    def on_customer_search_keypress(self, event):
        query = self.inp_cust_search.get().strip()
        if len(query) < 2:
            self.destroy_dropdown_popup(); return

        matches = db.get_ledger_customers(query) if hasattr(db, 'get_ledger_customers') else []
        if matches: self.render_dynamic_dropdown_popup(matches)
        else: self.destroy_dropdown_popup()

    def render_dynamic_dropdown_popup(self, dataset):
        self.destroy_dropdown_popup()
        x = self.inp_cust_search.winfo_rootx() - self.winfo_toplevel().winfo_rootx()
        y = (self.inp_cust_search.winfo_rooty() - self.winfo_toplevel().winfo_rooty()) + self.inp_cust_search.winfo_height()

        self.popup = ctk.CTkFrame(self.winfo_toplevel(), width=self.inp_cust_search.winfo_width(), height=150,
                                   fg_color=COL_BG_INPUT, border_color=COL_BORDER, border_width=1, corner_radius=8)
        self.popup.place(x=x, y=y + 4)

        scroll = ctk.CTkScrollableFrame(self.popup, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=4, pady=4)

        for record in dataset:
            k_id, name, phone, balance = record
            btn = ctk.CTkButton(scroll, text=f"  KH-{k_id:04d}  ·  {name}  ({phone})  ·  Bal: Rs.{balance}",
                                 height=32, corner_radius=6, fg_color="transparent",
                                 text_color=COL_TEXT_MUTED, hover_color=COL_ACCENT_SOFT, anchor="w",
                                 font=ctk.CTkFont(size=12),
                                 command=lambda p=record: self.link_customer_profile(p))
            btn.pack(fill="x", pady=1)

    def destroy_dropdown_popup(self):
        if hasattr(self, 'popup') and self.popup.winfo_exists():
            self.popup.destroy()

    def link_customer_profile(self, payload):
        self.destroy_dropdown_popup()
        k_id, name, phone, balance = payload
        self.selected_khata_id = k_id
        self.linked_customer_name = name
        self.inp_cust_search.delete(0, "end")
        self.inp_cust_search.insert(0, f"KH-{k_id:04d}  ·  {name}")
        self.btn_clear_cust.configure(state="normal")
        bal_color = COL_SUCCESS if balance >= 0 else COL_DANGER
        self.lbl_wallet_badge.configure(text=f"🛡️  Linked to {name}  ·  Balance: Rs. {balance}", text_color=bal_color)
        self.btn_pay_wallet.configure(state="normal")

    def unlink_customer_profile(self):
        self.selected_khata_id = None
        self.linked_customer_name = None
        self.inp_cust_search.delete(0, "end")
        self.btn_clear_cust.configure(state="disabled")
        self.lbl_wallet_badge.configure(text="🔒  Walk-in customer  ·  Standard cash invoice", text_color=COL_TEXT_SOFT)
        self.btn_pay_wallet.configure(state="disabled")

    def destroy(self):
        self.destroy_dropdown_popup()
        super().destroy()

    # =================================================================
    # 🏁 INVOICE COMMIT PIPELINE
    # =================================================================
    def commit_invoice(self, payment_mode="CASH"):
        if self.subtotal <= 0:
            messagebox.showerror("Empty Cart", "Add at least one item before generating an invoice."); return

        try:
            tax_percent = float(self.inp_tax_percent.get().strip() or 0)
        except ValueError:
            tax_percent = 0.0

        tax_amount = self.subtotal * tax_percent / 100
        net_total = self.subtotal + tax_amount

        # Build cart_items in the 6-tuple format expected by create_invoice & print window:
        # [p_id, name, qty, price, total, max_stock]
        cart_payload = []
        for p_id, item in self.cart_items.items():
            cart_payload.append([p_id, item['name'], item['qty'], item['rate'], item['total'], 0])

        if payment_mode == "WALLET":
            if not self.selected_khata_id:
                messagebox.showerror("No Customer Linked", "Please link a Khata account before deducting from wallet."); return

            customer_name = getattr(self, "linked_customer_name", None) or "Khata Customer"

            # 1. Save the invoice + deduct stock
            ok, result, inv_date = db.create_invoice(customer_name, self.subtotal, tax_percent, net_total, payment_mode, cart_payload)
            if not ok:
                messagebox.showerror("Database Error", f"Invoice save failed: {result}"); return
            invoice_id = result

            # 2. Deduct amount from customer's wallet balance
            success, msg = db.process_wallet_transaction(
                khata_id=self.selected_khata_id,
                action_type="PURCHASE_DEBIT",
                amount=net_total,
                desc="POS System Autolink Checkout Bill Processing Node Event",
                invoice_id=invoice_id
            )
            if not success:
                messagebox.showerror("Wallet Error", f"Wallet deduction failed: {msg}"); return
            messagebox.showinfo("Khata Updated", f"Rs. {net_total:,.2f} deducted from {customer_name}'s khata balance.")

        else:
            # Standard cash invoice (walk-in / "sada" customer)
            typed_name = self.inp_cust_search.get().strip()
            customer_name = typed_name if typed_name else "Walk-in Customer"

            try:
                ok, result, inv_date = db.create_invoice(customer_name, self.subtotal, tax_percent, net_total, payment_mode, cart_payload)
                if not ok:
                    messagebox.showerror("Database Error", f"Failed to save invoice: {result}")
                    return
                invoice_id = result
            except Exception as e:
                messagebox.showerror("Database Error", f"Failed to save invoice: {e}")
                return

        # 🖨️ Open print preview window with the saved invoice details
        try:
            from modules.invoice_print import InvoicePrintWindow
            InvoicePrintWindow(self.winfo_toplevel(), invoice_id, customer_name, inv_date, self.subtotal, tax_percent, net_total, cart_payload)
        except Exception as e:
            messagebox.showwarning("Print Preview Unavailable", f"Invoice saved successfully, but print preview failed to open: {e}")

        self.clear_entire_session()

    def clear_entire_session(self):
        self.cart_items.clear()
        self.unlink_customer_profile()
        self.inp_prod_search.delete(0, "end")
        self.render_product_search_results()
        self.refresh_cart_display_grid()