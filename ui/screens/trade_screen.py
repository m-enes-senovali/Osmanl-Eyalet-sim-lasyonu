# -*- coding: utf-8 -*-
"""
Osmanlı Eyalet Yönetim Simülasyonu - Ticaret Ekranı
"""

import pygame
from ui.screen_manager import BaseScreen, ScreenType
from ui.components import Button, Panel, MenuList
from config import COLORS, FONTS, SCREEN_WIDTH, SCREEN_HEIGHT


class TradeScreen(BaseScreen):
    """Ticaret yönetim ekranı"""
    
    def __init__(self, screen_manager):
        super().__init__(screen_manager)
        
        # Paneller
        self.status_panel = Panel(20, 80, 400, 180, "Ticaret Durumu")
        self.caravans_panel = Panel(20, 280, 400, 200, "Aktif Kervanlar")
        
        # Eylem menüsü
        self.action_menu = MenuList(
            x=450,
            y=100,
            width=400,
            item_height=40
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
        self.audio.play_ambient('market')
    
    def announce_screen(self):
        self.audio.announce_screen_change("Ticaret Yönetimi")
        gm = self.screen_manager.game_manager
        if gm:
            gm.trade.announce_status()
    
    def _setup_action_menu(self):
        """Eylem menüsünü ayarla"""
        self.action_menu.clear()
        gm = self.screen_manager.game_manager
        if not gm:
            return
        
        trade = gm.trade
        available_routes = trade.get_available_routes()
        
        # Mevcut yollara kervan gönder
        for route in available_routes:
            info = trade.get_route_info(route.route_id)
            risk_text = "Düşük" if route.risk_factor < 0.2 else "Orta" if route.risk_factor < 0.3 else "Yüksek"
            self.action_menu.add_item(
                f"{route.name} ({info['cost']} altın, {info['time']} tur)",
                lambda r=route.route_id: self._send_caravan(r)
            )
        
        if not trade.has_port:
            self.action_menu.add_item("", None)
            self.action_menu.add_item("⚠ Deniz yolları için Tersane gerekli", None)
        
        self.action_menu.add_item("", None)
        self.action_menu.add_item("R: Tüm yolları oku", None)
        self.action_menu.add_item("F1: Durumu oku", None)
    
    def _update_panels(self):
        """Panelleri güncelle"""
        gm = self.screen_manager.game_manager
        if not gm:
            return
        
        trade = gm.trade
        
        # Durum paneli
        self.status_panel.clear()
        self.status_panel.add_item("Aktif Kervan", f"{len(trade.active_caravans)}")
        self.status_panel.add_item("Toplam Gelir", f"{trade.total_trade_income} altın")
        self.status_panel.add_item("Başarılı", f"{trade.caravans_completed}")
        self.status_panel.add_item("Kayıp", f"{trade.caravans_lost}")
        
        if trade.has_port:
            self.status_panel.add_item("Liman", f"Aktif (Lv.{trade.port_level})")
        else:
            self.status_panel.add_item("Liman", "Yok (Tersane gerekli)")
        
        if trade.trade_agreements:
            partners = ", ".join(trade.trade_agreements.keys())
            self.status_panel.add_item("Anlaşmalar", partners[:20])
        
        # Kervanlar paneli
        self.caravans_panel.clear()
        if trade.active_caravans:
            for caravan in trade.active_caravans:
                self.caravans_panel.add_item(
                    caravan.route.name,
                    f"{caravan.turns_remaining} tur kaldı"
                )
        else:
            self.caravans_panel.add_item("Aktif kervan yok", "Yol seçerek kervan gönderin")
    
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
            
            # F1 - Durum özeti
            if event.key == pygame.K_F1:
                gm = self.screen_manager.game_manager
                if gm:
                    gm.trade.announce_status()
                return True
            
            # R - Yolları oku
            if event.key == pygame.K_r:
                gm = self.screen_manager.game_manager
                if gm:
                    gm.trade.announce_routes()
                return True
            
            # Tab - Panel değiştir
            if event.key == pygame.K_TAB:
                self._announce_next_panel()
                return True
        
        return False
    
    def _send_caravan(self, route_id: str):
        """Kervan gönder"""
        gm = self.screen_manager.game_manager
        if not gm:
            return
        
        gm.trade.send_caravan(route_id, gm.economy)
        self.audio.play_game_sound('economy', 'trade')
        self._update_panels()
        self._setup_action_menu()
    
    def _announce_next_panel(self):
        """Sıradaki paneli duyur"""
        if not hasattr(self, '_current_panel'):
            self._current_panel = 0
        
        panels = [self.status_panel, self.caravans_panel]
        self._current_panel = (self._current_panel + 1) % len(panels)
        panels[self._current_panel].announce_content()
    
    def update(self, dt: float):
        self._update_panels()
    
    def draw(self, surface: pygame.Surface):
        # Başlık
        header_font = self.get_header_font()
        title = header_font.render("🛤️ TİCARET YÖNETİMİ", True, COLORS['gold'])
        surface.blit(title, (20, 20))
        
        # Paneller
        self.status_panel.draw(surface)
        self.caravans_panel.draw(surface)
        
        # Eylem menüsü başlığı
        small_font = pygame.font.Font(None, FONTS['subheader'])
        action_title = small_font.render("Kervan Gönder", True, COLORS['gold'])
        surface.blit(action_title, (450, 75))
        self.action_menu.draw(surface)
        
        # Geri butonu
        self.back_button.draw(surface)
    
    def _go_back(self):
        self.screen_manager.change_screen(ScreenType.PROVINCE_VIEW)
