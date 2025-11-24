# AutoUSB

Tiny Tk/ttkthemes helper that writes `autorun.inf` to a USB drive, lets you pick the EXE to run, and can turn a batch script into an EXE.

## Use
- Select your USB drive and (optionally) a label.
- Pick the executable to auto-run, or click **Batch to EXE** to paste commands and build one.
- Click **Save** to copy the EXE and write `autorun.inf` to the USB root.

## Batch → EXE
- Windows: `pip install -r requirements.txt`, then use **Batch to EXE** (PyInstaller).
- Linux: install MinGW-w64 (e.g., `sudo apt-get install mingw-w64`). The app will prompt to install it if missing, then builds a Windows EXE via the cross-compiler.

<img width="548" height="406" alt="image" src="https://github.com/user-attachments/assets/2e31730c-5285-4540-bd8c-24851b7f419c" />

