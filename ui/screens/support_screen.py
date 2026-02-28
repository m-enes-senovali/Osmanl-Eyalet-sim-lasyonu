# -*- coding: utf-8 -*-
"""
Osmanlı Eyalet Yönetim Simülasyonu
Destek ve Geri Bildirim Ekranı (Oyun İçi Ticket Sistemi)
"""

import pygame
import webbrowser
from ui.screen_manager import BaseScreen, ScreenType
from ui.components import Button, Panel, MenuList
from config import COLORS, FONTS, SCREEN_WIDTH, SCREEN_HEIGHT, get_font
from api.support_api import get_support_api
from ui.text_input import AccessibleTextInput

class SupportScreen(BaseScreen):
    """Oyuncuların Hata, Öneri veya Şikayet bildirebileceği ekran."""

    def __init__(self, screen_manager):
        super().__init__(screen_manager)
        
        # Paneller
        self.main_panel = Panel(
            (SCREEN_WIDTH - 600) // 2, 
            (SCREEN_HEIGHT - 500) // 2, 
            600, 500, 
            "Destek ve Bildirim Sandığı"
        )
        
        # Durum ve Akış (Flow) Yönetimi
        # step 0: Platform Seçimi, step 1: Kategori ve Mesaj (veya Email)
        self.step = 0
        self.platforms = ["GitHub Üzerinden Gönder", "Geliştiriciye E-Posta Gönder", "WhatsApp Grubuna Başvur"]
        self.selected_platform_idx = 0
        
        self.categories = ["Öneri / Fikir", "Hata (Bug) Bildirimi", "Diğer"]
        self.selected_category_idx = 0
        
        # Metin girişleri
        box_x = self.main_panel.rect.x + 20
        # E-posta seçeneğinde İsim ve E-Posta ekstra alanları olacak
        self.name_input = AccessibleTextInput(box_x, self.main_panel.rect.y + 110, self.main_panel.rect.width - 40, 40, max_chars=100, placeholder="İsim / Unvanınız")
        self.email_input = AccessibleTextInput(box_x, self.main_panel.rect.y + 160, self.main_panel.rect.width - 40, 40, max_chars=100, placeholder="E-Posta Adresiniz (Cevap için)")
        self.subject_input = AccessibleTextInput(box_x, self.main_panel.rect.y + 210, self.main_panel.rect.width - 40, 40, max_chars=150, placeholder="Konu Başlığı")
        self.text_input = AccessibleTextInput(box_x, self.main_panel.rect.y + 260, self.main_panel.rect.width - 40, 200, max_chars=500, placeholder="Mektubunuzu buraya yazın...")
        
        # Hangi girdi kutusundayız 
        # (0: Category, 1: Name, 2: Email, 3: Subject, 4: Message, 5: Submit Button)
        self.active_input_idx = 0
        
        # Durum bilgilendirmesi
        self.status_message = "Lütfen Padişaha veya Geliştiricilere iletmek istediğiniz mektubu yazın."
        self.status_color = COLORS['text']
        self.is_sending = False
        
        # Seçenek Menüleri
        self.platform_list = MenuList(self.main_panel.rect.x + 20, self.main_panel.rect.y + 100, 400, 100)
        self.category_list = MenuList(self.main_panel.rect.x + 20, self.main_panel.rect.y + 60, 250, 150)
        self._update_lists()
        
        # Butonlar
        btn_y = self.main_panel.rect.bottom - 60
        btn_center_x = self.main_panel.rect.centerx
        
        self.btn_send = Button(
            btn_center_x - 160, btn_y, 140, 40, 
            "Devam (Enter)", shortcut=None, callback=self._handle_action_btn
        )
        
        self.btn_cancel = Button(
            btn_center_x + 20, btn_y, 140, 40, 
            "İptal (ESC)", shortcut=None, callback=self._go_back
        )
        
        # API Bağlantısı
        self.api = get_support_api()
        
    def get_header_font(self):
        return get_font(FONTS['subheader'])
        
    def get_body_font(self):
        return get_font(FONTS['body'])
        
    def on_enter(self):
        """Ekrana girildiğinde."""
        self.step = 0
        self.selected_platform_idx = 0
        self.selected_category_idx = 0
        self.active_input_idx = 0
        
        self.name_input.text = ""
        self.name_input.cursor_pos = 0
        self.name_input.set_focus(False)
        
        self.email_input.text = ""
        self.email_input.cursor_pos = 0
        self.email_input.set_focus(False)
        
        self.subject_input.text = ""
        self.subject_input.cursor_pos = 0
        self.subject_input.set_focus(False)
        
        self.text_input.text = ""
        self.text_input.cursor_pos = 0
        self.text_input.set_focus(False)
        
        self.status_message = "Lütfen Padişaha veya Geliştiricilere iletmek istediğiniz mektubu yazın."
        self.status_color = COLORS['text']
        self.is_sending = False
        self.btn_send.text = "Devam (Enter)"
        
        if not self.api.is_ready:
            self.status_message = "UYARI: Güvenlik anahtarları bulunamadı. Bildirim gönderilemeyecek."
            self.status_color = COLORS['danger']
            
        self.announce_screen()
        
    def announce_screen(self):
        self.audio.announce_screen_change("Destek Bildirim Ekranı")
        if self.step == 0:
            self.audio.speak(
                "Buradan geliştiricilere hata veya öneri bildirebilirsiniz. "
                "Gönderim yöntemini seçmek için Yukarı ve Aşağı ok tuşularını kullanın. "
                "Seçimi onaylayıp devam etmek için Enter'a basın.", 
                interrupt=False
            )
        else:
            self.audio.speak(
                "Detay ekranı. Yukarı ve Aşağı oklarla kategori ve metin kutuları arasında gezinebilirsiniz. "
                "Metin mesajınızı girdikten sonra Control ve Enter tuşuna basarak gönderebilirsiniz.", 
                interrupt=False
            )
        
    def _update_lists(self):
        self.platform_list.clear()
        for i, plat in enumerate(self.platforms):
            prefix = "► " if i == self.selected_platform_idx else "  "
            self.platform_list.add_item(plat, prefix + plat)
            
        self.category_list.clear()
        for i, cat in enumerate(self.categories):
            prefix = "► " if i == self.selected_category_idx else "  "
            self.category_list.add_item(cat, prefix + cat)
            
    def _change_selection(self, delta):
        if self.is_sending: return
        
        if self.step == 0:
            self.selected_platform_idx = (self.selected_platform_idx + delta) % len(self.platforms)
            self._update_lists()
            self.audio.play_game_sound('ui', 'tick')
            self.audio.speak(f"Seçilen yöntem: {self.platforms[self.selected_platform_idx]}", interrupt=True)
        else:
            if self.active_input_idx == 0: # Kategorideyiz
                self.selected_category_idx = (self.selected_category_idx + delta) % len(self.categories)
                self._update_lists()
                self.audio.play_game_sound('ui', 'tick')
                self.audio.speak(f"Kategori: {self.categories[self.selected_category_idx]}", interrupt=True)

            
    def _handle_action_btn(self):
        """Enter veya Butona tıklandığında (İleri/Gönder)"""
        if self.step == 0:
            if self.selected_platform_idx == 2:
                webbrowser.open("https://chat.whatsapp.com/Jb2NsbWbqWSFVR0opsmxOn")
                self.audio.play_game_sound('ui', 'success')
                self.audio.speak("WhatsApp davet bağlantısı tarayıcınızda açıldı.", interrupt=True)
                return
                
            self.step = 1
            self.active_input_idx = 0
            self.btn_send.text = "Gönder"
            
            # Seçime göre layout güncelle (Y koordinatları düzenlemesi)
            box_x = self.main_panel.rect.x + 20
            if self.selected_platform_idx == 1: # E-Posta Seçildi
                self.name_input.rect.y = self.main_panel.rect.y + 110
                self.email_input.rect.y = self.main_panel.rect.y + 170
                self.subject_input.rect.y = self.main_panel.rect.y + 230
                self.text_input.rect.y = self.main_panel.rect.y + 290
                self.text_input.rect.height = 80
            else: # GitHub
                # Name ve Email atlandığı için Subject yukarı çekilir
                self.subject_input.rect.y = self.main_panel.rect.y + 110
                self.text_input.rect.y = self.main_panel.rect.y + 175
                self.text_input.rect.height = 175
                
            self.announce_screen()
            self.audio.play_game_sound('ui', 'hover') # Transition sound
            pygame.time.set_timer(pygame.USEREVENT + 99, 3000, 1) # Biraz bekleyip aktif alanı okutalım
            # Asenkron bir şey olmadığı için _announce_active_field'ı direkt çağırmak announce_screen ile çakışabilir.
            # Şimdilik announce_screen yeterli, kullanıcı aşağı yukarı basarak öğrenebilir.
            # Ama ilk alanı bildirmek için _announce_active_field çağırıyoruz.
            self._announce_active_field()
        else:
            self._send_ticket()

    def _send_ticket(self):
        if self.is_sending or self.step == 0:
            return
            
        # Doğrulamalar
        if self.selected_platform_idx == 1:
            if not self.name_input.text.strip():
                self.status_message = "Hata: İsim / Unvan girmelisiniz!"
                self.status_color = COLORS['danger']
                self.audio.play_game_sound('ui', 'error')
                self.audio.speak(self.status_message, interrupt=True)
                self.active_input_idx = 1
                self.name_input.set_focus(True)
                self.email_input.set_focus(False)
                self.subject_input.set_focus(False)
                self.text_input.set_focus(False)
                return
                
            if not self.email_input.text.strip():
                self.status_message = "Hata: E-Posta adresi girmelisiniz!"
                self.status_color = COLORS['danger']
                self.audio.play_game_sound('ui', 'error')
                self.audio.speak(self.status_message, interrupt=True)
                self.active_input_idx = 2
                self.name_input.set_focus(False)
                self.email_input.set_focus(True)
                self.subject_input.set_focus(False)
                self.text_input.set_focus(False)
                return

        if not self.subject_input.text.strip():
            self.status_message = "Hata: Konu başlığı girmelisiniz!"
            self.status_color = COLORS['danger']
            self.audio.play_game_sound('ui', 'error')
            self.audio.speak(self.status_message, interrupt=True)
            self.active_input_idx = 3
            self.name_input.set_focus(False)
            self.email_input.set_focus(False)
            self.subject_input.set_focus(True)
            self.text_input.set_focus(False)
            return

        if not self.text_input.text.strip():
            self.status_message = "Hata: Boş bir mektup gönderemezsiniz!"
            self.status_color = COLORS['danger']
            self.audio.play_game_sound('ui', 'error')
            self.audio.speak(self.status_message, interrupt=True)
            self.active_input_idx = 4
            self.name_input.set_focus(False)
            self.email_input.set_focus(False)
            self.subject_input.set_focus(False)
            self.text_input.set_focus(True)
            return
            
        if not self.api.is_ready:
            self.status_message = "Hata: API anahtarları kurulu değil!"
            self.status_color = COLORS['danger']
            self.audio.play_game_sound('ui', 'error')
            self.audio.speak(self.status_message, interrupt=True)
            return

        self.is_sending = True
        self.name_input.set_focus(False)
        self.email_input.set_focus(False)
        self.subject_input.set_focus(False)
        self.text_input.set_focus(False)
        
        self.status_message = "Gönderiliyor... Güvercin yola çıktı."
        self.status_color = COLORS['highlight']
        self.audio.play_game_sound('ui', 'click')
        self.audio.speak(self.status_message, interrupt=True)
        
        # Oyun mevcut durumu (Debug verisi için)
        gm = self.screen_manager.game_manager
        debug_info = ""
        if gm:
            debug_info = (
                f"Yıl: {gm.current_year}, Tur: {gm.turn_count}\n"
                f"Eyalet: {gm.province.name}\n"
                f"Altın: {getattr(gm.economy.resources, 'gold', 0)}, Nüfus: {gm.population.population.total if hasattr(gm.population, 'population') else 0}\n"
                f"Sadakat: {getattr(gm.diplomacy, 'sultan_loyalty', 0)}, Memnuniyet: {getattr(gm.population, 'happiness', 0)}"
            )
            
        cat_name = self.categories[self.selected_category_idx]
        platform_name = "github" if self.selected_platform_idx == 0 else "email"
        player_name = self.name_input.text.strip() if platform_name == "email" else ""
        player_email = self.email_input.text.strip() if platform_name == "email" else ""
        subject = self.subject_input.text.strip()
        
        final_message = f"Gönderici: {player_name}\n\n{self.text_input.text}" if platform_name == "email" else self.text_input.text
        
        # Asenkron gönderim çağrısı
        self.api.submit_ticket_async(platform_name, cat_name, subject, final_message, debug_info, player_email, self._on_send_result)
        
    def _on_send_result(self, success: bool, message: str):
        """Asenkron Thread tarafından tetiklenen sonuç."""
        self.is_sending = False
        self.status_message = message
        
        if success:
            self.status_color = COLORS['success']
            # Ses API'si ana thread'de çağrılmalıdır normalde ama pygame mixer thread-safe'e yakındır.
            # Temiz bir UI akışı için doğrudan çalıyoruz:
            try:
                self.audio.play_game_sound('ui', 'success')
                self.audio.speak(message, interrupt=True)
                self.text_input.text = ""  # Başarılı olunca temizle
            except:
                pass
        else:
            self.status_color = COLORS['danger']
            try:
                self.audio.play_game_sound('ui', 'error')
                self.audio.speak("Gönderim başarısız: " + message, interrupt=True)
            except:
                pass
                
    def _go_back(self):
        if not self.is_sending:
            if self.step == 1:
                self.step = 0
                self.name_input.set_focus(False)
                self.email_input.set_focus(False)
                self.subject_input.set_focus(False)
                self.text_input.set_focus(False)
                self.btn_send.text = "Devam (Enter)"
                self.audio.play_ui_sound('click')
                self.audio.speak("Platform seçimine dönüldü.", interrupt=True)
            else:
                self.screen_manager.change_screen(ScreenType.MAIN_MENU)
        
    def handle_event(self, event) -> bool:
        if self.btn_send.handle_event(event):
            return True
        if self.btn_cancel.handle_event(event):
            return True
            
        if event.type == pygame.KEYDOWN:
            if self.is_sending:
                return True
                
            mods = pygame.key.get_mods()
            
            # STEP 0: Platform Seçimi
            if self.step == 0:
                if event.key == pygame.K_UP:
                    self._change_selection(-1)
                    return True
                elif event.key == pygame.K_DOWN:
                    self._change_selection(1)
                    return True
                elif event.key == pygame.K_RETURN:
                    self._handle_action_btn()
                    return True
                elif event.key == pygame.K_ESCAPE:
                    self._go_back()
                    return True
                    
            # STEP 1: Detay Girişi
            else:
                # Control + Enter = Gönder (Her durumda çalışır)
                if event.key == pygame.K_RETURN and (mods & pygame.KMOD_CTRL):
                    self._send_ticket()
                    return True
                
                # YAZMA MODU (Form Mode)
                if getattr(self, 'is_typing', False):
                    if event.key == pygame.K_ESCAPE:
                        self.is_typing = False
                        if self.active_input_idx == 1:
                            self.name_input.set_focus(False)
                        elif self.active_input_idx == 2:
                            self.email_input.set_focus(False)
                        elif self.active_input_idx == 3:
                            self.subject_input.set_focus(False)
                        elif self.active_input_idx == 4:
                            self.text_input.set_focus(False)
                        self.audio.speak("Yazma modundan çıkıldı. Form dolaşımındasınız. Kutu değiştirmek için Aşağı ve Yukarı okları kullanın.", interrupt=True)
                        return True
                        
                    # Yazma modundayken tüm tuşlar aktif input'a gider
                    if self.active_input_idx == 1:
                        return self.name_input.handle_event(event)
                    elif self.active_input_idx == 2:
                        return self.email_input.handle_event(event)
                    elif self.active_input_idx == 3:
                        return self.subject_input.handle_event(event)
                    elif self.active_input_idx == 4:
                        return self.text_input.handle_event(event)

                # DOLAŞIM MODU (Browse Mode)
                else:
                    if event.key == pygame.K_ESCAPE:
                        self._go_back()
                        return True
                        
                    # Alanlar arası gezinme
                    if event.key == pygame.K_DOWN:
                        self.active_input_idx += 1
                        if self.selected_platform_idx != 1 and self.active_input_idx == 1:
                            self.active_input_idx = 3 # Email yoksa Name(1) ve Mail(2)'yi atla Subject'e geç
                        if self.active_input_idx > 5:
                            self.active_input_idx = 5
                        self._announce_active_field()
                        return True
                        
                    elif event.key == pygame.K_UP:
                        self.active_input_idx -= 1
                        if self.selected_platform_idx != 1 and self.active_input_idx == 2:
                            self.active_input_idx = 0 # Email yoksa Subject(3)'ten yukarı çıkarken Kategori(0)'a atla
                        if self.active_input_idx < 0:
                            self.active_input_idx = 0
                        self._announce_active_field()
                        return True
                        
                    # Kategori Seçimindeyken Sol/Sağ oklarla değiştir
                    elif event.key in (pygame.K_LEFT, pygame.K_RIGHT) and self.active_input_idx == 0:
                        delta = -1 if event.key == pygame.K_LEFT else 1
                        self._change_selection(delta)
                        return True
                        
                    # Kutulara giriş yap (Enter)
                    elif event.key == pygame.K_RETURN:
                        if self.active_input_idx == 5: # Gönder Butonu
                            self._send_ticket()
                            return True
                            
                        if self.active_input_idx in (1, 2, 3, 4):
                            self.is_typing = True
                            if self.active_input_idx == 1:
                                self.name_input.set_focus(True)
                            elif self.active_input_idx == 2:
                                self.email_input.set_focus(True)
                            elif self.active_input_idx == 3:
                                self.subject_input.set_focus(True)
                            elif self.active_input_idx == 4:
                                self.text_input.set_focus(True)
                            self.audio.play_ui_sound('click')
                            self.audio.speak("Yazma modu açıldı. Çıkmak için Escape tuşuna basın.", interrupt=True)
                        return True
                        
        return False

    def _announce_active_field(self):
        """Dolaşım modunda aktif alanı okur."""
        self.audio.play_game_sound('ui', 'hover')
        if self.active_input_idx == 0:
            cat_name = self.categories[self.selected_category_idx]
            self.audio.speak(f"Kategori seçimi: {cat_name}. Değiştirmek için Sol ve Sağ okları kullanın.", interrupt=True)
        elif self.active_input_idx == 1:
            self.audio.speak("İsim ve Unvan kutusu. İçeriğe girmek ve yazmaya başlamak için Enter tuşuna basın.", interrupt=True)
        elif self.active_input_idx == 2:
            self.audio.speak("E-Posta Adresiniz kutusu. İçeriğe girmek ve yazmaya başlamak için Enter tuşuna basın.", interrupt=True)
        elif self.active_input_idx == 3:
            self.audio.speak("Konu Başlığı kutusu. İçeriğe girmek ve yazmaya başlamak için Enter tuşuna basın.", interrupt=True)
        elif self.active_input_idx == 4:
            self.audio.speak("Mektup mesaj kutusu. İçeriğe girmek ve yazmaya başlamak için Enter tuşuna basın.", interrupt=True)
        elif self.active_input_idx == 5:
            self.audio.speak("Gönder düğmesi. Formu iletmek için Enter tuşuna basın.", interrupt=True)
        
    def update(self, dt: float):
        pass
        
    def draw(self, surface: pygame.Surface):
        # Arka plan karatması
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.fill((0, 0, 0))
        overlay.set_alpha(180)
        surface.blit(overlay, (0, 0))
        
        self.main_panel.draw(surface)
        
        # Durum mesajı (Üst)
        status_surf = self.get_body_font().render(self.status_message, True, self.status_color)
        status_rect = status_surf.get_rect(centerx=self.main_panel.rect.centerx, y=self.main_panel.rect.y + 40)
        surface.blit(status_surf, status_rect)
        
        # Çizim referans noktaları
        x_left = self.main_panel.rect.x + 20
        
        if self.step == 0:
            # Sadece Platform listesi
            title = self.get_header_font().render("Lütfen Gönderim Yöntemini Seçin:", True, COLORS['gold'])
            surface.blit(title, (x_left, self.main_panel.rect.y + 60))
            self.platform_list.draw(surface)
        else:
            # Kategoriler Listesi
            cat_title = self.get_header_font().render("Kategori Seçimi (▲ ▼):", True, COLORS['gold'] if self.active_input_idx == 0 else COLORS['text_dim'])
            surface.blit(cat_title, (x_left, self.main_panel.rect.y + 35))
            self.category_list.draw(surface)
            
            # Seçili duruma göre extra alanlar
            if self.selected_platform_idx == 1: # E-Posta
                # İsim Alanı
                name_color = COLORS['gold'] if self.active_input_idx == 1 else COLORS['text']
                name_title = self.get_body_font().render("İsim / Unvan (Örn: Sadrazam Enes):", True, name_color)
                surface.blit(name_title, (x_left, self.name_input.rect.y - 25))
                self.name_input.draw(surface)
                if self.active_input_idx == 1 and not getattr(self, 'is_typing', False):
                    pygame.draw.rect(surface, COLORS['gold'], self.name_input.rect, 2)
                    
                # E-Posta Alanı
                mail_color = COLORS['gold'] if self.active_input_idx == 2 else COLORS['text']
                mail_title = self.get_body_font().render("E-Posta Adresiniz (Cevap Bekliyorsanız Doldurun):", True, mail_color)
                surface.blit(mail_title, (x_left, self.email_input.rect.y - 25))
                self.email_input.draw(surface)
                if self.active_input_idx == 2 and not getattr(self, 'is_typing', False):
                    pygame.draw.rect(surface, COLORS['gold'], self.email_input.rect, 2)
            
            # Konu Başlığı Kutusu
            subj_color = COLORS['gold'] if self.active_input_idx == 3 else COLORS['text']
            subj_title = self.get_body_font().render("Konu Başlığı:", True, subj_color)
            surface.blit(subj_title, (x_left, self.subject_input.rect.y - 25))
            self.subject_input.draw(surface)
            if self.active_input_idx == 3 and not getattr(self, 'is_typing', False):
                pygame.draw.rect(surface, COLORS['gold'], self.subject_input.rect, 2)

            # Mesaj Kutusu
            msg_color = COLORS['gold'] if self.active_input_idx == 4 else COLORS['text']
            msg_title = self.get_body_font().render("Mesajınız:", True, msg_color)
            surface.blit(msg_title, (x_left, self.text_input.rect.y - 25))
            self.text_input.draw(surface)
            if self.active_input_idx == 4 and not getattr(self, 'is_typing', False):
                pygame.draw.rect(surface, COLORS['gold'], self.text_input.rect, 2)
                
            # Gönder Butonu Vurgusu (Navigate modunda)
            if self.active_input_idx == 5:
                pygame.draw.rect(surface, COLORS['gold'], self.btn_send.rect, 3, border_radius=5)
            
        # Butonlar
        self.btn_send.draw(surface)
        self.btn_cancel.draw(surface)
