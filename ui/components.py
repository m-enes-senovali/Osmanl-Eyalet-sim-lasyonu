# -*- coding: utf-8 -*-
"""
Osmanlı Eyalet Yönetim Simülasyonu - UI Bileşenleri
Erişilebilirlik destekli butonlar, paneller ve diğer UI öğeleri.
"""

import pygame
from config import COLORS, FONTS, ACCESSIBILITY, get_font
from audio.audio_manager import get_audio_manager


class Button:
    """Erişilebilir buton bileşeni"""
    
    def __init__(self, x: int, y: int, width: int, height: int, 
                 text: str, shortcut: str = None, callback=None,
                 enabled: bool = True):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.shortcut = shortcut
        self.callback = callback
        self.enabled = enabled
        
        # Durumlar
        self.hovered = False
        self.pressed = False
        self.focused = False
        
        # Önbellek
        self._font = None
        self._last_announced = False
    
    def get_font(self):
        if self._font is None:
            self._font = get_font(FONTS['body'])
        return self._font
    
    def handle_event(self, event) -> bool:
        """Olayları işle, True dönerse tıklandı demek"""
        if not self.enabled:
            return False
        
        audio = get_audio_manager()
        
        if event.type == pygame.MOUSEMOTION:
            was_hovered = self.hovered
            self.hovered = self.rect.collidepoint(event.pos)
            
            # Hover duyurusu
            if self.hovered and not was_hovered:
                if ACCESSIBILITY['announce_hover']:
                    audio.announce_button(self.text, self.shortcut)
                audio.play_ui_sound('hover')
        
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.hovered:
                self.pressed = True
                audio.play_ui_sound('click')
        
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.pressed and self.hovered:
                self.pressed = False
                if self.callback:
                    self.callback()
                return True
            self.pressed = False
        
        elif event.type == pygame.KEYDOWN:
            # Enter tuşu ile tetikleme (odaklandığında)
            if self.focused and event.key == pygame.K_RETURN:
                audio.play_ui_sound('click')
                if self.callback:
                    self.callback()
                return True
            
            # Kısayol tuşu
            if self.shortcut:
                # Özel tuşlar için eşleme
                special_keys = {
                    'backspace': pygame.K_BACKSPACE,
                    'escape': pygame.K_ESCAPE,
                    'space': pygame.K_SPACE,
                    'return': pygame.K_RETURN,
                    'enter': pygame.K_RETURN,
                    'tab': pygame.K_TAB,
                    'f1': pygame.K_F1,
                    'f2': pygame.K_F2,
                    'f3': pygame.K_F3,
                    'f4': pygame.K_F4,
                    'f5': pygame.K_F5,
                    'f6': pygame.K_F6,
                    'f7': pygame.K_F7,
                    'f8': pygame.K_F8,
                    'f9': pygame.K_F9,
                    'f10': pygame.K_F10,
                    'f11': pygame.K_F11,
                    'f12': pygame.K_F12,
                }
                
                shortcut_lower = self.shortcut.lower()
                if shortcut_lower in special_keys:
                    shortcut_key = special_keys[shortcut_lower]
                else:
                    shortcut_key = getattr(pygame, f'K_{shortcut_lower}', None)
                
                if shortcut_key and event.key == shortcut_key:
                    audio.play_ui_sound('click')
                    if self.callback:
                        self.callback()
                    return True
        
        return False
    
    def set_focus(self, focused: bool):
        """Odak durumunu ayarla"""
        if self.focused != focused:
            self.focused = focused
            if focused and ACCESSIBILITY['announce_focus_change']:
                audio = get_audio_manager()
                audio.announce_button(self.text, self.shortcut)
    
    def draw(self, surface: pygame.Surface):
        """Butonu çiz"""
        # Renk ve boyut (lift) seçimi
        lift_y = 0
        if not self.enabled:
            bg_color = COLORS['button_disabled']
            text_color = (100, 100, 100)
            lift_y = 0
        elif self.pressed:
            bg_color = COLORS['button_pressed']
            text_color = COLORS['text']
            lift_y = 1
        elif self.hovered or self.focused:
            bg_color = COLORS['button_hover']
            text_color = COLORS['gold']
            lift_y = -2
        else:
            bg_color = COLORS['button_normal']
            text_color = COLORS['text']
            lift_y = 0
            
        # Çizim alanı (Aşağı/yukarı hareket efekti)
        draw_rect = self.rect.copy()
        draw_rect.y += lift_y
        
        # Gölge (Eğer engelli/basılı değilse)
        if self.enabled and not self.pressed:
            shadow_rect = self.rect.copy()
            shadow_rect.y += 3  # Sabit gölge konumu
            shadow_surface = pygame.Surface((shadow_rect.width, shadow_rect.height), pygame.SRCALPHA)
            pygame.draw.rect(shadow_surface, (0, 0, 0, 80), shadow_surface.get_rect(), border_radius=12)
            surface.blit(shadow_surface, shadow_rect.topleft)
        
        # Arka plan
        pygame.draw.rect(surface, bg_color, draw_rect, border_radius=12)
        
        # Kenarlık
        border_color = COLORS['gold'] if (self.focused or self.hovered) else COLORS['panel_border']
        pygame.draw.rect(surface, border_color, draw_rect, width=2, border_radius=12)
        
        # İç aydınlık efekti (Gloss)
        inner_rect = draw_rect.inflate(-4, -4)
        inner_surface = pygame.Surface((inner_rect.width, inner_rect.height), pygame.SRCALPHA)
        pygame.draw.rect(inner_surface, (255, 255, 255, 10), inner_surface.get_rect(), border_radius=10)
        surface.blit(inner_surface, inner_rect.topleft)
        
        # Metin
        font = self.get_font()
        text_surface = font.render(self.text, True, text_color)
        text_rect = text_surface.get_rect(center=draw_rect.center)
        surface.blit(text_surface, text_rect)
        
        # Kısayol göstergesi
        if self.shortcut and self.enabled:
            shortcut_font = get_font(FONTS['small'])
            shortcut_text = f"[{self.shortcut.upper()}]"
            shortcut_surface = shortcut_font.render(shortcut_text, True, COLORS['gold'])
            shortcut_rect = shortcut_surface.get_rect(
                right=self.rect.right - 8,
                bottom=self.rect.bottom - 4
            )
            surface.blit(shortcut_surface, shortcut_rect)


