@echo off
REM KisaYol.exe derleme betigi (Windows). Gereksinim: Python 3.9+
py -m pip install -r requirements.txt pyinstaller
py -m PyInstaller --noconfirm --clean --onefile --windowed ^
  --name KisaYol ^
  --icon assets\icon.ico ^
  --add-data "assets;assets" ^
  --collect-data customtkinter ^
  --hidden-import pystray._win32 ^
  KisaYol.pyw
echo.
echo Hazir: dist\KisaYol.exe
pause
