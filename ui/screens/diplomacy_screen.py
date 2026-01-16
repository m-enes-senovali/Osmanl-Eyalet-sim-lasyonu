# -*- coding: utf-8 -*-
"""
Osmanlı Eyalet Yönetim Simülasyonu - Diplomasi Ekranı
"""

import pygame
from ui.screen_manager import BaseScreen, ScreenType
from ui.components import Button, Panel, MenuList
from config import COLORS, FONTS, SCREEN_WIDTH, SCREEN_HEIGHT


class DiplomacyScreen(BaseScreen):
    """Diplomasi yönetim ekranı"""
    
    def __init__(self, screen_manager):
        super().__init__(screen_manager)
        
        # Paneller
        self.sultan_panel = Panel(20, 80, 400, 250, "Padişah İlişkileri")
        self.neighbors_panel = Panel(440, 80, 400, 250, "Komşu Beylikler")
        self.missions_panel = Panel(20, 350, 400, 200, "Aktif Görevler")
        
        # Eylem menüsü
        self.action_menu = MenuList(
            x=440,
            y=360,
            width=400,
            item_height=45
        )
        
        self.back_button = Button(
            x=20,
            y=SCREEN_HEIGHT - 70,
            width=150,
            height=50,
            text="Geri",
            shortcut="backspace",
            callback=self._go_back
        )
        
        self._header_font = None
    
    def get_header_font(self):
        if self._header_font is None:
            self._header_font = pygame.font.Font(None, FONTS['header'])
        return self._header_font
    
    def on_enter(self):
        self._update_panels()
        self._setup_action_menu()
    
    def announce_screen(self):
        self.audio.announce_screen_change("Diplomasi")
        gm = self.screen_manager.game_manager
        if gm:
            gm.diplomacy.announce_status()
    
    def _setup_action_menu(self):
        """Eylem menüsünü ayarla"""
        self.action_menu.clear()
        gm = self.screen_manager.game_manager
        if not gm:
            return
        
        # Haraç gönder
        self.action_menu.add_item(
            "Padişaha 500 Altın Gönder",
            lambda: self._send_tribute(500)
        )
        self.action_menu.add_item(
            "Padişaha 1000 Altın Gönder",
            lambda: self._send_tribute(1000)
        )
        
        # Elçi gönder
        for neighbor in gm.diplomacy.neighbors:
            self.action_menu.add_item(
                f"Elçi Gönder: {neighbor}",
                lambda n=neighbor: self._send_envoy(n)
            )
    
    def _update_panels(self):
        """Panelleri güncelle"""
        gm = self.screen_manager.game_manager
        if not gm:
            return
        
        dip = gm.diplomacy
        
        # Padişah paneli
        self.sultan_panel.clear()
        self.sultan_panel.add_item("Sadakat", f"%{dip.sultan_loyalty}")
        self.sultan_panel.add_item("Durum", dip.get_loyalty_description())
        self.sultan_panel.add_item("Lütuf", f"%{dip.sultan_favor}")
        self.sultan_panel.add_item("", "")
        self.sultan_panel.add_item("Sadrazam İlişkisi", f"{dip.sadrazam_relation}")
        self.sultan_panel.add_item("Defterdar İlişkisi", f"{dip.defterdar_relation}")
        
        # Komşular paneli
        self.neighbors_panel.clear()
        for name, relation in dip.neighbors.items():
            type_name = dip.get_relation_type_name(relation.relation_type)
            self.neighbors_panel.add_item(name, f"{type_name} ({relation.value})")
        
        if dip.envoy_cooldown > 0:
            self.neighbors_panel.add_item("", "")
            self.neighbors_panel.add_item("Elçi Bekleme", f"{dip.envoy_cooldown} tur")
        
        # Görevler paneli
        self.missions_panel.clear()
        if dip.active_missions:
            for mission in dip.active_missions:
                self.missions_panel.add_item(
                    mission['title'],
                    f"{mission['turns_remaining']} tur"
                )
        else:
            self.missions_panel.add_item("Aktif görev yok", "")
    
    def handle_event(self, event) -> bool:
        if self.action_menu.handle_event(event):
            return True
        
        if self.back_button.handle_event(event):
            return True
        
        if event.type == pygame.KEYDOWN:
            # Backspace veya Escape - Geri dön
            if event.key in (pygame.K_BACKSPACE, pygame.K_ESCAPE):
                self._go_back()
                return True
            
            # F1 - Özet
            if event.key == pygame.K_F1:
                gm = self.screen_manager.game_manager
                if gm:
                    gm.diplomacy.announce_status()
                return True
            
            # H - Hızlı haraç (500 altın)
            if event.key == pygame.K_h:
                self._send_tribute(500)
                self.audio.play_ui_sound('click')
                return True
            
            # S - Padişah durumu
            if event.key == pygame.K_s:
                self._announce_sultan_status()
                return True
            
            # N - Harita ekranına git (komşular ok tuşlarıyla)
            if event.key == pygame.K_n:
                self.screen_manager.change_screen(ScreenType.MAP)
                return True
            
            # Tab - Paneller arası
            if event.key == pygame.K_TAB:
                self._announce_next_panel()
                return True
        
        return False
    
    def _announce_sultan_status(self):
        """Padişah durumunu duyur"""
        gm = self.screen_manager.game_manager
        if not gm:
            return
        dip = gm.diplomacy
        self.audio.speak(f"Padişah Sadakati: yüzde {dip.sultan_loyalty}", interrupt=True)
        self.audio.speak(f"Durum: {dip.get_loyalty_description()}", interrupt=False)
        self.audio.speak(f"Padişah Lütfu: yüzde {dip.sultan_favor}", interrupt=False)
    
    def _announce_neighbor_status(self):
        """Komşu durumlarını duyur"""
        gm = self.screen_manager.game_manager
        if not gm:
            return
        dip = gm.diplomacy
        self.audio.speak("Komşu Beylikler:", interrupt=True)
        for neighbor, relation in dip.neighbor_relations.items():
            status = "Dost" if relation >= 50 else "Nötr" if relation >= 0 else "Düşman"
            self.audio.speak(f"{neighbor}: {status}, ilişki yüzde {relation}", interrupt=False)
    
    def _announce_next_panel(self):
        """Sıradaki paneli duyur"""
        if not hasattr(self, '_current_panel'):
            self._current_panel = 0
        
        panels = [self.sultan_panel, self.neighbors_panel, self.missions_panel]
        self._current_panel = (self._current_panel + 1) % len(panels)
        panels[self._current_panel].announce_content()
    
    def update(self, dt: float):
        self._update_panels()
    
    def draw(self, surface: pygame.Surface):
        # Başlık
        header_font = self.get_header_font()
        title = header_font.render("🤝 DİPLOMASİ", True, COLORS['gold'])
        surface.blit(title, (20, 20))
        
        # Paneller
        self.sultan_panel.draw(surface)
        self.neighbors_panel.draw(surface)
        self.missions_panel.draw(surface)
        
        # Eylem menüsü başlığı
        small_font = pygame.font.Font(None, FONTS['subheader'])
        action_title = small_font.render("Diplomatik Eylemler", True, COLORS['gold'])
        surface.blit(action_title, (440, 340))
        self.action_menu.draw(surface)
        
        # Sadakat göstergesi
        self._draw_loyalty_bar(surface)
        
        # Geri butonu
        self.back_button.draw(surface)
    
    def _draw_loyalty_bar(self, surface: pygame.Surface):
        """Sadakat göstergesini çiz"""
        gm = self.screen_manager.game_manager
        if not gm:
            return
        
        rect = pygame.Rect(860, 80, 380, 60)
        pygame.draw.rect(surface, COLORS['panel_bg'], rect, border_radius=10)
        pygame.draw.rect(surface, COLORS['panel_border'], rect, width=2, border_radius=10)
        
        # Progress bar
        loyalty = gm.diplomacy.sultan_loyalty
        bar_width = int((rect.width - 40) * (loyalty / 100))
        
        # Renk (düşükse kırmızı, yüksekse yeşil)
        if loyalty < 30:
            color = COLORS['danger']
        elif loyalty < 60:
            color = COLORS['warning']
        else:
            color = COLORS['success']
        
        bar_rect = pygame.Rect(rect.x + 20, rect.y + 30, bar_width, 15)
        pygame.draw.rect(surface, color, bar_rect, border_radius=5)
        
        # Label
        font = pygame.font.Font(None, FONTS['small'])
        label = font.render(f"Padişah Sadakati: %{loyalty}", True, COLORS['text'])
        surface.blit(label, (rect.x + 20, rect.y + 10))
    
    def _send_tribute(self, amount: int):
        """Haraç gönder"""
        gm = self.screen_manager.game_manager
        if gm:
            gm.diplomacy.send_tribute_to_sultan(amount, gm.economy)
            self._update_panels()
    
    def _send_envoy(self, target: str):
        """Elçi gönder"""
        gm = self.screen_manager.game_manager
        if gm:
            gm.diplomacy.send_envoy(target)
            self._update_panels()
    
    def _go_back(self):
        """Geri dön"""
        self.screen_manager.change_screen(ScreenType.PROVINCE_VIEW)
