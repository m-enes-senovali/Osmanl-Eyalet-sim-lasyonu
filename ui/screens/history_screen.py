# -*- coding: utf-8 -*-
"""
Osmanlı Eyalet Yönetim Simülasyonu - Geçmiş Olaylar Ekranı
"""

import pygame
from ui.screen_manager import BaseScreen, ScreenType
from ui.components import Button, Panel, MenuList
from config import COLORS, FONTS, SCREEN_WIDTH, SCREEN_HEIGHT, get_font

class HistoryScreen(BaseScreen):
    """Geçmiş olayları görüntüleme ekranı"""
    
    def __init__(self, screen_manager):
        super().__init__(screen_manager)
        
        # Filtre butonları
        self.filters = ["Tümü", "Genel", "Ekonomi", "Askeri", "Diplomasi", "Olay"]
        self.filter_keys = ["all", "general", "economic", "military", "diplomatic", "event"]
        self.current_filter_index = 0
        
        # Olay listesi menüsü
        self.history_menu = MenuList(
            x=50,
            y=120,
            width=SCREEN_WIDTH - 100,
            item_height=40
        )
        
        # Geri butonu
        self.back_button = Button(
            SCREEN_WIDTH - 200, SCREEN_HEIGHT - 60,
            180, 45, "Geri", callback=self._go_back
        )
        
        self.header_font = None
    
    def get_header_font(self):
        if self.header_font is None:
            self.header_font = get_font(FONTS['header'])
        return self.header_font
    
    def on_enter(self):
        self._refresh_list()
        self.audio.announce_screen_change("Geçmiş Olaylar")
        self.audio.speak(f"Filtre: {self.filters[self.current_filter_index]}. Tab ile filtre değiştirin.", interrupt=False)
    
    def _refresh_list(self):
        """Listeyi güncelle"""
        self.history_menu.clear()
        gm = self.screen_manager.game_manager
        if not gm or not hasattr(gm, 'history'):
            self.history_menu.add_item("Kayıt yok", None)
            return
            
        category = self.filter_keys[self.current_filter_index]
        entries = gm.history.get_entries(category)
        
        # Yeniden eskiye sırala
        entries.reverse()
        
        if not entries:
            self.history_menu.add_item("Bu kategoride kayıt yok", None)
            return
            
        for entry in entries:
            text = f"[{entry.year}] {entry.message}"
            self.history_menu.add_item(text, lambda e=entry: self._read_entry(e))
    
    def _read_entry(self, entry):
        """Olay detayını oku"""
        self.audio.speak(f"{entry.year} yılı, {entry.turn}. gün: {entry.message}", interrupt=True)
    
    def _cycle_filter(self):
        """Filtreyi değiştir"""
        self.current_filter_index = (self.current_filter_index + 1) % len(self.filters)
        filter_name = self.filters[self.current_filter_index]
        self.audio.speak(f"Filtre: {filter_name}", interrupt=True)
        self._refresh_list()
    
    def handle_event(self, event) -> bool:
        if self.back_button.handle_event(event):
            return True
        
        if self.history_menu.handle_event(event):
            return True
            
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE or event.key == pygame.K_BACKSPACE:
                self._go_back()
                return True
            
            if event.key == pygame.K_TAB:
                self._cycle_filter()
                return True
        
        return False
    
    def update(self, dt: float):
        pass
    
    def draw(self, surface: pygame.Surface):
        # Başlık
        header_font = self.get_header_font()
        title = header_font.render(f"Geçmiş Olaylar - {self.filters[self.current_filter_index]}", True, COLORS['gold'])
        title_rect = title.get_rect(centerx=SCREEN_WIDTH // 2, top=30)
        surface.blit(title, title_rect)
        
        # Menü
        self.history_menu.draw(surface)
        
        # Geri Butonu
        self.back_button.draw(surface)
        
    def _go_back(self):
        self.screen_manager.change_screen(ScreenType.PROVINCE_VIEW)
