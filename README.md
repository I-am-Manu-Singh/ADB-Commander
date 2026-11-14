# 📱 ADB Commander

ADB Commander is a sleek, macOS-optimized graphical interface for Android Debug Bridge (ADB). Designed with a modern "Glass" aesthetic inspired by macOS Sonoma/Sequoia, it brings powerful Android device management, file transferring, and debugging tools into a single, intuitive two-pane workspace.

Perfect for Android developers, QA testers, and power users who want a native-feeling desktop experience without constantly switching to the terminal.

## ✨ Key Features

### 📁 Advanced Dual-Pane File Manager
*   **Side-by-Side Navigation:** Browse your local Mac files and Android device (`/sdcard`) simultaneously.
*   **Native Drag & Drop:** Drag files directly between the two panes to push/pull. You can also drag files directly from the macOS Finder into the Android pane!
*   **Live Search & Inspector:** Instantly filter files in the current directory and view metadata/image thumbnails in the resizable Inspector pane.
*   **Smart Bookmarks:** Save frequent directories (like `/sdcard/DCIM` or `~/Downloads`) to custom dropdowns for instant access.

### 🛠️ Developer & Debugging Tools
*   **Color-Coded Logcat & Profiler:** A dedicated, robust Logcat window featuring:
    *   Android Studio-style color coding.
    *   Live fuzzy-search dropdown for filtering by installed Packages.
    *   Regex and Log Level (Verbose, Debug, Info, Warn, Error, Fatal) filters.
*   **App Management:** One-click APK installations and quick package uninstalls.
*   **Terminal Integration:** Open a native macOS Terminal instantly tethered to your device's ADB shell.

### 🎥 Media & Productivity
*   **One-Click Scrcpy Mirroring:** Launch an ultra-low latency, hardware-accelerated remote control window of your device.
*   **Custom Screen Recording:** Record your Android screen directly to your Mac. Prompts for custom resolutions (e.g., 1080x1920) and bitrates.
*   **Smart Screenshots:** Capture device screenshots that automatically save to your Mac *and* copy directly to your macOS System Clipboard. Detects and alerts on `FLAG_SECURE` blocks.
*   **Clipboard Injector:** Effortlessly paste long text, passwords, or URLs from your Mac clipboard directly into active text fields on your Android device.

---

## ⚙️ Prerequisites

This application is tailored for **macOS** and relies on a few underlying command-line tools.

1.  **Python 3.12+**
2.  **Homebrew** (for installing dependencies)
3.  **ADB & Scrcpy:**
    ```bash
    brew install android-platform-tools
    brew install scrcpy
    ```

### Python Dependencies
Install the required Python packages using pip:
```bash
pip install pillow tkinterdnd2
```
*(Optional) If you plan to package the app into a standalone macOS bundle, also install:*
```bash
pip install pyinstaller
```

---

## 🚀 How to Run

### Option 1: Run Directly via Python
Simply execute the main script from your terminal:
```bash
python3 main.py
```
*Note: To see the native macOS menu bar options (File, View, Tools) when running directly, ensure your terminal window has focus.*

### Option 2: Build a Standalone macOS App (`.app`)
You can package ADB Commander into a distributable macOS Application bundle using PyInstaller.

1. Ensure your custom icon (`app_icon.icns`) is in the project directory.
2. Run the build command:
   ```bash
   pyinstaller --noconfirm --windowed --name "ADB Commander" --icon=app_icon.icns main.py
   ```
3. Once complete, you will find `ADB Commander.app` inside the newly created `dist/` folder. You can move this to your `/Applications` folder.

---

## ⌨️ Keyboard Shortcuts

| Shortcut | Action |
| :--- | :--- |
| `Cmd + R` / `F5` | Refresh current directories (Mac and ADB) |
| `Cmd + A` | Select all items in the active pane |
| `Backspace` | Navigate up one directory folder |
| `Double-Click` | Open file (Mac) or enter folder |
| `Right-Click` | Open context menu (Delete, Rename, Move, etc.) |

---

## 💡 Troubleshooting

*   **"ADB not found" / "Scrcpy is not installed" inside the packaged `.app`:**
    macOS GUI apps do not inherit your terminal's `$PATH`. The app is hardcoded to look in standard Homebrew paths (`/opt/homebrew/bin` and `/usr/local/bin`). Ensure you installed these tools via Homebrew.
*   **Drag & Drop isn't working:**
    Ensure `tkinterdnd2` installed correctly. Sometimes, specific Python environments (like Conda) struggle with Tcl/Tk extensions on macOS. Standard python.org or Homebrew Python installations are recommended.
*   **Thumbnails aren't showing for large images:**
    For performance reasons, the app skips rendering thumbnails for files larger than 25MB over ADB.

---

## 📄 License
This project is open-source and free to use for personal and commercial projects. Customize it to fit your workflow!