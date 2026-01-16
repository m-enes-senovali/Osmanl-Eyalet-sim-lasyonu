# -*- coding: utf-8 -*-
"""
Osmanlı Eyalet Yönetim Simülasyonu - Bina İç Ekranı
Binaya girerek üretim, yönetim ve yükseltme işlemleri
"""

import pygame
from typing import Optional
from ui.screen_manager import BaseScreen, ScreenType
from ui.components import Button, Panel, MenuList
from game.systems.construction import BuildingType, BUILDING_DEFINITIONS
from config import COLORS, FONTS, SCREEN_WIDTH, SCREEN_HEIGHT


class BuildingInteriorScreen(BaseScreen):
    """Bina iç ekranı - üretim ve yönetim"""
    
    def __init__(self, screen_manager):
        super().__init__(screen_manager)
        
        self.building_type: Optional[BuildingType] = None
        self.building_level: int = 1
        
        # Ana panel
        self.info_panel = Panel(20, 80, 400, 250, "Bina Bilgisi")
        
        # Üretim paneli (sağ taraf)
        self.production_panel = Panel(450, 80, 400, 250, "Üretim")
        
        # Eylem menüsü
        self.action_menu = MenuList(
            x=20,
            y=360,
            width=830,
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
    
    def get_header_font(self):
        if self._header_font is None:
            self._header_font = pygame.font.Font(None, FONTS['header'])
        return self._header_font
    
    def set_building(self, building_type: BuildingType, level: int):
        """Görüntülenecek binayı ayarla"""
        self.building_type = building_type
        self.building_level = level
    
    def on_enter(self):
        self._update_panels()
        self._setup_action_menu()
    
    def announce_screen(self):
        if self.building_type:
            stats = BUILDING_DEFINITIONS[self.building_type]
            self.audio.announce_screen_change(f"{stats.name_tr} İç Mekanı")
            self.audio.speak(f"Seviye {self.building_level}. Eylem seçmek için menüyü kullanın.", interrupt=False)
        else:
            self.audio.announce_screen_change("Bina İç Mekanı")
    
    def _update_panels(self):
        """Panelleri güncelle"""
        gm = self.screen_manager.game_manager
        if not gm or not self.building_type:
            return
        
        stats = BUILDING_DEFINITIONS[self.building_type]
        
        # Bilgi paneli
        self.info_panel.clear()
        self.info_panel.add_item("Bina", stats.name_tr)
        self.info_panel.add_item("Seviye", f"{self.building_level} / {stats.max_level}")
        self.info_panel.add_item("Bakım", f"{stats.maintenance * self.building_level} altın/tur")
        
        if stats.happiness_bonus > 0:
            bonus = int(stats.happiness_bonus * (1 + (self.building_level - 1) * 0.5))
            self.info_panel.add_item("Mutluluk Bonusu", f"+{bonus}")
        if stats.trade_bonus > 0:
            bonus = int(stats.trade_bonus * (1 + (self.building_level - 1) * 0.5))
            self.info_panel.add_item("Ticaret Bonusu", f"+{bonus}")
        if stats.military_bonus > 0:
            bonus = int(stats.military_bonus * (1 + (self.building_level - 1) * 0.5))
            self.info_panel.add_item("Askeri Bonus", f"+{bonus}")
        if stats.food_production > 0:
            prod = int(stats.food_production * (1 + (self.building_level - 1) * 0.5))
            self.info_panel.add_item("Yiyecek Üretimi", f"+{prod}/tur")
        
        # Üretim paneli (binaya göre değişir)
        self.production_panel.clear()
        self._update_production_panel()
    
    def _update_production_panel(self):
        """Binaya özel üretim panelini güncelle"""
        gm = self.screen_manager.game_manager
        if not gm:
            return
        
        if self.building_type == BuildingType.ARTILLERY_FOUNDRY:
            # Topçu Ocağı - Top üretimi
            self.production_panel.title = "Top Üretimi"
            if hasattr(gm, 'artillery'):
                counts = gm.artillery.get_cannon_counts()
                from game.systems.artillery import CannonType, CANNON_DEFINITIONS
                for ct in CannonType:
                    cannon = CANNON_DEFINITIONS[ct]
                    self.production_panel.add_item(cannon.name, f"{counts[ct]} adet")
                
                # Üretim kuyruğu
                if gm.artillery.production_queue:
                    self.production_panel.add_item("", "")
                    self.production_panel.add_item("Üretimde", f"{len(gm.artillery.production_queue)} top")
        
        elif self.building_type == BuildingType.SHIPYARD:
            # Tersane - Gemi inşası
            self.production_panel.title = "Gemi İnşa"
            if hasattr(gm, 'naval'):
                counts = gm.naval.get_ship_counts()
                from game.systems.naval import ShipType, SHIP_DEFINITIONS
                for st in ShipType:
                    ship = SHIP_DEFINITIONS[st]
                    self.production_panel.add_item(ship.name, f"{counts[st]} adet")
                
                # İnşaat kuyruğu
                if gm.naval.construction_queue:
                    self.production_panel.add_item("", "")
                    self.production_panel.add_item("İnşaatta", f"{len(gm.naval.construction_queue)} gemi")
        
        elif self.building_type == BuildingType.BARRACKS:
            # Kışla - Asker eğitimi
            self.production_panel.title = "Asker Eğitimi"
            from game.systems.military import UnitType, UNIT_DEFINITIONS
            for ut in UnitType:
                unit = UNIT_DEFINITIONS[ut]
                count = gm.military.units.get(ut, 0)
                self.production_panel.add_item(unit.name_tr, f"{count} asker")
            
            # Eğitim kuyruğu
            if gm.military.training_queue:
                self.production_panel.add_item("", "")
                self.production_panel.add_item("Eğitimde", f"{len(gm.military.training_queue)} grup")
        
        elif self.building_type == BuildingType.FARM:
            # Çiftlik - Üretim bilgisi
            self.production_panel.title = "Tarım Üretimi"
            food_prod = gm.construction.get_food_production()
            season = gm.get_season()
            season_mod = {"Kış": 0.75, "İlkbahar": 1.2, "Yaz": 1.0, "Sonbahar": 1.5}.get(season, 1.0)
            actual = int(food_prod * season_mod)
            
            from game.systems.workers import TaskType
            farm_workers = gm.workers.get_workers_by_task(TaskType.FARMING)
            
            self.production_panel.add_item("Çalışan İşçi", str(farm_workers))
            self.production_panel.add_item("Temel Üretim", str(food_prod))
            self.production_panel.add_item("Mevsim", f"{season} (x{season_mod})")
            self.production_panel.add_item("Gerçek Üretim", f"{actual}/tur")
        
        elif self.building_type == BuildingType.MINE:
            # Maden - Demir üretimi
            self.production_panel.title = "Maden Üretimi"
            iron_prod = gm.construction.get_iron_production()
            
            from game.systems.workers import TaskType
            mine_workers = gm.workers.get_workers_by_task(TaskType.MINING)
            
            self.production_panel.add_item("Çalışan İşçi", str(mine_workers))
            self.production_panel.add_item("Demir Üretimi", f"{iron_prod}/tur")
            self.production_panel.add_item("Mevcut Demir", str(gm.economy.resources.iron))
        
        elif self.building_type == BuildingType.CARAVANSERAI:
            # Kervansaray - Ticaret bilgisi
            self.production_panel.title = "Kervan Ticareti"
            if hasattr(gm, 'trade'):
                from game.systems.trade import CaravanStatus
                active = len(gm.trade.active_caravans)
                completed = gm.trade.caravans_completed
                lost = gm.trade.caravans_lost
                total_income = gm.trade.total_trade_income
                self.production_panel.add_item("Aktif Kervanlar", str(active))
                self.production_panel.add_item("Tamamlanan", str(completed))
                self.production_panel.add_item("Kayıp", str(lost))
                self.production_panel.add_item("Toplam Gelir", f"{total_income} altın")
        
        else:
            # Varsayılan - Genel bilgi
            self.production_panel.title = "Durum"
            self.production_panel.add_item("Bu bina için", "")
            self.production_panel.add_item("özel üretim yok", "")
    
    def _setup_action_menu(self):
        """Eylem menüsünü ayarla"""
        self.action_menu.clear()
        gm = self.screen_manager.game_manager
        if not gm or not self.building_type:
            return
        
        stats = BUILDING_DEFINITIONS[self.building_type]
        
        # Yükseltme seçeneği
        if self.building_level < stats.max_level:
            next_level = self.building_level + 1
            multiplier = next_level
            cost_gold = int(stats.cost_gold * multiplier * 0.5)
            cost_wood = int(stats.cost_wood * multiplier * 0.5)
            cost_iron = int(stats.cost_iron * multiplier * 0.5)
            
            self.action_menu.add_item(
                f"Seviye {next_level}'e Yükselt ({cost_gold} altın, {cost_wood} kereste)",
                self._upgrade_building
            )
        else:
            self.action_menu.add_item("Maksimum seviyeye ulaşıldı", None)
        
        # Binaya özel eylemler
        if self.building_type == BuildingType.ARTILLERY_FOUNDRY:
            self.action_menu.add_item("", None)  # Ayırıcı
            self._add_artillery_actions()
        
        elif self.building_type == BuildingType.SHIPYARD:
            self.action_menu.add_item("", None)
            self._add_shipyard_actions()
        
        elif self.building_type == BuildingType.BARRACKS:
            self.action_menu.add_item("", None)
            self._add_barracks_actions()
        
        elif self.building_type == BuildingType.FARM:
            self.action_menu.add_item("", None)
            self._add_farm_actions()
        
        elif self.building_type == BuildingType.CARAVANSERAI:
            self.action_menu.add_item("", None)
            self._add_caravan_actions()
        
        elif self.building_type == BuildingType.MINE:
            self.action_menu.add_item("", None)
            self._add_mine_actions()
        
        # F1 bilgi
        self.action_menu.add_item("", None)
        self.action_menu.add_item("F1: Binanın bonuslarını oku", None)
    
    def _add_artillery_actions(self):
        """Topçu Ocağı eylemleri"""
        gm = self.screen_manager.game_manager
        if not gm or not hasattr(gm, 'artillery'):
            return
        
        from game.systems.artillery import CannonType, CANNON_DEFINITIONS
        
        for ct in CannonType:
            cannon = CANNON_DEFINITIONS[ct]
            self.action_menu.add_item(
                f"Üret: {cannon.name} ({cannon.gold_cost} altın, {cannon.iron_cost} demir)",
                lambda c=ct: self._produce_cannon(c)
            )
    
    def _add_shipyard_actions(self):
        """Tersane eylemleri"""
        gm = self.screen_manager.game_manager
        if not gm or not hasattr(gm, 'naval'):
            return
        
        from game.systems.naval import ShipType, SHIP_DEFINITIONS
        
        for st in ShipType:
            ship = SHIP_DEFINITIONS[st]
            self.action_menu.add_item(
                f"İnşa: {ship.name} ({ship.gold_cost} altın, {ship.wood_cost} kereste)",
                lambda s=st: self._build_ship(s)
            )
    
    def _add_barracks_actions(self):
        """Kışla eylemleri"""
        gm = self.screen_manager.game_manager
        if not gm:
            return
        
        from game.systems.military import UnitType, UNIT_DEFINITIONS
        
        for ut in UnitType:
            unit = UNIT_DEFINITIONS[ut]
            self.action_menu.add_item(
                f"Eğit: 10 {unit.name_tr} ({unit.cost_gold * 10} altın)",
                lambda u=ut: self._train_unit(u)
            )
    
    def _upgrade_building(self):
        """Binayı yükselt"""
        gm = self.screen_manager.game_manager
        if not gm or not self.building_type:
            return
        
        # Kıyı kontrolü (Tersane için)
        is_coastal = gm.province.is_coastal
        
        if gm.construction.start_upgrade(self.building_type, gm.economy):
            self.building_level += 1
            self._update_panels()
            self._setup_action_menu()
    
    def _produce_cannon(self, cannon_type):
        """Top üret"""
        gm = self.screen_manager.game_manager
        if not gm or not hasattr(gm, 'artillery'):
            return
        
        gm.artillery.start_production(cannon_type, gm.economy)
        self._update_panels()
    
    def _build_ship(self, ship_type):
        """Gemi inşa et"""
        gm = self.screen_manager.game_manager
        if not gm or not hasattr(gm, 'naval'):
            return
        
        gm.naval.start_construction(ship_type, gm.economy)
        self._update_panels()
    
    def _train_unit(self, unit_type):
        """Asker eğit"""
        gm = self.screen_manager.game_manager
        if not gm:
            return
        
        # MilitarySystem.recruit(unit_type, count, economy) kullanılır
        gm.military.recruit(unit_type, 10, gm.economy)
        self._update_panels()
    
    def _add_farm_actions(self):
        """Çiftlik eylemleri - işçi yönetimi"""
        gm = self.screen_manager.game_manager
        if not gm:
            return
        
        from game.systems.workers import TaskType
        
        # Mevcut işçi durumu
        farm_workers = gm.workers.get_workers_by_task(TaskType.FARMING)
        idle_workers = gm.workers.get_idle_count()
        
        self.action_menu.add_item(
            f"Çiftliğe işçi ata ({idle_workers} boşta)",
            self._assign_farm_workers
        )
        self.action_menu.add_item(
            f"Çiftlikten işçi çek ({farm_workers} çalışıyor)",
            self._remove_farm_workers
        )
    
    def _add_caravan_actions(self):
        """Kervansaray eylemleri - kervan gönderme"""
        gm = self.screen_manager.game_manager
        if not gm or not hasattr(gm, 'trade'):
            return
        
        from game.systems.trade import RouteType
        
        # Mevcut yolları listele
        available_routes = gm.trade.get_available_routes()
        for route in available_routes:
            cost = int(route.base_income * 0.3)
            self.action_menu.add_item(
                f"Kervan gönder: {route.name} ({cost} altın)",
                lambda r=route.route_id: self._send_caravan(r)
            )
    
    def _add_mine_actions(self):
        """Maden eylemleri - üretim artırma"""
        gm = self.screen_manager.game_manager
        if not gm:
            return
        
        from game.systems.workers import TaskType
        
        # Mevcut işçi durumu
        mine_workers = gm.workers.get_workers_by_task(TaskType.MINING)
        idle_workers = gm.workers.get_idle_count()
        
        self.action_menu.add_item(
            f"Madene işçi ata ({idle_workers} boşta)",
            self._assign_mine_workers
        )
        self.action_menu.add_item(
            f"Madenden işçi çek ({mine_workers} çalışıyor)",
            self._remove_mine_workers
        )
    
    def _assign_farm_workers(self):
        """Çiftliğe işçi ata"""
        gm = self.screen_manager.game_manager
        if not gm:
            return
        
        from game.systems.workers import TaskType
        
        assigned = gm.workers.assign_idle_to_task(TaskType.FARMING, 1)
        if assigned > 0:
            self.audio.speak(f"{assigned} işçi çiftliğe atandı.", interrupt=True)
        else:
            self.audio.speak("Boşta işçi yok.", interrupt=True)
        self._update_panels()
        self._setup_action_menu()
    
    def _remove_farm_workers(self):
        """Çiftlikten işçi çek"""
        gm = self.screen_manager.game_manager
        if not gm:
            return
        
        from game.systems.workers import TaskType
        
        removed = gm.workers.remove_from_task(TaskType.FARMING, 1)
        if removed > 0:
            self.audio.speak(f"{removed} işçi çiftlikten çekildi.", interrupt=True)
        else:
            self.audio.speak("Çiftlikte çalışan işçi yok.", interrupt=True)
        self._update_panels()
        self._setup_action_menu()
    
    def _assign_mine_workers(self):
        """Madene işçi ata"""
        gm = self.screen_manager.game_manager
        if not gm:
            return
        
        from game.systems.workers import TaskType
        
        assigned = gm.workers.assign_idle_to_task(TaskType.MINING, 1)
        if assigned > 0:
            self.audio.speak(f"{assigned} işçi madene atandı.", interrupt=True)
        else:
            self.audio.speak("Boşta işçi yok.", interrupt=True)
        self._update_panels()
        self._setup_action_menu()
    
    def _remove_mine_workers(self):
        """Madenden işçi çek"""
        gm = self.screen_manager.game_manager
        if not gm:
            return
        
        from game.systems.workers import TaskType
        
        removed = gm.workers.remove_from_task(TaskType.MINING, 1)
        if removed > 0:
            self.audio.speak(f"{removed} işçi madenden çekildi.", interrupt=True)
        else:
            self.audio.speak("Madende çalışan işçi yok.", interrupt=True)
        self._update_panels()
        self._setup_action_menu()
    
    def _send_caravan(self, route_id: str):
        """Kervan gönder"""
        gm = self.screen_manager.game_manager
        if not gm or not hasattr(gm, 'trade'):
            return
        
        gm.trade.send_caravan(route_id, gm.economy)
        self._update_panels()
    
    def handle_event(self, event) -> bool:
        if self.action_menu.handle_event(event):
            return True
        
        if self.back_button.handle_event(event):
            return True
        
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_BACKSPACE, pygame.K_ESCAPE):
                self._go_back()
                return True
            
            if event.key == pygame.K_F1:
                self._announce_building_info()
                return True
            
            if event.key == pygame.K_TAB:
                self._announce_next_panel()
                return True
        
        return False
    
    def _announce_building_info(self):
        """Bina bilgisini sesli oku"""
        if not self.building_type:
            return
        
        stats = BUILDING_DEFINITIONS[self.building_type]
        
        parts = [f"{stats.name_tr}, Seviye {self.building_level}."]
        parts.append(stats.description)
        
        if stats.happiness_bonus > 0:
            bonus = int(stats.happiness_bonus * (1 + (self.building_level - 1) * 0.5))
            parts.append(f"Mutluluk bonusu: artı {bonus}.")
        if stats.trade_bonus > 0:
            bonus = int(stats.trade_bonus * (1 + (self.building_level - 1) * 0.5))
            parts.append(f"Ticaret bonusu: artı {bonus}.")
        if stats.military_bonus > 0:
            bonus = int(stats.military_bonus * (1 + (self.building_level - 1) * 0.5))
            parts.append(f"Askeri bonus: artı {bonus}.")
        if stats.food_production > 0:
            prod = int(stats.food_production * (1 + (self.building_level - 1) * 0.5))
            parts.append(f"Yiyecek üretimi: {prod} birim.")
        
        self.audio.speak(" ".join(parts), interrupt=True)
    
    def _announce_next_panel(self):
        """Sıradaki paneli duyur"""
        if not hasattr(self, '_current_panel'):
            self._current_panel = 0
        
        panels = [self.info_panel, self.production_panel]
        self._current_panel = (self._current_panel + 1) % len(panels)
        panels[self._current_panel].announce_content()
    
    def update(self, dt: float):
        self._update_panels()
    
    def draw(self, surface: pygame.Surface):
        # Başlık
        header_font = self.get_header_font()
        if self.building_type:
            stats = BUILDING_DEFINITIONS[self.building_type]
            title = f"🏛️ {stats.name_tr.upper()} - SEVİYE {self.building_level}"
        else:
            title = "🏛️ BİNA"
        
        title_render = header_font.render(title, True, COLORS['gold'])
        surface.blit(title_render, (20, 30))
        
        # Paneller
        self.info_panel.draw(surface)
        self.production_panel.draw(surface)
        
        # Eylem menüsü
        self.action_menu.draw(surface)
        
        # Geri butonu
        self.back_button.draw(surface)
    
    def _go_back(self):
        self.screen_manager.change_screen(ScreenType.CONSTRUCTION)
