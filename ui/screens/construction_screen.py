# -*- coding: utf-8 -*-
"""
Osmanlı Eyalet Yönetim Simülasyonu - İnşaat Ekranı
"""

import pygame
from ui.screen_manager import BaseScreen, ScreenType
from ui.components import Button, Panel, MenuList
from game.systems.construction import BuildingType, BuildingCategory, BUILDING_DEFINITIONS
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
        
        con = gm.construction
        
        # Kategori başlıklarıyla inşa edilebilir binaları grupla
        available = con.get_available_buildings()
        
        # Kategori sırası
        category_order = [
            BuildingCategory.DINI,
            BuildingCategory.ASKERI,
            BuildingCategory.EKONOMI,
            BuildingCategory.ALTYAPI,
            BuildingCategory.SOSYAL
        ]
        category_labels = {
            BuildingCategory.DINI: "═══ Dinî Yapılar ═══",
            BuildingCategory.ASKERI: "═══ Askerî Yapılar ═══",
            BuildingCategory.EKONOMI: "═══ Ekonomik Yapılar ═══",
            BuildingCategory.ALTYAPI: "═══ Altyapı Yapıları ═══",
            BuildingCategory.SOSYAL: "═══ Sosyal Yapılar ═══"
        }
        
        # Inşa edilebilir binaları kategorilere göre sırala
        for cat in category_order:
            cat_buildings = [bt for bt in available if BUILDING_DEFINITIONS[bt].category == cat]
            if not cat_buildings:
                continue
            
            for building_type in cat_buildings:
                stats = BUILDING_DEFINITIONS[building_type]
                # Ön koşul durumunu kontrol et
                prereq_met, _ = con.check_prerequisite(building_type)
                prereq_marker = "" if prereq_met else "🔒 "
                self.build_menu.add_item(
                    f"İnşa: {prereq_marker}{stats.name_tr}",
                    lambda bt=building_type: self._build(bt)
                )
        
        # Yükseltilebilir binalar
        for building_type, building in con.buildings.items():
            stats = building.get_stats()
            level_name = building.get_level_name()
            if building.level < stats.max_level:
                # Sinerji göstergesi
                synergy_mult = con.get_synergy_multiplier(building_type)
                synergy_text = f" ✨+%{int((synergy_mult-1.0)*100)}" if synergy_mult > 1.0 else ""
                self.build_menu.add_item(
                    f"Yükselt: {stats.name_tr} ({level_name}){synergy_text}",
                    lambda bt=building_type: self._upgrade(bt)
                )
            else:
                self.build_menu.add_item(
                    f"Gir: {stats.name_tr} ({level_name} - MAX)",
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
                level_name = building.get_level_name()
                
                # Sinerji göstergesi
                synergy_mult = con.get_synergy_multiplier(building_type)
                synergy_text = f" ✨%{int((synergy_mult-1.0)*100)}" if synergy_mult > 1.0 else ""
                
                self.buildings_panel.add_item(
                    f"{stats.name_tr} ({level_name}){synergy_text}",
                    f"Bakım: {stats.maintenance * building.level}"
                )
            self.buildings_panel.add_item("", "")
            self.buildings_panel.add_item(
                "Toplam Bakım",
                str(con.get_total_maintenance())
            )
            # Bina gelir özeti
            gold_per_turn = con.get_gold_per_turn()
            if gold_per_turn > 0:
                self.buildings_panel.add_item(
                    "Bina Geliri",
                    f"+{gold_per_turn} altın/tur"
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
            
            # H - Tarihi bilgi
            if event.key == pygame.K_h:
                self._announce_historical_info()
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
            self._announce_building_details(building_type, stats, 0, gm.construction)
        elif idx < len(available) + len(upgradable):
            # Yükseltme
            bt, building = upgradable[idx - len(available)]
            stats = building.get_stats()
            self._announce_building_details(bt, stats, building.level, gm.construction)
    
    def _announce_building_details(self, building_type, stats, current_level: int, con=None):
        """Bina detaylarını duyur - gelişmiş bilgilerle"""
        self.audio.speak(f"{stats.name_tr} Bilgileri:", interrupt=True)
        self.audio.speak(stats.description, interrupt=False)
        
        # Kategori
        cat_names = {
            BuildingCategory.DINI: "Dinî",
            BuildingCategory.ASKERI: "Askerî",
            BuildingCategory.EKONOMI: "Ekonomik",
            BuildingCategory.ALTYAPI: "Altyapı",
            BuildingCategory.SOSYAL: "Sosyal"
        }
        self.audio.speak(f"Kategori: {cat_names.get(stats.category, 'Bilinmiyor')}", interrupt=False)
        
        if current_level == 0:
            # Yeni inşaat
            self.audio.speak(f"İnşaat maliyeti: {stats.cost_gold} altın, {stats.cost_wood} kereste, {stats.cost_iron} demir", interrupt=False)
            self.audio.speak(f"İnşaat süresi: {stats.build_time} tur", interrupt=False)
            self.audio.speak(f"Bakım maliyeti: {stats.maintenance} altın her tur", interrupt=False)
            
            # Ön koşul bildirimi
            if stats.prerequisite:
                try:
                    prereq_type = BuildingType(stats.prerequisite)
                    prereq_stats = BUILDING_DEFINITIONS[prereq_type]
                    if con and prereq_type in con.buildings:
                        self.audio.speak(f"Ön koşul: {prereq_stats.name_tr} ✅ (mevcut)", interrupt=False)
                    else:
                        self.audio.speak(f"Ön koşul: {prereq_stats.name_tr} ❗ (önce inşa edilmeli)", interrupt=False)
                except ValueError:
                    pass
        else:
            # Yükseltme - seviye ismiyle
            if stats.level_names and current_level <= len(stats.level_names):
                self.audio.speak(f"Mevcut: {stats.level_names[current_level - 1]}", interrupt=False)
                if current_level < len(stats.level_names):
                    self.audio.speak(f"Sonraki: {stats.level_names[current_level]}", interrupt=False)
            else:
                self.audio.speak(f"Mevcut seviye: {current_level}", interrupt=False)
            
            multiplier = current_level + 1
            upgrade_gold = int(stats.cost_gold * multiplier * 0.5)
            upgrade_wood = int(stats.cost_wood * multiplier * 0.5)
            upgrade_iron = int(stats.cost_iron * multiplier * 0.5)
            self.audio.speak(f"Yükseltme maliyeti: {upgrade_gold} altın, {upgrade_wood} kereste, {upgrade_iron} demir", interrupt=False)
        
        # Sinerji bilgisi
        if stats.synergy_bonus_desc:
            self.audio.speak(f"Sinerji: {stats.synergy_bonus_desc}", interrupt=False)
        
        if con:
            synergy_info = con.get_synergy_info(building_type)
            # Basitleştirilmiş sinerji durumu
            for name, has_it in synergy_info:
                marker = "✅" if has_it else "❌"
                self.audio.speak(f"  {marker} {name}", interrupt=False)
        
        # Seviye bonusları (seviye isimleriyle)
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
                level_label = stats.level_names[level-1] if stats.level_names and level <= len(stats.level_names) else f"Lv{level}"
                self.audio.speak(f"{level_label}: {', '.join(bonuses)}", interrupt=False)
        
        # Özel etkiler
        if stats.unique_effects:
            self.audio.speak("Özel etkiler:", interrupt=False)
            effect_names = {
                'piety': 'Dindarlık',
                'legitimacy': 'Meşruiyet',
                'education': 'Eğitim',
                'health': 'Sağlık',
                'defense': 'Savunma',
                'siege_power': 'Kuşatma Gücü',
                'gold_per_turn': 'Altın/Tur',
                'espionage_defense': 'Casusluk Savunması',
                'train_speed': 'Eğitim Hızı',
                'morale': 'Moral',
                'plague_resistance': 'Veba Direnci',
                'science': 'Bilim'
            }
            for key, value in stats.unique_effects.items():
                label = effect_names.get(key, key.replace('_', ' ').title())
                self.audio.speak(f"  {label}: +{value}", interrupt=False)
    
    def _announce_all_building_costs(self):
        """Tüm binaların maliyet listesi"""
        self.audio.speak("Tüm bina maliyetleri:", interrupt=True)
        for bt in BuildingType:
            stats = BUILDING_DEFINITIONS[bt]
            self.audio.speak(f"{stats.name_tr}: {stats.cost_gold} altın", interrupt=False)
    
    def _announce_historical_info(self):
        """Seçili binanın tarihi bilgisini duyur"""
        if self.build_menu.selected_index < 0:
            self.audio.speak("Önce bir bina seçin.", interrupt=True)
            return
        
        gm = self.screen_manager.game_manager
        if not gm:
            return
        
        # Seçili öğeden bina tipini çıkar
        selected_text = self.build_menu.items[self.build_menu.selected_index][0]
        
        building_type = None
        for bt in BuildingType:
            stats = BUILDING_DEFINITIONS[bt]
            if stats.name_tr in selected_text:
                building_type = bt
                break
        
        if not building_type:
            self.audio.speak("Bina bulunamadı.", interrupt=True)
            return
        
        stats = BUILDING_DEFINITIONS[building_type]
        
        if stats.historical_desc:
            self.audio.speak(f"{stats.name_tr} - Tarihi Bilgi:", interrupt=True)
            self.audio.speak(stats.historical_desc, interrupt=False)
        else:
            self.audio.speak(f"{stats.name_tr} için tarihi bilgi bulunmuyor.", interrupt=True)
    
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
        
        # Bilgi kutusu - genişletilmiş
        rect = pygame.Rect(20, 500, 850, 140)
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
        con = gm.construction
        
        font = pygame.font.Font(None, FONTS['body'])
        small_font = pygame.font.Font(None, FONTS['small'])
        
        # Kategori ve bina adı
        cat_names = {
            BuildingCategory.DINI: "🕌",
            BuildingCategory.ASKERI: "⚔️",
            BuildingCategory.EKONOMI: "💰",
            BuildingCategory.ALTYAPI: "🏛️",
            BuildingCategory.SOSYAL: "🏥"
        }
        cat_icon = cat_names.get(stats.category, "🏠")
        name = font.render(f"{cat_icon} {stats.name_tr}: {stats.description}", True, COLORS['gold'])
        surface.blit(name, (rect.x + 20, rect.y + 10))
        
        # Maliyet
        cost_text = f"Maliyet: {stats.cost_gold} Altın, {stats.cost_wood} Kereste, {stats.cost_iron} Demir"
        cost = small_font.render(cost_text, True, COLORS['text'])
        surface.blit(cost, (rect.x + 20, rect.y + 35))
        
        # Ön koşul ve sinerji satırı
        info_parts = []
        if stats.prerequisite:
            try:
                prereq_type = BuildingType(stats.prerequisite)
                prereq_stats = BUILDING_DEFINITIONS[prereq_type]
                prereq_met = prereq_type in con.buildings
                marker = "✅" if prereq_met else "❌"
                info_parts.append(f"Ön koşul: {marker}{prereq_stats.name_tr}")
            except ValueError:
                pass
        
        synergy_mult = con.get_synergy_multiplier(building_type)
        if synergy_mult > 1.0:
            info_parts.append(f"Sinerji: +%{int((synergy_mult-1.0)*100)}")
        
        if info_parts:
            info = small_font.render(" | ".join(info_parts), True, COLORS['text'])
            surface.blit(info, (rect.x + 20, rect.y + 55))
        
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
        # Özel etkilerden birkaçını göster
        if stats.unique_effects:
            for key, value in list(stats.unique_effects.items())[:3]:
                label = key.replace('_', ' ').title()
                effects.append(f"{label} +{value}")
        
        effect_text = " | ".join(effects) if effects else "Özel etki yok"
        effect = small_font.render(
            f"Süre: {stats.build_time} tur | {effect_text}",
            True, COLORS['text']
        )
        surface.blit(effect, (rect.x + 20, rect.y + 75))
        
        # Seviye isimleri
        if stats.level_names:
            names_text = " → ".join(stats.level_names)
            names = small_font.render(f"Seviyeler: {names_text}", True, COLORS.get('text_secondary', COLORS['text']))
            surface.blit(names, (rect.x + 20, rect.y + 95))
        
        # Kısayollar
        keys = small_font.render("B: Detay | H: Tarih | Tab: Yükseltme | I: Tüm binalar", True, COLORS.get('text_dim', (150,150,150)))
        surface.blit(keys, (rect.x + 20, rect.y + 115))
    
    def _build(self, building_type: BuildingType):
        """Bina inşa et"""
        gm = self.screen_manager.game_manager
        if gm:
            is_coastal = gm.province.is_coastal
            success = gm.construction.start_construction(building_type, gm.economy, is_coastal)
            if success:
                self.audio.play_game_sound('construction', 'hammer')
                self._update_panels()
                self._setup_build_menu()
    
    def _upgrade(self, building_type: BuildingType):
        """Bina yükselt"""
        gm = self.screen_manager.game_manager
        if gm:
            success = gm.construction.start_upgrade(building_type, gm.economy)
            if success:
                self.audio.play_game_sound('construction', 'upgrade')
                self._update_panels()
                self._setup_build_menu()
    
    def _go_back(self):
        """Geri dön"""
        if getattr(self.screen_manager, 'is_multiplayer_mode', False):
            self.screen_manager.change_screen(ScreenType.MULTIPLAYER_GAME)
        else:
            self.screen_manager.change_screen(ScreenType.PROVINCE_VIEW)
