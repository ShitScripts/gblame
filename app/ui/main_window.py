import os

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QDialog, QDialogButtonBox, QFileDialog, QFormLayout,
    QFrame, QGridLayout, QHBoxLayout, QLabel, QLineEdit, QListWidget,
    QListWidgetItem, QMainWindow, QMessageBox, QPlainTextEdit, QProgressBar,
    QPushButton, QSizePolicy, QVBoxLayout, QWidget,
)

from .. import config as gcfg
from .. import emulator
from ..device import Device
from ..library import Library


def card():
    frame = QFrame()
    frame.setObjectName("Card")
    return frame


def muted(text):
    label = QLabel(text)
    label.setObjectName("Muted")
    return label


class SettingsDialog(QDialog):
    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.setWindowTitle("Settings")
        self.setMinimumWidth(480)
        layout = QVBoxLayout(self)

        form = QFormLayout()
        self.mgba_edit = QLineEdit(settings.data.get("mgba_path", ""))
        self.mgba_edit.setPlaceholderText("Bundled mGBA (default) — optional: pick your own executable")
        mgba_row = QHBoxLayout()
        mgba_row.addWidget(self.mgba_edit, 1)
        browse_mgba = QPushButton("Browse...")
        browse_mgba.clicked.connect(self._browse_mgba)
        mgba_row.addWidget(browse_mgba)
        form.addRow("mGBA executable (optional)", mgba_row)

        self.lib_edit = QLineEdit(settings.data.get("library_dir", ""))
        self.lib_edit.setPlaceholderText(gcfg.default_library_dir())
        lib_row = QHBoxLayout()
        lib_row.addWidget(self.lib_edit, 1)
        browse_lib = QPushButton("Browse...")
        browse_lib.clicked.connect(self._browse_lib)
        lib_row.addWidget(browse_lib)
        form.addRow("Library folder", lib_row)

        self.port_combo = QComboBox()
        self.port_combo.addItem("Auto", None)
        try:
            from serial.tools import list_ports
            for p in list_ports.comports():
                self.port_combo.addItem("{} - {}".format(p.device, p.description), p.device)
        except Exception:
            pass
        current = settings.data.get("port")
        idx = self.port_combo.findData(current)
        self.port_combo.setCurrentIndex(idx if idx >= 0 else 0)
        form.addRow("GBxCart port", self.port_combo)

        self.mode_combo = QComboBox()
        for label, value in (("Auto-detect", "auto"), ("Game Boy / Color (DMG)", "dmg"),
                             ("Game Boy Advance (AGB)", "agb")):
            self.mode_combo.addItem(label, value)
        idx = self.mode_combo.findData(settings.data.get("mode", "auto"))
        self.mode_combo.setCurrentIndex(idx if idx >= 0 else 0)
        form.addRow("Platform", self.mode_combo)

        layout.addLayout(form)
        layout.addWidget(muted(
            "Saves are dumped read-only from the cart. Writing a save back to the "
            "cartridge only happens when you explicitly choose it."))

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _browse_mgba(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select mGBA executable", "",
            "Executables (*.exe);;All files (*)")
        if path:
            self.mgba_edit.setText(path)

    def _browse_lib(self):
        path = QFileDialog.getExistingDirectory(self, "Select library folder")
        if path:
            self.lib_edit.setText(path)

    def _save(self):
        self.settings.set("mgba_path", self.mgba_edit.text().strip())
        self.settings.set("library_dir", self.lib_edit.text().strip())
        self.settings.set("port", self.port_combo.currentData())
        self.settings.set("mode", self.mode_combo.currentData())
        self.accept()


