# -*- coding: utf-8 -*-
"""
Osmanlı Eyalet Yönetim Simülasyonu - İnşaat Ekranı
"""

import pygame
from ui.screen_manager import BaseScreen, ScreenType
from ui.components import Button, Panel, MenuList
from game.systems.construction import BuildingType, BUILDING_DEFINITIONS
from config import COLORS, FONTS, SCREEN_WIDTH, SCREEN_HEIGHT


class ConstructionScreen(BaseScreen):
    """İnşaat yönetim ekranı"""
    
    def __init__(self, screen_manager):
        super().__init__(screen_manager)
        
        # Paneller
        self.buildings_panel = Panel(20, 80, 450, 400, "Mevcut Binalar")
        self.queue_panel = Panel(490, 80, 380, 180, "İnşaat Kuyruğu")
        
        # İnşaat menüsü
        self.build_menu = MenuList(
            x=490,
            y=300,
            width=380,
            item_height=40
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
    
    def on_enter(self):
        self._update_panels()
        self._setup_build_menu()
    
    def announce_screen(self):
        self.audio.announce_screen_change("İnşaat Yönetimi")
        gm = self.screen_manager.game_manager
        if gm:
            gm.construction.announce_buildings()
    
    def _setup_build_menu(self):
        """İnşaat menüsünü ayarla"""
        self.build_menu.clear()
        gm = self.screen_manager.game_manager
        if not gm:
            return
        
        # İnşa edilebilir binalar
        available = gm.construction.get_available_buildings()
        for building_type in available:
            stats = BUILDING_DEFINITIONS[building_type]
            self.build_menu.add_item(
                f"İnşa: {stats.name_tr}",
                lambda bt=building_type: self._build(bt)
            )
        
        # Yükseltilebilir binalar
        for building_type, building in gm.construction.buildings.items():
            stats = building.get_stats()
            if building.level < stats.max_level:
                self.build_menu.add_item(
                    f"Yükselt: {stats.name_tr} (Lv.{building.level})",
                    lambda bt=building_type: self._upgrade(bt)
                )
            else:
                # Max seviye binalar - sadece içine girilebilir
                self.build_menu.add_item(
                    f"Gir: {stats.name_tr} (Lv.MAX)",
                    lambda bt=building_type: self._open_building_interior(bt)
                )
    
    def _update_panels(self):
        """Panelleri güncelle"""
        gm = self.screen_manager.game_manager
        if not gm:
            return
        
        con = gm.construction
        
        # Binalar paneli
        self.buildings_panel.clear()
        if con.buildings:
            for building_type, building in con.buildings.items():
                stats = building.get_stats()
                self.buildings_panel.add_item(
                    f"{stats.name_tr} Lv.{building.level}",
                    f"Bakım: {stats.maintenance * building.level}"
                )
            self.buildings_panel.add_item("", "")
            self.buildings_panel.add_item(
                "Toplam Bakım",
                str(con.get_total_maintenance())
            )
        else:
            self.buildings_panel.add_item("Bina yok", "")
        
        # Kuyruk paneli
        self.queue_panel.clear()
        if con.construction_queue:
            for item in con.construction_queue:
                stats = BUILDING_DEFINITIONS[item.building_type]
                action = "⬆" if item.is_upgrade else "🔨"
                self.queue_panel.add_item(
                    f"{action} {stats.name_tr}",
                    f"{item.turns_remaining} tur"
                )
        else:
            self.queue_panel.add_item("İnşaat yok", "")
    
    def handle_event(self, event) -> bool:
        # Enter tuşunu önce kontrol et - mevcut binaysa içine gir
        if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
            if self._try_enter_building():
                return True
            # Mevcut bina değilse, menünün inşa/yükseltme işlemini yapmasına izin ver
        
        if self.build_menu.handle_event(event):
            return True
        
        if self.back_button.handle_event(event):
            return True
        
        if event.type == pygame.KEYDOWN:
            # Backspace veya Escape - Geri dön
            if event.key in (pygame.K_BACKSPACE, pygame.K_ESCAPE):
                self._go_back()
                return True
            
            # F1 - Özet
            if event.key == pygame.K_F1:
                gm = self.screen_manager.game_manager
                if gm:
                    gm.construction.announce_buildings()
                return True
            
            # B - Seçili binanın maliyet önizlemesi
            if event.key == pygame.K_b:
                self._announce_selected_building_cost()
                return True
            
            # I - Tüm binaların maliyet listesi
            if event.key == pygame.K_i:
                self._announce_all_building_costs()
                return True
            
            # Tab - Seçili binanın yükseltme maliyetini duyur
            if event.key == pygame.K_TAB:
                self._announce_upgrade_cost()
                return True
        
        return False
    
    def _try_enter_building(self) -> bool:
        """Mevcut binaya girmeyi dene, başarılıysa True döndür"""
        gm = self.screen_manager.game_manager
        if not gm:
            return False
        
        available = gm.construction.get_available_buildings()
        # Tüm mevcut binalar - hem yükseltilebilir hem max seviye
        existing_buildings = list(gm.construction.buildings.items())
        
        idx = self.build_menu.selected_index
        
        if idx < 0:
            return False
        
        # Mevcut bina listesindeyse (available sonrası)
        building_idx = idx - len(available)
        if building_idx >= 0 and building_idx < len(existing_buildings):
            building_type, building = existing_buildings[building_idx]
            self._open_building_interior(building_type, building.level)
            return True
        
        # Yeni bina inşaatı - Enter ile inşa etmeli (False döndür, menü halletsin)
        return False
    
    def _announce_upgrade_cost(self):
        """Seçili binanın yükseltme maliyetini duyur"""
        gm = self.screen_manager.game_manager
        if not gm:
            return
        
        # Mevcut binalar listesi
        existing_buildings = list(gm.construction.buildings.keys())
        
        if self.build_menu.selected_index < 0:
            self.audio.speak("Önce bir bina seçin.", interrupt=True)
            return
        
        # Menüdeki seçili öğeyi bul
        available = gm.construction.get_available_buildings()
        upgradable = [(bt, b) for bt, b in gm.construction.buildings.items() 
                      if b.level < b.get_stats().max_level]
        
        idx = self.build_menu.selected_index
        
        if idx < len(available):
            # Yeni bina inşaatı
            building_type = available[idx]
            stats = BUILDING_DEFINITIONS[building_type]
            self.audio.speak(
                f"{stats.name_tr} henüz inşa edilmemiş. "
                f"İnşaat maliyeti: {stats.cost_gold} altın, {stats.cost_wood} kereste, {stats.cost_iron} demir.",
                interrupt=True
            )
        elif idx < len(available) + len(upgradable):
            # Yükseltme
            building_type, building = upgradable[idx - len(available)]
            stats = BUILDING_DEFINITIONS[building_type]
            next_level = building.level + 1
            cost_mult = next_level * 0.5
            cost_gold = int(stats.cost_gold * cost_mult)
            cost_wood = int(stats.cost_wood * cost_mult)
            cost_iron = int(stats.cost_iron * cost_mult)
            
            self.audio.speak(
                f"{stats.name_tr} Seviye {next_level}'e yükseltme: "
                f"{cost_gold} altın, {cost_wood} kereste, {cost_iron} demir.",
                interrupt=True
            )
        else:
            self.audio.speak("Bu öğe için yükseltme bilgisi yok.", interrupt=True)
    
    def _enter_building(self):
        """Mevcut binaya gir - iç ekranı aç"""
        gm = self.screen_manager.game_manager
        if not gm:
            return
        
        available = gm.construction.get_available_buildings()
        upgradable = [(bt, b) for bt, b in gm.construction.buildings.items() 
                      if b.level < b.get_stats().max_level]
        
        idx = self.build_menu.selected_index
        
        if idx < 0:
            self.audio.speak("Önce bir bina seçin.", interrupt=True)
            return
        
        # Mevcut bina mı kontrol et
        if idx >= len(available) and idx < len(available) + len(upgradable):
            building_type, building = upgradable[idx - len(available)]
            self._open_building_interior(building_type, building.level)
        elif idx < len(available):
            self.audio.speak("Bu bina henüz inşa edilmemiş. Girmek için önce inşa edin.", interrupt=True)
        else:
            # Mevcut binaları kontrol et
            all_buildings = list(gm.construction.buildings.items())
            building_idx = idx - len(available) - len(upgradable)
            if building_idx >= 0 and building_idx < len(all_buildings):
                building_type, building = all_buildings[building_idx]
                self._open_building_interior(building_type, building.level)
            else:
                self.audio.speak("Bu öğede bir bina yok.", interrupt=True)
    
    def _open_building_interior(self, building_type, level):
        """Bina iç ekranını aç"""
        interior_screen = self.screen_manager.screens.get(ScreenType.BUILDING_INTERIOR)
        if interior_screen:
            interior_screen.set_building(building_type, level)
            self.screen_manager.change_screen(ScreenType.BUILDING_INTERIOR)
    
    def _announce_selected_building_cost(self):
        """Seçili binanın maliyet ve seviye bilgisini duyur"""
        if self.build_menu.selected_index < 0:
            self.audio.speak("Önce bir bina seçin.", interrupt=True)
            return
        
        gm = self.screen_manager.game_manager
        if not gm:
            return
        
        # Mevcut menü öğesini belirle
        available = gm.construction.get_available_buildings()
        upgradable = [(bt, b) for bt, b in gm.construction.buildings.items() 
                      if b.level < b.get_stats().max_level]
        
        idx = self.build_menu.selected_index
        
        if idx < len(available):
            # Yeni bina inşaatı
            building_type = available[idx]
            stats = BUILDING_DEFINITIONS[building_type]
            self._announce_building_details(stats, 0)
        elif idx < len(available) + len(upgradable):
            # Yükseltme
            bt, building = upgradable[idx - len(available)]
            stats = building.get_stats()
            self._announce_building_details(stats, building.level)
    
    def _announce_building_details(self, stats, current_level: int):
        """Bina detaylarını duyur"""
        self.audio.speak(f"{stats.name_tr} Bilgileri:", interrupt=True)
        self.audio.speak(stats.description, interrupt=False)
        
        if current_level == 0:
            # Yeni inşaat
            self.audio.speak(f"İnşaat maliyeti: {stats.cost_gold} altın, {stats.cost_wood} kereste, {stats.cost_iron} demir", interrupt=False)
            self.audio.speak(f"İnşaat süresi: {stats.build_time} tur", interrupt=False)
            self.audio.speak(f"Bakım maliyeti: {stats.maintenance} altın her tur", interrupt=False)
        else:
            # Yükseltme
            multiplier = current_level + 1
            upgrade_gold = int(stats.cost_gold * multiplier * 0.5)
            upgrade_wood = int(stats.cost_wood * multiplier * 0.5)
            upgrade_iron = int(stats.cost_iron * multiplier * 0.5)
            self.audio.speak(f"Mevcut seviye: {current_level}", interrupt=False)
            self.audio.speak(f"Yükseltme maliyeti: {upgrade_gold} altın, {upgrade_wood} kereste, {upgrade_iron} demir", interrupt=False)
        
        # Seviye bonusları
        self.audio.speak("Seviye bonusları:", interrupt=False)
        for level in range(1, min(6, stats.max_level + 1)):
            bonuses = []
            multiplier = 1 + (level - 1) * 0.5
            if stats.happiness_bonus > 0:
                bonuses.append(f"+{int(stats.happiness_bonus * multiplier)} mutluluk")
            if stats.trade_bonus > 0:
                bonuses.append(f"+{int(stats.trade_bonus * multiplier)} ticaret")
            if stats.military_bonus > 0:
                bonuses.append(f"+{int(stats.military_bonus * multiplier)} askeri")
            if stats.food_production > 0:
                bonuses.append(f"+{int(stats.food_production * multiplier)} yiyecek")
            
            if bonuses:
                self.audio.speak(f"Lv{level}: {', '.join(bonuses)}", interrupt=False)
    
    def _announce_all_building_costs(self):
        """Tüm binaların maliyet listesi"""
        self.audio.speak("Tüm bina maliyetleri:", interrupt=True)
        for bt in BuildingType:
            stats = BUILDING_DEFINITIONS[bt]
            self.audio.speak(f"{stats.name_tr}: {stats.cost_gold} altın", interrupt=False)
    
    def _announce_next_panel(self):
        """Sıradaki paneli duyur"""
        if not hasattr(self, '_current_panel'):
            self._current_panel = 0
        
        panels = [self.buildings_panel, self.queue_panel]
        self._current_panel = (self._current_panel + 1) % len(panels)
        panels[self._current_panel].announce_content()
    
    def update(self, dt: float):
        self._update_panels()
    
    def draw(self, surface: pygame.Surface):
        # Başlık
        header_font = self.get_header_font()
        title = header_font.render("🏗 İNŞAAT YÖNETİMİ", True, COLORS['gold'])
        surface.blit(title, (20, 20))
        
        # Paneller
        self.buildings_panel.draw(surface)
        self.queue_panel.draw(surface)
        
        # İnşaat menüsü başlığı
        small_font = pygame.font.Font(None, FONTS['subheader'])
        build_title = small_font.render("İnşa / Yükselt", True, COLORS['gold'])
        surface.blit(build_title, (490, 275))
        self.build_menu.draw(surface)
        
        # Seçili bina bilgisi
        self._draw_building_info(surface)
        
        # Geri butonu
        self.back_button.draw(surface)
    
    def _draw_building_info(self, surface: pygame.Surface):
        """Seçili bina bilgilerini göster"""
        gm = self.screen_manager.game_manager
        if not gm or not self.build_menu.items:
            return
        
        # Bilgi kutusu
        rect = pygame.Rect(20, 500, 850, 100)
        pygame.draw.rect(surface, COLORS['panel_bg'], rect, border_radius=10)
        pygame.draw.rect(surface, COLORS['panel_border'], rect, width=2, border_radius=10)
        
        # Seçili öğeden bina tipini çıkar
        selected_text = self.build_menu.items[self.build_menu.selected_index][0]
        
        # Bina tipini bul
        building_type = None
        for bt in BuildingType:
            stats = BUILDING_DEFINITIONS[bt]
            if stats.name_tr in selected_text:
                building_type = bt
                break
        
        if not building_type:
            return
        
        stats = BUILDING_DEFINITIONS[building_type]
        
        font = pygame.font.Font(None, FONTS['body'])
        small_font = pygame.font.Font(None, FONTS['small'])
        
        # Bina adı ve açıklama
        name = font.render(f"{stats.name_tr}: {stats.description}", True, COLORS['gold'])
        surface.blit(name, (rect.x + 20, rect.y + 15))
        
        # Maliyet
        cost_text = f"Maliyet: {stats.cost_gold} Altın, {stats.cost_wood} Kereste, {stats.cost_iron} Demir"
        cost = small_font.render(cost_text, True, COLORS['text'])
        surface.blit(cost, (rect.x + 20, rect.y + 45))
        
        # Etkiler ve süre
        effects = []
        if stats.happiness_bonus > 0:
            effects.append(f"Mutluluk +{stats.happiness_bonus}")
        if stats.trade_bonus > 0:
            effects.append(f"Ticaret +{stats.trade_bonus}")
        if stats.military_bonus > 0:
            effects.append(f"Askeri +{stats.military_bonus}")
        if stats.food_production > 0:
            effects.append(f"Yiyecek +{stats.food_production}")
        
        effect_text = " | ".join(effects) if effects else "Özel etki yok"
        effect = small_font.render(
            f"Süre: {stats.build_time} tur | Etki: {effect_text}",
            True, COLORS['text']
        )
        surface.blit(effect, (rect.x + 20, rect.y + 70))
    
    def _build(self, building_type: BuildingType):
        """Bina inşa et"""
        gm = self.screen_manager.game_manager
        if gm:
            is_coastal = gm.province.is_coastal
            success = gm.construction.start_construction(building_type, gm.economy, is_coastal)
            if success:
                self._update_panels()
                self._setup_build_menu()
    
    def _upgrade(self, building_type: BuildingType):
        """Bina yükselt"""
        gm = self.screen_manager.game_manager
        if gm:
            success = gm.construction.start_upgrade(building_type, gm.economy)
            if success:
                self._update_panels()
                self._setup_build_menu()
    
    def _go_back(self):
        """Geri dön"""
        self.screen_manager.change_screen(ScreenType.PROVINCE_VIEW)
