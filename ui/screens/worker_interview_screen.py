# -*- coding: utf-8 -*-
"""
Osmanlı Eyalet Yönetim Simülasyonu - İşçi Görüşme Ekranı
İnteraktif iş görüşmesi sistemi
"""

import pygame
from ui.screen_manager import BaseScreen, ScreenType
from ui.components import Button, Panel, MenuList
from ui.text_input import AccessibleTextInput
from config import COLORS, FONTS, SCREEN_WIDTH, SCREEN_HEIGHT, get_font
from game.systems.workers import WorkerType, Worker
from game.systems.worker_hiring_events import (
    get_random_candidate, CandidateProfile, InterviewState
)


class WorkerInterviewScreen(BaseScreen):
    """İşçi görüşme ekranı"""
    
    def __init__(self, screen_manager):
        super().__init__(screen_manager)
        
        # Görüşme durumu
        self.interview_state: InterviewState = None
        self.selected_worker_type: WorkerType = None
        
        # Aşama: "type_select", "interview", "test_result", "naming", "result"
        self.stage = "type_select"
        
        # Aday paneli
        self.candidate_panel = Panel(
            x=20,
            y=100,
            width=800,
            height=280,
            title="Aday"
        )
        
        # Tür seçimi menüsü
        self.type_menu = MenuList(
            x=20,
            y=150,
            width=400,
            item_height=50
        )
        
        # Seçenek menüsü (görüşme seçimleri)
        self.choice_menu = MenuList(
            x=20,
            y=420,
            width=500,
            item_height=50
        )
        
        # İsim girişi
        self.name_input = AccessibleTextInput(
            x=20,
            y=420,
            width=400,
            height=50,
            label="İşçi Adı",
            placeholder="İsim yazın...",
            max_length=30
        )
        
        # Butonlar
        self.back_button = Button(
            x=20,
            y=SCREEN_HEIGHT - 70,
            width=150,
            height=50,
            text="Geri",
            shortcut="backspace",
            callback=self._go_back
        )
        
        self.confirm_button = Button(
            x=200,
            y=SCREEN_HEIGHT - 70,
            width=150,
            height=50,
            text="Onayla",
            shortcut="enter",
            callback=self._confirm_hire
        )
        
        self._header_font = None
        self._setup_type_menu()
    
    def get_header_font(self):
        if self._header_font is None:
            self._header_font = get_font(FONTS['header'])
        return self._header_font
    
    def on_enter(self):
        """Ekrana girişte"""
        self.stage = "type_select"
        self.interview_state = None
        self.selected_worker_type = None
        self._setup_type_menu()
    
    def announce_screen(self):
        self.audio.announce_screen_change("İşçi İstihdam")
        self.audio.speak("Ne tür bir işçi aramak istiyorsunuz? Bir kategori seçin.", interrupt=False)
    
    def _setup_type_menu(self):
        """İşçi türü seçim menüsü"""
        self.type_menu.clear()
        
        types = [
            (WorkerType.FARMER, "Çiftçi", "Tarım ve hasat işleri için"),
            (WorkerType.MINER, "Madenci", "Maden ocağında çalışacak"),
            (WorkerType.LUMBERJACK, "Oduncu", "Kereste kesimi için"),
            (WorkerType.CRAFTSMAN, "Zanaatkar", "Üretim ve zanaat işleri"),
            (WorkerType.MERCHANT, "Tüccar", "Ticaret ve satış için"),
            (WorkerType.ENVOY, "Elçi/Diplomat", "Diplomasi görevleri için"),
        ]
        
        for wtype, name, desc in types:
            self.type_menu.add_item(
                f"{name} - {desc}",
                lambda t=wtype: self._select_type(t)
            )
    
    def _select_type(self, worker_type: WorkerType):
        """İşçi türü seçildi, görüşme başlat"""
        self.selected_worker_type = worker_type
        
        # Rastgele aday getir
        candidate = get_random_candidate(worker_type)
        if not candidate:
            self.audio.speak("Bu türde aday bulunamadı.", interrupt=True)
            return
        
        self.interview_state = InterviewState(candidate=candidate)
        self.stage = "interview"
        
        self._update_candidate_panel()
        self._setup_interview_choices()
        
        # Adayı tanıt
        self.audio.speak(f"Görüşme: {candidate.title}", interrupt=True)
        self.audio.speak(candidate.description, interrupt=False)
    
    def _update_candidate_panel(self):
        """Aday panelini güncelle"""
        self.candidate_panel.clear()
        
        if not self.interview_state:
            return
        
        c = self.interview_state.candidate
        
        self.candidate_panel.title = c.title
        
        # Açıklama çok uzunsa kısalt
        desc = c.description
        if len(desc) > 100:
            desc = desc[:97] + "..."
        
        self.candidate_panel.add_item("", desc)
        self.candidate_panel.add_item("", "")
        
        # Test yapıldıysa ek bilgi göster
        if self.interview_state.is_testing:
            self.candidate_panel.add_item("Gözlem Sonucu", c.hidden_info)
            self.candidate_panel.add_item("Beceri", f"Seviye {c.skill_level}")
            self.candidate_panel.add_item("Sadakat", f"{c.loyalty_modifier:+d}")
            self.candidate_panel.add_item("Verimlilik", f"%{int(c.efficiency_modifier * 100)}")
        else:
            self.candidate_panel.add_item("Maliyet", f"{c.base_cost} altın")
            self.candidate_panel.add_item("Özellik", c.special_trait)
    
    def _setup_interview_choices(self):
        """Görüşme seçeneklerini oluştur"""
        self.choice_menu.clear()
        
        if not self.interview_state:
            return
        
        c = self.interview_state.candidate
        
        # Test yapıldıysa farklı seçenekler
        if self.interview_state.is_testing:
            self.choice_menu.add_item(
                f"{c.hire_text} ({c.base_cost} altın)",
                self._start_naming
            )
            self.choice_menu.add_item(
                f"{c.reject_text}",
                self._reject_and_next
            )
        else:
            self.choice_menu.add_item(
                f"{c.hire_text} ({c.base_cost} altın)",
                self._start_naming
            )
            self.choice_menu.add_item(
                f"{c.test_text}",
                self._test_candidate
            )
            self.choice_menu.add_item(
                f"{c.reject_text}",
                self._reject_and_next
            )
    
    def _test_candidate(self):
        """Adayı sına - gizli bilgiyi göster"""
        if not self.interview_state:
            return
        
        self.interview_state.is_testing = True
        self._update_candidate_panel()
        self._setup_interview_choices()
        
        c = self.interview_state.candidate
        self.audio.speak("Bir süre gözlemlediniz.", interrupt=True)
        self.audio.speak(f"Gözlem sonucu: {c.hidden_info}", interrupt=False)
        self.audio.speak(f"Beceri seviyesi: {c.skill_level}. Sadakat: {c.loyalty_modifier:+d}. "
                        f"Verimlilik: yüzde {int(c.efficiency_modifier * 100)}.", interrupt=False)
    
    def _start_naming(self):
        """İşe al - isim girişine geç"""
        if not self.interview_state:
            return
        
        gm = self.screen_manager.game_manager
        if not gm:
            return
        
        c = self.interview_state.candidate
        
        # Altın kontrolü
        if gm.economy.resources.gold < c.base_cost:
            self.audio.speak(f"Yeterli altın yok. {c.base_cost} altın gerekli.", interrupt=True)
            return
        
        self.stage = "naming"
        self.name_input.text = c.name_suggestion
        self.name_input.cursor_pos = len(c.name_suggestion)
        self.name_input.focus()
        
        self.audio.speak(f"İşe alıyorsunuz. İşçiye bir isim verin. Önerilen: {c.name_suggestion}", interrupt=True)
    
    def _confirm_hire(self):
        """İşe almayı onayla"""
        if self.stage != "naming" or not self.interview_state:
            return
        
        gm = self.screen_manager.game_manager
        if not gm:
            return
        
        name = self.name_input.text.strip()
        if not name:
            name = self.interview_state.candidate.name_suggestion
        
        c = self.interview_state.candidate
        
        # Altını düş
        gm.economy.resources.gold -= c.base_cost
        
        # İşçiyi oluştur
        worker = Worker(
            name=name,
            worker_type=c.worker_type,
            skill_level=c.skill_level,
            efficiency=c.efficiency_modifier
        )
        gm.workers.workers.append(worker)
        
        self.audio.play_ui_sound('click')
        self.audio.speak(f"{name} işe alındı! Beceri: {c.skill_level}, Verimlilik: yüzde {int(c.efficiency_modifier * 100)}.", interrupt=True)
        
        # İşçiler ekranına dön
        self.name_input.unfocus()
        self.screen_manager.change_screen(ScreenType.WORKERS)
    
    def _reject_and_next(self):
        """Reddet ve yeni aday getir"""
        self.audio.speak("Reddettiniz. Başka adaylar arıyoruz...", interrupt=True)
        
        # Aynı türde yeni aday
        candidate = get_random_candidate(self.selected_worker_type)
        if candidate:
            self.interview_state = InterviewState(candidate=candidate)
            self._update_candidate_panel()
            self._setup_interview_choices()
            
            self.audio.speak(f"Yeni aday: {candidate.title}", interrupt=False)
            self.audio.speak(candidate.description, interrupt=False)
        else:
            self.audio.speak("Başka aday bulunamadı.", interrupt=True)
            self._go_back()
    
    def _go_back(self):
        """Geri dön"""
        if self.stage == "naming":
            # İsim girişinden görüşmeye dön
            self.stage = "interview"
            self.name_input.unfocus()
            self._setup_interview_choices()
            self.audio.speak("İşe almaktan vazgeçtiniz.", interrupt=True)
        elif self.stage == "interview":
            # Görüşmeden tür seçimine dön
            self.stage = "type_select"
            self.interview_state = None
            self.audio.speak("Aday aramasından vazgeçtiniz.", interrupt=True)
        else:
            # Ekrandan çık
            self.screen_manager.change_screen(ScreenType.WORKERS)
    
    def handle_event(self, event) -> bool:
        # İsim girişi modunda
        if self.stage == "naming":
            if self.name_input.handle_event(event):
                return True
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    self._confirm_hire()
                    return True
                elif event.key == pygame.K_ESCAPE:
                    self._go_back()
                    return True
            return True
        
        # Tür seçimi
        if self.stage == "type_select":
            if self.type_menu.handle_event(event):
                return True
        
        # Görüşme seçenekleri
        if self.stage == "interview":
            if self.choice_menu.handle_event(event):
                return True
        
        if self.back_button.handle_event(event):
            return True
        
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_BACKSPACE or event.key == pygame.K_ESCAPE:
                self._go_back()
                return True
            
            # F1 - Yardım
            if event.key == pygame.K_F1:
                if self.stage == "type_select":
                    self.audio.speak("Ne tür işçi arıyorsunuz? Bir kategori seçin.", interrupt=True)
                elif self.stage == "interview":
                    c = self.interview_state.candidate if self.interview_state else None
                    if c:
                        self.audio.speak(c.description, interrupt=True)
                elif self.stage == "naming":
                    self.audio.speak("İşçiye bir isim verin ve Enter'a basın.", interrupt=True)
                return True
        
        return False
    
    def update(self, dt: float):
        pass
    
    def draw(self, surface: pygame.Surface):
        # Başlık
        header_font = self.get_header_font()
        
        if self.stage == "type_select":
            title = header_font.render("İŞÇİ İSTİHDAM - Tür Seçin", True, COLORS['gold'])
        elif self.stage == "interview":
            title = header_font.render("İŞ GÖRÜŞMESİ", True, COLORS['gold'])
        elif self.stage == "naming":
            title = header_font.render("İSİM VERİN", True, COLORS['gold'])
        else:
            title = header_font.render("İŞÇİ İSTİHDAM", True, COLORS['gold'])
        
        surface.blit(title, (20, 30))
        
        # Aşamaya göre içerik
        if self.stage == "type_select":
            # Tür seçim menüsü
            small_font = get_font(FONTS['subheader'])
            info = small_font.render("Hangi alanda çalışacak bir işçi arıyorsunuz?", True, COLORS['text'])
            surface.blit(info, (20, 100))
            self.type_menu.draw(surface)
        
        elif self.stage == "interview":
            # Aday paneli
            self.candidate_panel.draw(surface)
            
            # Seçenekler
            small_font = get_font(FONTS['subheader'])
            info = small_font.render("Ne yapmak istiyorsunuz?", True, COLORS['text'])
            surface.blit(info, (20, 395))
            self.choice_menu.draw(surface)
        
        elif self.stage == "naming":
            # Aday paneli
            self.candidate_panel.draw(surface)
            
            # İsim girişi
            small_font = get_font(FONTS['subheader'])
            info = small_font.render("İşçiye bir isim verin:", True, COLORS['text'])
            surface.blit(info, (20, 395))
            self.name_input.draw(surface)
            
            # Onay butonu
            self.confirm_button.draw(surface)
        
        # Geri butonu her zaman
        self.back_button.draw(surface)
