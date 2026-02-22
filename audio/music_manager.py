# -*- coding: utf-8 -*-
"""
Osmanlı Eyalet Yönetim Simülasyonu - Müzik Yöneticisi
Bağlama duyarlı hibrit müzik sistemi
"""

import os
import pygame
from typing import Optional, List
from enum import Enum
from config import AUDIO
from game.game_settings import get_settings


class MusicContext(Enum):
    """Müzik bağlamları"""
    MENU = "menu"           # Ana menü
    AMBIENT = "ambient"     # Normal oyun
    BATTLE = "battle"       # Savaş
    TENSE = "tense"         # Kriz/Gerilim
    VICTORY = "victory"     # Zafer
    DIPLOMACY = "diplomacy" # Diplomasi


# Müzik dosya eşlemeleri
MUSIC_FILES = {
    MusicContext.MENU: "menu_theme.ogg",
    MusicContext.AMBIENT: "background.ogg",
    MusicContext.BATTLE: "battle.ogg",
    MusicContext.TENSE: "tense.ogg",
    MusicContext.VICTORY: "victory.ogg",
    MusicContext.DIPLOMACY: "diplomacy.ogg",
}

# Ekran -> Müzik bağlamı eşlemesi
SCREEN_MUSIC_MAP = {
    'MAIN_MENU': MusicContext.MENU,
    'PROVINCE_VIEW': MusicContext.AMBIENT,
    'ECONOMY': MusicContext.AMBIENT,
    'MILITARY': MusicContext.AMBIENT,
    'CONSTRUCTION': MusicContext.AMBIENT,
    'POPULATION': MusicContext.AMBIENT,
    'WORKERS': MusicContext.AMBIENT,
    'TRADE': MusicContext.AMBIENT,
    'ESPIONAGE': MusicContext.AMBIENT,
    'RELIGION': MusicContext.AMBIENT,
    'DIPLOMACY': MusicContext.DIPLOMACY,
    'NEGOTIATION': MusicContext.DIPLOMACY,
    'WARFARE': MusicContext.BATTLE,
    'BATTLE': MusicContext.BATTLE,
    'MAP': MusicContext.AMBIENT,
    'SETTINGS': MusicContext.MENU,
    'SAVE_LOAD': MusicContext.MENU,
    'EVENT': MusicContext.AMBIENT,  # Olaya göre değişebilir
    'GAME_OVER': MusicContext.MENU,
}


