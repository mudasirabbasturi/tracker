import os
import sys
import json
import threading
import winreg
import pystray
from pystray import MenuItem as item
from PIL import Image, ImageDraw
import requests
import socket
from src.tracker import SystemTracker, DATA_DIR, PROJECT_ROOT
from src.ui import TrackerUI

CONFIG_FILE = os.path.join(DATA_DIR, "config.json")
LOCK_FILE = os.path.join(DATA_DIR, "tracker.lock")
APP_CONFIG_FILE = os.path.join(DATA_DIR, "config.json")

# ─── Load configurable API URL and other settings ────────────────────────────
def load_app_config():
    config = {}
    if os.path.exists(APP_CONFIG_FILE):
        try:
            with open(APP_CONFIG_FILE, "r") as f:
                config = json.load(f)
        except Exception:
            pass
    
    # Normalize API URL with default
    url = config.get("api_base_url") or "https://enterprise.bidwinners.net"
    if url and not (url.startswith("http://") or url.startswith("https://")):
        url = "http://" + url
    config["api_base_url"] = url.rstrip("/")
    
    # Load Admin Password and Interval with robust defaults
    config["admin_password"] = config.get("admin_password") or "bidenterprise#12"
    try:
        config["screenshot_interval"] = int(config.get("screenshot_interval") or 300)
    except (ValueError, TypeError):
        config["screenshot_interval"] = 300
    
    return config

_app_config = load_app_config()
API_BASE_URL = _app_config["api_base_url"]
ADMIN_PASSWORD = _app_config["admin_password"]
SCREENSHOT_INTERVAL = _app_config["screenshot_interval"]
SYNC_INTERVAL = int(_app_config.get("tracker_sync_interval") or 30)

tracker = None
ui = None
tray_icon = None

# ─── Windows Autostart ───────────────────────────────────────────────────────
def register_autostart():
    """Register the app to start automatically on Windows login."""
    try:
        app_path = os.path.abspath(sys.argv[0])
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0, winreg.KEY_SET_VALUE
        )
        python_path = os.path.join(os.path.dirname(sys.executable), "pythonw.exe")
        if not os.path.exists(python_path):
            python_path = sys.executable
        winreg.SetValueEx(key, "BidwinnersTracker", 0, winreg.REG_SZ, f'"{python_path}" "{app_path}"')
        winreg.CloseKey(key)
    except Exception as e:
        print(f"Autostart registration error: {e}")

# ─── Single Instance Lock ────────────────────────────────────────────────────
def is_already_running():
    """Checks if another instance is already running using a socket and signals it to show UI."""
    try:
        # Try to connect to a local port
        # Using a dedicated port for signaling
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1.0)
        result = sock.connect_ex(('127.0.0.1', 49152))
        
        if result == 0:
            # Successfully connected, meaning another instance is listening
            try:
                sock.sendall(b"SHOW_WINDOW")
                sock.close()
            except:
                pass
            return True
        sock.close()
        return False
    except:
        return False

def start_instance_listener():
    """Starts a socket listener to receive signals from other instances."""
    def _listener():
        try:
            server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server.bind(('127.0.0.1', 49152))
            server.listen(1)
            while True:
                conn, addr = server.accept()
                data = conn.recv(1024)
                if data == b"SHOW_WINDOW":
                    show_window()
                conn.close()
        except:
            pass
    threading.Thread(target=_listener, daemon=True).start()

def remove_lock():
    pass

# ─── Tray Icon ───────────────────────────────────────────────────────
def create_image():
    # Attempt to load the custom icon from assets
    icon_path = os.path.join(PROJECT_ROOT, "assets", "icon.png")
    if getattr(sys, 'frozen', False):
        # When running as EXE, assets is in sys._MEIPASS
        icon_path = os.path.join(sys._MEIPASS, "assets", "icon.png")
    
    if os.path.exists(icon_path):
        try:
            return Image.open(icon_path)
        except Exception as e:
            print(f"Error loading icon: {e}")

    # Fallback to generated image
    image = Image.new('RGB', (64, 64), (15, 23, 42))
    dc = ImageDraw.Draw(image)
    dc.ellipse((8, 8, 56, 56), fill="#2563EB")
    dc.ellipse((20, 20, 44, 44), fill="#F1F5F9")
    return image

# ─── Config (session) ────────────────────────────────────────────────────────
def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        except:
            pass
    return {}

def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f)