class Panel:
    """Bilgi paneli bileşeni"""
    
    def __init__(self, x: int, y: int, width: int, height: int, 
                 title: str = None):
        self.rect = pygame.Rect(x, y, width, height)
        self.title = title
        self.content_items = []
        self._title_font = None
        self._content_font = None
    
    def get_title_font(self):
        if self._title_font is None:
            self._title_font = get_font(FONTS['subheader'])
        return self._title_font
    
    def get_content_font(self):
        if self._content_font is None:
            self._content_font = get_font(FONTS['body'])
        return self._content_font
    
    def set_content(self, items: list):
        """Panel içeriğini ayarla [(label, value), ...]"""
        self.content_items = items
    
    def add_item(self, label: str, value: str):
        """İçerik öğesi ekle"""
        self.content_items.append((label, value))
    
    def clear(self):
        """İçeriği temizle"""
        self.content_items = []
    
    def announce_content(self):
        """Panel içeriğini ekran okuyucuya duyur"""
        audio = get_audio_manager()
        if self.title:
            audio.speak(self.title, interrupt=True)
        
        for label, value in self.content_items:
            audio.announce_value(label, str(value))
    
    def draw(self, surface: pygame.Surface):
        """Paneli çiz"""
        # Çok Katmanlı Yumuşak Gölge (Soft Shadow Overlay)
        for offset, alpha in [(4, 40), (8, 20), (12, 10)]:
            shadow_surface = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
            pygame.draw.rect(shadow_surface, (0, 0, 0, alpha), shadow_surface.get_rect(), border_radius=15)
            surface.blit(shadow_surface, (self.rect.x + offset, self.rect.y + offset))

        # Ana Arka plan
        pygame.draw.rect(surface, COLORS['panel_bg'], self.rect, border_radius=12)
        
        # Kenarlık
        pygame.draw.rect(surface, COLORS['panel_border'], self.rect, width=2, border_radius=12)
        
        y_offset = 15
        
        # Başlık
        if self.title:
            title_font = self.get_title_font()
            title_surface = title_font.render(self.title, True, COLORS['gold'])
            title_rect = title_surface.get_rect(
                centerx=self.rect.centerx,
                top=self.rect.top + y_offset
            )
            surface.blit(title_surface, title_rect)
            
            # Ayırıcı çizgi
            y_offset += 35
            pygame.draw.line(
                surface, COLORS['panel_border'],
                (self.rect.left + 20, self.rect.top + y_offset),
                (self.rect.right - 20, self.rect.top + y_offset),
                2
            )
            y_offset += 15
        
        # İçerik
        content_font = self.get_content_font()
        for label, value in self.content_items:
            # Label
            label_surface = content_font.render(f"{label}:", True, COLORS['text'])
            surface.blit(label_surface, (self.rect.left + 20, self.rect.top + y_offset))
            
            # Value
            value_surface = content_font.render(str(value), True, COLORS['gold'])
            value_rect = value_surface.get_rect(
                right=self.rect.right - 20,
                top=self.rect.top + y_offset
            )
            surface.blit(value_surface, value_rect)
            
            y_offset += 28


