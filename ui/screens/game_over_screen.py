# -*- coding: utf-8 -*-
"""
Osmanlı Eyalet Yönetim Simülasyonu - Oyun Sonu (Endgame) Ekranı
Zafer veya Mağlubiyet durumlarında oyuncuya istatistikleri ve hikayeyi gösterir.
"""

import pygame
from typing import Dict, Any
from ui.screen_manager import BaseScreen, ScreenType
from ui.components import Button, Panel, TextBlock
from config import COLORS, FONTS, SCREEN_WIDTH, SCREEN_HEIGHT, get_font

class GameOverScreen(BaseScreen):
    """Oyun bitiş ekranı (Kazandı/Kaybetti)"""
    
    def __init__(self, screen_manager):
        super().__init__(screen_manager)
        
        self.is_victory = False
        self.reason = ""
        self.stats: Dict[str, Any] = {}
        
        # Fontlar
        self._title_font = None
        self._header_font = None
        self._body_font = None
        self._small_font = None
        
        # UI Bileşenleri
        panel_width = 800
        panel_height = 500
        self.main_panel = Panel(
            x=(SCREEN_WIDTH - panel_width) // 2,
            y=(SCREEN_HEIGHT - panel_height) // 2 - 40,
            width=panel_width,
            height=panel_height,
            title=""
        )
        
        self.story_text = TextBlock(
            x=self.main_panel.rect.x + 40,
            y=self.main_panel.rect.y + 60,
            width=panel_width - 80,
            text="",
            color=COLORS['text']
        )
        
        self.btn_menu = Button(
            x=(SCREEN_WIDTH - 200) // 2,
            y=self.main_panel.rect.bottom + 20,
            width=200,
            height=50,
            text="Ana Menüye Dön",
            shortcut="return",
            callback=self._return_to_menu
        )
        
    def get_title_font(self):
        if self._title_font is None:
            self._title_font = get_font(FONTS['title'])
        return self._title_font
        
    def get_header_font(self):
        if self._header_font is None:
            self._header_font = get_font(FONTS['header'])
        return self._header_font
        
    def get_body_font(self):
        if self._body_font is None:
            self._body_font = get_font(FONTS['body'])
        return self._body_font
        
    def get_small_font(self):
        if self._small_font is None:
            self._small_font = get_font(FONTS['small'])
        return self._small_font
        
    def on_enter(self):
        """Ekrana girildiğinde GameManager'dan verileri çek."""
        gm = self.screen_manager.game_manager
        if not gm:
            return
            
        # Zafere ulaşmış mı bak (Eğer check_victory çalışıp won dondurduyse)
        victory_data = gm.check_victory()
        if victory_data and victory_data.get('won'):
            self.is_victory = True
            victories = victory_data.get('victories', [])
            v_name = victories[0]['name'] if victories else "Zafer"
            self.reason = f"Büyük başarılar elde ettiniz ({v_name})! Padişah sizi Payitaht'a çağırıp Sadrazam ilan etti."
            self.main_panel.title = "🏆 ŞANLI BİR ZAFER 🏆"
            # Müzik ekle
            self.audio.play_game_sound('ui', 'event_good')
        else:
            self.is_victory = False
            self.reason = getattr(gm, 'game_over_reason', "Eyaletin kontrolünü kaybettiniz.")
            self.main_panel.title = "☠ OYUN BİTTİ ☠"
            self.audio.play_game_sound('ui', 'event_bad')
            
        # İstatistikleri topla
        self.stats = {
            'year': gm.current_year,
            'turn': gm.turn_count,
            'gold': getattr(gm.economy.resources, 'gold', 0),
            'population': gm.population.population.total,
            'battles_won': getattr(gm.warfare, 'victories_count', 0),
            'battles_lost': getattr(gm.warfare, 'defeats_count', 0)
        }
        
        
        # İstatistik satırlarını hazırla
        self.stats_lines = [
            f"Görev Süresi: {self.stats.get('turn', 0)} tur (Yıl: {self.stats.get('year', 1520)})",
            f"Nihai Hazine: {self.stats.get('gold', 0):,} Altın",
            f"Yönetilen Nüfus: {self.stats.get('population', 0):,} Kişi",
            f"Savaş Başarıları: {self.stats.get('battles_won', 0)} Galibiyet, {self.stats.get('battles_lost', 0)} Mağlubiyet"
        ]
        self.selected_stat_index = -1  # Başlangıçta hiçbiri seçili değil
        
        # Metni güncelle
        self.story_text.set_text(self.reason)
        
        # Ekran okuyucu
        self.announce_screen()

    def announce_screen(self):
        title = "Zafer Kazandınız" if self.is_victory else "Oyun Bitti"
        self.audio.announce_screen_change(f"{title}")
        self.audio.speak(self.reason, interrupt=False)
        self.audio.speak("İstatistiklerinizi okumak veya Ana menüye dönmek için Enter'a basın.", interrupt=False)
        
    def handle_event(self, event) -> bool:
        if self.btn_menu.handle_event(event):
            return True
            
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                if self.selected_stat_index > 0:
                    self.selected_stat_index -= 1
                    self.audio.play_game_sound('ui', 'tick')
                    self.audio.speak(self.stats_lines[self.selected_stat_index], interrupt=True)
                elif self.selected_stat_index == -1 and len(self.stats_lines) > 0:
                    self.selected_stat_index = len(self.stats_lines) - 1
                    self.audio.play_game_sound('ui', 'tick')
                    self.audio.speak(self.stats_lines[self.selected_stat_index], interrupt=True)
                return True
                
            elif event.key == pygame.K_DOWN:
                if self.selected_stat_index < len(self.stats_lines) - 1:
                    self.selected_stat_index += 1
                    self.audio.play_game_sound('ui', 'tick')
                    self.audio.speak(self.stats_lines[self.selected_stat_index], interrupt=True)
                elif self.selected_stat_index == -1 and len(self.stats_lines) > 0:
                    self.selected_stat_index = 0
                    self.audio.play_game_sound('ui', 'tick')
                    self.audio.speak(self.stats_lines[self.selected_stat_index], interrupt=True)
                return True
                
            elif event.key == pygame.K_RETURN:
                # Enter'a basıldığında butonu tetikle
                self.audio.play_game_sound('ui', 'click')
                self._return_to_menu()
                return True
                
        return False
        
    def draw(self, surface: pygame.Surface):
        # Arka planı hafifçe karart (mevcut ekranın üzerine bindirilecekse)
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.fill((0, 0, 0))
        overlay.set_alpha(200)
        surface.blit(overlay, (0, 0))
        
        # Ana Paneli Çiz
        self.main_panel.draw(surface)
        
        # Başlık Rengi
        title_color = COLORS['gold'] if self.is_victory else COLORS['danger']
        title_surf = self.get_title_font().render(self.main_panel.title, True, title_color)
        title_rect = title_surf.get_rect(centerx=self.main_panel.rect.centerx, y=self.main_panel.rect.y + 15)
        surface.blit(title_surf, title_rect)
        
        # Hikaye (Neden) Metni
        self.story_text.draw(surface)
        
        # --- İSTATİSTİKLER KISMI ---
        stats_y = self.story_text.rect.bottom + 40
        header_surf = self.get_header_font().render("--- Valilik İstatistikleri ---", True, COLORS['highlight'])
        header_rect = header_surf.get_rect(centerx=self.main_panel.rect.centerx, y=stats_y)
        surface.blit(header_surf, header_rect)
        
        stats_y += 40
        body_font = self.get_body_font()
        
        for i, line in enumerate(self.stats_lines):
            # Seçili olanı sarı renkle vurgula
            color = COLORS['gold'] if i == self.selected_stat_index else COLORS['text']
            prefix = "► " if i == self.selected_stat_index else "  "
            
            line_surf = body_font.render(prefix + line, True, color)
            surface.blit(line_surf, (self.main_panel.rect.x + 40, stats_y))
            stats_y += 30
            
        # Butonlar
        self.btn_menu.draw(surface)
        
    def _return_to_menu(self):
        """Oyun bittikten sonra ana menüye dön."""
        if self.screen_manager.game_manager:
            # Ana menüye dönerken main loop'un bizi tekrar bu ekrana atmasını engelle
            self.screen_manager.game_manager.game_over = False
            
        self.screen_manager.change_screen(ScreenType.MAIN_MENU)
