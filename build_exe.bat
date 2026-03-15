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
echo Tum bagimliliklar yukleniyor (requirements.txt)...
pip install -r requirements.txt

echo.
echo EXE dosyasi olusturuluyor...
echo Bu islem birkaç dakika surebilir...
echo.

REM Tek dosya EXE olustur
pyinstaller --onefile --noconsole --name OsmanliEyaletSimulasyonu ^
    --add-data "audio/sounds;audio/sounds" ^
    --collect-all pygame ^
    --collect-all accessible_output2 ^
    --collect-all requests ^
    --hidden-import accessible_output2.outputs.auto ^
    --hidden-import accessible_output2.outputs.nvda ^
    --hidden-import accessible_output2.outputs.sapi5 ^
    --hidden-import requests ^
    --hidden-import urllib3 ^
    --hidden-import charset_normalizer ^
    --hidden-import certifi ^
    --hidden-import idna ^
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
