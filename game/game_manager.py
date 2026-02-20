# -*- coding: utf-8 -*-
"""
Osmanlı Eyalet Yönetim Simülasyonu - Oyun Yöneticisi
Tüm sistemleri koordine eden ana sınıf.
"""

import json
import os
import sys
from typing import Dict, Optional
from dataclasses import dataclass
from audio.audio_manager import get_audio_manager
from game.systems.economy import EconomySystem
from game.systems.military import MilitarySystem
from game.systems.population import PopulationSystem
from game.systems.construction import ConstructionSystem, BuildingType
from game.systems.diplomacy import DiplomacySystem
from game.systems.events import EventSystem
from game.systems.workers import WorkerSystem
from game.systems.warfare import WarfareSystem
from game.systems.trade import TradeSystem
from game.systems.naval import NavalSystem
from game.systems.artillery import ArtillerySystem
from game.systems.espionage import EspionageSystem  # YENİ
from game.systems.religion import ReligionSystem    # YENİ
from game.systems.history import HistorySystem      # YENİ


def get_base_path():
    """
    EXE veya Python script olarak çalışırken doğru temel yolu döndür.
    PyInstaller ile paketlendiğinde sys.executable'ın dizinini kullanır.
    """
    if getattr(sys, 'frozen', False):
        # PyInstaller ile paketlenmiş EXE
        return os.path.dirname(sys.executable)
    else:
        # Normal Python script
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@dataclass
class ProvinceInfo:
    """Eyalet bilgileri"""
    name: str = "Rum Eyaleti"
    capital: str = "Sivas"
    region: str = "Anadolu"
    is_coastal: bool = False  # Kıyı şehri mi? (Tersane için gerekli)


# Kıyı eyaletleri listesi
COASTAL_PROVINCES = [
    "İstanbul", "İzmir", "Trabzon", "Antalya", "Sinop",
    "Ege Eyaleti", "Karadeniz Eyaleti", "Akdeniz Eyaleti",
    "Cezayir", "Kırım", "Girit", "Rodos", "Kıbrıs"
]

# Mevsim isimleri
SEASONS = {
    1: "Kış", 2: "Kış", 3: "İlkbahar",
    4: "İlkbahar", 5: "İlkbahar", 6: "Yaz", 
    7: "Yaz", 8: "Yaz", 9: "Sonbahar",
    10: "Sonbahar", 11: "Sonbahar", 12: "Kış"
}


