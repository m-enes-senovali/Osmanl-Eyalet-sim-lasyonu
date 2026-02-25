# -*- coding: utf-8 -*-
"""
Osmanlı Eyalet Yönetim Simülasyonu - Topçu Ekranı (Geliştirilmiş)
Topçu Ocağı: 7 top türü, tunç/demir malzeme seçimi, tamir, envanter
"""

import pygame
from ui.screen_manager import BaseScreen, ScreenType
from ui.components import Button, Panel, MenuList
from config import COLORS, FONTS, SCREEN_WIDTH, SCREEN_HEIGHT, get_font
from game.systems.artillery import (
    CannonType, CannonMaterial, AmmoType, CANNON_DEFINITIONS, AMMO_MULTIPLIERS
)


class ArtilleryScreen(BaseScreen):
    """Topçu ekranı (Topçu Ocağı) — Geliştirilmiş"""
    
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
        self.menu_mode = "cannons"  # "cannons", "produce", "material"
        self._selected_cannon_type = None  # Malzeme seçimi için
    
    def get_header_font(self):
        if self._header_font is None:
            self._header_font = get_font(FONTS['header'])
        return self._header_font
    
    def on_enter(self):
        self._update_panels()
        self._setup_cannon_menu()
        self._setup_production_menu()
    
    def announce_screen(self):
        self.audio.announce_screen_change("Topçu Ocağı")
        gm = self.screen_manager.game_manager
        if gm and hasattr(gm, 'artillery'):
            gm.artillery.announce_artillery()
        self.audio.speak(
            "Enter ile seçin. "
            "M ile mühimmat değiştirin, I ile personel bilgisi. "
            "R ile tamir, F1 özet, F2 üretim menüsü.",
            interrupt=False
        )
    
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
            self.cannon_menu.add_item("TOP ÜRET (Tab veya Enter)", lambda: self._switch_to_produce())
            return
        
        for i, cannon in enumerate(artillery.cannons):
            definition = cannon.get_definition()
            
            # Durum göstergesi
            status_parts = []
            if cannon.condition < 100:
                status_parts.append(f"%{cannon.condition}")
            if cannon.damaged:
                status_parts.append("HASARLI")
            if cannon.material == "iron":
                status_parts.append("Demir")
            
            status_text = f" [{', '.join(status_parts)}]" if status_parts else ""
            
            self.cannon_menu.add_item(
                f"{cannon.name} - {definition.name}{status_text}",
                lambda idx=i: self._select_cannon(idx)
            )
        
        # Hasarlı top sayısı
        damaged = artillery.get_damaged_count()
        if damaged > 0:
            self.cannon_menu.add_item("", None)
            self.cannon_menu.add_item(
                f"TAMİR ET ({damaged} hasarlı top) [R]",
                lambda: self._repair_cannons()
            )
        
        # Ayırıcı ve üretim butonu
        self.cannon_menu.add_item("", None)
        self.cannon_menu.add_item("YENİ TOP ÜRET [F2]", lambda: self._switch_to_produce())
    
    def _setup_production_menu(self):
        """Üretim menüsünü oluştur — kategori bazlı alt menüler"""
        self.production_menu.clear()
        gm = self.screen_manager.game_manager
        if not gm:
            return
        
        # Geri butonu
        self.production_menu.add_item("<- Toplara Dön [Backspace]", lambda: self._switch_to_cannons())
        self.production_menu.add_item("", None)
        
        # Kategori seçimi
        self.production_menu.add_item(
            "SAHRA TOPLARI — Hafif ve hızlı, meydan savaşı için",
            lambda: self._show_category("sahra")
        )
        self.production_menu.add_item(
            "KUŞATMA TOPLARI — Ağır ve güçlü, sur yıkma için",
            lambda: self._show_category("kusatma")
        )
        self.production_menu.add_item(
            "DONANMA TOPLARI — Gemi savaşı için",
            lambda: self._show_category("donanma")
        )
    
    def _show_category(self, category: str):
        """Seçilen kategorinin toplarını göster"""
        self.menu_mode = "category"
        self._current_category = category
        self.production_menu.clear()
        
        gm = self.screen_manager.game_manager
        if not gm:
            return
        
        # Geri butonu
        self.production_menu.add_item("<- Kategorilere Dön [Backspace]", lambda: self._switch_to_produce())
        self.production_menu.add_item("", None)
        
        category_names = {
            "sahra": "SAHRA TOPLARI",
            "kusatma": "KUŞATMA TOPLARI",
            "donanma": "DONANMA TOPLARI"
        }
        
        category_cannons = {
            "sahra": [CannonType.ABUS, CannonType.DARBZEN, CannonType.KOLUNBURNA],
            "kusatma": [CannonType.HAVAN, CannonType.BALYEMEZ, CannonType.SAHI],
            "donanma": [CannonType.PRANGI],
        }
        
        cannons = category_cannons.get(category, [])
        for cannon_type in cannons:
            self._add_cannon_to_menu(cannon_type, gm)
        
        name = category_names.get(category, category)
        self.audio.speak(
            f"{name}. {len(cannons)} top türü mevcut. Enter ile seçin, Tab ile detay.",
            interrupt=True
        )
    
    def _add_cannon_to_menu(self, cannon_type: CannonType, gm):
        """Tek top türünü menüye ekle"""
        definition = CANNON_DEFINITIONS[cannon_type]
        
        # Temel maliyet (bronz varsayılan)
        cost = definition.get_cost(CannonMaterial.BRONZE)
        cost_parts = [f"{cost['gold']} altın"]
        if cost.get('copper', 0) > 0:
            cost_parts.append(f"{cost['copper']} bakır")
        if cost.get('iron', 0) > 0:
            cost_parts.append(f"{cost['iron']} demir")
        cost_text = ", ".join(cost_parts)
        
        # Üretilebilir mi?
        can_produce = False
        if hasattr(gm, 'artillery'):
            can_produce, _ = gm.artillery.can_produce_cannon(
                cannon_type, gm.economy, CannonMaterial.BRONZE
            )
        
        prefix = "" if can_produce else "[X] "
        
        self.production_menu.add_item(
            f"{prefix}{definition.name} ({cost_text}) - {definition.build_time} gün",
            lambda ct=cannon_type: self._choose_material(ct)
        )
    
    def _choose_material(self, cannon_type: CannonType):
        """Malzeme seçim menüsünü göster"""
        definition = CANNON_DEFINITIONS[cannon_type]
        self._selected_cannon_type = cannon_type
        
        # Şahi sadece tunç
        if not definition.can_be_iron:
            self._start_production(cannon_type, CannonMaterial.BRONZE)
            return
        
        # Malzeme seçim menüsü
        self.menu_mode = "material"
        self.production_menu.clear()
        
        # Geri: mevcut kategoriye dön
        back_fn = lambda: self._show_category(self._current_category) if hasattr(self, '_current_category') else self._switch_to_produce()
        self.production_menu.add_item("<- Geri [Backspace]", back_fn)
        self.production_menu.add_item("", None)
        self.production_menu.add_item(f"─── {definition.name} MALZEME SEÇİMİ ───", None)
        self.production_menu.add_item("", None)
        
        # Tunç seçeneği
        bronze_cost = definition.get_cost(CannonMaterial.BRONZE)
        bronze_risk = definition.get_burst_risk(CannonMaterial.BRONZE)
        bronze_parts = [f"{bronze_cost['gold']} altın"]
        if bronze_cost.get('copper', 0) > 0:
            bronze_parts.append(f"{bronze_cost['copper']} bakır")
        self.production_menu.add_item(
            f"TUNÇ (Güvenilir, Patlama: %{bronze_risk}) - {', '.join(bronze_parts)}",
            lambda: self._start_production(cannon_type, CannonMaterial.BRONZE)
        )
        
        # Demir seçeneği  
        iron_cost = definition.get_cost(CannonMaterial.IRON)
        iron_risk = definition.get_burst_risk(CannonMaterial.IRON)
        iron_parts = [f"{iron_cost['gold']} altın", f"{iron_cost['iron']} demir"]
        iron_build = max(1, definition.build_time // 2)
        self.production_menu.add_item(
            f"DEMİR (Ucuz ama riskli, Patlama: %{iron_risk}) - {', '.join(iron_parts)} - {iron_build} gün",
            lambda: self._start_production(cannon_type, CannonMaterial.IRON)
        )
        
        self.audio.speak(
            f"{definition.name} için malzeme seçin. "
            f"Tunç güvenilir ama bakır gerektirir, patlama riski yüzde {bronze_risk}. "
            f"Demir ucuz ve hızlı ama patlama riski yüzde {iron_risk}.",
            interrupt=True
        )
    
    def _switch_to_produce(self):
        """Üretim moduna geç — kategori seçimi"""
        self.menu_mode = "produce"
        self._setup_production_menu()
        self.audio.speak(
            "Dökümhane. Bir kategori seçin: Sahra, Kuşatma veya Donanma.",
            interrupt=True
        )
    
    def _switch_to_cannons(self):
        """Envanter moduna geç"""
        self.menu_mode = "cannons"
        self._setup_cannon_menu()
        self.audio.speak("Top envanteri.", interrupt=True)
    
    def _select_cannon(self, index: int):
        """Top seç ve detaylı bilgi oku"""
        gm = self.screen_manager.game_manager
        if not gm or not hasattr(gm, 'artillery'):
            return
        
        artillery = gm.artillery
        if index >= len(artillery.cannons):
            return
        
        cannon = artillery.cannons[index]
        definition = cannon.get_definition()
        burst_risk = cannon.get_burst_risk()
        mat_name = "Tunç" if cannon.material == "bronze" else "Demir"
        
        info_parts = [
            f"{cannon.name}.",
            f"Tür: {definition.name}. Malzeme: {mat_name}.",
            f"Durum: yüzde {cannon.condition}.",
            f"Sahra gücü: {cannon.get_power('field')}.",
            f"Kuşatma gücü: {cannon.get_power('siege')}.",
            f"Moral hasarı: {cannon.get_morale_damage()}.",
            f"Menzil: {definition.range_level}.",
            f"Mürettebat: {definition.crew_required} topçu.",
            f"Patlama riski: yüzde {burst_risk}.",
            f"Atış sayısı: {cannon.shots_fired}.",
            f"Tecrübe: {cannon.experience}.",
            f"Bakım: {definition.maintenance} altın.",
        ]
        
        if cannon.damaged:
            info_parts.append("DİKKAT: Bu top hasarlı! R tuşuyla tamir edin.")
        
        self.audio.speak(" ".join(info_parts), interrupt=True)
    
    def _start_production(self, cannon_type: CannonType, material: CannonMaterial):
        """Top üretimi başlat — Tophane seviyesi dahil"""
        gm = self.screen_manager.game_manager
        if not gm or not hasattr(gm, 'artillery'):
            return
        
        # Tophane seviyesini al
        from game.systems.construction import BuildingType
        foundry_level = gm.construction.get_building_level(BuildingType.ARTILLERY_FOUNDRY)
        foundry_level = max(1, foundry_level)  # Min seviye 1
        
        success = gm.artillery.start_production(
            cannon_type, gm.economy, material,
            foundry_level=foundry_level
        )
        if success:
            self.audio.play_game_sound('construction', 'hammer')
            self._update_panels()
            self._setup_production_menu()
            self._update_queue_panel()
            self.menu_mode = "produce"
    
    def _announce_cannon_detail(self):
        """
        Tab ile seçili topun DETAYLI bilgisini oku.
        İstatistikler + tarihi not + kullanım ipucu.
        """
        gm = self.screen_manager.game_manager
        if not gm or not hasattr(gm, 'artillery'):
            return
        
        artillery = gm.artillery
        idx = self.cannon_menu.selected_index
        
        # Menüdeki seçili öğenin bir top olup olmadığını kontrol et
        if idx >= len(artillery.cannons):
            self.audio.speak("Bu öğenin detayı yok.", interrupt=True)
            return
        
        cannon = artillery.cannons[idx]
        defn = cannon.get_definition()
        mat = "Tunç" if cannon.material == "bronze" else "Demir"
        burst = cannon.get_burst_risk()
        
        # Detaylı bilgi
        parts = [
            f"Detaylı bilgi: {cannon.name}.",
            f"Tür: {defn.name}. {defn.description}",
            f"Malzeme: {mat}.",
            f"",
            f"Savaş İstatistikleri:",
            f"Sahra gücü: {cannon.get_power('field')}.",
            f"Kuşatma gücü: {cannon.get_power('siege')}.",
            f"Moral hasarı: {cannon.get_morale_damage()}.",
            f"Menzil: {defn.range_level} üzerinden 10.",
            f"Günlük atış kapasitesi: {defn.daily_fire_rate}.",
            f"Manevra kabiliyeti: {defn.mobility} üzerinden 10.",
            f"",
            f"Durum ve Risk:",
            f"Kondisyon: yüzde {cannon.condition}.",
            f"Patlama riski: yüzde {burst}.",
            f"Toplam atış: {cannon.shots_fired}.",
            f"Mürettebat tecrübesi: {cannon.experience} üzerinden 100.",
            f"Bakım maliyeti: günlük {defn.maintenance} altın.",
            f"Atış başı barut tüketimi: {defn.gunpowder_per_shot}.",
            f"",
            f"Tarihi Not: {defn.historical_note}",
        ]
        
        if cannon.damaged:
            parts.append("DİKKAT: Bu top hasarlı! R tuşuyla tamir edin.")
        
        self.audio.speak(" ".join(parts), interrupt=True)
    
    def _announce_type_detail(self):
        """
        Üretim menüsünde Tab ile seçili top TÜRÜNÜN detaylı bilgisini oku.
        Yeni oyunculara öğretici.
        """
        # Üretim menüsündeki seçili öğeyi top türüne eşle
        idx = self.production_menu.selected_index
        
        # Menü yapısına göre cannon type'ları eşle
        # Üretim menüsü sırası: Geri, boş, SAHRA başlık, Abus, Darbzen, Kolunburna,
        #                         boş, KUŞATMA başlık, Havan, Balyemez, Şahi,
        #                         boş, DONANMA başlık, Prangi
        type_map = {
            3: CannonType.ABUS,
            4: CannonType.DARBZEN,
            5: CannonType.KOLUNBURNA,
            8: CannonType.HAVAN,
            9: CannonType.BALYEMEZ,
            10: CannonType.SAHI,
            13: CannonType.PRANGI,
        }
        
        cannon_type = type_map.get(idx)
        if not cannon_type:
            self.audio.speak("Bu öğenin detayı yok. Bir top türü seçin.", interrupt=True)
            return
        
        defn = CANNON_DEFINITIONS[cannon_type]
        bronze_cost = defn.get_cost(CannonMaterial.BRONZE)
        bronze_risk = defn.get_burst_risk(CannonMaterial.BRONZE)
        iron_risk = defn.get_burst_risk(CannonMaterial.IRON)
        
        # Kategori belirle
        if defn.is_naval:
            kategori = "Donanma topu"
        elif defn.siege_power >= 15:
            kategori = "Kuşatma topu"
        else:
            kategori = "Sahra topu"
        
        parts = [
            f"Detaylı bilgi: {defn.name}.",
            f"Kategori: {kategori}.",
            f"{defn.description}",
            f"",
            f"Savaş İstatistikleri:",
            f"Sahra gücü: {defn.field_power}.",
            f"Kuşatma gücü: {defn.siege_power}.",
            f"Moral hasarı: {defn.morale_damage}.",
            f"Menzil: {defn.range_level} üzerinden 10.",
            f"Günlük atış: {defn.daily_fire_rate}.",
            f"Manevra: {defn.mobility} üzerinden 10.",
            f"Ağırlık: {defn.weight:,} kilogram.",
            f"",
            f"Mürettebat ve Lojistik:",
            f"Gereken mürettebat: {defn.crew_required} topçu.",
            f"Atış başı barut: {defn.gunpowder_per_shot}.",
            f"Günlük bakım: {defn.maintenance} altın.",
            f"",
            f"Üretim Maliyeti: Tunç için {bronze_cost['gold']} altın, {bronze_cost.get('copper', 0)} bakır.",
            f"Üretim süresi: {defn.build_time} gün. Demir ile {max(1, defn.build_time // 2)} gün.",
            f"Patlama riski: Tunçta yüzde {bronze_risk}, demirde yüzde {iron_risk}.",
        ]
        
        if not defn.can_be_iron:
            parts.append("Not: Bu top sadece tunçtan üretilebilir, demir seçeneği yoktur.")
        
        parts.append(f"")
        parts.append(f"Tarihi Not: {defn.historical_note}")
        
        self.audio.speak(" ".join(parts), interrupt=True)
    
    def _cycle_ammo(self):
        """
        M tuşu ile seçili topun mühimmatını değiştir.
        Taş Gülle → Demir Gülle → Saçma → Ateşli Gülle → Zincirli Gülle → Taş Gülle
        """
        gm = self.screen_manager.game_manager
        if not gm or not hasattr(gm, 'artillery'):
            return
        
        artillery = gm.artillery
        idx = self.cannon_menu.selected_index
        
        if idx >= len(artillery.cannons):
            self.audio.speak("Bir top seçin.", interrupt=True)
            return
        
        cannon = artillery.cannons[idx]
        
        # Mühimmat sırası
        ammo_order = [
            AmmoType.STONE_BALL,
            AmmoType.IRON_BALL,
            AmmoType.GRAPESHOT,
            AmmoType.INCENDIARY,
            AmmoType.CHAIN_SHOT,
        ]
        
        current = cannon.get_ammo_type()
        current_idx = ammo_order.index(current) if current in ammo_order else 0
        next_idx = (current_idx + 1) % len(ammo_order)
        new_ammo = ammo_order[next_idx]
        
        cannon.selected_ammo = new_ammo.value
        ammo_info = AMMO_MULTIPLIERS[new_ammo]
        
        self.audio.speak(
            f"{cannon.name}: Mühimmat değiştirildi → {ammo_info['name']}. "
            f"{ammo_info['description']}",
            interrupt=True
        )
        
        # Panelı güncelle
        self._update_panels()
        self._setup_cannon_menu()
    
    def _announce_personnel(self):
        """
        I tuşu ile topçu personel durumunu oku.
        Topçu/Cebeci oranı ve etkinlik.
        """
        gm = self.screen_manager.game_manager
        if not gm or not hasattr(gm, 'artillery'):
            return
        
        artillery = gm.artillery
        crew_needed = artillery.get_total_crew_required()
        crew_eff = artillery.get_crew_effectiveness(gm.military)
        
        from game.systems.military import UnitType as MilitaryUnitType
        topcu = gm.military.units.get(MilitaryUnitType.TOPCU, 0)
        cebeci = gm.military.units.get(MilitaryUnitType.CEBECI, 0)
        cebeci_needed = max(1, crew_needed // 3)
        
        parts = [
            f"Topçu Personel Durumu.",
            f"Topçu askeri: {topcu}, ihtiyaç: {crew_needed}.",
            f"Cebeci askeri: {cebeci}, ihtiyaç: {cebeci_needed}.",
            f"Toplam etkinlik: yüzde {int(crew_eff * 100)}.",
        ]
        
        if crew_eff >= 1.0:
            parts.append("Durum: Tam kadro veya fazlası. Topçu tam güçte!")
        elif crew_eff >= 0.8:
            parts.append("Durum: Yeterli. Hafif performans kaybı.")
        elif crew_eff >= 0.5:
            parts.append("DİKKAT: Topçu eksik! Atış hızı ve isabet düşük.")
        else:
            parts.append("KRİTİK: Topçu birliği ciddi personel eksikliği yaşıyor!")
        
        # Barut stoku uyarısı
        gunpowder = gm.economy.resources.gunpowder
        daily_consumption = artillery.get_gunpowder_consumption()
        if daily_consumption > 0:
            days_left = gunpowder // daily_consumption
            parts.append(f"Barut stoku: {gunpowder}. Tahmini {days_left} atış günü kaldı.")
            if days_left < 5:
                parts.append("UYARI: Barut stoku kritik seviyede!")
        
        self.audio.speak(" ".join(parts), interrupt=True)
    
    def _repair_cannons(self):
        """Tüm hasarlı topları tamir et"""
        gm = self.screen_manager.game_manager
        if not gm or not hasattr(gm, 'artillery'):
            return
        
        gm.artillery.repair_all(gm.economy)
        self._update_panels()
        self._setup_cannon_menu()
    
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
            self.artillery_panel.add_item("Sahra Gücü", str(artillery.get_total_power("field")))
            self.artillery_panel.add_item("Kuşatma Gücü", str(artillery.get_total_power("siege")))
            self.artillery_panel.add_item("Moral Hasarı", str(artillery.get_morale_damage()))
            self.artillery_panel.add_item("Bakım", f"{artillery.get_maintenance_cost()} altın/gün")
            
            damaged = artillery.get_damaged_count()
            if damaged > 0:
                self.artillery_panel.add_item("Hasarlı", f"{damaged} top!")
            
            # Top türü sayıları
            counts = artillery.get_cannon_counts()
            for cannon_type, count in counts.items():
                if count > 0:
                    name = CANNON_DEFINITIONS[cannon_type].name
                    self.artillery_panel.add_item(name, str(count))
        else:
            self.artillery_panel.add_item("", "Topçu Ocağı sistemine erişilemiyor")
        
        # Dökümhane paneli — genişletilmiş kaynaklar
        self.foundry_panel.clear()
        res = gm.economy.resources
        self.foundry_panel.add_item("Altın", f"{res.gold:,}")
        self.foundry_panel.add_item("Demir", f"{res.iron:,}")
        self.foundry_panel.add_item("Bakır", f"{res.copper:,}")
        self.foundry_panel.add_item("Taş", f"{res.stone:,}")
        self.foundry_panel.add_item("Barut", f"{res.gunpowder:,}")
        
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
            mat = "Tunç" if production.material == "bronze" else "Demir"
            self.queue_panel.add_item(
                f"{i+1}. {mat} {name}",
                f"{production.turns_remaining} gün kaldı"
            )
    
    def _go_back(self):
        self.screen_manager.change_screen(ScreenType.PROVINCE_VIEW)
    
    def handle_event(self, event) -> bool:
        # Aktif menüyü işle
        if self.menu_mode in ("produce", "material", "category"):
            if self.production_menu.handle_event(event):
                return True
        else:
            if self.cannon_menu.handle_event(event):
                return True
        
        if self.back_button.handle_event(event):
            return True
        
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_BACKSPACE:
                if self.menu_mode == "material":
                    # Malzeme → Kategori
                    if hasattr(self, '_current_category'):
                        self._show_category(self._current_category)
                    else:
                        self._switch_to_produce()
                elif self.menu_mode == "category":
                    # Kategori → Kategoriler
                    self._switch_to_produce()
                elif self.menu_mode == "produce":
                    self._switch_to_cannons()
                else:
                    self._go_back()
                return True
            
            if event.key == pygame.K_ESCAPE:
                self._go_back()
                return True
            
            # Tab — Detaylı bilgi oku
            if event.key == pygame.K_TAB:
                if self.menu_mode == "cannons":
                    self._announce_cannon_detail()
                elif self.menu_mode in ("category", "material"):
                    self._announce_type_detail()
                return True
            
            # F2 — Menüler arası geçiş
            if event.key == pygame.K_F2:
                if self.menu_mode == "cannons":
                    self._switch_to_produce()
                else:
                    self._switch_to_cannons()
                return True
            
            # R - Tamir
            if event.key == pygame.K_r:
                self._repair_cannons()
                return True
            
            # M - Mühimmat değiştir (envanterde)
            if event.key == pygame.K_m and self.menu_mode == "cannons":
                self._cycle_ammo()
                return True
            
            # I - Personel bilgisi
            if event.key == pygame.K_i:
                self._announce_personnel()
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
        
        small_font = get_font(FONTS['subheader'])
        
        if self.menu_mode in ("produce", "material"):
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
