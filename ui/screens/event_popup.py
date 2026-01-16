# -*- coding: utf-8 -*-
"""
Osmanlı Eyalet Yönetim Simülasyonu - Olay Popup Ekranı
"""

import pygame
from ui.screen_manager import BaseScreen, ScreenType
from ui.components import Button, MenuList
from config import COLORS, FONTS, SCREEN_WIDTH, SCREEN_HEIGHT


class EventPopupScreen(BaseScreen):
    """Olay seçim ekranı"""
    
    def __init__(self, screen_manager):
        super().__init__(screen_manager)
        
        # Seçenekler menüsü
        self.choices_menu = MenuList(
            x=(SCREEN_WIDTH - 600) // 2,
            y=380,
            width=600,
            item_height=55
        )
        
        self.back_button = Button(
            x=(SCREEN_WIDTH - 150) // 2,
            y=SCREEN_HEIGHT - 100,
            width=150,
            height=50,
            text="Kapat",
            shortcut="escape",
            callback=self._close
        )
        
        self._title_font = None
        self._body_font = None
    
    def get_title_font(self):
        if self._title_font is None:
            self._title_font = pygame.font.Font(None, FONTS['header'])
        return self._title_font
    
    def get_body_font(self):
        if self._body_font is None:
            self._body_font = pygame.font.Font(None, FONTS['body'])
        return self._body_font
    
    def on_enter(self):
        self._setup_choices()
    
    def _setup_choices(self):
        """Seçenekleri ayarla"""
        self.choices_menu.clear()
        gm = self.screen_manager.game_manager
        if not gm or not gm.events.current_event:
            return
        
        event = gm.events.current_event
        for i, choice in enumerate(event.choices):
            self.choices_menu.add_item(
                choice.text,
                lambda idx=i: self._make_choice(idx),
                str(i + 1) if i < 9 else None
            )
    
    def announce_screen(self):
        gm = self.screen_manager.game_manager
        if gm and gm.events.current_event:
            gm.events.announce_event()
    
    def handle_event(self, event) -> bool:
        if self.choices_menu.handle_event(event):
            return True
        
        if self.back_button.handle_event(event):
            return True
        
        if event.type == pygame.KEYDOWN:
            gm = self.screen_manager.game_manager
            
            # F1 - Olayı tekrar oku (tam)
            if event.key == pygame.K_F1:
                self._announce_full_event()
                return True
            
            # R - Sadece açıklamayı oku
            if event.key == pygame.K_r:
                self._announce_description()
                return True
            
            # T - Sadece başlığı oku
            if event.key == pygame.K_t:
                self._announce_title()
                return True
            
            # C - Seçenekleri oku
            if event.key == pygame.K_c:
                self._announce_choices()
                return True
            
            # Backspace / Escape - Kapat
            if event.key == pygame.K_BACKSPACE:
                self._close()
                return True
            
            # Sayı tuşları ile seçim
            if gm and gm.events.current_event:
                for i in range(len(gm.events.current_event.choices)):
                    if event.key == pygame.K_1 + i:
                        self._make_choice(i)
                        return True
        
        return False
    
    def _announce_full_event(self):
        """Tüm olayı oku"""
        gm = self.screen_manager.game_manager
        if gm and gm.events.current_event:
            event = gm.events.current_event
            severity_names = {
                'minor': 'Küçük',
                'moderate': 'Orta', 
                'major': 'Büyük',
                'critical': 'Kritik'
            }
            severity = severity_names.get(event.severity.value, '')
            self.audio.speak(f"{severity} olay: {event.title}", interrupt=True)
            self.audio.speak(event.description)
            self.audio.speak("Seçenekler:")
            for i, choice in enumerate(event.choices):
                self.audio.speak(f"{i+1}: {choice.text}")
    
    def _announce_description(self):
        """Sadece açıklamayı oku"""
        gm = self.screen_manager.game_manager
        if gm and gm.events.current_event:
            self.audio.speak(gm.events.current_event.description, interrupt=True)
    
    def _announce_title(self):
        """Sadece başlığı oku"""
        gm = self.screen_manager.game_manager
        if gm and gm.events.current_event:
            self.audio.speak(gm.events.current_event.title, interrupt=True)
    
    def _announce_choices(self):
        """Seçenekleri ve sonuçlarını oku"""
        gm = self.screen_manager.game_manager
        if gm and gm.events.current_event:
            self.audio.speak("Seçenekler ve olası sonuçları:", interrupt=True)
            for i, choice in enumerate(gm.events.current_event.choices):
                # Seçenek metni
                self.audio.speak(f"{i+1}: {choice.text}")
                
                # Etki açıklaması
                if choice.description:
                    self.audio.speak(f"  Sonuç: {choice.description}")
                
                # Sayısal etkiler
                effect_texts = []
                effect_names = {
                    'gold': 'Altın',
                    'food': 'Zahire',
                    'population': 'Nüfus',
                    'happiness': 'Mutluluk',
                    'loyalty': 'Sadakat',
                    'soldiers': 'Asker',
                    'morale': 'Moral',
                    'unrest': 'Huzursuzluk',
                    'trade_modifier': 'Ticaret',
                    'tax_modifier': 'Vergi'
                }
                for effect, value in choice.effects.items():
                    name = effect_names.get(effect, effect)
                    sign = '+' if value > 0 else ''
                    effect_texts.append(f"{name}: {sign}{value}")
                
                if effect_texts:
                    self.audio.speak(f"  Etkiler: {', '.join(effect_texts)}")
    
    def draw(self, surface: pygame.Surface):
        gm = self.screen_manager.game_manager
        if not gm or not gm.events.current_event:
            return
        
        event = gm.events.current_event
        
        # Yarı saydam arka plan
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        surface.blit(overlay, (0, 0))
        
        # Olay kutusu
        box_rect = pygame.Rect(
            (SCREEN_WIDTH - 700) // 2,
            100,
            700,
            SCREEN_HEIGHT - 200
        )
        pygame.draw.rect(surface, COLORS['panel_bg'], box_rect, border_radius=15)
        
        # Ciddiyet rengine göre kenarlık
        severity_colors = {
            'minor': COLORS['panel_border'],
            'moderate': COLORS['warning'],
            'major': COLORS['danger'],
            'critical': (200, 0, 0)
        }
        border_color = severity_colors.get(event.severity.value, COLORS['panel_border'])
        pygame.draw.rect(surface, border_color, box_rect, width=4, border_radius=15)
        
        # Olay türü ikonu
        type_icons = {
            'economic': '💰',
            'military': '⚔',
            'population': '👥',
            'diplomatic': '🤝',
            'natural': '🌍',
            'opportunity': '⭐'
        }
        icon = type_icons.get(event.event_type.value, '❓')
        
        # Başlık
        title_font = self.get_title_font()
        title = title_font.render(f"{icon} {event.title}", True, COLORS['gold'])
        title_rect = title.get_rect(centerx=SCREEN_WIDTH // 2, top=box_rect.top + 30)
        surface.blit(title, title_rect)
        
        # Ciddiyet etiketi
        severity_names = {
            'minor': 'Küçük',
            'moderate': 'Orta',
            'major': 'Büyük',
            'critical': 'KRİTİK'
        }
        severity_text = severity_names.get(event.severity.value, '')
        small_font = pygame.font.Font(None, FONTS['small'])
        severity_label = small_font.render(f"[{severity_text}]", True, border_color)
        severity_rect = severity_label.get_rect(centerx=SCREEN_WIDTH // 2, top=box_rect.top + 70)
        surface.blit(severity_label, severity_rect)
        
        # Açıklama
        body_font = self.get_body_font()
        
        # Metni satırlara böl
        description = event.description
        words = description.split()
        lines = []
        current_line = ""
        max_width = 600
        
        for word in words:
            test_line = current_line + word + " "
            if body_font.size(test_line)[0] < max_width:
                current_line = test_line
            else:
                lines.append(current_line)
                current_line = word + " "
        if current_line:
            lines.append(current_line)
        
        y = box_rect.top + 120
        for line in lines:
            line_surface = body_font.render(line.strip(), True, COLORS['text'])
            line_rect = line_surface.get_rect(centerx=SCREEN_WIDTH // 2, top=y)
            surface.blit(line_surface, line_rect)
            y += 30
        
        # Ayırıcı
        pygame.draw.line(
            surface, COLORS['panel_border'],
            (box_rect.left + 50, y + 20),
            (box_rect.right - 50, y + 20),
            2
        )
        
        # Seçenekler başlığı
        choices_title = small_font.render("Ne yapacaksınız?", True, COLORS['gold'])
        choices_rect = choices_title.get_rect(centerx=SCREEN_WIDTH // 2, top=y + 40)
        surface.blit(choices_title, choices_rect)
        
        # Seçenekler menüsü
        self.choices_menu.y = y + 80
        self.choices_menu.draw(surface)
        
        # Kapat butonu
        self.back_button.y = box_rect.bottom - 70
        self.back_button.rect.y = self.back_button.y
        self.back_button.draw(surface)
    
    def _make_choice(self, choice_index: int):
        """Seçim yap"""
        gm = self.screen_manager.game_manager
        if gm:
            effects = gm.events.make_choice(choice_index)
            gm.apply_event_effects(effects)
            self.screen_manager.change_screen(ScreenType.PROVINCE_VIEW)
    
    def _close(self):
        """Olayı kapat (hiçbir şey yapma)"""
        gm = self.screen_manager.game_manager
        if gm:
            gm.events.dismiss_event()
        self.screen_manager.change_screen(ScreenType.PROVINCE_VIEW)
