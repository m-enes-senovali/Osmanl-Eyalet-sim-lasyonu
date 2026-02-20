# -*- coding: utf-8 -*-
"""
Osmanlı Eyalet Yönetim Simülasyonu - Deniz Kuvvetleri Ekranı
Tersane ve filo yönetimi
"""

import pygame
from ui.screen_manager import BaseScreen, ScreenType
from ui.components import Button, Panel, MenuList
from config import COLORS, FONTS, SCREEN_WIDTH, SCREEN_HEIGHT, get_font
from game.systems.naval import ShipType, SHIP_DEFINITIONS


class NavalScreen(BaseScreen):
    """Deniz kuvvetleri ekranı"""
    
    def __init__(self, screen_manager):
        super().__init__(screen_manager)
        
        # Filo paneli
        self.fleet_panel = Panel(20, 80, 450, 280, "Filo Durumu")
        
        # Tersane paneli
        self.shipyard_panel = Panel(490, 80, 500, 150, "Tersane")
        
        # Gemi listesi menüsü
        self.ship_menu = MenuList(
            x=20,
            y=200,
            width=450,
            item_height=40
        )
        
        # İnşa menüsü
        self.build_menu = MenuList(
            x=490,
            y=260,
            width=500,
            item_height=45
        )
        
        # İnşa kuyruğu paneli
        self.queue_panel = Panel(490, 480, 500, 150, "İnşa Kuyruğu")
        
        # Akın menüsü (YENİ)
        self.raid_menu = MenuList(
            x=490,
            y=260,
            width=500,
            item_height=45
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
        
        self._header_font = None
        self.menu_mode = "ships"  # "ships", "build", "raid"
    
    def get_header_font(self):
        if self._header_font is None:
            self._header_font = get_font(FONTS['header'])
        return self._header_font
    
    def on_enter(self):
        self._update_panels()
        self._setup_ship_menu()
        self._setup_build_menu()
        self._setup_raid_menu()
        self.audio.play_ambient('waves')
    
    def announce_screen(self):
        self.audio.announce_screen_change("Deniz Kuvvetleri")
        gm = self.screen_manager.game_manager
        if gm and hasattr(gm, 'naval'):
            gm.naval.announce_fleet()
    
    def _setup_ship_menu(self):
        """Gemi listesini oluştur"""
        self.ship_menu.clear()
        gm = self.screen_manager.game_manager
        if not gm or not hasattr(gm, 'naval'):
            self.ship_menu.add_item("Tersane kurulmamış", None)
            return
        
        naval = gm.naval
        
        if not naval.ships:
            self.ship_menu.add_item("Henüz geminiz yok", None)
            self.ship_menu.add_item("", None)
            self.ship_menu.add_item("GEMİ İNŞA ET (aşağı ok ile)", lambda: self._switch_to_build())
            return
        
        for i, ship in enumerate(naval.ships):
            definition = ship.get_definition()
            health_text = f"[%{ship.health}]" if ship.health < 100 else ""
            
            self.ship_menu.add_item(
                f"{ship.name} - {definition.name} {health_text}",
                lambda idx=i: self._select_ship(idx)
            )
        
        # Ayırıcı ve inşa butonu
        self.ship_menu.add_item("", None)
        self.ship_menu.add_item("YENİ GEMİ İNŞA ET", lambda: self._switch_to_build())
        self.ship_menu.add_item("DENİZ AKINI DÜZENLE", lambda: self._switch_to_raid())
    
    def _setup_build_menu(self):
        """İnşa menüsünü oluştur"""
        self.build_menu.clear()
        gm = self.screen_manager.game_manager
        if not gm:
            return
        
        # Geri butonu
        self.build_menu.add_item("<- Filoya Dön", lambda: self._switch_to_ships())
        self.build_menu.add_item("", None)
        
        for ship_type in ShipType:
            definition = SHIP_DEFINITIONS[ship_type]
            
            # Maliyet özeti (Türkçe)
            cost_text = f"{definition.gold_cost} altın, {definition.wood_cost} kereste"
            
            # İnşa edilebilir mi?
            can_build = False
            if hasattr(gm, 'naval'):
                can_build, _ = gm.naval.can_build_ship(ship_type, gm.economy)
            
            prefix = "" if can_build else "[X] "
            
            self.build_menu.add_item(
                f"{prefix}{definition.name} ({cost_text}) - {definition.build_time} tur",
                lambda st=ship_type: self._start_build(st)
            )
            
    def _setup_raid_menu(self):
        """Akın menüsünü oluştur"""
        self.raid_menu.clear()
        self.raid_menu.add_item("<- Filoya Dön", lambda: self._switch_to_ships())
        self.raid_menu.add_item("", None)
        
        self.raid_menu.add_item("Ticaret Rotası (Kolay) - Düşük Risk, Düşük Altın", lambda: self._start_raid('easy'))
        self.raid_menu.add_item("Sahil Kasabası (Orta) - Orta Risk, Orta Altın", lambda: self._start_raid('medium'))
        self.raid_menu.add_item("Liman Kalesi (Zor) - Yüksek Risk, Yüksek Altın", lambda: self._start_raid('hard'))
    
    def _switch_to_build(self):
        """İnşa moduna geç"""
        self.menu_mode = "build"
        self._setup_build_menu()
        self.audio.speak("Tersane - gemi inşa menüsü. Bir gemi türü seçin.", interrupt=True)
    
    def _switch_to_raid(self):
        """Akın moduna geç"""
        self.menu_mode = "raid"
        self._setup_raid_menu()
        self.audio.speak("Akın planlama. Hedef seçin.", interrupt=True)
    
    def _switch_to_ships(self):
        """Filo moduna geç"""
        self.menu_mode = "ships"
        self._setup_ship_menu()
        self.audio.speak("Filo listesi.", interrupt=True)
    
    def _select_ship(self, index: int):
        """Gemi seç ve bilgi oku"""
        gm = self.screen_manager.game_manager
        if not gm or not hasattr(gm, 'naval'):
            return
        
        naval = gm.naval
        if index >= len(naval.ships):
            return
        
        ship = naval.ships[index]
        definition = ship.get_definition()
        
        info_parts = [
            f"{ship.name}.",
            f"Tür: {definition.name}.",
            f"Sağlık: yüzde {ship.health}.",
            f"Savaş gücü: {ship.get_combat_power()}.",
        ]
        
        if not definition.is_warship:
            info_parts.append(f"Yük kapasitesi: {definition.cargo_capacity}.")
        
        info_parts.append(f"Bakım: {definition.maintenance} altın/tur.")
        
        self.audio.speak(" ".join(info_parts), interrupt=True)
    
    def _start_build(self, ship_type: ShipType):
        """Gemi inşası başlat"""
        gm = self.screen_manager.game_manager
        if not gm or not hasattr(gm, 'naval'):
            return
        
        success = gm.naval.start_construction(ship_type, gm.economy)
        if success:
            self._update_panels()
            self._setup_build_menu()
            self._update_queue_panel()
            
    def _start_raid(self, difficulty: str):
        """Akın başlat"""
        gm = self.screen_manager.game_manager
        if not gm or not hasattr(gm, 'naval'):
            return
            
        result = gm.naval.conduct_raid(difficulty)
        
        if result['success']:
            gm.economy.add_resources(gold=result['gold'])
            self.audio.play_game_sound('warfare', 'victory')
        else:
            self.audio.play_game_sound('warfare', 'defeat')
            
        self.audio.announce(result['message'])
        self._update_panels()
        self._setup_ship_menu() # Gemiler batmış olabilir
    
    def _update_panels(self):
        """Panelleri güncelle"""
        gm = self.screen_manager.game_manager
        if not gm:
            return
        
        # Filo paneli
        self.fleet_panel.clear()
        
        if hasattr(gm, 'naval'):
            naval = gm.naval
            self.fleet_panel.add_item("Toplam Gemi", str(len(naval.ships)))
            self.fleet_panel.add_item("Savaş Gücü", str(naval.get_fleet_power()))
            self.fleet_panel.add_item("Ticaret Kapasitesi", str(naval.get_trade_capacity()))
            self.fleet_panel.add_item("Bakım Maliyeti", f"{naval.get_maintenance_cost()} altın/tur")
            
            # Gemi türü sayıları
            counts = naval.get_ship_counts()
            for ship_type, count in counts.items():
                if count > 0:
                    name = SHIP_DEFINITIONS[ship_type].name
                    self.fleet_panel.add_item(name, str(count))
        else:
            self.fleet_panel.add_item("", "Tersane sistemine erişilemiyor")
        
        # Tersane paneli
        self.shipyard_panel.clear()
        self.shipyard_panel.add_item("Halat", str(gm.economy.resources.rope))
        self.shipyard_panel.add_item("Katran", str(gm.economy.resources.tar))
        self.shipyard_panel.add_item("Yelken Bezi", str(gm.economy.resources.sailcloth))
        
        # Kuyruk paneli
        self._update_queue_panel()
    
    def _update_queue_panel(self):
        """İnşa kuyruğu panelini güncelle"""
        gm = self.screen_manager.game_manager
        self.queue_panel.clear()
        
        if not gm or not hasattr(gm, 'naval'):
            return
        
        naval = gm.naval
        
        if not naval.construction_queue:
            self.queue_panel.add_item("", "İnşa kuyruğu boş")
            return
        
        for i, construction in enumerate(naval.construction_queue):
            definition = SHIP_DEFINITIONS[construction.ship_type]
            name = construction.custom_name or definition.name
            self.queue_panel.add_item(
                f"{i+1}. {name}",
                f"{construction.turns_remaining} tur kaldı"
            )
    
    def _go_back(self):
        self.screen_manager.change_screen(ScreenType.PROVINCE_VIEW)
    
    def handle_event(self, event) -> bool:
        # Aktif menüyü işle
        if self.menu_mode == "build":
            if self.build_menu.handle_event(event):
                return True
        elif self.menu_mode == "raid":
            if self.raid_menu.handle_event(event):
                return True
        else:
            if self.ship_menu.handle_event(event):
                return True
        
        if self.back_button.handle_event(event):
            return True
        
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_BACKSPACE:
                if self.menu_mode != "ships":
                    self._switch_to_ships()
                else:
                    self._go_back()
                return True
            
            if event.key == pygame.K_ESCAPE:
                self._go_back()
                return True
            
            # Tab ile menüler arası geçiş
            if event.key == pygame.K_TAB:
                if self.menu_mode == "ships":
                    self._switch_to_build()
                elif self.menu_mode == "build":
                    self._switch_to_raid()
                else:
                    self._switch_to_ships()
                return True
            
            # F1 - Özet
            if event.key == pygame.K_F1:
                gm = self.screen_manager.game_manager
                if gm and hasattr(gm, 'naval'):
                    gm.naval.announce_fleet()
                return True
        
        return False
    
    def update(self, dt: float):
        pass
    
    def draw(self, surface: pygame.Surface):
        # Başlık
        header_font = self.get_header_font()
        title = header_font.render("DENİZ KUVVETLERİ - TERSANE", True, COLORS['gold'])
        surface.blit(title, (20, 20))
        
        # Paneller
        self.fleet_panel.draw(surface)
        self.shipyard_panel.draw(surface)
        self.queue_panel.draw(surface)
        
        small_font = get_font(FONTS['subheader'])
        
        if self.menu_mode == "build":
            # İnşa menüsü
            build_title = small_font.render("Gemi İnşa Et", True, COLORS['gold'])
            surface.blit(build_title, (490, 235))
            self.build_menu.draw(surface)
        elif self.menu_mode == "raid":
            # Akın menüsü
            raid_title = small_font.render("Deniz Akını", True, COLORS['gold'])
            surface.blit(raid_title, (490, 235))
            self.raid_menu.draw(surface)
        else:
            # Gemi listesi
            ship_title = small_font.render("Gemiler", True, COLORS['gold'])
            surface.blit(ship_title, (20, 175))
            self.ship_menu.draw(surface)
        
        # Geri butonu
        self.back_button.draw(surface)
