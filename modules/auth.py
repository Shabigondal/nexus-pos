import customtkinter as ctk
from database.db_manager import is_first_run, register_admin, verify_login, reset_password

# =====================================================================
# 🎨 PROFESSIONAL THEME PALETTE (matches Billing Console / Settings)
# =====================================================================
COL_BG_CARD     = "#1a1d24"
COL_BG_CARD_ALT = "#15171d"
COL_BG_INPUT    = "#11131a"
COL_BORDER      = "#2a2e38"
COL_ACCENT      = "#3b82f6"
COL_ACCENT_SOFT = "#1e293b"
COL_ACCENT_DARK = "#0f1729"
COL_SUCCESS     = "#22c55e"
COL_DANGER      = "#ef4444"
COL_WARNING     = "#f59e0b"
COL_TEXT_MAIN   = "#f1f5f9"
COL_TEXT_MUTED  = "#94a3b8"
COL_TEXT_SOFT   = "#64748b"


class AuthWindow(ctk.CTkToplevel):
    def __init__(self, parent, on_success):
        super().__init__(parent)

        self.on_success = on_success
        self.title("Nexus POS - Secure Access")

        # Premium Center Screen Calculation Window Geometry
        window_width = 920
        window_height = 580
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        center_x = int(screen_width / 2 - window_width / 2)
        center_y = int(screen_height / 2 - window_height / 2)
        self.geometry(f"{window_width}x{window_height}+{center_x}+{center_y}")

        self.minsize(820, 540)
        self.resizable(True, True)
        self.attributes("-topmost", True)
        self.grab_set()

        self.protocol("WM_DELETE_WINDOW", self.on_close)

        self.questions = [
            "What is your birth city?",
            "What was your first pet's name?",
            "What was your high school name?"
        ]

        self.configure(fg_color=COL_BG_CARD_ALT)

        # ---------------------------------------------------------------
        # ROOT LAYOUT: left brand panel + right form panel
        # ---------------------------------------------------------------
        self.grid_columnconfigure(0, weight=4)
        self.grid_columnconfigure(1, weight=5)
        self.grid_rowconfigure(0, weight=1)

        self.build_brand_panel()

        self.form_panel = ctk.CTkFrame(self, fg_color=COL_BG_CARD, corner_radius=0)
        self.form_panel.grid(row=0, column=1, sticky="nsew")
        self.form_panel.grid_columnconfigure(0, weight=1)
        self.form_panel.grid_rowconfigure(0, weight=1)

        self.panel = ctk.CTkScrollableFrame(self.form_panel, fg_color="transparent")
        self.panel.grid(row=0, column=0, sticky="nsew")
        self.panel.grid_columnconfigure(0, weight=1)

        if is_first_run():
            self.show_registration_view()
        else:
            self.show_login_view()

    # =================================================================
    # LEFT BRANDING PANEL
    # =================================================================
    def build_brand_panel(self):
        brand = ctk.CTkFrame(self, fg_color=COL_ACCENT_DARK, corner_radius=0)
        brand.grid(row=0, column=0, sticky="nsew")
        brand.grid_rowconfigure(0, weight=1)
        brand.grid_rowconfigure(2, weight=1)
        brand.grid_columnconfigure(0, weight=1)

        # subtle accent glow block at top
        glow = ctk.CTkFrame(brand, fg_color=COL_ACCENT_SOFT, corner_radius=100, width=260, height=260)
        glow.place(relx=0.5, rely=0.18, anchor="center")

        content = ctk.CTkFrame(brand, fg_color="transparent")
        content.grid(row=1, column=0, sticky="ew", padx=46)

        # Logo badge
        logo_badge = ctk.CTkFrame(content, fg_color=COL_ACCENT, corner_radius=14, width=58, height=58)
        logo_badge.pack(anchor="w", pady=(0, 22))
        logo_badge.pack_propagate(False)
        ctk.CTkLabel(logo_badge, text="N", font=ctk.CTkFont(size=26, weight="bold"),
                     text_color="#ffffff").pack(expand=True)

        ctk.CTkLabel(content, text="NEXUS INDUSTRIAL", font=ctk.CTkFont(size=22, weight="bold"),
                     text_color=COL_TEXT_MAIN).pack(anchor="w")
        ctk.CTkLabel(content, text="POS & Inventory Control Workspace",
                     font=ctk.CTkFont(size=13), text_color=COL_ACCENT).pack(anchor="w", pady=(2, 28))

        # Feature highlights
        features = [
            ("⚡", "Real-time billing & invoicing"),
            ("📦", "Live inventory & stock control"),
            ("📊", "Analytics & daily sales reports"),
            ("🔒", "Secure, encrypted local sessions"),
        ]
        for icon, text in features:
            row = ctk.CTkFrame(content, fg_color="transparent")
            row.pack(anchor="w", fill="x", pady=6)

            icon_box = ctk.CTkFrame(row, fg_color=COL_ACCENT_SOFT, corner_radius=8, width=34, height=34)
            icon_box.pack(side="left")
            icon_box.pack_propagate(False)
            ctk.CTkLabel(icon_box, text=icon, font=ctk.CTkFont(size=15)).pack(expand=True)

            ctk.CTkLabel(row, text=text, font=ctk.CTkFont(size=12), text_color=COL_TEXT_MUTED).pack(
                side="left", padx=(12, 0))

        # Footer
        footer = ctk.CTkFrame(brand, fg_color="transparent")
        footer.grid(row=2, column=0, sticky="ews", padx=46, pady=24)
        ctk.CTkLabel(footer, text="© Nexus Industrial — All rights reserved.",
                     font=ctk.CTkFont(size=10), text_color=COL_TEXT_SOFT).pack(anchor="w")

    # =================================================================
    # SHARED HELPERS
    # =================================================================
    def clear_panel(self):
        for widget in self.panel.winfo_children():
            widget.destroy()

    def field_label(self, parent, text):
        return ctk.CTkLabel(parent, text=text, font=ctk.CTkFont(size=11, weight="bold"), text_color=COL_TEXT_SOFT)

    def styled_entry(self, parent, placeholder="", show=""):
        return ctk.CTkEntry(parent, placeholder_text=placeholder, show=show, height=42,
                             fg_color=COL_BG_INPUT, border_color=COL_BORDER, border_width=1,
                             corner_radius=8, text_color=COL_TEXT_MAIN, font=ctk.CTkFont(size=13))

    def styled_optionmenu(self, parent, values):
        return ctk.CTkOptionMenu(parent, values=values, height=42, fg_color=COL_BG_INPUT,
                                  button_color=COL_ACCENT_SOFT, button_hover_color=COL_ACCENT,
                                  dropdown_fg_color=COL_BG_CARD, text_color=COL_TEXT_MAIN,
                                  corner_radius=8, font=ctk.CTkFont(size=13))

    def primary_button(self, parent, text, command):
        return ctk.CTkButton(parent, text=text, height=46, corner_radius=8,
                              fg_color=COL_ACCENT, hover_color="#2563eb", text_color="#ffffff",
                              font=ctk.CTkFont(size=14, weight="bold"), command=command)

    def link_button(self, parent, text, command, color=None):
        return ctk.CTkButton(parent, text=text, fg_color="transparent", hover=False,
                              text_color=color or COL_ACCENT, cursor="hand2",
                              font=ctk.CTkFont(size=12), command=command)

    def page_header(self, badge_text, title, subtitle):
        wrap = ctk.CTkFrame(self.panel, fg_color="transparent")
        wrap.pack(fill="x", padx=56, pady=(56, 28))

        badge = ctk.CTkFrame(wrap, fg_color=COL_ACCENT_SOFT, corner_radius=8, width=46, height=46)
        badge.pack(anchor="w", pady=(0, 16))
        badge.pack_propagate(False)
        ctk.CTkLabel(badge, text=badge_text, font=ctk.CTkFont(size=20)).pack(expand=True)

        ctk.CTkLabel(wrap, text=title, font=ctk.CTkFont(size=22, weight="bold"),
                     text_color=COL_TEXT_MAIN).pack(anchor="w")
        ctk.CTkLabel(wrap, text=subtitle, font=ctk.CTkFont(size=12), text_color=COL_TEXT_SOFT).pack(
            anchor="w", pady=(4, 0))
        return wrap

    def status_label(self, parent):
        return ctk.CTkLabel(parent, text="", font=ctk.CTkFont(size=12), wraplength=380, justify="left")

    # =================================================================
    # REGISTRATION VIEW (first run / setup)
    # =================================================================
    def show_registration_view(self):
        self.clear_panel()

        self.page_header("🛠️", "Welcome to Nexus POS",
                         "Set up your administrator account to get started.")

        form = ctk.CTkFrame(self.panel, fg_color="transparent")
        form.pack(fill="x", padx=56)

        self.field_label(form, "ADMINISTRATOR USERNAME").pack(anchor="w", pady=(0, 6))
        self.reg_username = self.styled_entry(form, placeholder="e.g. admin")
        self.reg_username.pack(fill="x", pady=(0, 16))

        self.field_label(form, "ROOT PASSWORD").pack(anchor="w", pady=(0, 6))
        self.reg_password = self.styled_entry(form, placeholder="Create a strong password", show="*")
        self.reg_password.pack(fill="x", pady=(0, 16))

        self.field_label(form, "SECURITY QUESTION").pack(anchor="w", pady=(0, 6))
        ctk.CTkLabel(form, text="Used to recover your account if you forget your password.",
                     font=ctk.CTkFont(size=11), text_color=COL_TEXT_SOFT).pack(anchor="w", pady=(0, 6))
        self.reg_question = self.styled_optionmenu(form, self.questions)
        self.reg_question.pack(fill="x", pady=(0, 16))

        self.field_label(form, "YOUR ANSWER").pack(anchor="w", pady=(0, 6))
        self.reg_answer = self.styled_entry(form, placeholder="Type your answer")
        self.reg_answer.pack(fill="x", pady=(0, 10))

        self.reg_error = self.status_label(form)
        self.reg_error.pack(anchor="w", pady=(0, 10))

        self.primary_button(form, "Create Administrator Account", self.handle_registration).pack(
            fill="x", pady=(8, 40))

    def handle_registration(self):
        u = self.reg_username.get().strip()
        p = self.reg_password.get().strip()
        q = self.reg_question.get()
        a = self.reg_answer.get().strip()

        if not u or not p or not a:
            self.reg_error.configure(text="⚠  Please fill in all fields to continue.", text_color=COL_DANGER)
            return

        success, msg = register_admin(u, p, q, a)
        if success:
            self.show_login_view()
        else:
            self.reg_error.configure(text=f"⚠  {msg}", text_color=COL_DANGER)

    # =================================================================
    # LOGIN VIEW
    # =================================================================
    def show_login_view(self):
        self.clear_panel()

        self.page_header("👋", "Welcome Back", "Sign in to access your billing workspace.")

        form = ctk.CTkFrame(self.panel, fg_color="transparent")
        form.pack(fill="x", padx=56)

        self.field_label(form, "USERNAME").pack(anchor="w", pady=(0, 6))
        self.login_username = self.styled_entry(form, placeholder="Enter your username")
        self.login_username.pack(fill="x", pady=(0, 16))

        self.field_label(form, "PASSWORD").pack(anchor="w", pady=(0, 6))
        self.login_password = self.styled_entry(form, placeholder="Enter your password", show="*")
        self.login_password.pack(fill="x", pady=(0, 8))
        self.login_password.bind("<Return>", lambda e: self.handle_login())

        self.login_error = self.status_label(form)
        self.login_error.pack(anchor="w", pady=(0, 10))

        self.primary_button(form, "Sign In", self.handle_login).pack(fill="x", pady=(8, 16))

        forgot_row = ctk.CTkFrame(form, fg_color="transparent")
        forgot_row.pack(fill="x", pady=(0, 50))
        self.link_button(forgot_row, "Forgot your password?", self.show_recovery_view).pack(anchor="center")

    def handle_login(self):
        u = self.login_username.get().strip()
        p = self.login_password.get().strip()

        if not u or not p:
            self.login_error.configure(text="⚠  Please enter both username and password.", text_color=COL_DANGER)
            return

        success, msg = verify_login(u, p)
        if success:
            self.grab_release()
            self.destroy()
            self.on_success(u)
        else:
            self.login_error.configure(text=f"⚠  {msg}", text_color=COL_DANGER)

    # =================================================================
    # PASSWORD RECOVERY VIEW
    # =================================================================
    def show_recovery_view(self):
        self.clear_panel()

        self.page_header("🔑", "Reset Your Password",
                         "Answer your security question to set a new password.")

        form = ctk.CTkFrame(self.panel, fg_color="transparent")
        form.pack(fill="x", padx=56)

        self.field_label(form, "USERNAME").pack(anchor="w", pady=(0, 6))
        self.rec_username = self.styled_entry(form, placeholder="Enter your username")
        self.rec_username.pack(fill="x", pady=(0, 16))

        self.field_label(form, "SECURITY QUESTION").pack(anchor="w", pady=(0, 6))
        self.rec_question = self.styled_optionmenu(form, self.questions)
        self.rec_question.pack(fill="x", pady=(0, 16))

        self.field_label(form, "YOUR ANSWER").pack(anchor="w", pady=(0, 6))
        self.rec_answer = self.styled_entry(form, placeholder="Type your answer")
        self.rec_answer.pack(fill="x", pady=(0, 16))

        self.field_label(form, "NEW PASSWORD").pack(anchor="w", pady=(0, 6))
        self.rec_new_pass = self.styled_entry(form, placeholder="Choose a new password", show="*")
        self.rec_new_pass.pack(fill="x", pady=(0, 10))

        self.rec_error = self.status_label(form)
        self.rec_error.pack(anchor="w", pady=(0, 10))

        self.primary_button(form, "Reset Password", self.handle_recovery).pack(fill="x", pady=(8, 16))

        back_row = ctk.CTkFrame(form, fg_color="transparent")
        back_row.pack(fill="x", pady=(0, 50))
        self.link_button(back_row, "← Back to Sign In", self.show_login_view,
                          color=COL_TEXT_SOFT).pack(anchor="center")

    def handle_recovery(self):
        u = self.rec_username.get().strip()
        q = self.rec_question.get()
        a = self.rec_answer.get().strip()
        np = self.rec_new_pass.get().strip()

        if not u or not a or not np:
            self.rec_error.configure(text="⚠  Please fill in all fields.", text_color=COL_DANGER)
            return

        success, msg = reset_password(u, q, a, np)
        if success:
            self.rec_error.configure(text=f"✓  {msg}", text_color=COL_SUCCESS)
            self.panel.after(1500, self.show_login_view)
        else:
            self.rec_error.configure(text=f"⚠  {msg}", text_color=COL_DANGER)

    def on_close(self):
        self.master.destroy()