# -*- coding: utf-8 -*-
"""
Osmanlı Eyalet Yönetim Simülasyonu - Ekonomi Ekranı
"""

import pygame
from ui.screen_manager import BaseScreen, ScreenType
from ui.components import Button, Panel, ProgressBar, MenuList
from config import COLORS, FONTS, SCREEN_WIDTH, SCREEN_HEIGHT


class EconomyScreen(BaseScreen):
    """Ekonomi yönetim ekranı"""
    
    def __init__(self, screen_manager):
        super().__init__(screen_manager)
        
        # Paneller
        self.income_panel = Panel(20, 80, 380, 280, "Gelirler")
        self.expense_panel = Panel(420, 80, 380, 280, "Giderler")
        self.resources_panel = Panel(820, 80, 420, 280, "Kaynaklar")
        
        # Vergi ayar menüsü
        self.tax_menu = MenuList(
            x=20,
            y=400,
            width=380,
            item_height=45
        )
        self._setup_tax_menu()
        
        # Geri butonu
        self.back_button = Button(
            x=20,
            y=SCREEN_HEIGHT - 70,
            width=150,
            height=50,
            text="Geri",
            shortcut="backspace",
            callback=self._go_back
        )
        
        # Fontlar
        self._header_font = None
    
    def _setup_tax_menu(self):
        """Vergi menüsünü ayarla"""
        self.tax_menu.clear()
        self.tax_menu.add_item("Vergiyi Artır (+5%)", self._increase_tax, "plus")
        self.tax_menu.add_item("Vergiyi Azalt (-5%)", self._decrease_tax, "minus")
    
    def get_header_font(self):
        if self._header_font is None:
            self._header_font = pygame.font.Font(None, FONTS['header'])
        return self._header_font
    
    def on_enter(self):
        self._update_panels()
    
    def announce_screen(self):
        self.audio.announce_screen_change("Ekonomi Yönetimi")
        gm = self.screen_manager.game_manager
        if gm:
            gm.economy.announce_summary()
    
    def _update_panels(self):
        """Panelleri güncelle"""
        gm = self.screen_manager.game_manager
        if not gm:
            return
        
        eco = gm.economy
        
        # Gelir paneli
        self.income_panel.clear()
        self.income_panel.add_item("Vergi Geliri", f"{eco.income.tax:,}")
        self.income_panel.add_item("Ticaret Geliri", f"{eco.income.trade:,}")
        self.income_panel.add_item("Haraç Geliri", f"{eco.income.tribute:,}")
        self.income_panel.add_item("", "")
        self.income_panel.add_item("TOPLAM GELİR", f"{eco.income.total:,}")
        
        # Gider paneli
        self.expense_panel.clear()
        self.expense_panel.add_item("Askeri Harcama", f"{eco.expense.military:,}")
        self.expense_panel.add_item("Bina Bakımı", f"{eco.expense.buildings:,}")
        self.expense_panel.add_item("Padişaha Haraç", f"{eco.expense.tribute_to_sultan:,}")
        self.expense_panel.add_item("", "")
        self.expense_panel.add_item("TOPLAM GİDER", f"{eco.expense.total:,}")
        
        # Kaynak paneli
        self.resources_panel.clear()
        self.resources_panel.add_item("Altın", f"{eco.resources.gold:,}")
        self.resources_panel.add_item("Zahire", f"{eco.resources.food:,}")
        self.resources_panel.add_item("Kereste", f"{eco.resources.wood:,}")
        self.resources_panel.add_item("Demir", f"{eco.resources.iron:,}")
        self.resources_panel.add_item("", "")
        self.resources_panel.add_item("Vergi Oranı", f"%{int(eco.tax_rate * 100)}")
    
    def handle_event(self, event) -> bool:
        if self.tax_menu.handle_event(event):
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
                    gm.economy.announce_summary()
                return True
            
            # Tab - Paneller arası geçiş
            if event.key == pygame.K_TAB:
                self._announce_next_panel()
                return True
        
        return False
    
    def _announce_next_panel(self):
        """Sıradaki paneli duyur"""
        if not hasattr(self, '_current_panel'):
            self._current_panel = 0
        
        panels = [self.income_panel, self.expense_panel, self.resources_panel]
        self._current_panel = (self._current_panel + 1) % len(panels)
        panels[self._current_panel].announce_content()
    
    def update(self, dt: float):
        self._update_panels()
    
    def draw(self, surface: pygame.Surface):
        # Başlık
        header_font = self.get_header_font()
        title = header_font.render("EKONOMI YONETIMI", True, COLORS['gold'])
        surface.blit(title, (20, 20))
        
        # Paneller
        self.income_panel.draw(surface)
        self.expense_panel.draw(surface)
        self.resources_panel.draw(surface)
        
        # Net gelir göstergesi
        self._draw_net_indicator(surface)
        
        # Vergi menüsü
        small_font = pygame.font.Font(None, FONTS['subheader'])
        tax_title = small_font.render("Vergi Ayarları", True, COLORS['gold'])
        surface.blit(tax_title, (20, 370))
        self.tax_menu.draw(surface)
        
        # Vergi etki bilgisi
        self._draw_tax_info(surface)
        
        # Geri butonu
        self.back_button.draw(surface)
    
    def _draw_net_indicator(self, surface: pygame.Surface):
        """Net gelir göstergesini çiz"""
        gm = self.screen_manager.game_manager
        if not gm:
            return
        
        net = gm.economy.income.total - gm.economy.expense.total
        
        rect = pygame.Rect(420, 380, 380, 80)
        pygame.draw.rect(surface, COLORS['panel_bg'], rect, border_radius=10)
        
        color = COLORS['success'] if net >= 0 else COLORS['danger']
        pygame.draw.rect(surface, color, rect, width=3, border_radius=10)
        
        font = pygame.font.Font(None, FONTS['subheader'])
        label = font.render("Net Gelir/Tur:", True, COLORS['text'])
        surface.blit(label, (rect.x + 20, rect.y + 15))
        
        value_font = pygame.font.Font(None, FONTS['header'])
        sign = "+" if net >= 0 else ""
        value = value_font.render(f"{sign}{net:,}", True, color)
        surface.blit(value, (rect.x + 20, rect.y + 45))
    
    def _draw_tax_info(self, surface: pygame.Surface):
        """Vergi etki bilgisini çiz"""
        gm = self.screen_manager.game_manager
        if not gm:
            return
        
        happiness_effect = gm.economy.get_tax_happiness_effect()
        
        rect = pygame.Rect(420, 480, 380, 100)
        pygame.draw.rect(surface, COLORS['panel_bg'], rect, border_radius=10)
        pygame.draw.rect(surface, COLORS['panel_border'], rect, width=2, border_radius=10)
        
        font = pygame.font.Font(None, FONTS['body'])
        
        # Mevcut vergi
        tax_text = font.render(
            f"Mevcut Vergi: %{int(gm.economy.tax_rate * 100)}", 
            True, COLORS['text']
        )
        surface.blit(tax_text, (rect.x + 20, rect.y + 15))
        
        # Memnuniyet etkisi
        effect_color = COLORS['success'] if happiness_effect >= 0 else COLORS['danger']
        sign = "+" if happiness_effect >= 0 else ""
        effect_text = font.render(
            f"Memnuniyet Etkisi: {sign}{happiness_effect}", 
            True, effect_color
        )
        surface.blit(effect_text, (rect.x + 20, rect.y + 45))
        
        # Uyarı
        if gm.economy.tax_rate > 0.25:
            warning = font.render("⚠ Yüksek vergi isyan riski!", True, COLORS['danger'])
            surface.blit(warning, (rect.x + 20, rect.y + 70))
    
    def _increase_tax(self):
        """Vergiyi artır"""
        gm = self.screen_manager.game_manager
        if gm:
            new_rate = min(0.40, gm.economy.tax_rate + 0.05)
            gm.economy.set_tax_rate(new_rate)
            self._update_panels()
    
    def _decrease_tax(self):
        """Vergiyi azalt"""
        gm = self.screen_manager.game_manager
        if gm:
            new_rate = max(0.05, gm.economy.tax_rate - 0.05)
            gm.economy.set_tax_rate(new_rate)
            self._update_panels()
    
    def _go_back(self):
        """Geri dön"""
        if getattr(self.screen_manager, 'is_multiplayer_mode', False):
            self.screen_manager.change_screen(ScreenType.MULTIPLAYER_GAME)
        else:
            self.screen_manager.change_screen(ScreenType.PROVINCE_VIEW)