class ProgressBar:
    """İlerleme çubuğu bileşeni"""
    
    def __init__(self, x: int, y: int, width: int, height: int,
                 label: str = None, max_value: float = 100,
                 color: tuple = None):
        self.rect = pygame.Rect(x, y, width, height)
        self.label = label
        self.max_value = max_value
        self.target_value = 0
        self.current_value = 0
        self.color = color or COLORS['success']
        self._font = None
    
    def get_font(self):
        if self._font is None:
            self._font = get_font(FONTS['small'])
        return self._font
    
    def set_value(self, value: float):
        """Hedef değeri ayarla"""
        self.target_value = max(0, min(self.max_value, value))
        # Eğer ilk atamaysa direkt doldur
        if self.current_value == 0 and self.target_value > 0:
            self.current_value = self.target_value
    
    def get_percentage(self) -> float:
        """Yüzde değerini al"""
        if self.max_value == 0:
            return 0
        return (self.current_value / self.max_value) * 100
    
    def announce(self):
        """Değeri ekran okuyucuya duyur"""
        audio = get_audio_manager()
        percentage = int(self.get_percentage())
        if self.label:
            audio.announce_value(self.label, f"%{percentage}")
        else:
            audio.speak(f"Yüzde {percentage}")
    
    def draw(self, surface: pygame.Surface):
        """Çubuğu çiz"""
        # Akıcı doluluk efekti (Lerp)
        diff = self.target_value - self.current_value
        if abs(diff) > 0.1:
            self.current_value += diff * 0.1  # Yumuşak geçiş hızı
        else:
            self.current_value = self.target_value

        # Arka plan
        pygame.draw.rect(surface, COLORS['panel_bg'], self.rect, border_radius=8)
        
        # İç alan gölgesi (İçeri gömük hissi)
        inner_shadow = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
        pygame.draw.rect(inner_shadow, (0, 0, 0, 40), inner_shadow.get_rect(), border_radius=8)
        surface.blit(inner_shadow, self.rect.topleft)
        
        # Dolu kısım
        if self.current_value > 0:
            fill_width = max(10, int((self.current_value / self.max_value) * self.rect.width)) # En az 10 piksel görünsün
            fill_rect = pygame.Rect(
                self.rect.x, self.rect.y,
                fill_width, self.rect.height
            )
            pygame.draw.rect(surface, self.color, fill_rect, border_radius=8)
            
            # Üst yarıya parlama efekti (Gloss/3D)
            gloss_rect = pygame.Rect(
                self.rect.x, self.rect.y,
                fill_width, self.rect.height // 2
            )
            gloss_surface = pygame.Surface((gloss_rect.width, gloss_rect.height), pygame.SRCALPHA)
            pygame.draw.rect(gloss_surface, (255, 255, 255, 30), gloss_surface.get_rect(), border_top_left_radius=8, border_top_right_radius=8 if fill_width == self.rect.width else 0)
            surface.blit(gloss_surface, gloss_rect.topleft)
        
        # Kenarlık
        pygame.draw.rect(surface, COLORS['panel_border'], self.rect, width=2, border_radius=8)
        
        # Yüzde metni
        font = self.get_font()
        percentage = int(self.get_percentage())
        text = f"{percentage}%"
        if self.label:
            text = f"{self.label}: {percentage}%"
        text_surface = font.render(text, True, COLORS['text'])
        text_rect = text_surface.get_rect(center=self.rect.center)
        surface.blit(text_surface, text_rect)


