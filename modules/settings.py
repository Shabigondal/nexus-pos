import customtkinter as ctk
import tkinter.filedialog as filedialog
import tkinter.messagebox as messagebox
import shutil
import os
import webbrowser

from database.db_manager import (
    get_all_settings, set_settings_bulk,
    update_username, update_user_password
)
from modules.backup_manager import (
    backup_to_local, restore_from_local, upload_to_drive
)
from modules.update_checker import check_for_update, CURRENT_VERSION

ASSETS_DIR = os.path.join("assets")
PAPER_SIZES = ["58mm", "80mm"]


class SettingsView(ctk.CTkFrame):
    """Full System Configuration workspace: Account, Shop Profile, Printer Setup, and Software Update."""

    def __init__(self, parent, current_username, on_profile_updated=None):
        super().__init__(parent, fg_color="transparent")

        self.current_username = current_username
        self.on_profile_updated = on_profile_updated
        self.settings = get_all_settings()
        self.selected_logo_path = self.settings.get("logo_path", "")

        # Scrollable container so all sections fit on smaller screens
        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True)

        self.build_account_section()
        self.build_shop_profile_section()
        self.build_printer_section()
        self.build_backup_section()
        self.build_update_section()

    # =================================================================
    # SECTION 1: ACCOUNT SETTINGS (Username / Password)
    # =================================================================
    def build_account_section(self):
        panel = self.create_section_panel("Account Settings", "Manage your login username and password.")

        grid = ctk.CTkFrame(panel, fg_color="transparent")
        grid.pack(fill="x", padx=30, pady=(5, 25))

        # --- Username ---
        lbl_username = ctk.CTkLabel(grid, text="Username", font=ctk.CTkFont(size=12), text_color="#8a8a93")
        lbl_username.grid(row=0, column=0, sticky="w", pady=(0, 4))

        self.username_entry = ctk.CTkEntry(grid, width=320, height=38, fg_color="#0c0c0e",
                                            border_color="#333339", corner_radius=4)
        self.username_entry.insert(0, self.current_username)
        self.username_entry.grid(row=1, column=0, sticky="w", pady=(0, 15))

        btn_username = ctk.CTkButton(grid, text="Update Username", width=180, height=38,
                                      fg_color="#1f293d", hover_color="#2d3d5a",
                                      font=ctk.CTkFont(weight="bold"), command=self.handle_update_username)
        btn_username.grid(row=1, column=1, sticky="w", padx=(15, 0), pady=(0, 15))

        # --- Password Change ---
        lbl_pw_title = ctk.CTkLabel(grid, text="Change Password", font=ctk.CTkFont(size=12), text_color="#8a8a93")
        lbl_pw_title.grid(row=2, column=0, sticky="w", pady=(10, 4))

        self.old_password_entry = ctk.CTkEntry(grid, placeholder_text="Current Password", show="*", width=320,
                                                 height=38, fg_color="#0c0c0e", border_color="#333339", corner_radius=4)
        self.old_password_entry.grid(row=3, column=0, sticky="w", pady=4)

        self.new_password_entry = ctk.CTkEntry(grid, placeholder_text="New Password", show="*", width=320,
                                                height=38, fg_color="#0c0c0e", border_color="#333339", corner_radius=4)
        self.new_password_entry.grid(row=4, column=0, sticky="w", pady=4)

        self.confirm_password_entry = ctk.CTkEntry(grid, placeholder_text="Confirm New Password", show="*", width=320,
                                                     height=38, fg_color="#0c0c0e", border_color="#333339", corner_radius=4)
        self.confirm_password_entry.grid(row=5, column=0, sticky="w", pady=4)

        btn_password = ctk.CTkButton(grid, text="Update Password", width=180, height=38,
                                      fg_color="#1f293d", hover_color="#2d3d5a",
                                      font=ctk.CTkFont(weight="bold"), command=self.handle_update_password)
        btn_password.grid(row=5, column=1, sticky="w", padx=(15, 0), pady=4)

        self.account_status_lbl = ctk.CTkLabel(grid, text="", font=ctk.CTkFont(size=12))
        self.account_status_lbl.grid(row=6, column=0, columnspan=2, sticky="w", pady=(10, 0))

    def handle_update_username(self):
        new_username = self.username_entry.get().strip()
        if not new_username:
            self.account_status_lbl.configure(text="Username cannot be empty.", text_color="#ff4a4a")
            return

        if new_username == self.current_username:
            self.account_status_lbl.configure(text="This is already your current username.", text_color="orange")
            return

        success, msg = update_username(self.current_username, new_username)
        if success:
            self.current_username = new_username
            self.account_status_lbl.configure(text=msg, text_color="#4aff4a")
        else:
            self.account_status_lbl.configure(text=msg, text_color="#ff4a4a")

    def handle_update_password(self):
        old_pw = self.old_password_entry.get().strip()
        new_pw = self.new_password_entry.get().strip()
        confirm_pw = self.confirm_password_entry.get().strip()

        if not old_pw or not new_pw or not confirm_pw:
            self.account_status_lbl.configure(text="All password fields are required.", text_color="#ff4a4a")
            return

        if new_pw != confirm_pw:
            self.account_status_lbl.configure(text="New password and confirmation do not match.", text_color="#ff4a4a")
            return

        success, msg = update_user_password(self.current_username, old_pw, new_pw)
        if success:
            self.old_password_entry.delete(0, "end")
            self.new_password_entry.delete(0, "end")
            self.confirm_password_entry.delete(0, "end")
            self.account_status_lbl.configure(text=msg, text_color="#4aff4a")
        else:
            self.account_status_lbl.configure(text=msg, text_color="#ff4a4a")

    # =================================================================
    # SECTION 2: SHOP PROFILE (Shop Name / Logo / Footer Note)
    # =================================================================
    def build_shop_profile_section(self):
        panel = self.create_section_panel("Shop Profile", "Customize your business identity shown on invoices and the dashboard.")

        grid = ctk.CTkFrame(panel, fg_color="transparent")
        grid.pack(fill="x", padx=30, pady=(5, 25))

        # --- Shop Name ---
        lbl_shop = ctk.CTkLabel(grid, text="Shop / Business Name", font=ctk.CTkFont(size=12), text_color="#8a8a93")
        lbl_shop.grid(row=0, column=0, sticky="w", pady=(0, 4))

        self.shop_name_entry = ctk.CTkEntry(grid, width=320, height=38, fg_color="#0c0c0e",
                                             border_color="#333339", corner_radius=4)
        self.shop_name_entry.insert(0, self.settings.get("shop_name", "Afzal Petrol Agency"))
        self.shop_name_entry.grid(row=1, column=0, sticky="w", pady=(0, 15))

        # --- Logo Upload ---
        lbl_logo = ctk.CTkLabel(grid, text="Shop Logo", font=ctk.CTkFont(size=12), text_color="#8a8a93")
        lbl_logo.grid(row=2, column=0, sticky="w", pady=(10, 4))

        logo_row = ctk.CTkFrame(grid, fg_color="transparent")
        logo_row.grid(row=3, column=0, columnspan=2, sticky="w", pady=(0, 15))

        self.logo_preview_lbl = ctk.CTkLabel(logo_row, text="", width=80, height=80,
                                              fg_color="#0c0c0e", corner_radius=6)
        self.logo_preview_lbl.pack(side="left", padx=(0, 15))
        self.refresh_logo_preview()

        logo_btns = ctk.CTkFrame(logo_row, fg_color="transparent")
        logo_btns.pack(side="left")

        btn_upload_logo = ctk.CTkButton(logo_btns, text="Upload Logo", width=160, height=38,
                                         fg_color="#1f293d", hover_color="#2d3d5a",
                                         font=ctk.CTkFont(weight="bold"), command=self.handle_upload_logo)
        btn_upload_logo.pack(anchor="w", pady=(0, 6))

        btn_remove_logo = ctk.CTkButton(logo_btns, text="Remove Logo", width=160, height=32,
                                         fg_color="transparent", border_width=1, border_color="#444",
                                         hover_color="#1f1f24", text_color="#a0a0a9",
                                         font=ctk.CTkFont(size=12), command=self.handle_remove_logo)
        btn_remove_logo.pack(anchor="w")

        self.logo_hint_lbl = ctk.CTkLabel(grid, text="If no logo is uploaded, the shop name will be shown on invoices instead.",
                                           font=ctk.CTkFont(size=11), text_color="#6e6e77")
        self.logo_hint_lbl.grid(row=4, column=0, columnspan=2, sticky="w", pady=(0, 15))

        # --- Footer Note ---
        lbl_footer = ctk.CTkLabel(grid, text="Invoice Footer Note", font=ctk.CTkFont(size=12), text_color="#8a8a93")
        lbl_footer.grid(row=5, column=0, sticky="w", pady=(10, 4))

        self.footer_note_entry = ctk.CTkEntry(grid, width=480, height=38, fg_color="#0c0c0e",
                                               border_color="#333339", corner_radius=4)
        self.footer_note_entry.insert(0, self.settings.get("footer_note", "System generated invoice. Thank you for your business!"))
        self.footer_note_entry.grid(row=6, column=0, columnspan=2, sticky="w", pady=(0, 15))

        btn_save_profile = ctk.CTkButton(grid, text="Save Shop Profile", width=180, height=38,
                                          fg_color="#1f293d", hover_color="#2d3d5a",
                                          font=ctk.CTkFont(weight="bold"), command=self.handle_save_profile)
        btn_save_profile.grid(row=7, column=0, sticky="w", pady=(5, 0))

        self.profile_status_lbl = ctk.CTkLabel(grid, text="", font=ctk.CTkFont(size=12))
        self.profile_status_lbl.grid(row=7, column=1, sticky="w", padx=(15, 0), pady=(5, 0))

    def refresh_logo_preview(self):
        """Refresh the small logo preview box. Uses CTkImage if Pillow is available, otherwise shows placeholder text."""
        if self.selected_logo_path and os.path.exists(self.selected_logo_path):
            try:
                from PIL import Image
                img = Image.open(self.selected_logo_path)
                ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(72, 72))
                self.logo_preview_lbl.configure(image=ctk_img, text="")
                self.logo_preview_lbl.image = ctk_img  # keep reference to avoid garbage collection
                return
            except Exception:
                pass

        self.logo_preview_lbl.configure(image=None, text="No Logo", text_color="#6e6e77",
                                         font=ctk.CTkFont(size=11))

    def handle_upload_logo(self):
        file_path = filedialog.askopenfilename(
            title="Select Shop Logo",
            filetypes=[("Image Files", "*.png *.jpg *.jpeg *.bmp *.gif")]
        )
        if not file_path:
            return

        try:
            os.makedirs(ASSETS_DIR, exist_ok=True)
            _, ext = os.path.splitext(file_path)
            destination = os.path.join(ASSETS_DIR, f"shop_logo{ext.lower()}")
            shutil.copy(file_path, destination)

            self.selected_logo_path = destination
            self.refresh_logo_preview()
            self.profile_status_lbl.configure(text="Logo selected. Click 'Save Shop Profile' to apply.", text_color="#4a90e2")
        except Exception as e:
            self.profile_status_lbl.configure(text=f"Logo upload failed: {str(e)}", text_color="#ff4a4a")

    def handle_remove_logo(self):
        self.selected_logo_path = ""
        self.refresh_logo_preview()
        self.profile_status_lbl.configure(text="Logo removed. Click 'Save Shop Profile' to apply.", text_color="orange")

    def handle_save_profile(self):
        shop_name = self.shop_name_entry.get().strip()
        footer_note = self.footer_note_entry.get().strip()

        if not shop_name:
            self.profile_status_lbl.configure(text="Shop name cannot be empty.", text_color="#ff4a4a")
            return

        success, msg = set_settings_bulk({
            "shop_name": shop_name,
            "logo_path": self.selected_logo_path,
            "footer_note": footer_note
        })

        if success:
            self.settings = get_all_settings()
            self.profile_status_lbl.configure(text=msg, text_color="#4aff4a")
            if self.on_profile_updated:
                self.on_profile_updated()
        else:
            self.profile_status_lbl.configure(text=msg, text_color="#ff4a4a")

    # =================================================================
    # SECTION 3: THERMAL PRINTER SETUP
    # =================================================================
    def build_printer_section(self):
        panel = self.create_section_panel("Thermal Printer Setup", "Detect and configure the receipt printer connected to this system.")

        grid = ctk.CTkFrame(panel, fg_color="transparent")
        grid.pack(fill="x", padx=30, pady=(5, 25))

        # --- Detect Printer ---
        lbl_printer = ctk.CTkLabel(grid, text="Connected Printer", font=ctk.CTkFont(size=12), text_color="#8a8a93")
        lbl_printer.grid(row=0, column=0, sticky="w", pady=(0, 4))

        printer_row = ctk.CTkFrame(grid, fg_color="transparent")
        printer_row.grid(row=1, column=0, columnspan=2, sticky="w", pady=(0, 15))

        saved_printer = self.settings.get("printer_name", "")
        detected = self.detect_printers()
        options = detected if detected else ["No printers detected"]
        if saved_printer and saved_printer not in options:
            options = [saved_printer] + options

        self.printer_dropdown = ctk.CTkComboBox(printer_row, values=options, width=320, height=38,
                                                  fg_color="#0c0c0e", border_color="#333339",
                                                  button_color="#1f293d", dropdown_fg_color="#1a1a1e")
        if saved_printer:
            self.printer_dropdown.set(saved_printer)
        elif options:
            self.printer_dropdown.set(options[0])
        self.printer_dropdown.pack(side="left", padx=(0, 15))

        btn_detect = ctk.CTkButton(printer_row, text="Detect Printers", width=160, height=38,
                                    fg_color="#1f293d", hover_color="#2d3d5a",
                                    font=ctk.CTkFont(weight="bold"), command=self.handle_detect_printers)
        btn_detect.pack(side="left")

        # --- Paper Size ---
        lbl_paper = ctk.CTkLabel(grid, text="Receipt Paper Size", font=ctk.CTkFont(size=12), text_color="#8a8a93")
        lbl_paper.grid(row=2, column=0, sticky="w", pady=(10, 4))

        self.paper_size_segment = ctk.CTkSegmentedButton(grid, values=PAPER_SIZES,
                                                          fg_color="#0c0c0e", selected_color="#1f293d",
                                                          selected_hover_color="#2d3d5a",
                                                          unselected_color="#0c0c0e")
        saved_paper = self.settings.get("printer_paper_size", "80mm")
        if saved_paper not in PAPER_SIZES:
            saved_paper = "80mm"
        self.paper_size_segment.set(saved_paper)
        self.paper_size_segment.grid(row=3, column=0, sticky="w", pady=(0, 15))

        paper_hint = ctk.CTkLabel(grid, text="58mm and 80mm are the most common thermal receipt printer widths.",
                                   font=ctk.CTkFont(size=11), text_color="#6e6e77")
        paper_hint.grid(row=4, column=0, columnspan=2, sticky="w", pady=(0, 15))

        btn_save_printer = ctk.CTkButton(grid, text="Save Printer Settings", width=180, height=38,
                                          fg_color="#1f293d", hover_color="#2d3d5a",
                                          font=ctk.CTkFont(weight="bold"), command=self.handle_save_printer)
        btn_save_printer.grid(row=5, column=0, sticky="w", pady=(5, 0))

        self.printer_status_lbl = ctk.CTkLabel(grid, text="", font=ctk.CTkFont(size=12))
        self.printer_status_lbl.grid(row=5, column=1, sticky="w", padx=(15, 0), pady=(5, 0))

    def detect_printers(self):
        """Detect printers installed on the system. Works on Windows via pywin32; returns [] elsewhere/on failure."""
        try:
            import win32print
            printers = win32print.EnumPrinters(win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS)
            return [p[2] for p in printers]
        except Exception:
            return []

    def handle_detect_printers(self):
        detected = self.detect_printers()
        if detected:
            self.printer_dropdown.configure(values=detected)
            self.printer_dropdown.set(detected[0])
            self.printer_status_lbl.configure(text=f"{len(detected)} printer(s) detected.", text_color="#4aff4a")
        else:
            self.printer_dropdown.configure(values=["No printers detected"])
            self.printer_dropdown.set("No printers detected")
            self.printer_status_lbl.configure(text="No printers found. Ensure printer drivers are installed.", text_color="orange")

    def handle_save_printer(self):
        printer_name = self.printer_dropdown.get().strip()
        paper_size = self.paper_size_segment.get()

        if printer_name == "No printers detected":
            printer_name = ""

        success, msg = set_settings_bulk({
            "printer_name": printer_name,
            "printer_paper_size": paper_size
        })

        if success:
            self.settings = get_all_settings()
            self.printer_status_lbl.configure(text="Printer configuration saved.", text_color="#4aff4a")
        else:
            self.printer_status_lbl.configure(text=msg, text_color="#ff4a4a")

    # =================================================================
    # SECTION 4: BACKUP & RESTORE
    # =================================================================
    def build_backup_section(self):
        panel = self.create_section_panel(
            "Backup & Restore",
            "Save a local backup, upload it to your Google Drive, or restore data from a backup file."
        )

        grid = ctk.CTkFrame(panel, fg_color="transparent")
        grid.pack(fill="x", padx=30, pady=(5, 25))

        self.backup_status_lbl = ctk.CTkLabel(grid, text="",
                                               font=ctk.CTkFont(size=12), text_color="gray")
        self.backup_status_lbl.pack(anchor="w", pady=(0, 10))

        btn_row = ctk.CTkFrame(grid, fg_color="transparent")
        btn_row.pack(anchor="w", fill="x")

        btn_backup_local = ctk.CTkButton(
            btn_row, text="Download Backup (.db)", width=200, height=38,
            fg_color="#1f293d", hover_color="#2d3d5a",
            font=ctk.CTkFont(weight="bold"), command=self.handle_backup_local
        )
        btn_backup_local.pack(side="left", padx=(0, 10))

        btn_backup_drive = ctk.CTkButton(
            btn_row, text="Upload to Google Drive", width=200, height=38,
            fg_color="#1f293d", hover_color="#2d3d5a",
            font=ctk.CTkFont(weight="bold"), command=self.handle_backup_drive
        )
        btn_backup_drive.pack(side="left", padx=(0, 10))

        btn_restore = ctk.CTkButton(
            btn_row, text="Import / Restore Backup", width=200, height=38,
            fg_color="#3d1f1f", hover_color="#5a2d2d",
            font=ctk.CTkFont(weight="bold"), command=self.handle_restore
        )
        btn_restore.pack(side="left")

    def handle_backup_local(self):
        self.backup_status_lbl.configure(text="Opening save dialog...", text_color="#4a90e2")
        self.update_idletasks()
        path = backup_to_local(self)
        if path:
            self.backup_status_lbl.configure(text=f"Backup saved: {path}", text_color="#4aff4a")
        else:
            self.backup_status_lbl.configure(text="Backup cancelled.", text_color="gray")

    def handle_backup_drive(self):
        self.backup_status_lbl.configure(text="Connecting to Google Drive...", text_color="#4a90e2")
        self.update_idletasks()
        success = upload_to_drive(self)
        if success:
            self.backup_status_lbl.configure(text="Backup uploaded to Google Drive.", text_color="#4aff4a")
        else:
            self.backup_status_lbl.configure(text="Drive upload cancelled or failed.", text_color="orange")

    def handle_restore(self):
        self.backup_status_lbl.configure(text="Select a backup file to restore...", text_color="#4a90e2")
        self.update_idletasks()
        restored = restore_from_local(self)
        if restored:
            self.backup_status_lbl.configure(text="Restore complete. Please restart the app.", text_color="#4aff4a")
        else:
            self.backup_status_lbl.configure(text="Restore cancelled.", text_color="gray")

    # =================================================================
    # SECTION 5: SOFTWARE UPDATE
    # =================================================================
    def build_update_section(self):
        panel = self.create_section_panel("Software Update", "Check for the latest application build.")

        grid = ctk.CTkFrame(panel, fg_color="transparent")
        grid.pack(fill="x", padx=30, pady=(5, 25))

        version_lbl = ctk.CTkLabel(grid, text=f"Installed Build: {CURRENT_VERSION}", font=ctk.CTkFont(size=14))
        version_lbl.pack(anchor="w", pady=(0, 5))

        self.update_status_lbl = ctk.CTkLabel(grid, text="Updates: System up to date.",
                                               font=ctk.CTkFont(size=12), text_color="gray")
        self.update_status_lbl.pack(anchor="w", pady=5)

        btn_check_update = ctk.CTkButton(grid, text="Check for Software Updates", fg_color="#1f293d",
                                          hover_color="#2d3d5a", height=38, font=ctk.CTkFont(weight="bold"),
                                          command=self.check_for_updates)
        btn_check_update.pack(anchor="w", pady=10)

    def check_for_updates(self):
        self.update_status_lbl.configure(text="Checking for updates...", text_color="#4a90e2")
        self.update_idletasks()

        result = check_for_update()

        if result["status"] == "update_available":
            self.update_status_lbl.configure(
                text=f"New version available: {result['latest_version']} (current: {CURRENT_VERSION})",
                text_color="#ff4a4a"
            )
            self._latest_release_url = result.get("download_url") or result.get("release_url")
            if not hasattr(self, "btn_download_update"):
                self.btn_download_update = ctk.CTkButton(
                    self.update_status_lbl.master, text="Download Update", fg_color="#1f6b3a",
                    hover_color="#27893f", height=34, font=ctk.CTkFont(weight="bold"),
                    command=self.open_update_link
                )
                self.btn_download_update.pack(anchor="w", pady=(5, 0))
            else:
                self.btn_download_update.pack(anchor="w", pady=(5, 0))

        elif result["status"] == "up_to_date":
            self.update_status_lbl.configure(text="You are running the latest version.", text_color="#4aff4a")
            if hasattr(self, "btn_download_update"):
                self.btn_download_update.pack_forget()

        else:
            self.update_status_lbl.configure(text=result["message"], text_color="orange")
            if hasattr(self, "btn_download_update"):
                self.btn_download_update.pack_forget()

    def open_update_link(self):
        url = getattr(self, "_latest_release_url", None)
        if url:
            webbrowser.open(url)

    # =================================================================
    # HELPERS
    # =================================================================
    def create_section_panel(self, title, subtitle):
        panel = ctk.CTkFrame(self.scroll, fg_color="#121214", border_color="#222227", border_width=1, corner_radius=4)
        panel.pack(fill="x", padx=5, pady=(0, 20))

        title_lbl = ctk.CTkLabel(panel, text=title, font=ctk.CTkFont(family="Arial", size=17, weight="bold"), text_color="#ffffff")
        title_lbl.pack(anchor="w", padx=30, pady=(20, 2))

        subtitle_lbl = ctk.CTkLabel(panel, text=subtitle, font=ctk.CTkFont(family="Arial", size=12), text_color="#8a8a93")
        subtitle_lbl.pack(anchor="w", padx=30, pady=(0, 10))

        return panel
