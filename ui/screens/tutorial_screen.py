# -*- coding: utf-8 -*-
"""
Osmanlı Eyalet Yönetim Simülasyonu - Eğitim Ekranı
İnteraktif uygulama sistemi: her adım belirli bir tuşa basılmasını bekler.
Tamamlandığında kullanıcıya seçenek sunar.
"""

import pygame
from ui.screen_manager import BaseScreen, ScreenType
from ui.components import Panel, MenuList
from config import COLORS, FONTS, SCREEN_WIDTH, SCREEN_HEIGHT, get_font
from game.systems.tutorial import (
    get_tutorial_system, TutorialChapter, TutorialStep
)


class TutorialScreen(BaseScreen):
    """Tutorial görüntüleme ve kontrol ekranı — İnteraktif Uygulama Modu"""
    
    # Tuş adı → pygame sabiti eşleştirmesi
    KEY_MAP = {
        'return': pygame.K_RETURN,
        'space': pygame.K_SPACE,
        'backspace': pygame.K_BACKSPACE,
        'down': pygame.K_DOWN,
        'up': pygame.K_UP,
        'left': pygame.K_LEFT,
        'right': pygame.K_RIGHT,
        'f1': pygame.K_F1,
        'f5': pygame.K_F5,
        'e': pygame.K_e,
        'w': pygame.K_w,
        't': pygame.K_t,
        'm': pygame.K_m,
        'c': pygame.K_c,
        'd': pygame.K_d,
        's': pygame.K_s,
        'k': pygame.K_k,
        'l': pygame.K_l,
        'p': pygame.K_p,
        'b': pygame.K_b,
        'g': pygame.K_g,
        'v': pygame.K_v,
        'o': pygame.K_o,
        'x': pygame.K_x,
        'n': pygame.K_n,
        'f': pygame.K_f,
    }
    
    # Tuş adı → Türkçe görüntü adı
    KEY_DISPLAY_NAMES = {
        'return': 'Enter',
        'space': 'Boşluk (Space)',
        'backspace': 'Backspace',
        'down': 'Aşağı ok',
        'up': 'Yukarı ok',
        'left': 'Sol ok',
        'right': 'Sağ ok',
        'f1': 'F1',
        'f5': 'F5',
        'f': 'F',
    }
    
    CHAPTER_NAMES = {
        TutorialChapter.BASICS: "Temel Kontroller",
        TutorialChapter.NAVIGATION: "Eyalet Gezinme",
        TutorialChapter.ECONOMY: "Ekonomi",
        TutorialChapter.MILITARY: "Askeri",
        TutorialChapter.CONSTRUCTION: "İnşaat",
        TutorialChapter.DIPLOMACY: "Diplomasi",
        TutorialChapter.PEOPLE: "Halk",
        TutorialChapter.ADVANCED: "İleri Konular",
    }
    
    def __init__(self, screen_manager):
        super().__init__(screen_manager)
        
        self.tutorial = get_tutorial_system()
        
        # Mevcut adım paneli
        self.step_panel = Panel(
            x=SCREEN_WIDTH // 2 - 400,
            y=150,
            width=800,
            height=250,
            title="Eğitim"
        )
        
        # İlerleme paneli
        self.progress_panel = Panel(
            x=20,
            y=420,
            width=300,
            height=150,
            title="İlerleme"
        )
        
        # Bölüm listesi (sadece görüntüleme)
        self.chapter_menu = MenuList(
            x=340,
            y=420,
            width=250,
            item_height=40
        )
        
        # Tamamlanma sonrası seçim menüsü
        self.showing_completion_dialog = False
        self.completion_menu = MenuList(
            x=(SCREEN_WIDTH - 400) // 2,
            y=(SCREEN_HEIGHT - 200) // 2 + 50,
            width=400,
            item_height=50
        )
        self.completion_menu.add_item("Yeni Oyuna Başla", self._start_new_game, "n")
        self.completion_menu.add_item("Ana Menüye Dön", self._go_to_main_menu, "a")
        
        self._header_font = None
        self._subtitle_font = None
    
    def get_header_font(self):
        if self._header_font is None:
            self._header_font = get_font(FONTS['header'])
        return self._header_font
    
    def get_subtitle_font(self):
        if self._subtitle_font is None:
            self._subtitle_font = get_font(FONTS['subheader'])
        return self._subtitle_font
    
    def on_enter(self):
        """Ekrana girişte — eğitimi her zaman baştan başlat"""
        self.tutorial = get_tutorial_system()
        self.showing_completion_dialog = False
        
        # Eğitimi sıfırla ve baştan başlat
        self.tutorial.reset()
        self.tutorial.start()
        
        self._update_panels()
        self._setup_chapter_menu()
    
    def announce_screen(self):
        self.audio.announce_screen_change("Eğitim — İnteraktif Uygulama")
        
        # Yeni sisteme uygun talimat
        self.audio.speak(
            "Her adımda size söylenen tuşa basarak ilerleyin. "
            "Escape ile eğitimi atlayıp ana menüye dönebilirsiniz. "
            "Sol ok ile önceki adıma dönebilirsiniz.",
            interrupt=False
        )
        
        # Mevcut adımı ve ne yapılması gerektiğini duyur
        step = self.tutorial.get_current_step()
        if step:
            self._announce_step(step)
    
    def _announce_step(self, step: TutorialStep):
        """Adımı sesli duyur — bölüm geçişi kontrolü ile"""
        # Bölüm değişim kontrolü
        prev_idx = self.tutorial.current_step_index - 1
        if prev_idx >= 0:
            prev_step = self.tutorial.steps[prev_idx]
            if prev_step.chapter != step.chapter:
                chapter_name = self.CHAPTER_NAMES.get(step.chapter, step.chapter.value)
                self.audio.speak(f"Yeni bölüm: {chapter_name}", interrupt=False)
        
        self.audio.speak(
            f"{step.title}. {step.description}",
            interrupt=False
        )
        
        # Beklenen tuşu Türkçe olarak duyur
        if step.required_key:
            display_name = self.KEY_DISPLAY_NAMES.get(step.required_key, step.required_key.upper())
            self.audio.speak(
                f"Şimdi {display_name} tuşuna basın.",
                interrupt=False
            )
        else:
            self.audio.speak(step.instruction, interrupt=False)
    
    def _setup_chapter_menu(self):
        """Bölüm menüsünü oluştur (sadece görüntüleme)"""
        self.chapter_menu.clear()
        
        for chapter in TutorialChapter:
            steps = self.tutorial.get_steps_by_chapter(chapter)
            completed = sum(1 for s in steps if s.completed)
            total = len(steps)
            
            current = self.tutorial.get_current_chapter()
            prefix = "▶ " if chapter == current else "  "
            
            self.chapter_menu.add_item(
                f"{prefix}{self.CHAPTER_NAMES[chapter]} ({completed}/{total})",
                None,
                ""
            )
    
    def _update_panels(self):
        """Panelleri güncelle"""
        # Adım paneli
        self.step_panel.clear()
        step = self.tutorial.get_current_step()
        
        if step:
            self.step_panel.title = step.title
            desc = step.description[:50] + "..." if len(step.description) > 50 else step.description
            self.step_panel.add_item("Açıklama", desc)
            self.step_panel.add_item("Yapılacak", step.instruction)
            if step.required_key:
                display_name = self.KEY_DISPLAY_NAMES.get(step.required_key, step.required_key.upper())
                self.step_panel.add_item("Beklenen Tuş", display_name)
        else:
            self.step_panel.title = "Tamamlandı"
            self.step_panel.add_item("", "Eğitim tamamlandı!")
        
        # İlerleme paneli
        self.progress_panel.clear()
        progress = self.tutorial.get_progress()
        
        self.progress_panel.add_item("Adım", f"{progress['current_step']} / {progress['total_steps']}")
        self.progress_panel.add_item("Tamamlanan", f"{progress['completed']}")
        self.progress_panel.add_item("İlerleme", f"%{int(progress['percentage'])}")
    
    def _advance_step(self):
        """
        Adımı ilerlet, panelleri güncelle, tamamlanma kontrolü yap.
        Tüm ilerleme bu metottan geçer.
        """
        self.tutorial.advance(silent=True)
        self._update_panels()
        self._setup_chapter_menu()
        
        # Eğitim tamamlandıysa tamamlanma diyaloğunu göster
        if self.tutorial.completed:
            self._show_completion_dialog()
        else:
            # Sonraki adımı duyur
            next_step = self.tutorial.get_current_step()
            if next_step:
                self._announce_step(next_step)
    
    def _show_completion_dialog(self):
        """Eğitim tamamlandı diyaloğunu göster"""
        self.showing_completion_dialog = True
        self.completion_menu.selected_index = 0
        self.audio.speak(
            "Tebrikler! Eğitimi başarıyla tamamladınız. "
            "Yeni Oyuna Başla için N tuşuna, Ana Menüye Dön için A tuşuna basın. "
            "Yukarı aşağı ok tuşlarıyla da seçim yapabilirsiniz.",
            interrupt=True
        )
    
    def _start_new_game(self):
        """Yeni oyuna başla — karakter oluşturma ekranına git"""
        self.showing_completion_dialog = False
        self.audio.speak("Yeni oyun başlatılıyor.", interrupt=True)
        self.screen_manager.change_screen(ScreenType.CHARACTER_CREATION)
    
    def _go_to_main_menu(self):
        """Ana menüye dön"""
        self.showing_completion_dialog = False
        self.audio.speak("Ana menüye dönülüyor.", interrupt=True)
        self.screen_manager.change_screen(ScreenType.MAIN_MENU)
    
    def _skip_tutorial(self):
        """Tutorial'ı atla — ana menüye dön"""
        self.tutorial.skip()
        self.screen_manager.change_screen(ScreenType.MAIN_MENU)
    
    def handle_event(self, event):
        # === TAMAMLANMA DİYALOĞU AKTİFSE ===
        if self.showing_completion_dialog:
            if self.completion_menu.handle_event(event):
                return True
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self._go_to_main_menu()
                    return True
            return True  # Diyalog açıkken diğer olayları engelle
        
        if event.type != pygame.KEYDOWN:
            return False
        
        # === ESCAPE HER ZAMAN ÇIKAR ===
        if event.key == pygame.K_ESCAPE:
            self._skip_tutorial()
            return True
        
        # === SOL OK → ÖNCEKİ ADIMA DÖN (her zaman) ===
        if event.key == pygame.K_LEFT:
            if self.tutorial.current_step_index > 0:
                self.tutorial.current_step_index -= 1
                self._update_panels()
                self._setup_chapter_menu()
                step = self.tutorial.get_current_step()
                if step:
                    self.audio.speak("Önceki adıma dönüldü.", interrupt=True)
                    self._announce_step(step)
            else:
                self.audio.speak("İlk adımdasınız, daha geri gidemezsiniz.", interrupt=True)
            return True
        
        # === İNTERAKTİF UYGULAMA MODU ===
        # ÖNCELİK: Adımın beklediği tuş kontrolü GLOBAL kısayollardan ÖNCE yapılır!
        # Bu sayede F1 adımında F1'e basınca "durum oku" yerine "Doğru!" denir.
        step = self.tutorial.get_current_step()
        if not step:
            self._show_completion_dialog()
            return True
        
        if step.required_key:
            expected_pygame_key = self.KEY_MAP.get(step.required_key)
            
            if expected_pygame_key is not None and event.key == expected_pygame_key:
                # Doğru tuşa basıldı!
                self.audio.speak("Doğru!", interrupt=True)
                self._advance_step()
                return True
            else:
                # Yanlış tuş — hatırlat
                display_name = self.KEY_DISPLAY_NAMES.get(step.required_key, step.required_key.upper())
                self.audio.speak(
                    f"{display_name} tuşuna basmanız gerekiyor.",
                    interrupt=True
                )
                return True
        else:
            # required_key tanımlı değilse Enter ile devam et
            if event.key == pygame.K_RETURN:
                self._advance_step()
                return True
        
        return True  # Tüm tuşları yakala
    
    def update(self, dt: float):
        pass
    
    def draw(self, surface: pygame.Surface):
        # Başlık
        header_font = self.get_header_font()
        title = header_font.render("Eğitim", True, COLORS['gold'])
        surface.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 50))
        
        # İlerleme çubuğu
        progress = self.tutorial.get_progress()
        bar_width = 600
        bar_height = 20
        bar_x = SCREEN_WIDTH // 2 - bar_width // 2
        bar_y = 100
        
        # Arka plan
        pygame.draw.rect(surface, COLORS['panel_bg'], (bar_x, bar_y, bar_width, bar_height))
        
        # Dolgu
        fill_width = int(bar_width * (progress['percentage'] / 100))
        if fill_width > 0:
            pygame.draw.rect(surface, COLORS['success'], (bar_x, bar_y, fill_width, bar_height))
        
        # Çerçeve
        pygame.draw.rect(surface, COLORS['panel_border'], (bar_x, bar_y, bar_width, bar_height), 2)
        
        # Paneller
        self.step_panel.draw(surface)
        self.progress_panel.draw(surface)
        
        # Bölüm listesi
        self.chapter_menu.draw(surface)
        
        # Tamamlanma diyaloğu
        if self.showing_completion_dialog:
            # Karartma
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 150))
            surface.blit(overlay, (0, 0))
            
            # Diyalog kutusu
            dialog_rect = pygame.Rect((SCREEN_WIDTH - 500) // 2, (SCREEN_HEIGHT - 300) // 2, 500, 300)
            pygame.draw.rect(surface, COLORS['panel_bg'], dialog_rect, border_radius=10)
            pygame.draw.rect(surface, COLORS['gold'], dialog_rect, width=2, border_radius=10)
            
            # Diyalog başlığı
            subtitle_font = self.get_subtitle_font()
            dialog_title = subtitle_font.render("Eğitim Tamamlandı!", True, COLORS['gold'])
            dialog_title_rect = dialog_title.get_rect(centerx=SCREEN_WIDTH // 2, top=dialog_rect.top + 30)
            surface.blit(dialog_title, dialog_title_rect)
            
            # Menü çiz
            self.completion_menu.draw(surface)
