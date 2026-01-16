# -*- coding: utf-8 -*-
"""
Osmanlı Eyalet Yönetim Simülasyonu - İnşaat Sistemi
"""

from dataclasses import dataclass
from typing import Dict, List, Optional
from enum import Enum
from audio.audio_manager import get_audio_manager


class BuildingType(Enum):
    """Bina tipleri"""
    MOSQUE = "mosque"              # Cami
    MEDRESE = "medrese"            # Medrese (eğitim)
    BARRACKS = "barracks"          # Kışla
    MARKET = "market"              # Pazar/Çarşı
    CARAVANSERAI = "caravanserai"  # Kervansaray
    HOSPITAL = "hospital"          # Darüşşifa (hastane)
    BATH = "bath"                  # Hamam
    FORTRESS = "fortress"          # Kale
    FARM = "farm"                  # Çiftlik
    MINE = "mine"                  # Maden
    LUMBER_MILL = "lumber_mill"    # Kereste Ocağı
    QUARRY = "quarry"              # Taş Ocağı
    WAREHOUSE = "warehouse"        # Ambar
    INN = "inn"                    # Han
    SHIPYARD = "shipyard"          # Tersane
    ARTILLERY_FOUNDRY = "artillery_foundry"  # Topçu Ocağı (YENİ)
    ROPEMAKER = "ropemaker"        # Urgan/Halat Atölyesi (YENİ)


@dataclass
class BuildingStats:
    """Bina istatistikleri"""
    name: str
    name_tr: str
    description: str
    cost_gold: int
    cost_wood: int
    cost_iron: int
    maintenance: int    # Tur başına bakım
    build_time: int     # İnşaat süresi (tur)
    max_level: int      # Maksimum yükseltme seviyesi
    
    # Etkiler
    happiness_bonus: int = 0
    trade_bonus: int = 0
    military_bonus: int = 0
    food_production: int = 0
    resource_production: Dict = None
    requires_coastal: bool = False  # Kıyı şehri gerektirir mi?


