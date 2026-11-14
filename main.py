import os
import re
import shutil
import subprocess
import tempfile
import threading
import time
import queue
import tkinter as tk
from datetime import datetime
from tkinter import filedialog, messagebox, simpledialog, ttk

try:
    from PIL import Image, ImageDraw, ImageTk
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

try:
    from tkinterdnd2 import COPY, DND_FILES, TkinterDnD
    HAS_DND2 = True
except ImportError:
    HAS_DND2 = False

def find_adb_binary():
    adb = shutil.which("adb")
    if adb:
        return adb
    candidates = [
        "/opt/homebrew/bin/adb",
        "/usr/local/bin/adb",
        os.path.expanduser("~/Library/Android/sdk/platform-tools/adb"),
    ]
    for path in candidates:
        if os.path.isfile(path) and os.access(path, os.X_OK):
            return path
    return "adb"

ADB_BIN = find_adb_binary()

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".heic"}
VIDEO_EXTS = {".mp4", ".mkv", ".mov", ".avi", ".webm", ".3gp"}
AUDIO_EXTS = {".mp3", ".wav", ".flac", ".aac", ".ogg", ".m4a"}
ARCHIVE_EXTS = {".zip", ".rar", ".7z", ".tar", ".gz", ".bz2"}
DOC_EXTS = {".pdf", ".doc", ".docx", ".txt", ".md", ".csv", ".xlsx", ".ppt", ".pptx"}

GLASS_BG = "#12151C"
GLASS_PANEL = "#191D26"
GLASS_ELEVATED = "#212632"
GLASS_BORDER = "#2F3646"
GLASS_HOVER = "#2A3242"
ACCENT_BLUE = "#0A84FF"
ACCENT_GREEN = "#30D158"
ACCENT_AMBER = "#FF9F0A"
ACCENT_RED = "#FF453A"
TEXT_PRIMARY = "#F5F7FA"
TEXT_SECONDARY = "#9BA3B4"
TEXT_DARK = "#000000" # Explicit dark text for standard entry boxes

class VectorIconFactory:
    def __init__(self):
        self._cache = {}

    def get(self, name, size=16, color=TEXT_PRIMARY):
        key = (name, size, color)
        if key in self._cache:
            return self._cache[key]
        if HAS_PIL:
            img = self._draw_pil_icon(name, size, color)
            photo = ImageTk.PhotoImage(img)
        else:
            photo = self._draw_tk_fallback(name, size, color)
        self._cache[key] = photo
        return photo

    def _draw_pil_icon(self, name, size, color):
        # Draw on a fixed 64x64 high-res canvas, then smoothly resize to any requested size
        scale = 4
        s = 64
        img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        w = max(2, int(1.6 * scale))
        pad = 2 * scale

        if name == "folder":
            d.rounded_rectangle([pad, 4 * scale, s - pad, s - 3 * scale], radius=3 * scale, fill="#3B82F6")
            d.rounded_rectangle([pad, 2.5 * scale, 8 * scale, 6 * scale], radius=2 * scale, fill="#60A5FA")
        elif name == "image":
            d.rounded_rectangle([pad, pad, s - pad, s - pad], radius=2 * scale, outline="#34D399", width=w)
            d.ellipse([4.5 * scale, 4.5 * scale, 7 * scale, 7 * scale], fill="#34D399")
            d.polygon([(3 * scale, s - 3 * scale), (7 * scale, 8 * scale), (10 * scale, 11 * scale), (12 * scale, 9 * scale), (s - 3 * scale, s - 3 * scale)], fill="#34D399")
        elif name == "video":
            d.rounded_rectangle([pad, 3 * scale, s - pad, s - 3 * scale], radius=2 * scale, outline="#F472B6", width=w)
            d.polygon([(6.5 * scale, 5.5 * scale), (6.5 * scale, 10.5 * scale), (11 * scale, 8 * scale)], fill="#F472B6")
        elif name == "audio":
            d.ellipse([3.5 * scale, 9.5 * scale, 7.5 * scale, 13.5 * scale], fill="#A78BFA")
            d.ellipse([9.5 * scale, 8.5 * scale, 13.5 * scale, 12.5 * scale], fill="#A78BFA")
            d.line([(7 * scale, 11 * scale), (7 * scale, 3.5 * scale), (13 * scale, 2.5 * scale), (13 * scale, 10 * scale)], fill="#A78BFA", width=w)
        elif name == "apk":
            d.pieslice([3.5 * scale, 3 * scale, 12.5 * scale, 11 * scale], 180, 360, fill="#30D158")
            d.rectangle([3.5 * scale, 7.5 * scale, 12.5 * scale, 13.5 * scale], fill="#30D158")
        elif name == "archive":
            d.rounded_rectangle([pad, pad, s - pad, s - pad], radius=2 * scale, outline="#FBBF24", width=w)
            d.line([(8 * scale, pad), (8 * scale, s - pad)], fill="#FBBF24", width=w)
            d.rectangle([6.5 * scale, 6 * scale, 9.5 * scale, 9 * scale], fill="#FBBF24")
        elif name == "doc":
            d.polygon([(3 * scale, pad), (10 * scale, pad), (13 * scale, 5 * scale), (13 * scale, s - pad), (3 * scale, s - pad)], outline="#93C5FD", width=w)
            d.line([(5 * scale, 8 * scale), (11 * scale, 8 * scale)], fill="#93C5FD", width=w)
            d.line([(5 * scale, 11 * scale), (11 * scale, 11 * scale)], fill="#93C5FD", width=w)
        elif name == "file":
            d.polygon([(3 * scale, pad), (10 * scale, pad), (13 * scale, 5 * scale), (13 * scale, s - pad), (3 * scale, s - pad)], outline="#9CA3AF", width=w)
        elif name == "up":
            d.line([(8 * scale, 13 * scale), (8 * scale, 3 * scale)], fill=color, width=w)
            d.line([(4 * scale, 7 * scale), (8 * scale, 3 * scale), (12 * scale, 7 * scale)], fill=color, width=w)
        elif name == "refresh":
            d.arc([3 * scale, 3 * scale, 13 * scale, 13 * scale], 30, 320, fill=color, width=w)
            d.polygon([(11 * scale, 2 * scale), (14 * scale, 5 * scale), (10 * scale, 6 * scale)], fill=color)
        elif name == "search":
            d.ellipse([2.5 * scale, 2.5 * scale, 10.5 * scale, 10.5 * scale], outline=color, width=w)
            d.line([(9.5 * scale, 9.5 * scale), (13.5 * scale, 13.5 * scale)], fill=color, width=w)
        elif name == "right":
            d.line([(3 * scale, 8 * scale), (13 * scale, 8 * scale)], fill=color, width=w)
            d.line([(9 * scale, 4 * scale), (13 * scale, 8 * scale), (9 * scale, 12 * scale)], fill=color, width=w)
        elif name == "left":
            d.line([(13 * scale, 8 * scale), (3 * scale, 8 * scale)], fill=color, width=w)
            d.line([(7 * scale, 4 * scale), (3 * scale, 8 * scale), (7 * scale, 12 * scale)], fill=color, width=w)
        elif name == "new_folder":
            d.rounded_rectangle([pad, 4 * scale, s - pad, s - 3 * scale], radius=2 * scale, outline=color, width=w)
            d.line([(8 * scale, 6.5 * scale), (8 * scale, 11.5 * scale)], fill=color, width=w)
            d.line([(5.5 * scale, 9 * scale), (10.5 * scale, 9 * scale)], fill=color, width=w)
        elif name == "trash":
            d.line([(3 * scale, 4.5 * scale), (13 * scale, 4.5 * scale)], fill=color, width=w)
            d.rectangle([4.5 * scale, 4.5 * scale, 11.5 * scale, 13.5 * scale], outline=color, width=w)
            d.line([(6.5 * scale, 2.5 * scale), (9.5 * scale, 2.5 * scale)], fill=color, width=w)
        elif name == "camera":
            d.rounded_rectangle([2 * scale, 4 * scale, 14 * scale, 13 * scale], radius=2 * scale, outline=color, width=w)
            d.ellipse([6 * scale, 6.5 * scale, 10 * scale, 10.5 * scale], outline=color, width=w)
        elif name == "terminal":
            d.rounded_rectangle([2 * scale, 3 * scale, 14 * scale, 13 * scale], radius=2 * scale, outline=color, width=w)
            d.line([(4.5 * scale, 6 * scale), (7 * scale, 8 * scale), (4.5 * scale, 10 * scale)], fill=color, width=w)
            d.line([(8 * scale, 10 * scale), (11 * scale, 10 * scale)], fill=color, width=w)
        elif name == "device":
            d.rounded_rectangle([4 * scale, 1.5 * scale, 12 * scale, 14.5 * scale], radius=2 * scale, outline=color, width=w)
            d.line([(7 * scale, 12.5 * scale), (9 * scale, 12.5 * scale)], fill=color, width=w)
        elif name == "mac":
            d.rounded_rectangle([2 * scale, 2.5 * scale, 14 * scale, 11.5 * scale], radius=1.5 * scale, outline=color, width=w)
            d.line([(1 * scale, 13 * scale), (15 * scale, 13 * scale)], fill=color, width=w)
        elif name == "info":
            d.ellipse([2 * scale, 2 * scale, 14 * scale, 14 * scale], outline=color, width=w)
            d.line([(8 * scale, 7 * scale), (8 * scale, 11.5 * scale)], fill=color, width=w)
            d.ellipse([7.2 * scale, 4.3 * scale, 8.8 * scale, 5.8 * scale], fill=color)
        elif name == "finder":
            d.rounded_rectangle([2 * scale, 2 * scale, 14 * scale, 14 * scale], radius=3 * scale, outline=color, width=w)
            d.line([(8 * scale, 2 * scale), (8 * scale, 14 * scale)], fill=color, width=w)

        return img.resize((size, size), Image.Resampling.LANCZOS)

    def _draw_tk_fallback(self, name, size, color):
        photo = tk.PhotoImage(width=size, height=size)
        photo.put(color, to=(3, 3, size - 3, size - 3))
        return photo

def classify_file_icon(name, is_dir=False):
    if is_dir:
        return "folder"
    ext = os.path.splitext(name)[1].lower()
    if ext in IMAGE_EXTS:
        return "image"
    if ext in VIDEO_EXTS:
        return "video"
    if ext in AUDIO_EXTS:
        return "audio"
    if ext in ARCHIVE_EXTS:
        return "archive"
    if ext in DOC_EXTS:
        return "doc"
    if ext == ".apk":
        return "apk"
    return "file"

def format_size(size_bytes):
    if size_bytes is None or size_bytes < 0:
        return "—"
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if size_bytes < 1024:
            return f"{size_bytes:.0f} {unit}" if unit == "B" else f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} PB"

