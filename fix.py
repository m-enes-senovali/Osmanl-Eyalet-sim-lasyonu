import os

# GitHub'in hatasiz okuyacagi temiz YAML icerigi
yaml_icerigi = """name: Mac Build
on: [push, workflow_dispatch]

jobs:
  build:
    runs-on: macos-latest
    steps:
      - name: Kodlari Cek
        uses: actions/checkout@v3

      - name: Python Kur
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Yuklemeler
        run: |
          pip install pyinstaller
          if [ -f requirements.txt ]; then pip install -r requirements.txt; fi

      - name: Derleme
        run: pyinstaller --onefile --windowed main.py

      - name: Kaydetme
        uses: actions/upload-artifact@v3
        with:
          name: macos-app
          path: dist/
"""

# Klasor yollarini garantile
klasor_yolu = os.path.join(".github", "workflows")
os.makedirs(klasor_yolu, exist_ok=True)

# Dosyayi temiz bir sekilde yaz
dosya_yolu = os.path.join(klasor_yolu, "mac_build.yml")
with open(dosya_yolu, "w", encoding="utf-8") as f:
    f.write(yaml_icerigi)

print("Basarili! mac_build.yml dosyasi sifirdan ve hatasiz olarak olusturuldu.")