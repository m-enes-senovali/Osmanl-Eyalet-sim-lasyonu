# -*- coding: utf-8 -*-
"""
Osmanlı Eyalet Yönetim Simülasyonu - Topçu Sistemi
Top üretimi ve topçu yönetimi (Topçu Ocağı)
"""

from dataclasses import dataclass, field
from typing import Dict, List
from enum import Enum
from audio.audio_manager import get_audio_manager


class CannonType(Enum):
    """Top türleri"""
    DARBZEN = "darbzen"       # Hafif top
    BALYEMEZ = "balyemez"     # Orta menzilli top
    KOLUNBURNA = "kolunburna" # Uzun menzilli top
    SAHI = "sahi"             # Kale yıkıcı bombard


@dataclass
class CannonDefinition:
    """Top tanımı"""
    cannon_type: CannonType
    name: str
    description: str
    
    # Maliyet
    gold_cost: int
    iron_cost: int
    stone_cost: int  # Mermi için taş
    
    # Özellikler
    build_time: int      # Tur sayısı
    crew_required: int   # Topçu sayısı
    power: int           # Savaş gücü
    range_level: int     # Menzil (1-10)
    siege_bonus: int     # Kuşatma bonusu
    maintenance: int     # Günlük bakım maliyeti (altın)


# Tüm top tanımları
CANNON_DEFINITIONS: Dict[CannonType, CannonDefinition] = {
    CannonType.DARBZEN: CannonDefinition(
        cannon_type=CannonType.DARBZEN,
        name="Darbzen",
        description="Hafif top, hızlı ateş, 0.15-2.5 kg mermi",
        gold_cost=200,
        iron_cost=20,
        stone_cost=5,
        build_time=2,
        crew_required=3,
        power=10,
        range_level=3,
        siege_bonus=5,
        maintenance=2  # Küçük top, düşük bakım
    ),
    
    CannonType.BALYEMEZ: CannonDefinition(
        cannon_type=CannonType.BALYEMEZ,
        name="Balyemez",
        description="Orta menzilli top, 31-74 kg mermi atar",
        gold_cost=500,
        iron_cost=50,
        stone_cost=15,
        build_time=4,
        crew_required=6,
        power=25,
        range_level=6,
        siege_bonus=15,
        maintenance=5  # Orta top
    ),
    
    CannonType.KOLUNBURNA: CannonDefinition(
        cannon_type=CannonType.KOLUNBURNA,
        name="Kolunburna",
        description="Uzun menzilli top (colubrina), 2-9 kg mermi",
        gold_cost=800,
        iron_cost=80,
        stone_cost=25,
        build_time=6,
        crew_required=8,
        power=40,
        range_level=9,
        siege_bonus=25,
        maintenance=8  # Hassas top, yüksek bakım
    ),
    
    CannonType.SAHI: CannonDefinition(
        cannon_type=CannonType.SAHI,
        name="Şahi",
        description="Kale yıkıcı bombard, 600+ kg mermi, İstanbul'un fatihi",
        gold_cost=2000,
        iron_cost=200,
        stone_cost=100,
        build_time=12,
        crew_required=20,
        power=100,
        range_level=5,  # Ağır olduğu için menzil düşük
        siege_bonus=80,
        maintenance=20  # Devasa top, yüksek bakım
    )
}


@dataclass
class Cannon:
    """Aktif top"""
    cannon_id: str
    cannon_type: CannonType
    name: str
    condition: int = 100  # Durum (0-100)
    shots_fired: int = 0
    
    def get_definition(self) -> CannonDefinition:
        return CANNON_DEFINITIONS[self.cannon_type]
    
    def get_power(self) -> int:
        """Duruma göre güç"""
        base = self.get_definition().power
        condition_mult = self.condition / 100
        return int(base * condition_mult)


@dataclass
class CannonProduction:
    """Üretim halindeki top"""
    cannon_type: CannonType
    turns_remaining: int
    custom_name: str = ""


