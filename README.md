# gblame

A friendly Game Boy / Game Boy Color / Game Boy Advance cartridge manager for
the **GBxCart RW**, with everything integrated in-tree: FlashGBX for cartridge
access and mGBA for instant playback of your dumps — no separate packages to
install.

The UI is inspired by the clean, card-based layout of modern handheld-companion
apps: one thing at a time, big buttons, no walls of settings.

## Features

- **One-click device detection** — plug in the GBxCart RW, pick the cartridge
  slot, and gblame reads the header for you.
- **Dump ROM** — backs up the cartridge to a `.gb` / `.gbc` / `.gba` file, with
  an automatic No-Intro style filename when the ROM is recognized.
- **Dump save** — copies the save RAM off the cartridge.
- **Write save** — pick any save file (`.sav`, `.srm`, `.flash`, `.dat`) from
  your PC and write it back to the cartridge, only via an explicit button and a
  file selector. The cartridge save is never modified implicitly.
- **Instant playback** — play your dumped ROMs right away with the bundled
  mGBA emulator (v0.10.5, MPL-2.0). Using your own mGBA executable is optional
  (Settings → mGBA executable); the bundled one is the default.
- **Library view** — remember where your dumps live and re-open them quickly.
- **Hidden debug mode** — press `Ctrl+Shift+D` (or click the "gblame" title 5
  times) to reveal a **Debug ROM...** button that loads a ROM file you already
  own directly into the emulator, no cartridge required.

## Requirements

- Windows 10/11 (Linux/macOS should work but are untested)
- Python 3.9+
- A GBxCart RW (v4 or v5 recommended; mini/Pro also supported)

## Install & run from source

```
pip install -r requirements.txt
python gblame.py
```

FlashGBX and mGBA do **not** need to be installed — full copies live in
`vendor/FlashGBX` and `vendor/mgba` and are picked up automatically.

## Build a standalone EXE

```
build.bat
```

This uses PyInstaller to produce `dist/gblame.exe`.

## Project layout

```
gblame/
├── gblame.py             # entry point (also wires up vendor/ import path)
├── app/
│   ├── config.py         # settings + paths
│   ├── device.py         # FlashGBX session wrapper (detect/dump/write, QThread)
│   ├── emulator.py       # local playback of dumped ROMs
│   ├── library.py        # remembers dumped ROMs
│   └── ui/
│       ├── main_window.py
│       └── styles.py     # QSS theme
├── assets/fonts/         # Open Sans (Apache 2.0)
├── vendor/FlashGBX/      # FlashGBX v5.2.1 source, GPL-3.0 (license included)
├── vendor/mgba/          # mGBA v0.10.5 Windows build, MPL-2.0 (licenses included)
├── requirements.txt
├── build.bat
└── README.md
```

## License

FlashGBX is licensed GPL-3.0 (see `vendor/FlashGBX/LICENSE`) and mGBA is
licensed MPL-2.0 (see `vendor/mgba/LICENSE.txt`); this project inherits the
GPL-3.0 terms.