class GameManager:
    """Ana oyun yöneticisi"""
    
    def __init__(self):
        # Eyalet bilgisi
        self.province = ProvinceInfo()
        
        # Oyuncu karakteri (YENİ)
        self.player = None  # CharacterCreationScreen'de atanır
        
        # Oyun kimliği (aynı oyunun aynı yuvaya kaydı için)
        self.game_id = None
        self.save_slot = None  # 1, 2, 3
        
        # Zaman (1 tur = 1 gün)
        self.current_year = 1520
        self.current_month = 1  # 1-12
        self.current_day = 1    # 1-31
        self.turn_count = 0
        
        # Oyun durumu
        self.is_running = True
        self.is_paused = False
        self.game_over = False
        self.game_over_reason = ""
        
        # Sistemler
        self.economy = EconomySystem()
        self.military = MilitarySystem()
        self.population = PopulationSystem()
        self.construction = ConstructionSystem()
        self.diplomacy = DiplomacySystem()
        self.events = EventSystem()
        self.workers = WorkerSystem()
        self.warfare = WarfareSystem()  # Savaş sistemi
        self.trade = TradeSystem()  # Ticaret sistemi
        self.naval = NavalSystem()  # Deniz kuvvetleri
        self.artillery = ArtillerySystem()  # Topçu ocağı
        self.espionage = EspionageSystem()  # Casusluk sistemi (YENİ)
        self.religion = ReligionSystem()    # Din/Kültür sistemi (YENİ)
        self.history = HistorySystem()      # Geçmiş Olaylar (YENİ)
        
        # Ses yöneticisi
        self.audio = get_audio_manager()
    
    def new_game(self, province_name: str = None):
        """Yeni oyun başlat"""
        import uuid
        from game.player import create_default_character
        
        if province_name:
            self.province.name = province_name
        
        # Yeni benzersiz oyun ID'si oluştur
        self.game_id = str(uuid.uuid4())[:8]
        self.save_slot = None  # Henüz kaydedilmedi
        
        # Varsayılan karakter (CharacterCreationScreen kullanılmazsa)
        if self.player is None:
            self.player = create_default_character()
        
        # Sistemleri sıfırla
        self.economy = EconomySystem()
        self.military = MilitarySystem()
        self.population = PopulationSystem()
        self.construction = ConstructionSystem()
        self.diplomacy = DiplomacySystem()
        self.events = EventSystem()
        self.workers = WorkerSystem()
        self.warfare = WarfareSystem()
        self.trade = TradeSystem()
        self.naval = NavalSystem()
        self.artillery = ArtillerySystem()
        
        # YENİ SİSTEMLER (Kritik Düzeltme: Resetlenmediği için önceki oyun verisi kalıyordu)
        from game.systems.espionage import EspionageSystem
        from game.systems.religion import ReligionSystem
        from game.systems.guilds import GuildSystem
        from game.systems.history import HistorySystem
        
        self.espionage = EspionageSystem()
        self.religion = ReligionSystem()
        self.guild_system = GuildSystem()
        self.history = HistorySystem()
        
        # Zaman sıfırla (1 tur = 1 gün)
        self.current_year = 1520
        self.current_month = 1
        self.current_day = 1
        self.turn_count = 0
        
        # Durum
        self.is_running = True
        self.game_over = False
        
        # Karaktere göre duyuru
        if self.player:
            title = self.player.get_full_title()
            self.audio.announce_screen_change(f"{self.province.name} - {title}")
            self.audio.speak(
                f"1 {self._get_month_name(self.current_month)} {self.current_year}. "
                f"Padişah Kanuni Sultan Süleyman döneminde, {title} olarak göreve başladınız.",
                interrupt=False
            )
        else:
            self.audio.announce_screen_change(f"{self.province.name} Valiliği")
            self.audio.speak(
                f"1 {self._get_month_name(self.current_month)} {self.current_year}. "
                f"Osmanlı İmparatorluğu'nda eyalet valisi olarak göreve başladınız.",
                interrupt=False
            )
        
        # Geçmişe kaydet
        if hasattr(self, 'history'):
            self.history.add_entry(
                turn=0,
                year=self.current_year,
                message="Yeni oyun başlatıldı. Eyalet valisi olarak göreve atandınız.",
                category="general"
            )
    
    def _get_month_name(self, month: int) -> str:
        """Ay numarasından Türkçe ay ismi döndür"""
        month_names = ["", "Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran",
                      "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]
        return month_names[month] if 1 <= month <= 12 else ""
    
    def process_turn(self):
        """
        Tur işleme - tüm sistemleri güncelle (1 tur = 1 gün)
        """
        self.turn_count += 1
        
        # Günü ilerlet
        self.current_day += 1
        
        # Ay geçişi (her ayda farklı gün sayısı)
        days_in_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
        if self.current_day > days_in_month[self.current_month - 1]:
            self.current_day = 1
            self.current_month += 1
            
            # Ay başı bildirimi
            month_names = ["", "Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran",
                          "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]
            if self.current_month <= 12:
                self.audio.announce(f"{month_names[self.current_month]} ayı başladı")
        
        if self.current_month > 12:
            self.current_month = 1
            self.current_year += 1
            self.events.reset_yearly()
            self.audio.announce(f"Yeni Yıl: {self.current_year}")
            
            # Geçmişe kaydet
            if hasattr(self, 'history'):
                self.history.add_entry(
                    turn=self.turn_count,
                    year=self.current_year,
                    message=f"Yeni Yıl: {self.current_year}",
                    category="general"
                )
        
        # === SİSTEMLERİ GÜNCELLE ===
        
        # Mevsim belirle ve modifierleri uygula
        current_season = self.get_season()
        seasonal_food_mod = 1.0
        seasonal_trade_mod = 1.0
        
        if current_season == "Kış":
            seasonal_food_mod = 0.75  # Kışta üretim %25 azalır
            seasonal_trade_mod = 0.8  # Ticaret de biraz azalır
        elif current_season == "İlkbahar":
            seasonal_food_mod = 1.2  # Ekim dönemi
        elif current_season == "Yaz":
            seasonal_trade_mod = 1.2  # Ticaret canlanır
        elif current_season == "Sonbahar":
            seasonal_food_mod = 1.5  # Hasat dönemi
        
        # 1. Ekonomi
        building_maintenance = self.construction.get_total_maintenance()
        military_maintenance = self.military.get_maintenance_cost()
        artillery_maintenance = self.artillery.get_maintenance_cost()
        naval_maintenance = self.naval.get_maintenance_cost() if self.province.is_coastal else 0
        
        total_maintenance = (building_maintenance + military_maintenance + 
                           artillery_maintenance + naval_maintenance)
        
        # Ticaret bonusu uygula (mevsimsel modifier ile)
        # Bonus daha dengeli hesaplama: /500 ile azalan getiri
        trade_bonus = self.construction.get_total_trade_bonus()
        trade_mod = (1.0 + (trade_bonus / 500)) * seasonal_trade_mod
        
        # Kadın karakter: Tekstil ticareti bonusu (+%15)
        if self.player:
            textile_bonus = self.player.get_bonus('textile_trade')
            if textile_bonus > 0:
                trade_mod *= (1.0 + textile_bonus)
        
        self.economy.trade_modifier = trade_mod
        
        net_income = self.economy.process_turn(
            population=self.population.population.total,
            military_count=self.military.get_total_soldiers(),
            building_maintenance=total_maintenance
        )
        
        # 2. Üretim (çiftlik, kereste ocağı, maden) - mevsimsel modifier
        farm_food = int(self.construction.get_food_production() * seasonal_food_mod)
        # YENİ: Çiftçiler de zahire üretir (kişi başı 0.1)
        farmer_food = int(self.population.population.farmers * 0.1)
        food_production = farm_food + farmer_food
        
        wood_production = self.construction.get_wood_production()
        iron_production = self.construction.get_iron_production()
        
        # YENİ: Taş ve Denizcilik Malzemeleri
        stone_production = self.construction.get_stone_production()
        naval_supplies = self.construction.get_naval_supplies_production()
        
        self.economy.add_resources(
            food=food_production,
            wood=wood_production,
            iron=iron_production,
            stone=stone_production,
            rope=naval_supplies['rope'],
            tar=naval_supplies['tar'],
            sailcloth=naval_supplies['sailcloth']
        )
        
        # 3. Nüfus
        has_mosque = self.construction.has_building(BuildingType.MOSQUE)
        has_hospital = self.construction.has_building(BuildingType.HOSPITAL)
        military_power = self.military.get_total_power()
        
        # Han bonusu nüfus artışına ekle
        pop_growth_bonus = self.construction.get_population_growth_bonus()
        base_growth = 0.02 + pop_growth_bonus
        
        # Kadın karakter: Nüfus artışı bonusu (+%10)
        if self.player:
            pop_bonus = self.player.get_bonus('population_growth')
            if pop_bonus > 0:
                base_growth *= (1.0 + pop_bonus)
        
        self.population.growth_rate = base_growth
        
        # === KADIN MALUS: Bey sadakati → huzur düşüşü ===
        if self.player:
            bey_malus = self.player.get_malus('bey_loyalty')  # -%20 → 0 arası
            if bey_malus < 0:
                # Her 5 turda bir malus etkisi (sürekli değil, periyodik)
                if self.turn_count % 5 == 0:
                    happiness_penalty = int(abs(bey_malus) * 10)  # Max -%20*10 = -2
                    self.population.happiness = max(0, self.population.happiness - happiness_penalty)
        
        # === KADIN MALUS: Ulema desteği → sadakat düşüşü ===
        if self.player:
            ulema_malus = self.player.get_malus('ulema_support')  # -%15 → 0 arası
            if ulema_malus < 0:
                if self.turn_count % 5 == 0:
                    loyalty_penalty = int(abs(ulema_malus) * 10)  # Max -%15*10 = -1
                    self.diplomacy.sultan_loyalty = max(0, self.diplomacy.sultan_loyalty - loyalty_penalty)
        
        # YENİ: Nüfus kapasitesi hesapla
        population_capacity = self.construction.get_population_capacity()
        
        pop_result = self.population.process_turn(
            food_available=self.economy.resources.food,
            tax_rate=self.economy.tax_rate,
            has_mosque=has_mosque,
            has_hospital=has_hospital,
            military_power=military_power,
            population_capacity=population_capacity
        )
        
        # Yiyecek tüketimi
        self.economy.resources.food -= self.population.food_consumption
        if self.economy.resources.food < 0:
            self.economy.resources.food = 0
        
        # 4. İnşaat
        construction_messages = self.construction.process_turn()
        
        # 5. İşçiler
        worker_result = self.workers.process_turn()
        # İşçi üretimini ekle
        self.economy.add_resources(
            food=worker_result['production']['food'],
            wood=worker_result['production']['wood'],
            iron=worker_result['production']['iron']
        )
        # İşçi bonuslarını uygula
        trade_bonus = worker_result['bonuses'].get('trade_bonus', 0)
        if trade_bonus > 0:
            self.economy.trade_modifier += trade_bonus
        
        # 6. Askeri
        self.military.process_turn()
        
        # Erkek karakter: Yeniçeri sadakat bonusu (+%15)
        # Her 3 turda +1 moral (0.15 * 3 turda bir = sürekli küçük etki)
        if self.player:
            janissary_bonus = self.player.get_bonus('janissary_loyalty')
            if janissary_bonus > 0 and self.turn_count % 3 == 0:
                self.military.morale = min(100, self.military.morale + 1)
        
        # 7. Topçu üretimi (Topçu Ocağı)
        self.artillery.process_production()
        
        # 8. Deniz kuvvetleri (Tersane) - sadece kıyı eyaletlerinde
        if self.province.is_coastal:
            self.naval.process_construction()
        
        # 9. Diplomasi
        diplomacy_messages = self.diplomacy.process_turn()
        
        # Görev sürelerini kontrol et (Sondan başa doğru, silme işlemi için güvenli)
        for i in range(len(self.diplomacy.active_missions) - 1, -1, -1):
            mission = self.diplomacy.active_missions[i]
            mission['turns_remaining'] -= 1
            if mission['turns_remaining'] <= 0:
                self.diplomacy.fail_mission(i)
        
        # 10. Savaşlar - topçu ve deniz gücü desteği ile
        artillery_power = self.artillery.get_total_power()
        siege_bonus = self.artillery.get_siege_bonus()
        naval_power = self.naval.get_fleet_power() if self.province.is_coastal else 0
        
        # Erkek karakter: Kuşatma saldırı bonusu (+%10)
        if self.player:
            siege_attack_bonus = self.player.get_bonus('siege_attack')
            if siege_attack_bonus > 0:
                siege_bonus = int(siege_bonus * (1.0 + siege_attack_bonus))
        
        battle_results = self.warfare.process_battles(
            self.military,
            artillery_power=artillery_power,
            siege_bonus=siege_bonus,
            naval_power=naval_power
        )
        for result in battle_results:
            loyalty_change = result.loyalty_change
            
            # Geçmişe kaydet (YENİ)
            if hasattr(self, 'history'):
                victory_str = "ZAFER" if result.victory else "YENİLGİ"
                target_name = "Düşman"
                if result.battle_report:
                    target_name = result.battle_report.target_name
                
                self.history.add_entry(
                    turn=self.turn_count,
                    year=self.current_year,
                    message=f"SAVAŞ SONUCU: {victory_str}! {target_name}. Yağma: {result.loot_gold} altın.",
                    category="military"
                )
            
            # Erkek karakter: Askeri prestij bonusu (+%10 sadakat kazancı)
            if self.player and result.victory:
                prestige_bonus = self.player.get_bonus('military_prestige')
                if prestige_bonus > 0 and loyalty_change > 0:
                    loyalty_change = int(loyalty_change * (1.0 + prestige_bonus))
            
            self.diplomacy.sultan_loyalty = max(0, min(100, 
                self.diplomacy.sultan_loyalty + loyalty_change))
            if result.loot_gold > 0:
                self.economy.add_resources(gold=result.loot_gold)
        
        # 11. Ticaret
        # Liman durumunu güncelle (Tersane binası)
        has_shipyard = self.construction.has_building(BuildingType.SHIPYARD)
        shipyard_level = 0
        if has_shipyard:
            shipyard_level = self.construction.buildings[BuildingType.SHIPYARD].level
        self.trade.update_port_status(has_shipyard, shipyard_level)
        
        # Ticaret işle
        trade_result = self.trade.process_turn(self.economy)
        
        # 13. Casusluk
        espionage_result = self.espionage.process_turn()
        espionage_messages = espionage_result.get('messages', [])
        
        # Casusluk etkilerini oyuna yansıt (Keşif, Sabotaj, Fitne vb.)
        if espionage_result.get('completed'):
            for result in espionage_result['completed']:
                effects = result.get('effects', {})
                for effect_name, value in effects.items():
                    # Kendi devletimize olan etkiler
                    if effect_name == 'happiness':
                        self.population.happiness = min(100, self.population.happiness + value)
                    elif effect_name == 'loyalty':
                        self.diplomacy.sultan_loyalty = min(100, self.diplomacy.sultan_loyalty + value)
                    elif effect_name == 'sultan_loyalty':
                        self.diplomacy.sultan_loyalty = min(100, self.diplomacy.sultan_loyalty + value)
                    elif effect_name == 'security':
                        self.espionage.security_level = min(100, self.espionage.security_level + value)
                    elif effect_name == 'intelligence':
                        self.espionage.intelligence_level = min(100, self.espionage.intelligence_level + value)
                    # Düşmana olan etkiler (Şimdilik varsayımsal global etki olarak tutuluyor)
                    # enemy_morale, enemy_stability vb. eklenebilir. Şimdilik pas geçiyoruz.
        
        # 14. Din ve Kültür (YENİ)
        religion_result = self.religion.process_turn(self.economy)
        
        # 15. Vakıf bonusu (Kadın karakter: +%30 vakıf etkisi)
        # Her 3 turda +1 huzur (küçük ama birikimli etki)
        if self.player:
            vakif_bonus = self.player.get_bonus('vakif_effect')
            if vakif_bonus > 0 and self.turn_count % 3 == 0:
                self.population.happiness = min(100, self.population.happiness + 1)
                # Her 10 turda +1 sadakat (vakıf padişahı da etkiler)
                if self.turn_count % 10 == 0:
                    self.diplomacy.sultan_loyalty = min(100, self.diplomacy.sultan_loyalty + 1)
        
        # 16. Oyuncu karakter tur güncellemesi (malus azalması vb.)
        if self.player:
            self.player.process_turn()
        
        # 17. Olaylar
        game_state = {
            'happiness': self.population.happiness,
            'at_war': len(self.warfare.active_battles) > 0,
            'loyalty': self.diplomacy.sultan_loyalty,
            'player_gender': self.player.gender.value if self.player else 'male',
            'player_title': self.player.get_full_title() if self.player else None,
            'turn_count': self.turn_count
        }
        
        event = self.events.check_for_event(self.current_year, game_state)
        if event:
            self.events.announce_event()
            # Geçmişe kaydet (YENİ)
            if hasattr(self, 'history'):
                self.history.add_entry(
                    turn=self.turn_count,
                    year=self.current_year,
                    message=f"OLAY: {event.title} - {event.description}",
                    category="event"
                )
        
        # 18. Başarı kontrolü
        try:
            from game.systems.achievements import get_achievement_system
            achievement_system = get_achievement_system()
            achievement_system.on_turn_end(self)
        except Exception:
            pass  # Başarı sistemi yüklenemezse oyunu etkilemesin
        
        # === OYUN SONU KONTROL ===
        self._check_game_over()
        
        # Tur sonu özeti
        self._announce_turn_summary(net_income, pop_result)
        
        # === OTOMATİK KAYIT ===
        self._check_auto_save()
        
        # Toplanan mesajları birleştir
        messages = []
        if 'construction_messages' in locals():
            messages.extend(construction_messages)
        if 'espionage_messages' in locals():
            messages.extend(espionage_messages)
        if 'diplomacy_messages' in locals():
            messages.extend(diplomacy_messages)
        
        return {
            'year': self.current_year,
            'month': self.current_month,
            'turn': self.turn_count,
            'net_income': net_income,
            'population_change': pop_result['population_change'],
            'event': event is not None,
            'messages': messages
        }
    
    def _check_game_over(self):
        """Oyun sonu koşullarını kontrol et"""
        # Padişah sadakati çok düşük
        if self.diplomacy.sultan_loyalty <= 0:
            self.game_over = True
            self.game_over_reason = "Padişah sizi hain ilan etti ve idam ettirdi!"
            self.audio.announce(self.game_over_reason)
        
        # Halk isyanı çok uzun sürdü
        if self.population.active_revolt and self.population.unrest >= 100:
            self.game_over = True
            self.game_over_reason = "Halk ayaklanması kontrol altına alınamadı. Eyalet kaybedildi!"
            self.audio.announce(self.game_over_reason)
        
        # İflas
        if self.economy.resources.gold < -5000:
            self.game_over = True
            self.game_over_reason = "Hazine iflas etti. Görevden alındınız!"
            self.audio.announce(self.game_over_reason)
    
    def _announce_turn_summary(self, net_income: int, pop_result: dict):
        """Tur özeti duyur"""
        # Her 3 turda bir özet
        if self.turn_count % 3 == 0:
            self.audio.announce_value("Yıl", str(self.current_year))
            self.audio.announce_value("Altın", str(self.economy.resources.gold))
            
            if net_income >= 0:
                self.audio.speak(f"Gelir fazlası: {net_income}")
            else:
                self.audio.speak(f"Zarar: {net_income}")
    
    def check_victory(self) -> Optional[dict]:
        """Zafer koşullarını kontrol et"""
        from config import VICTORY_CONDITIONS
        
        victories = []
        
        # Ekonomik zafer
        if self.economy.resources.gold >= VICTORY_CONDITIONS['economic_gold']:
            victories.append({
                'type': 'economic',
                'name': 'Ekonomik Zafer',
                'description': f'{VICTORY_CONDITIONS["economic_gold"]:,} altın biriktirdiniz!'
            })
        
        # Askeri zafer - savaş kazanma sayısı
        if hasattr(self.warfare, 'victories_count'):
            if self.warfare.victories_count >= VICTORY_CONDITIONS['military_victories']:
                victories.append({
                    'type': 'military',
                    'name': 'Askeri Zafer',
                    'description': f'{VICTORY_CONDITIONS["military_victories"]} zafer kazandınız!'
                })
        
        # Diplomatik zafer - ittifak sayısı
        alliance_count = len(self.diplomacy.allies) if hasattr(self.diplomacy, 'allies') else 0
        if alliance_count >= VICTORY_CONDITIONS['diplomatic_alliances']:
            victories.append({
                'type': 'diplomatic',
                'name': 'Diplomatik Zafer',
                'description': f'{VICTORY_CONDITIONS["diplomatic_alliances"]} ittifak kurdunuz!'
            })
        
        # Hakimiyet zafer - nüfus
        base_capacity = 50000
        target_pop = base_capacity * VICTORY_CONDITIONS['dominance_population_multiplier']
        if self.population.population.total >= target_pop:
            victories.append({
                'type': 'dominance',
                'name': 'Hakimiyet Zaferi',
                'description': f'{target_pop:,} nüfusa ulaştınız!'
            })
        
        if victories:
            return {'won': True, 'victories': victories}
        return None
    
    def _check_auto_save(self):
        """Otomatik kayıt kontrolü"""
        from game.game_settings import get_settings
        
        settings = get_settings()
        
        # Otomatik kayıt açık mı?
        if not settings.get('auto_save_enabled', True):
            return
        
        # Kayıt aralığını kontrol et
        interval = settings.get('auto_save_interval', 5)
        if self.turn_count % interval != 0:
            return
        
        # Oyun bittiyse kaydetme
        if self.game_over:
            return
        
        # Kaydet (mevcut slot veya slot 1)
        slot = self.save_slot or 1
        
        # Sessiz kayıt (bildirim olmadan)
        try:
            self._silent_save(slot)
        except Exception as e:
            print(f"Otomatik kayıt hatası: {e}")
    
    def _silent_save(self, slot: int):
        """Sessiz kayıt (bildirim olmadan)"""
        import uuid
        
        if self.game_id is None:
            self.game_id = str(uuid.uuid4())[:8]
        
        if self.save_slot is None:
            self.save_slot = slot
        
        filepath = os.path.join(
            get_base_path(),
            'saves',
            f'slot_{slot}.json'
        )
        
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        save_data = {
            'version': '1.1',
            'game_id': self.game_id,
            'save_slot': slot,
            'auto_save': True,  # Otomatik kayıt işareti
            'player': self.player.to_dict() if self.player else None,
            'province': {
                'name': self.province.name,
                'capital': self.province.capital,
                'region': self.province.region,
                'is_coastal': self.province.is_coastal
            },
            'time': {
                'year': self.current_year,
                'month': self.current_month,
                'day': self.current_day,
                'turn': self.turn_count
            },
            'economy': self.economy.to_dict(),
            'military': self.military.to_dict(),
            'population': self.population.to_dict(),
            'construction': self.construction.to_dict(),
            'diplomacy': self.diplomacy.to_dict(),
            'events': self.events.to_dict(),
            'warfare': self.warfare.to_dict(),
            'trade': self.trade.to_dict(),
            'workers': self.workers.to_dict(),
            'naval': self.naval.to_dict(),
            'artillery': self.artillery.to_dict(),
            'espionage': self.espionage.to_dict(),
            'religion': self.religion.to_dict(),
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(save_data, f, ensure_ascii=False, indent=2)
    
    def apply_event_effects(self, effects: Dict[str, int]):
        """Olay etkilerini uygula"""
        for effect, value in effects.items():
            if effect == 'gold':
                self.economy.resources.gold += value
            elif effect == 'food':
                self.economy.resources.food += value
            elif effect == 'wood':
                self.economy.resources.wood += value
            elif effect == 'iron':
                self.economy.resources.iron += value
            elif effect == 'happiness':
                self.population.add_happiness_modifier('event', value)
            elif effect == 'loyalty':
                self.diplomacy.sultan_loyalty += value
            elif effect == 'favor':
                self.diplomacy.sultan_favor += value
            elif effect == 'morale':
                self.military.morale += value
            elif effect == 'population_loss':
                self.population.population.farmers -= value
            elif effect == 'military_loss':
                # Azap'lardan kayıp
                from game.systems.military import UnitType
                loss = min(value, self.military.units[UnitType.AZAP])
                self.military.units[UnitType.AZAP] -= loss
            elif effect == 'trade_modifier':
                self.economy.trade_modifier += value / 100
            elif effect == 'tax_modifier':
                self.economy.tax_modifier += value / 100
            elif effect == 'unrest':
                self.population.unrest += value
            elif effect == 'neighbor_relation':
                # İlk komşuya etkile
                if self.diplomacy.neighbors:
                    first = list(self.diplomacy.neighbors.keys())[0]
                    self.diplomacy.neighbors[first].value += value
                    self.diplomacy.neighbors[first].update_type()
    
    def get_season(self) -> str:
        """Mevcut mevsimi döndür"""
        return SEASONS.get(self.current_month, "Yaz")
    
    def get_summary(self) -> Dict:
        """Oyun durumu özeti"""
        return {
            'province': self.province.name,
            'year': self.current_year,
            'month': self.current_month,
            'season': self.get_season(),
            'turn': self.turn_count,
            'gold': self.economy.resources.gold,
            'food': self.economy.resources.food,
            'population': self.population.population.total,
            'happiness': self.population.happiness,
            'military_power': self.military.get_total_power(),
            'sultan_loyalty': self.diplomacy.sultan_loyalty,
            'buildings': len(self.construction.buildings),
            'game_over': self.game_over,
            'is_coastal': self.province.is_coastal
        }
    
    def get_pending_raid_report(self):
        """Bekleyen akın raporu var mı?"""
        return self.warfare.pending_raid_report
    
    def consume_pending_raid_report(self):
        """Bekleyen akın raporunu al ve temizle"""
        report = self.warfare.pending_raid_report
        self.warfare.pending_raid_report = None
        return report
    
    def get_pending_siege_battle(self):
        """Bekleyen kuşatma savaşı var mı?"""
        return self.warfare.pending_siege_battle
    
    def consume_pending_siege_battle(self):
        """Bekleyen kuşatma savaşını al ve temizle"""
        battle = self.warfare.pending_siege_battle
        self.warfare.pending_siege_battle = None
        return battle
    
    def save_game(self, slot: int = None) -> bool:
        """
        Oyunu kaydet
        slot: 1, 2, veya 3. None ise mevcut slot veya otomatik atama.
        """
        # Slot belirleme
        if slot is None:
            if self.save_slot:
                slot = self.save_slot
            else:
                # Boş slot bul veya ilk slotu kullan
                slot = self._find_empty_slot() or 1
        
        self.save_slot = slot
        
        filepath = os.path.join(
            get_base_path(),
            'saves',
            f'slot_{slot}.json'
        )
        
        # Saves klasörünü oluştur
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        save_data = {
            'version': '1.1',  # Versiyon güncellendi
            'game_id': self.game_id,
            'save_slot': slot,
            'player': self.player.to_dict() if self.player else None,  # YENİ
            'province': {
                'name': self.province.name,
                'capital': self.province.capital,
                'region': self.province.region,
                'is_coastal': self.province.is_coastal
            },
            'time': {
                'year': self.current_year,
                'month': self.current_month,
                'day': self.current_day,
                'turn': self.turn_count
            },
            'economy': self.economy.to_dict(),
            'military': self.military.to_dict(),
            'population': self.population.to_dict(),
            'construction': self.construction.to_dict(),
            'diplomacy': self.diplomacy.to_dict(),
            'events': self.events.to_dict(),
            'warfare': self.warfare.to_dict(),
            'trade': self.trade.to_dict(),
            'workers': self.workers.to_dict(),
            'naval': self.naval.to_dict(),
            'artillery': self.artillery.to_dict(),
            'espionage': self.espionage.to_dict(),  # YENİ
            'religion': self.religion.to_dict(),    # YENİ
            'history': self.history.to_dict(),      # YENİ
        }
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, ensure_ascii=False, indent=2)
            
            self.audio.speak(f"Oyun Yuva {slot}'e kaydedildi.", interrupt=True)
            return True
        except Exception as e:
            self.audio.announce_action_result("Oyun kaydetme", False, str(e))
            return False
    
    def _find_empty_slot(self) -> int:
        """Boş kayıt yuvası bul"""
        for slot in [1, 2, 3]:
            filepath = os.path.join(
                get_base_path(),
                'saves',
                f'slot_{slot}.json'
            )
            if not os.path.exists(filepath):
                return slot
        return None
    
    def load_game(self, slot: int = None) -> bool:
        """
        Oyunu yükle
        slot: 1, 2, veya 3.
        """
        if slot is None:
            slot = 1
        
        filepath = os.path.join(
            get_base_path(),
            'saves',
            f'slot_{slot}.json'
        )
        
        if not os.path.exists(filepath):
            self.audio.speak(f"Yuva {slot}'de kayıt bulunamadı.", interrupt=True)
            return False
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                save_data = json.load(f)
            
            # Verileri yükle
            self.game_id = save_data.get('game_id', str(hash(filepath))[:8])
            self.save_slot = save_data.get('save_slot', slot)
            
            self.province.name = save_data['province']['name']
            self.province.capital = save_data['province']['capital']
            self.province.region = save_data['province']['region']
            self.province.is_coastal = save_data['province'].get('is_coastal', False)
            
            self.current_year = save_data['time']['year']
            self.current_month = save_data['time']['month']
            self.current_day = save_data['time'].get('day', 1)
            self.turn_count = save_data['time']['turn']
            
            self.economy = EconomySystem.from_dict(save_data['economy'])
            self.military = MilitarySystem.from_dict(save_data['military'])
            self.population = PopulationSystem.from_dict(save_data['population'])
            self.construction = ConstructionSystem.from_dict(save_data['construction'])
            self.diplomacy = DiplomacySystem.from_dict(save_data['diplomacy'])
            self.events = EventSystem.from_dict(save_data['events'])
            
            # Yeni sistemler (geriye uyumluluk için kontrol)
            if 'warfare' in save_data:
                self.warfare = WarfareSystem.from_dict(save_data['warfare'])
            if 'trade' in save_data:
                self.trade = TradeSystem.from_dict(save_data['trade'])
            if 'workers' in save_data:
                self.workers = WorkerSystem.from_dict(save_data['workers'])
            if 'naval' in save_data:
                self.naval = NavalSystem.from_dict(save_data['naval'])
            if 'artillery' in save_data:
                self.artillery = ArtillerySystem.from_dict(save_data['artillery'])
            if 'espionage' in save_data:  # YENİ
                self.espionage = EspionageSystem.from_dict(save_data['espionage'])
            if 'religion' in save_data:   # YENİ
                self.religion = ReligionSystem.from_dict(save_data['religion'])
            
            # Oyuncu karakteri yükle (YENİ)
            if 'player' in save_data and save_data['player']:
                from game.player import PlayerCharacter
                self.player = PlayerCharacter.from_dict(save_data['player'])
            else:
                # Eski kayıtlar için varsayılan karakter
                from game.player import create_default_character
                self.player = create_default_character()
            
            self.audio.speak(
                f"Yuva {slot} yüklendi. {self.province.name}, Yıl {self.current_year}.",
                interrupt=True
            )
            return True
            
        except Exception as e:
            self.audio.announce_action_result("Oyun yükleme", False, str(e))
            return False
    
    def get_save_slots_info(self) -> list:
        """Tüm kayıt yuvalarının bilgilerini al"""
        slots = []
        for slot in [1, 2, 3]:
            filepath = os.path.join(
                get_base_path(),
                'saves',
                f'slot_{slot}.json'
            )
            
            if os.path.exists(filepath):
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    slots.append({
                        'slot': slot,
                        'empty': False,
                        'province': data['province']['name'],
                        'year': data['time']['year'],
                        'turn': data['time']['turn'],
                        'game_id': data.get('game_id', 'unknown')
                    })
                except:
                    slots.append({'slot': slot, 'empty': True})
            else:
                slots.append({'slot': slot, 'empty': True})
        
        return slots
    
    def delete_save(self, slot: int) -> bool:
        """
        Kayıt yuvasını sil
        slot: 1, 2, veya 3
        Returns: True if deleted, False otherwise
        """
        if slot not in [1, 2, 3]:
            return False
        
        filepath = os.path.join(
            get_base_path(),
            'saves',
            f'slot_{slot}.json'
        )
        
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
                self.audio.announce_action_result(f"Yuva {slot} silme", True, "Kayıt silindi")
                return True
            except Exception as e:
                self.audio.announce_action_result(f"Yuva {slot} silme", False, str(e))
                return False
        else:
            self.audio.speak(f"Yuva {slot} zaten boş.", interrupt=True)
            return False
    
    def announce_full_status(self):
        """Tam durum duyurusu"""
        self.audio.speak(f"{self.province.name}, Yıl {self.current_year}", interrupt=True)
        self.economy.announce_summary()
        self.population.announce_status()
        self.military.announce_army()
        self.construction.announce_buildings()
        self.diplomacy.announce_status()
