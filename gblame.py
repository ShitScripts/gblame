import os
import sys

# FlashGBX is vendored in-tree (see vendor/); make it importable before anything else.
if getattr(sys, "frozen", False):
    _ROOT = sys._MEIPASS
else:
    _ROOT = os.path.dirname(os.path.abspath(__file__))
_VENDOR = os.path.join(_ROOT, "vendor")
if os.path.isdir(_VENDOR) and _VENDOR not in sys.path:
    sys.path.insert(0, _VENDOR)

from PySide6.QtGui import QFont, QFontDatabase
from PySide6.QtWidgets import QApplication

from app import config as gcfg
from app.config import Settings
from app.ui import styles
from app.ui.main_window import MainWindow


def load_fonts():
    fonts_dir = os.path.join(gcfg.resource_dir(), "fonts")
    if not os.path.isdir(fonts_dir):
        return
    for name in os.listdir(fonts_dir):
        if name.lower().endswith((".otf", ".ttf")):
            QFontDatabase.addApplicationFont(os.path.join(fonts_dir, name))


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("gblame")
    app.setOrganizationName("gblame")
    load_fonts()
    app.setFont(QFont("Open Sans", 9))
    app.setStyleSheet(styles.QSS)

    settings = Settings()
    os.makedirs(settings.library_dir, exist_ok=True)

    window = MainWindow(settings)
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
