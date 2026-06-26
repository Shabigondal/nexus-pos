import customtkinter as ctk
import threading
import time
import tkinter.messagebox as messagebox
import webbrowser
from modules.auth import AuthWindow
from modules.activation_window import ActivationWindow
from modules.license_manager import is_activated
from modules.inventory import InventoryView
from modules.billing import BillingView
from modules.analytical_reports import AnalyticalReportsView
from modules.credit_ledger import CreditLedgerView
from modules.dashboard import DashboardView
from modules.settings import SettingsView
from modules.product_daily_report import ProductDailyReportView
from modules.dealer_view import DealerView
from modules.household_expenses import HouseholdExpensesView
from modules.update_checker import check_for_update, CURRENT_VERSION
from modules.backup_manager import sync_db_to_drive
from database.db_manager import get_setting

ctk.set_appearance_mode("Dark")

class EnterpriseBillingApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Nexus POS & Inventory Control Workspace")
        self.geometry("1280x768")
        self.minsize(1100, 680)

        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        pos_x = int(screen_width/2 - 1280/2)
        pos_y = int(screen_height/2 - 768/2)
        self.geometry(f"1280x768+{pos_x}+{pos_y}")

        # Session State
        self.current_username = "Administrator"

        # Security Execution Context Initialization
        self.withdraw()
        if is_activated():
            self.security_gate = AuthWindow(self, on_success=self.initialize_system)
        else:
            self.activation_gate = ActivationWindow(self, on_success=self.launch_login_gate)

    def launch_login_gate(self):
        """Called once activation succeeds - proceeds to the normal login screen."""
        self.security_gate = AuthWindow(self, on_success=self.initialize_system)

    def initialize_system(self, username=None):
        if username:
            self.current_username = username
        self.deiconify()
        self.render_application_shell()
        # Silent background check for new releases (non-blocking)
        self.after(1500, self.run_startup_update_check)
        # Start the 24-hour silent Google Drive auto-sync loop
        self.start_drive_auto_sync()

    def start_drive_auto_sync(self):
        """Runs sync_db_to_drive() once now, then every 24 hours, on a background thread."""
        SYNC_INTERVAL_SECONDS = 24 * 60 * 60  # 24 hours

        def _loop():
            while True:
                sync_db_to_drive()
                time.sleep(SYNC_INTERVAL_SECONDS)

        threading.Thread(target=_loop, daemon=True).start()

    def run_startup_update_check(self):
        threading.Thread(target=self._check_update_background, daemon=True).start()

    def _check_update_background(self):
        result = check_for_update()
        if result["status"] == "update_available":
            self.after(0, lambda: self._show_update_popup(result))

    def _show_update_popup(self, result):
        latest = result["latest_version"]
        link = result.get("download_url") or result.get("release_url")

        choice = messagebox.askyesno(
            "Update Available",
            f"A new version of Nexus POS is available: {latest}\n"
            f"(You are currently using {CURRENT_VERSION})\n\n"
            f"Do you want to open the download page now?"
        )
        if choice and link:
            webbrowser.open(link)

    def render_application_shell(self):
        # --- SIDE PANEL CONTAINER NAVIGATION ---
        self.side_panel = ctk.CTkFrame(self, width=240, corner_radius=0, fg_color="#16161a", border_color="#222227", border_width=1)
        self.side_panel.pack(side="left", fill="y")

        self.brand_lbl = ctk.CTkLabel(self.side_panel, text="NEXUS INDUSTRIAL",
                                      font=ctk.CTkFont(family="Arial", size=15, weight="bold"), text_color="#4a90e2")
        self.brand_lbl.pack(padx=25, pady=35, anchor="w")

        # Menu Links (Ab commands perfectly lambda wrap ke sath direct route hoti hain)
        self.create_menu_item("Dashboard", lambda: self.route_dashboard())
        self.create_menu_item("Billing Console", lambda: self.route_billing())
        self.create_menu_item("Inventory Control", lambda: self.route_inventory())
        self.create_menu_item("Credit Ledger (Khata)", lambda: self.route_khata())
        self.create_menu_item("Analytical Reports", lambda: self.route_reports())
        self.create_menu_item("Product Daily Report", lambda: self.route_product_daily_report())
        self.create_menu_item("Dealer Management", lambda: self.route_dealers())
        self.create_menu_item("Household Expenses", lambda: self.route_household_expenses())
        self.create_menu_item("System Configuration", lambda: self.route_settings())

        self.status_lbl = ctk.CTkLabel(self.side_panel, text=f"Engine State: {CURRENT_VERSION}",
                                       font=ctk.CTkFont(family="Arial", size=11), text_color="#6e6e77")
        self.status_lbl.pack(side="bottom", pady=25)

        # --- PRIMARY ISOLATED WORKSPACE ---
        self.workspace = ctk.CTkFrame(self, corner_radius=0, fg_color="#0c0c0e")
        self.workspace.pack(side="right", fill="both", expand=True)

        self.route_dashboard()

    def create_menu_item(self, label_text, routing_command):
        btn = ctk.CTkButton(self.side_panel, text=label_text, height=42, corner_radius=0,
                            fg_color="transparent", text_color="#a0a0a9", hover_color="#1f1f24",
                            anchor="w", font=ctk.CTkFont(family="Arial", size=13, weight="normal"),
                            command=routing_command)
        btn.pack(padx=5, pady=2, fill="x")

    def reset_workspace(self):
        for widget in self.workspace.winfo_children():
            widget.destroy()

    # --- ARCHITECTURE CONTROLLER ROUTING MODULES ---
    def route_dashboard(self):
        self.reset_workspace()

        dashboard_panel = DashboardView(self.workspace)
        dashboard_panel.pack(fill="both", expand=True, padx=30, pady=(25, 30))

    def route_billing(self):
        self.reset_workspace()
        header = ctk.CTkLabel(self.workspace, text="Billing Console System Workspace", font=ctk.CTkFont(family="Arial", size=20, weight="bold"), text_color="#ffffff")
        header.pack(anchor="w", padx=30, pady=(25, 10))

        billing_panel = BillingView(self.workspace)
        billing_panel.pack(fill="both", expand=True, padx=30, pady=(0, 30))

    def route_inventory(self):
        self.reset_workspace()
        header = ctk.CTkLabel(self.workspace, text="Inventory Master Data Control Panel", font=ctk.CTkFont(family="Arial", size=20, weight="bold"), text_color="#ffffff")
        header.pack(anchor="w", padx=30, pady=(25, 10))

        inventory_panel = InventoryView(self.workspace)
        inventory_panel.pack(fill="both", expand=True, padx=30, pady=(0, 30))

    def route_khata(self):
        """⚡ FIXED & CLEANED: Khata Module mounts seamlessly on self.workspace like other views"""
        self.reset_workspace()
        header = ctk.CTkLabel(self.workspace, text="Credit Ledger & Khata Management Terminal", font=ctk.CTkFont(family="Arial", size=20, weight="bold"), text_color="#ffffff")
        header.pack(anchor="w", padx=30, pady=(25, 10))

        # Injected onto the verified local self.workspace
        ledger_panel = CreditLedgerView(self.workspace)
        ledger_panel.pack(fill="both", expand=True, padx=30, pady=(0, 30))

    def route_reports(self):
        """⚡ FIXED MAP: This function mounts the full professional Invoice Auditing History Panel"""
        self.reset_workspace()
        header = ctk.CTkLabel(self.workspace, text="Invoices Auditing History Ledger", font=ctk.CTkFont(family="Arial", size=20, weight="bold"), text_color="#ffffff")
        header.pack(anchor="w", padx=30, pady=(25, 10))

        # Injecting the advanced tracking grid dashboard view components
        invoice_ledger_panel = AnalyticalReportsView(self.workspace)
        invoice_ledger_panel.pack(fill="both", expand=True, padx=30, pady=(0, 30))

    def route_product_daily_report(self):
        self.reset_workspace()
        header = ctk.CTkLabel(self.workspace, text="Product Daily / Period Report", font=ctk.CTkFont(family="Arial", size=20, weight="bold"), text_color="#ffffff")
        header.pack(anchor="w", padx=30, pady=(25, 10))

        report_panel = ProductDailyReportView(self.workspace)
        report_panel.pack(fill="both", expand=True, padx=30, pady=(0, 30))

    def route_dealers(self):
        self.reset_workspace()
        header = ctk.CTkLabel(self.workspace, text="Dealer Management Panel",
                              font=ctk.CTkFont(family="Arial", size=20, weight="bold"), text_color="#ffffff")
        header.pack(anchor="w", padx=30, pady=(25, 10))
        dealer_panel = DealerView(self.workspace)
        dealer_panel.pack(fill="both", expand=True, padx=30, pady=(0, 30))

    def route_household_expenses(self):
        self.reset_workspace()
        header = ctk.CTkLabel(self.workspace, text="Household Expenses Manager",
                              font=ctk.CTkFont(family="Arial", size=20, weight="bold"), text_color="#ffffff")
        header.pack(anchor="w", padx=30, pady=(25, 10))
        expense_panel = HouseholdExpensesView(self.workspace)
        expense_panel.pack(fill="both", expand=True, padx=30, pady=(0, 30))

    def route_settings(self):
        self.reset_workspace()
        header = ctk.CTkLabel(self.workspace, text="System Configuration", font=ctk.CTkFont(family="Arial", size=22, weight="bold"), text_color="#ffffff")
        header.pack(anchor="w", padx=30, pady=(25, 10))

        settings_panel = SettingsView(self.workspace, current_username=self.current_username,
                                       on_profile_updated=self.on_profile_updated)
        settings_panel.pack(fill="both", expand=True, padx=30, pady=(0, 30))

    def on_profile_updated(self):
        """Called when shop profile (name/logo/footer) is saved, so brand label can refresh if needed."""
        pass

if __name__ == "__main__":
    # --- AUTO-INITIALIZE LEDGER TABLES BEFORE APP LAUNCH ---
    try:
        import database.db_manager as db
        # Agar function ka naam thora badal diya ho toh verification ke liye database file zaroor check kar lena
        if hasattr(db, 'CRITICAL_init_ledger_tables'):
            db.CRITICAL_init_ledger_tables()
            print(" Ledger tables verified successfully.")
    except Exception as e:
        print(f"⚠️ Warning during ledger initialization: {e}")

    # App start karne ka original execution logic
    app = EnterpriseBillingApp()
    app.mainloop()