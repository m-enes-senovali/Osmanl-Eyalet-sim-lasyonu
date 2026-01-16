# -*- coding: utf-8 -*-
"""
Osmanlı Eyalet Yönetim Simülasyonu - Askeri Ekran
"""

import pygame
from ui.screen_manager import BaseScreen, ScreenType
from ui.components import Button, Panel, MenuList
from game.systems.military import UnitType, UNIT_DEFINITIONS
from config import COLORS, FONTS, SCREEN_WIDTH, SCREEN_HEIGHT


class MilitaryScreen(BaseScreen):
    """Askeri yönetim ekranı"""
    
    def __init__(self, screen_manager):
        super().__init__(screen_manager)
        
        # Paneller
        self.army_panel = Panel(20, 80, 450, 350, "Ordu Durumu")
        self.training_panel = Panel(490, 80, 380, 200, "Eğitim Kuyruğu")
        self.stats_panel = Panel(490, 300, 380, 130, "İstatistikler")
        
        # Birlik toplama menüsü
        self.recruit_menu = MenuList(
            x=20,
            y=460,
            width=450,
            item_height=40
        )
        self._setup_recruit_menu()
        
        # Eylem butonları
        self.fight_button = Button(
            x=490,
            y=460,
            width=180,
            height=50,
            text="Eşkıya Bastır",
            shortcut="f",
            callback=self._fight_bandits
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
    
    def _setup_recruit_menu(self):
        """Asker toplama menüsünü ayarla"""
        self.recruit_menu.clear()
        for unit_type in UnitType:
            stats = UNIT_DEFINITIONS[unit_type]
            self.recruit_menu.add_item(
                f"{stats.name_tr} Topla (10)",
                lambda ut=unit_type: self._recruit(ut, 10)
            )
    
    def get_header_font(self):
        if self._header_font is None:
            self._header_font = pygame.font.Font(None, FONTS['header'])
        return self._header_font
    
    def on_enter(self):
        self._update_panels()
    
    def announce_screen(self):
        self.audio.announce_screen_change("Askeri Yönetim")
        gm = self.screen_manager.game_manager
        if gm:
            gm.military.announce_army()
    
    def _update_panels(self):
        """Panelleri güncelle"""
        gm = self.screen_manager.game_manager
        if not gm:
            return
        
        mil = gm.military
        
        # Ordu paneli
        self.army_panel.clear()
        for unit_type, count in mil.units.items():
            stats = UNIT_DEFINITIONS[unit_type]
            self.army_panel.add_item(stats.name_tr, str(count))
        self.army_panel.add_item("", "")
        self.army_panel.add_item("Toplam Asker", str(mil.get_total_soldiers()))
        self.army_panel.add_item("Toplam Güç", str(mil.get_total_power()))
        self.army_panel.add_item("Bakım Maliyeti", f"{mil.get_maintenance_cost()}/tur")
        
        # Eğitim paneli
        self.training_panel.clear()
        if mil.training_queue:
            for item in mil.training_queue:
                stats = UNIT_DEFINITIONS[item.unit_type]
                self.training_panel.add_item(
                    f"{item.count}x {stats.name_tr}",
                    f"{item.turns_remaining} tur"
                )
        else:
            self.training_panel.add_item("Eğitim yok", "")
        
        # İstatistik paneli
        self.stats_panel.clear()
        self.stats_panel.add_item("Moral", f"%{mil.morale}")
        self.stats_panel.add_item("Zaferler", str(mil.total_victories))
        self.stats_panel.add_item("Kayıplar", str(mil.total_losses))
    
    def handle_event(self, event) -> bool:
        if self.recruit_menu.handle_event(event):
            return True
        
        if self.fight_button.handle_event(event):
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
                    gm.military.announce_army()
                return True
            
            # Tab - Paneller arası
            if event.key == pygame.K_TAB:
                self._announce_next_panel()
                return True
            
            # I - Detaylı birim dökümü
            if event.key == pygame.K_i:
                self._announce_unit_breakdown()
                return True
        
        return False
    
    def _announce_unit_breakdown(self):
        """Detaylı birim dökümü"""
        gm = self.screen_manager.game_manager
        if not gm:
            return
        
        mil = gm.military
        
        # Kara kuvvetleri
        lines = []
        lines.append(f"Piyade: {mil.infantry} asker")
        lines.append(f"Süvari: {mil.cavalry} atlı")
        lines.append(f"Topçu mürettebatı: {mil.artillery_crew} kişi")
        lines.append(f"Akıncı: {mil.raiders} kişi")
        lines.append(f"Toplam kara gücü: {mil.get_total_soldiers()} asker, güç: {mil.get_total_power()}")
        
        # Toplar
        if hasattr(gm, 'artillery') and gm.artillery.cannons:
            counts = gm.artillery.get_cannon_counts()
            cannon_parts = []
            from game.systems.artillery import CannonType, CANNON_DEFINITIONS
            for ct in CannonType:
                if counts[ct] > 0:
                    cannon_parts.append(f"{counts[ct]} {CANNON_DEFINITIONS[ct].name}")
            if cannon_parts:
                lines.append(f"Toplar: {', '.join(cannon_parts)}")
                lines.append(f"Toplam top gücü: {gm.artillery.get_total_power()}")
        
        # Gemiler
        if hasattr(gm, 'naval') and gm.naval.ships:
            counts = gm.naval.get_ship_counts()
            ship_parts = []
            from game.systems.naval import ShipType, SHIP_DEFINITIONS
            for st in ShipType:
                if counts[st] > 0:
                    ship_parts.append(f"{counts[st]} {SHIP_DEFINITIONS[st].name}")
            if ship_parts:
                lines.append(f"Gemiler: {', '.join(ship_parts)}")
                lines.append(f"Filo savaş gücü: {gm.naval.get_fleet_power()}")
        
        full_text = ". ".join(lines)
        self.audio.speak(full_text, interrupt=True)
    
    def _announce_next_panel(self):
        """Sıradaki paneli duyur"""
        if not hasattr(self, '_current_panel'):
            self._current_panel = 0
        
        panels = [self.army_panel, self.training_panel, self.stats_panel]
        self._current_panel = (self._current_panel + 1) % len(panels)
        panels[self._current_panel].announce_content()
    
    def update(self, dt: float):
        self._update_panels()
    
    def draw(self, surface: pygame.Surface):
        # Başlık
        header_font = self.get_header_font()
        title = header_font.render("⚔ ASKERİ YÖNETİM", True, COLORS['gold'])
        surface.blit(title, (20, 20))
        
        # Paneller
        self.army_panel.draw(surface)
        self.training_panel.draw(surface)
        self.stats_panel.draw(surface)
        
        # Asker toplama menüsü başlığı
        small_font = pygame.font.Font(None, FONTS['subheader'])
        recruit_title = small_font.render("Asker Topla", True, COLORS['gold'])
        surface.blit(recruit_title, (20, 435))
        self.recruit_menu.draw(surface)
        
        # Butonlar
        self.fight_button.draw(surface)
        self.back_button.draw(surface)
        
        # Birim bilgileri
        self._draw_unit_info(surface)
    
    def _draw_unit_info(self, surface: pygame.Surface):
        """Seçili birim bilgilerini göster"""
        gm = self.screen_manager.game_manager
        if not gm:
            return
        
        # Bilgi kutusu
        rect = pygame.Rect(700, 460, 540, 130)
        pygame.draw.rect(surface, COLORS['panel_bg'], rect, border_radius=10)
        pygame.draw.rect(surface, COLORS['panel_border'], rect, width=2, border_radius=10)
        
        # Seçili birim
        if self.recruit_menu.items:
            selected_idx = self.recruit_menu.selected_index
            unit_type = list(UnitType)[selected_idx]
            stats = UNIT_DEFINITIONS[unit_type]
            
            font = pygame.font.Font(None, FONTS['body'])
            small_font = pygame.font.Font(None, FONTS['small'])
            
            # Birim adı
            name = font.render(stats.name_tr, True, COLORS['gold'])
            surface.blit(name, (rect.x + 20, rect.y + 15))
            
            # İstatistikler
            info_lines = [
                f"Saldırı: {stats.attack} | Savunma: {stats.defense} | Hız: {stats.speed}",
                f"Maliyet: {stats.cost_gold} Altın, {stats.cost_food} Zahire",
                f"Eğitim: {stats.train_time} tur | Bakım: {stats.maintenance}/tur"
            ]
            
            for i, line in enumerate(info_lines):
                text = small_font.render(line, True, COLORS['text'])
                surface.blit(text, (rect.x + 20, rect.y + 45 + i * 25))
    
    def _recruit(self, unit_type: UnitType, count: int):
        """Asker topla"""
        gm = self.screen_manager.game_manager
        if gm:
            gm.military.recruit(unit_type, count, gm.economy)
            self._update_panels()
    
    def _fight_bandits(self):
        """Eşkıya bastır"""
        gm = self.screen_manager.game_manager
        if gm:
            result = gm.military.fight_bandits()
            
            if result['victory']:
                self.audio.announce(
                    f"Zafer! Eşkıyalar bastırıldı. "
                    f"Kayıplar: {sum(result['losses'].values())} asker"
                )
            else:
                self.audio.announce(
                    f"Mağlubiyet! Ordu geri çekildi. "
                    f"Kayıplar: {sum(result['losses'].values())} asker"
                )
            
            self._update_panels()
    
    def _go_back(self):
        """Geri dön"""
        self.screen_manager.change_screen(ScreenType.PROVINCE_VIEW)
