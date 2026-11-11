@echo off
REM Build gblame.exe with PyInstaller (FlashGBX + mGBA are vendored under vendor\)
cd /d "%~dp0"

python -m pip install --upgrade pyinstaller
python -m PyInstaller --noconfirm --onefile --windowed ^
    --name gblame ^
    --paths vendor ^
    --collect-all FlashGBX ^
    --collect-submodules FlashGBX ^
    --add-data "vendor\mgba;vendor/mgba" ^
    --add-data "assets;assets" ^
    gblame.py

echo.
echo Done: dist\gblame.exe
pause