# ─── API Calls ───────────────────────────────────────────────────────────────
def api_login(email, password):
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/login",
            json={"email": email, "password": password},
            timeout=10
        )
        if response.status_code == 200:
            user_data = response.json().get("user")
            if user_data:
                # Notify server we are online immediately after successful login
                update_server_status(user_data.get('id'), 'online')
            return user_data
    except Exception as e:
        print(f"Login connection error: {e}")
    return None

def update_server_status(user_id, status):
    """Notify Laravel backend of the user's online/offline status."""
    def _do_update():
        try:
            requests.post(
                f"{API_BASE_URL}/api/track/update-status",
                json={"user_id": user_id, "status": status},
                timeout=5
            )
        except:
            pass
    threading.Thread(target=_do_update, daemon=True).start()
    
def sync_settings(user_data):
    """Fetch latest settings and permissions from API periodically."""
    if not user_data:
        return
        
    def _do_sync():
        global ADMIN_PASSWORD, API_BASE_URL, SCREENSHOT_INTERVAL, SYNC_INTERVAL, tracker
        import datetime
        now_str = datetime.datetime.now().strftime("%H:%M:%S")
        try:
            # 1. Fetch Global Settings (Interval, Password, Allowed IPs, Sync Interval)
            resp = requests.get(f"{API_BASE_URL}/api/track/settings", timeout=10)
            settings = {}
            if resp.status_code == 200:
                settings = resp.json()
            
            # 2. Fetch/Refresh User Permission Status
            user_resp = requests.get(f"{API_BASE_URL}/api/track/users", timeout=10)
            users_list = user_resp.json() if user_resp.status_code == 200 else []
            # Safety: Compare IDs as strings to avoid type mismatch
            curr_user = next((u for u in users_list if str(u['id']) == str(user_data['id'])), user_data)
            
            # 3. Determine if Tracking is Allowed
            allowed_ips = settings.get("tracker_allowed_ips", [])
            
            # Get local public IP
            try:
                my_ip = requests.get('https://api.ipify.org', timeout=5).text
            except:
                my_ip = "unknown"

            is_on_office_ip = my_ip in allowed_ips
            is_manual_allowed = bool(curr_user.get('is_permission_granted'))
            
            tracking_allowed = is_on_office_ip or is_manual_allowed
            
            # 4. Apply Settings and Logic (Password, Interval)
            config_changed = False
            config = load_app_config()
            
            new_password = settings.get("tracker_admin_password")
            if new_password and new_password != ADMIN_PASSWORD:
                ADMIN_PASSWORD = new_password
                config["admin_password"] = new_password
                config_changed = True
                if ui: ui.set_admin_password(new_password)
            
            try:
                interval = int(settings.get("screenshot_interval", 300))
            except:
                interval = 300

            if interval != SCREENSHOT_INTERVAL:
                SCREENSHOT_INTERVAL = interval
                config["screenshot_interval"] = interval
                config_changed = True
                if tracker: tracker.screenshot_interval = interval

            new_sync_interval = settings.get("tracker_sync_interval")
            if new_sync_interval and int(new_sync_interval) != SYNC_INTERVAL:
                SYNC_INTERVAL = int(new_sync_interval)
                config["tracker_sync_interval"] = SYNC_INTERVAL
                config_changed = True

            new_allowed_ips = settings.get("tracker_allowed_ips", [])
            if new_allowed_ips != config.get("allowed_ips"):
                config["allowed_ips"] = new_allowed_ips
                config_changed = True

            if config_changed:
                with open(APP_CONFIG_FILE, "w") as f:
                    json.dump(config, f)

            # 5. Start/Stop Tracker based on Permission
            if tracking_allowed:
                if not tracker or not tracker.running:
                    print(f"[{now_str}] Permission GRANTED (IP: {my_ip}, Manual: {is_manual_allowed}). Starting tracker...")
                    start_tracker(curr_user, interval=SCREENSHOT_INTERVAL)
            else:
                if tracker and tracker.running:
                    print(f"[{now_str}] Permission DENIED (IP: {my_ip}, Manual: {is_manual_allowed}). Stopping tracker...")
                    tracker.stop()

            print(f"[{now_str}] Sync Done. IP: {my_ip}, Allowed: {tracking_allowed}")

        except Exception as e:
            print(f"[{now_str}] Sync error: {e}")
        finally:
            # Reschedule the next sync
            current_config = load_config()
            if current_config.get("user"):
                threading.Timer(SYNC_INTERVAL, sync_settings, [current_config.get("user")]).start()
            
    threading.Thread(target=_do_sync, daemon=True).start()

