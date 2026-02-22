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
        self.menu_mode = "ships"  # "ships", "build"
    
    def get_header_font(self):
        if self._header_font is None:
            self._header_font = get_font(FONTS['header'])
        return self._header_font
    
    def on_enter(self):
        self._update_panels()
        self._setup_ship_menu()
        self._setup_build_menu()
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
            
            # Eğer gemi tamirdeyse ekstra bilgi ver
            repair_info = ""
            for r in naval.repair_queue:
                if r.ship.ship_id == ship.ship_id:
                    repair_info = f" [Tamirde: {r.turns_remaining} Tur]"
                    break
                    
            health_text = f"[%{ship.health}]" if ship.health < 100 else ""
            
            # # işaretini sil
            display_name = ship.name.replace(" #", " ")
            
            self.ship_menu.add_item(
                f"{display_name} - {definition.name} {health_text}{repair_info}",
                lambda idx=i: self._select_ship(idx)
            )
        
        # Ayırıcı ve inşa butonu
        self.ship_menu.add_item("", None)
        self.ship_menu.add_item("YENİ GEMİ İNŞA ET", lambda: self._switch_to_build())
        self.ship_menu.add_item("FİLOYU TAMİR ET", lambda: self._repair_fleet())
    
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
            
            # Maliyet özeti (Türkçe) - Eksiksiz
            costs = []
            if definition.gold_cost > 0: costs.append(f"{definition.gold_cost} Altın")
            if definition.wood_cost > 0: costs.append(f"{definition.wood_cost} Kereste")
            if hasattr(definition, 'iron_cost') and definition.iron_cost > 0: costs.append(f"{definition.iron_cost} Demir")
            if hasattr(definition, 'rope_cost') and definition.rope_cost > 0: costs.append(f"{definition.rope_cost} Halat")
            if hasattr(definition, 'tar_cost') and definition.tar_cost > 0: costs.append(f"{definition.tar_cost} Katran")
            if hasattr(definition, 'sailcloth_cost') and definition.sailcloth_cost > 0: costs.append(f"{definition.sailcloth_cost} Yelken Bezi")
            cost_text = ", ".join(costs)
            
            # İnşa edilebilir mi?
            can_build = False
            if hasattr(gm, 'naval'):
                can_build, _ = gm.naval.can_build_ship(ship_type, gm.economy)
            
            prefix = "" if can_build else "[X] "
            
            self.build_menu.add_item(
                f"{prefix}{definition.name} ({cost_text}) - {definition.build_time} tur",
                lambda st=ship_type: self._start_build(st)
            )
            
    def _switch_to_build(self):
        """İnşa moduna geç"""
        self.menu_mode = "build"
        self._setup_build_menu()
        self.audio.speak("Tersane - gemi inşa menüsü. Bir gemi türü seçin.", interrupt=True)
    
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
        
        success = gm.naval.start_construction(ship_type, gm.economy, gm.construction)
        if success:
            self._update_panels()
            self._setup_build_menu()
            self._update_queue_panel()
            
    def _repair_fleet(self):
        """Filoyu tamir et"""
        gm = self.screen_manager.game_manager
        if not gm or not hasattr(gm, 'naval'):
            return
            
        success, message = gm.naval.repair_fleet(gm.economy)
        if success:
            self.audio.play_game_sound('construction', 'build')
            self._update_panels()
            self._setup_ship_menu()
        else:
            self.audio.speak(message, interrupt=True)
    
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
        
        if not naval.construction_queue and not getattr(naval, 'repair_queue', []):
            self.queue_panel.add_item("", "İnşa ve tamir kuyruğu boş")
            return
        
        # İnşaatlar
        for i, construction in enumerate(naval.construction_queue):
            definition = SHIP_DEFINITIONS[construction.ship_type]
            name = construction.custom_name or definition.name
            display_name = name.replace(" #", " ")
            self.queue_panel.add_item(
                f"İnşa: {display_name}",
                f"{construction.turns_remaining} tur kaldı"
            )
            
        # Tamirler
        if hasattr(naval, 'repair_queue'):
            for i, repair in enumerate(naval.repair_queue):
                display_name = repair.ship.name.replace(" #", " ")
                self.queue_panel.add_item(
                    f"Tamir: {display_name}",
                    f"{repair.turns_remaining} tur kaldı"
                )
    
    def _go_back(self):
        self.screen_manager.change_screen(ScreenType.PROVINCE_VIEW)
    
    def handle_event(self, event) -> bool:
        # Aktif menüyü işle
        if self.menu_mode == "build":
            if self.build_menu.handle_event(event):
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
        else:
            # Gemi listesi
            ship_title = small_font.render("Gemiler", True, COLORS['gold'])
            surface.blit(ship_title, (20, 175))
            self.ship_menu.draw(surface)
        
        # Geri butonu
        self.back_button.draw(surface)
