import os
import shutil
import subprocess
import sys


def _bundled_mgba():
    """mGBA vendored in-tree under vendor/mgba (also bundled by PyInstaller)."""
    if getattr(sys, "frozen", False):
        base = getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
    else:
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    exe = os.path.join(base, "vendor", "mgba", "mGBA.exe")
    return exe if os.path.isfile(exe) else None


FALLBACKS = [
    r"C:\Program Files\mGBA\mgba-qt.exe",
    r"C:\Program Files (x86)\mGBA\mgba-qt.exe",
    r"C:\Program Files\mGBA\mGBA.exe",
    r"C:\mGBA\mgba-qt.exe",
    os.path.expandvars(r"%LOCALAPPDATA%\Programs\mGBA\mgba-qt.exe"),
]


def find_mgba(settings):
    override = settings.data.get("mgba_path")
    if override and os.path.isfile(override):
        return override
    bundled = _bundled_mgba()
    if bundled:
        return bundled
    for exe in ("mgba-qt", "mgba", "mGBA"):
        found = shutil.which(exe)
        if found:
            return found
    for path in FALLBACKS:
        if path and os.path.isfile(path):
            return path
    return None


def launch(rom_path, settings):
    """Start mGBA on the dumped ROM. Returns (ok, message)."""
    exe = find_mgba(settings)
    if not exe:
        return False, (
            "mGBA was not found.\n\n"
            "The bundled emulator appears to be missing. Install mGBA from "
            "https://mgba.io/downloads.html and set its location in gblame Settings.")
    if not os.path.isfile(rom_path):
        return False, "ROM file not found: " + rom_path
    try:
        subprocess.Popen([exe, rom_path], close_fds=True)
        return True, "Launched " + os.path.basename(exe)
    except OSError as e:
        return False, "Could not launch mGBA: " + str(e)