# ─── Auth Flow ───────────────────────────────────────────────────────────────
def on_login(email, password):
    global tracker, ui
    def _do_login():
        if ui:
            ui.set_login_loading(True)
        user_data = api_login(email, password)
        if ui:
            ui.set_login_loading(False)
        if user_data:
            config = load_config()
            config["user"] = user_data
            save_config(config)
            start_tracker(user_data)
            if ui:
                ui.show_attendance(user_data.get('name'), user_data.get('email'))
                update_tray_menu(user_data.get('name'))
                sync_settings(user_data)
        else:
            if ui:
                ui.show_login(error_message="Invalid credentials or server unreachable")
    threading.Thread(target=_do_login, daemon=True).start()

def on_logout():
    global tracker, ui
    config = load_config()
    user_data = config.get("user")
    
    if user_data:
        # Notify server we are going offline
        update_server_status(user_data.get('id'), 'offline')
        
    if tracker:
        tracker.stop()
        tracker = None
        
    # CLEAR USER FROM CONFIG (Session Expire)
    if "user" in config:
        del config["user"]
    save_config(config)
    
    if ui:
        ui.show_login()
    update_tray_menu("Not Logged In")

def start_tracker(user_data, interval=300):
    global tracker
    if tracker:
        tracker.stop()
    tracker = SystemTracker(user_data.get('id'), screenshot_interval=interval)
    tracker.start()

# ─── Tray / Window ───────────────────────────────────────────────────────────
def show_window(icon=None, item=None):
    if ui:
        ui.deiconify()
        ui.lift()
        ui.focus_force()
        ui.attributes("-topmost", True)
        ui.after(100, lambda: ui.attributes("-topmost", False))

def toggle_window(icon=None, item=None):
    if ui:
        if ui.state() == "withdrawn" or ui.state() == "iconic":
            show_window()
        else:
            hide_window()

def hide_window():
    if ui:
        ui.withdraw()

def quit_app(icon=None, item=None):
    global tracker, tray_icon, ui
    from tkinter import simpledialog, messagebox
    import tkinter as _tk

    # Ask for admin password before allowing exit
    root = _tk.Tk()
    root.withdraw()
    pwd = simpledialog.askstring(
        "Confirm Exit",
        "Enter admin password to exit the app:",
        show="*",
        parent=root
    )
    root.destroy()

    if pwd != ADMIN_PASSWORD:
        if pwd is not None:  # None means user cancelled
            from tkinter import messagebox as mb
            import tkinter as tk2
            r = tk2.Tk(); r.withdraw()
            mb.showerror("Access Denied", "Incorrect password. You cannot exit.", parent=r)
            r.destroy()
        return

    # Password correct — log out and exit cleanly
    if tracker:
        tracker.stop()
    if tray_icon:
        tray_icon.stop()
    if ui:
        ui.quit()
    remove_lock()

def update_tray_menu(user_name):
    global tray_icon
    menu = pystray.Menu(
        item(f'User: {user_name}', lambda: None, enabled=False),
        item('Show/Hide Tracker', toggle_window, default=True)
    )
    if tray_icon:
        tray_icon.menu = menu

def setup_tray(user_name="Not Logged In"):
    global tray_icon
    menu = pystray.Menu(
        item(f'User: {user_name}', lambda: None, enabled=False),
        item('Show/Hide Tracker', toggle_window, default=True)
    )
    tray_icon = pystray.Icon("BidwinnersTracker", create_image(), "Bidwinners Tracker", menu)
    tray_icon.run_detached()

# ─── Main ─────────────────────────────────────────────────────────────────────
def main():
    global ui, tracker

    # Register autostart so app launches on every Windows startup
    register_autostart()

    if is_already_running():
        return

    # Start listener for other instances
    start_instance_listener()

    config = load_config()
    user_data = config.get("user")

    ui = TrackerUI(on_login, on_logout, None, None)
    ui.protocol("WM_DELETE_WINDOW", hide_window)

    if user_data:
        setup_tray(user_data.get('name'))
        ui.set_admin_password(ADMIN_PASSWORD)
        sync_settings(user_data)
        
        # Start with persisted interval
        start_tracker(user_data, interval=SCREENSHOT_INTERVAL)
        ui.show_attendance(user_data.get('name'), user_data.get('email'))
    else:
        setup_tray()
        ui.show_login()

    ui.run()

if __name__ == "__main__":
    main()
