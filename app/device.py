import os
import traceback

from PySide6.QtCore import QObject, QThread, Signal


class Worker(QThread):
    progress = Signal(dict)
    finished_ok = Signal(object)
    failed = Signal(str)

    def __init__(self, fn, parent=None):
        super().__init__(parent)
        self._fn = fn

    def run(self):
        try:
            result = self._fn(self.progress.emit)
            self.finished_ok.emit(result)
        except Exception:
            self.failed.emit(traceback.format_exc())


class Device(QObject):
    """Thin session wrapper around FlashGBX's GBxCart RW driver."""

    stateChanged = Signal(str)          # "disconnected" | "connecting" | "connected"
    progressUpdate = Signal(str, int, int)
    actionFinished = Signal(str, object)  # action name, payload
    actionFailed = Signal(str, str)

    def __init__(self, settings):
        super().__init__()
        self.settings = settings
        self.dev = None
        self.mode = None
        self.header = None
        self.worker = None
        self._flashcarts = None
        self._busy_action = None

    # ---------- FlashGBX bootstrap ----------

    def _bootstrap(self):
        if self._flashcarts is not None:
            return self._flashcarts
        import argparse
        import FlashGBX
        from FlashGBX.app import AppContext
        from FlashGBX.FlashGBX import LoadConfig
        from . import config as gcfg

        pkg = os.path.dirname(FlashGBX.__file__)
        cfg = gcfg.config_dir()
        AppContext.APP_PATH = pkg
        AppContext.CONFIG_PATH = cfg
        args = {"app_path": pkg, "config_path": cfg,
                "argparsed": argparse.Namespace(reset=False)}
        loaded = LoadConfig(args)
        self._flashcarts = loaded["flashcarts"]
        return self._flashcarts

    # ---------- actions ----------

    @property
    def busy(self):
        return self.worker is not None and self.worker.isRunning()

    def _start(self, action, fn):
        if self.busy:
            self.actionFailed.emit(action, "Another operation is already running.")
            return
        self._busy_action = action
        self.worker = Worker(fn)
        self.worker.progress.connect(self._on_progress)
        self.worker.finished_ok.connect(lambda r: self._on_done(r))
        self.worker.failed.connect(lambda tb: self._on_fail(tb))
        self.worker.start()

    def _on_progress(self, p):
        action = p.get("action", "")
        if action == "UPDATE_INFO":
            self.progressUpdate.emit(str(p.get("text", "")), 0, 0)
        elif action in ("UPDATE_POS", "READ"):
            info = self.dev.INFO if self.dev else {}
            total = int(info.get("total_size") or 0)
            cur = int(info.get("transferred") or 0)
            self.progressUpdate.emit("", cur, total)
        elif action == "ABORT":
            self.progressUpdate.emit(str(p.get("info_msg", "Aborted")), 0, 0)

    def _on_done(self, result):
        action, self._busy_action = self._busy_action, None
        self.actionFinished.emit(action, result)

    def _on_fail(self, tb):
        action, self._busy_action = self._busy_action, None
        self.actionFailed.emit(action, tb)

    def cancel(self):
        if self.dev is not None and self.busy:
            self.dev.CANCEL = True

    # ---------- connect / header ----------

    def connect_device(self):
        self.stateChanged.emit("connecting")

        def fn(progress):
            from FlashGBX import hw_GBxCartRW
            flashcarts = self._bootstrap()
            dev = hw_GBxCartRW.GbxDevice()
            ret = dev.Initialize(flashcarts, port=self.settings.data.get("port"),
                                 max_baud=int(self.settings.data.get("max_baud") or 1500000))
            if not ret:
                raise RuntimeError(
                    "No GBxCart device found. Check the USB connection and that no other "
                    "software (FlashGBX, GBxCart Firmware Updater) is using the device.")
            self.dev = dev
            want = (self.settings.data.get("mode") or "auto").upper()
            modes = ["DMG", "AGB"] if want == "AUTO" else [want]
            header, mode = None, None
            for m in modes:
                dev.SetMode(m)
                try:
                    h = dev.ReadHeader()
                except Exception:
                    continue
                if h and h.get("logo_correct"):
                    header, mode = h, m
                    break
                if header is None:
                    header, mode = h, m
            self.mode, self.header = mode, header
            return {
                "ok": True,
                "mode": mode,
                "header": header,
                "device": dev.GetFullName() if hasattr(dev, "GetFullName") else "GBxCart RW",
                "firmware": dev.GetFirmwareVersion() if hasattr(dev, "GetFirmwareVersion") else "",
            }

        self._start("connect", fn)

    def disconnect_device(self):
        if self.dev is not None:
            try:
                self.dev.Close(cartPowerOff=True)
            except Exception:
                pass
        self.dev = None
        self.mode = None
        self.header = None
        self.stateChanged.emit("disconnected")

    def reread_header(self):
        def fn(progress):
            if self.dev is None:
                raise RuntimeError("Device not connected.")
            self.header = self.dev.ReadHeader()
            return {"mode": self.mode, "header": self.header}
        self._start("header", fn)

    # ---------- transfer helpers ----------

    def _require(self):
        if self.dev is None or self.header is None:
            raise RuntimeError("Device not connected or cartridge header not read.")
        return self.dev, self.mode, self.header

    def _rom_args(self):
        from FlashGBX.CartridgeTypes import RomSizes
        dev, mode, header = self._require()
        if mode == "DMG":
            mbc = header.get("mapper_raw") or 0x19
            try:
                rom_size = RomSizes().GetSize(header["rom_size_raw"])
            except Exception:
                rom_size = 8 * 1024 * 1024
        else:
            mbc = 1
            rom_size = header.get("rom_size") or 32 * 1024 * 1024
        return {"mode": 1, "mbc": mbc, "rom_size": rom_size, "agb_rom_size": rom_size,
                "start_addr": 0, "fast_read_mode": True, "cart_type": 0}

    def _save_type(self):
        dev, mode, header = self._require()
        if mode == "DMG":
            mapper = header.get("mapper_raw")
            title = header.get("game_title", "")
            if mapper == 0x06:
                return 0x100
            if mapper == 0x22 and title in ("KORO2 KIRBY", "KIRBY TNT"):
                return 0x101
            if mapper == 0x22 and title == "CMASTER":
                return 0x102
            if mapper == 0xFD:
                return 0x103
            if mapper == 0x20:
                return 0x104
            st = header.get("ram_size_raw", 0)
            if st == 0x205:
                raise RuntimeError("Batteryless SRAM cartridges are not supported by gblame yet.")
            return st
        st = header.get("save_type")
        if not st:
            raise RuntimeError("Could not determine the GBA save type from the header.")
        if st == 9:
            raise RuntimeError("Batteryless SRAM cartridges are not supported by gblame yet.")
        return st

    def dump_rom(self, path):
        def fn(progress):
            args = self._rom_args()
            args["path"] = path
            ret = self.dev.TransferData(args=args, signal=progress)
            if not ret or self.dev.ERROR:
                raise RuntimeError("ROM dump failed or was aborted.")
            info = dict(self.dev.INFO)
            return {"path": path, "info": info}
        self._start("dump_rom", fn)

    def dump_save(self, path):
        def fn(progress):
            dev, mode, header = self._require()
            save_type = self._save_type()
            if save_type in (0, None):
                return {"path": path, "skipped": "no save hardware detected"}
            args = {"mode": 2, "path": path,
                    "mbc": header.get("mapper_raw") or 0x19 if mode == "DMG" else 1,
                    "save_type": save_type, "rtc": False}
            ret = dev.TransferData(args=args, signal=progress)
            if not ret or dev.ERROR:
                raise RuntimeError("Save dump failed or was aborted.")
            return {"path": path, "info": dict(dev.INFO)}
        self._start("dump_save", fn)

    def write_save(self, path):
        """Explicit user-initiated write of a PC save file back to the cartridge."""
        def fn(progress):
            dev, mode, header = self._require()
            save_type = self._save_type()
            args = {"mode": 3, "path": path,
                    "mbc": header.get("mapper_raw") or 0x19 if mode == "DMG" else 1,
                    "save_type": save_type, "erase": True, "rtc": False, "cart_type": 0}
            ret = dev.TransferData(args=args, signal=progress)
            if not ret or dev.ERROR:
                raise RuntimeError("Save write failed or was aborted.")
            return {"path": path, "info": dict(dev.INFO)}
        self._start("write_save", fn)

    # ---------- display helpers ----------

    def header_display(self):
        dev, mode, header = self._require()
        rows = []
        title = header.get("game_title") or "(unknown)"
        rows.append(("Title", title))
        if header.get("game_code"):
            rows.append(("Game code", str(header["game_code"])))
        rows.append(("Revision", str(header.get("version", "?"))))
        rows.append(("Platform", "Game Boy / Color" if mode == "DMG" else "Game Boy Advance"))
        if mode == "DMG":
            try:
                from FlashGBX.Mapper import DMG_Mapper
                rows.append(("Mapper", DMG_Mapper().GetMapperName(header.get("mapper_raw", 0))))
            except Exception:
                rows.append(("Mapper", "0x{:02X}".format(header.get("mapper_raw", 0))))
            try:
                from FlashGBX.CartridgeTypes import RomSizes
                rows.append(("ROM size", RomSizes().GetString(index=header["rom_size_raw"])))
            except Exception:
                pass
            try:
                from FlashGBX.CartridgeTypes import DmgSaveTypes
                rows.append(("Save type", DmgSaveTypes(mbc=header.get("ram_size_raw", 0)).GetString()))
            except Exception:
                pass
        else:
            size = header.get("rom_size")
            if size:
                rows.append(("ROM size", "{:.1f} MiB".format(size / 1048576)))
            try:
                from FlashGBX.CartridgeTypes import AgbSaveTypes
                st = header.get("save_type")
                if st:
                    rows.append(("Save type", AgbSaveTypes(index=st).GetString()))
            except Exception:
                pass
        if header.get("rtc_string"):
            rows.append(("RTC", str(header["rtc_string"])))
        db = header.get("db")
        if db and db.get("gn"):
            rows.append(("Database name", str(db["gn"])))
        rows.append(("Header", "OK" if header.get("logo_correct") else "INVALID"))
        return rows

    def suggested_filename(self):
        from FlashGBX.app import generate_filename
        dev, mode, header = self._require()
        try:
            name = generate_filename(mode=mode, header=dev.INFO, settings=None)
        except Exception:
            ext = "gba" if mode == "AGB" else "gb"
            name = (header.get("game_title") or "ROM").strip().replace("/", "_") + "." + ext
        return name