class ArtillerySystem:
    """Topçu yönetim sistemi (Topçu Ocağı)"""
    
    def __init__(self):
        self.cannons: List[Cannon] = []
        self.production_queue: List[CannonProduction] = []
        self.total_cannons_produced: int = 0
        self.cannons_destroyed: int = 0
        
        # Audio
        self.audio = get_audio_manager()
    
    def can_produce_cannon(self, cannon_type: CannonType, economy) -> tuple:
        """Top üretilebilir mi?"""
        definition = CANNON_DEFINITIONS[cannon_type]
        res = economy.resources
        
        if res.gold < definition.gold_cost:
            return False, f"Yetersiz altın ({res.gold}/{definition.gold_cost})"
        if res.iron < definition.iron_cost:
            return False, f"Yetersiz demir ({res.iron}/{definition.iron_cost})"
        if res.stone < definition.stone_cost:
            return False, f"Yetersiz taş ({res.stone}/{definition.stone_cost})"
        
        return True, "Üretilebilir"
    
    def start_production(self, cannon_type: CannonType, economy, custom_name: str = "") -> bool:
        """Top üretimini başlat"""
        can_produce, reason = self.can_produce_cannon(cannon_type, economy)
        if not can_produce:
            self.audio.speak(f"Top üretilemedi: {reason}", interrupt=True)
            return False
        
        definition = CANNON_DEFINITIONS[cannon_type]
        
        # Kaynakları düş
        economy.resources.gold -= definition.gold_cost
        economy.resources.iron -= definition.iron_cost
        economy.resources.stone -= definition.stone_cost
        
        # Kuyruğa ekle
        self.production_queue.append(CannonProduction(
            cannon_type=cannon_type,
            turns_remaining=definition.build_time,
            custom_name=custom_name
        ))
        
        self.audio.speak(
            f"{definition.name} üretimi başladı! {definition.build_time} tur sürecek.",
            interrupt=True
        )
        return True
    
    def process_production(self):
        """Üretimi işle (her tur çağrılır)"""
        completed = []
        
        for production in self.production_queue:
            production.turns_remaining -= 1
            
            if production.turns_remaining <= 0:
                completed.append(production)
        
        for production in completed:
            self.production_queue.remove(production)
            self._complete_cannon(production)
    
    def _complete_cannon(self, production: CannonProduction):
        """Top üretimini tamamla"""
        definition = CANNON_DEFINITIONS[production.cannon_type]
        
        self.total_cannons_produced += 1
        cannon_id = f"cannon_{self.total_cannons_produced}"
        
        name = production.custom_name or f"{definition.name} #{self.total_cannons_produced}"
        
        cannon = Cannon(
            cannon_id=cannon_id,
            cannon_type=production.cannon_type,
            name=name
        )
        
        self.cannons.append(cannon)
        
        # Güçlendirilmiş bildirim
        self.audio.speak(
            f"🔫 TOP TAMAMLANDI! {name} topçu birliğine katıldı! "
            f"Güç: {definition.power}, Kuşatma bonusu: +{definition.siege_bonus}",
            interrupt=True
        )
    
    def get_total_power(self) -> int:
        """Toplam topçu gücü"""
        return sum(cannon.get_power() for cannon in self.cannons)
    
    def get_siege_bonus(self) -> int:
        """Toplam kuşatma bonusu"""
        return sum(cannon.get_definition().siege_bonus for cannon in self.cannons)
    
    def get_maintenance_cost(self) -> int:
        """Toplam topçu bakım maliyeti"""
        return sum(cannon.get_definition().maintenance for cannon in self.cannons)
    
    def get_cannon_counts(self) -> Dict[CannonType, int]:
        """Her türden kaç top var"""
        counts = {ct: 0 for ct in CannonType}
        for cannon in self.cannons:
            counts[cannon.cannon_type] += 1
        return counts
    
    def announce_artillery(self):
        """Topçu durumunu duyur"""
        if not self.cannons:
            self.audio.speak("Henüz topunuz yok. Topçu Ocağı'nda top üretebilirsiniz.", interrupt=True)
            return
        
        counts = self.get_cannon_counts()
        parts = []
        
        for cannon_type in CannonType:
            count = counts[cannon_type]
            if count > 0:
                name = CANNON_DEFINITIONS[cannon_type].name
                parts.append(f"{count} {name}")
        
        total_power = self.get_total_power()
        siege_bonus = self.get_siege_bonus()
        
        self.audio.speak(
            f"Topçu birliği: {', '.join(parts)}. "
            f"Toplam güç: {total_power}. "
            f"Kuşatma bonusu: +{siege_bonus}.",
            interrupt=True
        )
    
    def to_dict(self) -> Dict:
        """Kayıt için dictionary"""
        return {
            "cannons": [
                {
                    "cannon_id": c.cannon_id,
                    "cannon_type": c.cannon_type.value,
                    "name": c.name,
                    "condition": c.condition,
                    "shots_fired": c.shots_fired
                }
                for c in self.cannons
            ],
            "production_queue": [
                {
                    "cannon_type": p.cannon_type.value,
                    "turns_remaining": p.turns_remaining,
                    "custom_name": p.custom_name
                }
                for p in self.production_queue
            ],
            "total_cannons_produced": self.total_cannons_produced,
            "cannons_destroyed": self.cannons_destroyed
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ArtillerySystem':
        """Dictionary'den yükle"""
        system = cls()
        
        for cannon_data in data.get("cannons", []):
            cannon = Cannon(
                cannon_id=cannon_data["cannon_id"],
                cannon_type=CannonType(cannon_data["cannon_type"]),
                name=cannon_data["name"],
                condition=cannon_data.get("condition", 100),
                shots_fired=cannon_data.get("shots_fired", 0)
            )
            system.cannons.append(cannon)
        
        for prod_data in data.get("production_queue", []):
            production = CannonProduction(
                cannon_type=CannonType(prod_data["cannon_type"]),
                turns_remaining=prod_data["turns_remaining"],
                custom_name=prod_data.get("custom_name", "")
            )
            system.production_queue.append(production)
        
        system.total_cannons_produced = data.get("total_cannons_produced", 0)
        system.cannons_destroyed = data.get("cannons_destroyed", 0)
        
        return system
