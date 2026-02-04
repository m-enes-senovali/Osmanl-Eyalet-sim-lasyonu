# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec dosyası - Osmanlı Eyalet Yönetim Simülasyonu

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('audio/sounds', 'audio/sounds'),  # Ses dosyaları
        ('saves', 'saves'),  # Kayıt klasörü (boş olabilir)
        ('config.py', '.'),  # Ayar dosyası
    ],
    hiddenimports=[
        'pygame',
        'pygame.mixer',
        'pygame.font',
        'accessible_output2',
        'accessible_output2.outputs',
        'accessible_output2.outputs.auto',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='OsmanliEyaletSimulasyonu',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Konsol penceresi gösterme
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # İkon eklemek isterseniz: icon='icon.ico'
)
