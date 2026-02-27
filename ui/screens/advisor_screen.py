# -*- coding: utf-8 -*-
"""
Osmanlı Eyalet Yönetim Simülasyonu - Danışman (Kethüda) Ekranı
Gerçek zamanlı durum analizlerini gösteren ve seslendiren ekran.
"""

import pygame
from ui.screen_manager import BaseScreen, ScreenType
from ui.components import Button, Panel
from ui.visual_effects import GradientRenderer, OttomanPatterns
from config import COLORS, FONTS, SCREEN_WIDTH, SCREEN_HEIGHT, get_font
from game.systems.advisor import Urgency

class AdvisorScreen(BaseScreen):
    """Kethüda (Danışman) Rapor Ekranı"""
    
    def __init__(self, screen_manager):
        super().__init__(screen_manager)
        
        self.report_panel = Panel(50, 100, SCREEN_WIDTH - 100, SCREEN_HEIGHT - 200, "Kethüda'nın Arzuhali")
        
        self.back_button = Button(
            x=50,
            y=SCREEN_HEIGHT - 80,
            width=200,
            height=50,
            text="Geri Dön",
            shortcut="backspace",
            callback=self._go_back
        )
        
        self._gradient = GradientRenderer.get_gradient('menu')
        self._report_data = []
        self._title_font = None
        self._item_font = None
        
    def get_title_font(self):
        if self._title_font is None:
            self._title_font = get_font(FONTS['title'])
        return self._title_font
        
    def get_item_font(self):
        if self._item_font is None:
            self._item_font = get_font(FONTS['body'])
        return self._item_font
        
    def on_enter(self):
        """Ekrana girildiğinde verileri anlık olarak çek"""
        gm = self.screen_manager.game_manager
        if not gm or not hasattr(gm, 'advisor'):
            self._report_data = [(Urgency.INFO, "Sistem hatası. Danışman bulunamadı.")]
            return
            
        self._report_data = gm.advisor.get_report()
        
    def announce_screen(self):
        """Ekrana girildiğinde TTS üzerinden okuma yap"""
        self.audio.announce_screen_change("Kethüda'nın Çadırı")
        
        gm = self.screen_manager.game_manager
        if gm and hasattr(gm, 'advisor'):
            summary = gm.advisor.get_summary_text()
            self.audio.speak(summary, interrupt=False)
            
    def _go_back(self):
        """Önceki ekrana dön"""
        self.audio.play_ui_sound('click')
        self.screen_manager.change_screen(ScreenType.PROVINCE_VIEW)
        
    def handle_event(self, event: pygame.event.Event) -> bool:
        if self.back_button.handle_event(event):
            return True
            
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_f:
                # F tuşu ile kapatabilme rahatlığı
                self._go_back()
                return True
            if event.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
                self._go_back()
                return True
                
        return False
        
    def draw(self, surface: pygame.Surface):
        # Arka plan
        surface.blit(self._gradient, (0, 0))
        OttomanPatterns.draw_panel_ornaments(surface, surface.get_rect())
        
        # Başlık çizimi
        title_font = self.get_title_font()
        title_render = title_font.render("KETHÜDA'NIN ARZUHALİ", True, COLORS['gold'])
        title_rect = title_render.get_rect(centerx=SCREEN_WIDTH // 2, top=40)
        surface.blit(title_render, title_rect)
        
        # Panel
        self.report_panel.draw(surface)
        
        # İçerik Çizimi (Raporlar)
        item_font = self.get_item_font()
        start_y = 160
        x_pos = 80
        
        if not self._report_data:
            text = item_font.render("Mevcut bir rapor bulunamadı.", True, COLORS['text'])
            surface.blit(text, (x_pos, start_y))
        else:
            for urgency, msg in self._report_data:
                # Renge karar ver
                if urgency == Urgency.CRITICAL:
                    color = COLORS['danger']
                    prefix = "[KRİTİK]"
                elif urgency == Urgency.WARNING:
                    color = COLORS['warning']
                    prefix = "[UYARI]"
                else:
                    color = COLORS['text']
                    prefix = "[BİLGİ]"
                
                # Metni sarmalama (Word wrap) basit çözümü
                words = msg.split(' ')
                lines = []
                current_line = []
                
                for word in words:
                    test_line = " ".join(current_line + [word])
                    if item_font.size(f"{prefix} {test_line}")[0] < (SCREEN_WIDTH - 160):
                        current_line.append(word)
                    else:
                        lines.append(" ".join(current_line))
                        current_line = [word]
                if current_line:
                    lines.append(" ".join(current_line))
                
                # İlk satırı prefix ile bas
                first_str = f"{prefix} {lines[0]}" if lines else prefix
                first_render = item_font.render(first_str, True, color)
                surface.blit(first_render, (x_pos, start_y))
                start_y += 35
                
                # Kalan satırları biraz içeriden bas
                for line in lines[1:]:
                    line_render = item_font.render(line, True, color)
                    surface.blit(line_render, (x_pos + 40, start_y))
                    start_y += 35
                    
                start_y += 15 # Raporlar arası boşluk
        
        self.back_button.draw(surface)
