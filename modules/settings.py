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

# =====================================================================
# 🎨 PROFESSIONAL THEME PALETTE (matches Billing Console)
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
COL_WARNING     = "#f59e0b"
COL_TEXT_MAIN   = "#f1f5f9"
COL_TEXT_MUTED  = "#94a3b8"
COL_TEXT_SOFT   = "#64748b"

FONT_LABEL = ctk.CTkFont(size=12)
FONT_BOLD  = ctk.CTkFont(size=13, weight="bold")
FONT_HINT  = ctk.CTkFont(size=11)


class SettingsView(ctk.CTkFrame):
    """Full System Configuration workspace: Account, Shop Profile, Printer Setup, Backup, and Software Update."""

    def __init__(self, parent, current_username, on_profile_updated=None):
        super().__init__(parent, fg_color="transparent")

        self.current_username = current_username
        self.on_profile_updated = on_profile_updated
        self.settings = get_all_settings()
        self.selected_logo_path = self.settings.get("logo_path", "")

        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=2, pady=(0, 14))
        ctk.CTkLabel(header, text="⚙️  System Configuration", font=ctk.CTkFont(size=22, weight="bold"),
                     text_color=COL_TEXT_MAIN).pack(anchor="w")
        ctk.CTkLabel(header, text="Manage your account, shop profile, printer, backups, and updates.",
                     font=ctk.CTkFont(size=12), text_color=COL_TEXT_SOFT).pack(anchor="w", pady=(2, 0))

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
        panel = self.create_section_panel("👤", "Account Settings", "Manage your login username and password.")

        grid = ctk.CTkFrame(panel, fg_color="transparent")
        grid.pack(fill="x", padx=24, pady=(5, 22))
        grid.grid_columnconfigure(0, weight=1)
        grid.grid_columnconfigure(1, weight=1)

        # --- Username card ---
        user_card = self.create_inner_card(grid)
        user_card.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 16))

        self.field_label(user_card, "USERNAME").pack(anchor="w", padx=18, pady=(14, 4))
        u_row = ctk.CTkFrame(user_card, fg_color="transparent")
        u_row.pack(fill="x", padx=18, pady=(0, 14))

        self.username_entry = self.styled_entry(u_row, width=300)
        self.username_entry.insert(0, self.current_username)
        self.username_entry.pack(side="left", fill="x", expand=True, padx=(0, 12))

        self.accent_button(u_row, "Update Username", command=self.handle_update_username, width=170).pack(side="left")

        # --- Password card ---
        pw_card = self.create_inner_card(grid)
        pw_card.grid(row=1, column=0, columnspan=2, sticky="ew")

        pw_header = ctk.CTkFrame(pw_card, fg_color="transparent")
        pw_header.pack(fill="x", padx=18, pady=(14, 4))
        ctk.CTkLabel(pw_header, text="🔒 CHANGE PASSWORD", font=ctk.CTkFont(size=11, weight="bold"),
                     text_color=COL_TEXT_SOFT).pack(side="left")

        pw_fields = ctk.CTkFrame(pw_card, fg_color="transparent")
        pw_fields.pack(fill="x", padx=18, pady=(4, 14))
        pw_fields.grid_columnconfigure(0, weight=1)
        pw_fields.grid_columnconfigure(1, weight=1)
        pw_fields.grid_columnconfigure(2, weight=1)

        self.old_password_entry = self.styled_entry(pw_fields, placeholder="Current Password", show="*")
        self.old_password_entry.grid(row=0, column=0, sticky="ew", padx=(0, 8), pady=4)

        self.new_password_entry = self.styled_entry(pw_fields, placeholder="New Password", show="*")
        self.new_password_entry.grid(row=0, column=1, sticky="ew", padx=8, pady=4)

        self.confirm_password_entry = self.styled_entry(pw_fields, placeholder="Confirm New Password", show="*")
        self.confirm_password_entry.grid(row=0, column=2, sticky="ew", padx=(8, 0), pady=4)

        pw_action_row = ctk.CTkFrame(pw_card, fg_color="transparent")
        pw_action_row.pack(fill="x", padx=18, pady=(2, 16))

        self.accent_button(pw_action_row, "Update Password", command=self.handle_update_password, width=170).pack(side="left")
        self.account_status_lbl = ctk.CTkLabel(pw_action_row, text="", font=FONT_LABEL)
        self.account_status_lbl.pack(side="left", padx=(14, 0))

    def handle_update_username(self):
        new_username = self.username_entry.get().strip()
        if not new_username:
            self.account_status_lbl.configure(text="Username cannot be empty.", text_color=COL_DANGER)
            return

        if new_username == self.current_username:
            self.account_status_lbl.configure(text="This is already your current username.", text_color=COL_WARNING)
            return

        success, msg = update_username(self.current_username, new_username)
        if success:
            self.current_username = new_username
            self.account_status_lbl.configure(text=msg, text_color=COL_SUCCESS)
        else:
            self.account_status_lbl.configure(text=msg, text_color=COL_DANGER)

    def handle_update_password(self):
        old_pw = self.old_password_entry.get().strip()
        new_pw = self.new_password_entry.get().strip()
        confirm_pw = self.confirm_password_entry.get().strip()

        if not old_pw or not new_pw or not confirm_pw:
            self.account_status_lbl.configure(text="All password fields are required.", text_color=COL_DANGER)
            return

        if new_pw != confirm_pw:
            self.account_status_lbl.configure(text="New password and confirmation do not match.", text_color=COL_DANGER)
            return

        success, msg = update_user_password(self.current_username, old_pw, new_pw)
        if success:
            self.old_password_entry.delete(0, "end")
            self.new_password_entry.delete(0, "end")
            self.confirm_password_entry.delete(0, "end")
            self.account_status_lbl.configure(text=msg, text_color=COL_SUCCESS)
        else:
            self.account_status_lbl.configure(text=msg, text_color=COL_DANGER)

    # =================================================================
    # SECTION 2: SHOP PROFILE (Shop Name / Logo / Footer Note)
    # =================================================================
    def build_shop_profile_section(self):
        panel = self.create_section_panel("🏪", "Shop Profile",
                                           "Customize your business identity shown on invoices and the dashboard.")

        body = ctk.CTkFrame(panel, fg_color="transparent")
        body.pack(fill="x", padx=24, pady=(5, 22))
        body.grid_columnconfigure(0, weight=2)
        body.grid_columnconfigure(1, weight=1)

        # --- Left: Identity card ---
        identity_card = self.create_inner_card(body)
        identity_card.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        self.field_label(identity_card, "SHOP / BUSINESS NAME").pack(anchor="w", padx=18, pady=(14, 4))
        self.shop_name_entry = self.styled_entry(identity_card, width=320)
        self.shop_name_entry.insert(0, self.settings.get("shop_name", "Afzal Petrol Agency"))
        self.shop_name_entry.pack(anchor="w", fill="x", padx=18, pady=(0, 14))

        self.field_label(identity_card, "INVOICE FOOTER NOTE").pack(anchor="w", padx=18, pady=(0, 4))
        self.footer_note_entry = self.styled_entry(identity_card, width=320)
        self.footer_note_entry.insert(0, self.settings.get("footer_note", "System generated invoice. Thank you for your business!"))
        self.footer_note_entry.pack(anchor="w", fill="x", padx=18, pady=(0, 8))
        ctk.CTkLabel(identity_card, text="Shown at the bottom of every printed receipt.",
                     font=FONT_HINT, text_color=COL_TEXT_SOFT).pack(anchor="w", padx=18, pady=(0, 16))

        # --- Right: Logo card ---
        logo_card = self.create_inner_card(body)
        logo_card.grid(row=0, column=1, sticky="nsew", padx=(8, 0))

        self.field_label(logo_card, "SHOP LOGO").pack(anchor="w", padx=18, pady=(14, 8))

        logo_row = ctk.CTkFrame(logo_card, fg_color="transparent")
        logo_row.pack(fill="x", padx=18, pady=(0, 8))

        self.logo_preview_lbl = ctk.CTkLabel(logo_row, text="", width=80, height=80,
                                              fg_color=COL_BG_INPUT, corner_radius=8,
                                              text_color=COL_TEXT_SOFT, font=FONT_HINT)
        self.logo_preview_lbl.configure(text="No Logo")
        self.logo_preview_lbl.pack(side="left", padx=(0, 14))
        self.refresh_logo_preview()

        logo_btns = ctk.CTkFrame(logo_row, fg_color="transparent")
        logo_btns.pack(side="left", fill="x", expand=True)

        self.accent_button(logo_btns, "Upload Logo", command=self.handle_upload_logo).pack(fill="x", pady=(0, 6))
        self.ghost_button(logo_btns, "Remove Logo", command=self.handle_remove_logo).pack(fill="x")

        ctk.CTkLabel(logo_card, text="If no logo is uploaded, the shop name will be shown on invoices instead.",
                     font=FONT_HINT, text_color=COL_TEXT_SOFT, wraplength=240, justify="left").pack(
            anchor="w", padx=18, pady=(8, 16))

        # --- Save row ---
        save_row = ctk.CTkFrame(body, fg_color="transparent")
        save_row.grid(row=1, column=0, columnspan=2, sticky="w", pady=(14, 0))

        self.accent_button(save_row, "💾  Save Shop Profile", command=self.handle_save_profile, width=190).pack(side="left")
        self.profile_status_lbl = ctk.CTkLabel(save_row, text="", font=FONT_LABEL)
        self.profile_status_lbl.pack(side="left", padx=(14, 0))

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

        self.logo_preview_lbl.configure(image=None, text="No Logo", text_color=COL_TEXT_SOFT,
                                         font=FONT_HINT)

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
            self.profile_status_lbl.configure(text="Logo selected. Click 'Save Shop Profile' to apply.", text_color=COL_ACCENT)
        except Exception as e:
            self.profile_status_lbl.configure(text=f"Logo upload failed: {str(e)}", text_color=COL_DANGER)

    def handle_remove_logo(self):
        self.selected_logo_path = ""
        self.refresh_logo_preview()
        self.profile_status_lbl.configure(text="Logo removed. Click 'Save Shop Profile' to apply.", text_color=COL_WARNING)

    def handle_save_profile(self):
        shop_name = self.shop_name_entry.get().strip()
        footer_note = self.footer_note_entry.get().strip()

        if not shop_name:
            self.profile_status_lbl.configure(text="Shop name cannot be empty.", text_color=COL_DANGER)
            return

        success, msg = set_settings_bulk({
            "shop_name": shop_name,
            "logo_path": self.selected_logo_path,
            "footer_note": footer_note
        })

        if success:
            self.settings = get_all_settings()
            self.profile_status_lbl.configure(text=msg, text_color=COL_SUCCESS)
            if self.on_profile_updated:
                self.on_profile_updated()
        else:
            self.profile_status_lbl.configure(text=msg, text_color=COL_DANGER)

    # =================================================================
    # SECTION 3: THERMAL PRINTER SETUP
    # =================================================================
    def build_printer_section(self):
        panel = self.create_section_panel("🖨️", "Thermal Printer Setup",
                                           "Detect and configure the receipt printer connected to this system.")

        body = ctk.CTkFrame(panel, fg_color="transparent")
        body.pack(fill="x", padx=24, pady=(5, 22))
        body.grid_columnconfigure(0, weight=1)
        body.grid_columnconfigure(1, weight=1)

        # --- Printer card ---
        printer_card = self.create_inner_card(body)
        printer_card.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        self.field_label(printer_card, "CONNECTED PRINTER").pack(anchor="w", padx=18, pady=(14, 4))

        saved_printer = self.settings.get("printer_name", "")
        detected = self.detect_printers()
        options = detected if detected else ["No printers detected"]
        if saved_printer and saved_printer not in options:
            options = [saved_printer] + options

        self.printer_dropdown = ctk.CTkComboBox(printer_card, values=options, height=38,
                                                  fg_color=COL_BG_INPUT, border_color=COL_BORDER,
                                                  border_width=1, button_color=COL_ACCENT_SOFT,
                                                  button_hover_color=COL_ACCENT,
                                                  dropdown_fg_color=COL_BG_CARD,
                                                  text_color=COL_TEXT_MAIN,
                                                  font=FONT_LABEL)
        if saved_printer:
            self.printer_dropdown.set(saved_printer)
        elif options:
            self.printer_dropdown.set(options[0])
        self.printer_dropdown.pack(anchor="w", fill="x", padx=18, pady=(0, 10))

        self.ghost_button(printer_card, "🔄  Detect Printers", command=self.handle_detect_printers).pack(
            anchor="w", padx=18, pady=(0, 16), fill="x")

        # --- Paper size card ---
        paper_card = self.create_inner_card(body)
        paper_card.grid(row=0, column=1, sticky="nsew", padx=(8, 0))

        self.field_label(paper_card, "RECEIPT PAPER SIZE").pack(anchor="w", padx=18, pady=(14, 4))

        self.paper_size_segment = ctk.CTkSegmentedButton(
            paper_card, values=PAPER_SIZES,
            fg_color=COL_BG_INPUT, selected_color=COL_ACCENT,
            selected_hover_color="#2563eb",
            unselected_color=COL_BG_INPUT,
            unselected_hover_color=COL_BORDER,
            text_color=COL_TEXT_MAIN, height=38,
            font=FONT_BOLD
        )
        saved_paper = self.settings.get("printer_paper_size", "80mm")
        if saved_paper not in PAPER_SIZES:
            saved_paper = "80mm"
        self.paper_size_segment.set(saved_paper)
        self.paper_size_segment.pack(anchor="w", fill="x", padx=18, pady=(0, 10))

        ctk.CTkLabel(paper_card, text="58mm and 80mm are the most common thermal receipt printer widths.",
                     font=FONT_HINT, text_color=COL_TEXT_SOFT, wraplength=260, justify="left").pack(
            anchor="w", padx=18, pady=(0, 16))

        # --- Save row ---
        save_row = ctk.CTkFrame(body, fg_color="transparent")
        save_row.grid(row=1, column=0, columnspan=2, sticky="w", pady=(14, 0))

        self.accent_button(save_row, "💾  Save Printer Settings", command=self.handle_save_printer, width=200).pack(side="left")
        self.printer_status_lbl = ctk.CTkLabel(save_row, text="", font=FONT_LABEL)
        self.printer_status_lbl.pack(side="left", padx=(14, 0))

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
            self.printer_status_lbl.configure(text=f"{len(detected)} printer(s) detected.", text_color=COL_SUCCESS)
        else:
            self.printer_dropdown.configure(values=["No printers detected"])
            self.printer_dropdown.set("No printers detected")
            self.printer_status_lbl.configure(text="No printers found. Ensure printer drivers are installed.", text_color=COL_WARNING)

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
            self.printer_status_lbl.configure(text="Printer configuration saved.", text_color=COL_SUCCESS)
        else:
            self.printer_status_lbl.configure(text=msg, text_color=COL_DANGER)

    # =================================================================
    # SECTION 4: BACKUP & RESTORE
    # =================================================================
    def build_backup_section(self):
        panel = self.create_section_panel("🗄️", "Backup & Restore",
                                           "Save a local backup, upload it to your Google Drive, or restore data from a backup file.")

        body = ctk.CTkFrame(panel, fg_color="transparent")
        body.pack(fill="x", padx=24, pady=(5, 22))

        card = self.create_inner_card(body)
        card.pack(fill="x")

        self.backup_status_lbl = ctk.CTkLabel(card, text="No recent backup activity.",
                                               font=FONT_LABEL, text_color=COL_TEXT_SOFT)
        self.backup_status_lbl.pack(anchor="w", padx=18, pady=(16, 10))

        btn_row = ctk.CTkFrame(card, fg_color="transparent")
        btn_row.pack(anchor="w", fill="x", padx=18, pady=(0, 18))

        self.accent_button(btn_row, "⬇️  Download Backup (.db)", command=self.handle_backup_local, width=210).pack(side="left", padx=(0, 10))
        self.accent_button(btn_row, "☁️  Upload to Google Drive", command=self.handle_backup_drive, width=210).pack(side="left", padx=(0, 10))
        self.danger_button(btn_row, "♻️  Import / Restore Backup", command=self.handle_restore, width=210).pack(side="left")

    def handle_backup_local(self):
        self.backup_status_lbl.configure(text="Opening save dialog...", text_color=COL_ACCENT)
        self.update_idletasks()
        path = backup_to_local(self)
        if path:
            self.backup_status_lbl.configure(text=f"Backup saved: {path}", text_color=COL_SUCCESS)
        else:
            self.backup_status_lbl.configure(text="Backup cancelled.", text_color=COL_TEXT_SOFT)

    def handle_backup_drive(self):
        self.backup_status_lbl.configure(text="Connecting to Google Drive...", text_color=COL_ACCENT)
        self.update_idletasks()
        success = upload_to_drive(self)
        if success:
            self.backup_status_lbl.configure(text="Backup uploaded to Google Drive.", text_color=COL_SUCCESS)
        else:
            self.backup_status_lbl.configure(text="Drive upload cancelled or failed.", text_color=COL_WARNING)

    def handle_restore(self):
        self.backup_status_lbl.configure(text="Select a backup file to restore...", text_color=COL_ACCENT)
        self.update_idletasks()
        restored = restore_from_local(self)
        if restored:
            self.backup_status_lbl.configure(text="Restore complete. Please restart the app.", text_color=COL_SUCCESS)
        else:
            self.backup_status_lbl.configure(text="Restore cancelled.", text_color=COL_TEXT_SOFT)

    # =================================================================
    # SECTION 5: SOFTWARE UPDATE
    # =================================================================
    def build_update_section(self):
        panel = self.create_section_panel("🔔", "Software Update", "Check for the latest application build.")

        body = ctk.CTkFrame(panel, fg_color="transparent")
        body.pack(fill="x", padx=24, pady=(5, 24))

        card = self.create_inner_card(body)
        card.pack(fill="x")

        info_row = ctk.CTkFrame(card, fg_color="transparent")
        info_row.pack(fill="x", padx=18, pady=(16, 4))

        version_badge = ctk.CTkFrame(info_row, fg_color=COL_ACCENT_SOFT, corner_radius=6)
        version_badge.pack(side="left")
        ctk.CTkLabel(version_badge, text=f"  Build {CURRENT_VERSION}  ", font=FONT_BOLD,
                     text_color=COL_ACCENT).pack(padx=4, pady=4)

        self.update_status_lbl = ctk.CTkLabel(card, text="Updates: System up to date.",
                                               font=FONT_LABEL, text_color=COL_TEXT_SOFT)
        self.update_status_lbl.pack(anchor="w", padx=18, pady=(10, 10))

        self.accent_button(card, "🔍  Check for Software Updates", command=self.check_for_updates, width=230).pack(
            anchor="w", padx=18, pady=(0, 18))

    def check_for_updates(self):
        self.update_status_lbl.configure(text="Checking for updates...", text_color=COL_ACCENT)
        self.update_idletasks()

        result = check_for_update()

        if result["status"] == "update_available":
            self.update_status_lbl.configure(
                text=f"New version available: {result['latest_version']} (current: {CURRENT_VERSION})",
                text_color=COL_DANGER
            )
            self._latest_release_url = result.get("download_url") or result.get("release_url")
            if not hasattr(self, "btn_download_update"):
                self.btn_download_update = ctk.CTkButton(
                    self.update_status_lbl.master, text="⬇️  Download Update", fg_color=COL_SUCCESS_BG,
                    hover_color="#1f3d2c", text_color=COL_SUCCESS, border_color=COL_SUCCESS, border_width=1,
                    height=36, corner_radius=8, font=FONT_BOLD,
                    command=self.open_update_link
                )
                self.btn_download_update.pack(anchor="w", padx=18, pady=(0, 14))
            else:
                self.btn_download_update.pack(anchor="w", padx=18, pady=(0, 14))

        elif result["status"] == "up_to_date":
            self.update_status_lbl.configure(text="You are running the latest version.", text_color=COL_SUCCESS)
            if hasattr(self, "btn_download_update"):
                self.btn_download_update.pack_forget()

        else:
            self.update_status_lbl.configure(text=result["message"], text_color=COL_WARNING)
            if hasattr(self, "btn_download_update"):
                self.btn_download_update.pack_forget()

    def open_update_link(self):
        url = getattr(self, "_latest_release_url", None)
        if url:
            webbrowser.open(url)

    # =================================================================
    # HELPERS / UI PRIMITIVES
    # =================================================================
    def create_section_panel(self, icon, title, subtitle):
        panel = ctk.CTkFrame(self.scroll, fg_color=COL_BG_CARD, border_color=COL_BORDER,
                              border_width=1, corner_radius=10)
        panel.pack(fill="x", pady=(0, 18))

        header_row = ctk.CTkFrame(panel, fg_color="transparent")
        header_row.pack(fill="x", padx=24, pady=(18, 4))

        icon_badge = ctk.CTkFrame(header_row, fg_color=COL_ACCENT_SOFT, corner_radius=8, width=38, height=38)
        icon_badge.pack(side="left", padx=(0, 12))
        icon_badge.pack_propagate(False)
        ctk.CTkLabel(icon_badge, text=icon, font=ctk.CTkFont(size=17)).pack(expand=True)

        text_col = ctk.CTkFrame(header_row, fg_color="transparent")
        text_col.pack(side="left", fill="x", expand=True)
        ctk.CTkLabel(text_col, text=title, font=ctk.CTkFont(size=15, weight="bold"),
                     text_color=COL_TEXT_MAIN).pack(anchor="w")
        ctk.CTkLabel(text_col, text=subtitle, font=FONT_HINT, text_color=COL_TEXT_SOFT).pack(anchor="w", pady=(2, 0))

        return panel

    def create_inner_card(self, parent):
        return ctk.CTkFrame(parent, fg_color=COL_BG_CARD_ALT, border_color=COL_BORDER,
                             border_width=1, corner_radius=8)

    def field_label(self, parent, text):
        return ctk.CTkLabel(parent, text=text, font=ctk.CTkFont(size=11, weight="bold"), text_color=COL_TEXT_SOFT)

    def styled_entry(self, parent, width=240, placeholder="", show=""):
        return ctk.CTkEntry(parent, width=width, height=38, fg_color=COL_BG_INPUT,
                             border_color=COL_BORDER, border_width=1, corner_radius=6,
                             text_color=COL_TEXT_MAIN, placeholder_text=placeholder, show=show,
                             font=FONT_LABEL)

    def accent_button(self, parent, text, command, width=160):
        return ctk.CTkButton(parent, text=text, width=width, height=38, corner_radius=8,
                              fg_color=COL_ACCENT, hover_color="#2563eb", text_color="#ffffff",
                              font=FONT_BOLD, command=command)

    def ghost_button(self, parent, text, command, width=160):
        return ctk.CTkButton(parent, text=text, width=width, height=38, corner_radius=8,
                              fg_color="transparent", hover_color=COL_BORDER,
                              border_color=COL_BORDER, border_width=1, text_color=COL_TEXT_MUTED,
                              font=FONT_BOLD, command=command)

    def danger_button(self, parent, text, command, width=160):
        return ctk.CTkButton(parent, text=text, width=width, height=38, corner_radius=8,
                              fg_color=COL_DANGER_BG, hover_color="#3a1c1c",
                              border_color=COL_DANGER, border_width=1, text_color=COL_DANGER,
                              font=FONT_BOLD, command=command)