class MusicManager:
    """
    Bağlama duyarlı müzik yöneticisi.
    
    Özellikler:
    - Ekran değişiminde otomatik müzik geçişi
    - Kriz durumlarında gerilim müziği
    - Fade-out/fade-in geçişler
    - Playlist desteği (ambient için)
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._initialized = True
        
        # Müzik klasörü
        self.music_dir = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'audio', 'sounds', 'music'
        )
        
        # Durum
        self.current_context: Optional[MusicContext] = None
        self.current_file: Optional[str] = None
        self.is_playing = False
        settings = get_settings()
        self.volume = settings.get('music_volume') / 100.0
        if not settings.get('music_enabled'):
            self.volume = 0.0
        
        # Kriz durumu
        self.crisis_active = False
        self.previous_context: Optional[MusicContext] = None
        
        # Ambient playlist
        self.ambient_playlist: List[str] = []
        self.playlist_index = 0
        
        # Yüklü müzikler
        self.available_music: dict = {}
        self._scan_music_files()
    
    def _scan_music_files(self):
        """Mevcut müzik dosyalarını tara"""
        self.available_music = {}
        
        if not os.path.exists(self.music_dir):
            os.makedirs(self.music_dir, exist_ok=True)
            return
        
        for context, filename in MUSIC_FILES.items():
            filepath = os.path.join(self.music_dir, filename)
            if os.path.exists(filepath):
                self.available_music[context] = filepath
        
        # Ambient playlist için tüm ambient_*.ogg dosyalarını tara
        for f in os.listdir(self.music_dir):
            if f.startswith('ambient_') and f.endswith('.ogg'):
                self.ambient_playlist.append(os.path.join(self.music_dir, f))
        
        # Ana ambient dosyasını da ekle
        if MusicContext.AMBIENT in self.available_music:
            if self.available_music[MusicContext.AMBIENT] not in self.ambient_playlist:
                self.ambient_playlist.insert(0, self.available_music[MusicContext.AMBIENT])
    
    def get_music_for_context(self, context: MusicContext) -> Optional[str]:
        """Bağlam için müzik dosyasını al"""
        # Ambient için playlist kullan
        if context == MusicContext.AMBIENT and self.ambient_playlist:
            return self.ambient_playlist[self.playlist_index % len(self.ambient_playlist)]
        
        return self.available_music.get(context)
    
    def play_context(self, context: MusicContext, force: bool = False):
        """
        Belirli bir bağlam için müzik çal.
        
        Args:
            context: Müzik bağlamı
            force: True ise aynı bağlamda bile müziği yeniden başlat
        """
        if not force and context == self.current_context:
            return
        
        music_file = self.get_music_for_context(context)
        
        if not music_file:
            # Dosya yoksa, mevcut en uygun alternatifi kullan
            if context in (MusicContext.TENSE, MusicContext.DIPLOMACY, MusicContext.VICTORY, MusicContext.BATTLE):
                # Alternatif olarak ambient kullan
                music_file = self.get_music_for_context(MusicContext.AMBIENT)
            elif context == MusicContext.MENU:
                # Menu yoksa ambient
                music_file = self.get_music_for_context(MusicContext.AMBIENT)
        
        if not music_file:
            return
        
        self._play_file(music_file)
        self.current_context = context
    
    def _play_file(self, filepath: str, loop: bool = True):
        """Müzik dosyasını çal"""
        if self.current_file == filepath and self.is_playing:
            return
        
        try:
            pygame.mixer.music.stop()
            pygame.mixer.music.load(filepath)
            pygame.mixer.music.set_volume(self.volume)
            pygame.mixer.music.play(-1 if loop else 0)
            
            self.current_file = filepath
            self.is_playing = True
            
        except Exception as e:
            print(f"Müzik çalma hatası: {e}")
    
    def on_screen_change(self, screen_name: str):
        """
        Ekran değiştiğinde çağrılır.
        Otomatik olarak uygun müziği çalar.
        """
        # Kriz aktifse müziği değiştirme
        if self.crisis_active:
            return
        
        # Ekran için bağlam bul
        context = SCREEN_MUSIC_MAP.get(screen_name.upper(), MusicContext.AMBIENT)
        self.play_context(context)
    
    def set_crisis(self, active: bool):
        """
        Kriz modunu aç/kapa.
        Kriz aktifken gerilim müziği çalar.
        """
        if active and not self.crisis_active:
            # Kriz başladı
            self.previous_context = self.current_context
            self.crisis_active = True
            self.play_context(MusicContext.TENSE)
            
        elif not active and self.crisis_active:
            # Kriz bitti
            self.crisis_active = False
            if self.previous_context:
                self.play_context(self.previous_context)
                self.previous_context = None
    
    def check_game_state(self, game_manager):
        """
        Oyun durumuna göre müzik kontrolü.
        Her tur veya periyodik olarak çağrılabilir.
        """
        if not game_manager:
            return
        
        # Düşük sadakat kontrolü
        loyalty = getattr(game_manager.population, 'loyalty', 100)
        
        # İsyan kontrolü
        has_rebellion = False
        if hasattr(game_manager, 'events'):
            for event in game_manager.events.current_events:
                if 'isyan' in event.lower() or 'rebellion' in event.lower():
                    has_rebellion = True
                    break
        
        # Kriz durumu
        crisis = loyalty < 30 or has_rebellion
        self.set_crisis(crisis)
    
    def next_ambient_track(self):
        """Sonraki ambient parçasına geç"""
        if self.ambient_playlist and self.current_context == MusicContext.AMBIENT:
            self.playlist_index = (self.playlist_index + 1) % len(self.ambient_playlist)
            self.play_context(MusicContext.AMBIENT, force=True)
    
    def set_volume(self, volume: float):
        """Ses seviyesini ayarla (0.0 - 1.0)"""
        self.volume = max(0.0, min(1.0, volume))
        if self.is_playing:
            pygame.mixer.music.set_volume(self.volume)
    
    def stop(self):
        """Müziği durdur"""
        pygame.mixer.music.stop()
        self.is_playing = False
    
    def pause(self):
        """Müziği duraklat"""
        pygame.mixer.music.pause()
        self.is_playing = False
    
    def resume(self):
        """Müziğe devam et"""
        pygame.mixer.music.unpause()
        self.is_playing = True
    
    def get_missing_music_files(self) -> List[str]:
        """Eksik müzik dosyalarını listele"""
        missing = []
        for context, filename in MUSIC_FILES.items():
            filepath = os.path.join(self.music_dir, filename)
            if not os.path.exists(filepath):
                missing.append(filename)
        return missing


# Global instance
_music_manager: Optional[MusicManager] = None


def get_music_manager() -> MusicManager:
    """Global MusicManager instance"""
    global _music_manager
    if _music_manager is None:
        _music_manager = MusicManager()
    return _music_manager