class MenuList:
    """Klavye ile gezinilebilir menü listesi"""
    
    def __init__(self, x: int, y: int, width: int, item_height: int = 50):
        self.x = x
        self.y = y
        self.width = width
        self.item_height = item_height
        self.items = []  # [(text, callback, shortcut), ...]
        self.selected_index = 0
        self._font = None
    
    def get_font(self):
        if self._font is None:
            self._font = get_font(FONTS['body'])
        return self._font
    
    def add_item(self, text: str, callback=None, shortcut: str = None):
        """Menü öğesi ekle"""
        self.items.append((text, callback, shortcut))
    
    def clear(self):
        """Menüyü temizle"""
        self.items = []
        self.selected_index = 0
    
    def _is_separator(self, index: int) -> bool:
        """Öğenin boş ayırıcı olup olmadığını kontrol et"""
        if 0 <= index < len(self.items):
            text, callback, _ = self.items[index]
            return text.strip() == "" and callback is None
        return False
    
    def _find_next_valid(self, start: int, direction: int) -> int:
        """Bir sonraki geçerli (boş olmayan) öğeyi bul"""
        if not self.items:
            return 0
        
        current = start
        attempts = 0
        while attempts < len(self.items):
            current = (current + direction) % len(self.items)
            if not self._is_separator(current):
                return current
            attempts += 1
        
        # Tüm öğeler boşsa ilk öğeye dön
        return 0
    
    def select_next(self):
        """Sonraki öğeyi seç (boş ayırıcıları atla)"""
        if self.items:
            self.selected_index = self._find_next_valid(self.selected_index, 1)
            self._announce_current()
    
    def select_prev(self):
        """Önceki öğeyi seç (boş ayırıcıları atla)"""
        if self.items:
            self.selected_index = self._find_next_valid(self.selected_index, -1)
            self._announce_current()
    
    def _announce_current(self):
        """Seçili öğeyi duyur (boş öğeleri atlayarak)"""
        if self.items:
            text, _, shortcut = self.items[self.selected_index]
            # Boş öğeleri duyurma
            if text.strip() == "":
                return
            
            audio = get_audio_manager()
            # Toplam sayıda boş öğeleri sayma
            valid_count = sum(1 for t, c, _ in self.items if t.strip() != "" or c is not None)
            valid_index = sum(1 for i, (t, c, _) in enumerate(self.items[:self.selected_index + 1]) if t.strip() != "" or c is not None)
            audio.announce_menu_item(
                text, 
                valid_index, 
                valid_count
            )
    
    def activate_selected(self) -> bool:
        """Seçili öğeyi etkinleştir"""
        if self.items:
            text, callback, _ = self.items[self.selected_index]
            if callback:
                audio = get_audio_manager()
                audio.play_ui_sound('click')
                callback()
                return True
        return False
    
    def handle_event(self, event) -> bool:
        """Olayları işle"""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.select_prev()
                return True
            elif event.key == pygame.K_DOWN:
                self.select_next()
                return True
            elif event.key == pygame.K_HOME:
                # İlk öğeye git
                self.selected_index = self._find_next_valid(-1, 1)
                self._announce_current()
                return True
            elif event.key == pygame.K_END:
                # Son öğeye git
                self.selected_index = self._find_next_valid(len(self.items), -1)
                self._announce_current()
                return True
            elif event.key == pygame.K_RETURN:
                return self.activate_selected()
            else:
                # Kısayol kontrolü
                for i, (text, callback, shortcut) in enumerate(self.items):
                    if shortcut:
                        key = getattr(pygame, f'K_{shortcut.lower()}', None)
                        if key and event.key == key:
                            self.selected_index = i
                            audio = get_audio_manager()
                            audio.play_ui_sound('click')
                            if callback:
                                callback()
                            return True
        
        elif event.type == pygame.MOUSEMOTION:
            for i, _ in enumerate(self.items):
                item_rect = pygame.Rect(
                    self.x, self.y + i * self.item_height,
                    self.width, self.item_height
                )
                if item_rect.collidepoint(event.pos):
                    if self.selected_index != i:
                        self.selected_index = i
                        self._announce_current()
                    break
        
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for i, (text, callback, _) in enumerate(self.items):
                item_rect = pygame.Rect(
                    self.x, self.y + i * self.item_height,
                    self.width, self.item_height
                )
                if item_rect.collidepoint(event.pos):
                    self.selected_index = i
                    audio = get_audio_manager()
                    audio.play_ui_sound('click')
                    if callback:
                        callback()
                    return True
        
        return False
    
    def draw(self, surface: pygame.Surface):
        """Menüyü çiz"""
        font = self.get_font()
        
        for i, (text, _, shortcut) in enumerate(self.items):
            # Boş ayırıcıları farklı çiz
            if text.strip() == "":
                separator_y = self.y + i * self.item_height + self.item_height // 2
                pygame.draw.line(
                    surface, COLORS['panel_border'],
                    (self.x + 20, separator_y),
                    (self.x + self.width - 20, separator_y),
                    2
                )
                continue
            
            is_selected = (i == self.selected_index)
            lift_y = -2 if is_selected else 0
            
            item_rect = pygame.Rect(
                self.x, self.y + i * self.item_height + lift_y,
                self.width, self.item_height - 4
            )
            
            # Seçili olmayan öğelere gölge
            if not is_selected:
                shadow_rect = item_rect.copy()
                shadow_rect.y += 2
                shadow_surface = pygame.Surface((shadow_rect.width, shadow_rect.height), pygame.SRCALPHA)
                pygame.draw.rect(shadow_surface, (0, 0, 0, 40), shadow_surface.get_rect(), border_radius=10)
                surface.blit(shadow_surface, shadow_rect.topleft)
            
            # Seçili öğe arka planı
            if is_selected:
                pygame.draw.rect(surface, COLORS['button_hover'], item_rect, border_radius=10)
                pygame.draw.rect(surface, COLORS['gold'], item_rect, width=2, border_radius=10)
                text_color = COLORS['gold']
            else:
                pygame.draw.rect(surface, COLORS['button_normal'], item_rect, border_radius=10)
                pygame.draw.rect(surface, COLORS['panel_border'], item_rect, width=1, border_radius=10)
                text_color = COLORS['text']
            
            # İç Parlama effect (Gloss)
            inner_rect = item_rect.inflate(-4, -4)
            inner_surface = pygame.Surface((inner_rect.width, inner_rect.height), pygame.SRCALPHA)
            pygame.draw.rect(inner_surface, (255, 255, 255, 5), inner_surface.get_rect(), border_radius=8)
            surface.blit(inner_surface, inner_rect.topleft)
            
            # Metin
            text_surface = font.render(text, True, text_color)
            text_rect = text_surface.get_rect(
                left=item_rect.left + 20,
                centery=item_rect.centery
            )
            surface.blit(text_surface, text_rect)
            
            # Kısayol
            if shortcut:
                shortcut_font = get_font(FONTS['small'])
                shortcut_text = f"[{shortcut.upper()}]"
                shortcut_surface = shortcut_font.render(shortcut_text, True, COLORS['gold'])
                shortcut_rect = shortcut_surface.get_rect(
                    right=item_rect.right - 15,
                    centery=item_rect.centery
                )
                surface.blit(shortcut_surface, shortcut_rect)


