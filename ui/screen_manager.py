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


class BaseScreen:
    """Tüm ekranlar için temel sınıf"""
    
    def __init__(self, screen_manager):
        self.screen_manager = screen_manager
        self.audio = get_audio_manager()
        self.initialized = False
    
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
        
        # Multiplayer mod flag - alt ekranların geri dönüşünü belirler
        self.is_multiplayer_mode = False
    
    def register_screen(self, screen_type: ScreenType, screen: BaseScreen):
        """Ekran kaydet"""
        self.screens[screen_type] = screen
    
    def change_screen(self, screen_type: ScreenType, announce: bool = True):
        """Ekran değiştir"""
        if screen_type not in self.screens:
            print(f"Ekran bulunamadı: {screen_type}")
            return
        
        # Önceki ekrandan çık
        if self.current_screen:
            self.current_screen.on_exit()
        
        self.previous_screen_type = self.current_screen_type
        self.current_screen_type = screen_type
        self.current_screen = self.screens[screen_type]
        
        # Yeni ekrana gir
        self.current_screen.on_enter()
        
        # Müziği ekrana göre değiştir
        self.music.on_screen_change(screen_type.name)
        
        if announce:
            self.current_screen.announce_screen()
    
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
        """Aktif ekranı güncelle"""
        if self.current_screen:
            self.current_screen.update(dt)
    
    def draw(self, surface: pygame.Surface):
        """Aktif ekranı çiz"""
        # Arka plan
        surface.fill(COLORS['background'])
        
        if self.current_screen:
            self.current_screen.draw(surface)
