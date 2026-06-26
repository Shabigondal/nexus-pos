import customtkinter as ctk
import math
from datetime import datetime
from database.db_manager import get_dashboard_summary, get_today_summary, get_setting


class DashboardView(ctk.CTkFrame):
    """Professional dashboard: today summary cards, all-time stats, revenue/profit chart."""

    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")

        self.shop_name = get_setting("shop_name", "Nexus POS")

        # ── WELCOME HEADER ────────────────────────────────────────────────────
        hdr_row = ctk.CTkFrame(self, fg_color="transparent")
        hdr_row.pack(fill="x", padx=5, pady=(0, 4))

        ctk.CTkLabel(
            hdr_row,
            text=f"Welcome, {self.shop_name}",
            font=ctk.CTkFont(family="Arial", size=24, weight="bold"),
            text_color="#ffffff"
        ).pack(side="left", anchor="w")

        self.lbl_time = ctk.CTkLabel(
            hdr_row, text="",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color="#555560"
        )
        self.lbl_time.pack(side="right", anchor="e", padx=4)
        self._tick_clock()

        ctk.CTkLabel(
            self,
            text="Here's a quick overview of your business performance.",
            font=ctk.CTkFont(family="Arial", size=13),
            text_color="#8a8a93"
        ).pack(anchor="w", padx=5, pady=(0, 16))

        # ── SCROLLABLE BODY ───────────────────────────────────────────────────
        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True)

        self._build_body()

    # ── CLOCK ─────────────────────────────────────────────────────────────────
    def _tick_clock(self):
        now = datetime.now().strftime("%A, %d %B %Y   %I:%M %p")
        self.lbl_time.configure(text=now)
        self.after(30000, self._tick_clock)

    # ── BODY BUILD ────────────────────────────────────────────────────────────
    def _build_body(self):
        today   = get_today_summary()
        summary = get_dashboard_summary()

        # ── SECTION LABEL: TODAY ──────────────────────────────────────────────
        self._section_label("📅  Today's Overview")

        today_row = ctk.CTkFrame(self.scroll, fg_color="transparent")
        today_row.pack(fill="x", padx=5, pady=(0, 20))
        today_row.grid_columnconfigure((0, 1, 2, 3, 4), weight=1, uniform="today")

        self._stat_card(today_row, 0,
                        "Today Revenue",
                        f"Rs {today['today_revenue']:,.2f}",
                        "#4a90e2", "💰",
                        sub=f"{today['today_invoices']} invoice{'s' if today['today_invoices'] != 1 else ''}")

        self._stat_card(today_row, 1,
                        "Today Profit",
                        f"Rs {today['today_profit']:,.2f}",
                        "#4aff8a", "📈",
                        sub=self._margin_str(today['today_profit'], today['today_revenue']))

        self._stat_card(today_row, 2,
                        "Today Invoices",
                        str(today['today_invoices']),
                        "#f5a623", "🧾",
                        sub="Bills created today")

        cash_in_color = "#4aff8a"
        self._stat_card(today_row, 3,
                        "Cash In  (Today)",
                        f"Rs {today['cash_in']:,.2f}",
                        cash_in_color, "⬇️",
                        sub="Revenue received")

        cash_out_color = "#ff6b6b"
        breakdown = []
        if today['today_household'] > 0:
            breakdown.append(f"Ghar: Rs {today['today_household']:,.0f}")
        if today['today_udhaar_out'] > 0:
            breakdown.append(f"Udhaar: Rs {today['today_udhaar_out']:,.0f}")
        cash_out_sub = "  •  ".join(breakdown) if breakdown else "Koi kharch nahi"

        self._stat_card(today_row, 4,
                        "Cash Out  (Today)",
                        f"Rs {today['cash_out']:,.2f}",
                        cash_out_color, "⬆️",
                        sub=cash_out_sub)

        # ── SECTION LABEL: ALL TIME ───────────────────────────────────────────
        self._section_label("📊  All-Time Performance")

        all_row = ctk.CTkFrame(self.scroll, fg_color="transparent")
        all_row.pack(fill="x", padx=5, pady=(0, 20))
        all_row.grid_columnconfigure((0, 1, 2, 3), weight=1, uniform="alltime")

        self._stat_card(all_row, 0, "Total Revenue",
                        f"Rs. {summary['total_revenue']:,.2f}", "#4a90e2", "📦")
        self._stat_card(all_row, 1, "Total Profit",
                        f"Rs. {summary['total_profit']:,.2f}", "#4aff8a", "💹")
        self._stat_card(all_row, 2, "Total Invoices",
                        str(summary['total_invoices']), "#f5a623", "🧾")
        self._stat_card(all_row, 3, "Low Stock Items",
                        str(summary['low_stock_count']), "#ff4a4a", "⚠️")

        # ── SECTION LABEL: KHATA ──────────────────────────────────────────────
        self._section_label("🏦  Khata / Wallet Summary")

        khata_row = ctk.CTkFrame(self.scroll, fg_color="transparent")
        khata_row.pack(fill="x", padx=5, pady=(0, 24))
        khata_row.grid_columnconfigure((0, 1, 2, 3), weight=1, uniform="khata")

        net = summary.get("net_wallet_total", 0.0)
        net_color = "#4aff8a" if net >= 0 else "#ff4a4a"
        net_disp  = f"Rs. {net:,.2f}" if net >= 0 else f"-Rs. {abs(net):,.2f}"

        self._stat_card(khata_row, 0, "Net Wallet (All Khata)", net_disp, net_color, "💼")
        self._stat_card(khata_row, 1, "Total Advance (Credit)",
                        f"Rs. {summary.get('total_advance', 0):,.2f}", "#4aff8a", "✅")
        self._stat_card(khata_row, 2, "Total Udhaar (Debit)",
                        f"-Rs. {abs(summary.get('total_udhaar', 0)):,.2f}", "#ff4a4a", "❌")
        self._stat_card(khata_row, 3, "Total Khata Accounts",
                        str(summary.get("total_khatas", 0)), "#a78bfa", "👥")

        # ── CHART PANEL ───────────────────────────────────────────────────────
        chart_panel = ctk.CTkFrame(self.scroll, fg_color="#121214",
                                   border_color="#222227", border_width=1,
                                   corner_radius=8, height=400)
        chart_panel.pack(fill="x", padx=5, pady=(0, 10))

        ctk.CTkLabel(
            chart_panel,
            text="Revenue vs Profit Overview",
            font=ctk.CTkFont(family="Arial", size=16, weight="bold"),
            text_color="#ffffff"
        ).pack(anchor="w", padx=25, pady=(20, 5))

        chart_body = ctk.CTkFrame(chart_panel, fg_color="transparent")
        chart_body.pack(fill="both", expand=True, padx=25, pady=(5, 25))

        revenue = summary["total_revenue"]
        profit  = summary["total_profit"]

        if revenue <= 0 and profit <= 0:
            ctk.CTkLabel(
                chart_body,
                text="No sales data available yet.\nCreate invoices from the Billing Console to see analytics here.",
                font=ctk.CTkFont(family="Arial", size=13),
                text_color="#6e6e77", justify="center"
            ).pack(expand=True)
        else:
            self.canvas = ctk.CTkCanvas(chart_body, width=300, height=300,
                                        bg="#121214", highlightthickness=0)
            self.canvas.pack(side="left", padx=(0, 40), pady=10)

            cost_part = max(revenue - profit, 0)
            self._draw_pie([profit if profit > 0 else 0, cost_part if cost_part > 0 else 0],
                           ["#4aff8a", "#4a90e2"])

            legend_f = ctk.CTkFrame(chart_body, fg_color="transparent")
            legend_f.pack(side="left", fill="both", expand=True, pady=10)
            self._legend_row(legend_f, "#4a90e2", "Total Revenue", f"Rs. {revenue:,.2f}")
            self._legend_row(legend_f, "#4aff8a", "Total Profit",  f"Rs. {profit:,.2f}")
            margin = (profit / revenue * 100) if revenue > 0 else 0
            self._legend_row(legend_f, "#f5a623", "Profit Margin", f"{margin:.1f}%")

    # ── HELPERS ───────────────────────────────────────────────────────────────
    def _section_label(self, text):
        row = ctk.CTkFrame(self.scroll, fg_color="transparent")
        row.pack(fill="x", padx=5, pady=(4, 8))
        ctk.CTkLabel(row, text=text,
                     font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
                     text_color="#4a90e2").pack(side="left")
        ctk.CTkFrame(row, fg_color="#222230", height=1).pack(
            side="left", fill="x", expand=True, padx=(12, 0), pady=6)

    def _margin_str(self, profit, revenue):
        if revenue > 0:
            return f"Margin: {profit / revenue * 100:.1f}%"
        return "No sales yet"

    def _stat_card(self, parent, col, title, value, accent, icon="", sub=None):
        card = ctk.CTkFrame(parent, fg_color="#121214",
                            border_color="#222227", border_width=1, corner_radius=8)
        card.grid(row=0, column=col, padx=6, pady=0, sticky="nsew")

        # Accent top bar
        ctk.CTkFrame(card, fg_color=accent, height=4, corner_radius=0).pack(fill="x", side="top")

        # Icon + title row
        top_row = ctk.CTkFrame(card, fg_color="transparent")
        top_row.pack(fill="x", padx=16, pady=(14, 0))
        if icon:
            ctk.CTkLabel(top_row, text=icon,
                         font=ctk.CTkFont(size=16), text_color=accent,
                         width=26).pack(side="left", padx=(0, 6))
        ctk.CTkLabel(top_row, text=title,
                     font=ctk.CTkFont(family="Arial", size=11),
                     text_color="#8a8a93", anchor="w").pack(side="left")

        # Value
        ctk.CTkLabel(card, text=value,
                     font=ctk.CTkFont(family="Arial", size=19, weight="bold"),
                     text_color="#ffffff").pack(anchor="w", padx=16, pady=(4, 0))

        # Sub-label
        if sub:
            ctk.CTkLabel(card, text=sub,
                         font=ctk.CTkFont(family="Segoe UI", size=10),
                         text_color="#555568").pack(anchor="w", padx=16, pady=(2, 12))
        else:
            ctk.CTkFrame(card, fg_color="transparent", height=12).pack()

    # backward-compat (kept in case anything calls old name)
    def create_stat_card(self, parent, col, title, value, accent):
        self._stat_card(parent, col, title, value, accent)

    def _legend_row(self, parent, color, label, value):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=10, anchor="w")
        ctk.CTkFrame(row, fg_color=color, width=16, height=16, corner_radius=3).pack(side="left", padx=(0, 12))
        tf = ctk.CTkFrame(row, fg_color="transparent")
        tf.pack(side="left", fill="x", expand=True)
        ctk.CTkLabel(tf, text=label, font=ctk.CTkFont(family="Arial", size=12), text_color="#8a8a93").pack(anchor="w")
        ctk.CTkLabel(tf, text=value, font=ctk.CTkFont(family="Arial", size=16, weight="bold"), text_color="#ffffff").pack(anchor="w")

    # kept for compat
    def create_legend_row(self, parent, color, label, value):
        self._legend_row(parent, color, label, value)

    def _draw_pie(self, values, colors):
        total = sum(values)
        if total <= 0:
            return
        size, padding = 300, 20
        x0, y0, x1, y1 = padding, padding, size - padding, size - padding
        start = 90
        for v, c in zip(values, colors):
            if v <= 0:
                continue
            ext = (v / total) * 360
            self.canvas.create_arc(x0, y0, x1, y1, start=start, extent=-ext,
                                   fill=c, outline="#121214", width=2, style="pieslice")
            start -= ext
        hp = 65
        self.canvas.create_oval(padding + hp, padding + hp,
                                size - padding - hp, size - padding - hp,
                                fill="#121214", outline="#121214")
        self.canvas.create_text(size / 2, size / 2 - 10, text="Revenue",
                                fill="#8a8a93", font=("Arial", 11))
        self.canvas.create_text(size / 2, size / 2 + 12, text="Breakdown",
                                fill="#ffffff", font=("Arial", 13, "bold"))

    # kept for compat
    def draw_pie_chart(self, canvas, values, colors, labels):
        self.canvas = canvas
        self._draw_pie(values, colors)
