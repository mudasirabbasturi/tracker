import customtkinter as ctk
from tkinter import simpledialog, messagebox
import os
BRAND_COLOR = "#2563EB"      # Primary blue
BRAND_HOVER = "#1D4ED8"
SUCCESS_COLOR = "#16A34A"    # Green
SUCCESS_HOVER = "#15803D"
DANGER_COLOR = "#DC2626"     # Red
DANGER_HOVER = "#B91C1C"
DISABLED_COLOR = "#6B7280"   # Gray
class TrackerUI(ctk.CTk):
    def __init__(self, on_login_callback, on_logout_callback, on_check_in_callback, on_check_out_callback):
        super().__init__()

        self.title("Bidwinners Tracker")
        self.geometry("420x580")
        self.resizable(False, False)
        self.on_login_callback = on_login_callback
        self.on_logout_callback = on_logout_callback
        self.on_check_in_callback = on_check_in_callback
        self.on_check_out_callback = on_check_out_callback
        self.admin_password = "bidenterprise#12"  # Default fallback

        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")
        self.configure(fg_color="#0F172A")  # deep navy bg

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.login_frame = None
        self.attendance_frame = None
        self.check_in_button = None
        self.check_out_button = None
        self.status_label = None

    # ─── Login Screen ───────────────────────────────────────────
    def show_login(self, error_message=None):
        if self.attendance_frame:
            self.attendance_frame.destroy()
            self.attendance_frame = None

        self.login_frame = ctk.CTkFrame(self, fg_color="#1E293B", corner_radius=16)
        self.login_frame.grid(row=0, column=0, padx=30, pady=30, sticky="nsew")
        self.login_frame.grid_columnconfigure(0, weight=1)

        # Brand header
        brand_label = ctk.CTkLabel(
            self.login_frame,
            text="BIDWINNERS",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color=BRAND_COLOR
        )
        brand_label.grid(row=0, column=0, pady=(36, 4))

        title_label = ctk.CTkLabel(
            self.login_frame,
            text="Estimator Login",
            font=ctk.CTkFont(family="Segoe UI", size=26, weight="bold"),
            text_color="#F1F5F9"
        )
        title_label.grid(row=1, column=0, pady=(0, 6))

        sub = ctk.CTkLabel(
            self.login_frame,
            text="Sign in to continue tracking",
            font=ctk.CTkFont(size=12),
            text_color="#64748B"
        )
        sub.grid(row=2, column=0, pady=(0, 24))

        # Email
        self.email_entry = ctk.CTkEntry(
            self.login_frame,
            placeholder_text="Email address",
            width=300, height=44,
            corner_radius=10,
            border_color="#334155",
            fg_color="#0F172A",
            font=ctk.CTkFont(size=14)
        )
        self.email_entry.grid(row=3, column=0, padx=40, pady=(0, 12))

        # Password
        self.password_entry = ctk.CTkEntry(
            self.login_frame,
            placeholder_text="Password",
            show="*",
            width=300, height=44,
            corner_radius=10,
            border_color="#334155",
            fg_color="#0F172A",
            font=ctk.CTkFont(size=14)
        )
        self.password_entry.grid(row=4, column=0, padx=40, pady=(0, 8))
        self.password_entry.bind("<Return>", lambda e: self.login_event())

        if error_message:
            error_frame = ctk.CTkFrame(self.login_frame, fg_color="#450A0A", corner_radius=8)
            error_frame.grid(row=5, column=0, padx=40, pady=(0, 8), sticky="ew")
            ctk.CTkLabel(
                error_frame,
                text=f"⚠  {error_message}",
                text_color="#FCA5A5",
                font=ctk.CTkFont(size=12)
            ).pack(padx=12, pady=8)

        self._login_button = ctk.CTkButton(
            self.login_frame,
            text="Sign In",
            command=self.login_event,
            width=300, height=46,
            corner_radius=10,
            fg_color=BRAND_COLOR,
            hover_color=BRAND_HOVER,
            font=ctk.CTkFont(size=15, weight="bold")
        )
        self._login_button.grid(row=6, column=0, padx=40, pady=(12, 36))

    def set_login_loading(self, loading: bool):
        """Toggle the login button between loading and normal state."""
        if not hasattr(self, '_login_button') or not self._login_button:
            return
        if loading:
            self._login_button.configure(text="Signing in...", state="disabled", fg_color="#334155")
        else:
            self._login_button.configure(text="Sign In", state="normal", fg_color=BRAND_COLOR)

    def login_event(self):
        email = self.email_entry.get()
        password = self.password_entry.get()
        self.on_login_callback(email, password)

    # ─── Attendance Screen ───────────────────────────────────────
    def show_attendance(self, user_name, user_email):
        if self.login_frame:
            self.login_frame.destroy()
            self.login_frame = None

        self.attendance_frame = ctk.CTkFrame(self, fg_color="#1E293B", corner_radius=16)
        self.attendance_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        self.attendance_frame.grid_columnconfigure(0, weight=1)

        # Brand strip
        brand_strip = ctk.CTkFrame(self.attendance_frame, fg_color="#0F172A", corner_radius=0, height=46)
        brand_strip.grid(row=0, column=0, sticky="ew")
        brand_strip.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            brand_strip, text="BIDWINNERS Tracker",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=BRAND_COLOR
        ).grid(row=0, column=0, pady=12)

        # Avatar circle + user info
        avatar_frame = ctk.CTkFrame(self.attendance_frame, fg_color="#0F172A", corner_radius=50, width=60, height=60)
        avatar_frame.grid(row=1, column=0, pady=(24, 0))
        avatar_label = ctk.CTkLabel(
            avatar_frame,
            text=user_name[0].upper() if user_name else "?",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color="white",
            width=60, height=60
        )
        avatar_label.pack()

        ctk.CTkLabel(
            self.attendance_frame,
            text=user_name,
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="#F1F5F9"
        ).grid(row=2, column=0, pady=(10, 2))

        ctk.CTkLabel(
            self.attendance_frame,
            text=user_email,
            font=ctk.CTkFont(size=12),
            text_color="#64748B"
        ).grid(row=3, column=0, pady=(0, 20))

        # Divider
        div = ctk.CTkFrame(self.attendance_frame, height=1, fg_color="#334155")
        div.grid(row=4, column=0, sticky="ew", padx=30, pady=(0, 20))

        # Privacy priority message
        self.privacy_label = ctk.CTkLabel(
            self.attendance_frame,
            text="Your privacy is our priority. The app operates\nin the background during office hours and captures\nscreenshots only while you are on duty at the office.",
            font=ctk.CTkFont(size=13),
            text_color="#94A3B8",
            justify="center"
        )
        self.privacy_label.grid(row=5, column=0, padx=40, pady=(0, 24))

        # Logout
        ctk.CTkButton(
            self.attendance_frame,
            text="Logout",
            command=self._on_logout_request,
            width=300, height=40,
            corner_radius=10,
            fg_color="transparent",
            border_width=1,
            border_color="#334155",
            text_color="#94A3B8",
            hover_color="#1E293B",
            font=ctk.CTkFont(size=13)
        ).grid(row=6, column=0, padx=40, pady=(16, 0))

        # Running hint
        ctk.CTkLabel(
            self.attendance_frame,
            text="🟢  Tracker is running in the background",
            font=ctk.CTkFont(size=11),
            text_color="#334155"
        ).grid(row=7, column=0, pady=(14, 16))

    def _on_check_in(self):
        pass

    def _on_check_out(self):
        pass

    def _on_logout_request(self):
        pwd = simpledialog.askstring(
            "Confirm Logout",
            "Enter admin password to logout:",
            show="*",
            parent=self
        )
        if pwd == self.admin_password:
            self.on_logout_callback()
        elif pwd is not None:
            messagebox.showerror("Access Denied", "Incorrect password. You cannot log out.", parent=self)

    def set_admin_password(self, password):
        """Update the admin password dynamically."""
        if password:
            self.admin_password = password

    # ─── Button State Helpers ────────────────────────────────────
    def set_attendance_status(self, checked_in: bool, checked_out: bool):
        """No-op: Attendance status is no longer displayed."""
        pass

    def _disable_button(self, btn, label):
        pass

    def _enable_button(self, btn, label, color, hover):
        btn.configure(
            state="normal",
            text=label,
            fg_color=color,
            hover_color=hover
        )

    def run(self):
        self.mainloop()