class Tooltip:
    """Araç ipucu bileşeni"""
    
    def __init__(self):
        self.text = None
        self.position = (0, 0)
        self.visible = False
        self._font = None
    
    def get_font(self):
        if self._font is None:
            self._font = get_font(FONTS['tooltip'])
        return self._font
    
    def show(self, text: str, position: tuple):
        """Tooltip göster"""
        self.text = text
        self.position = position
        self.visible = True
    
    def hide(self):
        """Tooltip gizle"""
        self.visible = False
    
    def draw(self, surface: pygame.Surface):
        """Tooltip çiz"""
        if not self.visible or not self.text:
            return
        
        font = self.get_font()
        
        # Padding
        padding = 10
        
        # Metin boyutu
        text_surface = font.render(self.text, True, COLORS['text'])
        text_rect = text_surface.get_rect()
        
        # Arka plan dikdörtgeni
        bg_rect = pygame.Rect(
            self.position[0], self.position[1],
            text_rect.width + padding * 2,
            text_rect.height + padding * 2
        )
        
        # Ekran sınırları kontrolü
        screen_width, screen_height = surface.get_size()
        if bg_rect.right > screen_width:
            bg_rect.right = screen_width - 5
        if bg_rect.bottom > screen_height:
            bg_rect.bottom = screen_height - 5
        
        # Arka plan
        pygame.draw.rect(surface, COLORS['panel_bg'], bg_rect, border_radius=5)
        pygame.draw.rect(surface, COLORS['gold'], bg_rect, width=1, border_radius=5)
        
        # Metin
        text_rect.topleft = (bg_rect.left + padding, bg_rect.top + padding)
        surface.blit(text_surface, text_rect)


