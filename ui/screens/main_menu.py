# -*- coding: utf-8 -*-
"""
Osmanlı Eyalet Yönetim Simülasyonu - Ana Menü Ekranı
"""

import pygame
from ui.screen_manager import BaseScreen, ScreenType
from ui.components import MenuList, Button
from config import COLORS, FONTS, SCREEN_WIDTH, SCREEN_HEIGHT, KEYBINDS


class MainMenuScreen(BaseScreen):
    """Ana menü ekranı"""
    
    def __init__(self, screen_manager):
        super().__init__(screen_manager)
        
        # Menü listesi
        self.menu = MenuList(
            x=(SCREEN_WIDTH - 400) // 2,
            y=300,
            width=400,
            item_height=60
        )
        
        # Menü öğelerini ekle
        self.menu.add_item("Yeni Oyun", self._on_new_game, "n")
        self.menu.add_item("Devam Et", self._on_continue, "c")
        self.menu.add_item("Çok Oyunculu", self._on_multiplayer, "m")
        self.menu.add_item("Ayarlar", self._on_settings, "a")
        self.menu.add_item("Hakkında", self._on_about, "h")
        self.menu.add_item("Çıkış", self._on_exit, "q")
        
        # Başlık fontları
        self._title_font = None
        self._subtitle_font = None
    
    def get_title_font(self):
        if self._title_font is None:
            self._title_font = pygame.font.Font(None, FONTS['title'])
        return self._title_font
    
    def get_subtitle_font(self):
        if self._subtitle_font is None:
            self._subtitle_font = pygame.font.Font(None, FONTS['subheader'])
        return self._subtitle_font
    
    def on_enter(self):
        """Ekrana girişte menüyü duyur"""
        self.menu.selected_index = 0
    
    def announce_screen(self):
        self.audio.announce_screen_change("Ana Menü")
        self.audio.speak("Yeni Oyun başlatmak için N, Devam etmek için C tuşuna basın")
    
    def handle_event(self, event) -> bool:
        # Menü olaylarını işle
        if self.menu.handle_event(event):
            return True
        
        # Ek kısayollar
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_F1:
                self.audio.speak("Ana Menü. Yeni Oyun, Devam Et, Ayarlar ve Çıkış seçenekleri mevcut.")
                return True
        
        return False
    
    def draw(self, surface: pygame.Surface):
        # Başlık
        title_font = self.get_title_font()
        title = title_font.render("OSMANLI EYALET YÖNETİMİ", True, COLORS['gold'])
        title_rect = title.get_rect(centerx=SCREEN_WIDTH // 2, top=80)
        surface.blit(title, title_rect)
        
        # Alt başlık
        subtitle_font = self.get_subtitle_font()
        subtitle = subtitle_font.render("Beylerbeyi Simülasyonu", True, COLORS['text'])
        subtitle_rect = subtitle.get_rect(centerx=SCREEN_WIDTH // 2, top=150)
        surface.blit(subtitle, subtitle_rect)
        
        # Dönem bilgisi
        period = subtitle_font.render("M.S. 1520 - Kanuni Sultan Süleyman Dönemi", True, COLORS['panel_border'])
        period_rect = period.get_rect(centerx=SCREEN_WIDTH // 2, top=190)
        surface.blit(period, period_rect)
        
        # Dekoratif çizgi
        pygame.draw.line(
            surface, COLORS['gold'],
            (SCREEN_WIDTH // 2 - 200, 250),
            (SCREEN_WIDTH // 2 + 200, 250),
            3
        )
        
        # Menü
        self.menu.draw(surface)
        
        # Alt bilgi
        info_font = pygame.font.Font(None, FONTS['small'])
        info = info_font.render("F1: Yardım | Yukarı/Aşağı: Gezin | Enter: Seç", True, COLORS['text'])
        info_rect = info.get_rect(centerx=SCREEN_WIDTH // 2, bottom=SCREEN_HEIGHT - 30)
        surface.blit(info, info_rect)
    
    def _on_new_game(self):
        """Yeni oyun başlat - eyalet seçim ekranına git"""
        self.screen_manager.change_screen(ScreenType.PROVINCE_SELECT)
    
    def _on_continue(self):
        """Kayıtlı oyuna devam et - yuva seçim ekranını aç"""
        # SaveLoadScreen'i load modunda aç
        save_screen = self.screen_manager.screens.get(ScreenType.SAVE_LOAD)
        if save_screen:
            save_screen.set_mode('load')
        self.screen_manager.change_screen(ScreenType.SAVE_LOAD)
    
    def _on_multiplayer(self):
        """Çok oyunculu lobi ekranına git"""
        self.screen_manager.change_screen(ScreenType.MULTIPLAYER)
    
    def _on_settings(self):
        """Ayarlar ekranı"""
        self.audio.speak("Ayarlar ekranı henüz hazır değil")
    
    def _on_about(self):
        """Oyun hakkında bilgi"""
        self.audio.speak(
            "Osmanlı Eyalet Yönetim Simülasyonu. "
            "Versiyon: Kapalı Beta 1.0. "
            "Bu oyun Muhammet Enes Şenovalı tarafından geliştirilmektedir. "
            "Oyun 1520 yılında, Kanuni Sultan Süleyman döneminde geçmektedir. "
            "Görme engelli oyuncular için tam erişilebilirlik desteği sunulmaktadır. "
            "İyi oyunlar!",
            interrupt=True
        )
    
    def _on_exit(self):
        """Oyundan çık"""
        self.audio.speak("Oyundan çıkılıyor")
        pygame.event.post(pygame.event.Event(pygame.QUIT))