BUILDING_DEFINITIONS = {
    BuildingType.MOSQUE: BuildingStats(
        name="Mosque",
        name_tr="Cami",
        description="Halk memnuniyetini artırır",
        cost_gold=1000,
        cost_wood=200,
        cost_iron=50,
        maintenance=20,
        build_time=3,
        max_level=5,
        happiness_bonus=10
    ),
    BuildingType.MEDRESE: BuildingStats(
        name="Medrese",
        name_tr="Medrese",
        description="Eğitim ve kültür merkezi",
        cost_gold=800,
        cost_wood=150,
        cost_iron=30,
        maintenance=15,
        build_time=2,
        max_level=5,
        happiness_bonus=5
    ),
    BuildingType.BARRACKS: BuildingStats(
        name="Barracks",
        name_tr="Kışla",
        description="Asker eğitim süresini kısaltır",
        cost_gold=1500,
        cost_wood=300,
        cost_iron=200,
        maintenance=30,
        build_time=4,
        max_level=5,
        military_bonus=20
    ),
    BuildingType.MARKET: BuildingStats(
        name="Market",
        name_tr="Çarşı",
        description="Ticaret gelirini artırır",
        cost_gold=600,
        cost_wood=100,
        cost_iron=20,
        maintenance=10,
        build_time=2,
        max_level=5,
        trade_bonus=150  # Artırıldı: daha fazla ticaret geliri
    ),
    BuildingType.CARAVANSERAI: BuildingStats(
        name="Caravanserai",
        name_tr="Kervansaray",
        description="Kervan ticaretini geliştirir",
        cost_gold=1200,
        cost_wood=250,
        cost_iron=50,
        maintenance=25,
        build_time=3,
        max_level=5,
        trade_bonus=300  # Artırıldı: ana ticaret binası
    ),
    BuildingType.HOSPITAL: BuildingStats(
        name="Hospital",
        name_tr="Darüşşifa",
        description="Halk sağlığını artırır",
        cost_gold=1500,
        cost_wood=200,
        cost_iron=100,
        maintenance=35,
        build_time=4,
        max_level=5,
        happiness_bonus=10
    ),
    BuildingType.BATH: BuildingStats(
        name="Bath",
        name_tr="Hamam",
        description="Halk memnuniyetini artırır",
        cost_gold=400,
        cost_wood=80,
        cost_iron=20,
        maintenance=8,
        build_time=2,
        max_level=5,
        happiness_bonus=5
    ),
    BuildingType.FORTRESS: BuildingStats(
        name="Fortress",
        name_tr="Kale",
        description="Savunma gücünü artırır",
        cost_gold=3000,
        cost_wood=500,
        cost_iron=400,
        maintenance=50,
        build_time=6,
        max_level=5,
        military_bonus=50
    ),
    BuildingType.FARM: BuildingStats(
        name="Farm",
        name_tr="Çiftlik",
        description="Yiyecek üretir",
        cost_gold=300,
        cost_wood=150,
        cost_iron=10,
        maintenance=5,
        build_time=2,
        max_level=5,
        food_production=400
    ),
    BuildingType.MINE: BuildingStats(
        name="Mine",
        name_tr="Maden",
        description="Demir üretir",
        cost_gold=800,
        cost_wood=200,
        cost_iron=50,
        maintenance=20,
        build_time=3,
        max_level=5
    ),
    # YENİ BİNALAR
    BuildingType.LUMBER_MILL: BuildingStats(
        name="Lumber Mill",
        name_tr="Kereste Ocağı",
        description="Kereste üretir",
        cost_gold=500,
        cost_wood=50,
        cost_iron=100,
        maintenance=15,
        build_time=2,
        max_level=5
    ),
    BuildingType.QUARRY: BuildingStats(
        name="Quarry",
        name_tr="Taş Ocağı",
        description="Taş ve ek demir üretir",
        cost_gold=800,
        cost_wood=200,
        cost_iron=50,
        maintenance=20,
        build_time=3,
        max_level=5
    ),
    BuildingType.WAREHOUSE: BuildingStats(
        name="Warehouse",
        name_tr="Ambar",
        description="Kaynak kapasitesini artırır",
        cost_gold=400,
        cost_wood=300,
        cost_iron=50,
        maintenance=5,
        build_time=2,
        max_level=5
    ),
    BuildingType.INN: BuildingStats(
        name="Inn",
        name_tr="Han",
        description="Nüfus artışını hızlandırır",
        cost_gold=600,
        cost_wood=200,
        cost_iron=30,
        maintenance=12,
        build_time=2,
        max_level=5,
        happiness_bonus=3
    ),
    BuildingType.SHIPYARD: BuildingStats(
        name="Shipyard",
        name_tr="Tersane",
        description="Deniz ticareti ve askeri gemi (Kıyı şehri gerektirir)",
        cost_gold=2000,
        cost_wood=500,
        cost_iron=200,
        maintenance=40,
        build_time=5,
        max_level=5,
        trade_bonus=500,
        military_bonus=30,
        requires_coastal=True  # Sadece kıyı şehirlerinde
    ),
    BuildingType.ARTILLERY_FOUNDRY: BuildingStats(
        name="Artillery Foundry",
        name_tr="Topçu Ocağı",
        description="Top üretimi - Darbzen, Balyemez, Kolunburna ve Şahi topları",
        cost_gold=2500,
        cost_wood=300,
        cost_iron=400,
        maintenance=50,
        build_time=6,
        max_level=5,
        military_bonus=50
    ),
    BuildingType.ROPEMAKER: BuildingStats(
        name="Ropemaker",
        name_tr="Halat Atölyesi",
        description="Halat, katran ve yelken bezi üretir (Gemi yapımı için)",
        cost_gold=800,
        cost_wood=200,
        cost_iron=30,
        maintenance=15,
        build_time=3,
        max_level=5,
        resource_production={'rope': 10, 'tar': 5, 'sailcloth': 3}
    ),
}


@dataclass
class Building:
    """İnşa edilmiş bina"""
    building_type: BuildingType
    level: int = 1
    under_construction: bool = False
    construction_turns: int = 0
    
    def get_stats(self) -> BuildingStats:
        return BUILDING_DEFINITIONS[self.building_type]
    
    def get_effective_bonus(self, bonus_type: str) -> int:
        """Seviye bazlı etkin bonusu al"""
        stats = self.get_stats()
        base = getattr(stats, bonus_type, 0)
        return int(base * (1 + (self.level - 1) * 0.5))  # Her seviye %50 artış


@dataclass
class ConstructionQueue:
    """İnşaat kuyruğu öğesi"""
    building_type: BuildingType
    turns_remaining: int
    is_upgrade: bool = False


