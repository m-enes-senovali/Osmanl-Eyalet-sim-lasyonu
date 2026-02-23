@echo off
set "mesaj="

echo Lutfen bu guncellemede ne degistirdigini yaz.
echo Eger bos birakip Enter tusuna basarsan, Otomatik Hizli Kayit olarak islenecektir.
echo.
set /p mesaj="Degisiklik notun: "

if not defined mesaj set mesaj=Otomatik Hizli Kayit

echo.
echo Dosyalar paketleniyor (Add)...
git add .

echo.
echo Tarihceye su notla isleniyor (Commit): %mesaj%
git commit -m "%mesaj%"

echo.
echo Uzak sunucuya gonderiliyor (Push)...
git push

echo.
echo ISLEM KUSURSUZ TAMAMLANDI! 
echo Cikmak icin Enter tusuna basabilirsin.
pause >nul