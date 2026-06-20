import customtkinter as ctk
from modules.license_manager import get_device_id, activate_with_code

# Reuse the same palette as auth.py for visual consistency
COL_BG_CARD     = "#1a1d24"
COL_BG_CARD_ALT = "#15171d"
COL_BG_INPUT    = "#11131a"
COL_BORDER      = "#2a2e38"
COL_ACCENT      = "#3b82f6"
COL_ACCENT_SOFT = "#1e293b"
COL_SUCCESS     = "#22c55e"
COL_DANGER      = "#ef4444"
COL_TEXT_MAIN   = "#f1f5f9"
COL_TEXT_MUTED  = "#94a3b8"
COL_TEXT_SOFT   = "#64748b"


class ActivationWindow(ctk.CTkToplevel):
    """Blocks the app until a valid activation code is entered for this PC."""

    def __init__(self, parent, on_success):
        super().__init__(parent)
        self.on_success = on_success

        self.title("Nexus POS - Activation Required")
        window_width, window_height = 560, 520
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        center_x = int(screen_width / 2 - window_width / 2)
        center_y = int(screen_height / 2 - window_height / 2)
        self.geometry(f"{window_width}x{window_height}+{center_x}+{center_y}")
        self.resizable(False, False)
        self.attributes("-topmost", True)
        self.grab_set()
        self.configure(fg_color=COL_BG_CARD_ALT)
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        self.device_id = get_device_id()

        card = ctk.CTkFrame(self, fg_color=COL_BG_CARD, corner_radius=14, border_color=COL_BORDER, border_width=1)
        card.pack(fill="both", expand=True, padx=24, pady=24)

        badge = ctk.CTkFrame(card, fg_color=COL_ACCENT_SOFT, corner_radius=10, width=50, height=50)
        badge.pack(pady=(30, 14))
        badge.pack_propagate(False)
        ctk.CTkLabel(badge, text="🔒", font=ctk.CTkFont(size=22)).pack(expand=True)

        ctk.CTkLabel(card, text="Activation Required", font=ctk.CTkFont(size=20, weight="bold"),
                     text_color=COL_TEXT_MAIN).pack()
        ctk.CTkLabel(card, text="This copy of Nexus POS needs to be activated for this PC.",
                     font=ctk.CTkFont(size=12), text_color=COL_TEXT_SOFT, wraplength=440).pack(pady=(4, 24))

        # Device ID box
        ctk.CTkLabel(card, text="STEP 1 — Send this Device ID to your software provider",
                     font=ctk.CTkFont(size=11, weight="bold"), text_color=COL_TEXT_SOFT).pack(anchor="w", padx=40)

        id_row = ctk.CTkFrame(card, fg_color=COL_BG_INPUT, corner_radius=8, border_color=COL_BORDER, border_width=1)
        id_row.pack(fill="x", padx=40, pady=(8, 4))
        ctk.CTkLabel(id_row, text=self.device_id, font=ctk.CTkFont(size=15, weight="bold", family="Consolas"),
                     text_color=COL_ACCENT).pack(side="left", padx=14, pady=12)
        ctk.CTkButton(id_row, text="Copy", width=64, height=28, corner_radius=6,
                      fg_color=COL_ACCENT_SOFT, hover_color=COL_ACCENT,
                      command=self.copy_device_id).pack(side="right", padx=10)

        self.copy_status = ctk.CTkLabel(card, text="", font=ctk.CTkFont(size=10), text_color=COL_SUCCESS)
        self.copy_status.pack(anchor="w", padx=40, pady=(0, 18))

        # Activation code entry
        ctk.CTkLabel(card, text="STEP 2 — Enter the Activation Code you received",
                     font=ctk.CTkFont(size=11, weight="bold"), text_color=COL_TEXT_SOFT).pack(anchor="w", padx=40)

        self.code_entry = ctk.CTkEntry(card, placeholder_text="Paste activation code here", height=42,
                                        fg_color=COL_BG_INPUT, border_color=COL_BORDER, border_width=1,
                                        corner_radius=8, text_color=COL_TEXT_MAIN, font=ctk.CTkFont(size=13))
        self.code_entry.pack(fill="x", padx=40, pady=(8, 10))
        self.code_entry.bind("<Return>", lambda e: self.handle_activate())

        self.status_lbl = ctk.CTkLabel(card, text="", font=ctk.CTkFont(size=12), wraplength=440)
        self.status_lbl.pack(padx=40, pady=(0, 6))

        ctk.CTkButton(card, text="Activate", height=44, corner_radius=8,
                      fg_color=COL_ACCENT, hover_color="#2563eb", text_color="#ffffff",
                      font=ctk.CTkFont(size=14, weight="bold"),
                      command=self.handle_activate).pack(fill="x", padx=40, pady=(10, 8))

        ctk.CTkButton(card, text="Exit", height=32, fg_color="transparent", hover=False,
                      text_color=COL_TEXT_SOFT, cursor="hand2",
                      command=self.on_close).pack(pady=(0, 16))

    def copy_device_id(self):
        self.clipboard_clear()
        self.clipboard_append(self.device_id)
        self.copy_status.configure(text="✓ Copied to clipboard")

    def handle_activate(self):
        code = self.code_entry.get().strip()
        if not code:
            self.status_lbl.configure(text="⚠  Please enter the activation code.", text_color=COL_DANGER)
            return

        if activate_with_code(code):
            self.status_lbl.configure(text="✓  Activated successfully!", text_color=COL_SUCCESS)
            self.grab_release()
            self.destroy()
            self.on_success()
        else:
            self.status_lbl.configure(
                text="⚠  Invalid activation code for this device. Double-check and try again.",
                text_color=COL_DANGER
            )

    def on_close(self):
        self.master.destroy()