class HierarchicalMenu:
    """
    Hiyerarşik alt menü desteği olan erişilebilir menü.
    
    Navigasyon:
    - Yukarı/Aşağı: Öğeler arası gezin
    - Enter: Alt menüye gir / Eylemi uygula
    - Backspace/Escape: Üst menüye dön
    """
    
    def __init__(self, x: int, y: int, width: int, item_height: int = 40):
        self.x = x
        self.y = y
        self.width = width
        self.item_height = item_height
        
        # Menü yığını - her seviye bir dict listesi
        # Her öğe: {'text': str, 'callback': func, 'submenu': list veya None}
        self.menu_stack = []
        self.root_menu = []
        self.selected_index = 0
        
        self.audio = get_audio_manager()
        self._font = None
        self._announced = False
    
    def get_font(self):
        if self._font is None:
            self._font = get_font(FONTS['body'])
        return self._font
    
    def set_menu(self, items: list):
        """
        Kök menüyü ayarla.
        items: [{'text': str, 'callback': func veya None, 'submenu': list veya None}, ...]
        """
        self.root_menu = items
        self.menu_stack = []
        self.selected_index = 0
        self._announced = False
    
    def add_category(self, text: str, items: list):
        """
        Kategorili alt menü ekle.
        items: [{'text': str, 'callback': func}, ...]
        """
        # Otomatik geri butonu ekle
        submenu_items = items.copy()
        submenu_items.append({'text': '-- Geri --', 'callback': None, 'submenu': None, 'is_back': True})
        
        self.root_menu.append({
            'text': text,
            'callback': None,
            'submenu': submenu_items
        })
    
    def add_action(self, text: str, callback):
        """Direkt eylem ekle (alt menüsüz)."""
        self.root_menu.append({
            'text': text,
            'callback': callback,
            'submenu': None
        })
    
    def add_separator(self):
        """Ayırıcı ekle."""
        self.root_menu.append({
            'text': '',
            'callback': None,
            'submenu': None,
            'is_separator': True
        })
    
    def add_back_button(self):
        """Ana ekrana dönüş butonu ekle."""
        self.root_menu.append({
            'text': '-- Ana Ekrana Dön --',
            'callback': None,
            'submenu': None,
            'is_main_back': True
        })
    
    def clear(self):
        """Menüyü temizle."""
        self.root_menu = []
        self.menu_stack = []
        self.selected_index = 0
    
    def get_current_menu(self) -> list:
        """Mevcut görüntülenen menüyü al."""
        if self.menu_stack:
            return self.menu_stack[-1]['items']
        return self.root_menu
    
    def get_current_title(self) -> str:
        """Mevcut menü başlığını al."""
        if self.menu_stack:
            return self.menu_stack[-1]['title']
        return "Ana Menü"
    
    def _is_valid_item(self, item: dict) -> bool:
        """Öğenin geçerli (seçilebilir) olup olmadığını kontrol et."""
        if item.get('is_separator', False):
            return False
        if not item.get('text', '').strip():
            return False
        return True
    
    def _find_next_valid(self, start: int, direction: int) -> int:
        """Bir sonraki geçerli öğeyi bul."""
        menu = self.get_current_menu()
        if not menu:
            return 0
        
        index = start
        for _ in range(len(menu)):
            index = (index + direction) % len(menu)
            if self._is_valid_item(menu[index]):
                return index
        return start
    
    def _announce_current(self):
        """Seçili öğeyi duyur."""
        menu = self.get_current_menu()
        if not menu or self.selected_index >= len(menu):
            return
        
        item = menu[self.selected_index]
        text = item.get('text', '')
        
        # Alt menü varsa belirt
        if item.get('submenu'):
            text += ". Alt menü, Enter ile açın."
        elif item.get('is_back') or item.get('is_main_back'):
            text += ". Geri dönmek için Enter."
        elif item.get('callback'):
            text += ". Seçmek için Enter."
        
        self.audio.speak(text, interrupt=True)
    
    def _announce_menu_enter(self, title: str, count: int):
        """Alt menüye giriş duyurusu."""
        self.audio.speak(f"{title} menüsü. {count} öğe.", interrupt=True)
    
    def _announce_menu_exit(self):
        """Üst menüye dönüş duyurusu."""
        title = self.get_current_title()
        self.audio.speak(f"Geri: {title}", interrupt=True)
    
    def handle_event(self, event):
        """
        Olayları işle.
        Returns: 
            True - olay işlendi
            False - ana ekrana dönülmeli
            None - olay işlenmedi
        """
        menu = self.get_current_menu()
        if not menu:
            return None  # Menü boşsa işleme
        
        if event.type == pygame.KEYDOWN:
            # Yukarı - Önceki öğe
            if event.key == pygame.K_UP:
                self.selected_index = self._find_next_valid(self.selected_index, -1)
                self._announce_current()
                return True
            
            # Aşağı - Sonraki öğe
            if event.key == pygame.K_DOWN:
                self.selected_index = self._find_next_valid(self.selected_index, 1)
                self._announce_current()
                return True
            
            # Enter - Seç / Alt menüye gir
            if event.key == pygame.K_RETURN:
                if self.selected_index < len(menu):
                    item = menu[self.selected_index]
                    
                    # Geri butonu
                    if item.get('is_back'):
                        self.audio.play_ui_sound('click')
                        return self._go_back()
                    
                    # Ana ekrana dönüş
                    if item.get('is_main_back'):
                        self.audio.play_ui_sound('click')
                        return False  # Ana ekrana dön sinyali
                    
                    # Alt menü varsa aç
                    if item.get('submenu'):
                        self.audio.play_ui_sound('click')
                        self.menu_stack.append({
                            'title': item['text'],
                            'items': item['submenu']
                        })
                        self.selected_index = 0
                        self._announce_menu_enter(item['text'], len(item['submenu']))
                        return True
                    
                    # Callback varsa çalıştır
                    if item.get('callback'):
                        self.audio.play_ui_sound('click')
                        item['callback']()
                        return True
                
                return True
            
            # Backspace veya Escape - Geri
            if event.key in (pygame.K_BACKSPACE, pygame.K_ESCAPE):
                self.audio.play_ui_sound('click')
                result = self._go_back()
                if not result:
                    return False  # Ana ekrana dön sinyali
                return True
        
        return None  # Olay işlenmedi
    
    def _go_back(self) -> bool:
        """
        Üst menüye dön.
        Returns: True ise hala menüdeyiz, False ise ana ekrana dönülmeli
        """
        if self.menu_stack:
            self.menu_stack.pop()
            self.selected_index = 0
            self._announce_menu_exit()
            return True
        return False  # Kök menüdeyiz, ana ekrana dön
    
    def announce_menu(self):
        """Mevcut menüyü duyur."""
        menu = self.get_current_menu()
        title = self.get_current_title()
        count = len([i for i in menu if self._is_valid_item(i)])
        self.audio.speak(f"{title}. {count} öğe. Yukarı aşağı ok ile gezin, Enter ile seçin.", interrupt=True)
    
    def update(self):
        """Her frame çağrılır, ilk duyuruyu yapar."""
        if not self._announced:
            self.announce_menu()
            self._announced = True
    
    def draw(self, surface: pygame.Surface):
        """Menüyü çiz."""
        menu = self.get_current_menu()
        if not menu:
            return
        
        font = self.get_font()
        
        # Başlık
        title = self.get_current_title()
        if self.menu_stack:
            title_surface = font.render(f"[{title}]", True, COLORS['gold'])
            surface.blit(title_surface, (self.x, self.y - 30))
        
        # Öğeleri çiz
        visible_start = max(0, self.selected_index - 5)
        visible_end = min(len(menu), visible_start + 12)
        
        for i, item in enumerate(menu[visible_start:visible_end]):
            actual_index = visible_start + i
            y_pos = self.y + (i * self.item_height)
            
            # Ayırıcı
            if item.get('is_separator', False) or not item.get('text', '').strip():
                continue
            
            # Arka plan
            item_rect = pygame.Rect(self.x, y_pos, self.width, self.item_height - 5)
            
            if actual_index == self.selected_index:
                pygame.draw.rect(surface, COLORS['button_hover'], item_rect, border_radius=5)
                pygame.draw.rect(surface, COLORS['gold'], item_rect, width=2, border_radius=5)
            else:
                pygame.draw.rect(surface, COLORS['button_normal'], item_rect, border_radius=5)
            
            # Metin
            text = item.get('text', '')
            color = COLORS['gold'] if actual_index == self.selected_index else COLORS['text']
            
            # Geri butonu farklı renk
            if item.get('is_back') or item.get('is_main_back'):
                color = COLORS['warning'] if actual_index == self.selected_index else COLORS['text_dim']
            
            text_surface = font.render(text, True, color)
            text_rect = text_surface.get_rect(left=item_rect.left + 15, centery=item_rect.centery)
            surface.blit(text_surface, text_rect)
            
            # Alt menü göstergesi
            if item.get('submenu'):
                arrow = font.render(">", True, color)
                arrow_rect = arrow.get_rect(right=item_rect.right - 10, centery=item_rect.centery)
                surface.blit(arrow, arrow_rect)
