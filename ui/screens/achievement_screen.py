# -*- coding: utf-8 -*-
"""
Osmanlı Eyalet Yönetim Simülasyonu - Başarı Ekranı
"""

import pygame
from ui.screen_manager import BaseScreen, ScreenType
from ui.components import Button, Panel, MenuList
from config import COLORS, FONTS, SCREEN_WIDTH, SCREEN_HEIGHT
from game.systems.achievements import (
    get_achievement_system, AchievementCategory, Achievement
)


class AchievementScreen(BaseScreen):
    """Başarı görüntüleme ekranı"""
    
    def __init__(self, screen_manager):
        super().__init__(screen_manager)
        
        self.achievement_system = get_achievement_system()
        
        # Özet paneli
        self.summary_panel = Panel(20, 80, 400, 150, "Başarı Özeti")
        
        # Kategori seçici
        self.category_menu = MenuList(
            x=20,
            y=250,
            width=200,
            item_height=40
        )
        
        # Başarı listesi
        self.achievement_menu = MenuList(
            x=240,
            y=250,
            width=520,
            item_height=50
        )
        
        # Detay paneli
        self.detail_panel = Panel(780, 80, 480, 300, "Başarı Detayı")
        
        self.back_button = Button(
            x=20,
            y=SCREEN_HEIGHT - 70,
            width=150,
            height=50,
            text="Geri",
            shortcut="backspace",
            callback=self._go_back
        )
        
        self._header_font = None
        self.current_category = AchievementCategory.ECONOMIC
        self.selected_achievement: Achievement = None
        self.active_menu = 'category'  # 'category' veya 'achievement'
    
    def get_header_font(self):
        if self._header_font is None:
            self._header_font = pygame.font.Font(None, FONTS['header'])
        return self._header_font
    
    def on_enter(self):
        self.achievement_system = get_achievement_system()
        self._setup_category_menu()
        self._setup_achievement_menu()
        self._update_summary_panel()
        self._update_detail_panel()
        self.audio.play_game_sound('events', 'achievement')
    
    def announce_screen(self):
        self.audio.announce_screen_change("Başarılar")
        
        # Özet duyur
        unlocked = self.achievement_system.unlocked_count
        total = len(self.achievement_system.achievements)
        points = self.achievement_system.total_points
        self.audio.speak(
            f"{unlocked} / {total} başarı açıldı. Toplam {points} puan.",
            interrupt=False
        )
    
    def _setup_category_menu(self):
        """Kategori menüsünü oluştur"""
        self.category_menu.clear()
        
        category_names = {
            AchievementCategory.ECONOMIC: "Ekonomik",
            AchievementCategory.MILITARY: "Askeri",
            AchievementCategory.DIPLOMATIC: "Diplomatik",
            AchievementCategory.SOCIAL: "Sosyal",
            AchievementCategory.HIDDEN: "Gizli",
        }
        
        for cat in AchievementCategory:
            achievements = self.achievement_system.get_achievements_by_category(cat)
            unlocked = sum(1 for a in achievements if a.unlocked)
            total = len(achievements)
            
            self.category_menu.add_item(
                f"{category_names[cat]} ({unlocked}/{total})",
                lambda c=cat: self._select_category(c),
                ""
            )
    
    def _select_category(self, category: AchievementCategory):
        """Kategori seç"""
        self.current_category = category
        self._setup_achievement_menu()
        
        # Başarı menüsüne geç
        self.active_menu = 'achievement'
        self.achievement_menu.selected_index = 0
        
        # Duyur
        category_names = {
            AchievementCategory.ECONOMIC: "Ekonomik",
            AchievementCategory.MILITARY: "Askeri",
            AchievementCategory.DIPLOMATIC: "Diplomatik",
            AchievementCategory.SOCIAL: "Sosyal",
            AchievementCategory.HIDDEN: "Gizli",
        }
        self.audio.speak(f"{category_names[category]} başarıları. Başarı seçmek için ok tuşlarını kullanın.", interrupt=True)
    
    def _setup_achievement_menu(self):
        """Başarı listesini oluştur"""
        self.achievement_menu.clear()
        
        achievements = self.achievement_system.get_achievements_by_category(self.current_category)
        
        for ach in achievements:
            if ach.unlocked:
                icon = "✓"
                text = f"{icon} {ach.name} ({ach.points} puan)"
            elif ach.hidden:
                text = "??? (Gizli Başarı)"
            else:
                progress = int(ach.progress)
                text = f"○ {ach.name} (%{progress})"
            
            self.achievement_menu.add_item(
                text,
                lambda a=ach: self._select_achievement(a),
                ""
            )
    
    def _select_achievement(self, achievement: Achievement):
        """Başarı seç ve detayını göster"""
        self.selected_achievement = achievement
        self._update_detail_panel()
        
        # Duyur
        if achievement.hidden and not achievement.unlocked:
            self.audio.speak("Gizli başarı - henüz açılmadı", interrupt=True)
        else:
            self.audio.speak(
                f"{achievement.name}. {achievement.description}. "
                f"{'Açıldı' if achievement.unlocked else f'İlerleme: yüzde {int(achievement.progress)}'}",
                interrupt=True
            )
    
    def _update_summary_panel(self):
        """Özet panelini güncelle"""
        self.summary_panel.clear()
        
        sys = self.achievement_system
        total = len(sys.achievements)
        
        self.summary_panel.add_item("Açılan", f"{sys.unlocked_count} / {total}")
        self.summary_panel.add_item("Tamamlanma", f"%{int(sys.get_completion_percentage())}")
        self.summary_panel.add_item("Toplam Puan", str(sys.total_points))
    
    def _update_detail_panel(self):
        """Detay panelini güncelle"""
        self.detail_panel.clear()
        
        ach = self.selected_achievement
        if not ach:
            self.detail_panel.add_item("", "Bir başarı seçin")
            return
        
        if ach.hidden and not ach.unlocked:
            self.detail_panel.add_item("Başarı", "???")
            self.detail_panel.add_item("Açıklama", "Gizli başarı")
            self.detail_panel.add_item("Durum", "Kilitli")
            return
        
        self.detail_panel.add_item("Başarı", ach.name)
        self.detail_panel.add_item("Açıklama", ach.description)
        self.detail_panel.add_item("Puan", str(ach.points))
        
        if ach.unlocked:
            self.detail_panel.add_item("Durum", "✓ Açıldı")
            if ach.unlock_date:
                self.detail_panel.add_item("Tarih", ach.unlock_date)
        else:
            self.detail_panel.add_item("İlerleme", f"%{int(ach.progress)}")
            if ach.target_value > 1:
                self.detail_panel.add_item("Mevcut/Hedef", f"{ach.current_value} / {ach.target_value}")
    
    def _go_back(self):
        self.screen_manager.change_screen(ScreenType.PROVINCE_VIEW)
    
    def handle_event(self, event) -> bool:
        # Sadece aktif menüyü işle
        if self.active_menu == 'category':
            if self.category_menu.handle_event(event):
                return True
        else:
            if self.achievement_menu.handle_event(event):
                return True
        
        if self.back_button.handle_event(event):
            return True
        
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_BACKSPACE:
                if self.active_menu == 'achievement':
                    # Kategori menüsüne geri dön
                    self.active_menu = 'category'
                    self.audio.speak("Kategoriler", interrupt=True)
                    return True
                else:
                    self._go_back()
                    return True
            elif event.key == pygame.K_ESCAPE:
                self._go_back()
                return True
            
            # Tab ile menüler arası geçiş
            elif event.key == pygame.K_TAB:
                if self.active_menu == 'category':
                    self.active_menu = 'achievement'
                    self.audio.speak("Başarı listesi", interrupt=True)
                else:
                    self.active_menu = 'category'
                    self.audio.speak("Kategoriler", interrupt=True)
                return True
        
        return False
    
    def update(self, dt: float):
        pass
    
    def draw(self, surface: pygame.Surface):
        # Başlık
        header_font = self.get_header_font()
        title = header_font.render("Başarılar", True, COLORS['gold'])
        surface.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 20))
        
        # Paneller
        self.summary_panel.draw(surface)
        self.detail_panel.draw(surface)
        
        # Menüler
        self.category_menu.draw(surface)
        self.achievement_menu.draw(surface)
        
        # Geri butonu
        self.back_button.draw(surface)
