# -*- coding: utf-8 -*-
"""
Osmanlı Eyalet Yönetim Simülasyonu - Halk/Nüfus Ekranı
"""

import pygame
from ui.screen_manager import BaseScreen, ScreenType
from ui.components import Button, Panel, ProgressBar, MenuList
from config import COLORS, FONTS, SCREEN_WIDTH, SCREEN_HEIGHT, get_font


class PopulationScreen(BaseScreen):
    """Halk yönetim ekranı"""
    
    def __init__(self, screen_manager):
        super().__init__(screen_manager)
        
        # Paneller
        self.population_panel = Panel(20, 80, 400, 280, "Nüfus Dağılımı")
        self.status_panel = Panel(440, 80, 400, 280, "Halk Durumu")
        
        # İlerleme çubukları
        self.happiness_bar = ProgressBar(
            20, 400, 400, 35,
            label="Memnuniyet",
            color=COLORS['success']
        )
        self.health_bar = ProgressBar(
            20, 450, 400, 35,
            label="Sağlık",
            color=(100, 200, 255)
        )
        self.unrest_bar = ProgressBar(
            20, 500, 400, 35,
            label="Huzursuzluk",
            color=COLORS['danger']
        )
        
        # Eylem menüsü
        self.action_menu = MenuList(
            x=860,
            y=120,
            width=380,
            item_height=45
        )
        self.menu_mode = "main"
        
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
            self._header_font = get_font(FONTS['header'])
        return self._header_font
    
    def on_enter(self):
        self._update_panels()
        self._setup_main_menu()
    
    def announce_screen(self):
        self.audio.announce_screen_change("Halk Yönetimi")
        gm = self.screen_manager.game_manager
        if gm:
            gm.population.announce_status()
            
    def _setup_main_menu(self):
        """Ana eylem menüsünü ayarla"""
        self.menu_mode = "main"
        self.action_menu.clear()
        self.action_menu.add_item("1. Göç Politikası Belirle", self._setup_migration_menu, "1")
        self.action_menu.add_item("2. Şehirlileşme (Meslek Dönüşümü)", self._setup_profession_menu, "2")
        
    def _setup_migration_menu(self):
        """Göç politikası menüsünü ayarla"""
        self.menu_mode = "migration"
        self.action_menu.clear()
        self.audio.speak("Göç Politikası seçin.", interrupt=True)
        
        self.action_menu.add_item("<- Geri", self._setup_main_menu, "escape")
        self.action_menu.add_item("", None)
        
        policies = [
            ("open", "Açık Kapı (Nüfus++ | İsyan++)"),
            ("selective", "Seçici (Dengeli)"),
            ("restricted", "Kısıtlı (Nüfus+ | Huzur+)"),
            ("closed", "Kapalı (Nüfus Durur | Huzur++)")
        ]
        
        for i, (policy_id, text) in enumerate(policies):
            self.action_menu.add_item(
                f"{i+1}. {text}", 
                lambda p=policy_id: self._set_migration_policy(p),
                str(i+1)
            )
            
    def _setup_profession_menu(self):
        """Meslek dönüştürme menüsünü ayarla"""
        self.menu_mode = "profession"
        self.action_menu.clear()
        
        gm = self.screen_manager.game_manager
        if not gm:
            return
            
        cost_per_100 = (5 - gm.population.education_level) * 50
        self.audio.speak(f"Meslek dönüşümü. 100 kişi için {cost_per_100} altın.", interrupt=True)
        
        self.action_menu.add_item("<- Geri", self._setup_main_menu, "escape")
        self.action_menu.add_item("", None)
        
        self.action_menu.add_item(f"1. Çiftçi -> Zanaatkar ({cost_per_100} altın)", 
            lambda: self._convert_profession("farmers", "artisans", 100), "1")
        self.action_menu.add_item(f"2. Çiftçi -> Tüccar ({cost_per_100} altın)", 
            lambda: self._convert_profession("farmers", "merchants", 100), "2")
        self.action_menu.add_item(f"3. Zanaatkar -> Tüccar ({cost_per_100} altın)", 
            lambda: self._convert_profession("artisans", "merchants", 100), "3")
        self.action_menu.add_item(f"4. Tüccar -> Ulema ({cost_per_100} altın)", 
            lambda: self._convert_profession("merchants", "scholars", 100), "4")

    def _set_migration_policy(self, policy: str):
        gm = self.screen_manager.game_manager
        if gm:
            gm.population.set_migration_policy(policy)
            self._update_panels()
            self._setup_main_menu()
            
    def _convert_profession(self, from_group: str, to_group: str, count: int):
        gm = self.screen_manager.game_manager
        if gm:
            gm.population.convert_profession(from_group, to_group, count, economy_system=gm.economy)
            self._update_panels()
    
    def _update_panels(self):
        """Panelleri güncelle"""
        gm = self.screen_manager.game_manager
        if not gm:
            return
        
        pop = gm.population
        
        # Nüfus paneli
        self.population_panel.clear()
        self.population_panel.add_item("Çiftçiler", f"{pop.population.farmers:,}")
        self.population_panel.add_item("Tüccarlar", f"{pop.population.merchants:,}")
        self.population_panel.add_item("Zanaatkarlar", f"{pop.population.artisans:,}")
        self.population_panel.add_item("Asker Aileleri", f"{pop.population.soldiers:,}")
        self.population_panel.add_item("", "")
        self.population_panel.add_item("TOPLAM", f"{pop.population.total:,}")
        
        # Durum paneli
        self.status_panel.clear()
        self.status_panel.add_item("Memnuniyet", f"%{pop.happiness}")
        self.status_panel.add_item("Sağlık", f"%{pop.health}")
        self.status_panel.add_item("Huzursuzluk", f"%{pop.unrest}")
        self.status_panel.add_item("", "")
        self.status_panel.add_item("Büyüme Oranı", f"%{pop.growth_rate * 100:.1f}")
        self.status_panel.add_item("Yiyecek Tüketimi", f"{pop.food_consumption}/tur")
        
        if pop.active_revolt:
            self.status_panel.add_item("⚠ DURUM", "AKTİF İSYAN!")
        
        # İlerleme çubukları
        self.happiness_bar.set_value(pop.happiness)
        self.health_bar.set_value(pop.health)
        self.unrest_bar.set_value(pop.unrest)
    
    def handle_event(self, event) -> bool:
        if self.action_menu.handle_event(event):
            return True
            
        if self.back_button.handle_event(event):
            return True
        
        if event.type == pygame.KEYDOWN:
            # Backspace veya Escape - Geri dön
            if event.key in (pygame.K_BACKSPACE, pygame.K_ESCAPE):
                if self.menu_mode != "main":
                    self._setup_main_menu()
                else:
                    self._go_back()
                return True
            
            # F1 - Özet
            if event.key == pygame.K_F1:
                gm = self.screen_manager.game_manager
                if gm:
                    gm.population.announce_status()
                return True
            
            # Tab - Paneller ve çubuklar arası
            if event.key == pygame.K_TAB:
                self._announce_next_item()
                return True
        
        return False
    
    def _announce_next_item(self):
        """Sıradaki öğeyi duyur"""
        if not hasattr(self, '_current_item'):
            self._current_item = 0
        
        items = [
            ('panel', self.population_panel),
            ('panel', self.status_panel),
            ('bar', self.happiness_bar),
            ('bar', self.health_bar),
            ('bar', self.unrest_bar)
        ]
        
        self._current_item = (self._current_item + 1) % len(items)
        item_type, item = items[self._current_item]
        
        if item_type == 'panel':
            item.announce_content()
        else:
            item.announce()
    
    def update(self, dt: float):
        self._update_panels()
    
    def draw(self, surface: pygame.Surface):
        # Başlık
        header_font = self.get_header_font()
        title = header_font.render("HALK YONETIMI", True, COLORS['gold'])
        surface.blit(title, (20, 20))
        
        # Paneller
        self.population_panel.draw(surface)
        self.status_panel.draw(surface)
        
        # İlerleme çubukları
        self.happiness_bar.draw(surface)
        self.health_bar.draw(surface)
        self.unrest_bar.draw(surface)
        
        # Etkiler bilgisi
        self._draw_modifiers(surface)
        
        # Eylem Menüsü
        small_font = get_font(FONTS['subheader'])
        menu_title = small_font.render("Halk Eylemleri", True, COLORS['gold'])
        surface.blit(menu_title, (860, 80))
        self.action_menu.draw(surface)
        
        # İsyan uyarısı
        gm = self.screen_manager.game_manager
        if gm and gm.population.active_revolt:
            self._draw_revolt_warning(surface)
        
        # Geri butonu
        self.back_button.draw(surface)
    
    def _draw_modifiers(self, surface: pygame.Surface):
        """Memnuniyet etkilerini göster"""
        gm = self.screen_manager.game_manager
        if not gm:
            return
        
        rect = pygame.Rect(440, 380, 400, 180)
        pygame.draw.rect(surface, COLORS['panel_bg'], rect, border_radius=10)
        pygame.draw.rect(surface, COLORS['panel_border'], rect, width=2, border_radius=10)
        
        font = get_font(FONTS['body'])
        small_font = get_font(FONTS['small'])
        
        # Başlık
        title = font.render("Memnuniyet Etkenleri", True, COLORS['gold'])
        surface.blit(title, (rect.x + 20, rect.y + 15))
        
        # Etkiler listesi
        modifiers = gm.population.happiness_modifiers
        y = rect.y + 50
        
        if modifiers:
            for source, value in modifiers.items():
                source_names = {
                    'food_shortage': 'Yiyecek Kıtlığı',
                    'event': 'Olay Etkisi',
                    'tax': 'Vergi Etkisi'
                }
                name = source_names.get(source, source)
                color = COLORS['success'] if value >= 0 else COLORS['danger']
                sign = "+" if value >= 0 else ""
                
                text = small_font.render(f"{name}: {sign}{value}", True, color)
                surface.blit(text, (rect.x + 20, y))
                y += 25
        else:
            text = small_font.render("Özel etken yok", True, COLORS['text'])
            surface.blit(text, (rect.x + 20, y))
        
        # Tavsiyeler
        y = rect.y + 120
        tips = []
        
        if gm.population.happiness < 50:
            tips.append("💡 Vergiyi düşürmeyi deneyin")
        if gm.population.health < 60:
            tips.append("💡 Darüşşifa (hastane) inşa edin")
        if gm.population.unrest > 50:
            tips.append("💡 Askeri güç artırın")
        
        for tip in tips[:2]:
            tip_text = small_font.render(tip, True, COLORS['warning'])
            surface.blit(tip_text, (rect.x + 20, y))
            y += 22
    
    def _draw_revolt_warning(self, surface: pygame.Surface):
        """İsyan uyarısı çiz"""
        rect = pygame.Rect(
            (SCREEN_WIDTH - 500) // 2,
            SCREEN_HEIGHT - 150,
            500,
            60
        )
        
        pygame.draw.rect(surface, COLORS['danger'], rect, border_radius=10)
        pygame.draw.rect(surface, (255, 200, 200), rect, width=3, border_radius=10)
        
        font = get_font(FONTS['subheader'])
        text = font.render("⚠ HALK İSYAN HALİNDE! ⚠", True, COLORS['text'])
        text_rect = text.get_rect(center=rect.center)
        surface.blit(text, text_rect)
    
    def _go_back(self):
        """Geri dön"""
        if getattr(self.screen_manager, 'is_multiplayer_mode', False):
            self.screen_manager.change_screen(ScreenType.MULTIPLAYER_GAME)
        else:
            self.screen_manager.change_screen(ScreenType.PROVINCE_VIEW)
