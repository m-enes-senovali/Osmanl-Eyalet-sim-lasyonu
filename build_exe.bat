@echo off
echo ========================================
echo  Osmanli Eyalet Simulasyonu - EXE Olusturucu
echo ========================================
echo.

REM PyInstaller kontrolu
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo PyInstaller yukleniyor...
    pip install pyinstaller
)

echo.
echo EXE dosyasi olusturuluyor...
echo Bu islem birkaç dakika surebilir...
echo.

REM Tek dosya EXE olustur
pyinstaller --onefile --noconsole --name OsmanliEyaletSimulasyonu ^
    --add-data "audio/sounds;audio/sounds" ^
    --add-data "config.py;." ^
    --hidden-import pygame ^
    --hidden-import pygame.mixer ^
    --hidden-import accessible_output2 ^
    --hidden-import accessible_output2.outputs.auto ^
    main.py

echo.
echo ========================================
if exist "dist\OsmanliEyaletSimulasyonu.exe" (
    echo BASARILI! EXE dosyasi olusturuldu:
    echo dist\OsmanliEyaletSimulasyonu.exe
    echo.
    echo Dagitim icin 'dist' klasorunu kullanin.
) else (
    echo HATA! EXE dosyasi olusturulamadi.
    echo Hata mesajlarini kontrol edin.
)
echo ========================================
pause
