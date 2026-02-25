# -*- coding: utf-8 -*-
"""
Osmanlı Eyalet Yönetim Simülasyonu - Karakter Oluşturma Ekranı
İsim ve cinsiyet seçimi
"""

import pygame
from ui.screen_manager import BaseScreen, ScreenType
from ui.components import Button, Panel, MenuList
from ui.text_input import AccessibleTextInput
from config import COLORS, FONTS, SCREEN_WIDTH, SCREEN_HEIGHT, get_font
from game.player import PlayerCharacter, Gender


class CharacterCreationScreen(BaseScreen):
    """Karakter oluşturma ekranı"""
    
    def __init__(self, screen_manager):
        super().__init__(screen_manager)
        
        # Aşama: "gender" -> "name" -> "confirm"
        self.stage = "gender"
        self.selected_gender = None
        self.character_name = ""
        
        # Cinsiyet seçim menüsü
        self.gender_menu = MenuList(
            x=SCREEN_WIDTH // 2 - 250,
            y=250,
            width=500,
            item_height=80
        )
        
        # İsim girişi
        self.name_input = AccessibleTextInput(
            x=SCREEN_WIDTH // 2 - 200,
            y=300,
            width=400,
            height=50,
            label="Karakter İsmi",
            placeholder="İsminizi yazın...",
            max_length=30
        )
        
        # Onay paneli
        self.confirm_panel = Panel(
            SCREEN_WIDTH // 2 - 250,
            200,
            500,
            300,
            "Karakter Özeti"
        )
        
        # Butonlar
        self.next_button = Button(
            x=SCREEN_WIDTH // 2 + 50,
            y=SCREEN_HEIGHT - 100,
            width=150,
            height=50,
            text="İleri",
            shortcut="return",
            callback=self._next_stage
        )
        
        self.back_button = Button(
            x=SCREEN_WIDTH // 2 - 200,
            y=SCREEN_HEIGHT - 100,
            width=150,
            height=50,
            text="Geri",
            shortcut="backspace",
            callback=self._prev_stage
        )
        
        self.start_button = Button(
            x=SCREEN_WIDTH // 2 - 100,
            y=SCREEN_HEIGHT - 100,
            width=200,
            height=50,
            text="Oyunu Başlat",
            shortcut="return",
            callback=self._start_game
        )
        
        self._header_font = None
        self._subheader_font = None
        
        self._setup_gender_menu()
    
    def get_header_font(self):
        if self._header_font is None:
            self._header_font = get_font(FONTS['header'])
        return self._header_font
    
    def get_subheader_font(self):
        if self._subheader_font is None:
            self._subheader_font = get_font(FONTS['subheader'])
        return self._subheader_font
    
    def _setup_gender_menu(self):
        """Cinsiyet seçim menüsünü oluştur"""
        self.gender_menu.clear()
        
        self.gender_menu.add_item(
            "ERKEK - Vali Paşa olarak oyna",
            lambda: self._select_gender(Gender.MALE)
        )
        self.gender_menu.add_item("", None)  # Ayırıcı
        self.gender_menu.add_item(
            "KADIN - Vali Hatun olarak oyna (Alternatif Tarih)",
            lambda: self._select_gender(Gender.FEMALE)
        )
    
    def on_enter(self):
        self.stage = "gender"
        self.selected_gender = None
        self.character_name = ""
        self.name_input.clear()
    
    def announce_screen(self):
        self.audio.announce_screen_change("Karakter Oluşturma")
        self.audio.speak(
            "Yeni bir maceraya başlıyorsunuz. Önce karakterinizin cinsiyetini seçin.",
            interrupt=False
        )
    
    def _select_gender(self, gender: Gender):
        """Cinsiyet seçildi"""
        self.selected_gender = gender
        
        if gender == Gender.MALE:
            self.audio.speak(
                "Erkek seçildi. Vali Paşa olarak oynayacaksınız. "
                "Askeri güç ve akınlarda avantajlısınız.",
                interrupt=True
            )
        else:
            self.audio.speak(
                "Kadın seçildi. Vali Hatun olarak oynayacaksınız. "
                "Alternatif tarih senaryosu. Diplomasi ve casuslukta avantajlısınız. "
                "Başlangıçta bazı beyler şüpheyle bakacak, ama başarınızla güven kazanacaksınız.",
                interrupt=True
            )
        
        # İsim aşamasına geç — varsayılan isim yok, oyuncu kendi girsin
        self.stage = "name"
        self.name_input.set_text("")
        self.name_input.focus()
        self.audio.speak("Şimdi karakterinize bir isim verin. İsim yazıp Enter'a basın.", interrupt=False)
    
    def _next_stage(self):
        """Sonraki aşamaya geç"""
        if self.stage == "gender":
            if self.selected_gender:
                self.stage = "name"
                self.name_input.focus()
                self.audio.speak("Karakterinize bir isim verin.", interrupt=True)
            else:
                self.audio.speak("Önce bir cinsiyet seçin.", interrupt=True)
        
        elif self.stage == "name":
            name = self.name_input.get_text().strip()
            if name:
                self.character_name = name
                self.stage = "confirm"
                self.name_input.unfocus()
                self._update_confirm_panel()
                self._announce_summary()
            else:
                self.audio.speak("Lütfen bir isim girin.", interrupt=True)
    
    def _prev_stage(self):
        """Önceki aşamaya dön"""
        if self.stage == "name":
            self.stage = "gender"
            self.name_input.unfocus()
            self.audio.speak("Cinsiyet seçimine döndünüz.", interrupt=True)
        
        elif self.stage == "confirm":
            self.stage = "name"
            self.name_input.focus()
            self.audio.speak("İsim girişine döndünüz.", interrupt=True)
        
        else:
            # Ana menüye dön
            self.screen_manager.change_screen(ScreenType.MAIN_MENU)
    
    def _update_confirm_panel(self):
        """Onay panelini güncelle"""
        self.confirm_panel.clear()
        
        if self.selected_gender == Gender.MALE:
            title = "Vali Paşa"
            bonuses = "Akın +%20, Yeniçeri sadakati +%15"
        else:
            title = "Vali Hatun"
            bonuses = "Diplomasi +%20, Evlilik ittifakı +%25, Vakıf +%30"
        
        self.confirm_panel.add_item("İsim", self.character_name)
        self.confirm_panel.add_item("Unvan", title)
        self.confirm_panel.add_item("Avantajlar", bonuses)
        self.confirm_panel.add_item("", "")
        self.confirm_panel.add_item("Başlangıç", "1520, Rumeli Eyaleti")
    
    def _announce_summary(self):
        """Özeti duyur"""
        if self.selected_gender == Gender.MALE:
            title = "Vali Paşa"
            story_preview = "Köklü bir askeri aileden geliyorsunuz."
        else:
            title = "Vali Hatun"
            story_preview = "Sarayda yetişen nadir kadınlardan birisiniz."
        
        self.audio.speak(
            f"Karakter özeti: {self.character_name} {title}. "
            f"{story_preview} "
            f"Oyunu başlatmak için Enter'a basın.",
            interrupt=True
        )
    
    def _start_game(self):
        """Oyunu başlat"""
        if not self.character_name or not self.selected_gender:
            self.audio.speak("Karakter bilgileri eksik.", interrupt=True)
            return
        
        # Karakter oluştur
        character = PlayerCharacter(
            name=self.character_name,
            gender=self.selected_gender
        )
        
        # Game Manager'a kaydet (oyun başlatmayı eyalet seçiminden sonra yap)
        gm = self.screen_manager.game_manager
        if gm:
            gm.player = character
            
            # Başlangıç hikayesini duyur
            self.audio.speak(character.get_background_story(), interrupt=True)
        
        # Eyalet seçimine yönlendir
        self.audio.speak("Şimdi yönetmek istediğiniz eyaleti seçin.", interrupt=False)
        self.screen_manager.change_screen(ScreenType.PROVINCE_SELECT)
    
    def handle_event(self, event) -> bool:
        if self.stage == "gender":
            if self.gender_menu.handle_event(event):
                return True
        
        elif self.stage == "name":
            if self.name_input.handle_event(event):
                return True
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    self._next_stage()
                    return True
                elif event.key == pygame.K_ESCAPE:
                    self._prev_stage()
                    return True
        
        elif self.stage == "confirm":
            if self.start_button.handle_event(event):
                return True
            if self.back_button.handle_event(event):
                return True
        
        # Genel tuşlar
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self._prev_stage()
                return True
            
            if event.key == pygame.K_F1:
                self._announce_help()
                return True
        
        return False
    
    def _announce_help(self):
        """Yardım duyurusu"""
        if self.stage == "gender":
            self.audio.speak(
                "Cinsiyet seçimi. Yukarı aşağı okla seçin, Enter ile onaylayın. "
                "Erkek karakter askeri güce, kadın karakter diplomasiye odaklıdır.",
                interrupt=True
            )
        elif self.stage == "name":
            self.audio.speak(
                "İsim girişi. Karakterinizin ismini yazın ve Enter ile onaylayın. "
                "Escape ile geri dönebilirsiniz.",
                interrupt=True
            )
        elif self.stage == "confirm":
            self.audio.speak(
                "Onay ekranı. Enter ile oyunu başlatın, Escape ile geri dönün.",
                interrupt=True
            )
    
    def update(self, dt: float):
        pass
    
    def draw(self, surface: pygame.Surface):
        header_font = self.get_header_font()
        subheader_font = self.get_subheader_font()
        
        # Başlık
        title = header_font.render("KARAKTER OLUŞTURMA", True, COLORS['gold'])
        title_rect = title.get_rect(centerx=SCREEN_WIDTH // 2, y=30)
        surface.blit(title, title_rect)
        
        if self.stage == "gender":
            # Cinsiyet seçimi
            subtitle = subheader_font.render(
                "Karakterinizin cinsiyetini seçin",
                True, COLORS['text']
            )
            subtitle_rect = subtitle.get_rect(centerx=SCREEN_WIDTH // 2, y=180)
            surface.blit(subtitle, subtitle_rect)
            
            self.gender_menu.draw(surface)
            
            # Bilgi metni
            info_font = get_font(24)
            info1 = info_font.render(
                "Erkek: Askeri güç, akın ve savaş avantajı",
                True, COLORS['text']
            )
            info2 = info_font.render(
                "Kadın: Diplomasi, casusluk ve vakıf avantajı (Alternatif Tarih)",
                True, COLORS['text']
            )
            surface.blit(info1, (SCREEN_WIDTH // 2 - 200, 500))
            surface.blit(info2, (SCREEN_WIDTH // 2 - 220, 530))
        
        elif self.stage == "name":
            # İsim girişi
            subtitle = subheader_font.render(
                "Karakterinize bir isim verin",
                True, COLORS['text']
            )
            subtitle_rect = subtitle.get_rect(centerx=SCREEN_WIDTH // 2, y=180)
            surface.blit(subtitle, subtitle_rect)
            
            # Seçilen cinsiyet bilgisi
            gender_text = "Erkek - Vali Paşa" if self.selected_gender == Gender.MALE else "Kadın - Vali Hatun"
            gender_surf = subheader_font.render(gender_text, True, COLORS['gold'])
            gender_rect = gender_surf.get_rect(centerx=SCREEN_WIDTH // 2, y=230)
            surface.blit(gender_surf, gender_rect)
            
            self.name_input.draw(surface)
            self.next_button.draw(surface)
            self.back_button.draw(surface)
        
        elif self.stage == "confirm":
            # Onay ekranı
            subtitle = subheader_font.render(
                "Karakterinizi onaylayın",
                True, COLORS['text']
            )
            subtitle_rect = subtitle.get_rect(centerx=SCREEN_WIDTH // 2, y=150)
            surface.blit(subtitle, subtitle_rect)
            
            self.confirm_panel.draw(surface)
            self.start_button.draw(surface)
            self.back_button.draw(surface)
