"""gblame stylesheet — design tokens reverse-engineered from Epilogue Playback's
combined.qss (colors, radii, type scale). Fonts: Open Sans (Apache 2.0)."""

BG = "#202020"
BG_DEEP = "#1a1a1a"
CARD = "#2D2D2D"
CARD_RAISED = "#343434"
BORDER = "#424242"
BORDER_HOVER = "#555555"
TEXT = "#D0D0D0"
TEXT_DIM = "#8E8E8E"
BLUE = "#0074E0"
BLUE_HOVER = "#2C88F1"
BLUE_PRESSED = "#1F6FD1"
RED = "#C81844"
RED_HOVER = "#D63A5C"
RED_PRESSED = "#8c0d26"
GREEN = "#28C840"
YELLOW = "#FEBC2E"
DOT_RED = "#FE5F57"

QSS = """
* {
    font-family: "Open Sans", "Segoe UI", sans-serif;
    font-size: 12px;
    color: %(TEXT)s;
    outline: none;
}
QMainWindow, QDialog { background-color: %(BG)s; }
QWidget { background-color: transparent; }

QFrame#Card {
    background-color: %(CARD)s;
    border-radius: 10px;
}
QFrame#Navbar {
    background-color: %(BG_DEEP)s;
    border-bottom: 1px solid %(CARD_RAISED)s;
}
QLabel#AppTitle {
    font-size: 16px;
    font-weight: 600;
    color: #FFFFFF;
}
QLabel#GameTitle {
    font-size: 20px;
    font-weight: 600;
    color: #FFFFFF;
}
QLabel#SectionTitle {
    font-size: 14px;
    font-weight: 600;
    color: #FFFFFF;
}
QLabel#Muted { color: %(TEXT_DIM)s; }
QLabel#Mono {
    font-family: "Consolas", "Courier New", monospace;
    font-size: 11px;
    color: %(TEXT_DIM)s;
}
QLabel#FieldKey { color: %(TEXT_DIM)s; }
QLabel#FieldValue { color: %(TEXT)s; }
QLabel#ErrorText { color: %(DOT_RED)s; }

QLabel#StatusDot {
    border-radius: 5px;
    min-width: 10px; max-width: 10px;
    min-height: 10px; max-height: 10px;
    background-color: %(TEXT_DIM)s;
}
QLabel#StatusDot[state="active"]   { background-color: %(GREEN)s; }
QLabel#StatusDot[state="busy"]    { background-color: %(YELLOW)s; }
QLabel#StatusDot[state="error"]   { background-color: %(DOT_RED)s; }
QLabel#StatusDot[state="inactive"]{ background-color: %(TEXT_DIM)s; }

QPushButton {
    background-color: transparent;
    border: 1px solid %(BORDER)s;
    border-radius: 5px;
    padding: 7px 16px;
    color: %(TEXT)s;
}
QPushButton:hover { background-color: %(CARD_RAISED)s; border-color: %(BORDER_HOVER)s; }
QPushButton:pressed { background-color: %(CARD)s; }
QPushButton:disabled { color: %(TEXT_DIM)s; border-color: %(CARD_RAISED)s; }

QPushButton#Primary {
    background-color: %(BLUE)s;
    border: none;
    color: #FFFFFF;
    font-size: 14px;
    font-weight: 600;
    padding: 10px 22px;
}
QPushButton#Primary:hover { background-color: %(BLUE_HOVER)s; }
QPushButton#Primary:pressed { background-color: %(BLUE_PRESSED)s; }
QPushButton#Primary:disabled { background-color: %(CARD_RAISED)s; color: %(TEXT_DIM)s; }

QPushButton#Danger {
    background-color: transparent;
    border: 1px solid %(RED)s;
    color: %(RED_HOVER)s;
}
QPushButton#Danger:hover { background-color: %(RED)s; color: #FFFFFF; }
QPushButton#Danger:pressed { background-color: %(RED_PRESSED)s; color: #FFFFFF; }
QPushButton#Danger:disabled { border-color: %(CARD_RAISED)s; color: %(TEXT_DIM)s; }

QPushButton#BigPrimary {
    background-color: %(BLUE)s;
    border: none;
    border-radius: 7px;
    color: #FFFFFF;
    font-size: 16px;
    font-weight: 600;
    padding: 14px 22px;
}
QPushButton#BigPrimary:hover { background-color: %(BLUE_HOVER)s; }
QPushButton#BigPrimary:pressed { background-color: %(BLUE_PRESSED)s; }
QPushButton#BigPrimary:disabled { background-color: %(CARD_RAISED)s; color: %(TEXT_DIM)s; }

QPushButton#NavButton {
    border: none;
    border-radius: 5px;
    padding: 6px 10px;
    color: %(TEXT_DIM)s;
}
QPushButton#NavButton:hover { background-color: %(CARD_RAISED)s; color: %(TEXT)s; }

QListWidget {
    background-color: %(BG_DEEP)s;
    border: none;
    border-radius: 7px;
    padding: 4px;
}
QListWidget::item {
    padding: 8px 10px;
    border-radius: 5px;
    color: %(TEXT)s;
}
QListWidget::item:hover { background-color: %(CARD_RAISED)s; }
QListWidget::item:selected { background-color: #323A46; color: #FFFFFF; }

QLineEdit, QComboBox, QSpinBox {
    background-color: %(CARD_RAISED)s;
    border: 1px solid %(BORDER)s;
    border-radius: 4px;
    padding: 6px 8px;
    selection-background-color: %(BLUE)s;
}
QLineEdit:focus, QComboBox:focus { border-color: %(BLUE)s; }
QComboBox::drop-down { border: none; width: 20px; }
QComboBox QAbstractItemView {
    background-color: %(CARD_RAISED)s;
    border: 1px solid %(BORDER)s;
    border-radius: 4px;
    selection-background-color: %(BLUE)s;
}

QProgressBar {
    background-color: %(CARD_RAISED)s;
    border: none;
    border-radius: 5px;
    height: 10px;
    text-align: center;
    color: transparent;
}
QProgressBar::chunk {
    background-color: %(BLUE)s;
    border-radius: 5px;
}

QCheckBox { spacing: 8px; }
QCheckBox::indicator {
    width: 16px; height: 16px;
    border-radius: 4px;
    border: 1px solid %(BORDER)s;
    background-color: %(CARD_RAISED)s;
}
QCheckBox::indicator:checked {
    background-color: %(BLUE)s;
    border-color: %(BLUE)s;
}

QScrollBar:vertical {
    background: transparent; width: 10px; margin: 2px;
}
QScrollBar::handle:vertical {
    background: %(BORDER)s; border-radius: 4px; min-height: 24px;
}
QScrollBar::handle:vertical:hover { background: %(BORDER_HOVER)s; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar:horizontal {
    background: transparent; height: 10px; margin: 2px;
}
QScrollBar::handle:horizontal {
    background: %(BORDER)s; border-radius: 4px; min-width: 24px;
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }

QToolTip {
    background-color: %(CARD_RAISED)s;
    color: %(TEXT)s;
    border: 1px solid %(BORDER)s;
    border-radius: 4px;
    padding: 4px 8px;
}

QMessageBox { background-color: %(CARD)s; }
QPlainTextEdit#Log {
    background-color: %(BG_DEEP)s;
    border: none;
    border-radius: 7px;
    color: %(TEXT_DIM)s;
    font-family: "Consolas", "Courier New", monospace;
    font-size: 11px;
    padding: 6px;
}
""" % {
    "BG": BG, "BG_DEEP": BG_DEEP, "CARD": CARD, "CARD_RAISED": CARD_RAISED,
    "BORDER": BORDER, "BORDER_HOVER": BORDER_HOVER, "TEXT": TEXT,
    "TEXT_DIM": TEXT_DIM, "BLUE": BLUE, "BLUE_HOVER": BLUE_HOVER,
    "BLUE_PRESSED": BLUE_PRESSED, "RED": RED, "RED_HOVER": RED_HOVER,
    "RED_PRESSED": RED_PRESSED, "GREEN": GREEN, "YELLOW": YELLOW,
    "DOT_RED": DOT_RED,
}
