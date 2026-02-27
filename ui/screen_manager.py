# -*- coding: utf-8 -*-
"""
Osmanlı Eyalet Yönetim Simülasyonu - Ekran Yöneticisi
Ekranlar arası geçiş ve aktif ekran yönetimi.
"""

import pygame
from enum import Enum
from typing import Optional
from audio.audio_manager import get_audio_manager
from audio.music_manager import get_music_manager
from config import COLORS


class ScreenType(Enum):
    """Ekran tipleri"""
    MAIN_MENU = "main_menu"
    PROVINCE_VIEW = "province_view"
    ECONOMY = "economy"
    MILITARY = "military"
    CONSTRUCTION = "construction"
    DIPLOMACY = "diplomacy"
    POPULATION = "population"
    EVENT = "event"
    SETTINGS = "settings"
    GAME_OVER = "game_over"
    SAVE_LOAD = "save_load"
    WORKERS = "workers"
    MAP = "map"
    WARFARE = "warfare"
    TRADE = "trade"
    PROVINCE_SELECT = "province_select"
    BATTLE = "battle"  # İnteraktif savaş ekranı
    MULTIPLAYER = "multiplayer"  # Çok oyunculu lobi
    MULTIPLAYER_GAME = "multiplayer_game"  # Çok oyunculu oyun
    RAID_REPORT = "raid_report"  # Akın rapor ekranı
    BUILDING_INTERIOR = "building_interior"  # Bina iç ekranı
    NEGOTIATION = "negotiation"  # Diplomatik müzakere ekranı
    ESPIONAGE = "espionage"  # Casusluk ekranı (YENİ)
    RELIGION = "religion"  # Din/Kültür ekranı (YENİ)
    ACHIEVEMENT = "achievement"  # Başarılar ekranı (YENİ)
    TUTORIAL = "tutorial"  # Eğitim ekranı (YENİ)
    WORKER_INTERVIEW = "worker_interview"  # İşçi görüşme ekranı (YENİ)
    NAVAL = "naval"  # Deniz kuvvetleri ekranı (YENİ)
    ARTILLERY = "artillery"  # Topçu ekranı (YENİ)
    CHARACTER_CREATION = "character_creation"  # Karakter oluşturma (YENİ)
    GUILD = "guild"  # Lonca yönetim ekranı (YENİ)
    HISTORY = "history"  # Geçmiş olaylar ekranı (YENİ)
    DIVAN = "divan"  # Eyalet Divanı ekranı (YENİ)
    ADVISOR = "advisor"  # Kethüda ekranı (YENİ)


class BaseScreen:
    """Tüm ekranlar için temel sınıf"""
    
    def __init__(self, screen_manager):
        self.screen_manager = screen_manager
        self.audio = get_audio_manager()
        self.initialized = False
        
        # Font önbellekleri (Tüm alt ekranlar için ortak)
        from config import FONTS, get_font
        self._header_font = None
        self._body_font = None
        
    def get_header_font(self):
        if self._header_font is None:
            from config import FONTS, get_font
            self._header_font = get_font(FONTS['header'])
        return self._header_font
        
    def get_font(self):
        if self._body_font is None:
            from config import FONTS, get_font
            self._body_font = get_font(FONTS['body'])
        return self._body_font
    
    def on_enter(self):
        """Ekrana girişte çağrılır"""
        pass
    
    def on_exit(self):
        """Ekrandan çıkışta çağrılır"""
        pass
    
    def handle_event(self, event) -> bool:
        """Olay işle, True dönerse olay tüketildi demek"""
        return False
    
    def update(self, dt: float):
        """Ekranı güncelle (dt: delta time in seconds)"""
        pass
    
    def draw(self, surface: pygame.Surface):
        """Ekranı çiz"""
        pass
    
    def announce_screen(self):
        """Ekran ismini duyur"""
        pass


