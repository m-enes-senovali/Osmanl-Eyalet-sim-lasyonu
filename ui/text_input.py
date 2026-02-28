# -*- coding: utf-8 -*-
"""
Osmanlı Eyalet Yönetim Simülasyonu - Kapsamlı Metin Girdisi (Text Input)
Görme engelli oyuncular için erişilebilirlik, metin seçimi (shift), kopyalama/yapıştırma (ctrl+c, ctrl+v) destekleri içerir.
"""

import pygame
import base64
import os
import ctypes
from config import COLORS, FONTS, get_font
from audio.audio_manager import get_audio_manager

# Pyperclip sorun çıkarırsa diye Windows tabanlı basit Panolama:
def get_clipboard():
    try:
        import pyperclip
        return pyperclip.paste()
    except:
        return ""

def set_clipboard(text):
    try:
        import pyperclip
        pyperclip.copy(text)
    except:
        pass

class AccessibleTextInput:
    """Erişilebilir, çok satırlı ve seçilebilir metin kutusu."""
    def __init__(self, x: int, y: int, width: int, height: int, max_chars: int = 500, placeholder: str = "(Yazmaya başlamak için Enter'a basın)", **kwargs):
        # Desteklenmeyen veya eski sürümden kalma argümanları sönümle (label, max_length vb.)
        if 'max_length' in kwargs:
            max_chars = kwargs.get('max_length')
            
        self.rect = pygame.Rect(x, y, width, height)
        self.max_chars = max_chars
        self.placeholder = placeholder
        self.text = ""
        
        # İmleç (Cursor) Yönetimi
        self.cursor_pos = 0     # String içerisindeki index
        self.selection_start = None # Seçim başlangıç indexi
        
        # UI & Font
        self._font = None
        self.is_focused = False
        
        # Görünüm Kaydırma (Scroll)
        self.scroll_y = 0
        
        # Ses & TTS
        self.audio = get_audio_manager()

    def get_font(self):
        if self._font is None:
            self._font = get_font(FONTS['body'])
        return self._font

    def set_focus(self, focused: bool):
        self.is_focused = focused
        if focused:
            self.audio.play_ui_sound('hover')
            if not self.text:
                self.audio.speak("Metin Kutusu aktif. Yazmaya başlayabilirsiniz.", interrupt=True)
            else:
                self.audio.speak("Metin Kutusuna dönüldü.", interrupt=True)
        else:
            self.selection_start = None

    # Eski ekranlarla (workers_screen, vs.) geriye dönük uyumluluk için alias fonksiyonlar
    def focus(self):
        self.set_focus(True)
        
    def unfocus(self):
        self.set_focus(False)
        
    def get_text(self):
        return self.text

    def _get_selected_text(self):
        """Seçili metni döndür (start, end) indexleriyle birlikte."""
        if self.selection_start is None or self.selection_start == self.cursor_pos:
            return "", 0, 0
        
        start = min(self.selection_start, self.cursor_pos)
        end = max(self.selection_start, self.cursor_pos)
        return self.text[start:end], start, end

    def _delete_selection(self):
        """Seçili kısmı sil, geriye True döndürürse silindi demektir."""
        if self.selection_start is not None and self.selection_start != self.cursor_pos:
            start = min(self.selection_start, self.cursor_pos)
            end = max(self.selection_start, self.cursor_pos)
            
            self.text = self.text[:start] + self.text[end:]
            self.cursor_pos = start
            self.selection_start = None
            return True
        return False

    def _insert_text(self, new_text: str):
        self._delete_selection()
        
        # Kalan karakter kapasitesine göre kırp
        remaining = self.max_chars - len(self.text)
        if remaining > 0:
            insert_str = new_text[:remaining]
            self.text = self.text[:self.cursor_pos] + insert_str + self.text[self.cursor_pos:]
            self.cursor_pos += len(insert_str)

    def set_text(self, new_text: str):
        """Dışarıdan (kod üzerinden) metni doğrudan değiştirmeyi sağlar."""
        self.text = str(new_text)[:self.max_chars]
        self.cursor_pos = len(self.text)
        self.selection_start = None

    def _get_char_at(self, pos):
        if 0 <= pos < len(self.text):
            return self.text[pos]
        return ""

    def _get_word_boundaries(self, current_pos, direction):
        """Ctrl + Sol/Sağ ok için kelime atlama"""
        pos = current_pos
        
        if direction == -1: # Sola git
            if pos <= 0: return 0
            pos -= 1
            while pos > 0 and self.text[pos].isspace(): pos -= 1
            while pos > 0 and not self.text[pos-1].isspace(): pos -= 1
            return pos
            
        elif direction == 1: # Sağa git
            if pos >= len(self.text): return len(self.text)
            while pos < len(self.text) and not self.text[pos].isspace(): pos += 1
            while pos < len(self.text) and self.text[pos].isspace(): pos += 1
            return pos

    def handle_event(self, event) -> bool:
        if not self.is_focused:
            return False

        if event.type == pygame.KEYDOWN:
            mods = pygame.key.get_mods()
            ctrl_pressed = (mods & pygame.KMOD_CTRL)
            shift_pressed = (mods & pygame.KMOD_SHIFT)

            # ESC: Odak çıkışı (SupportScreen handle_event içinde _go_back tetiklememek için is_typing bool dönüyoruz)
            if event.key == pygame.K_ESCAPE:
                self.is_focused = False
                self.selection_start = None
                self.audio.play_ui_sound('click')
                self.audio.speak("Kategori seçimine dönüldü.", interrupt=True)
                return True

            # --- PANOLAMA İŞLEMLERİ ---
            if ctrl_pressed:
                if event.key == pygame.K_RETURN:
                    # Gönderimi Tetikleyecek, False dönelim ki support screen yakalasın
                    return False
                elif event.key == pygame.K_a: # Tümünü Seç
                    self.selection_start = 0
                    self.cursor_pos = len(self.text)
                    self.audio.speak("Tüm metin seçildi", interrupt=True)
                    return True
                elif event.key == pygame.K_c: # Kopyala
                    selected, _, _ = self._get_selected_text()
                    if selected:
                        set_clipboard(selected)
                        self.audio.speak("Panoya kopyalandı", interrupt=True)
                    return True
                elif event.key == pygame.K_x: # Kes
                    selected, _, _ = self._get_selected_text()
                    if selected:
                        set_clipboard(selected)
                        self._delete_selection()
                        self.audio.play_game_sound('ui', 'tick')
                        self.audio.speak("Kesildi", interrupt=True)
                    return True
                elif event.key == pygame.K_v: # Yapıştır
                    clipboard_data = get_clipboard()
                    if clipboard_data:
                        self._insert_text(clipboard_data)
                        self.audio.play_game_sound('ui', 'tick')
                        self.audio.speak("Pano içeriği yapıştırıldı", interrupt=True)
                    return True

            # --- NAVİGASYON VE SEÇİM ---
            if shift_pressed and self.selection_start is None:
                self.selection_start = self.cursor_pos
            elif not shift_pressed and event.key in (pygame.K_LEFT, pygame.K_RIGHT, pygame.K_UP, pygame.K_DOWN, pygame.K_HOME, pygame.K_END):
                self.selection_start = None

            if event.key == pygame.K_LEFT:
                old_pos = self.cursor_pos
                if ctrl_pressed:
                    self.cursor_pos = self._get_word_boundaries(self.cursor_pos, -1)
                else:
                    self.cursor_pos = max(0, self.cursor_pos - 1)
                
                if self.cursor_pos != old_pos:
                    char = self._get_char_at(self.cursor_pos)
                    if char == "\n": char = "yeni satır"
                    elif char == " ": char = "boşluk"
                    
                    if shift_pressed:
                        self.audio.speak(f"Seçildi: {char}", interrupt=True)
                    else:
                        if ctrl_pressed:
                            # Kelimeyi bul
                            word = self.text[self.cursor_pos:old_pos]
                            self.audio.speak(word.strip(), interrupt=True)
                        else:
                            self.audio.speak(char, interrupt=True)
                else:
                    self.audio.speak("Metnin başı", interrupt=True)
                return True

            elif event.key == pygame.K_RIGHT:
                old_pos = self.cursor_pos
                if ctrl_pressed:
                    self.cursor_pos = self._get_word_boundaries(self.cursor_pos, 1)
                else:
                    self.cursor_pos = min(len(self.text), self.cursor_pos + 1)
                
                if self.cursor_pos != old_pos:
                    char = self._get_char_at(old_pos)
                    if char == "\n": char = "yeni satır"
                    elif char == " ": char = "boşluk"
                    
                    if shift_pressed:
                        self.audio.speak(f"Seçildi: {char}", interrupt=True)
                    else:
                        if ctrl_pressed:
                            word = self.text[old_pos:self.cursor_pos]
                            self.audio.speak(word.strip(), interrupt=True)
                        else:
                            self.audio.speak(char, interrupt=True)
                else:
                    self.audio.speak("Metnin sonu", interrupt=True)
                return True
                
            elif event.key == pygame.K_UP:
                lines = self.text.split('\n')
                current_line_idx = self.text[:self.cursor_pos].count('\n')
                if current_line_idx > 0:
                    prev_line = lines[current_line_idx - 1]
                    self.audio.speak(prev_line if prev_line else "Boş satır", interrupt=True)
                    # cursor'ı üst satırın başına al
                    new_pos = sum(len(l) + 1 for l in lines[:current_line_idx - 1])
                    self.cursor_pos = new_pos
                else:
                    current_line = lines[0] if lines else ""
                    self.audio.speak(current_line if current_line else "Boş satır", interrupt=True)
                    self.cursor_pos = 0
                return True
                
            elif event.key == pygame.K_DOWN:
                lines = self.text.split('\n')
                current_line_idx = self.text[:self.cursor_pos].count('\n')
                if current_line_idx < len(lines) - 1:
                    next_line = lines[current_line_idx + 1]
                    self.audio.speak(next_line if next_line else "Boş satır", interrupt=True)
                    new_pos = sum(len(l) + 1 for l in lines[:current_line_idx + 1])
                    self.cursor_pos = new_pos
                else:
                    current_line = lines[-1] if lines else ""
                    self.audio.speak(current_line if current_line else "Boş satır", interrupt=True)
                    self.cursor_pos = len(self.text)
                return True

            elif event.key in (pygame.K_HOME, pygame.K_END):
                if event.key == pygame.K_HOME:
                    self.cursor_pos = 0
                    self.audio.speak("En başa dönüldü", interrupt=True)
                else:
                    self.cursor_pos = len(self.text)
                    self.audio.speak("En sona gidildi", interrupt=True)
                return True

            # --- DÜZENLEME ---
            elif event.key == pygame.K_BACKSPACE:
                if self._delete_selection():
                    self.audio.play_game_sound('ui', 'backspace')
                    self.audio.speak("Seçim silindi", interrupt=True)
                elif self.cursor_pos > 0:
                    deleted_char = self.text[self.cursor_pos - 1]
                    self.text = self.text[:self.cursor_pos - 1] + self.text[self.cursor_pos:]
                    self.cursor_pos -= 1
                    self.audio.play_game_sound('ui', 'backspace')
                    
                    if deleted_char == "\n": deleted_char = "yeni satır"
                    elif deleted_char == " ": deleted_char = "boşluk"
                    self.audio.speak(f"{deleted_char} silindi", interrupt=True)
                return True
                
            elif event.key == pygame.K_DELETE:
                if self._delete_selection():
                    self.audio.play_game_sound('ui', 'backspace')
                    self.audio.speak("Seçim silindi", interrupt=True)
                elif self.cursor_pos < len(self.text):
                    deleted_char = self.text[self.cursor_pos]
                    self.text = self.text[:self.cursor_pos] + self.text[self.cursor_pos + 1:]
                    self.audio.play_game_sound('ui', 'backspace')
                    
                    if deleted_char == "\n": deleted_char = "yeni satır"
                    elif deleted_char == " ": deleted_char = "boşluk"
                    self.audio.speak(f"{deleted_char} silindi", interrupt=True)
                return True

            elif event.key == pygame.K_RETURN:
                if not ctrl_pressed:
                    self._insert_text("\n")
                    self.audio.play_game_sound('ui', 'type')
                    self.audio.speak("Yeni satır", interrupt=True)
                    return True
                return False

            # --- NORMAL YAZI GİRİŞİ ---
            else:
                if event.unicode and len(self.text) < self.max_chars:
                    if event.unicode >= ' ' or event.unicode in ('\n',):
                        self._insert_text(event.unicode)
                        try:
                            if event.unicode == ' ':
                                self.audio.play_game_sound('ui', 'space')
                                self.audio.speak("Boşluk", interrupt=True)
                            else:
                                self.audio.play_game_sound('ui', 'type')
                                self.audio.speak(event.unicode, interrupt=True)
                        except: pass
                        return True
                        
        return False

    def draw(self, surface: pygame.Surface):
        # Arka plan
        bg_color = (60, 55, 75) if self.is_focused else COLORS['panel_bg']
        pygame.draw.rect(surface, bg_color, self.rect)
        
        # Kenarlık
        border_color = COLORS['highlight'] if self.is_focused else COLORS['panel_border']
        pygame.draw.rect(surface, border_color, self.rect, 2)
        
        font = self.get_font()
        
        if not self.is_focused and not self.text:
            hint = font.render(self.placeholder, True, COLORS['text_dim'])
            surface.blit(hint, (self.rect.x + 10, self.rect.y + 10))
            return

        # Çok basit render (word wrap yapmadan, satır satır bölerek kaba görünüm ile hızı artırmak için)
        lines = self.text.split('\n')
        
        y_offset = self.rect.y + 10 - self.scroll_y
        x_offset = self.rect.x + 10
        
        # Cursor'un görsel koordinatları
        cursor_visual_pos = None 

        char_idx = 0
        has_sel = self.selection_start is not None and self.selection_start != self.cursor_pos
        sel_start = min(self.selection_start or 0, self.cursor_pos) if has_sel else -1
        sel_end = max(self.selection_start or 0, self.cursor_pos) if has_sel else -1
        
        for p_line in lines:
            line_surf = font.render(p_line, True, COLORS['text'])
            surface.blit(line_surf, (x_offset, y_offset))
            
            # Bu satırın içinde seçim varsa
            if has_sel:
                line_end = char_idx + len(p_line)
                if not (sel_end < char_idx or sel_start > line_end):
                    # Seçim bu satırla kesişiyor
                    overlap_start = max(sel_start, char_idx) - char_idx
                    overlap_end = min(sel_end, line_end) - char_idx
                    
                    if overlap_start < overlap_end:
                        pre_w = font.size(p_line[:overlap_start])[0]
                        sel_w = font.size(p_line[overlap_start:overlap_end])[0]
                        # Arka planı boya
                        bg_rect = pygame.Rect(x_offset + pre_w, y_offset, sel_w, font.get_linesize())
                        s = pygame.Surface((bg_rect.width, bg_rect.height), pygame.SRCALPHA)
                        s.fill((100, 100, 255, 128)) # Yarı saydam mavi
                        surface.blit(s, bg_rect)
            
            # Cursor hizada mı?
            if char_idx <= self.cursor_pos <= char_idx + len(p_line):
                offset_char = self.cursor_pos - char_idx
                cursor_x = x_offset + font.size(p_line[:offset_char])[0]
                cursor_visual_pos = (cursor_x, y_offset)
                
            char_idx += len(p_line) + 1 # +1 is \n
            y_offset += font.get_linesize()
            
        if cursor_visual_pos is None:
            # En sona
            cursor_visual_pos = (x_offset, y_offset - font.get_linesize())

        # Cursor Çiz
        if self.is_focused and pygame.time.get_ticks() % 1000 < 500:
            cx, cy = cursor_visual_pos
            pygame.draw.line(surface, COLORS['text'], (cx, cy), (cx, cy + font.get_linesize()), 2)
            
        # Basit Scroll (Metin kutudan taşmasın)
        cy = cursor_visual_pos[1] if cursor_visual_pos else 0
        if cy > self.rect.bottom - 30:
            self.scroll_y += font.get_linesize()
        elif cy < self.rect.top + 10 and self.scroll_y > 0:
            self.scroll_y -= font.get_linesize()
            
        # Karakter Sınırı Çiz
        char_count_str = f"{len(self.text)} / {self.max_chars}"
        color = COLORS['danger'] if len(self.text) >= self.max_chars - 10 else COLORS['text_dim']
        char_surf = self.get_font().render(char_count_str, True, color)
        surface.blit(char_surf, (self.rect.right - 80, self.rect.bottom + 5))
