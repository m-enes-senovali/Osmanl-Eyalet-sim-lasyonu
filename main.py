# -*- coding: utf-8 -*-
"""
Osmanlı Eyalet Yönetim Simülasyonu
Ana Giriş Noktası

Bir Osmanlı dönemi eyalet yönetim simülasyonu.
Beylerbeyi olarak eyaletinizi yönetin, ekonomiyi dengeleyin,
ordu kurun ve padişahın güvenini kazanın.

Geliştirici: [Kullanıcı Adı]
Erişilebilirlik: NVDA ekran okuyucu desteği
"""

import os
import sys

# Çalışma dizinini ayarla
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pygame
from config import SCREEN_WIDTH, SCREEN_HEIGHT, FPS, GAME_TITLE, COLORS
from audio.audio_manager import get_audio_manager
from updater import get_updater
from game.game_manager import GameManager
from ui.screen_manager import ScreenManager, ScreenType
from ui.screens.main_menu import MainMenuScreen
from ui.screens.province_view import ProvinceViewScreen
from ui.screens.economy_screen import EconomyScreen
from ui.screens.military_screen import MilitaryScreen
from ui.screens.construction_screen import ConstructionScreen
from ui.screens.diplomacy_screen import DiplomacyScreen
from ui.screens.population_screen import PopulationScreen
from ui.screens.event_popup import EventPopupScreen