class ScreenManager:
    """Ekran yöneticisi"""
    
    def __init__(self, game_manager=None):
        self.game_manager = game_manager
        self.screens = {}
        self.current_screen: Optional[BaseScreen] = None
        self.current_screen_type: Optional[ScreenType] = None
        self.previous_screen_type: Optional[ScreenType] = None
        self.audio = get_audio_manager()
        self.music = get_music_manager()
        
        # Ekran geçişi (Fade) değişkenleri
        self.fade_alpha = 0
        self.fade_state = None  # None, "out" (kararma), "in" (aydınlanma)
        self.fade_speed = 1200  # alpha per second (0-255 scaling). 1200 means full fade out/in takes ~0.2s total
        self.target_screen_type = None
        self.target_announce = False
        
        # Multiplayer mod flag - alt ekranların geri dönüşünü belirler
        self.is_multiplayer_mode = False
    
    def register_screen(self, screen_type: ScreenType, screen: BaseScreen):
        """Ekran kaydet"""
        self.screens[screen_type] = screen
    
    def change_screen(self, screen_type: ScreenType, announce: bool = True):
        """Ekran değiştir (Fade ile)"""
        if screen_type not in self.screens:
            print(f"Ekran bulunamadı: {screen_type}")
            return
            
        # Eğer zaten bir geçiş varsa iptal et, hemen geç (veya sıraya al)
        if self.fade_state is not None:
            self._execute_screen_change(self.target_screen_type, self.target_announce)
            
        self.target_screen_type = screen_type
        self.target_announce = announce
        self.fade_state = "out"
        self.fade_alpha = 0
        
    def _execute_screen_change(self, screen_type: ScreenType, announce: bool):
        """Gerçek ekran değişimini uygula"""
        # Önceki ekrandan çık
        if self.current_screen:
            self.current_screen.on_exit()
            # Ambiyans sesini durdur
            self.audio.stop_ambient()
        
        self.previous_screen_type = self.current_screen_type
        self.current_screen_type = screen_type
        self.current_screen = self.screens[screen_type]
        
        # Yeni ekrana gir
        self.current_screen.on_enter()
        
        # Müziği ekrana göre değiştir
        self.music.on_screen_change(screen_type.name)
        
        # Ambiyans sesini ekrana göre çal (dosya varsa)
        self._play_screen_ambient(screen_type)
        
        if announce:
            self.current_screen.announce_screen()
    
    # Ekran -> Ambiyans ses eşlemesi
    # Her ekran için tematik çevre sesi. Dosya yoksa sessizce devam eder.
    SCREEN_AMBIENT_MAP = {
        ScreenType.MAIN_MENU: None,  # Menüde ambiyans yok, sadece müzik
        ScreenType.PROVINCE_VIEW: "city",  # Şehir sesleri
        ScreenType.ECONOMY: "market",  # Pazar sesleri
        ScreenType.MILITARY: "camp",  # Askeri kamp sesleri
        ScreenType.CONSTRUCTION: "workshop",  # Atölye/inşaat sesleri
        ScreenType.POPULATION: "crowd",  # Kalabalık sesleri
        ScreenType.WORKERS: "crowd",  # Çalışan işçi sesleri
        ScreenType.TRADE: "bazaar",  # Çarşı/Bedesten sesleri
        ScreenType.ESPIONAGE: "night",  # Gece sesleri
        ScreenType.RELIGION: "mosque",  # Cami ambiyansı
        ScreenType.DIPLOMACY: "court",  # Saray sesleri
        ScreenType.NEGOTIATION: "court",  # Saray sesleri
        ScreenType.WARFARE: "march",  # Yürüyüş/savaş hazırlığı
        ScreenType.BATTLE: "battlefield",  # Savaş alanı
        ScreenType.RAID_REPORT: None,
        ScreenType.MAP: "wind",  # Rüzgar sesi
        ScreenType.NAVAL: "sea",  # Deniz/dalga sesleri
        ScreenType.ARTILLERY: "foundry",  # Dökümhane sesleri
        ScreenType.BUILDING_INTERIOR: "workshop",  # Atölye sesleri
        ScreenType.GUILD: "bazaar",  # Çarşı sesleri
        ScreenType.HISTORY: None,
        ScreenType.DIVAN: "court",  # Divan toplantısı
        ScreenType.TUTORIAL: None,
        ScreenType.ACHIEVEMENT: None,
    }
    
    def _play_screen_ambient(self, screen_type: ScreenType):
        """Ekrana uygun ambiyans sesini çal (dosya yoksa sessizce geç)"""
        ambient_name = self.SCREEN_AMBIENT_MAP.get(screen_type)
        if ambient_name:
            self.audio.play_ambient(ambient_name)
    
    def go_back(self):
        """Önceki ekrana dön"""
        if self.previous_screen_type:
            self.change_screen(self.previous_screen_type)
    
    def handle_event(self, event) -> bool:
        """Olayı aktif ekrana ilet"""
        if self.current_screen:
            return self.current_screen.handle_event(event)
        return False
    
    def update(self, dt: float):
        """Aktif ekranı ve geçiş efeklerini güncelle"""
        # Fade güncellemeleri
        if self.fade_state == "out":
            self.fade_alpha += self.fade_speed * dt
            if self.fade_alpha >= 255:
                self.fade_alpha = 255
                self._execute_screen_change(self.target_screen_type, self.target_announce)
                self.fade_state = "in"
        elif self.fade_state == "in":
            self.fade_alpha -= self.fade_speed * dt
            if self.fade_alpha <= 0:
                self.fade_alpha = 0
                self.fade_state = None
                
        # Aktif ekran güncellemeleri
        if self.current_screen:
            self.current_screen.update(dt)
    
    # Ekran tipi → gradient tema eşleştirmesi
    SCREEN_GRADIENT_MAP = {
        'main_menu': 'menu',
        'province_view': 'default',
        'economy': 'economy',
        'military': 'military',
        'construction': 'construction',
        'diplomacy': 'diplomacy',
        'population': 'default',
        'trade': 'trade',
        'save_load': 'default',
        'event': 'default',
        'settings': 'default',
        'espionage': 'espionage',
        'warfare': 'battle',
        'battle': 'battle',
        'raid_report': 'battle',
        'negotiation': 'diplomacy',
        'workers': 'construction',
        'worker_interview': 'construction',
        'multiplayer': 'menu',
        'multiplayer_game': 'default',
        'religion': 'religion',
        'map': 'map',
        'achievement': 'default',
        'tutorial': 'menu',
        'naval': 'naval',
        'artillery': 'artillery',
        'province_select': 'menu',
        'character_creation': 'menu',
        'guild': 'trade',
        'history': 'default',
        'divan': 'diplomacy',
    }
    
    def draw(self, surface: pygame.Surface):
        """Aktif ekranı ve fade overlay'i çiz"""
        # Gradient arka plan (ekran tipine göre)
        from ui.visual_effects import GradientRenderer
        theme = 'default'
        if self.current_screen_type:
            theme = self.SCREEN_GRADIENT_MAP.get(self.current_screen_type.value, 'default')
        gradient = GradientRenderer.get_gradient(theme)
        surface.blit(gradient, (0, 0))
        
        if self.current_screen:
            self.current_screen.draw(surface)
            
        # Karartma (Fade) Overlay
        if self.fade_state is not None and self.fade_alpha > 0:
            fade_surface = pygame.Surface(surface.get_size())
            fade_surface.fill((0, 0, 0))
            fade_surface.set_alpha(int(self.fade_alpha))
            surface.blit(fade_surface, (0, 0))
