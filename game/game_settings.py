# -*- coding: utf-8 -*-
"""
Osmanlı Eyalet Yönetim Simülasyonu - Oyun Ayarları
Kalıcı ayarlar ve çeviri sistemi
"""

import json
import os
from typing import Dict, Any


class GameSettings:
    """Kalıcı oyun ayarları - JSON'a kaydedilir"""
    
    _instance = None
    SETTINGS_FILE = "game_settings.json"
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._initialized = True
        
        # Varsayılan ayarlar
        self.defaults = {
            # Ses ayarları
            'music_volume': 25,      # 0-100
            'sfx_volume': 70,        # 0-100
            'music_enabled': True,
            'sfx_enabled': True,
            
            # Otomatik kayıt
            'auto_save_enabled': True,
            'auto_save_interval': 5,  # Her X turda
            
            # Dil
            'language': 'tr',  # 'tr' veya 'en'
            
            # Erişilebilirlik
            'announce_hover': True,
            'high_contrast': False,
        }
        
        self.settings: Dict[str, Any] = {}
        self.load()
    
    def load(self):
        """Ayarları dosyadan yükle"""
        try:
            if os.path.exists(self.SETTINGS_FILE):
                with open(self.SETTINGS_FILE, 'r', encoding='utf-8') as f:
                    self.settings = json.load(f)
                # Eksik ayarları varsayılanlardan doldur
                for key, value in self.defaults.items():
                    if key not in self.settings:
                        self.settings[key] = value
            else:
                self.settings = self.defaults.copy()
        except Exception as e:
            print(f"Ayarlar yüklenemedi: {e}")
            self.settings = self.defaults.copy()
    
    def save(self):
        """Ayarları dosyaya kaydet"""
        try:
            with open(self.SETTINGS_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Ayarlar kaydedilemedi: {e}")
    
    def get(self, key: str, default=None):
        """Ayar değerini al"""
        return self.settings.get(key, self.defaults.get(key, default))
    
    def set(self, key: str, value):
        """Ayar değerini ayarla ve kaydet"""
        self.settings[key] = value
        self.save()
    
    def get_language(self) -> str:
        """Aktif dili al"""
        return self.settings.get('language', 'tr')
    
    def set_language(self, lang: str):
        """Dili değiştir"""
        if lang in ('tr', 'en'):
            self.settings['language'] = lang
            self.save()


# Çeviri sistemi
TRANSLATIONS = {
    'tr': {
        # Ana Menü
        'game_title': 'Osmanlı Eyalet Yönetimi',
        'new_game': 'Yeni Oyun',
        'continue_game': 'Devam Et',
        'load_game': 'Oyun Yükle',
        'settings': 'Ayarlar',
        'quit': 'Çıkış',
        
        # Ayarlar Ekranı
        'settings_title': 'Ayarlar',
        'sound_settings': 'Ses Ayarları',
        'music_volume': 'Müzik Seviyesi',
        'sfx_volume': 'Efekt Seviyesi',
        'music_enabled': 'Müzik',
        'sfx_enabled': 'Efektler',
        'enabled': 'Açık',
        'disabled': 'Kapalı',
        
        'auto_save': 'Otomatik Kayıt',
        'auto_save_interval': 'Kayıt Aralığı (tur)',
        'every_x_turns': 'Her {} turda',
        
        'language': 'Dil',
        'turkish': 'Türkçe',
        'english': 'English',
        
        'back': 'Geri',
        'save_settings': 'Kaydet',
        
        # Genel
        'gold': 'Altın',
        'food': 'Zahire',
        'wood': 'Kereste',
        'iron': 'Demir',
        'population': 'Nüfus',
        'turn': 'Tur',
        'year': 'Yıl',
        
        # Askeri
        'army': 'Ordu',
        'soldiers': 'Asker',
        'cavalry': 'Süvari',
        'infantry': 'Piyade',
        'artillery': 'Topçu',
        'morale': 'Moral',
        
        # Savaş
        'battle': 'Savaş',
        'raid': 'Akın',
        'siege': 'Kuşatma',
        'victory': 'Zafer',
        'defeat': 'Yenilgi',
        'attack': 'Saldır',
        'defend': 'Savun',
        'retreat': 'Geri Çekil',
        
        # İşçiler
        'workers': 'İşçiler',
        'farmer': 'Çiftçi',
        'miner': 'Madenci',
        'lumberjack': 'Oduncu',
        'craftsman': 'Usta',
        'merchant': 'Tüccar',
        'envoy': 'Elçi',
        'hire': 'İşe Al',
        'fire': 'İşten Çıkar',
        'rename': 'İsim Değiştir',
        
        # Binalar
        'buildings': 'Binalar',
        'construction': 'İnşaat',
        'build': 'İnşa Et',
        'upgrade': 'Geliştir',
        'demolish': 'Yık',
        
        # Diplomasi
        'diplomacy': 'Diplomasi',
        'alliance': 'İttifak',
        'trade_agreement': 'Ticaret Anlaşması',
        'war': 'Savaş',
        'peace': 'Barış',
        
        # Navigasyon
        'next_turn': 'Sonraki Tur',
        'press_key': '{} Tuşuna Basın',
    },
    
    'en': {
        # Main Menu
        'game_title': 'Ottoman Province Management',
        'new_game': 'New Game',
        'continue_game': 'Continue',
        'load_game': 'Load Game',
        'settings': 'Settings',
        'quit': 'Quit',
        
        # Settings Screen
        'settings_title': 'Settings',
        'sound_settings': 'Sound Settings',
        'music_volume': 'Music Volume',
        'sfx_volume': 'Effects Volume',
        'music_enabled': 'Music',
        'sfx_enabled': 'Effects',
        'enabled': 'On',
        'disabled': 'Off',
        
        'auto_save': 'Auto Save',
        'auto_save_interval': 'Save Interval (turns)',
        'every_x_turns': 'Every {} turns',
        
        'language': 'Language',
        'turkish': 'Türkçe',
        'english': 'English',
        
        'back': 'Back',
        'save_settings': 'Save',
        
        # General
        'gold': 'Gold',
        'food': 'Food',
        'wood': 'Wood',
        'iron': 'Iron',
        'population': 'Population',
        'turn': 'Turn',
        'year': 'Year',
        
        # Military
        'army': 'Army',
        'soldiers': 'Soldiers',
        'cavalry': 'Cavalry',
        'infantry': 'Infantry',
        'artillery': 'Artillery',
        'morale': 'Morale',
        
        # Battle
        'battle': 'Battle',
        'raid': 'Raid',
        'siege': 'Siege',
        'victory': 'Victory',
        'defeat': 'Defeat',
        'attack': 'Attack',
        'defend': 'Defend',
        'retreat': 'Retreat',
        
        # Workers
        'workers': 'Workers',
        'farmer': 'Farmer',
        'miner': 'Miner',
        'lumberjack': 'Lumberjack',
        'craftsman': 'Craftsman',
        'merchant': 'Merchant',
        'envoy': 'Envoy',
        'hire': 'Hire',
        'fire': 'Fire',
        'rename': 'Rename',
        
        # Buildings
        'buildings': 'Buildings',
        'construction': 'Construction',
        'build': 'Build',
        'upgrade': 'Upgrade',
        'demolish': 'Demolish',
        
        # Diplomacy
        'diplomacy': 'Diplomacy',
        'alliance': 'Alliance',
        'trade_agreement': 'Trade Agreement',
        'war': 'War',
        'peace': 'Peace',
        
        # Navigation
        'next_turn': 'Next Turn',
        'press_key': 'Press {}',
    }
}


def get_text(key: str, *args) -> str:
    """Çeviri metnini al"""
    settings = GameSettings()
    lang = settings.get_language()
    
    text = TRANSLATIONS.get(lang, TRANSLATIONS['tr']).get(key, key)
    
    # Format argümanları varsa uygula
    if args:
        try:
            text = text.format(*args)
        except:
            pass
    
    return text


def t(key: str, *args) -> str:
    """Kısa çeviri fonksiyonu"""
    return get_text(key, *args)


# Singleton erişim
def get_settings() -> GameSettings:
    return GameSettings()
