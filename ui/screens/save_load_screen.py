# -*- coding: utf-8 -*-
"""
Osmanlı Eyalet Yönetim Simülasyonu - Kayıt Yuvası Ekranı
"""

import pygame
from ui.screen_manager import BaseScreen, ScreenType
from ui.components import Button, MenuList, Panel
from config import COLORS, FONTS, SCREEN_WIDTH, SCREEN_HEIGHT


class SaveLoadScreen(BaseScreen):
    """Kayıt yuvası seçim ekranı"""
    
    def __init__(self, screen_manager):
        super().__init__(screen_manager)
        
        self.mode = 'save'  # 'save' veya 'load'
        
        # Silme onayı durumu
        self.confirmation_pending = False
        self.pending_delete_slot = None
        
        # Yuva menüsü
        self.slot_menu = MenuList(
            x=(SCREEN_WIDTH - 500) // 2,
            y=250,
            width=500,
            item_height=80
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
        
        self._title_font = None
    
    def get_title_font(self):
        if self._title_font is None:
            self._title_font = pygame.font.Font(None, FONTS['header'])
        return self._title_font
    
    def set_mode(self, mode: str):
        """Mod ayarla: 'save' veya 'load'"""
        self.mode = mode
        self._update_slots()
    
    def on_enter(self):
        self._update_slots()
    
    def _update_slots(self):
        """Yuva listesini güncelle"""
        self.slot_menu.clear()
        gm = self.screen_manager.game_manager
        if not gm:
            return
        
        slots = gm.get_save_slots_info()
        
        for info in slots:
            if info['empty']:
                text = f"Yuva {info['slot']}: Boş"
            else:
                text = f"Yuva {info['slot']}: {info['province']} - Yıl {info['year']} ({info['turn']} tur)"
            
            slot_num = info['slot']
            self.slot_menu.add_item(
                text,
                lambda s=slot_num: self._select_slot(s),
                str(slot_num)
            )
    
    def announce_screen(self):
        if self.mode == 'save':
            self.audio.announce_screen_change("Oyun Kaydet")
        else:
            self.audio.announce_screen_change("Oyun Yükle")
        self.audio.speak("Bir yuva seçin. 1, 2 veya 3 tuşlarına basın. Delete ile silin.", interrupt=False)
    
    def handle_event(self, event) -> bool:
        # Onay bekleniyorsa özel işle
        if self.confirmation_pending:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_e:  # E = Evet
                    self._confirm_delete()
                    return True
                elif event.key == pygame.K_h or event.key == pygame.K_ESCAPE:  # H = Hayır veya ESC
                    self._cancel_delete()
                    return True
            return True  # Diğer tuşları yoksay
        
        if self.slot_menu.handle_event(event):
            return True
        
        if self.back_button.handle_event(event):
            return True
        
        if event.type == pygame.KEYDOWN:
            # Backspace veya Escape - Geri
            if event.key in (pygame.K_BACKSPACE, pygame.K_ESCAPE):
                self._go_back()
                return True
            
            # 1, 2, 3 - Doğrudan yuva seç
            if event.key == pygame.K_1:
                self._select_slot(1)
                return True
            if event.key == pygame.K_2:
                self._select_slot(2)
                return True
            if event.key == pygame.K_3:
                self._select_slot(3)
                return True
            
            # Delete - Seçili yuvayı sil
            if event.key == pygame.K_DELETE:
                selected = self.slot_menu.selected_index + 1  # 1-indexed
                if 1 <= selected <= 3:
                    self._request_delete(selected)
                return True
        
        return False
    
    def _request_delete(self, slot: int):
        """Silme onayı iste"""
        gm = self.screen_manager.game_manager
        if not gm:
            return
        
        slots = gm.get_save_slots_info()
        slot_info = next((s for s in slots if s['slot'] == slot), None)
        
        if slot_info and not slot_info['empty']:
            self.confirmation_pending = True
            self.pending_delete_slot = slot
            self.audio.speak(
                f"Yuva {slot} silinecek. {slot_info['province']}, Yıl {slot_info['year']}. "
                "Emin misiniz? E: Evet, H: Hayır",
                interrupt=True
            )
        else:
            self.audio.speak(f"Yuva {slot} zaten boş.", interrupt=True)
    
    def _confirm_delete(self):
        """Silmeyi onayla"""
        if self.pending_delete_slot:
            gm = self.screen_manager.game_manager
            if gm:
                success = gm.delete_save(self.pending_delete_slot)
                if success:
                    self.audio.speak(f"Yuva {self.pending_delete_slot} silindi.", interrupt=True)
                else:
                    self.audio.speak("Silme başarısız.", interrupt=True)
                self._update_slots()
        
        self.confirmation_pending = False
        self.pending_delete_slot = None
    
    def _cancel_delete(self):
        """Silmeyi iptal et"""
        self.audio.speak("Silme iptal edildi.", interrupt=True)
        self.confirmation_pending = False
        self.pending_delete_slot = None
    
    def draw(self, surface: pygame.Surface):
        # Başlık
        title_font = self.get_title_font()
        title_text = "💾 OYUN KAYDET" if self.mode == 'save' else "📂 OYUN YÜKLE"
        title = title_font.render(title_text, True, COLORS['gold'])
        title_rect = title.get_rect(centerx=SCREEN_WIDTH // 2, top=80)
        surface.blit(title, title_rect)
        
        # Alt başlık
        subtitle_font = pygame.font.Font(None, FONTS['body'])
        subtitle = subtitle_font.render("Bir kayıt yuvası seçin", True, COLORS['text'])
        subtitle_rect = subtitle.get_rect(centerx=SCREEN_WIDTH // 2, top=150)
        surface.blit(subtitle, subtitle_rect)
        
        # Yuva menüsü
        self.slot_menu.draw(surface)
        
        # Geri butonu
        self.back_button.draw(surface)
        
        # Mevcut oyun bilgisi (kaydetme modunda)
        if self.mode == 'save':
            gm = self.screen_manager.game_manager
            if gm and gm.save_slot:
                info_font = pygame.font.Font(None, FONTS['small'])
                info = info_font.render(
                    f"Mevcut oyun: Yuva {gm.save_slot}",
                    True, COLORS['gold']
                )
                info_rect = info.get_rect(centerx=SCREEN_WIDTH // 2, bottom=SCREEN_HEIGHT - 100)
                surface.blit(info, info_rect)
    
    def _select_slot(self, slot: int):
        """Yuva seç"""
        gm = self.screen_manager.game_manager
        if not gm:
            return
        
        if self.mode == 'save':
            gm.save_game(slot)
            self._go_back()
        else:
            success = gm.load_game(slot)
            if success:
                self.screen_manager.change_screen(ScreenType.PROVINCE_VIEW)
    
    def _go_back(self):
        """Geri dön"""
        if self.mode == 'save':
            self.screen_manager.change_screen(ScreenType.PROVINCE_VIEW)
        else:
            self.screen_manager.change_screen(ScreenType.MAIN_MENU)
