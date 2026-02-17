# -*- coding: utf-8 -*-
"""
Osmanlı Eyalet Yönetim Simülasyonu - Erişilebilir Metin Girişi
Ekran okuyucu uyumlu metin kutusu
"""

import pygame
from audio.audio_manager import get_audio_manager
from config import get_font

# Clipboard desteği
try:
    pygame.scrap.init()
    SCRAP_AVAILABLE = True
except:
    SCRAP_AVAILABLE = False


class AccessibleTextInput:
    """Erişilebilir metin giriş kutusu"""
    
    def __init__(self, x: int, y: int, width: int, height: int, 
                 label: str = "", placeholder: str = "", max_length: int = 50):
        self.rect = pygame.Rect(x, y, width, height)
        self.label = label
        self.placeholder = placeholder
        self.max_length = max_length
        
        self.text = ""
        self.cursor_pos = 0
        self.focused = False
        
        self.audio = get_audio_manager()
        
        # Görsel ayarlar
        self.bg_color = (45, 40, 55)
        self.border_color = (120, 90, 60)
        self.focus_color = (218, 165, 32)
        self.text_color = (245, 240, 230)
        self.placeholder_color = (150, 145, 140)
        
        self._font = None
    
    def get_font(self):
        if self._font is None:
            self._font = get_font(24)
        return self._font
    
    def focus(self):
        """Odaklan"""
        self.focused = True
        self.cursor_pos = len(self.text)
        
        if self.label:
            self.audio.speak(f"{self.label}. ", interrupt=True)
        
        if self.text:
            self.audio.speak(f"Mevcut: {self.text}")
        else:
            self.audio.speak(f"Boş. {self.placeholder}")
        
        self.audio.speak("Yazın ve Enter ile onaylayın. Escape ile iptal.")
    
    def unfocus(self):
        """Odağı kaldır"""
        self.focused = False
    
    def handle_event(self, event) -> bool:
        """Olayları işle"""
        if not self.focused:
            return False
        
        if event.type == pygame.KEYDOWN:
            # Enter - Onay (parent ekrana bırak)
            if event.key == pygame.K_RETURN:
                self.audio.play_ui_sound('enter')  # Enter sesi
                # Parent ekranın işleyebilmesi için False döndür
                return False
            
            # Escape - İptal
            if event.key == pygame.K_ESCAPE:
                self.audio.speak("İptal edildi", interrupt=True)
                self.unfocus()
                return True
            
            # Sol ok - Cursor sola
            if event.key == pygame.K_LEFT:
                if self.cursor_pos > 0:
                    self.cursor_pos -= 1
                    char = self.text[self.cursor_pos]
                    self._speak_char(char)
                else:
                    self.audio.speak("Başlangıç", interrupt=True)
                return True
            
            # Sağ ok - Cursor sağa
            if event.key == pygame.K_RIGHT:
                if self.cursor_pos < len(self.text):
                    char = self.text[self.cursor_pos]
                    self._speak_char(char)
                    self.cursor_pos += 1
                else:
                    self.audio.speak("Son", interrupt=True)
                return True
            
            # Home - Başa git
            if event.key == pygame.K_HOME:
                self.cursor_pos = 0
                self.audio.speak("Başlangıç", interrupt=True)
                return True
            
            # End - Sona git
            if event.key == pygame.K_END:
                self.cursor_pos = len(self.text)
                self.audio.speak("Son", interrupt=True)
                return True
            
            # Backspace - Sil (cursordan önce)
            if event.key == pygame.K_BACKSPACE:
                if self.cursor_pos > 0:
                    deleted = self.text[self.cursor_pos - 1]
                    self.text = self.text[:self.cursor_pos-1] + self.text[self.cursor_pos:]
                    self.cursor_pos -= 1
                    self.audio.play_ui_sound('delete')  # Silme sesi
                    self._speak_char(deleted, prefix="silindi: ")
                else:
                    self.audio.speak("Silinecek karakter yok", interrupt=True)
                return True
            
            # Delete - Sil (cursordan sonra)
            if event.key == pygame.K_DELETE:
                if self.cursor_pos < len(self.text):
                    deleted = self.text[self.cursor_pos]
                    self.text = self.text[:self.cursor_pos] + self.text[self.cursor_pos+1:]
                    self.audio.play_ui_sound('delete')  # Silme sesi
                    self._speak_char(deleted, prefix="silindi: ")
                else:
                    self.audio.speak("Silinecek karakter yok", interrupt=True)
                return True
            
            # Ctrl+A - Tümünü seç ve sil
            if event.key == pygame.K_a and pygame.key.get_mods() & pygame.KMOD_CTRL:
                if self.text:
                    deleted_text = self.text
                    self.text = ""
                    self.cursor_pos = 0
                    self.audio.play_ui_sound('delete')
                    self.audio.speak(f"Tümü silindi: {deleted_text}", interrupt=True)
                else:
                    self.audio.speak("Zaten boş", interrupt=True)
                return True
            
            # Ctrl+V - Yapıştır
            if event.key == pygame.K_v and (pygame.key.get_mods() & pygame.KMOD_CTRL):
                try:
                    if SCRAP_AVAILABLE:
                        clipboard = pygame.scrap.get(pygame.SCRAP_TEXT)
                        if clipboard:
                            # Bytes to string
                            if isinstance(clipboard, bytes):
                                clipboard = clipboard.decode('utf-8').rstrip('\x00')
                            paste_text = clipboard[:self.max_length - len(self.text)]
                            if paste_text:
                                self.text = self.text[:self.cursor_pos] + paste_text + self.text[self.cursor_pos:]
                                self.cursor_pos += len(paste_text)
                                self.audio.speak(f"Yapıştırıldı: {paste_text}", interrupt=True)
                            else:
                                self.audio.speak("Yapıştırılacak yer yok", interrupt=True)
                        else:
                            self.audio.speak("Panoda metin yok", interrupt=True)
                    else:
                        self.audio.speak("Yapıştırma desteklenmiyor", interrupt=True)
                except Exception as e:
                    self.audio.speak("Yapıştırma hatası", interrupt=True)
                return True
            
            # Normal karakter girişi
            if event.unicode and event.unicode.isprintable():
                if len(self.text) < self.max_length:
                    char = event.unicode
                    self.text = self.text[:self.cursor_pos] + char + self.text[self.cursor_pos:]
                    self.cursor_pos += 1
                    # Yazma sesi çal (boşluk için farklı ses)
                    if char == ' ':
                        self.audio.play_ui_sound('space')  # Boşluk sesi
                    else:
                        self.audio.play_ui_sound('type')  # Normal yazma sesi
                    self._speak_char(char)
                else:
                    self.audio.speak("Maksimum uzunluğa ulaşıldı", interrupt=True)
                return True
        
        return False
    
    def _speak_char(self, char: str, prefix: str = ""):
        """Karakteri oku"""
        # Özel karakterler için açıklama
        char_names = {
            ' ': 'boşluk',
            '.': 'nokta',
            ',': 'virgül',
            ':': 'iki nokta',
            ';': 'noktalı virgül',
            '!': 'ünlem',
            '?': 'soru işareti',
            '@': 'at işareti',
            '#': 'diyez',
            '$': 'dolar',
            '%': 'yüzde',
            '&': 've işareti',
            '*': 'yıldız',
            '(': 'açık parantez',
            ')': 'kapalı parantez',
            '-': 'tire',
            '_': 'alt çizgi',
            '=': 'eşittir',
            '+': 'artı',
            '/': 'bölü',
            '\\': 'ters bölü',
            "'": 'tek tırnak',
            '"': 'çift tırnak',
            '<': 'küçüktür',
            '>': 'büyüktür',
        }
        
        name = char_names.get(char, char)
        self.audio.speak(f"{prefix}{name}", interrupt=True)
    
    def get_text(self) -> str:
        """Metni döndür"""
        return self.text
    
    def set_text(self, text: str):
        """Metni ayarla"""
        self.text = text[:self.max_length]
        self.cursor_pos = len(self.text)
    
    def clear(self):
        """Metni temizle"""
        self.text = ""
        self.cursor_pos = 0
    
    def draw(self, surface: pygame.Surface):
        """Çiz"""
        font = self.get_font()
        
        # Arkaplan
        pygame.draw.rect(surface, self.bg_color, self.rect)
        
        # Kenarlık
        border_color = self.focus_color if self.focused else self.border_color
        pygame.draw.rect(surface, border_color, self.rect, 2)
        
        # Etiket
        if self.label:
            label_surf = font.render(self.label + ":", True, self.text_color)
            surface.blit(label_surf, (self.rect.x, self.rect.y - 25))
        
        # Metin veya placeholder
        if self.text:
            text_surf = font.render(self.text, True, self.text_color)
        else:
            text_surf = font.render(self.placeholder, True, self.placeholder_color)
        
        # Metin konumu
        text_rect = text_surf.get_rect(midleft=(self.rect.x + 10, self.rect.centery))
        surface.blit(text_surf, text_rect)
        
        # Cursor
        if self.focused:
            cursor_x = self.rect.x + 10 + font.size(self.text[:self.cursor_pos])[0]
            pygame.draw.line(
                surface,
                self.text_color,
                (cursor_x, self.rect.y + 5),
                (cursor_x, self.rect.bottom - 5),
                2
            )
