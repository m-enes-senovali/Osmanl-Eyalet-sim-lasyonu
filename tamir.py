import os

# GitHub'in sevdigi basit ve garantili format
# Satir sonlari Unix uyumlu (\n) olacak
yaml_icerigi = """name: MacDerleme
on: [push]

jobs:
  build:
    runs-on: macos-latest
    steps:
      - uses: actions/checkout@v3

      - name: Python Yukle
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Yuklemeler
        run: |
          pip install pyinstaller
          if [ -f requirements.txt ]; then pip install -r requirements.txt; fi

      - name: Derleme Basliyor
        run: pyinstaller --onefile --windowed main.py

      - name: Sonucu Kaydet
        uses: actions/upload-artifact@v3
        with:
          name: MacUygulamasi
          path: dist/
"""

# Dosya yolu
klasor = os.path.join(".github", "workflows")
dosya = os.path.join(klasor, "mac_build.yml")

# Klasor yoksa olustur
os.makedirs(klasor, exist_ok=True)

# Varsa eski dosyayi sil (temiz baslangic icin)
if os.path.exists(dosya):
    os.remove(dosya)

# Dosyayi 'binary' modunda yazarak Windows'un satir sonlarini bozmasini engelliyoruz
with open(dosya, "wb") as f:
    f.write(yaml_icerigi.encode('utf-8'))

print("Dosya Unix formatinda tertemiz sekilde yeniden olusturuldu.")