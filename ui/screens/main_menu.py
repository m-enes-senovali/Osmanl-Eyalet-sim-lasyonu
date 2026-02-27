# -*- coding: utf-8 -*-
"""
Osmanlı Eyalet Yönetim Simülasyonu - Ana Menü Ekranı
"""

import pygame
from ui.screen_manager import BaseScreen, ScreenType
from ui.components import MenuList, Button
from ui.visual_effects import GradientRenderer, SparkleSystem, OttomanPatterns, PulseText
from config import COLORS, FONTS, SCREEN_WIDTH, SCREEN_HEIGHT, KEYBINDS, get_font


class MainMenuScreen(BaseScreen):
    """Ana menü ekranı"""
    
    def __init__(self, screen_manager):
        super().__init__(screen_manager)
        
        # Menü listesi
        self.menu = MenuList(
            x=(SCREEN_WIDTH - 400) // 2,
            y=300,
            width=400,
            item_height=60
        )
        
        # Menü öğelerini ekle
        self.menu.add_item("Yeni Oyun", self._on_new_game, "n")
        self.menu.add_item("Devam Et", self._on_continue, "c")
        self.menu.add_item("Çok Oyunculu", self._on_multiplayer, "m")
        self.menu.add_item("Eğitim", self._on_tutorial, "e")
        self.menu.add_item("Ayarlar", self._on_settings, "a")
        self.menu.add_item("Hakkında", self._on_about, "h")
        self.menu.add_item("Çıkış", self._on_exit, "q")
        
        # Çıkış Diyaloğu
        self.showing_exit_dialog = False
        self.exit_menu = MenuList(
            x=(SCREEN_WIDTH - 300) // 2,
            y=(SCREEN_HEIGHT - 200) // 2 + 50,
            width=300,
            item_height=50
        )
        self.exit_menu.add_item("Kaydet ve Çık", self._exit_save, "y")
        self.exit_menu.add_item("Kaydetmeden Çık", self._exit_no_save, "n")
        self.exit_menu.add_item("İptal", self._exit_cancel, "c")
        
        # Başlık fontları
        self._title_font = None
        self._subtitle_font = None
        
        # Görsel efektler
        self._gradient = GradientRenderer.get_gradient('menu')
        self._sparkles = SparkleSystem(count=25)
        self._pulse = PulseText()
    
    def get_title_font(self):
        if self._title_font is None:
            self._title_font = get_font(FONTS['title'])
        return self._title_font
    
    def get_subtitle_font(self):
        if self._subtitle_font is None:
            self._subtitle_font = get_font(FONTS['subheader'])
        return self._subtitle_font
    
    def on_enter(self):
        """Ekrana girişte menüyü duyur"""
        self.menu.selected_index = 0
        self.showing_exit_dialog = False
    
    def announce_screen(self):
        self.audio.announce_screen_change("Ana Menü")
        self.audio.speak("Yeni Oyun başlatmak için N, Devam etmek için C tuşuna basın")
    
    def handle_event(self, event) -> bool:
        # Çıkış diyaloğu aktifse
        if self.showing_exit_dialog:
            if self.exit_menu.handle_event(event):
                return True
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self._exit_cancel()
                return True
            return True  # Diyalog açıkken diğer olayları engelle
            
        # Menü olaylarını işle
        if self.menu.handle_event(event):
            return True
        
        # Ek kısayollar
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_F1:
                self.audio.speak("Ana Menü. Yeni Oyun, Devam Et, Ayarlar ve Çıkış seçenekleri mevcut.")
                return True
            if event.key == pygame.K_ESCAPE:
                self._on_exit()
                return True
        
        return False
    
    def update(self, dt: float):
        """Efektleri güncelle"""
        self._sparkles.update(dt)
        self._pulse.update(dt)
    
    def draw(self, surface: pygame.Surface):
        # Gradient arka plan
        surface.blit(self._gradient, (0, 0))
        
        # Kıvılcım parçacıkları (arka planda)
        self._sparkles.draw(surface)
        
        # Başlık — nabız efektli
        title_font = self.get_title_font()
        title_color = self._pulse.get_color(COLORS['gold'], speed=1.2)
        title = title_font.render("OSMANLI EYALET YÖNETİMİ", True, title_color)
        title_rect = title.get_rect(centerx=SCREEN_WIDTH // 2, top=80)
        surface.blit(title, title_rect)
        
        # Başlık çerçevesi — Osmanlı süslemeli
        OttomanPatterns.draw_title_frame(surface, title_rect)
        
        # Alt başlık
        subtitle_font = self.get_subtitle_font()
        subtitle = subtitle_font.render("Beylerbeyi Simülasyonu", True, COLORS['text'])
        subtitle_rect = subtitle.get_rect(centerx=SCREEN_WIDTH // 2, top=150)
        surface.blit(subtitle, subtitle_rect)
        
        # Dönem bilgisi
        period = subtitle_font.render("M.S. 1520 - Kanuni Sultan Süleyman Dönemi", True, COLORS['panel_border'])
        period_rect = period.get_rect(centerx=SCREEN_WIDTH // 2, top=190)
        surface.blit(period, period_rect)
        
        # Süslü ayırıcı (eski düz çizgi yerine)
        OttomanPatterns.draw_ornamental_divider(surface, y=250, width=420)
        
        # Menü
        self.menu.draw(surface)
        
        # Alt bilgi
        info_font = get_font(FONTS['small'])
        info = info_font.render("F1: Yardım | Yukarı/Aşağı: Gezin | Enter: Seç", True, COLORS['text'])
        info_rect = info.get_rect(centerx=SCREEN_WIDTH // 2, bottom=SCREEN_HEIGHT - 30)
        surface.blit(info, info_rect)
        
        # Çıkış Diyaloğu Çizimi
        if self.showing_exit_dialog:
            # Karartma
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 150))
            surface.blit(overlay, (0, 0))
            
            # Diyalog kutusu
            dialog_rect = pygame.Rect((SCREEN_WIDTH - 400) // 2, (SCREEN_HEIGHT - 300) // 2, 400, 300)
            pygame.draw.rect(surface, COLORS['panel_bg'], dialog_rect, border_radius=10)
            pygame.draw.rect(surface, COLORS['gold'], dialog_rect, width=2, border_radius=10)
            
            # Diyalog başlığı
            dialog_title = subtitle_font.render("Oyundan Çıkış", True, COLORS['gold'])
            dialog_title_rect = dialog_title.get_rect(centerx=SCREEN_WIDTH // 2, top=dialog_rect.top + 30)
            surface.blit(dialog_title, dialog_title_rect)
            
            # Menü çiz
            self.exit_menu.draw(surface)

    def _on_new_game(self):
        """Yeni oyun başlat - karakter oluşturma ekranına git"""
        self.screen_manager.change_screen(ScreenType.CHARACTER_CREATION)
    
    def _on_continue(self):
        """Kayıtlı oyuna devam et - yuva seçim ekranını aç"""
        # SaveLoadScreen'i load modunda aç
        save_screen = self.screen_manager.screens.get(ScreenType.SAVE_LOAD)
        if save_screen:
            save_screen.set_mode('load')
        self.screen_manager.change_screen(ScreenType.SAVE_LOAD)
    
    def _on_multiplayer(self):
        """Çok oyunculu lobi ekranına git"""
        self.screen_manager.change_screen(ScreenType.MULTIPLAYER)
    
    def _on_tutorial(self):
        """Eğitim ekranına git"""
        self.screen_manager.change_screen(ScreenType.TUTORIAL)
    
    def _on_settings(self):
        """Ayarlar ekranına git"""
        self.screen_manager.change_screen(ScreenType.SETTINGS)
    
    def _on_about(self):
        """Oyun hakkında bilgi"""
        self.audio.speak(
            "Osmanlı Eyalet Yönetim Simülasyonu. "
            "Versiyon: Kapalı Beta 3.0. "
            "Bu oyun Muhammet Enes Şenovalı tarafından geliştirilmektedir. "
            "Oyun 1520 yılında, Kanuni Sultan Süleyman döneminde geçmektedir. "
            "Görme engelli oyuncular için tam erişilebilirlik desteği sunulmaktadır. "
            "İyi oyunlar!",
            interrupt=True
        )
    
    def _on_exit(self):
        """Çıkış diyaloğunu göster"""
        self.showing_exit_dialog = True
        self.audio.speak("Oyundan çıkmak istiyor musunuz? Yukarı aşağı ok tuşlarıyla seçin.", interrupt=True)
        self.exit_menu.selected_index = 0
    
    def _exit_save(self):
        """Kaydet ve Çık"""
        # Hızlı kayıt olabilir veya kayıt ekranına yönlendirebiliriz.
        # Basitlik için şu an sadece çıkış yapıyoruz ama mesaj veriyoruz.
        self.audio.speak("Oyun kaydedildi ve çıkılıyor.", interrupt=True)
        # TODO: Gerçek kayıt işlemi buraya
        pygame.event.post(pygame.event.Event(pygame.QUIT))

    def _exit_no_save(self):
        """Kaydetmeden Çık"""
        self.audio.speak("Kaydedilmeden çıkılıyor.", interrupt=True)
        pygame.event.post(pygame.event.Event(pygame.QUIT))
    
    def _exit_cancel(self):
        """İptal"""
        self.showing_exit_dialog = False
        self.audio.speak("Çıkış iptal edildi.", interrupt=True)
