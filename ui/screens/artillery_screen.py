# -*- coding: utf-8 -*-
"""
Osmanlı Eyalet Yönetim Simülasyonu - Topçu Ekranı
Topçu Ocağı ve top üretimi yönetimi
"""

import pygame
from ui.screen_manager import BaseScreen, ScreenType
from ui.components import Button, Panel, MenuList
from config import COLORS, FONTS, SCREEN_WIDTH, SCREEN_HEIGHT
from game.systems.artillery import CannonType, CANNON_DEFINITIONS


class ArtilleryScreen(BaseScreen):
    """Topçu ekranı (Topçu Ocağı)"""
    
    def __init__(self, screen_manager):
        super().__init__(screen_manager)
        
        # Topçu birliği paneli
        self.artillery_panel = Panel(20, 80, 450, 250, "Topçu Birliği")
        
        # Dökümhane paneli
        self.foundry_panel = Panel(490, 80, 500, 120, "Dökümhane Kaynakları")
        
        # Top listesi menüsü
        self.cannon_menu = MenuList(
            x=20,
            y=200,
            width=450,
            item_height=40
        )
        
        # Üretim menüsü
        self.production_menu = MenuList(
            x=490,
            y=230,
            width=500,
            item_height=50
        )
        
        # Üretim kuyruğu paneli
        self.queue_panel = Panel(490, 480, 500, 150, "Üretim Kuyruğu")
        
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
        self.menu_mode = "cannons"  # "cannons" veya "produce"
    
    def get_header_font(self):
        if self._header_font is None:
            self._header_font = pygame.font.Font(None, FONTS['header'])
        return self._header_font
    
    def on_enter(self):
        self._update_panels()
        self._setup_cannon_menu()
        self._setup_production_menu()
        self.audio.play_game_sound('military', 'cannon')
    
    def announce_screen(self):
        self.audio.announce_screen_change("Topçu Ocağı")
        gm = self.screen_manager.game_manager
        if gm and hasattr(gm, 'artillery'):
            gm.artillery.announce_artillery()
    
    def _setup_cannon_menu(self):
        """Top envanteri menüsünü oluştur"""
        self.cannon_menu.clear()
        gm = self.screen_manager.game_manager
        if not gm or not hasattr(gm, 'artillery'):
            self.cannon_menu.add_item("Topçu Ocağı kurulmamış", None)
            return
        
        artillery = gm.artillery
        
        if not artillery.cannons:
            self.cannon_menu.add_item("Henüz topunuz yok", None)
            self.cannon_menu.add_item("", None)
            self.cannon_menu.add_item("TOP ÜRET (aşağı ok ile)", lambda: self._switch_to_produce())
            return
        
        for i, cannon in enumerate(artillery.cannons):
            definition = cannon.get_definition()
            condition_text = f"[%{cannon.condition}]" if cannon.condition < 100 else ""
            
            self.cannon_menu.add_item(
                f"{cannon.name} - {definition.name} {condition_text}",
                lambda idx=i: self._select_cannon(idx)
            )
        
        # Ayırıcı ve üretim butonu
        self.cannon_menu.add_item("", None)
        self.cannon_menu.add_item("YENİ TOP ÜRET", lambda: self._switch_to_produce())
    
    def _setup_production_menu(self):
        """Üretim menüsünü oluştur"""
        self.production_menu.clear()
        gm = self.screen_manager.game_manager
        if not gm:
            return
        
        # Geri butonu
        self.production_menu.add_item("<- Toplara Dön", lambda: self._switch_to_cannons())
        self.production_menu.add_item("", None)
        
        for cannon_type in CannonType:
            definition = CANNON_DEFINITIONS[cannon_type]
            
            # Maliyet özeti (Türkçe)
            cost_text = f"{definition.gold_cost} altın, {definition.iron_cost} demir, {definition.stone_cost} taş"
            
            # Üretilebilir mi?
            can_produce = False
            if hasattr(gm, 'artillery'):
                can_produce, _ = gm.artillery.can_produce_cannon(cannon_type, gm.economy)
            
            prefix = "" if can_produce else "[X] "
            
            self.production_menu.add_item(
                f"{prefix}{definition.name} ({cost_text}) - {definition.build_time} tur",
                lambda ct=cannon_type: self._start_production(ct)
            )
    
    def _switch_to_produce(self):
        """Üretim moduna geç"""
        self.menu_mode = "produce"
        self._setup_production_menu()
        self.audio.speak("Dökümhane - top üretim menüsü. Bir top türü seçin.", interrupt=True)
    
    def _switch_to_cannons(self):
        """Envanter moduna geç"""
        self.menu_mode = "cannons"
        self._setup_cannon_menu()
        self.audio.speak("Top envanteri.", interrupt=True)
    
    def _select_cannon(self, index: int):
        """Top seç ve bilgi oku"""
        gm = self.screen_manager.game_manager
        if not gm or not hasattr(gm, 'artillery'):
            return
        
        artillery = gm.artillery
        if index >= len(artillery.cannons):
            return
        
        cannon = artillery.cannons[index]
        definition = cannon.get_definition()
        
        info_parts = [
            f"{cannon.name}.",
            f"Tür: {definition.name}.",
            f"Durum: yüzde {cannon.condition}.",
            f"Güç: {cannon.get_power()}.",
            f"Menzil: {definition.range_level}.",
            f"Kuşatma bonusu: artı {definition.siege_bonus}.",
            f"Mürettebat: {definition.crew_required} topçu.",
            f"Bakım: {definition.maintenance} altın/tur."
        ]
        
        self.audio.speak(" ".join(info_parts), interrupt=True)
    
    def _start_production(self, cannon_type: CannonType):
        """Top üretimi başlat"""
        gm = self.screen_manager.game_manager
        if not gm or not hasattr(gm, 'artillery'):
            return
        
        success = gm.artillery.start_production(cannon_type, gm.economy)
        if success:
            self.audio.play_game_sound('construction', 'hammer')
            self._update_panels()
            self._setup_production_menu()
            self._update_queue_panel()
    
    def _update_panels(self):
        """Panelleri güncelle"""
        gm = self.screen_manager.game_manager
        if not gm:
            return
        
        # Topçu paneli
        self.artillery_panel.clear()
        
        if hasattr(gm, 'artillery'):
            artillery = gm.artillery
            self.artillery_panel.add_item("Toplam Top", str(len(artillery.cannons)))
            self.artillery_panel.add_item("Toplam Güç", str(artillery.get_total_power()))
            self.artillery_panel.add_item("Kuşatma Bonusu", f"+{artillery.get_siege_bonus()}")
            self.artillery_panel.add_item("Bakım Maliyeti", f"{artillery.get_maintenance_cost()} altın/tur")
            
            # Top türü sayıları
            counts = artillery.get_cannon_counts()
            for cannon_type, count in counts.items():
                if count > 0:
                    name = CANNON_DEFINITIONS[cannon_type].name
                    self.artillery_panel.add_item(name, str(count))
        else:
            self.artillery_panel.add_item("", "Topçu Ocağı sistemine erişilemiyor")
        
        # Dökümhane paneli
        self.foundry_panel.clear()
        self.foundry_panel.add_item("Altın", str(gm.economy.resources.gold))
        self.foundry_panel.add_item("Demir", str(gm.economy.resources.iron))
        self.foundry_panel.add_item("Taş", str(gm.economy.resources.stone))
        
        # Kuyruk paneli
        self._update_queue_panel()
    
    def _update_queue_panel(self):
        """Üretim kuyruğu panelini güncelle"""
        gm = self.screen_manager.game_manager
        self.queue_panel.clear()
        
        if not gm or not hasattr(gm, 'artillery'):
            return
        
        artillery = gm.artillery
        
        if not artillery.production_queue:
            self.queue_panel.add_item("", "Üretim kuyruğu boş")
            return
        
        for i, production in enumerate(artillery.production_queue):
            definition = CANNON_DEFINITIONS[production.cannon_type]
            name = production.custom_name or definition.name
            self.queue_panel.add_item(
                f"{i+1}. {name}",
                f"{production.turns_remaining} tur kaldı"
            )
    
    def _go_back(self):
        self.screen_manager.change_screen(ScreenType.PROVINCE_VIEW)
    
    def handle_event(self, event) -> bool:
        # Aktif menüyü işle
        if self.menu_mode == "produce":
            if self.production_menu.handle_event(event):
                return True
        else:
            if self.cannon_menu.handle_event(event):
                return True
        
        if self.back_button.handle_event(event):
            return True
        
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_BACKSPACE:
                if self.menu_mode == "produce":
                    self._switch_to_cannons()
                else:
                    self._go_back()
                return True
            
            if event.key == pygame.K_ESCAPE:
                self._go_back()
                return True
            
            # Tab ile menüler arası geçiş
            if event.key == pygame.K_TAB:
                if self.menu_mode == "cannons":
                    self._switch_to_produce()
                else:
                    self._switch_to_cannons()
                return True
            
            # F1 - Özet
            if event.key == pygame.K_F1:
                gm = self.screen_manager.game_manager
                if gm and hasattr(gm, 'artillery'):
                    gm.artillery.announce_artillery()
                return True
        
        return False
    
    def update(self, dt: float):
        pass
    
    def draw(self, surface: pygame.Surface):
        # Başlık
        header_font = self.get_header_font()
        title = header_font.render("TOPÇU OCAĞI - DÖKÜMHANE", True, COLORS['gold'])
        surface.blit(title, (20, 20))
        
        # Paneller
        self.artillery_panel.draw(surface)
        self.foundry_panel.draw(surface)
        self.queue_panel.draw(surface)
        
        small_font = pygame.font.Font(None, FONTS['subheader'])
        
        if self.menu_mode == "produce":
            # Üretim menüsü
            produce_title = small_font.render("Top Üret", True, COLORS['gold'])
            surface.blit(produce_title, (490, 205))
            self.production_menu.draw(surface)
        else:
            # Top listesi
            cannon_title = small_font.render("Toplar", True, COLORS['gold'])
            surface.blit(cannon_title, (20, 175))
            self.cannon_menu.draw(surface)
        
        # Geri butonu
        self.back_button.draw(surface)
