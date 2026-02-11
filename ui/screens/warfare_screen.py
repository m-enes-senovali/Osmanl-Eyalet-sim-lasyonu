# -*- coding: utf-8 -*-
"""
Osmanlı Eyalet Yönetim Simülasyonu - Savaş Ekranı
"""

import pygame
from ui.screen_manager import BaseScreen, ScreenType
from ui.components import Button, Panel, MenuList
from config import COLORS, FONTS, SCREEN_WIDTH, SCREEN_HEIGHT


class WarfareScreen(BaseScreen):
    """Savaş yönetim ekranı"""
    
    def __init__(self, screen_manager):
        super().__init__(screen_manager)
        
        # Paneller
        self.status_panel = Panel(20, 80, 400, 200, "Savaş Durumu")
        self.battles_panel = Panel(20, 300, 400, 180, "Aktif Savaşlar")
        
        # Eylem menüsü
        self.action_menu = MenuList(
            x=450,
            y=100,
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
        self.audio.play_game_sound('military', 'march')
    
    def announce_screen(self):
        gm = self.screen_manager.game_manager
        title_suffix = ""
        if gm and gm.player:
            title_suffix = f" - {gm.player.get_full_title()}"
        self.audio.announce_screen_change(f"Savaş Yönetimi{title_suffix}")
        if gm:
            gm.warfare.announce_status()
    
    def _setup_action_menu(self):
        """Eylem menüsünü ayarla"""
        self.action_menu.clear()
        gm = self.screen_manager.game_manager
        if not gm:
            return
        
        # Savaş başlatılabilir mi?
        can_war, reason = gm.warfare.can_start_war(gm.turn_count)
        
        if can_war:
            # Kadın karakter kontrolü
            is_female = gm.player and gm.player.gender.value == 'female'
            
            # Komşulara akın/kuşatma seçenekleri
            for neighbor in gm.diplomacy.neighbors.keys():
                if is_female:
                    # Kadın vali akına bizzat katılamaz, vekil gönderir
                    self.action_menu.add_item(
                        f"Akına Vekil Gönder: {neighbor} (300 altın)",
                        lambda n=neighbor: self._start_raid(n, personal=False)
                    )
                else:
                    # Erkek vali bizzat liderlik edebilir
                    self.action_menu.add_item(
                        f"Akın (Bizzat): {neighbor} (+%20 bonus, 300 altın)",
                        lambda n=neighbor: self._start_raid(n, personal=True)
                    )
            
            self.action_menu.add_item("", None)  # Ayırıcı
            
            for neighbor in gm.diplomacy.neighbors.keys():
                self.action_menu.add_item(
                    f"Kuşatma: {neighbor} (1500 altın)",
                    lambda n=neighbor: self._start_siege(n)
                )
            
            # Deniz akını - sadece kıyı eyaletlerinde
            if gm.province.is_coastal:
                self.action_menu.add_item("", None)  # Ayırıcı
                fleet_power = gm.naval.get_fleet_power()
                warship_count = sum(1 for s in gm.naval.ships if s.get_definition().is_warship)
                
                if warship_count > 0:
                    for neighbor in gm.diplomacy.neighbors.keys():
                        self.action_menu.add_item(
                            f"Deniz Akini: {neighbor} (500 altin)",
                            lambda n=neighbor: self._start_naval_raid(n)
                        )
                else:
                    self.action_menu.add_item("Deniz akini icin savas gemisi gerekli", None)
        else:
            self.action_menu.add_item(f"⚠ {reason}", None)
        
        self.action_menu.add_item("", None)
        self.action_menu.add_item("F1: Durumu oku", None)
    
    def _update_panels(self):
        """Panelleri güncelle"""
        gm = self.screen_manager.game_manager
        if not gm:
            return
        
        war = gm.warfare
        mil = gm.military
        
        # Durum paneli
        self.status_panel.clear()
        self.status_panel.add_item("Toplam Asker", f"{mil.get_total_soldiers()}")
        self.status_panel.add_item("Askeri Güç", f"{mil.get_total_power()}")
        self.status_panel.add_item("Moral", f"%{mil.morale}")
        self.status_panel.add_item("Deneyim", f"%{mil.experience}")
        self.status_panel.add_item("Savaş Yorgunluğu", f"%{war.war_weariness}")
        
        # Barış dönemi kontrolü
        if gm.turn_count < war.EARLY_GAME_PROTECTION:
            remaining = war.EARLY_GAME_PROTECTION - gm.turn_count
            self.status_panel.add_item("Barış Dönemi", f"{remaining} tur kaldı")
        
        # Aktif savaşlar paneli
        self.battles_panel.clear()
        if war.active_battles:
            for battle in war.active_battles:
                self.battles_panel.add_item(
                    battle.defender_name,
                    battle.get_status_text()
                )
        else:
            self.battles_panel.add_item("Aktif savaş yok", "Barış zamanı")
    
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
                    gm.warfare.announce_status()
                return True
            
            # Tab - Panel değiştir
            if event.key == pygame.K_TAB:
                self._announce_next_panel()
                return True
        
        return False
    
    def _start_raid(self, target: str, personal: bool = True):
        """Akın başlat - personal=True ise bizzat liderlik"""
        gm = self.screen_manager.game_manager
        if not gm:
            return
        
        # Erkek karakter bizzat liderlik ederse +%20 bonus
        raid_bonus = 0.20 if personal else 0.0
        
        success, message = gm.warfare.start_raid(
            target, gm.military, gm.economy, gm.turn_count, raid_bonus
        )
        
        if personal:
            self.audio.speak("Bizzat akını yönetiyorsunuz! " + message, interrupt=True)
        else:
            self.audio.speak("Vekiliniz akını yönetiyor. " + message, interrupt=True)
        
        self._update_panels()
        self._setup_action_menu()
    
    def _start_siege(self, target: str):
        """Kuşatma başlat"""
        gm = self.screen_manager.game_manager
        if not gm:
            return
        
        success, message = gm.warfare.start_siege(target, gm.military, gm.economy, gm.turn_count)
        self.audio.speak(message, interrupt=True)
        self._update_panels()
        self._setup_action_menu()
    
    def _start_naval_raid(self, target: str):
        """Deniz akını başlat"""
        gm = self.screen_manager.game_manager
        if not gm:
            return
        
        success, message = gm.warfare.start_naval_raid(
            target, gm.naval, gm.economy, gm.turn_count, gm.province.is_coastal
        )
        self.audio.speak(message, interrupt=True)
        self._update_panels()
        self._setup_action_menu()
    
    def _announce_next_panel(self):
        """Sıradaki paneli duyur"""
        if not hasattr(self, '_current_panel'):
            self._current_panel = 0
        
        panels = [self.status_panel, self.battles_panel]
        self._current_panel = (self._current_panel + 1) % len(panels)
        panels[self._current_panel].announce_content()
    
    def update(self, dt: float):
        self._update_panels()
    
    def draw(self, surface: pygame.Surface):
        # Başlık
        header_font = self.get_header_font()
        title = header_font.render("SAVAS YONETIMI", True, COLORS['gold'])
        surface.blit(title, (20, 20))
        
        # Paneller
        self.status_panel.draw(surface)
        self.battles_panel.draw(surface)
        
        # Eylem menüsü başlığı
        small_font = pygame.font.Font(None, FONTS['subheader'])
        action_title = small_font.render("Savaş Eylemleri", True, COLORS['gold'])
        surface.blit(action_title, (450, 75))
        self.action_menu.draw(surface)
        
        # Geri butonu
        self.back_button.draw(surface)
    
    def _go_back(self):
        self.screen_manager.change_screen(ScreenType.PROVINCE_VIEW)
