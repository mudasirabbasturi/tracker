
import datetime
import io
import json
import logging
import os
import threading
import time
import requests
from PIL import ImageGrab

# --- Configuration ---
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
LOG_FILE = os.path.join(DATA_DIR, "tracker.log")
APP_CONFIG_FILE = os.path.join(PROJECT_ROOT, "config.json")

def load_app_config():
    if os.path.exists(APP_CONFIG_FILE):
        try:
            with open(APP_CONFIG_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

_app_config = load_app_config()
API_BASE_URL = _app_config.get("api_base_url", "https://enterprise.bidwinners.net").rstrip("/")

# Ensure data directory exists
os.makedirs(DATA_DIR, exist_ok=True)

# Logging Setup with Rotation (Prevents file from growing too large)
from logging.handlers import RotatingFileHandler

# Max size 1MB, keep 2 backup files
file_handler = RotatingFileHandler(LOG_FILE, maxBytes=1 * 1024 * 1024, backupCount=2)
logging.basicConfig(
    handlers=[file_handler],
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

class SystemTracker:
    @property
    def screenshot_interval(self):
        return self._screenshot_interval

    @screenshot_interval.setter
    def screenshot_interval(self, value):
        old_val = getattr(self, '_screenshot_interval', None)
        if old_val != value:
            logging.info(f"Screenshot interval changed from {old_val} to {value} seconds.")
        self._screenshot_interval = value

    def __init__(self, employee_id: str, screenshot_interval: int = 300):
        self.employee_id = employee_id
        self.running = False
        
        # Screenshot tracking
        self._screenshot_interval = screenshot_interval
        # Initialize to 0 so the first screenshot happens immediately on start
        self.last_screenshot_time = 0 
        
        # Polling for remote triggers
        self.polling_interval = 10 # Check every 10 seconds
        self.last_polling_time = 0
        
        # Shutdown flag
        self._stop_event = threading.Event()
        
    def start(self):
        """Starts the tracking loop."""
        self.running = True
        
        # Start monitoring thread (screenshots)
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True, name="MonitorThread")
        self.monitor_thread.start()
        logging.info("SystemTracker started.")

    def stop(self):
        self.running = False
        self._stop_event.set()
        
        if hasattr(self, 'monitor_thread') and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=2)
        logging.info("SystemTracker stopped.")

    def _monitor_loop(self):
        """Main loop for periodic screenshots and remote triggers."""
        while self.running:
            try:
                current_time = time.time()
                
                # Periodic Screenshot (5 mins)
                if current_time - self.last_screenshot_time >= self.screenshot_interval:
                    self._capture_and_upload_screenshot()
                    self.last_screenshot_time = current_time
                
                # Check for remote trigger (10 seconds)
                if current_time - self.last_polling_time >= self.polling_interval:
                    self._check_remote_trigger()
                    self.last_polling_time = current_time
                    
            except Exception as e:
                logging.error(f"Monitor loop error: {e}")
            
            time.sleep(1) # Base tick

    def _check_remote_trigger(self):
        """Checks if the admin requested a manual screenshot."""
        try:
            api_url = f"{API_BASE_URL}/api/track/screenshot/pending/{self.employee_id}"
            response = requests.get(api_url, timeout=5)
            if response.status_code == 200 and response.json().get('pending'):
                logging.info("Remote screenshot trigger detected!")
                self._capture_and_upload_screenshot()
        except Exception as e:
            # Don't log polling errors too often to avoid log bloat
            pass

    def _capture_and_upload_screenshot(self):
        """Captures a screenshot and uploads it to the API."""
        try:
            logging.info("Capturing screenshot...")
            screenshot = ImageGrab.grab()
            
            # Save to buffer
            buf = io.BytesIO()
            screenshot.save(buf, format='JPEG', quality=70)
            buf.seek(0)
            
            # Upload to API
            api_url = f"{API_BASE_URL}/api/track/screenshot"
            files = {
                'screenshot': ('screenshot.jpg', buf, 'image/jpeg')
            }
            data = {
                'user_id': self.employee_id,
                'timestamp': datetime.datetime.now().isoformat()
            }
            
            response = requests.post(api_url, files=files, data=data, timeout=30)
            if response.status_code == 200:
                logging.info("Screenshot uploaded successfully.")
            else:
                logging.warning(f"Screenshot upload failed: {response.status_code} - {response.text}")
                
        except Exception as e:
            logging.error(f"Failed to capture/upload screenshot: {e}")


