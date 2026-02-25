# -*- coding: utf-8 -*-
"""
Osmanlı Eyalet Yönetim Simülasyonu - Yapılandırma
"""

# Ekran Ayarları
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
FPS = 60

# Sürüm Bilgisi (Güncelleme Sistemi için)
VERSION = "1.1.0"
GITHUB_REPO = "m-enes-senovali/Osmanl-Eyalet-sim-lasyonu"

GAME_TITLE = "Osmanlı Eyalet Yönetimi"

# Renk Paleti (Osmanlı Motifleri)
COLORS = {
    'background': (30, 25, 35),          # Koyu mor-siyah
    'panel_bg': (45, 40, 55),            # Panel arka planı
    'panel_border': (120, 90, 60),       # Altın kahve
    'primary': (139, 69, 19),            # Bordo-kahve
    'secondary': (70, 50, 80),           # Mor
    'gold': (218, 165, 32),              # Altın
    'text': (245, 240, 230),             # Krem beyaz
    'text_dark': (60, 50, 45),           # Koyu metin
    'text_dim': (150, 145, 140),         # Soluk metin
    'success': (34, 139, 34),            # Yeşil
    'danger': (178, 34, 34),             # Kırmızı
    'warning': (218, 165, 32),           # Altın sarı
    'button_normal': (80, 60, 90),       # Normal buton
    'button_hover': (100, 75, 110),      # Hover buton
    'button_pressed': (60, 45, 70),      # Basılı buton
    'button_disabled': (50, 45, 55),     # Devre dışı buton
    'highlight': (255, 215, 0),          # Vurgulama
}

# Ses Ayarları
AUDIO = {
    'music_volume': 0.5,
    'sfx_volume': 0.7,
    'ui_volume': 0.6,
}

# Oyun Ayarları
GAME = {
    'starting_gold': 5000,
    'starting_food': 3000,
    'starting_wood': 2000,
    'starting_iron': 1000,
    'starting_population': 10000,
    'starting_happiness': 70,
    'starting_loyalty': 80,
    'tax_rate_default': 0.15,
    'turn_year_start': 1520,
}

# Klavye Kısayolları
KEYBINDS = {
    'next_turn': 'space',
    'economy': 'e',
    'military': 'm',
    'construction': 'c',
    'diplomacy': 'd',
    'population': 'p',
    'save_game': 'f5',
    'load_game': 'f9',
    'main_menu': 'escape',
    'help': 'f1',
    'navigate_up': 'up',
    'navigate_down': 'down',
    'navigate_left': 'left',
    'navigate_right': 'right',
    'select': 'return',
    'back': 'backspace',
}

# Erişilebilirlik Ayarları
ACCESSIBILITY = {
    'screen_reader_enabled': True,
    'announce_hover': True,
    'announce_focus_change': True,
    'high_contrast_mode': False,
    'large_text_mode': False,
    'keyboard_navigation': True,
}

# Font Boyutları
FONTS = {
    'title': 48,
    'header': 32,
    'subheader': 24,
    'body': 18,
    'small': 14,
    'tooltip': 16,
}

# ── Türkçe Karakter Destekli Font Yardımcısı ──
# pygame.font.Font(None, size) Türkçe ğ, ş, ç, ı, ö, ü karakterlerini
# render edemez. Bu yardımcı Windows sistem fontlarını kullanır.
_font_cache = {}

def get_font(size: int):
    """
    Türkçe destekli pygame fontu döndürür.
    Önbellek kullanır, aynı boyut tekrar istendiğinde yeni Font oluşturmaz.
    
    Kullanım:
        from config import get_font, FONTS
        font = get_font(FONTS['header'])
    """
    if size in _font_cache:
        return _font_cache[size]
    
    import pygame
    # Türkçe karakter destekli font sırası (Windows → cross-platform)
    # Segoe UI, modern Windows'un varsayılan ve en estetik fontudur.
    turkish_fonts = [
        "segoeui",       # Windows 10/11 varsayılan — en iyi Türkçe desteği ve estetik
        "corbel",        # Modern alternatif
        "calibri",       # Başka bir temiz sans-serif
        "arial",         # Tüm Windows sürümlerinde mevcut
        "tahoma",        # Eski Windows uyumluluğu
        "verdana",       # Alternatif
        "dejavusans",    # Linux/cross-platform
        "freesans",      # Son çare
    ]
    
    font = None
    for font_name in turkish_fonts:
        try:
            font = pygame.font.SysFont(font_name, size)
            # Türkçe karakter testi — font render edebiliyor mu?
            test_surface = font.render("şğçıöüŞĞÇİÖÜ", True, (255, 255, 255))
            if test_surface.get_width() > 0:
                break
        except Exception:
            continue
    
    if font is None:
        # Hiçbir sistem fontu bulunamazsa varsayılana düş
        font = pygame.font.Font(None, size)
    
    _font_cache[size] = font
    return font

# Çok Oyunculu Ayarları (HTTP Polling)
MULTIPLAYER = {
    # Varsayılan sunucu - VDS IP adresinizi buraya yazın
    'default_server': '127.0.0.1',  # Localhost test için
    'default_port': 5000,  # HTTP sunucu portu
}

# Zafer Koşulları (Oyun Sonu Hedefleri)
VICTORY_CONDITIONS = {
    # Ekonomik zafer: Bu kadar altın biriktir
    'economic_gold': 500000,
    
    # Askeri zafer: Bu kadar düşman yenilgisi
    'military_victories': 10,
    
    # Diplomatik zafer: Bu kadar ittifak
    'diplomatic_alliances': 5,
    
    # Hakimiyet zafer: Kapasitenin bu kadar katına ulaş
    'dominance_population_multiplier': 3,  # 3x kapasite = 150k+
}