class ADBLogcatWindow:
    def __init__(self, parent, device_id, adb_bin, theme_colors):
        self.parent = parent
        self.device_id = device_id
        self.adb_bin = adb_bin
        self.colors = theme_colors
        
        self.window = tk.Toplevel(parent)
        self.window.title(f"Logcat & Profiler - {device_id}")
        self.window.geometry("1100x700")
        self.window.configure(bg=self.colors['GLASS_BG'])
        
        self.log_process = None
        self.is_running = False
        self.log_queue = queue.Queue()
        
        self.packages = []
        self._load_packages()
        
        self._build_ui()
        self.start_logcat()

    def _filter_packages(self, event):
        if event.keysym in ("Up", "Down", "Left", "Right", "Return", "BackSpace"):
            return
        query = self.package_var.get().lower()
        if query == "":
            self.package_cb["values"] = self.packages
        else:
            filtered = [pkg for pkg in self.packages if query in pkg.lower()]
            self.package_cb["values"] = filtered if filtered else ["No matches found"]
        # Trigger dropdown opening automatically while typing
        self.package_cb.event_generate('<Down>')

    def _load_packages(self):
        try:
            res = subprocess.run([self.adb_bin, "-s", self.device_id, "shell", "pm", "list", "packages", "-3"], capture_output=True, text=True)
            if res.returncode == 0:
                self.packages = [line.strip().split(':')[1] for line in res.stdout.splitlines() if line.startswith('package:')]
                self.packages.insert(0, "All Packages")
        except Exception:
            pass

    def _build_ui(self):
        toolbar = tk.Frame(self.window, bg=self.colors['GLASS_PANEL'], padx=10, pady=10)
        toolbar.pack(fill=tk.X)

        tk.Label(toolbar, text="Level:", bg=self.colors['GLASS_PANEL'], fg=self.colors['TEXT_PRIMARY']).pack(side=tk.LEFT)
        self.level_var = tk.StringVar(value="V")
        level_cb = ttk.Combobox(toolbar, textvariable=self.level_var, values=["V", "D", "I", "W", "E", "F"], width=3, state="readonly")
        level_cb.pack(side=tk.LEFT, padx=(5, 15))
        level_cb.bind("<<ComboboxSelected>>", lambda e: self.restart_logcat())
        
        tk.Label(toolbar, text="Package/PID:", bg=self.colors['GLASS_PANEL'], fg=self.colors['TEXT_PRIMARY']).pack(side=tk.LEFT)
        self.package_var = tk.StringVar(value="All Packages")
        self.package_cb = ttk.Combobox(toolbar, textvariable=self.package_var, values=self.packages, width=25)
        self.package_cb.pack(side=tk.LEFT, padx=(5, 15))
        
        # Bindings for fuzzy search
        self.package_cb.bind("<KeyRelease>", self._filter_packages)
        self.package_cb.bind("<Return>", lambda e: self.restart_logcat())
        self.package_cb.bind("<<ComboboxSelected>>", lambda e: self.restart_logcat())

        tk.Label(toolbar, text="Search Regex:", bg=self.colors['GLASS_PANEL'], fg=self.colors['TEXT_PRIMARY']).pack(side=tk.LEFT)
        # Using standard tk.Entry to ensure reliable dark text rendering on macOS
        self.filter_entry = tk.Entry(toolbar, width=25, bg="#FFFFFF", fg=TEXT_DARK, insertbackground=TEXT_DARK, font=("SF Pro Text", 12))
        self.filter_entry.pack(side=tk.LEFT, padx=(5, 15))
        self.filter_entry.bind("<Return>", lambda e: self.restart_logcat())

        ttk.Button(toolbar, text="Clear", command=self.clear_logs).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Copy All", command=self.copy_logs).pack(side=tk.LEFT, padx=2)
        
        self.btn_toggle = ttk.Button(toolbar, text="Stop", command=self.toggle_logcat)
        self.btn_toggle.pack(side=tk.RIGHT, padx=2)

        self.autoscroll_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(toolbar, text="Auto-Scroll", variable=self.autoscroll_var).pack(side=tk.RIGHT, padx=10)

        text_frame = tk.Frame(self.window, bg=self.colors['GLASS_BG'])
        text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.text_widget = tk.Text(
            text_frame, bg=self.colors['GLASS_ELEVATED'], fg=self.colors['TEXT_PRIMARY'],
            font=("SF Mono", 11), wrap=tk.NONE, insertbackground=self.colors['TEXT_PRIMARY']
        )
        sb_y = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=self.text_widget.yview)
        sb_x = ttk.Scrollbar(text_frame, orient=tk.HORIZONTAL, command=self.text_widget.xview)
        self.text_widget.configure(yscrollcommand=sb_y.set, xscrollcommand=sb_x.set)

        self.text_widget.grid(row=0, column=0, sticky="nsew")
        sb_y.grid(row=0, column=1, sticky="ns")
        sb_x.grid(row=1, column=0, sticky="ew")
        text_frame.grid_rowconfigure(0, weight=1)
        text_frame.grid_columnconfigure(0, weight=1)

        self.text_widget.tag_config("V", foreground=self.colors['TEXT_SECONDARY'])
        self.text_widget.tag_config("D", foreground="#60A5FA")
        self.text_widget.tag_config("I", foreground="#34D399")
        self.text_widget.tag_config("W", foreground="#FBBF24")
        self.text_widget.tag_config("E", foreground="#FF453A", font=("SF Mono", 11, "bold"))
        self.text_widget.tag_config("F", foreground="#FFFFFF", background="#FF453A", font=("SF Mono", 11, "bold"))

        self.window.protocol("WM_DELETE_WINDOW", self.on_close)

    def start_logcat(self):
        self.clear_logs()
        cmd = [self.adb_bin, "-s", self.device_id, "logcat", "-v", "threadtime"]
        
        pkg_filter = self.package_var.get().strip()
        if pkg_filter and pkg_filter != "All Packages":
            if pkg_filter.isdigit():
                cmd.extend(["--pid", pkg_filter])
            else:
                try:
                    res = subprocess.run([self.adb_bin, "-s", self.device_id, "shell", "pidof", pkg_filter], capture_output=True, text=True)
                    if res.returncode == 0 and res.stdout.strip():
                        pids = res.stdout.strip().split()
                        if pids:
                            cmd.extend(["--pid", pids[0]]) 
                    else:
                        # Fallback if pidof fails
                        cmd.extend(["-e", pkg_filter])
                except Exception:
                    cmd.extend(["-e", pkg_filter])

        regex_filter = self.filter_entry.get().strip()
        if regex_filter:
            cmd.extend(["-e", regex_filter])

        level = self.level_var.get()
        if level != "V":
            cmd.append(f"*:{level}")

        self.log_process = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, 
            text=True, encoding="utf-8", errors="replace"
        )
        self.is_running = True
        self.btn_toggle.config(text="Stop")
        
        threading.Thread(target=self._read_logs, daemon=True).start()
        self.window.after(100, self._process_log_queue)

    def _read_logs(self):
        while self.is_running and self.log_process:
            try:
                line = self.log_process.stdout.readline()
                if not line:
                    # Edge Case: Stream closed (Device disconnected or process killed)
                    self.log_queue.put("--- LOG STREAM ENDED (Device Disconnected?) ---\n")
                    break
                self.log_queue.put(line)
            except Exception as e:
                self.log_queue.put(f"--- STREAM ERROR: {str(e)} ---\n")
                break
        
        # Reset UI button safely if stream breaks unexpectedly
        if self.is_running:
            self.is_running = False
            self.window.after(0, lambda: self.btn_toggle.config(text="Start"))

    def _process_log_queue(self):
        if not self.is_running:
            return

        lines = []
        try:
            for _ in range(500):
                lines.append(self.log_queue.get_nowait())
        except queue.Empty:
            pass

        if lines:
            self.text_widget.configure(state=tk.NORMAL)
            for line in lines:
                tag = self._get_log_level(line)
                self.text_widget.insert(tk.END, line, tag)
            
            if int(self.text_widget.index('end-1c').split('.')[0]) > 20000:
                self.text_widget.delete("1.0", "5000.0")

            if self.autoscroll_var.get():
                self.text_widget.see(tk.END)
            
            self.text_widget.configure(state=tk.DISABLED)

        self.window.after(50, self._process_log_queue)

    def _get_log_level(self, line):
        m = re.search(r'\s+([VDIWEF])\s+', line)
        return m.group(1) if m else "V"

    def restart_logcat(self):
        self.stop_logcat()
        self.start_logcat()

    def toggle_logcat(self):
        if self.is_running:
            self.stop_logcat()
            self.btn_toggle.config(text="Start")
        else:
            self.start_logcat()
            self.btn_toggle.config(text="Stop")

    def stop_logcat(self):
        self.is_running = False
        if self.log_process:
            self.log_process.terminate()
            self.log_process = None

    def clear_logs(self):
        self.text_widget.configure(state=tk.NORMAL)
        self.text_widget.delete("1.0", tk.END)
        self.text_widget.configure(state=tk.DISABLED)
        subprocess.run([self.adb_bin, "-s", self.device_id, "logcat", "-c"])

    def copy_logs(self):
        self.parent.clipboard_clear()
        self.parent.clipboard_append(self.text_widget.get("1.0", tk.END))
        messagebox.showinfo("Copied", "Logs copied to clipboard.")

    def on_close(self):
        self.stop_logcat()
        self.window.destroy()


class ADBFileManagerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("ADB Commander")
        self.root.geometry("1360x800")
        self.root.minsize(1060, 650)

        self.icons = VectorIconFactory()

        self.mac_path = os.path.expanduser("~/Downloads")
        if not os.path.isdir(self.mac_path):
            self.mac_path = os.path.expanduser("~")

        self.adb_path = "/sdcard"
        self.selected_device = tk.StringVar()
        self.show_hidden = tk.BooleanVar(value=False)

        self.mac_search_var = tk.StringVar()
        self.adb_search_var = tk.StringVar()

        self.mac_items_cache = []
        self.adb_items_cache = []

        self.drag_source = None
        self.drag_items = []
        self.drag_ghost = None
        self.drag_ghost_label = None
        self.drag_start_xy = (0, 0)
        self.is_dragging = False
        self.hovered_folder = None

        self.thumb_temp_dir = tempfile.mkdtemp(prefix="adb_glass_thumbs_")
        self.current_preview_img = None
        self.preview_request_id = 0

        self._apply_macos_glass_theme()
        self._build_ui()
        self._bind_shortcuts()

        self.load_mac_directory(self.mac_path)
        self.refresh_devices()

        # Start background device connection monitor
        self._monitor_running = True
        threading.Thread(target=self._device_monitor_loop, daemon=True).start()

    def _handle_adb_bookmark(self, event):
        sel = self.adb_bm_var.get()
        if sel == "+ Add Current Folder...":
            name = simpledialog.askstring("Add Bookmark", "Bookmark Name:", initialvalue=os.path.basename(self.adb_path))
            if name:
                self.adb_bookmarks[name] = self.adb_path
                self.adb_bm_cb["values"] = list(self.adb_bookmarks.keys()) + ["+ Add Current Folder..."]
            self.adb_bm_var.set("Bookmarks...")
        elif sel in self.adb_bookmarks:
            self.load_adb_directory(self.adb_bookmarks[sel])
            self.adb_bm_var.set("Bookmarks...")
            
    def _apply_macos_glass_theme(self):
        self.root.configure(bg=GLASS_BG)
        try:
            self.root.attributes("-alpha", 0.97)
        except tk.TclError:
            pass

        style = ttk.Style()
        style.theme_use("clam")
        style.configure(".", background=GLASS_BG, foreground=TEXT_PRIMARY, font=("SF Pro Text", 12))
        style.configure("Glass.TFrame", background=GLASS_BG)
        style.configure("Panel.TFrame", background=GLASS_PANEL)
        style.configure("Card.TFrame", background=GLASS_ELEVATED)

        style.configure("Glass.TLabel", background=GLASS_BG, foreground=TEXT_PRIMARY, font=("SF Pro Text", 12))
        style.configure("Panel.TLabel", background=GLASS_PANEL, foreground=TEXT_PRIMARY, font=("SF Pro Text", 12))
        style.configure("PanelTitle.TLabel", background=GLASS_PANEL, foreground=TEXT_PRIMARY, font=("SF Pro Display", 13, "bold"))
        style.configure("Subtle.TLabel", background=GLASS_PANEL, foreground=TEXT_SECONDARY, font=("SF Pro Text", 11))
        style.configure("Status.TLabel", background=GLASS_ELEVATED, foreground=TEXT_SECONDARY, font=("SF Pro Text", 11))

        style.configure("Glass.TButton", background=GLASS_ELEVATED, foreground=TEXT_PRIMARY, bordercolor=GLASS_BORDER, lightcolor=GLASS_BORDER, darkcolor=GLASS_BORDER, focusthickness=0, padding=(8, 5), font=("SF Pro Text", 11, "bold"))
        style.map("Glass.TButton", background=[("active", GLASS_HOVER), ("pressed", ACCENT_BLUE)], foreground=[("pressed", "#FFFFFF")])

        style.configure("Accent.TButton", background=ACCENT_BLUE, foreground="#FFFFFF", bordercolor=ACCENT_BLUE, focusthickness=0, padding=(10, 5), font=("SF Pro Text", 11, "bold"))
        style.map("Accent.TButton", background=[("active", "#2192FF"), ("pressed", "#0066CC")])

        style.configure("Glass.TEntry", fieldbackground=GLASS_ELEVATED, foreground=TEXT_PRIMARY, insertcolor=TEXT_PRIMARY, bordercolor=GLASS_BORDER, lightcolor=GLASS_BORDER, darkcolor=GLASS_BORDER, padding=(6, 4))
        style.configure("Glass.TCombobox", fieldbackground=GLASS_ELEVATED, background=GLASS_ELEVATED, foreground=TEXT_PRIMARY, arrowcolor=TEXT_PRIMARY, bordercolor=GLASS_BORDER, padding=(6, 4))
        style.map("Glass.TCombobox", fieldbackground=[("readonly", GLASS_ELEVATED)], selectbackground=[("readonly", GLASS_ELEVATED)], selectforeground=[("readonly", TEXT_PRIMARY)])

        style.configure("Glass.TCheckbutton", background=GLASS_BG, foreground=TEXT_SECONDARY, font=("SF Pro Text", 11))
        style.map("Glass.TCheckbutton", background=[("active", GLASS_BG)], foreground=[("active", TEXT_PRIMARY)])

        style.configure("Glass.Treeview", background=GLASS_PANEL, fieldbackground=GLASS_PANEL, foreground=TEXT_PRIMARY, rowheight=30, borderwidth=0, font=("SF Pro Text", 12))
        style.configure("Glass.Treeview.Heading", background=GLASS_ELEVATED, foreground=TEXT_SECONDARY, relief="flat", padding=(8, 6), font=("SF Pro Text", 11, "bold"))
        style.map("Glass.Treeview", background=[("selected", ACCENT_BLUE)], foreground=[("selected", "#FFFFFF")])

        style.configure("Glass.Horizontal.TProgressbar", troughcolor=GLASS_BG, background=ACCENT_BLUE, bordercolor=GLASS_BORDER, thickness=6)

    def _build_ui(self):
        # Native macOS Menu Bar
        self.menubar = tk.Menu(self.root)
        
        # Apple Menu (shows as Application Menu on macOS)
        app_menu = tk.Menu(self.menubar, name='apple')
        self.menubar.add_cascade(menu=app_menu)
        app_menu.add_command(label='About ADB Commander', command=self.show_device_info)
        app_menu.add_separator()
        
        # File Menu
        file_menu = tk.Menu(self.menubar, tearoff=0)
        file_menu.add_command(label="Refresh Devices", command=self.refresh_devices)
        file_menu.add_command(label="Screen Record", command=self.toggle_screen_record)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        self.menubar.add_cascade(label="File", menu=file_menu)
        
        # View Menu
        view_menu = tk.Menu(self.menubar, tearoff=0)
        view_menu.add_command(label="Scrcpy Mirror", command=self.launch_scrcpy)
        view_menu.add_command(label="Logcat & Profiler", command=self.open_logcat_window)
        view_menu.add_separator()
        view_menu.add_command(label="Toggle Hidden Files", command=lambda: (self.show_hidden.set(not self.show_hidden.get()), self._reload_both()))
        self.menubar.add_cascade(label="View", menu=view_menu)
        
        # Tools Menu
        tools_menu = tk.Menu(self.menubar, tearoff=0)
        tools_menu.add_command(label="Inject Clipboard to Device", command=self.inject_clipboard_to_device)
        tools_menu.add_command(label="Uninstall Package...", command=self.uninstall_selected_package)
        self.menubar.add_cascade(label="Tools", menu=tools_menu)
        
        self.root.config(menu=self.menubar)

        # Header
        header = ttk.Frame(self.root, style="Glass.TFrame", padding=(14, 10, 14, 8))
        header.pack(fill=tk.X)

        ttk.Label(header, text=" ADB Commander", image=self.icons.get("device", 18, ACCENT_BLUE), compound=tk.LEFT, font=("SF Pro Display", 15, "bold"), style="Glass.TLabel").pack(side=tk.LEFT, padx=(0, 16))

        self.device_combo = ttk.Combobox(header, textvariable=self.selected_device, state="readonly", width=26, style="Glass.TCombobox")
        self.device_combo.pack(side=tk.LEFT, padx=(0, 6))
        self.device_combo.bind("<<ComboboxSelected>>", lambda e: self.load_adb_directory(self.adb_path))

        ttk.Button(header, text=" Refresh", image=self.icons.get("refresh", 14, TEXT_PRIMARY), compound=tk.LEFT, style="Glass.TButton", command=self.refresh_devices).pack(side=tk.LEFT, padx=3)
        ttk.Button(header, text=" Screenshot", image=self.icons.get("camera", 14, ACCENT_GREEN), compound=tk.LEFT, style="Glass.TButton", command=self.capture_device_screenshot).pack(side=tk.LEFT, padx=3)
        ttk.Button(header, text=" Scrcpy", image=self.icons.get("video", 14, ACCENT_BLUE), compound=tk.LEFT, style="Glass.TButton", command=self.launch_scrcpy).pack(side=tk.LEFT, padx=3)
        ttk.Button(header, text=" Logcat", image=self.icons.get("terminal", 14, ACCENT_AMBER), compound=tk.LEFT, style="Glass.TButton", command=self.open_logcat_window).pack(side=tk.LEFT, padx=3)
        ttk.Button(header, text=" Paste Text", image=self.icons.get("doc", 14, TEXT_PRIMARY), compound=tk.LEFT, style="Glass.TButton", command=self.inject_clipboard_to_device).pack(side=tk.LEFT, padx=3)
        ttk.Button(header, text=" Device Info", image=self.icons.get("info", 14, TEXT_PRIMARY), compound=tk.LEFT, style="Glass.TButton", command=self.show_device_info).pack(side=tk.LEFT, padx=3)

        ttk.Checkbutton(header, text="Show Hidden", variable=self.show_hidden, style="Glass.TCheckbutton", command=self._reload_both).pack(side=tk.RIGHT, padx=6)

        # Workspace
        workspace = ttk.Frame(self.root, style="Glass.TFrame", padding=(12, 2, 12, 10))
        workspace.pack(fill=tk.BOTH, expand=True)

        self.paned = ttk.PanedWindow(workspace, orient=tk.HORIZONTAL)
        self.paned.pack(fill=tk.BOTH, expand=True) # Fill the entire workspace

        self.mac_pane = self._build_mac_pane(self.paned)
        self.adb_pane = self._build_adb_pane(self.paned)
        
        # Pass self.paned as the parent instead of workspace
        self.inspector_pane = self._build_inspector_pane(self.paned)

        self.paned.add(self.mac_pane, weight=1)
        self.paned.add(self.adb_pane, weight=1)
        # weight=0 means it won't auto-expand when you resize the whole app window, 
        # but you can still manually drag the sash to resize it.
        self.paned.add(self.inspector_pane, weight=0)

        # Footer
        footer = ttk.Frame(self.root, style="Card.TFrame", padding=(12, 5))
        footer.pack(fill=tk.X, side=tk.BOTTOM)

        self.status_var = tk.StringVar(value=f"Ready  |  ADB: {ADB_BIN}")
        ttk.Label(footer, textvariable=self.status_var, style="Status.TLabel").pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.progress = ttk.Progressbar(footer, mode="indeterminate", length=180, style="Glass.Horizontal.TProgressbar")
        self.progress.pack(side=tk.RIGHT, padx=(10, 0))

        # Bind the clean exit protocol to the window's close button
        self.root.protocol("WM_DELETE_WINDOW", self._on_app_close)

    def _handle_mac_bookmark(self, event):
        sel = self.mac_bm_var.get()
        if sel == "+ Add Current Folder...":
            name = simpledialog.askstring("Add Bookmark", "Bookmark Name:", initialvalue=os.path.basename(self.mac_path))
            if name:
                self.mac_bookmarks[name] = self.mac_path
                self.mac_bm_cb["values"] = list(self.mac_bookmarks.keys()) + ["+ Add Current Folder..."]
            self.mac_bm_var.set("Bookmarks...")
        elif sel in self.mac_bookmarks:
            self.load_mac_directory(self.mac_bookmarks[sel])
            self.mac_bm_var.set("Bookmarks...")
            
    def _build_mac_pane(self, parent):
        outer = tk.Frame(parent, bg=GLASS_PANEL, highlightbackground=GLASS_BORDER, highlightthickness=1)
        frame = ttk.Frame(outer, style="Panel.TFrame", padding=10)
        frame.pack(fill=tk.BOTH, expand=True)

        title_bar = ttk.Frame(frame, style="Panel.TFrame")
        title_bar.pack(fill=tk.X, pady=(0, 8))
        ttk.Label(title_bar, text=" Mac Local Storage", image=self.icons.get("mac", 16, ACCENT_BLUE), compound=tk.LEFT, style="PanelTitle.TLabel").pack(side=tk.LEFT)

        bm_wrap = ttk.Frame(title_bar, style="Panel.TFrame")
        bm_wrap.pack(side=tk.RIGHT)
        
        self.mac_bookmarks = {
            "Home": os.path.expanduser("~"),
            "Desktop": os.path.expanduser("~/Desktop"),
            "Downloads": os.path.expanduser("~/Downloads"),
            "Documents": os.path.expanduser("~/Documents")
        }
        self.mac_bm_var = tk.StringVar(value="Bookmarks...")
        self.mac_bm_cb = ttk.Combobox(bm_wrap, textvariable=self.mac_bm_var, values=list(self.mac_bookmarks.keys()) + ["+ Add Current Folder..."], state="readonly", width=16)
        self.mac_bm_cb.pack(side=tk.LEFT, padx=(3, 0))
        self.mac_bm_cb.bind("<<ComboboxSelected>>", self._handle_mac_bookmark)

        nav = ttk.Frame(frame, style="Panel.TFrame")
        nav.pack(fill=tk.X, pady=(0, 6))
        ttk.Button(nav, image=self.icons.get("up", 14, TEXT_PRIMARY), style="Glass.TButton", command=self.mac_go_up).pack(side=tk.LEFT)
        
        # Use standard Entry for reliable styling
        self.mac_path_entry = tk.Entry(nav, bg="#FFFFFF", fg=TEXT_DARK, insertbackground=TEXT_DARK, font=("SF Pro Text", 12))
        self.mac_path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.mac_path_entry.bind("<Return>", lambda e: self.load_mac_directory(self.mac_path_entry.get().strip()))
        
        ttk.Button(nav, image=self.icons.get("refresh", 14, TEXT_PRIMARY), style="Glass.TButton", command=lambda: self.load_mac_directory(self.mac_path)).pack(side=tk.LEFT)

        search_bar = ttk.Frame(frame, style="Panel.TFrame")
        search_bar.pack(fill=tk.X, pady=(0, 6))
        ttk.Label(search_bar, image=self.icons.get("search", 14, TEXT_SECONDARY), style="Panel.TLabel").pack(side=tk.LEFT, padx=(2, 6))
        
        # Use standard Entry for search too
        self.mac_search_entry = tk.Entry(search_bar, textvariable=self.mac_search_var, bg="#FFFFFF", fg=TEXT_DARK, insertbackground=TEXT_DARK, font=("SF Pro Text", 12))
        self.mac_search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.mac_search_var.trace_add("write", lambda *_: self._render_mac_tree())

        tree_box = ttk.Frame(frame, style="Panel.TFrame")
        tree_box.pack(fill=tk.BOTH, expand=True)
        self.mac_tree = ttk.Treeview(tree_box, columns=("size", "modified"), show="tree headings", selectmode="extended", style="Glass.Treeview")
        self.mac_tree.heading("#0", text="Name", anchor=tk.W)
        self.mac_tree.heading("size", text="Size", anchor=tk.E)
        self.mac_tree.heading("modified", text="Modified", anchor=tk.W)
        self.mac_tree.column("#0", width=270, anchor=tk.W)
        self.mac_tree.column("size", width=80, anchor=tk.E, stretch=False)
        self.mac_tree.column("modified", width=115, anchor=tk.W, stretch=False)
        self.mac_tree.tag_configure("drop_hover", background=ACCENT_BLUE, foreground="#FFFFFF")
        sb = ttk.Scrollbar(tree_box, orient=tk.VERTICAL, command=self.mac_tree.yview)
        self.mac_tree.configure(yscroll=sb.set)
        self.mac_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.RIGHT, fill=tk.Y)

        self.mac_tree.bind("<Double-1>", self.on_mac_double_click)
        self.mac_tree.bind("<<TreeviewSelect>>", lambda e: self._on_item_selected("mac"))
        self.mac_tree.bind("<Button-2>", lambda e: self._show_context_menu(e, "mac"))
        self.mac_tree.bind("<Button-3>", lambda e: self._show_context_menu(e, "mac"))
        self.mac_tree.bind("<ButtonPress-1>", lambda e: self._on_drag_start(e, "mac"), add="+")
        self.mac_tree.bind("<B1-Motion>", self._on_drag_motion, add="+")
        self.mac_tree.bind("<ButtonRelease-1>", self._on_drag_release, add="+")

        if HAS_DND2:
            self.mac_tree.drop_target_register(DND_FILES)
            self.mac_tree.dnd_bind("<<Drop>>", lambda e: self._on_finder_drop(e, "mac"))
            self.mac_tree.dnd_bind("<<DropPosition>>", lambda e: self._on_finder_hover(e, "mac"))
            self.mac_tree.dnd_bind("<<DropLeave>>", lambda e: self._clear_hover_highlight())
            self.mac_tree.drag_source_register(1, DND_FILES)
            self.mac_tree.dnd_bind("<<DragInitCmd>>", self._on_mac_drag_out_to_finder)

        actions = ttk.Frame(frame, style="Panel.TFrame")
        actions.pack(fill=tk.X, pady=(8, 0))
        self.btn_push = ttk.Button(actions, text=" Send to Phone", image=self.icons.get("right", 14, "#FFFFFF"), compound=tk.LEFT, style="Accent.TButton", command=self.push_selected_from_mac)
        self.btn_push.pack(side=tk.LEFT, padx=(0, 4))
        ttk.Button(actions, text=" New Folder", image=self.icons.get("new_folder", 14, TEXT_PRIMARY), compound=tk.LEFT, style="Glass.TButton", command=self.mac_create_folder).pack(side=tk.LEFT, padx=3)
        ttk.Button(actions, text=" Finder", image=self.icons.get("finder", 14, TEXT_PRIMARY), compound=tk.LEFT, style="Glass.TButton", command=self.open_in_finder).pack(side=tk.LEFT, padx=3)
        ttk.Button(actions, text=" Delete", image=self.icons.get("trash", 14, ACCENT_RED), compound=tk.LEFT, style="Glass.TButton", command=self.mac_delete_selected).pack(side=tk.RIGHT)

        self.mac_count_var = tk.StringVar(value="0 items")
        ttk.Label(frame, textvariable=self.mac_count_var, style="Subtle.TLabel").pack(anchor=tk.W, pady=(5, 0))
        return outer

    def _build_adb_pane(self, parent):
        outer = tk.Frame(parent, bg=GLASS_PANEL, highlightbackground=GLASS_BORDER, highlightthickness=1)
        frame = ttk.Frame(outer, style="Panel.TFrame", padding=10)
        frame.pack(fill=tk.BOTH, expand=True)

        title_bar = ttk.Frame(frame, style="Panel.TFrame")
        title_bar.pack(fill=tk.X, pady=(0, 8))
        ttk.Label(title_bar, text=" Android ADB Storage", image=self.icons.get("device", 16, ACCENT_GREEN), compound=tk.LEFT, style="PanelTitle.TLabel").pack(side=tk.LEFT)

        bm_wrap = ttk.Frame(title_bar, style="Panel.TFrame")
        bm_wrap.pack(side=tk.RIGHT)
        
        self.adb_bookmarks = {
            "/sdcard": "/sdcard",
            "Download": "/sdcard/Download",
            "DCIM": "/sdcard/DCIM",
            "Android/data": "/sdcard/Android/data"
        }
        self.adb_bm_var = tk.StringVar(value="Bookmarks...")
        self.adb_bm_cb = ttk.Combobox(bm_wrap, textvariable=self.adb_bm_var, values=list(self.adb_bookmarks.keys()) + ["+ Add Current Folder..."], state="readonly", width=16)
        self.adb_bm_cb.pack(side=tk.LEFT, padx=(3, 0))
        self.adb_bm_cb.bind("<<ComboboxSelected>>", self._handle_adb_bookmark)

        nav = ttk.Frame(frame, style="Panel.TFrame")
        nav.pack(fill=tk.X, pady=(0, 6))
        ttk.Button(nav, image=self.icons.get("up", 14, TEXT_PRIMARY), style="Glass.TButton", command=self.adb_go_up).pack(side=tk.LEFT)
        
        # Use standard tk.Entry
        self.adb_path_entry = tk.Entry(nav, bg="#FFFFFF", fg=TEXT_DARK, insertbackground=TEXT_DARK, font=("SF Pro Text", 12))
        self.adb_path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.adb_path_entry.bind("<Return>", lambda e: self.load_adb_directory(self.adb_path_entry.get().strip()))
        
        ttk.Button(nav, image=self.icons.get("refresh", 14, TEXT_PRIMARY), style="Glass.TButton", command=lambda: self.load_adb_directory(self.adb_path)).pack(side=tk.LEFT)

        search_bar = ttk.Frame(frame, style="Panel.TFrame")
        search_bar.pack(fill=tk.X, pady=(0, 6))
        ttk.Label(search_bar, image=self.icons.get("search", 14, TEXT_SECONDARY), style="Panel.TLabel").pack(side=tk.LEFT, padx=(2, 6))
        
        self.adb_search_entry = tk.Entry(search_bar, textvariable=self.adb_search_var, bg="#FFFFFF", fg=TEXT_DARK, insertbackground=TEXT_DARK, font=("SF Pro Text", 12))
        self.adb_search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.adb_search_var.trace_add("write", lambda *_: self._render_adb_tree())

        tree_box = ttk.Frame(frame, style="Panel.TFrame")
        tree_box.pack(fill=tk.BOTH, expand=True)
        self.adb_tree = ttk.Treeview(tree_box, columns=("size", "modified"), show="tree headings", selectmode="extended", style="Glass.Treeview")
        self.adb_tree.heading("#0", text="Name", anchor=tk.W)
        self.adb_tree.heading("size", text="Size", anchor=tk.E)
        self.adb_tree.heading("modified", text="Modified", anchor=tk.W)
        self.adb_tree.column("#0", width=270, anchor=tk.W)
        self.adb_tree.column("size", width=80, anchor=tk.E, stretch=False)
        self.adb_tree.column("modified", width=115, anchor=tk.W, stretch=False)
        self.adb_tree.tag_configure("drop_hover", background=ACCENT_BLUE, foreground="#FFFFFF")
        sb = ttk.Scrollbar(tree_box, orient=tk.VERTICAL, command=self.adb_tree.yview)
        self.adb_tree.configure(yscroll=sb.set)
        self.adb_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.RIGHT, fill=tk.Y)

        self.adb_tree.bind("<Double-1>", self.on_adb_double_click)
        self.adb_tree.bind("<<TreeviewSelect>>", lambda e: self._on_item_selected("adb"))
        self.adb_tree.bind("<Button-2>", lambda e: self._show_context_menu(e, "adb"))
        self.adb_tree.bind("<Button-3>", lambda e: self._show_context_menu(e, "adb"))
        self.adb_tree.bind("<ButtonPress-1>", lambda e: self._on_drag_start(e, "adb"), add="+")
        self.adb_tree.bind("<B1-Motion>", self._on_drag_motion, add="+")
        self.adb_tree.bind("<ButtonRelease-1>", self._on_drag_release, add="+")

        if HAS_DND2:
            self.adb_tree.drop_target_register(DND_FILES)
            self.adb_tree.dnd_bind("<<Drop>>", lambda e: self._on_finder_drop(e, "adb"))
            self.adb_tree.dnd_bind("<<DropPosition>>", lambda e: self._on_finder_hover(e, "adb"))
            self.adb_tree.dnd_bind("<<DropLeave>>", lambda e: self._clear_hover_highlight())
            self.adb_tree.drag_source_register(1, DND_FILES)
            self.adb_tree.dnd_bind("<<DragInitCmd>>", self._on_adb_drag_out_to_finder)

        actions = ttk.Frame(frame, style="Panel.TFrame")
        actions.pack(fill=tk.X, pady=(8, 0))
        self.btn_pull = ttk.Button(actions, text=" Pull to Mac", image=self.icons.get("left", 14, "#FFFFFF"), compound=tk.LEFT, style="Accent.TButton", command=self.pull_selected_from_adb)
        self.btn_pull.pack(side=tk.LEFT, padx=(0, 4))
        self.btn_adb_mkdir = ttk.Button(actions, text=" New Folder", image=self.icons.get("new_folder", 14, TEXT_PRIMARY), compound=tk.LEFT, style="Glass.TButton", command=self.adb_create_folder)
        self.btn_adb_mkdir.pack(side=tk.LEFT, padx=3)
        self.btn_adb_install = ttk.Button(actions, text=" Install APK", image=self.icons.get("apk", 14, ACCENT_GREEN), compound=tk.LEFT, style="Glass.TButton", command=self.install_selected_apk)
        self.btn_adb_install.pack(side=tk.LEFT, padx=3)
        self.btn_adb_del = ttk.Button(actions, text=" Delete", image=self.icons.get("trash", 14, ACCENT_RED), compound=tk.LEFT, style="Glass.TButton", command=self.adb_delete_selected)
        self.btn_adb_del.pack(side=tk.RIGHT)

        bottom_meta = ttk.Frame(frame, style="Panel.TFrame")
        bottom_meta.pack(fill=tk.X, pady=(5, 0))
        self.adb_count_var = tk.StringVar(value="0 items")
        ttk.Label(bottom_meta, textvariable=self.adb_count_var, style="Subtle.TLabel").pack(side=tk.LEFT)
        self.adb_storage_var = tk.StringVar(value="")
        ttk.Label(bottom_meta, textvariable=self.adb_storage_var, style="Subtle.TLabel").pack(side=tk.RIGHT)
        return outer

    def _build_inspector_pane(self, parent):
        # Removed width=240 and outer.pack_propagate(False) so it can flex
        outer = tk.Frame(parent, bg=GLASS_PANEL, highlightbackground=GLASS_BORDER, highlightthickness=1)
        
        frame = ttk.Frame(outer, style="Panel.TFrame", padding=12)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="Inspector & Preview", style="PanelTitle.TLabel").pack(anchor=tk.W, pady=(0, 8))
        self.preview_canvas = tk.Canvas(frame, width=204, height=204, bg=GLASS_ELEVATED, highlightthickness=1, highlightbackground=GLASS_BORDER)
        self.preview_canvas.pack(pady=(0, 10))
        self.preview_canvas.create_text(102, 102, text="Select any file\nto inspect", fill=TEXT_SECONDARY, justify=tk.CENTER, font=("SF Pro Text", 11))

        self.info_name_var = tk.StringVar(value="No Selection")
        self.info_type_var = tk.StringVar(value="Type: —")
        self.info_size_var = tk.StringVar(value="Size: —")
        self.info_mod_var = tk.StringVar(value="Modified: —")

        ttk.Label(frame, textvariable=self.info_name_var, font=("SF Pro Text", 12, "bold"), style="Panel.TLabel", wraplength=210).pack(anchor=tk.W, pady=(0, 6))
        ttk.Label(frame, textvariable=self.info_type_var, style="Subtle.TLabel").pack(anchor=tk.W, pady=2)
        ttk.Label(frame, textvariable=self.info_size_var, style="Subtle.TLabel").pack(anchor=tk.W, pady=2)
        ttk.Label(frame, textvariable=self.info_mod_var, style="Subtle.TLabel").pack(anchor=tk.W, pady=2)

        sep = tk.Frame(frame, bg=GLASS_BORDER, height=1)
        sep.pack(fill=tk.X, pady=12)

        guide = "Drag & Drop Guide:\n• Drag between panes to copy.\n• Hover over any folder to drop directly inside it.\n• Drag within a pane onto a folder to move.\n" + ("• Finder drag & drop active." if HAS_DND2 else "• Run 'pip install tkinterdnd2' for Finder DnD.")
        ttk.Label(frame, text=guide, style="Subtle.TLabel", wraplength=210, justify=tk.LEFT).pack(anchor=tk.W)
        return outer

    def _bind_shortcuts(self):
        self.root.bind("<Command-r>", lambda e: self._reload_both())
        self.root.bind("<F5>", lambda e: self._reload_both())
        self.mac_tree.bind("<BackSpace>", lambda e: self.mac_go_up())
        self.adb_tree.bind("<BackSpace>", lambda e: self.adb_go_up())
        self.mac_tree.bind("<Command-a>", lambda e: self._select_all(self.mac_tree))
        self.adb_tree.bind("<Command-a>", lambda e: self._select_all(self.adb_tree))

    def _select_all(self, tree):
        tree.selection_set(tree.get_children())
        return "break"

    def _reload_both(self):
        self.load_mac_directory(self.mac_path)
        self.load_adb_directory(self.adb_path)

    def _set_busy(self, busy, status_text=None):
        state = tk.DISABLED if busy else tk.NORMAL
        for btn in (self.btn_push, self.btn_pull, self.btn_adb_mkdir, self.btn_adb_del, self.btn_adb_install):
            btn.config(state=state)
        if busy:
            self.progress.start(12)
        else:
            self.progress.stop()
        if status_text:
            self.status_var.set(status_text)

    def mac_go_up(self):
        parent = os.path.dirname(self.mac_path.rstrip("/"))
        if parent and parent != self.mac_path:
            self.load_mac_directory(parent)

    def load_mac_directory(self, path):
        path = os.path.expanduser(path)
        if not os.path.isdir(path):
            self.status_var.set(f"Directory not found: {path}")
            return
        self.mac_path = os.path.abspath(path)
        self.mac_path_entry.delete(0, tk.END)
        self.mac_path_entry.insert(0, self.mac_path)

        items = []
        try:
            with os.scandir(self.mac_path) as it:
                for entry in it:
                    if not self.show_hidden.get() and entry.name.startswith("."):
                        continue
                    try:
                        st = entry.stat()
                        is_dir = entry.is_dir()
                        items.append({
                            "name": entry.name,
                            "is_dir": is_dir,
                            "size": None if is_dir else st.st_size,
                            "size_str": "—" if is_dir else format_size(st.st_size),
                            "mtime": datetime.fromtimestamp(st.st_mtime).strftime("%Y-%m-%d %H:%M"),
                        })
                    except OSError:
                        continue
        except PermissionError:
            messagebox.showerror("Permission Denied", f"Cannot access:\n{self.mac_path}")
            return

        items.sort(key=lambda x: (not x["is_dir"], x["name"].lower()))
        self.mac_items_cache = items
        self._render_mac_tree()

    def _render_mac_tree(self):
        q = self.mac_search_var.get().strip().lower()
        for row in self.mac_tree.get_children():
            self.mac_tree.delete(row)
        shown = 0
        for item in self.mac_items_cache:
            if q and q not in item["name"].lower():
                continue
            icon_key = classify_file_icon(item["name"], item["is_dir"])
            self.mac_tree.insert("", tk.END, iid=item["name"], text=f"  {item['name']}", image=self.icons.get(icon_key, 16), values=(item["size_str"], item["mtime"]))
            shown += 1
        self.mac_count_var.set(f"{shown} item(s)  •  {os.path.basename(self.mac_path) or '/'}")

    def on_mac_double_click(self, event):
        sel = self.mac_tree.selection()
        if not sel:
            return
        target = os.path.join(self.mac_path, sel[0])
        if os.path.isdir(target):
            self.load_mac_directory(target)
        else:
            subprocess.run(["open", target])

    def open_in_finder(self):
        subprocess.run(["open", self.mac_path])

    def mac_create_folder(self):
        name = simpledialog.askstring("New Mac Folder", "Enter folder name:")
        if not name or not name.strip():
            return
        try:
            os.makedirs(os.path.join(self.mac_path, name.strip()), exist_ok=True)
            self.load_mac_directory(self.mac_path)
        except OSError as e:
            messagebox.showerror("Error", str(e))

    def mac_delete_selected(self):
        sel = self.mac_tree.selection()
        if not sel:
            return
        if not messagebox.askyesno("Confirm Delete", f"Delete {len(sel)} selected item(s) from your Mac?"):
            return
        for name in sel:
            target = os.path.join(self.mac_path, name)
            try:
                if os.path.isdir(target):
                    shutil.rmtree(target)
                else:
                    os.remove(target)
            except OSError as e:
                messagebox.showerror("Delete Error", f"{name}: {e}")
        self.load_mac_directory(self.mac_path)

    def run_adb(self, args, timeout_sec=30):
        cmd = [ADB_BIN]
        if self.selected_device.get():
            cmd.extend(["-s", self.selected_device.get()])
        cmd.extend(args)
        
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout_sec)
            
            # Edge Case: Device disconnected mid-command or ADB daemon hung
            if "device offline" in res.stderr.lower() or "not found" in res.stderr.lower():
                self.root.after(0, lambda: self.status_var.set("Error: Device offline or disconnected."))
                
            return res.returncode, res.stdout, res.stderr
            
        except subprocess.TimeoutExpired:
            self.root.after(0, lambda: self.status_var.set("Error: ADB command timed out."))
            return -1, "", "ADB command timed out."
        except Exception as e:
            return -1, "", str(e)

    def refresh_devices(self):
        try:
            res = subprocess.run([ADB_BIN, "devices"], capture_output=True, text=True)
        except FileNotFoundError:
            self.status_var.set("ADB not found. Install via: brew install android-platform-tools")
            return

        devices = []
        for line in res.stdout.splitlines()[1:]:
            parts = line.strip().split()
            if len(parts) >= 2 and parts[1] == "device":
                devices.append(parts[0])

        self.device_combo["values"] = devices
        if devices:
            if self.selected_device.get() not in devices:
                self.selected_device.set(devices[0])
            self.load_adb_directory(self.adb_path)
        else:
            self.selected_device.set("")
            self.status_var.set("No authorized ADB devices found.")

    def adb_go_up(self):
        if self.adb_path in ("/", ""):
            return
        parent = os.path.dirname(self.adb_path.rstrip("/"))
        self.load_adb_directory(parent if parent else "/")

    def load_adb_directory(self, path):
        if not self.selected_device.get():
            return
        if not path.startswith("/"):
            path = "/" + path
        self.adb_path = path
        self.adb_path_entry.delete(0, tk.END)
        self.adb_path_entry.insert(0, path)

        flag = "-la" if self.show_hidden.get() else "-l"
        code, out, err = self.run_adb(["shell", f'ls {flag} "{path}"'])
        if code != 0:
            self.status_var.set(f"Error accessing {path}: {err.strip() or out.strip()}")
            return

        items = []
        pattern = re.compile(r"^([d\-lcbps])[rwxstST\-]{9}\+?\s+\d+\s+\S+\s+\S+\s+(\d+)\s+(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2})\s+(.+)$")

        for raw_line in out.splitlines():
            line = raw_line.strip("\r\n")
            if not line or line.startswith("total "):
                continue
            m = pattern.match(line)
            if m:
                ftype, size_str, mtime, name = m.groups()
                if ftype == "l" and " -> " in name:
                    name = name.split(" -> ")[0]
                if name in (".", ".."):
                    continue
                is_dir = ftype == "d"
                size_bytes = int(size_str)
                items.append({
                    "name": name,
                    "is_dir": is_dir,
                    "size": None if is_dir else size_bytes,
                    "size_str": "—" if is_dir else format_size(size_bytes),
                    "mtime": mtime,
                })

        items.sort(key=lambda x: (not x["is_dir"], x["name"].lower()))
        self.adb_items_cache = items
        self._render_adb_tree()
        self._update_adb_storage_stat()
        self.status_var.set(f"Connected ({self.selected_device.get()})  •  {path}")

    def _update_adb_storage_stat(self):
        _, out, _ = self.run_adb(["shell", "df -h /sdcard | tail -n 1"])
        parts = out.strip().split()
        if len(parts) >= 5:
            self.adb_storage_var.set(f"Storage: {parts[2]} used / {parts[1]} ({parts[4]})")

    def _render_adb_tree(self):
        q = self.adb_search_var.get().strip().lower()
        for row in self.adb_tree.get_children():
            self.adb_tree.delete(row)
        shown = 0
        for item in self.adb_items_cache:
            if q and q not in item["name"].lower():
                continue
            icon_key = classify_file_icon(item["name"], item["is_dir"])
            self.adb_tree.insert("", tk.END, iid=item["name"], text=f"  {item['name']}", image=self.icons.get(icon_key, 16), values=(item["size_str"], item["mtime"]))
            shown += 1
        self.adb_count_var.set(f"{shown} item(s)  •  {self.adb_path}")

    def on_adb_double_click(self, event):
        sel = self.adb_tree.selection()
        if not sel:
            return
        name = sel[0]
        match = next((x for x in self.adb_items_cache if x["name"] == name), None)
        if match and match["is_dir"]:
            self.load_adb_directory(f"{self.adb_path.rstrip('/')}/{name}")

    def adb_create_folder(self):
        if not self.selected_device.get():
            return
        name = simpledialog.askstring("New Android Folder", "Enter folder name:")
        if not name or not name.strip():
            return
        target = f"{self.adb_path.rstrip('/')}/{name.strip()}"
        code, out, err = self.run_adb(["shell", f'mkdir -p "{target}"'])
        if code != 0:
            messagebox.showerror("Error", err.strip() or out.strip())
        else:
            self.load_adb_directory(self.adb_path)

    def adb_delete_selected(self):
        sel = self.adb_tree.selection()
        if not sel:
            return
        if not messagebox.askyesno("Confirm Delete", f"Permanently delete {len(sel)} item(s) from your phone?"):
            return
        errors = []
        for name in sel:
            target = f"{self.adb_path.rstrip('/')}/{name}"
            code, out, err = self.run_adb(["shell", f'rm -rf "{target}"'])
            if code != 0:
                errors.append(f"{name}: {err.strip() or out.strip()}")
        self.load_adb_directory(self.adb_path)
        if errors:
            messagebox.showwarning("Delete Errors", "\n".join(errors))

    def install_selected_apk(self):
        sel = self.mac_tree.selection()
        apks = [os.path.join(self.mac_path, n) for n in sel if n.lower().endswith(".apk")]
        if not apks:
            apks = list(filedialog.askopenfilenames(title="Select APK(s)", filetypes=[("Android APK", "*.apk")]))
        if not apks or not self.selected_device.get():
            return

        self._set_busy(True, "Installing APK...")
        def worker():
            errors = []
            for apk in apks:
                code, out, err = self.run_adb(["install", "-r", apk])
                if code != 0:
                    errors.append(f"{os.path.basename(apk)}: {err.strip() or out.strip()}")
            def done():
                self._set_busy(False, "APK installation complete.")
                if errors:
                    messagebox.showwarning("Install Errors", "\n".join(errors))
                else:
                    messagebox.showinfo("Success", f"Installed {len(apks)} APK(s) successfully.")
            self.root.after(0, done)
        threading.Thread(target=worker, daemon=True).start()

    def capture_device_screenshot(self):
        if not self.selected_device.get():
            messagebox.showwarning("No Device", "Connect an Android device first.")
            return
        filename = f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        out_path = os.path.join(self.mac_path, filename)
        self._set_busy(True, "Capturing device screenshot...")

        def worker():
            cmd = [ADB_BIN, "-s", self.selected_device.get(), "exec-out", "screencap", "-p"]
            res = subprocess.run(cmd, capture_output=True)
            
            # Detect FLAG_SECURE / DRM blocks (returns empty or throws error)
            if len(res.stdout) == 0 or b"secure" in res.stderr.lower():
                self.root.after(0, lambda: self._set_busy(False))
                self.root.after(0, lambda: messagebox.showwarning("Screenshot Blocked", "Failed to capture screen.\nThe current app likely has FLAG_SECURE enabled (e.g., Banking, Netflix)."))
                return

            with open(out_path, "wb") as f:
                f.write(res.stdout)
                
            # macOS: Execute AppleScript to inject image directly into System Clipboard
            subprocess.run(["osascript", "-e", f'set the clipboard to (read (POSIX file "{out_path}") as JPEG picture)'])

            def done():
                self._set_busy(False)
                self.load_mac_directory(self.mac_path)
                self.mac_tree.selection_set(filename)
                self._on_item_selected("mac")
                self.status_var.set(f"Screenshot saved & copied to clipboard: {filename}")
            self.root.after(0, done)
        threading.Thread(target=worker, daemon=True).start()

    def show_device_info(self):
        if not self.selected_device.get():
            messagebox.showinfo("No Device", "No Android device connected.")
            return
        lines = []
        for key, label in [
            ("ro.product.manufacturer", "Manufacturer"),
            ("ro.product.model", "Model"),
            ("ro.build.version.release", "Android Version"),
            ("ro.build.version.sdk", "SDK Level"),
        ]:
            _, out, _ = self.run_adb(["shell", "getprop", key])
            lines.append(f"{label}: {out.strip() or 'Unknown'}")
        messagebox.showinfo("Device Info", "\n".join(lines))

    def push_selected_from_mac(self):
        sel = self.mac_tree.selection()
        if not sel:
            return
        paths = [os.path.join(self.mac_path, name) for name in sel]
        self._transfer_push(paths, self.adb_path)

    def _transfer_push(self, local_paths, target_adb_dir):
        if not self.selected_device.get():
            messagebox.showwarning("No Device", "Connect an Android device first.")
            return
        self._set_busy(True, f"Pushing to {target_adb_dir}...")
        def worker():
            total = len(local_paths)
            errors = []
            for idx, lpath in enumerate(local_paths, 1):
                name = os.path.basename(lpath)
                self.root.after(0, self.status_var.set, f"Pushing ({idx}/{total}): {name} -> {target_adb_dir}")
                code, out, err = self.run_adb(["push", lpath, target_adb_dir])
                if code != 0:
                    errors.append(f"{name}: {err.strip() or out.strip()}")
            def done():
                self._set_busy(False)
                self.load_adb_directory(self.adb_path)
                if errors:
                    self.status_var.set("Upload finished with errors.")
                    messagebox.showwarning("Upload Errors", "\n".join(errors))
                else:
                    self.status_var.set(f"Uploaded {total} item(s) to {target_adb_dir}")
            self.root.after(0, done)
        threading.Thread(target=worker, daemon=True).start()

    def pull_selected_from_adb(self):
        sel = self.adb_tree.selection()
        if not sel:
            return
        self._transfer_pull(list(sel), self.mac_path)

    def _transfer_pull(self, item_names, target_mac_dir):
        if not self.selected_device.get():
            return
        self._set_busy(True, f"Pulling to {target_mac_dir}...")
        src_dir = self.adb_path
        def worker():
            total = len(item_names)
            errors = []
            for idx, name in enumerate(item_names, 1):
                remote = f"{src_dir.rstrip('/')}/{name}"
                self.root.after(0, self.status_var.set, f"Pulling ({idx}/{total}): {name} -> {target_mac_dir}")
                code, out, err = self.run_adb(["pull", remote, target_mac_dir])
                if code != 0:
                    errors.append(f"{name}: {err.strip() or out.strip()}")
            def done():
                self._set_busy(False)
                self.load_mac_directory(self.mac_path)
                if errors:
                    self.status_var.set("Download finished with errors.")
                    messagebox.showwarning("Download Errors", "\n".join(errors))
                else:
                    self.status_var.set(f"Downloaded {total} item(s) to {target_mac_dir}")
            self.root.after(0, done)
        threading.Thread(target=worker, daemon=True).start()

    def _move_within_mac(self, item_names, dest_folder_name):
        dest_dir = os.path.join(self.mac_path, dest_folder_name)
        for name in item_names:
            if name == dest_folder_name:
                continue
            try:
                shutil.move(os.path.join(self.mac_path, name), os.path.join(dest_dir, name))
            except OSError as e:
                messagebox.showerror("Move Error", f"{name}: {e}")
        self.load_mac_directory(self.mac_path)
        self.status_var.set(f"Moved {len(item_names)} item(s) into {dest_folder_name}")

    def _move_within_adb(self, item_names, dest_folder_name):
        dest_dir = f"{self.adb_path.rstrip('/')}/{dest_folder_name}"
        errors = []
        for name in item_names:
            if name == dest_folder_name:
                continue
            src = f"{self.adb_path.rstrip('/')}/{name}"
            code, out, err = self.run_adb(["shell", f'mv "{src}" "{dest_dir}/"'])
            if code != 0:
                errors.append(f"{name}: {err.strip() or out.strip()}")
        self.load_adb_directory(self.adb_path)
        if errors:
            messagebox.showwarning("Move Errors", "\n".join(errors))
        else:
            self.status_var.set(f"Moved {len(item_names)} item(s) into {dest_folder_name}")

    def _clear_hover_highlight(self):
        if self.hovered_folder:
            pane_type, folder_name = self.hovered_folder
            tree = self.mac_tree if pane_type == "mac" else self.adb_tree
            if tree.exists(folder_name):
                tree.item(folder_name, tags=())
            self.hovered_folder = None

    def _update_hover_folder_at(self, x_root, y_root):
        widget = self.root.winfo_containing(x_root, y_root)
        target_pane = None
        if self._is_descendant(widget, self.mac_tree):
            target_pane = "mac"
        elif self._is_descendant(widget, self.adb_tree):
            target_pane = "adb"

        if not target_pane:
            self._clear_hover_highlight()
            return None, None

        tree = self.mac_tree if target_pane == "mac" else self.adb_tree
        cache = self.mac_items_cache if target_pane == "mac" else self.adb_items_cache
        local_y = y_root - tree.winfo_rooty()
        row_id = tree.identify_row(local_y)

        if row_id:
            match = next((x for x in cache if x["name"] == row_id and x["is_dir"]), None)
            if match and not (self.drag_source == target_pane and row_id in self.drag_items):
                if self.hovered_folder != (target_pane, row_id):
                    self._clear_hover_highlight()
                    tree.item(row_id, tags=("drop_hover",))
                    self.hovered_folder = (target_pane, row_id)
                return target_pane, row_id

        self._clear_hover_highlight()
        return target_pane, None

    def _on_drag_start(self, event, source):
        tree = self.mac_tree if source == "mac" else self.adb_tree
        row_id = tree.identify_row(event.y)
        if not row_id:
            self.drag_source = None
            return

        current_sel = tree.selection()
        if row_id not in current_sel:
            tree.selection_set(row_id)
            current_sel = (row_id,)

        self.drag_source = source
        self.drag_items = list(current_sel)
        self.drag_start_xy = (event.x_root, event.y_root)
        self.is_dragging = False

    def _on_drag_motion(self, event):
        if not self.drag_source or not self.drag_items:
            return

        dx = abs(event.x_root - self.drag_start_xy[0])
        dy = abs(event.y_root - self.drag_start_xy[1])
        if not self.is_dragging and (dx > 8 or dy > 8):
            self.is_dragging = True
            self._create_drag_ghost(event.x_root, event.y_root)

        if self.is_dragging and self.drag_ghost:
            self.drag_ghost.geometry(f"+{event.x_root + 14}+{event.y_root + 14}")
            target_pane, hovered_dir = self._update_hover_folder_at(event.x_root, event.y_root)
            self._update_drag_ghost_label(target_pane, hovered_dir)

    def _create_drag_ghost(self, x, y):
        self.drag_ghost = tk.Toplevel(self.root)
        self.drag_ghost.overrideredirect(True)
        self.drag_ghost.attributes("-topmost", True)
        try:
            self.drag_ghost.attributes("-alpha", 0.90)
        except tk.TclError:
            pass
        self.drag_ghost_label = tk.Label(self.drag_ghost, text="", bg=ACCENT_BLUE, fg="#FFFFFF", font=("SF Pro Text", 11, "bold"), padx=10, pady=5)
        self.drag_ghost_label.pack()
        self._update_drag_ghost_label(None, None)
        self.drag_ghost.geometry(f"+{x + 14}+{y + 14}")

    def _update_drag_ghost_label(self, target_pane, hovered_dir):
        if not self.drag_ghost_label:
            return
        count = len(self.drag_items)
        item_desc = self.drag_items[0] if count == 1 else f"{count} items"

        if hovered_dir:
            verb = "Move into" if target_pane == self.drag_source else "Copy into"
            text = f"{verb} {hovered_dir}/  ({item_desc})"
        elif target_pane and target_pane != self.drag_source:
            dest_label = "Phone" if target_pane == "adb" else "Mac"
            text = f"Copy to {dest_label}  ({item_desc})"
        else:
            text = f"Dragging {item_desc}"

        self.drag_ghost_label.config(text=text)

    def _on_drag_release(self, event):
        if self.drag_ghost:
            self.drag_ghost.destroy()
            self.drag_ghost = None
            self.drag_ghost_label = None

        if not self.is_dragging or not self.drag_source:
            self._clear_hover_highlight()
            self.drag_source = None
            return

        target_pane, hovered_dir = self._update_hover_folder_at(event.x_root, event.y_root)
        self._clear_hover_highlight()

        if target_pane == "mac":
            if self.drag_source == "adb":
                dest = os.path.join(self.mac_path, hovered_dir) if hovered_dir else self.mac_path
                self._transfer_pull(self.drag_items, dest)
            elif self.drag_source == "mac" and hovered_dir:
                self._move_within_mac(self.drag_items, hovered_dir)
        elif target_pane == "adb":
            if self.drag_source == "mac":
                paths = [os.path.join(self.mac_path, n) for n in self.drag_items]
                dest = f"{self.adb_path.rstrip('/')}/{hovered_dir}" if hovered_dir else self.adb_path
                self._transfer_push(paths, dest)
            elif self.drag_source == "adb" and hovered_dir:
                self._move_within_adb(self.drag_items, hovered_dir)

        self.drag_source = None
        self.drag_items = []
        self.is_dragging = False

    def _is_descendant(self, widget, ancestor):
        while widget is not None:
            if widget == ancestor:
                return True
            widget = widget.master
        return False

    def _on_finder_hover(self, event, pane_type):
        self._update_hover_folder_at(event.x_root, event.y_root)
        return COPY

    def _on_finder_drop(self, event, pane_type):
        _, hovered_dir = self._update_hover_folder_at(event.x_root, event.y_root)
        self._clear_hover_highlight()
        try:
            paths = list(self.root.tk.splitlist(event.data))
        except tk.TclError:
            paths = []
        valid_paths = [p for p in paths if os.path.exists(p)]
        if not valid_paths:
            return COPY

        if pane_type == "adb":
            dest = f"{self.adb_path.rstrip('/')}/{hovered_dir}" if hovered_dir else self.adb_path
            self._transfer_push(valid_paths, dest)
        elif pane_type == "mac":
            dest = os.path.join(self.mac_path, hovered_dir) if hovered_dir else self.mac_path
            for p in valid_paths:
                target = os.path.join(dest, os.path.basename(p))
                if os.path.abspath(p) != os.path.abspath(target):
                    shutil.copytree(p, target, dirs_exist_ok=True) if os.path.isdir(p) else shutil.copy2(p, target)
            self.load_mac_directory(self.mac_path)
            self.status_var.set(f"Copied {len(valid_paths)} item(s) from Finder to {dest}")
        return COPY

    def _on_mac_drag_out_to_finder(self, event):
        sel = self.mac_tree.selection()
        if not sel:
            return None
        paths = [os.path.join(self.mac_path, name) for name in sel]
        tcl_list = self.root.tk.call("list", *paths)
        return (COPY, DND_FILES, tcl_list)

    def _on_adb_drag_out_to_finder(self, event):
        sel = self.adb_tree.selection()
        if not sel or not self.selected_device.get():
            return None
        stage_dir = tempfile.mkdtemp(prefix="adb_finder_export_")
        staged_paths = []
        for name in sel:
            remote = f"{self.adb_path.rstrip('/')}/{name}"
            code, _, _ = self.run_adb(["pull", remote, stage_dir])
            local_item = os.path.join(stage_dir, name)
            if code == 0 and os.path.exists(local_item):
                staged_paths.append(local_item)
        if not staged_paths:
            return None
        tcl_list = self.root.tk.call("list", *staged_paths)
        return (COPY, DND_FILES, tcl_list)

    def _show_context_menu(self, event, source):
        tree = self.mac_tree if source == "mac" else self.adb_tree
        row_id = tree.identify_row(event.y)
        if row_id and row_id not in tree.selection():
            tree.selection_set(row_id)

        menu = tk.Menu(self.root, tearoff=0, bg=GLASS_ELEVATED, fg=TEXT_PRIMARY, activebackground=ACCENT_BLUE)
        if source == "mac":
            menu.add_command(label="Send to Phone", command=self.push_selected_from_mac)
            menu.add_command(label="Reveal in Finder", command=self.open_in_finder)
            menu.add_separator()
            menu.add_command(label="Rename", command=lambda: self._rename_item("mac"))
            menu.add_command(label="New Folder", command=self.mac_create_folder)
            menu.add_command(label="Delete", command=self.mac_delete_selected)
        else:
            menu.add_command(label="Pull to Mac", command=self.pull_selected_from_adb)
            menu.add_command(label="Copy Full Path", command=self._copy_adb_path)
            menu.add_separator()
            menu.add_command(label="Rename", command=lambda: self._rename_item("adb"))
            menu.add_command(label="New Folder", command=self.adb_create_folder)
            menu.add_command(label="Delete", command=self.adb_delete_selected)

        menu.tk_popup(event.x_root, event.y_root)

    def _copy_adb_path(self):
        sel = self.adb_tree.selection()
        if not sel:
            return
        full_path = f"{self.adb_path.rstrip('/')}/{sel[0]}"
        self.root.clipboard_clear()
        self.root.clipboard_append(full_path)
        self.status_var.set(f"Copied path: {full_path}")

    def _rename_item(self, source):
        tree = self.mac_tree if source == "mac" else self.adb_tree
        sel = tree.selection()
        if not sel:
            return
        old_name = sel[0]
        new_name = simpledialog.askstring("Rename", "Enter new name:", initialvalue=old_name)
        if not new_name or not new_name.strip() or new_name.strip() == old_name:
            return
        new_name = new_name.strip()

        if source == "mac":
            try:
                os.rename(os.path.join(self.mac_path, old_name), os.path.join(self.mac_path, new_name))
                self.load_mac_directory(self.mac_path)
            except OSError as e:
                messagebox.showerror("Rename Error", str(e))
        else:
            src = f"{self.adb_path.rstrip('/')}/{old_name}"
            dst = f"{self.adb_path.rstrip('/')}/{new_name}"
            code, out, err = self.run_adb(["shell", f'mv "{src}" "{dst}"'])
            if code != 0:
                messagebox.showerror("Rename Error", err.strip() or out.strip())
            else:
                self.load_adb_directory(self.adb_path)

    def _on_item_selected(self, source):
        tree = self.mac_tree if source == "mac" else self.adb_tree
        cache = self.mac_items_cache if source == "mac" else self.adb_items_cache
        sel = tree.selection()
        if not sel:
            return

        name = sel[0]
        item = next((x for x in cache if x["name"] == name), None)
        if not item:
            return

        self.info_name_var.set(name)
        self.info_type_var.set("Type: Folder" if item["is_dir"] else f"Type: {os.path.splitext(name)[1].upper() or 'File'}")
        self.info_size_var.set(f"Size: {item['size_str']}")
        self.info_mod_var.set(f"Modified: {item['mtime']}")

        ext = os.path.splitext(name)[1].lower()
        self.preview_request_id += 1
        req_id = self.preview_request_id

        if item["is_dir"] or ext not in IMAGE_EXTS or not HAS_PIL:
            self.preview_canvas.delete("all")
            icon_key = classify_file_icon(name, item["is_dir"])
            large_icon = self.icons.get(icon_key, 56)
            self.preview_canvas.create_image(102, 95, image=large_icon, anchor=tk.CENTER)
            if ext in IMAGE_EXTS and not HAS_PIL:
                self.preview_canvas.create_text(102, 155, text="Install 'pillow'\nfor thumbnails", fill=TEXT_SECONDARY, justify=tk.CENTER)
            return

        if source == "mac":
            self._render_thumbnail_async(os.path.join(self.mac_path, name), req_id)
        else:
            if item["size"] and item["size"] > 25 * 1024 * 1024:
                self.preview_canvas.delete("all")
                self.preview_canvas.create_text(102, 102, text="Image too large\nfor live preview (>25MB)", fill=TEXT_SECONDARY, justify=tk.CENTER)
                return
            self._pull_and_preview_adb_image(name, req_id)

    def _pull_and_preview_adb_image(self, name, req_id):
        self.preview_canvas.delete("all")
        self.preview_canvas.create_text(102, 102, text="Loading preview...", fill=TEXT_SECONDARY)
        remote_path = f"{self.adb_path.rstrip('/')}/{name}"
        cached_file = os.path.join(self.thumb_temp_dir, f"{int(time.time() * 1000)}_{name}")

        def worker():
            code, _, _ = self.run_adb(["pull", remote_path, cached_file])
            if code == 0 and os.path.isfile(cached_file):
                self._render_thumbnail_async(cached_file, req_id)
        threading.Thread(target=worker, daemon=True).start()

    def _render_thumbnail_async(self, image_path, req_id):
        def worker():
            try:
                with Image.open(image_path) as img:
                    img.thumbnail((192, 192))
                    tk_img = ImageTk.PhotoImage(img.copy())
                def apply():
                    if req_id != self.preview_request_id:
                        return
                    self.current_preview_img = tk_img
                    self.preview_canvas.delete("all")
                    self.preview_canvas.create_image(102, 102, image=tk_img, anchor=tk.CENTER)
                self.root.after(0, apply)
            except Exception:
                pass
        threading.Thread(target=worker, daemon=True).start()

    # --- ADVANCED ROADMAP FEATURES ---
    
    def open_logcat_window(self):
        if not self.selected_device.get():
            messagebox.showwarning("No Device", "Connect an Android device first.")
            return
            
        theme_colors = {'GLASS_BG': GLASS_BG, 'GLASS_PANEL': GLASS_PANEL, 'GLASS_ELEVATED': GLASS_ELEVATED, 'TEXT_PRIMARY': TEXT_PRIMARY, 'TEXT_SECONDARY': TEXT_SECONDARY}
        ADBLogcatWindow(self.root, self.selected_device.get(), ADB_BIN, theme_colors)
        
    def launch_scrcpy(self):
        if not self.selected_device.get():
            messagebox.showwarning("No Device", "Connect an Android device first.")
            return
            
        # Resolve scrcpy path explicitly for macOS GUI apps
        scrcpy_bin = shutil.which("scrcpy")
        if not scrcpy_bin:
            for path in ["/opt/homebrew/bin/scrcpy", "/usr/local/bin/scrcpy"]:
                if os.path.isfile(path) and os.access(path, os.X_OK):
                    scrcpy_bin = path
                    break
                    
        if not scrcpy_bin:
            messagebox.showerror("Dependency Missing", "Scrcpy is not installed.\nRun: brew install scrcpy")
            return
            
        self.status_var.set("Launching Scrcpy mirroring...")
        subprocess.Popen(
            [scrcpy_bin, "-s", self.selected_device.get(), "--max-fps", "60", "--window-title", f"Glass Mirror: {self.selected_device.get()}"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )

    def toggle_screen_record(self):
        if not self.selected_device.get():
            return
            
        if hasattr(self, 'recording_process') and self.recording_process:
            self.recording_process.terminate()
            self.recording_process = None
            self.status_var.set("Pulling screen recording...")
            
            out_file = f"Record_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
            dest = os.path.join(self.mac_path, out_file)
            
            def pull_worker():
                time.sleep(1.5) # Give Android MP4 muxer time to finalize the file
                self.run_adb(["pull", "/sdcard/recording_temp.mp4", dest])
                self.run_adb(["shell", "rm", "/sdcard/recording_temp.mp4"])
                self.root.after(0, lambda: self.load_mac_directory(self.mac_path))
                self.root.after(0, lambda: self.status_var.set(f"Recording saved: {out_file}"))
                
            threading.Thread(target=pull_worker, daemon=True).start()
        else:
            res = simpledialog.askstring("Resolution", "Resolution (e.g. 1920x1080) or leave blank:")
            bitrate = simpledialog.askstring("Bitrate", "Bitrate in Mbps (e.g. 8 for high quality):", initialvalue="8")
            
            cmd = [ADB_BIN, "-s", self.selected_device.get(), "shell", "screenrecord"]
            if res and "x" in res:
                cmd.extend(["--size", res.strip()])
            if bitrate and bitrate.isdigit():
                cmd.extend(["--bit-rate", str(int(bitrate) * 1000000)])
                
            cmd.append("/sdcard/recording_temp.mp4")
            
            self.recording_process = subprocess.Popen(cmd)
            self.status_var.set("🔴 Recording... Click Screen Record again to STOP and save.")

    def inject_clipboard_to_device(self):
        if not self.selected_device.get():
            return
        
        try:
            mac_clip = self.root.clipboard_get()
            if not mac_clip:
                return
            escaped_text = mac_clip.replace(' ', '%s').replace("'", "\\'").replace('"', '\\"')
            
            def worker():
                code, _, _ = self.run_adb(["shell", "input", "text", f"'{escaped_text}'"])
                if code == 0:
                    self.root.after(0, lambda: self.status_var.set("Clipboard injected to device."))
                else:
                    self.root.after(0, lambda: self.status_var.set("Failed to inject clipboard."))
                    
            threading.Thread(target=worker, daemon=True).start()
        except tk.TclError:
            self.status_var.set("Mac clipboard is empty.")

    def _device_monitor_loop(self):
        """Background thread polling for ADB device state changes."""
        while self._monitor_running:
            try:
                res = subprocess.run([ADB_BIN, "devices"], capture_output=True, text=True, timeout=5)
                if res.returncode == 0:
                    current_devices = [
                        line.strip().split()[0] 
                        for line in res.stdout.splitlines()[1:] 
                        if len(line.strip().split()) >= 2 and line.strip().split()[1] == "device"
                    ]
                    # Safely schedule UI update
                    self.root.after(0, lambda d=current_devices: self._sync_devices_list(d))
            except Exception:
                pass
            time.sleep(2) # Poll every 2 seconds

    def _sync_devices_list(self, current_devices):
        """Handles the edge cases of devices connecting/disconnecting dynamically."""
        prev_devices = list(self.device_combo["values"])
        if current_devices != prev_devices:
            self.device_combo["values"] = current_devices
            selected = self.selected_device.get()
            
            if not current_devices:
                # Edge Case: All devices unplugged
                self.selected_device.set("")
                self.status_var.set("All ADB devices disconnected.")
                for row in self.adb_tree.get_children():
                    self.adb_tree.delete(row)
                self.adb_path_entry.delete(0, tk.END)
                self.adb_count_var.set("0 items")
                self.adb_storage_var.set("")
                
            elif selected not in current_devices:
                # Edge Case: The active device was unplugged, but others remain
                self.selected_device.set(current_devices[0])
                self.status_var.set(f"Switched to {current_devices[0]}")
                self.load_adb_directory(self.adb_path if self.adb_path else "/sdcard")
                
            elif not prev_devices and current_devices:
                # Edge Case: App started with no devices, and one was just plugged in
                self.selected_device.set(current_devices[0])
                self.load_adb_directory("/sdcard")

    def _on_app_close(self):
        """Kills background threads and active ADB streams upon exit."""
        self._monitor_running = False
        if hasattr(self, 'recording_process') and self.recording_process:
            self.recording_process.terminate()
        self.root.destroy()

    def uninstall_selected_package(self):
        package_name = simpledialog.askstring("Uninstall App", "Enter precise package name (e.g., com.example.app):")
        if not package_name:
            return
            
        if messagebox.askyesno("Confirm", f"Are you sure you want to permanently uninstall {package_name}?"):
            self._set_busy(True, f"Uninstalling {package_name}...")
            
            def worker():
                code, out, err = self.run_adb(["uninstall", package_name.strip()])
                msg = "Successfully uninstalled." if code == 0 else f"Error: {err or out}"
                self.root.after(0, lambda: self._set_busy(False, msg))
                if code != 0:
                    self.root.after(0, lambda: messagebox.showerror("Uninstall Failed", msg))
                    
            threading.Thread(target=worker, daemon=True).start()


if __name__ == "__main__":
    root = TkinterDnD.Tk() if HAS_DND2 else tk.Tk()
    app = ADBFileManagerApp(root)
    root.mainloop()
