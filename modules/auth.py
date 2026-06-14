import customtkinter as ctk
from database.db_manager import is_first_run, register_admin, verify_login, reset_password

class AuthWindow(ctk.CTkToplevel):
    def __init__(self, parent, on_success):
        super().__init__(parent)
        
        self.on_success = on_success
        self.title("Nexus POS Core - Identity Provider")
        
        # Premium Center Screen Calculation Window Geometry
        window_width = 460
        window_height = 560
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        center_x = int(screen_width/2 - window_width/2)
        center_y = int(screen_height/2 - window_height/2)
        self.geometry(f"{window_width}x{window_height}+{center_x}+{center_y}")
        
        self.resizable(True, True)  # Enabled client request min/max capabilities
        self.attributes("-topmost", True)
        self.grab_set()
        
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        self.questions = [
            "What is your birth city?", 
            "What was your first pet's name?", 
            "What was your high school name?"
        ]

        # Industrial Workspace Theme Coloring
        self.configure(fg_color="#121214")
        self.panel = ctk.CTkFrame(self, corner_radius=6, fg_color="#1a1a1e", border_color="#2b2b30", border_width=1)
        self.panel.pack(fill="both", expand=True, padx=30, pady=30)

        if is_first_run():
            self.show_registration_view()
        else:
            self.show_login_view()

    def clear_panel(self):
        for widget in self.panel.winfo_children():
            widget.destroy()

    def show_registration_view(self):
        self.clear_panel()
        
        lbl_title = ctk.CTkLabel(self.panel, text="Initial System Deployment", font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold"), text_color="#ffffff")
        lbl_title.pack(pady=(35, 5))
        
        lbl_subtitle = ctk.CTkLabel(self.panel, text="Configure global super-user security parameters.", font=ctk.CTkFont(family="Segoe UI", size=11), text_color="#8a8a93")
        lbl_subtitle.pack(pady=(0, 25))

        self.reg_username = ctk.CTkEntry(self.panel, placeholder_text="Administrator Account ID", width=320, height=38, fg_color="#121214", border_color="#333339", corner_radius=4)
        self.reg_username.pack(pady=8)

        self.reg_password = ctk.CTkEntry(self.panel, placeholder_text="Root Access Password", show="*", width=320, height=38, fg_color="#121214", border_color="#333339", corner_radius=4)
        self.reg_password.pack(pady=8)

        lbl_q = ctk.CTkLabel(self.panel, text="Emergency Account Recovery Identifier:", font=ctk.CTkFont(family="Segoe UI", size=11), text_color="#cfcfd4")
        lbl_q.pack(pady=(12, 4), anchor="w", padx=40)
        
        self.reg_question = ctk.CTkOptionMenu(self.panel, values=self.questions, width=320, height=38, fg_color="#121214", button_color="#2b2b30", button_hover_color="#333339", corner_radius=4)
        self.reg_question.pack(pady=5)

        self.reg_answer = ctk.CTkEntry(self.panel, placeholder_text="Validation Answer String", width=320, height=38, fg_color="#121214", border_color="#333339", corner_radius=4)
        self.reg_answer.pack(pady=8)

        self.reg_error = ctk.CTkLabel(self.panel, text="", font=ctk.CTkFont(size=12))
        self.reg_error.pack(pady=5)

        btn_setup = ctk.CTkButton(self.panel, text="Initialize Architecture", width=320, height=42, fg_color="#1f293d", hover_color="#2d3d5a", text_color="#ffffff", corner_radius=4, font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"), command=self.handle_registration)
        btn_setup.pack(pady=20)

    def handle_registration(self):
        u = self.reg_username.get().strip()
        p = self.reg_password.get().strip()
        q = self.reg_question.get()
        a = self.reg_answer.get().strip()

        if not u or not p or not a:
            self.reg_error.configure(text="Execution halted: All properties required.", text_color="#ff4a4a")
            return

        success, msg = register_admin(u, p, q, a)
        if success:
            self.show_login_view()
        else:
            self.reg_error.configure(text=msg, text_color="#ff4a4a")

    def show_login_view(self):
        self.clear_panel()

        lbl_title = ctk.CTkLabel(self.panel, text="Secure Gateway Access", font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold"), text_color="#ffffff")
        lbl_title.pack(pady=(45, 5))
        
        lbl_subtitle = ctk.CTkLabel(self.panel, text="Provide credentials to initialize localized session.", font=ctk.CTkFont(family="Segoe UI", size=11), text_color="#8a8a93")
        lbl_subtitle.pack(pady=(0, 35))

        self.login_username = ctk.CTkEntry(self.panel, placeholder_text="User Principal ID", width=320, height=42, fg_color="#121214", border_color="#333339", corner_radius=4)
        self.login_username.pack(pady=10)

        self.login_password = ctk.CTkEntry(self.panel, placeholder_text="Secure Token / Password", show="*", width=320, height=42, fg_color="#121214", border_color="#333339", corner_radius=4)
        self.login_password.pack(pady=10)

        self.login_error = ctk.CTkLabel(self.panel, text="", font=ctk.CTkFont(size=12))
        self.login_error.pack(pady=5)

        btn_login = ctk.CTkButton(self.panel, text="Authenticate Account", width=320, height=45, fg_color="#1f293d", hover_color="#2d3d5a", text_color="#ffffff", corner_radius=4, font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"), command=self.handle_login)
        btn_login.pack(pady=(15, 12))

        btn_forgot = ctk.CTkButton(self.panel, text="Identity Recovery Manager", fg_color="transparent", text_color="#5b9bd5", hover=False, cursor="hand2", font=ctk.CTkFont(family="Segoe UI", size=11), command=self.show_recovery_view)
        btn_forgot.pack(pady=5)

    def handle_login(self):
        u = self.login_username.get().strip()
        p = self.login_password.get().strip()

        success, msg = verify_login(u, p)
        if success:
            self.grab_release()
            self.destroy()
            self.on_success(u)
        else:
            self.login_error.configure(text=msg, text_color="#ff4a4a")

    def show_recovery_view(self):
        self.clear_panel()

        lbl_title = ctk.CTkLabel(self.panel, text="Identity Token Recovery", font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold"), text_color="#ffffff")
        lbl_title.pack(pady=(30, 25))

        self.rec_username = ctk.CTkEntry(self.panel, placeholder_text="Confirm User Target ID", width=320, height=38, fg_color="#121214", border_color="#333339", corner_radius=4)
        self.rec_username.pack(pady=8)

        self.rec_question = ctk.CTkOptionMenu(self.panel, values=self.questions, width=320, height=38, fg_color="#121214", button_color="#2b2b30", button_hover_color="#333339", corner_radius=4)
        self.rec_question.pack(pady=8)

        self.rec_answer = ctk.CTkEntry(self.panel, placeholder_text="Matching Answer String", width=320, height=38, fg_color="#121214", border_color="#333339", corner_radius=4)
        self.rec_answer.pack(pady=8)

        self.rec_new_pass = ctk.CTkEntry(self.panel, placeholder_text="Assign New Passcode", show="*", width=320, height=38, fg_color="#121214", border_color="#333339", corner_radius=4)
        self.rec_new_pass.pack(pady=8)

        self.rec_error = ctk.CTkLabel(self.panel, text="", font=ctk.CTkFont(size=12))
        self.rec_error.pack(pady=5)

        btn_recover = ctk.CTkButton(self.panel, text="Apply Global Password Reset", width=320, height=42, fg_color="#1f293d", hover_color="#2d3d5a", text_color="#ffffff", corner_radius=4, font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"), command=self.handle_recovery)
        btn_recover.pack(pady=15)

        btn_back = ctk.CTkButton(self.panel, text="Abort Recovery Process", fg_color="transparent", text_color="#8a8a93", hover=False, cursor="hand2", font=ctk.CTkFont(family="Segoe UI", size=11), command=self.show_login_view)
        btn_back.pack(pady=5)

    def handle_recovery(self):
        u = self.rec_username.get().strip()
        q = self.rec_question.get()
        a = self.rec_answer.get().strip()
        np = self.rec_new_pass.get().strip()

        if not u or not a or not np:
            self.rec_error.configure(text="Validation error: Missing elements.", text_color="#ff4a4a")
            return

        success, msg = reset_password(u, q, a, np)
        if success:
            self.rec_error.configure(text=msg, text_color="#4aff4a")
            self.panel.after(1500, self.show_login_view)
        else:
            self.rec_error.configure(text=msg, text_color="#ff4a4a")

    def on_close(self):
        self.master.destroy()