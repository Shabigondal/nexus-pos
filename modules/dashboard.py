import customtkinter as ctk
import math
from database.db_manager import get_dashboard_summary, get_setting


class DashboardView(ctk.CTkFrame):
    """Professional welcome dashboard: shop name greeting, summary stat cards, and a Revenue vs Profit pie chart."""

    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")

        shop_name = get_setting("shop_name", "Afzal Petrol Agency")
        summary = get_dashboard_summary()

        # --- WELCOME HEADER ---
        welcome_lbl = ctk.CTkLabel(
            self,
            text=f"Welcome, {shop_name}",
            font=ctk.CTkFont(family="Arial", size=24, weight="bold"),
            text_color="#ffffff"
        )
        welcome_lbl.pack(anchor="w", padx=5, pady=(0, 5))

        sub_lbl = ctk.CTkLabel(
            self,
            text="Here's a quick overview of your business performance.",
            font=ctk.CTkFont(family="Arial", size=13),
            text_color="#8a8a93"
        )
        sub_lbl.pack(anchor="w", padx=5, pady=(0, 20))

        # --- SCROLLABLE CONTENT (cards + chart) ---
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        # --- STAT CARDS ROW ---
        cards_row = ctk.CTkFrame(scroll, fg_color="transparent")
        cards_row.pack(fill="x", padx=5, pady=(0, 25))
        cards_row.grid_columnconfigure((0, 1, 2, 3), weight=1, uniform="cards")

        self.create_stat_card(cards_row, 0, "Total Revenue", f"Rs. {summary['total_revenue']:,.2f}", "#4a90e2")
        self.create_stat_card(cards_row, 1, "Total Profit", f"Rs. {summary['total_profit']:,.2f}", "#4aff8a")
        self.create_stat_card(cards_row, 2, "Total Invoices", f"{summary['total_invoices']}", "#f5a623")
        self.create_stat_card(cards_row, 3, "Low Stock Items", f"{summary['low_stock_count']}", "#ff4a4a")

        # --- KHATA / WALLET STAT CARDS ROW ---
        khata_cards_row = ctk.CTkFrame(scroll, fg_color="transparent")
        khata_cards_row.pack(fill="x", padx=5, pady=(0, 25))
        khata_cards_row.grid_columnconfigure((0, 1, 2, 3), weight=1, uniform="khata_cards")

        net_wallet_total = summary.get('net_wallet_total', 0.0)
        total_advance = summary.get('total_advance', 0.0)
        total_udhaar = summary.get('total_udhaar', 0.0)

        net_wallet_color = "#4aff8a" if net_wallet_total >= 0 else "#ff4a4a"
        net_wallet_display = f"Rs. {net_wallet_total:,.2f}" if net_wallet_total >= 0 else f"-Rs. {abs(net_wallet_total):,.2f}"

        self.create_stat_card(khata_cards_row, 0, "Net Wallet (All Khata)", net_wallet_display, net_wallet_color)
        self.create_stat_card(khata_cards_row, 1, "Total Advance (Credit)", f"Rs. {total_advance:,.2f}", "#4aff8a")
        self.create_stat_card(khata_cards_row, 2, "Total Udhaar (Debit)", f"-Rs. {abs(total_udhaar):,.2f}", "#ff4a4a")
        self.create_stat_card(khata_cards_row, 3, "Total Khata Accounts", f"{summary.get('total_khatas', 0)}", "#a78bfa")

        # --- CHART PANEL ---
        chart_panel = ctk.CTkFrame(scroll, fg_color="#121214", border_color="#222227", border_width=1, corner_radius=8, height=400)
        chart_panel.pack(fill="x", padx=5, pady=(0, 10))

        chart_title = ctk.CTkLabel(
            chart_panel,
            text="Revenue vs Profit Overview",
            font=ctk.CTkFont(family="Arial", size=16, weight="bold"),
            text_color="#ffffff"
        )
        chart_title.pack(anchor="w", padx=25, pady=(20, 5))

        chart_body = ctk.CTkFrame(chart_panel, fg_color="transparent")
        chart_body.pack(fill="both", expand=True, padx=25, pady=(5, 25))

        revenue = summary['total_revenue']
        profit = summary['total_profit']

        if revenue <= 0 and profit <= 0:
            empty_lbl = ctk.CTkLabel(
                chart_body,
                text="No sales data available yet.\nCreate invoices from the Billing Console to see analytics here.",
                font=ctk.CTkFont(family="Arial", size=13),
                text_color="#6e6e77",
                justify="center"
            )
            empty_lbl.pack(expand=True)
        else:
            # Pie chart canvas (left)
            self.canvas = ctk.CTkCanvas(chart_body, width=300, height=300, bg="#121214", highlightthickness=0)
            self.canvas.pack(side="left", padx=(0, 40), pady=10)

            cost_or_remainder = max(revenue - profit, 0)

            self.draw_pie_chart(
                self.canvas,
                values=[profit if profit > 0 else 0, cost_or_remainder if cost_or_remainder > 0 else 0],
                colors=["#4aff8a", "#4a90e2"],
                labels=["Profit", "Revenue (Cost Portion)"]
            )

            # Legend / breakdown (right)
            legend_frame = ctk.CTkFrame(chart_body, fg_color="transparent")
            legend_frame.pack(side="left", fill="both", expand=True, pady=10)

            self.create_legend_row(legend_frame, "#4a90e2", "Total Revenue", f"Rs. {revenue:,.2f}")
            self.create_legend_row(legend_frame, "#4aff8a", "Total Profit", f"Rs. {profit:,.2f}")

            if revenue > 0:
                margin = (profit / revenue) * 100
            else:
                margin = 0
            self.create_legend_row(legend_frame, "#f5a623", "Profit Margin", f"{margin:.1f}%")

    def create_stat_card(self, parent, col, title, value, accent_color):
        card = ctk.CTkFrame(parent, fg_color="#121214", border_color="#222227", border_width=1, corner_radius=8)
        card.grid(row=0, column=col, padx=8, pady=0, sticky="nsew")

        accent_bar = ctk.CTkFrame(card, fg_color=accent_color, height=4, corner_radius=0)
        accent_bar.pack(fill="x", side="top")

        title_lbl = ctk.CTkLabel(card, text=title, font=ctk.CTkFont(family="Arial", size=12), text_color="#8a8a93")
        title_lbl.pack(anchor="w", padx=18, pady=(18, 4))

        value_lbl = ctk.CTkLabel(card, text=value, font=ctk.CTkFont(family="Arial", size=20, weight="bold"), text_color="#ffffff")
        value_lbl.pack(anchor="w", padx=18, pady=(0, 18))

    def create_legend_row(self, parent, color, label, value):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=10, anchor="w")

        swatch = ctk.CTkFrame(row, fg_color=color, width=16, height=16, corner_radius=3)
        swatch.pack(side="left", padx=(0, 12))

        text_frame = ctk.CTkFrame(row, fg_color="transparent")
        text_frame.pack(side="left", fill="x", expand=True)

        lbl = ctk.CTkLabel(text_frame, text=label, font=ctk.CTkFont(family="Arial", size=12), text_color="#8a8a93")
        lbl.pack(anchor="w")

        val = ctk.CTkLabel(text_frame, text=value, font=ctk.CTkFont(family="Arial", size=16, weight="bold"), text_color="#ffffff")
        val.pack(anchor="w")

    def draw_pie_chart(self, canvas, values, colors, labels):
        """Draws a simple pie/donut chart using arcs on a CTkCanvas."""
        total = sum(values)
        if total <= 0:
            return

        size = 300
        padding = 20
        x0, y0, x1, y1 = padding, padding, size - padding, size - padding

        start_angle = 90  # start from the top
        for value, color in zip(values, colors):
            if value <= 0:
                continue
            extent = (value / total) * 360
            canvas.create_arc(
                x0, y0, x1, y1,
                start=start_angle,
                extent=-extent,
                fill=color,
                outline="#121214",
                width=2,
                style="pieslice"
            )
            start_angle -= extent

        # Donut hole in the center for a clean modern look
        hole_padding = 65
        canvas.create_oval(
            padding + hole_padding, padding + hole_padding,
            size - padding - hole_padding, size - padding - hole_padding,
            fill="#121214", outline="#121214"
        )

        # Center label
        canvas.create_text(
            size / 2, size / 2 - 10,
            text="Revenue",
            fill="#8a8a93",
            font=("Arial", 11)
        )
        canvas.create_text(
            size / 2, size / 2 + 12,
            text="Breakdown",
            fill="#ffffff",
            font=("Arial", 13, "bold")
        )