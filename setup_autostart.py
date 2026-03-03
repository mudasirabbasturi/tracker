
import winreg
import sys
import os

def add_to_startup(name, script_path):
    # Determine pythonw.exe path
    python_exe = sys.executable
    pythonw_exe = python_exe.replace("python.exe", "pythonw.exe")
    
    if not os.path.exists(pythonw_exe):
        print(f"pythonw.exe not found at {pythonw_exe}, using {python_exe}")
        pythonw_exe = python_exe

    # Command to run
    command = f'"{pythonw_exe}" "{script_path}"'
    
    key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
    
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(key, name, 0, winreg.REG_SZ, command)
        winreg.CloseKey(key)
        print(f"Successfully added {name} to startup.")
    except Exception as e:
        print(f"Failed to add to startup: {e}")

if __name__ == "__main__":
    script_path = os.path.abspath("main.pyw")
    add_to_startup("TrackerApp", script_path)
