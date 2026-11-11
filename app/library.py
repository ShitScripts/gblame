import json
import os
import re
import shutil
import time


def sanitize(name):
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", name).strip().rstrip(".")
    return name or "ROM"


class Game:
    """One dumped cartridge in the working library folder.

    Layout per game:
      rom.<ext>        ROM dump (refreshed from cart on demand)
      rom.sav          emulator save (mGBA writes here; seeded from cart.sav)
      cart.sav         pristine dump of the cart's save (never written back automatically)
      meta.json        header info + timestamps
    """

    def __init__(self, folder):
        self.folder = folder

    @property
    def name(self):
        return os.path.basename(self.folder)

    @property
    def meta_path(self):
        return os.path.join(self.folder, "meta.json")

    def load_meta(self):
        try:
            with open(self.meta_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (OSError, ValueError):
            return {}

    def save_meta(self, meta):
        with open(self.meta_path, "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2)

    @property
    def rom_target_path(self):
        meta = self.load_meta()
        rom = meta.get("rom_file") or "rom.gb"
        return os.path.join(self.folder, rom)

    @property
    def rom_path(self):
        meta = self.load_meta()
        rom = meta.get("rom_file")
        if rom:
            p = os.path.join(self.folder, rom)
            if os.path.exists(p):
                return p
        for f in os.listdir(self.folder):
            if f.lower().endswith((".gb", ".gbc", ".gba", ".sgb")):
                return os.path.join(self.folder, f)
        return None

    @property
    def emu_sav_path(self):
        rom = self.rom_path
        if rom:
            return os.path.splitext(rom)[0] + ".sav"
        return os.path.join(self.folder, "rom.sav")

    @property
    def cart_sav_path(self):
        return os.path.join(self.folder, "cart.sav")

    def seed_emu_save(self):
        """Create the emulator save from the cart dump if it does not exist yet."""
        emu, cart = self.emu_sav_path, self.cart_sav_path
        if not os.path.exists(emu) and os.path.exists(cart) and os.path.getsize(cart) > 0:
            shutil.copyfile(cart, emu)
            return True
        return False

    def has_emu_save(self):
        p = self.emu_sav_path
        return os.path.exists(p) and os.path.getsize(p) > 0


class Library:
    def __init__(self, settings):
        self.settings = settings

    @property
    def root(self):
        root = self.settings.library_dir
        os.makedirs(root, exist_ok=True)
        return root

    def game_for(self, filename, mode, header):
        base = sanitize(os.path.splitext(filename)[0])
        folder = os.path.join(self.root, base)
        os.makedirs(folder, exist_ok=True)
        game = Game(folder)
        meta = game.load_meta()
        meta.update({
            "rom_file": os.path.basename(filename),
            "mode": mode,
            "title": header.get("game_title", ""),
            "game_code": header.get("game_code", ""),
            "revision": header.get("version"),
            "last_seen": time.time(),
        })
        game.save_meta(meta)
        return game

    def list_games(self):
        games = []
        try:
            entries = os.listdir(self.root)
        except OSError:
            return games
        for entry in entries:
            folder = os.path.join(self.root, entry)
            if not os.path.isdir(folder):
                continue
            game = Game(folder)
            meta = game.load_meta()
            if not meta and not game.rom_path:
                continue
            games.append((game, meta))
        games.sort(key=lambda gm: gm[1].get("last_seen", 0), reverse=True)
        return games