class ConstructionSystem:
    """İnşaat yönetim sistemi"""
    
    def __init__(self):
        # Mevcut binalar
        self.buildings: Dict[BuildingType, Building] = {}
        
        # İnşaat kuyruğu
        self.construction_queue: List[ConstructionQueue] = []
        
        # Başlangıç binaları
        self._initialize_starting_buildings()
    
    def _initialize_starting_buildings(self):
        """Başlangıç binalarını oluştur"""
        # Her eyalet bir cami ve çiftlik ile başlar
        self.buildings[BuildingType.MOSQUE] = Building(BuildingType.MOSQUE, level=1)
        self.buildings[BuildingType.FARM] = Building(BuildingType.FARM, level=1)
    
    def has_building(self, building_type: BuildingType) -> bool:
        """Bina var mı?"""
        return building_type in self.buildings
    
    def get_building_level(self, building_type: BuildingType) -> int:
        """Bina seviyesini al"""
        if building_type in self.buildings:
            return self.buildings[building_type].level
        return 0
    
    def can_build(self, building_type: BuildingType, economy, is_coastal: bool = False) -> tuple:
        """
        İnşa edilebilir mi kontrol et
        Returns: (can_build: bool, reason: str)
        """
        # Zaten var mı?
        if building_type in self.buildings:
            return False, "Bu bina zaten mevcut"
        
        # İnşaat kuyruğunda mı?
        for item in self.construction_queue:
            if item.building_type == building_type:
                return False, "Bu bina zaten inşa ediliyor"
        
        # Kaynak kontrolü
        stats = BUILDING_DEFINITIONS[building_type]
        
        # Kıyı şehri kontrolü (Tersane için)
        if stats.requires_coastal and not is_coastal:
            return False, "Bu bina sadece kıyı şehirlerinde inşa edilebilir"
        
        if not economy.can_afford(
            gold=stats.cost_gold,
            wood=stats.cost_wood,
            iron=stats.cost_iron
        ):
            return False, "Yetersiz kaynak"
        
        return True, ""
    
    def can_upgrade(self, building_type: BuildingType, economy) -> tuple:
        """
        Yükseltilebilir mi kontrol et
        Returns: (can_upgrade: bool, reason: str)
        """
        if building_type not in self.buildings:
            return False, "Bina mevcut değil"
        
        building = self.buildings[building_type]
        stats = building.get_stats()
        
        if building.level >= stats.max_level:
            return False, "Maksimum seviyeye ulaşıldı"
        
        # Yükseltme maliyeti (seviye * temel maliyet)
        multiplier = building.level + 1
        if not economy.can_afford(
            gold=int(stats.cost_gold * multiplier * 0.5),
            wood=int(stats.cost_wood * multiplier * 0.5),
            iron=int(stats.cost_iron * multiplier * 0.5)
        ):
            return False, "Yetersiz kaynak"
        
        return True, ""
    
    def start_construction(self, building_type: BuildingType, economy, is_coastal: bool = False) -> bool:
        """İnşaata başla"""
        can, reason = self.can_build(building_type, economy, is_coastal)
        if not can:
            audio = get_audio_manager()
            audio.announce_action_result("İnşaat", False, reason)
            return False
        
        stats = BUILDING_DEFINITIONS[building_type]
        
        # Kaynakları harca
        economy.spend(
            gold=stats.cost_gold,
            wood=stats.cost_wood,
            iron=stats.cost_iron
        )
        
        # Kuyruğa ekle
        self.construction_queue.append(ConstructionQueue(
            building_type=building_type,
            turns_remaining=stats.build_time
        ))
        
        audio = get_audio_manager()
        audio.play_ui_sound('build')  # İnşaat sesi
        audio.announce_action_result(
            f"{stats.name_tr} inşaatı",
            True,
            f"{stats.build_time} tur sonra tamamlanacak"
        )
        
        return True
    
    def start_upgrade(self, building_type: BuildingType, economy) -> bool:
        """Yükseltme başlat"""
        can, reason = self.can_upgrade(building_type, economy)
        if not can:
            audio = get_audio_manager()
            audio.announce_action_result("Yükseltme", False, reason)
            return False
        
        building = self.buildings[building_type]
        stats = building.get_stats()
        
        # Yükseltme maliyeti
        multiplier = building.level + 1
        economy.spend(
            gold=int(stats.cost_gold * multiplier * 0.5),
            wood=int(stats.cost_wood * multiplier * 0.5),
            iron=int(stats.cost_iron * multiplier * 0.5)
        )
        
        # Kuyruğa ekle
        self.construction_queue.append(ConstructionQueue(
            building_type=building_type,
            turns_remaining=max(1, stats.build_time // 2),
            is_upgrade=True
        ))
        
        audio = get_audio_manager()
        audio.announce_action_result(
            f"{stats.name_tr} yükseltme",
            True,
            f"Seviye {building.level + 1}'e yükseltiliyor"
        )
        
        return True
    
    def process_turn(self):
        """Tur sonunda inşaatları işle"""
        completed = []
        
        for item in self.construction_queue:
            item.turns_remaining -= 1
            if item.turns_remaining <= 0:
                completed.append(item)
        
        # Tamamlananları işle
        for item in completed:
            self.construction_queue.remove(item)
            stats = BUILDING_DEFINITIONS[item.building_type]
            audio = get_audio_manager()
            
            if item.is_upgrade:
                if item.building_type in self.buildings:
                    self.buildings[item.building_type].level += 1
                    new_level = self.buildings[item.building_type].level
                    audio.play_ui_sound('complete')  # Tamamlandı sesi
                    audio.announce(f"{stats.name_tr} Seviye {new_level}'e yükseltildi!")
            else:
                self.buildings[item.building_type] = Building(item.building_type, level=1)
                audio.play_ui_sound('complete')  # Tamamlandı sesi
                audio.announce(f"{stats.name_tr} tamamlandı!")
    
    def get_total_maintenance(self) -> int:
        """Toplam bina bakım maliyeti"""
        total = 0
        for building in self.buildings.values():
            stats = building.get_stats()
            total += stats.maintenance * building.level
        return total
    
    def get_total_happiness_bonus(self) -> int:
        """Toplam mutluluk bonusu"""
        total = 0
        for building in self.buildings.values():
            total += building.get_effective_bonus('happiness_bonus')
        return total
    
    def get_total_trade_bonus(self) -> int:
        """Toplam ticaret bonusu"""
        total = 0
        for building in self.buildings.values():
            total += building.get_effective_bonus('trade_bonus')
        return total
    
    def get_total_military_bonus(self) -> int:
        """Toplam askeri bonus"""
        total = 0
        for building in self.buildings.values():
            total += building.get_effective_bonus('military_bonus')
        return total
    
    def get_food_production(self) -> int:
        """Toplam yiyecek üretimi"""
        total = 0
        for building in self.buildings.values():
            total += building.get_effective_bonus('food_production')
        return total
    
    def get_wood_production(self) -> int:
        """Toplam kereste üretimi (Kereste Ocağından)"""
        if BuildingType.LUMBER_MILL in self.buildings:
            building = self.buildings[BuildingType.LUMBER_MILL]
            return 300 * building.level  # Seviye başına 300 kereste
        return 0
    
    def get_iron_production(self) -> int:
        """Toplam demir üretimi (Maden ve Taş Ocağından)"""
        total = 0
        
        # Maden
        if BuildingType.MINE in self.buildings:
            building = self.buildings[BuildingType.MINE]
            total += 150 * building.level  # Seviye başına 150 demir
        
        # Taş Ocağı (ek demir)
        if BuildingType.QUARRY in self.buildings:
            building = self.buildings[BuildingType.QUARRY]
            total += 100 * building.level  # Seviye başına 100 ek demir
        
        return total
    
    def get_population_growth_bonus(self) -> float:
        """Han'dan nüfus artış bonusu"""
        if BuildingType.INN in self.buildings:
            building = self.buildings[BuildingType.INN]
            return 0.01 * building.level  # Seviye başına +1% nüfus artışı
        return 0.0
    
    def get_building_list(self) -> List[tuple]:
        """Bina listesi [(tip, isim, seviye), ...]"""
        result = []
        for building_type, building in self.buildings.items():
            stats = building.get_stats()
            result.append((building_type, stats.name_tr, building.level))
        return result
    
    def get_available_buildings(self) -> List[BuildingType]:
        """İnşa edilebilir binalar"""
        available = []
        for building_type in BuildingType:
            if building_type not in self.buildings:
                in_queue = any(
                    item.building_type == building_type 
                    for item in self.construction_queue
                )
                if not in_queue:
                    available.append(building_type)
        return available
    
    def announce_buildings(self):
        """Bina durumunu ekran okuyucuya duyur"""
        audio = get_audio_manager()
        audio.speak("Binalar", interrupt=True)
        
        if not self.buildings:
            audio.speak("Henüz bina yok")
            return
        
        for building_type, building in self.buildings.items():
            stats = building.get_stats()
            audio.speak(f"{stats.name_tr}, Seviye {building.level}")
        
        if self.construction_queue:
            audio.speak("İnşaat halinde:")
            for item in self.construction_queue:
                stats = BUILDING_DEFINITIONS[item.building_type]
                action = "yükseltiliyor" if item.is_upgrade else "inşa ediliyor"
                audio.speak(f"{stats.name_tr} {action}, {item.turns_remaining} tur kaldı")
    
    def to_dict(self) -> Dict:
        """Kayıt için dictionary'e dönüştür"""
        return {
            'buildings': {
                k.value: {'level': v.level}
                for k, v in self.buildings.items()
            },
            'construction_queue': [
                {
                    'type': item.building_type.value,
                    'turns': item.turns_remaining,
                    'is_upgrade': item.is_upgrade
                }
                for item in self.construction_queue
            ]
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ConstructionSystem':
        """Dictionary'den yükle"""
        system = cls()
        system.buildings = {
            BuildingType(k): Building(BuildingType(k), level=v['level'])
            for k, v in data['buildings'].items()
        }
        system.construction_queue = [
            ConstructionQueue(
                BuildingType(item['type']),
                item['turns'],
                item.get('is_upgrade', False)
            )
            for item in data['construction_queue']
        ]
        return system
