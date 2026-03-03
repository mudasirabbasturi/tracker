
# Employee Tracker Agent

This is a Windows desktop background agent that tracks user activity (Active Window, Idle Time, Sleep/Wake) and stores it locally for future sync with a Laravel API.

## Features
- **Auto-starts** on Windows login (via Registry).
- **Silent** background operation (System Tray icon with options to Change ID and Open Data Folder).
- **One-time Login** via employee ID (stored securely in `~/.tracker_app/config.json`).
- **Offline Queue** stored locally in `~/.tracker_app/queue.json` (cleared automatically after future API sync).
- **Real-time Ready**: Background sync worker already implemented (currently a stub, ready for Laravel API endpoint).
- **Lightweight**: Uses Python `pywin32` for efficient system API hooks and minimal resources.


## Installation

1.  **Install Python Dependencies:**
    ```powershell
    pip install -r requirements.txt
    ```

2.  **Run the Agent:**
    Double-click `main.pyw` or run:
    ```powershell
    pythonw main.pyw
    ```
    On first run, it will ask for your Employee ID.

3.  **Enable Auto-Start:**
    Run the setup script to add the agent to Windows startup:
    ```powershell
    python setup_autostart.py
    ```

## Logs & Data
- **Logs:** `f:\dashboard\tracker-apps\data\tracker.log`
- **Data Queue:** `f:\dashboard\tracker-apps\data\queue.json`
- **Config:** `f:\dashboard\tracker-apps\data\config.json`


## Future Integration
The `EventQueueManager` class in `src/tracker.py` is designed to be easily extended to push data to a Laravel API endpoint instead of just saving to a local JSON file.


Prompts for the admin password (bidenterprise#12) — same as the Logout button.



get IPs from
https://api.ipify.org/

close the exe 
taskkill /IM pythonw.exe /F
and restart it 
main.pyw