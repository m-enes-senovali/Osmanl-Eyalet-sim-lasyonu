# -*- coding: utf-8 -*-
"""
Osmanlı Eyalet Yönetim Simülasyonu - Eğitim Ekranı
"""

import pygame
from ui.screen_manager import BaseScreen, ScreenType
from ui.components import Button, Panel, MenuList
from config import COLORS, FONTS, SCREEN_WIDTH, SCREEN_HEIGHT, get_font
from game.systems.tutorial import (
    get_tutorial_system, TutorialChapter, TutorialStep
)


class TutorialScreen(BaseScreen):
    """Tutorial görüntüleme ve kontrol ekranı"""
    
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
        
        # Bölüm listesi
        self.chapter_menu = MenuList(
            x=340,
            y=420,
            width=250,
            item_height=40
        )
        
        # Butonlar
        self.continue_button = Button(
            x=SCREEN_WIDTH // 2 - 100,
            y=SCREEN_HEIGHT - 150,
            width=200,
            height=50,
            text="Devam Et",
            shortcut="enter",
            callback=self._continue_tutorial
        )
        
        self.skip_button = Button(
            x=SCREEN_WIDTH // 2 - 100,
            y=SCREEN_HEIGHT - 90,
            width=200,
            height=50,
            text="Eğitimi Atla",
            shortcut="escape",
            callback=self._skip_tutorial
        )
        
        self.back_button = Button(
            x=20,
            y=SCREEN_HEIGHT - 70,
            width=150,
            height=50,
            text="Ana Menü",
            shortcut="backspace",
            callback=self._go_back
        )
        
        self._header_font = None
    
    def get_header_font(self):
        if self._header_font is None:
            self._header_font = get_font(FONTS['header'])
        return self._header_font
    
    def on_enter(self):
        """Ekrana girişte"""
        self.tutorial = get_tutorial_system()
        
        if not self.tutorial.is_active:
            self.tutorial.start()
        
        self._update_panels()
        self._setup_chapter_menu()
    
    def announce_screen(self):
        self.audio.announce_screen_change("Eğitim")
        
        # Mevcut adımı duyur
        step = self.tutorial.get_current_step()
        if step:
            self.audio.speak(
                f"{step.title}. {step.description}",
                interrupt=False
            )
    
    def _setup_chapter_menu(self):
        """Bölüm menüsünü oluştur"""
        self.chapter_menu.clear()
        
        chapter_names = {
            TutorialChapter.BASICS: "Temel Kontroller",
            TutorialChapter.ECONOMY: "Ekonomi",
            TutorialChapter.MILITARY: "Askeri",
            TutorialChapter.DIPLOMACY: "Diplomasi"
        }
        
        for chapter in TutorialChapter:
            steps = self.tutorial.get_steps_by_chapter(chapter)
            completed = sum(1 for s in steps if s.completed)
            total = len(steps)
            
            current = self.tutorial.get_current_chapter()
            prefix = "▶ " if chapter == current else "  "
            
            self.chapter_menu.add_item(
                f"{prefix}{chapter_names[chapter]} ({completed}/{total})",
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
            self.step_panel.add_item("Açıklama", step.description[:50] + "..." if len(step.description) > 50 else step.description)
            self.step_panel.add_item("Yapılacak", step.instruction)
        else:
            self.step_panel.title = "Tamamlandı"
            self.step_panel.add_item("", "Eğitim tamamlandı!")
        
        # İlerleme paneli
        self.progress_panel.clear()
        progress = self.tutorial.get_progress()
        
        self.progress_panel.add_item("Adım", f"{progress['current_step']} / {progress['total_steps']}")
        self.progress_panel.add_item("Tamamlanan", f"{progress['completed']}")
        self.progress_panel.add_item("İlerleme", f"%{int(progress['percentage'])}")
    
    def _continue_tutorial(self):
        """Tutorial'a devam et"""
        self.tutorial.advance()
        self._update_panels()
        self._setup_chapter_menu()
        
        # Eğitim tamamlandıysa ana ekrana git
        if self.tutorial.completed:
            self.screen_manager.change_screen(ScreenType.PROVINCE_VIEW)
    
    def _skip_tutorial(self):
        """Tutorial'ı atla"""
        self.tutorial.skip()
        self.screen_manager.change_screen(ScreenType.MAIN_MENU)
    
    def _go_back(self):
        """Ana menüye dön"""
        self.screen_manager.change_screen(ScreenType.MAIN_MENU)
    
    def handle_event(self, event) -> bool:
        if self.continue_button.handle_event(event):
            return True
        
        if self.skip_button.handle_event(event):
            return True
        
        if self.back_button.handle_event(event):
            return True
        
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                self._continue_tutorial()
                return True
            elif event.key == pygame.K_ESCAPE:
                self._skip_tutorial()
                return True
            elif event.key == pygame.K_BACKSPACE:
                self._go_back()
                return True
            
            # F1 ile mevcut adımı tekrar duyur
            elif event.key == pygame.K_F1:
                step = self.tutorial.get_current_step()
                if step:
                    self.audio.speak(
                        f"{step.title}. {step.description} {step.instruction}",
                        interrupt=True
                    )
                return True
        
        return False
    
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
        
        # Bölüm menüsü
        self.chapter_menu.draw(surface)
        
        # Butonlar
        self.continue_button.draw(surface)
        self.skip_button.draw(surface)
        self.back_button.draw(surface)
