import os
import shutil
import subprocess
import tempfile
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
from ttkthemes import ThemedTk
import webbrowser


def list_drives():
    """Lists available drives on Windows & Linux."""
    drives = []
    if os.name == "nt":
        for letter in "CDEFGHIJKLMNOPQRSTUVWXYZ":
            path = f"{letter}:"
            if os.path.exists(path):
                drives.append(path)
        return drives

    user = os.getenv("USER") or os.getenv("USERNAME") or ""
    mount_roots = ["/media", "/run/media"]
    for root in mount_roots:
        if not os.path.isdir(root):
            continue
        bases = []
        if user and os.path.isdir(os.path.join(root, user)):
            bases.append(os.path.join(root, user))
        bases.append(root)
        for base in bases:
            if not os.path.isdir(base):
                continue
            for name in os.listdir(base):
                path = os.path.join(base, name)
                if os.path.ismount(path):
                    drives.append(path)
    return drives


class AutoUSBApp(ThemedTk):
    def __init__(self):
        super().__init__()
        self.title("AutoUSB: USB autorun helper")
        self.get_themes()
        self.set_theme("arc")
        self.resizable(False, False)
        self._center_window(520, 340)
        self.configure(padx=10, pady=8)
        self.last_built_exe = ""
        self.bg_color = "#eaf0fb"
        self.panel_color = "#ffffff"
        self.accent_color = "#2f7bff"
        self.accent_hover = "#2264d4"
        self.text_color = "#182a43"
        self._configure_style()
        self._build_ui()
        self.refresh_drives()

    def _next_available_path(self, folder, filename):
        """Returns a path in folder that does not overwrite existing files."""
        base, ext = os.path.splitext(filename)
        candidate = os.path.join(folder, filename)
        counter = 1
        while os.path.exists(candidate):
            candidate = os.path.join(folder, f"{base}_{counter}{ext}")
            counter += 1
        return candidate

    def _center_window(self, width, height):
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")

    def _configure_style(self):
        style = ttk.Style(self)
        self.configure(background=self.bg_color)
        style.configure(".", background=self.bg_color, foreground=self.text_color)
        style.configure("TFrame", padding=4, background=self.panel_color)
        style.configure("Card.TFrame", padding=6, background=self.panel_color)
        style.configure("TNotebook", background=self.bg_color, padding=4)
        style.configure(
            "TNotebook.Tab",
            padding=(12, 6),
            background=self.panel_color,
            foreground=self.text_color,
        )
        style.map(
            "TNotebook.Tab",
            background=[("selected", self.bg_color), ("active", self.bg_color)],
            foreground=[("selected", self.text_color)],
        )
        style.configure("TLabel", padding=(2, 2), background=self.panel_color, foreground=self.text_color)
        style.configure(
            "TButton",
            padding=(8, 5),
            background=self.panel_color,
            foreground="#000000",
        )
        style.map("TButton", background=[("active", "#e5e9f2"), ("!disabled", self.panel_color)])
        style.configure(
            "Accent.TButton",
            padding=(8, 5),
            foreground="#000000",
            background=self.panel_color,
        )
        style.map("Accent.TButton", background=[("active", "#e5e9f2"), ("!disabled", self.panel_color)])
        style.configure("Header.TLabel", font=("Helvetica", 18, "bold"), background=self.bg_color)
        style.configure("Sub.TLabel", font=("Helvetica", 11), background=self.bg_color)
        style.configure("Section.TLabel", font=("Helvetica", 12, "bold"), background=self.panel_color)

    def _build_ui(self):
        header = ttk.Frame(self, style="Card.TFrame")
        header.pack(fill="x")
        ttk.Label(header, text="Welcome to AutoUSB", style="Header.TLabel").pack(anchor="w")
        # Subtitle removed for a cleaner header

        body = ttk.Frame(self, style="Card.TFrame")
        body.pack(fill="x", expand=False, pady=(0, 0))

        form = ttk.Frame(body, style="Card.TFrame")
        form.pack(fill="x", pady=(0, 8))
        ttk.Label(form, text="USB drive").grid(row=0, column=0, sticky="w", pady=4)
        self.drive_var = tk.StringVar()
        self.drive_combo = ttk.Combobox(
            form, textvariable=self.drive_var, state="readonly", width=24, values=list_drives()
        )
        self.drive_combo.grid(row=0, column=1, columnspan=2, sticky="ew", pady=4, padx=(6, 4))
        btn_refresh = ttk.Button(form, text="Refresh", command=self.refresh_drives)
        btn_refresh.grid(row=0, column=3, sticky="e", pady=4, ipady=1)
        form.grid_columnconfigure(1, weight=1)
        form.grid_columnconfigure(2, weight=1)

        ttk.Label(form, text="Label (optional)").grid(row=1, column=0, sticky="w", pady=4)
        self.name_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.name_var).grid(row=1, column=1, columnspan=3, sticky="ew", pady=4, padx=(6, 0))

        ttk.Label(form, text="Executable to auto-run").grid(row=2, column=0, sticky="w", pady=(8, 4))
        self.start_file_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.start_file_var).grid(row=2, column=1, sticky="ew", pady=(8, 4), padx=(6, 4))
        ttk.Button(form, text="Browse", command=self.select_start_file).grid(row=2, column=2, sticky="w", pady=(8, 4))
        ttk.Button(form, text="Batch to EXE", command=self.open_batch_builder).grid(
            row=2, column=3, sticky="w", pady=(8, 4), padx=(6, 0)
        )

        self.autorun_status_var = tk.StringVar()
        ttk.Label(form, textvariable=self.autorun_status_var, foreground="#3c763d").grid(
            row=3, column=0, columnspan=4, sticky="w", pady=(6, 2)
        )
        self.batch_status_var = tk.StringVar()
        ttk.Label(form, textvariable=self.batch_status_var, foreground="#3c763d").grid(
            row=4, column=0, columnspan=4, sticky="w", pady=(0, 0)
        )

        footer = ttk.Frame(self)
        footer.pack(fill="x", pady=(12, 4))
        ttk.Button(footer, text="Open GitHub", command=self.open_github).pack(side="left")
        ttk.Button(footer, text="Help", command=self.show_help).pack(side="left", padx=(6, 0))
        ttk.Button(footer, text="Save", command=self.save_everything, style="Accent.TButton").pack(side="right")

    # --- Autorun logic ---
    def refresh_drives(self):
        drives = list_drives()
        self.drive_combo["values"] = drives
        if drives:
            self.drive_combo.current(0)
        self.autorun_status_var.set("")

    def select_start_file(self):
        start_file = filedialog.askopenfilename(
            title="Select Start File",
            filetypes=[
                ("Executable Files", "*.exe"),
                ("All Files", "*.*"),
            ],
        )
        if start_file:
            self.start_file_var.set(start_file)

    def create_autorun(self, copy_files=False, notify=True):
        drive = self.drive_var.get()
        new_name = self.name_var.get().strip()
        start_file_path = self.start_file_var.get().strip()

        if not drive:
            messagebox.showerror("Error", "Please select a USB drive.")
            return False

        if not os.path.isdir(drive):
            messagebox.showerror("Error", f"Drive '{drive}' does not exist.")
            return False
        start_file_name = ""

        if start_file_path and not os.path.isfile(start_file_path):
            messagebox.showerror("Error", f"File not found: {start_file_path}")
            return False

        if copy_files:
            if not start_file_path:
                messagebox.showerror("Error", "Select an executable to auto-run before saving to USB.")
                return False
            start_file_name = os.path.basename(start_file_path)
            destination_start_file_path = os.path.join(drive, start_file_name)
            try:
                shutil.copy2(start_file_path, destination_start_file_path)
            except Exception as exc:
                messagebox.showerror("Error", f"Could not copy the start file: {exc}")
                return False
        else:
            if start_file_path:
                start_file_name = os.path.basename(start_file_path)

        autorun_lines = ["[Autorun]"]
        if new_name:
            autorun_lines.append(f"Label={new_name}")
        if start_file_name:
            # Use both Open and ShellExecute for better compatibility
            autorun_lines.append(f"Open={start_file_name}")
            autorun_lines.append(f"ShellExecute={start_file_name}")
            autorun_lines.append("Action=Run autorun")
            autorun_lines.append("UseAutoPlay=1")
            # If there's no explicit icon, let the exe act as the icon
            autorun_lines.append(f"Icon={start_file_name}")
        autorun_lines.append("; autorun.inf created by AutoUSB")
        # Windows prefers CRLF line endings for autorun.inf
        autorun_content = "\r\n".join(autorun_lines) + "\r\n"
        autorun_path = os.path.join(drive, "autorun.inf")

        try:
            with open(autorun_path, "w", encoding="utf-8") as f:
                f.write(autorun_content)
            self.autorun_status_var.set(f"autorun.inf created at {autorun_path}")
            if notify:
                messagebox.showinfo("Success", f"autorun.inf saved to {autorun_path}")
            return True
        except Exception as exc:
            messagebox.showerror("Error", f"Could not create autorun.inf: {exc}")
            return False

    def show_help(self):
        help_text = (
            "1) Pick your USB drive and optional label.\n"
            "2) Choose the executable to auto-run, or click 'Batch to EXE' to paste commands and generate one.\n"
            "3) Click 'Save' to copy the EXE and write autorun.inf.\n\n"
            "Note: Modern Windows limits USB autorun; you may still get an AutoPlay prompt. Batch to EXE uses PyInstaller (pip install pyinstaller) and must be built on Windows."
        )
        messagebox.showinfo("How to use AutoUSB", help_text)

    def open_github(self):
        webbrowser.open("https://github.com/tripleu613/AutoUSB")

    # --- Batch logic ---
    def open_batch_builder(self):
        builder = tk.Toplevel(self)
        builder.title("Build EXE from batch")
        builder.geometry("560x420")
        builder.transient(self)
        builder.grab_set()

        frame = ttk.Frame(builder, padding=10)
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text="Paste your batch commands, then build an EXE (saved here).", style="Section.TLabel").pack(
            anchor="w", pady=(0, 6)
        )
        text = tk.Text(
            frame,
            height=14,
            width=70,
            wrap="word",
            font=("Consolas", 10),
            bg="#f6f8ff",
            fg=self.text_color,
            insertbackground=self.text_color,
            relief="flat",
            bd=1,
            highlightbackground="#d6def2",
            highlightcolor=self.accent_color,
            highlightthickness=1,
        )
        text.pack(fill="both", expand=True, pady=4)
        text.insert(
            "1.0",
            "@echo off\n"
            "rem Paste your commands below. Example:\n"
            "rem start \"\" \"%~dp0MyApp.exe\"\n",
        )

        status_var = tk.StringVar()
        ttk.Label(frame, textvariable=status_var, foreground="#3c763d").pack(anchor="w", pady=(4, 0))

        btns = ttk.Frame(frame)
        btns.pack(fill="x", pady=(8, 0))

        def build_now():
            content = text.get("1.0", "end").strip().replace("\r\n", "\n")
            self.build_batch_to_exe(content, status_var=status_var, parent=builder)

        ttk.Button(btns, text="Build EXE (save here)", command=build_now).pack(side="left")
        ttk.Button(btns, text="Close", command=builder.destroy).pack(side="right")

    def build_batch_to_exe(self, content, status_var=None, parent=None):
        if not content:
            messagebox.showerror("Empty batch", "Add some commands before converting.")
            return

        binary_label = "EXE"
        base_name = "autorun_built.exe"
        save_path = self._next_available_path(os.getcwd(), base_name)

        if os.name == "nt":
            pyinstaller = shutil.which("pyinstaller")
            if not pyinstaller:
                messagebox.showerror(
                    "PyInstaller missing",
                    "PyInstaller is required to build the EXE.\nInstall with: pip install pyinstaller",
                )
                return

            if status_var:
                status_var.set(f"Building {binary_label} with PyInstaller...")
            self.batch_status_var.set(f"Building {binary_label} with PyInstaller...")
            self.update_idletasks()

            runner_template = (
                "import os, subprocess, tempfile\n"
                f"SCRIPT_CONTENT = {content!r}\n"
                "IS_WINDOWS = True\n\n"
                "def main():\n"
                "    suffix = '.bat' if IS_WINDOWS else '.sh'\n"
                "    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix, mode='w', encoding='utf-8') as fh:\n"
                "        fh.write(SCRIPT_CONTENT)\n"
                "        script_path = fh.name\n"
                "    try:\n"
                "        if IS_WINDOWS:\n"
                "            creation_flags = getattr(subprocess, 'CREATE_NO_WINDOW', 0)\n"
                "            subprocess.run(['cmd', '/c', script_path], check=False, creationflags=creation_flags)\n"
                "        else:\n"
                "            os.chmod(script_path, 0o700)\n"
                "            subprocess.run(['bash', script_path], check=False)\n"
                "    finally:\n"
                "        try:\n"
                "            os.remove(script_path)\n"
                "        except OSError:\n"
                "            pass\n\n"
                "if __name__ == '__main__':\n"
                "    main()\n"
            )

            try:
                with tempfile.TemporaryDirectory() as tmpdir:
                    runner_path = os.path.join(tmpdir, "runner.py")
                    with open(runner_path, "w", encoding="utf-8") as fh:
                        fh.write(runner_template)

                    exe_name = os.path.splitext(os.path.basename(save_path))[0]
                    cmd = [
                        pyinstaller,
                        "--onefile",
                        "--noconsole",
                        "--clean",
                        "--distpath",
                        tmpdir,
                        "--name",
                        exe_name,
                        runner_path,
                    ]
                    result = subprocess.run(cmd, capture_output=True, text=True, cwd=tmpdir)
                    if result.returncode != 0:
                        raise RuntimeError(result.stderr or result.stdout)

                    built_path = os.path.join(tmpdir, f"{exe_name}.exe")
                    if not os.path.exists(built_path):
                        raise FileNotFoundError("Expected build artifact not found after PyInstaller run.")
                    shutil.copy2(built_path, save_path)
            except Exception as exc:
                if status_var:
                    status_var.set("")
                self.batch_status_var.set("")
                messagebox.showerror("Build failed", f"Could not create {binary_label}:\n{exc}")
                return
        else:
            compiler = shutil.which("x86_64-w64-mingw32-g++") or shutil.which("i686-w64-mingw32-g++")
            if not compiler:
                maybe_apt = shutil.which("apt-get")
                if maybe_apt and messagebox.askyesno(
                    "Install MinGW-w64?",
                    "To build a Windows EXE on Linux, MinGW-w64 is required.\n\n"
                    "Install now with: sudo apt-get install -y mingw-w64 ?",
                ):
                    try:
                        install_cmd = ["sudo", "apt-get", "install", "-y", "mingw-w64"]
                        result = subprocess.run(install_cmd, capture_output=True, text=True)
                        if result.returncode != 0:
                            raise RuntimeError(result.stderr or result.stdout)
                        compiler = shutil.which("x86_64-w64-mingw32-g++") or shutil.which("i686-w64-mingw32-g++")
                    except Exception as exc:
                        messagebox.showerror(
                            "Install failed",
                            f"Could not install mingw-w64 automatically:\n{exc}\n\n"
                            "Please install mingw-w64 manually (e.g., sudo apt-get install mingw-w64).",
                        )
                        return
                if not compiler:
                    messagebox.showerror(
                        "MinGW-w64 missing",
                        "To build a Windows EXE on Linux, install MinGW-w64 (e.g., apt install mingw-w64) "
                        "to get x86_64-w64-mingw32-g++.",
                    )
                    return

            if status_var:
                status_var.set(f"Building {binary_label} with MinGW-w64 cross-compiler...")
            self.batch_status_var.set(f"Building {binary_label} with MinGW-w64 cross-compiler...")
            self.update_idletasks()

            def escape_cpp_string(text):
                return (
                    text.replace("\\", "\\\\")
                    .replace('"', '\\"')
                    .replace("\r", "")
                    .replace("\n", "\\n\"\n\"")
                )

            escaped_batch = escape_cpp_string(content)
            cpp_template = f'''
#include <windows.h>
#include <string>
#include <fstream>

int WINAPI WinMain(HINSTANCE, HINSTANCE, LPSTR, int) {{
    char tempPath[MAX_PATH];
    if (!GetTempPathA(MAX_PATH, tempPath)) return 1;
    char tempFile[MAX_PATH];
    if (!GetTempFileNameA(tempPath, "ab", 0, tempFile)) return 1;
    {{
        std::ofstream out(tempFile, std::ios::binary);
        out << "{escaped_batch}";
    }}
    STARTUPINFOA si = {{0}};
    si.cb = sizeof(si);
    PROCESS_INFORMATION pi = {{0}};
    std::string cmd = std::string("cmd /c \\"") + tempFile + "\\"";
    if (!CreateProcessA(NULL, cmd.data(), NULL, NULL, FALSE, CREATE_NO_WINDOW, NULL, NULL, &si, &pi)) {{
        return 1;
    }}
    CloseHandle(pi.hProcess);
    CloseHandle(pi.hThread);
    DeleteFileA(tempFile);
    return 0;
}}
'''
            try:
                with tempfile.TemporaryDirectory() as tmpdir:
                    cpp_path = os.path.join(tmpdir, "stub.cpp")
                    with open(cpp_path, "w", encoding="utf-8") as fh:
                        fh.write(cpp_template)

                    out_path = os.path.join(tmpdir, "autorun.exe")
                    cmd = [
                        compiler,
                        "-Os",
                        "-static",
                        "-s",
                        "-mwindows",
                        cpp_path,
                        "-o",
                        out_path,
                    ]
                    result = subprocess.run(cmd, capture_output=True, text=True)
                    if result.returncode != 0:
                        raise RuntimeError(result.stderr or result.stdout)

                    shutil.copy2(out_path, save_path)
            except Exception as exc:
                if status_var:
                    status_var.set("")
                self.batch_status_var.set("")
                messagebox.showerror(
                    "Build failed",
                    f"Could not create {binary_label} with MinGW-w64:\n{exc}\n\n"
                    "Ensure MinGW-w64 cross-compiler is installed and try again.",
                )
                return

        if status_var:
            status_var.set(f"{binary_label} saved to {save_path}")
        self.last_built_exe = save_path
        self.start_file_var.set(save_path)
        self.batch_status_var.set(f"{binary_label} saved to {save_path}")
        messagebox.showinfo(
            "Done",
            f"Executable saved to:\n{save_path}\n\nIt is now set as your autorun target.",
            parent=parent,
        )
        if parent:
            parent.destroy()

    def save_everything(self):
        drive = self.drive_var.get().strip()
        if not drive:
            messagebox.showerror("Error", "Select a USB drive first.")
            return
        if not os.path.isdir(drive):
            messagebox.showerror("Error", f"Drive '{drive}' does not exist.")
            return

        autorun_ok = self.create_autorun(copy_files=True, notify=False)
        if autorun_ok is False:
            return

        msg = f"Saved autorun.inf and executable to {drive}"
        self.autorun_status_var.set(msg)
        self.batch_status_var.set(msg)
        messagebox.showinfo("Saved", msg)


if __name__ == "__main__":
    app = AutoUSBApp()
    app.mainloop()
