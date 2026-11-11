import json
import os
import sys

APP_NAME = "gblame"
APP_VERSION = "0.1.0"


def app_base_dir():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def resource_dir():
    if getattr(sys, "frozen", False):
        return getattr(sys, "_MEIPASS", app_base_dir())
    return os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")


def config_dir():
    base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
    path = os.path.join(base, APP_NAME, "config")
    os.makedirs(path, exist_ok=True)
    return path


def default_library_dir():
    return os.path.join(os.environ.get("TEMP") or "/tmp", APP_NAME)


DEFAULTS = {
    "mgba_path": "",
    "library_dir": "",
    "port": None,
    "max_baud": 1500000,
    "mode": "auto",
}


class Settings:
    def __init__(self):
        self.path = os.path.join(config_dir(), "settings.json")
        self.data = dict(DEFAULTS)
        self.load()

    def load(self):
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                stored = json.load(f)
            for k in DEFAULTS:
                if k in stored:
                    self.data[k] = stored[k]
        except (OSError, ValueError):
            pass

    def save(self):
        try:
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=2)
        except OSError:
            pass

    def get(self, key, default=None):
        value = self.data.get(key, default)
        return default if value in (None, "") and default is not None else value

    def set(self, key, value):
        self.data[key] = value
        self.save()

    @property
    def library_dir(self):
        return self.data.get("library_dir") or default_library_dir()