class MainWindow(QMainWindow):
    def __init__(self, settings):
        super().__init__()
        self.settings = settings
        self.library = Library(settings)
        self.device = Device(settings)
        self.current_game = None
        self._dump_play = False

        self.setWindowTitle("gblame")
        self.resize(1000, 660)
        self.setMinimumSize(860, 560)

        self.device.stateChanged.connect(self._on_state)
        self.device.progressUpdate.connect(self._on_progress)
        self.device.actionFinished.connect(self._on_action_finished)
        self.device.actionFailed.connect(self._on_action_failed)

        self._build_ui()
        self._refresh_library()
        self._set_status("Connect your GBxCart RW and press Connect.", "inactive")

    # ---------- UI construction ----------

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._build_navbar())

        body = QHBoxLayout()
        body.setContentsMargins(16, 16, 16, 16)
        body.setSpacing(16)
        root.addLayout(body, 1)

        body.addWidget(self._build_library_panel(), 2)
        body.addWidget(self._build_cart_panel(), 3)

        root.addWidget(self._build_status_bar())

    def _build_navbar(self):
        bar = QFrame()
        bar.setObjectName("Navbar")
        bar.setFixedHeight(52)
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(16, 0, 16, 0)

        title = QLabel("gblame")
        title.setObjectName("AppTitle")
        self._title_clicks = 0
        title.mousePressEvent = self._on_title_clicked
        layout.addWidget(title)
        layout.addWidget(muted("  GBxCart dump & play"), 0)
        layout.addStretch(1)

        self.status_dot = QLabel()
        self.status_dot.setObjectName("StatusDot")
        self.status_dot.setProperty("state", "inactive")
        layout.addWidget(self.status_dot)
        self.device_label = QLabel("Not connected")
        self.device_label.setObjectName("Muted")
        layout.addWidget(self.device_label)

        self.btn_connect = QPushButton("Connect")
        self.btn_connect.setObjectName("NavButton")
        self.btn_connect.clicked.connect(self._connect)
        layout.addWidget(self.btn_connect)

        btn_settings = QPushButton("Settings")
        btn_settings.setObjectName("NavButton")
        btn_settings.clicked.connect(self._open_settings)
        layout.addWidget(btn_settings)

        self.btn_debug = QPushButton("Debug ROM...")
        self.btn_debug.setObjectName("NavButton")
        self.btn_debug.setToolTip("Load a ROM file you own directly into the emulator")
        self.btn_debug.clicked.connect(self._debug_load_rom)
        self.btn_debug.setVisible(False)
        layout.addWidget(self.btn_debug)

        QShortcut(QKeySequence("Ctrl+Shift+D"), self, activated=self._toggle_debug)
        return bar

    def _build_library_panel(self):
        panel = card()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        header = QHBoxLayout()
        section = QLabel("Library")
        section.setObjectName("SectionTitle")
        header.addWidget(section)
        header.addStretch(1)
        btn_open = QPushButton("Open folder")
        btn_open.setObjectName("NavButton")
        btn_open.clicked.connect(self._open_library_folder)
        header.addWidget(btn_open)
        layout.addLayout(header)

        self.game_list = QListWidget()
        self.game_list.itemDoubleClicked.connect(lambda _: self._play_selected())
        layout.addWidget(self.game_list, 1)

        row = QHBoxLayout()
        self.btn_play = QPushButton("Play")
        self.btn_play.clicked.connect(self._play_selected)
        self.btn_play.setEnabled(False)
        row.addWidget(self.btn_play)
        self.btn_refresh_dump = QPushButton("Re-dump from cart")
        self.btn_refresh_dump.clicked.connect(self._redump_selected)
        self.btn_refresh_dump.setEnabled(False)
        row.addWidget(self.btn_refresh_dump)
        layout.addLayout(row)
        layout.addWidget(muted("Double-click a game to launch it. ROMs and saves live in the temp library folder."))
        return panel

    def _build_cart_panel(self):
        panel = card()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        self.cart_title = QLabel("No cartridge")
        self.cart_title.setObjectName("GameTitle")
        layout.addWidget(self.cart_title)

        self.cart_grid_host = QGridLayout()
        self.cart_grid_host.setHorizontalSpacing(18)
        self.cart_grid_host.setVerticalSpacing(6)
        layout.addLayout(self.cart_grid_host)

        layout.addSpacing(6)

        self.btn_dump_play = QPushButton("Dump && Play")
        self.btn_dump_play.setObjectName("BigPrimary")
        self.btn_dump_play.setEnabled(False)
        self.btn_dump_play.clicked.connect(self._dump_and_play)
        layout.addWidget(self.btn_dump_play)

        row = QHBoxLayout()
        self.btn_dump_rom = QPushButton("Dump ROM")
        self.btn_dump_rom.setEnabled(False)
        self.btn_dump_rom.clicked.connect(lambda: self._dump(rom=True, save=False))
        row.addWidget(self.btn_dump_rom)
        self.btn_dump_save = QPushButton("Dump save")
        self.btn_dump_save.setEnabled(False)
        self.btn_dump_save.clicked.connect(lambda: self._dump(rom=False, save=True))
        row.addWidget(self.btn_dump_save)
        layout.addLayout(row)

        self.btn_write_save = QPushButton("Write emulator save to cart...")
        self.btn_write_save.setObjectName("Danger")
        self.btn_write_save.setEnabled(False)
        self.btn_write_save.clicked.connect(self._write_save)
        layout.addWidget(self.btn_write_save)

        layout.addStretch(1)

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setVisible(False)
        layout.addWidget(self.progress)
        self.progress_text = QLabel("")
        self.progress_text.setObjectName("Muted")
        self.progress_text.setWordWrap(True)
        layout.addWidget(self.progress_text)
        return panel

    def _build_status_bar(self):
        bar = QFrame()
        bar.setObjectName("Navbar")
        bar.setFixedHeight(36)
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(16, 0, 16, 0)
        self.status_label = QLabel("")
        self.status_label.setObjectName("Muted")
        layout.addWidget(self.status_label, 1)
        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.setObjectName("NavButton")
        self.btn_cancel.setVisible(False)
        self.btn_cancel.clicked.connect(self.device.cancel)
        layout.addWidget(self.btn_cancel)
        return bar

    # ---------- status helpers ----------

    def _set_status(self, text, state="inactive"):
        self.status_label.setText(text)
        self.status_dot.setProperty("state", state)
        self.status_dot.style().unpolish(self.status_dot)
        self.status_dot.style().polish(self.status_dot)

    def _log(self, text):
        self.progress_text.setText(text)

    def _set_busy(self, busy):
        self.btn_connect.setEnabled(not busy)
        self.progress.setVisible(busy)
        self.btn_cancel.setVisible(busy)
        if busy:
            self.progress.setRange(0, 0)
        else:
            self.progress.setRange(0, 100)
            self.progress.setValue(0)
        self._update_action_buttons()

    # ---------- device flow ----------

    def _connect(self):
        if self.device.busy:
            return
        self._set_busy(True)
        self._set_status("Connecting to GBxCart...", "busy")
        self.device.connect_device()

    def _on_state(self, state):
        if state == "disconnected":
            self.device_label.setText("Not connected")
            self.cart_title.setText("No cartridge")
            self._clear_cart_grid()
            self._set_status("Device disconnected.", "inactive")
            self._update_action_buttons()

    def _on_progress(self, text, cur, total):
        if text:
            self._log(text)
        if total > 0:
            self.progress.setRange(0, 100)
            self.progress.setValue(min(100, int(cur * 100 / total)))
            mb = 1048576
            self._log("{:.1f} / {:.1f} MiB".format(cur / mb, total / mb))

    def _on_action_finished(self, action, result):
        self._set_busy(False)
        if action == "connect":
            self.device_label.setText(str(result.get("device", "GBxCart RW")))
            fw = result.get("firmware")
            suffix = " (fw {})".format(fw) if fw else ""
            self._set_status("Connected" + suffix, "active")
            self._show_header()
        elif action == "header":
            self._show_header()
        elif action == "dump_rom":
            self._set_status("ROM dumped.", "active")
            self._after_dump_step(result.get("path"))
        elif action == "dump_save":
            skipped = isinstance(result, dict) and result.get("skipped")
            self._set_status("Save skipped ({})".format(skipped) if skipped else "Save dumped.", "active")
            self._after_dump_step(result.get("path") if not skipped else None)
        elif action == "write_save":
            self._set_status("Save written to cartridge.", "active")
            QMessageBox.information(self, "gblame", "The save was written to the cartridge.")
        self._update_action_buttons()

    def _on_action_failed(self, action, tb):
        self._set_busy(False)
        msg = tb.strip().splitlines()[-1] if tb.strip() else "Unknown error"
        self._set_status("Error: " + msg, "error")
        if action == "connect":
            self._set_status(msg, "error")
        QMessageBox.critical(self, "gblame", msg)
        if self._dump_play:
            self._dump_play = False
        self._update_action_buttons()

    def _show_header(self):
        try:
            rows = self.device.header_display()
        except RuntimeError:
            return
        header = self.device.header or {}
        title = header.get("game_title") or "(unknown title)"
        db = header.get("db")
        if db and db.get("gn"):
            title = str(db["gn"])
        self.cart_title.setText(title)
        self._clear_cart_grid()
        for i, (key, value) in enumerate(rows):
            k = QLabel(key)
            k.setObjectName("FieldKey")
            v = QLabel(str(value))
            v.setObjectName("ErrorText" if (key == "Header" and value != "OK") else "FieldValue")
            v.setTextInteractionFlags(Qt.TextSelectableByMouse)
            self.cart_grid_host.addWidget(k, i, 0)
            self.cart_grid_host.addWidget(v, i, 1)
        self._update_action_buttons()

    def _clear_cart_grid(self):
        while self.cart_grid_host.count():
            item = self.cart_grid_host.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

    def _update_action_buttons(self):
        connected = self.device.dev is not None and self.device.header is not None
        busy = self.device.busy
        ok = connected and not busy
        self.btn_dump_play.setEnabled(ok)
        self.btn_dump_rom.setEnabled(ok)
        self.btn_dump_save.setEnabled(ok)
        have_game = self.current_game is not None and not busy
        self.btn_write_save.setEnabled(bool(have_game and self.current_game.has_emu_save()))
        self.btn_play.setEnabled(bool(have_game and self.current_game.rom_path))
        self.btn_refresh_dump.setEnabled(bool(have_game and connected))
        if not connected:
            self.cart_title.setText("No cartridge" if self.device.dev is None else "Reading...")

    # ---------- dump / play ----------

    def _game_for_current_cart(self):
        filename = self.device.suggested_filename()
        return self.library.game_for(filename, self.device.mode, self.device.header)

    def _dump_and_play(self):
        self._dump_play = True
        self._dump(rom=True, save=True)

    def _dump(self, rom, save):
        if self.device.busy:
            return
        try:
            game = self._game_for_current_cart()
        except RuntimeError as e:
            QMessageBox.critical(self, "gblame", str(e))
            return
        self.current_game = game
        self._dump_queue = ([("dump_rom", game.rom_target_path)] if rom else []) + \
                           ([("dump_save", game.cart_sav_path)] if save else [])
        self._set_busy(True)
        self._set_status("Dumping cartridge...", "busy")
        self._next_dump_step()

    def _next_dump_step(self):
        if not self._dump_queue:
            self._dump_finished()
            return
        kind, path = self._dump_queue.pop(0)
        self._log("Working: {} -> {}".format(kind, path))
        if kind == "dump_rom":
            self.device.dump_rom(path)
        else:
            self.device.dump_save(path)

    def _after_dump_step(self, path):
        QTimer.singleShot(0, self._next_dump_step)

    def _dump_finished(self):
        self._set_busy(False)
        game = self.current_game
        if game is None:
            return
        game.save_meta({**game.load_meta()})
        self._refresh_library(select=game.folder)
        if self._dump_play:
            self._dump_play = False
            game.seed_emu_save()
            self._launch(game)
        else:
            self._set_status("Dump complete: " + game.folder, "active")
        self._update_action_buttons()

    def _launch(self, game):
        rom = game.rom_path
        if not rom:
            self._set_status("No ROM file in " + game.folder, "error")
            return
        game.seed_emu_save()
        ok, msg = emulator.launch(rom, self.settings)
        self._set_status(msg, "active" if ok else "error")
        if not ok:
            box = QMessageBox(self)
            box.setIcon(QMessageBox.Warning)
            box.setWindowTitle("gblame")
            box.setText(msg)
            browse = box.addButton("Find mGBA...", QMessageBox.AcceptRole)
            box.addButton(QMessageBox.Close)
            box.exec()
            if box.clickedButton() is browse:
                path, _ = QFileDialog.getOpenFileName(
                    self, "Select mGBA executable", "", "Executables (*.exe)")
                if path:
                    self.settings.set("mgba_path", path)
                    ok, msg = emulator.launch(rom, self.settings)
                    self._set_status(msg, "active" if ok else "error")

    def _play_selected(self):
        game = self._selected_game()
        if game:
            self.current_game = game
            self._launch(game)
            self._update_action_buttons()

    def _redump_selected(self):
        if self.device.busy or self.device.dev is None:
            QMessageBox.information(self, "gblame", "Connect the GBxCart with the cartridge inserted first.")
            return
        self._dump(rom=True, save=True)

    def _write_save(self):
        game = self.current_game or self._selected_game()
        if game is None or not game.has_emu_save():
            return
        answer = QMessageBox.warning(
            self, "Write save to cartridge",
            "This OVERWRITES the save data on the cartridge with your emulator "
            "save:\n\n{}\n\nThe cart's current save was backed up to cart.sav "
            "when it was dumped. Continue?".format(game.emu_sav_path),
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if answer != QMessageBox.Yes:
            return
        self._set_busy(True)
        self._set_status("Writing save to cartridge...", "busy")
        self.device.write_save(game.emu_sav_path)

    # ---------- library panel ----------

    def _refresh_library(self, select=None):
        self.game_list.clear()
        for game, meta in self.library.list_games():
            title = meta.get("title") or game.name
            mode = meta.get("mode") or ""
            item = QListWidgetItem("{}\n{}".format(game.name, mode))
            item.setToolTip(title)
            item.setData(Qt.UserRole, game.folder)
            self.game_list.addItem(item)
            if select and game.folder == select:
                self.game_list.setCurrentItem(item)
        self._update_action_buttons()

    def _selected_game(self):
        item = self.game_list.currentItem()
        if not item:
            return None
        from ..library import Game
        return Game(item.data(Qt.UserRole))

    def _open_library_folder(self):
        try:
            os.startfile(self.library.root)
        except OSError:
            pass

    def _open_settings(self):
        dialog = SettingsDialog(self.settings, self)
        if dialog.exec():
            self._set_status("Settings saved. Reconnect to apply port/platform changes.", "active")

    # ---------- hidden debug mode ----------

    def _on_title_clicked(self, event):
        self._title_clicks += 1
        if self._title_clicks >= 5:
            self._title_clicks = 0
            self._toggle_debug()
        QTimer.singleShot(3000, self._reset_title_clicks)

    def _reset_title_clicks(self):
        self._title_clicks = 0

    def _toggle_debug(self):
        enabled = not self.btn_debug.isVisible()
        self.btn_debug.setVisible(enabled)
        if enabled:
            self._set_status("Debug mode on — load ROM files you own with 'Debug ROM...'.", "active")
        else:
            self._set_status("Debug mode off.", "inactive")

    def _debug_load_rom(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Load a ROM you own",
            self.library.root,
            "Game Boy ROMs (*.gb *.gbc *.gba *.sgb *.dmg);;All files (*)")
        if not path:
            return
        ok, msg = emulator.launch(path, self.settings)
        self._set_status(msg, "active" if ok else "error")
        if not ok:
            QMessageBox.warning(self, "gblame", msg)

    def closeEvent(self, event):
        self.device.disconnect_device()
        super().closeEvent(event)