class Game:
    """Ana oyun sınıfı"""
    
    def __init__(self):
        # Pygame başlat
        pygame.init()
        pygame.font.init()
        
        # Ekran oluştur
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption(GAME_TITLE)
        
        # Icon ayarla (varsa)
        # pygame.display.set_icon(pygame.image.load('assets/icon.png'))
        
        # Saat
        self.clock = pygame.time.Clock()
        
        # Oyun yöneticisi
        self.game_manager = GameManager()
        
        # Ekran yöneticisi
        self.screen_manager = ScreenManager(self.game_manager)
        
        # Ses yöneticisi
        self.audio = get_audio_manager()
        
        # Ekranları kaydet
        self._register_screens()
        
        # Durumlar
        self.running = True
        
        # Ses dosyalarını yükle
        self._load_sounds()
        
        # Güncelleme kontrolü (arka planda)
        self.updater = get_updater()
        self.updater.check_on_startup()
        
        # Tuş basılı tutma özelliğini etkinleştir (ilk gecikme 400ms, tekrar 50ms)
        pygame.key.set_repeat(400, 50)
    
    def _register_screens(self):
        """Ekranları kaydet"""
        self.screen_manager.register_screen(
            ScreenType.MAIN_MENU,
            MainMenuScreen(self.screen_manager)
        )
        self.screen_manager.register_screen(
            ScreenType.PROVINCE_VIEW,
            ProvinceViewScreen(self.screen_manager)
        )
        self.screen_manager.register_screen(
            ScreenType.ECONOMY,
            EconomyScreen(self.screen_manager)
        )
        self.screen_manager.register_screen(
            ScreenType.MILITARY,
            MilitaryScreen(self.screen_manager)
        )
        self.screen_manager.register_screen(
            ScreenType.CONSTRUCTION,
            ConstructionScreen(self.screen_manager)
        )
        self.screen_manager.register_screen(
            ScreenType.DIPLOMACY,
            DiplomacyScreen(self.screen_manager)
        )
        self.screen_manager.register_screen(
            ScreenType.POPULATION,
            PopulationScreen(self.screen_manager)
        )
        self.screen_manager.register_screen(
            ScreenType.EVENT,
            EventPopupScreen(self.screen_manager)
        )
        
        # Oyun Sonu ekranı
        from ui.screens.game_over_screen import GameOverScreen
        self.screen_manager.register_screen(
            ScreenType.GAME_OVER,
            GameOverScreen(self.screen_manager)
        )
        
        # Kayıt/Yükleme ekranı
        from ui.screens.save_load_screen import SaveLoadScreen
        self.screen_manager.register_screen(
            ScreenType.SAVE_LOAD,
            SaveLoadScreen(self.screen_manager)
        )
        
        # İşçi ekranı
        from ui.screens.workers_screen import WorkersScreen
        self.screen_manager.register_screen(
            ScreenType.WORKERS,
            WorkersScreen(self.screen_manager)
        )
        
        # Harita ekranı
        from ui.screens.map_screen import MapScreen
        self.screen_manager.register_screen(
            ScreenType.MAP,
            MapScreen(self.screen_manager)
        )
        
        # Savaş ekranı
        from ui.screens.warfare_screen import WarfareScreen
        self.screen_manager.register_screen(
            ScreenType.WARFARE,
            WarfareScreen(self.screen_manager)
        )
        
        # Danışman (Kethüda) ekranı
        from ui.screens.advisor_screen import AdvisorScreen
        self.screen_manager.register_screen(
            ScreenType.ADVISOR,
            AdvisorScreen(self.screen_manager)
        )
        
        # Ticaret ekranı
        from ui.screens.trade_screen import TradeScreen
        self.screen_manager.register_screen(
            ScreenType.TRADE,
            TradeScreen(self.screen_manager)
        )
        
        # Eyalet seçim ekranı
        from ui.screens.province_select_screen import ProvinceSelectScreen
        self.screen_manager.register_screen(
            ScreenType.PROVINCE_SELECT,
            ProvinceSelectScreen(self.screen_manager)
        )
        
        # İnteraktif savaş ekranı
        from ui.screens.battle_screen import BattleScreen
        self.screen_manager.register_screen(
            ScreenType.BATTLE,
            BattleScreen(self.screen_manager)
        )
        
        # Çok oyunculu lobi ekranı
        from ui.screens.multiplayer_lobby import MultiplayerLobbyScreen
        self.screen_manager.register_screen(
            ScreenType.MULTIPLAYER,
            MultiplayerLobbyScreen(self.screen_manager)
        )
        
        # Çok oyunculu oyun ekranı
        from ui.screens.multiplayer_game_screen import MultiplayerGameScreen
        self.screen_manager.register_screen(
            ScreenType.MULTIPLAYER_GAME,
            MultiplayerGameScreen(self.screen_manager)
        )
        
        # Akın rapor ekranı
        from ui.screens.raid_report_screen import RaidReportScreen
        self.screen_manager.register_screen(
            ScreenType.RAID_REPORT,
            RaidReportScreen(self.screen_manager)
        )
        
        # Bina iç ekranı
        from ui.screens.building_interior_screen import BuildingInteriorScreen
        self.screen_manager.register_screen(
            ScreenType.BUILDING_INTERIOR,
            BuildingInteriorScreen(self.screen_manager)
        )
        
        # Ayarlar ekranı
        from ui.screens.settings_screen import SettingsScreen
        self.screen_manager.register_screen(
            ScreenType.SETTINGS,
            SettingsScreen(self.screen_manager)
        )
        
        # Müzakere ekranı
        from ui.screens.negotiation_screen import NegotiationScreen
        self.screen_manager.register_screen(
            ScreenType.NEGOTIATION,
            NegotiationScreen(self.screen_manager)
        )
        
        # Casusluk ekranı (YENİ)
        from ui.screens.espionage_screen import EspionageScreen
        self.screen_manager.register_screen(
            ScreenType.ESPIONAGE,
            EspionageScreen(self.screen_manager)
        )
        
        # Din/Kültür ekranı (YENİ)
        from ui.screens.religion_screen import ReligionScreen
        self.screen_manager.register_screen(
            ScreenType.RELIGION,
            ReligionScreen(self.screen_manager)
        )
        
        # Eyalet Divanı ekranı (YENİ)
        from ui.screens.divan_screen import DivanScreen
        self.screen_manager.register_screen(
            ScreenType.DIVAN,
            DivanScreen(self.screen_manager)
        )
        
        # Başarılar ekranı (YENİ)
        from ui.screens.achievement_screen import AchievementScreen
        self.screen_manager.register_screen(
            ScreenType.ACHIEVEMENT,
            AchievementScreen(self.screen_manager)
        )
        
        # Eğitim ekranı (YENİ)
        from ui.screens.tutorial_screen import TutorialScreen
        self.screen_manager.register_screen(
            ScreenType.TUTORIAL,
            TutorialScreen(self.screen_manager)
        )
        
        # İşçi görüşme ekranı (YENİ)
        from ui.screens.worker_interview_screen import WorkerInterviewScreen
        self.screen_manager.register_screen(
            ScreenType.WORKER_INTERVIEW,
            WorkerInterviewScreen(self.screen_manager)
        )
        
        # Deniz kuvvetleri ekranı (YENİ)
        from ui.screens.naval_screen import NavalScreen
        self.screen_manager.register_screen(
            ScreenType.NAVAL,
            NavalScreen(self.screen_manager)
        )
        
        # Topçu ekranı (YENİ)
        from ui.screens.artillery_screen import ArtilleryScreen
        self.screen_manager.register_screen(
            ScreenType.ARTILLERY,
            ArtilleryScreen(self.screen_manager)
        )
        
        # Karakter oluşturma ekranı (YENİ)
        from ui.screens.character_creation_screen import CharacterCreationScreen
        self.screen_manager.register_screen(
            ScreenType.CHARACTER_CREATION,
            CharacterCreationScreen(self.screen_manager)
        )
        
        # Lonca yönetim ekranı (YENİ)
        from ui.screens.guild_screen import GuildScreen
        self.screen_manager.register_screen(
            ScreenType.GUILD,
            GuildScreen(self.screen_manager)
        )
        
        # Geçmiş olaylar ekranı (YENİ)
        from ui.screens.history_screen import HistoryScreen
        self.screen_manager.register_screen(
            ScreenType.HISTORY,
            HistoryScreen(self.screen_manager)
        )
    
    def _load_sounds(self):
        """Ses dosyalarını yükle"""
        base_path = os.path.dirname(os.path.abspath(__file__))
        
        # UI sesleri
        ui_path = os.path.join(base_path, 'audio', 'sounds', 'ui')
        self.audio.load_sounds_from_directory(ui_path, prefix='ui_')
        
        # Oyun ses kategorileri
        categories = [
            'military', 'construction', 'economy', 'diplomacy',
            'naval', 'ambient', 'espionage', 'religion', 'events'
        ]
        for cat in categories:
            cat_path = os.path.join(base_path, 'audio', 'sounds', cat)
            self.audio.load_sounds_from_directory(cat_path, prefix=f'{cat}_')
        
        # Müzik yüklemesi ve yönetimi artık tamamen MusicManager (ScreenManager üzerinden) 
        # tarafından bağlam-duyarlı (context-aware) olarak yapılmaktadır.
    
    def run(self):
        """Ana oyun döngüsü"""
        # Ana menüyle başla
        self.screen_manager.change_screen(ScreenType.MAIN_MENU)
        
        while self.running:
            # Delta time (saniye)
            dt = self.clock.tick(FPS) / 1000.0
            
            # Olayları işle
            self._handle_events()
            
            # Güncelleme callback'lerini işle (thread-safe)
            self.updater.process_callbacks()
            
            # Güncelle
            self.screen_manager.update(dt)
            
            # Çiz
            self.screen_manager.draw(self.screen)
            
            # Olay kontrolü (oyun ekranındayken)
            self._check_event_popup()
            
            # Oyun Sonu kontrolü (Win / Loss)
            if self.game_manager and getattr(self.game_manager, 'game_over', False):
                if self.screen_manager.current_screen_type != ScreenType.GAME_OVER:
                    self.screen_manager.change_screen(ScreenType.GAME_OVER)
            
            # Ekranı güncelle
            pygame.display.flip()
        
        # Temizlik
        self._cleanup()
    
    def _handle_events(self):
        """Pygame olaylarını işle"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                return
            
            # Global kısayollar
            if event.type == pygame.KEYDOWN:
                # Shift + Page Up - Ambiyans sesini artır
                if event.key == pygame.K_PAGEUP and pygame.key.get_mods() & pygame.KMOD_SHIFT:
                    self.audio.increase_ambient_volume(0.05)
                    continue
                
                # Shift + Page Down - Ambiyans sesini azalt
                if event.key == pygame.K_PAGEDOWN and pygame.key.get_mods() & pygame.KMOD_SHIFT:
                    self.audio.decrease_ambient_volume(0.05)
                    continue
                
                # Page Up - Müzik sesini artır
                if event.key == pygame.K_PAGEUP:
                    self.audio.increase_music_volume(0.05)
                    continue
                
                # Page Down - Müzik sesini azalt
                if event.key == pygame.K_PAGEDOWN:
                    self.audio.decrease_music_volume(0.05)
                    continue
                
                # O tuşu - olay popup
                if event.key == pygame.K_o:
                    if (self.screen_manager.current_screen_type == ScreenType.PROVINCE_VIEW and
                        self.game_manager.events.current_event):
                        self.screen_manager.change_screen(ScreenType.EVENT)
                        continue
                
                # J tuşu - Mevsim bilgisi (sadece oyun ekranlarında)
                game_screens = [ScreenType.PROVINCE_VIEW, ScreenType.ECONOMY, ScreenType.MILITARY, 
                               ScreenType.DIPLOMACY, ScreenType.CONSTRUCTION, ScreenType.TRADE,
                               ScreenType.WORKERS, ScreenType.POPULATION, ScreenType.MAP]
                if event.key == pygame.K_j and self.screen_manager.current_screen_type in game_screens:
                    gm = self.game_manager
                    if gm:
                        season = gm.get_season()
                        food_effects = {
                            "Kış": "azalmış (%75)",
                            "İlkbahar": "artırılmış (%120)",
                            "Yaz": "normal (%100)",
                            "Sonbahar": "yüksek hasat (%150)"
                        }
                        food_mod = food_effects.get(season, "normal")
                        month_names = ["", "Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran",
                                      "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]
                        month_name = month_names[gm.current_month] if 1 <= gm.current_month <= 12 else ""
                        self.audio.speak(
                            f"Mevsim: {season}. Yiyecek üretimi {food_mod}. "
                            f"Tarih: {gm.current_day} {month_name} {gm.current_year}",
                            interrupt=True
                        )
                        continue
            
            # Aktif ekrana ilet
            self.screen_manager.handle_event(event)
    
    def _check_event_popup(self):
        """Olay popup kontrolü"""
        # Sadece ana ekrandayken ve olay varsa
        if (self.screen_manager.current_screen_type == ScreenType.PROVINCE_VIEW and
            self.game_manager.events.current_event):
            # İlk kez olay çıktıysa bildir
            pass  # Bu province_view'da hallediliyor
    
    def _cleanup(self):
        """Temizlik işlemleri"""
        self.audio.cleanup()
        pygame.quit()


def main():
    """Ana fonksiyon"""
    try:
        game = Game()
        game.run()
    except Exception as e:
        print(f"Hata oluştu: {e}")
        import traceback
        traceback.print_exc()
        
        # Pygame'i temizle
        pygame.quit()
        
        # Hata durumunda bekle
        input("Devam etmek için Enter'a basın...")


if __name__ == "__main__":
    main()
