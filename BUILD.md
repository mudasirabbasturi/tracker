# Bidwinners Tracker — Build Guide

## How to Build the Windows Installer

### Step 1: Install Dependencies

Open a terminal in the `tracker-apps` folder and run:

```powershell
python -m pip install pyinstaller -r requirements.txt
```

### Step 2: Build the EXE with PyInstaller

```powershell
python -m PyInstaller BidwinnersTracker.spec --clean
```

This creates `dist/BidwinnersTracker.exe` — a single self-contained executable.

> **Test it first:** Run `dist\BidwinnersTracker.exe` to make sure it works before building the installer.

### Step 3: Build the Windows Installer

1. Download and install **Inno Setup** from: https://jrsoftware.org/isinfo.php (free)
2. Open `installer.iss` in the Inno Setup Compiler.
3. Click **Build → Compile** (or press `F9`).
4. The installer will be in `installer_output/BidwinnersTracker_Setup_v1.0.0.exe`

### What the Installer Does

- Asks for the **Server URL** during installation (e.g. `https://my-company.com`)
- Writes `config.json` automatically with that URL
- Creates a desktop shortcut
- Launches the app after install

---

## Updating the Domain Later

If the server URL changes, just edit `config.json` in the install folder (default: `C:\Program Files\Bidwinners Tracker\config.json`):

```json
{
  "api_base_url": "https://your-new-domain.com"
}
```

---

## Requirements for the installer machine

Only Python needs to be installed on the **build machine** (the PC that runs the build steps above).

The **end-user PCs** that receive `BidwinnersTracker_Setup_v1.0.0.exe` do **NOT** need Python installed — everything is bundled inside the `.exe`.
