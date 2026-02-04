# -*- coding: utf-8 -*-
"""
Osmanlı Eyalet Yönetim Simülasyonu - Ses Yöneticisi
NVDA ve diğer ekran okuyucu desteği ile.
"""

import os
import pygame
from config import AUDIO, ACCESSIBILITY

# Erişilebilirlik için accessible_output2
try:
    import accessible_output2.outputs.auto as ao2
    SCREEN_READER_AVAILABLE = True
except ImportError:
    SCREEN_READER_AVAILABLE = False
    print("Uyarı: accessible_output2 bulunamadı. Ekran okuyucu desteği devre dışı.")


class AudioManager:
    """Ses ve erişilebilirlik yöneticisi"""
    
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
        self.music_volume = AUDIO['music_volume']
        self.sfx_volume = AUDIO['sfx_volume']
        self.ui_volume = AUDIO['ui_volume']
        
        # Ses dosyaları önbelleği
        self.sounds = {}
        self.music_paths = {}  # Müzik adı -> dosya yolu eşlemesi
        self.current_music = None
        
        # Erişilebilirlik
        self.screen_reader = None
        if SCREEN_READER_AVAILABLE and ACCESSIBILITY['screen_reader_enabled']:
            try:
                self.screen_reader = ao2.Auto()
            except Exception as e:
                print(f"Ekran okuyucu başlatılamadı: {e}")
        
        # Pygame mixer başlat
        try:
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=2048)
            self.mixer_available = True
        except pygame.error as e:
            print(f"Ses sistemi başlatılamadı: {e}")
            self.mixer_available = False
        
        # Ses klasörlerini oluştur
        self._ensure_sound_directories()
    
    def _ensure_sound_directories(self):
        """Ses klasörlerinin varlığını kontrol et ve oluştur"""
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        sound_dirs = [
            os.path.join(base_path, 'audio', 'sounds', 'music'),
            os.path.join(base_path, 'audio', 'sounds', 'ui'),
            os.path.join(base_path, 'audio', 'sounds', 'events'),
        ]
        for dir_path in sound_dirs:
            os.makedirs(dir_path, exist_ok=True)
    
    def load_sound(self, name: str, path: str) -> bool:
        """Ses dosyası yükle"""
        if not self.mixer_available:
            return False
        
        try:
            if os.path.exists(path):
                self.sounds[name] = pygame.mixer.Sound(path)
                return True
            else:
                print(f"Ses dosyası bulunamadı: {path}")
                return False
        except pygame.error as e:
            print(f"Ses yüklenemedi {path}: {e}")
            return False
    
    def play_sound(self, name: str, volume: float = None):
        """Ses efekti çal"""
        if not self.mixer_available:
            return
        
        if name in self.sounds:
            sound = self.sounds[name]
            if volume is not None:
                sound.set_volume(volume)
            else:
                sound.set_volume(self.sfx_volume)
            sound.play()
    
    def play_ui_sound(self, sound_type: str):
        """UI ses efekti çal (click, hover, notification)"""
        sound_name = f"ui_{sound_type}"
        if sound_name in self.sounds:
            self.sounds[sound_name].set_volume(self.ui_volume)
            self.sounds[sound_name].play()
    
    def play_music(self, name_or_path: str, loop: bool = True):
        """Müzik çal - isim veya dosya yolu kabul eder"""
        if not self.mixer_available:
            return
        
        # Önce music_paths sözlüğünde ara
        if name_or_path in self.music_paths:
            path = self.music_paths[name_or_path]
        else:
            path = name_or_path
        
        try:
            if os.path.exists(path):
                pygame.mixer.music.load(path)
                pygame.mixer.music.set_volume(self.music_volume)
                pygame.mixer.music.play(-1 if loop else 0)
                self.current_music = path
            else:
                # Dosya yoksa sessizce devam et
                pass
        except pygame.error as e:
            print(f"Müzik çalınamadı: {e}")
    
    def stop_music(self):
        """Müziği durdur"""
        if self.mixer_available:
            pygame.mixer.music.stop()
            self.current_music = None
    
    def pause_music(self):
        """Müziği duraklat"""
        if self.mixer_available:
            pygame.mixer.music.pause()
    
    def resume_music(self):
        """Müziğe devam et"""
        if self.mixer_available:
            pygame.mixer.music.unpause()
    
    def set_music_volume(self, volume: float):
        """Müzik ses seviyesi ayarla (0.0 - 1.0)"""
        self.music_volume = max(0.0, min(1.0, volume))
        if self.mixer_available:
            pygame.mixer.music.set_volume(self.music_volume)
    
    def set_sfx_volume(self, volume: float):
        """Efekt ses seviyesi ayarla (0.0 - 1.0)"""
        self.sfx_volume = max(0.0, min(1.0, volume))
    
    def set_ui_volume(self, volume: float):
        """UI ses seviyesi ayarla (0.0 - 1.0)"""
        self.ui_volume = max(0.0, min(1.0, volume))
    
    def increase_music_volume(self, amount: float = 0.05):
        """Müzik sesini artır (varsayılan %5)"""
        new_volume = min(1.0, self.music_volume + amount)
        self.set_music_volume(new_volume)
        pct = int(new_volume * 100)
        self.speak(f"Müzik sesi: %{pct}", interrupt=True)
    
    def decrease_music_volume(self, amount: float = 0.05):
        """Müzik sesini azalt (varsayılan %5)"""
        new_volume = max(0.0, self.music_volume - amount)
        self.set_music_volume(new_volume)
        pct = int(new_volume * 100)
        self.speak(f"Müzik sesi: %{pct}", interrupt=True)
    
    # === EKRAN OKUYUCU FONKSİYONLARI ===
    
    def speak(self, text: str, interrupt: bool = True):
        """
        Metni ekran okuyucu ile seslendir
        
        Args:
            text: Okunacak metin
            interrupt: True ise önceki konuşmayı kes
        """
        if self.screen_reader and ACCESSIBILITY['screen_reader_enabled']:
            try:
                self.screen_reader.speak(text, interrupt=interrupt)
            except Exception as e:
                print(f"Ekran okuyucu hatası: {e}")
    
    def announce(self, text: str):
        """Duyuru yap (genellikle önemli bilgiler için)"""
        self.speak(text, interrupt=True)
    
    def announce_menu_item(self, item_name: str, position: int = None, total: int = None):
        """Menü öğesini duyur"""
        if position is not None and total is not None:
            message = f"{item_name}, {position}/{total}"
        else:
            message = item_name
        self.speak(message)
    
    def announce_button(self, button_name: str, shortcut: str = None):
        """Buton bilgisini duyur"""
        if shortcut:
            message = f"{button_name} butonu, kısayol: {shortcut}"
        else:
            message = f"{button_name} butonu"
        self.speak(message)
    
    def announce_value(self, label: str, value: str, unit: str = None):
        """Değer bilgisini duyur"""
        if unit:
            message = f"{label}: {value} {unit}"
        else:
            message = f"{label}: {value}"
        self.speak(message)
    
    def announce_screen_change(self, screen_name: str):
        """Ekran değişikliğini duyur"""
        self.speak(f"{screen_name} ekranı açıldı", interrupt=True)
    
    def announce_action_result(self, action: str, success: bool, detail: str = None):
        """İşlem sonucunu duyur"""
        result = "başarılı" if success else "başarısız"
        message = f"{action} {result}"
        if detail:
            message += f". {detail}"
        self.speak(message)
    
    def load_sounds_from_directory(self, directory: str, prefix: str = ""):
        """Bir klasördeki tüm ses dosyalarını yükle"""
        if not os.path.exists(directory):
            return
        
        supported_formats = ('.wav', '.ogg', '.mp3')
        
        for filename in os.listdir(directory):
            if filename.lower().endswith(supported_formats):
                name = prefix + os.path.splitext(filename)[0]
                path = os.path.join(directory, filename)
                self.load_sound(name, path)
    
    def cleanup(self):
        """Kaynakları temizle"""
        if self.mixer_available:
            pygame.mixer.quit()


# Global erişim için
_audio_manager = None

def get_audio_manager() -> AudioManager:
    """AudioManager singleton örneğini al"""
    global _audio_manager
    if _audio_manager is None:
        _audio_manager = AudioManager()
    return _audio_manager
