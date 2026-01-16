# -*- coding: utf-8 -*-
"""
Osmanlı Eyalet Yönetim Simülasyonu - Deniz Kuvvetleri Sistemi
Gemi inşası, deniz ticareti ve deniz savaşları
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from enum import Enum
from audio.audio_manager import get_audio_manager


class ShipType(Enum):
    """Gemi türleri"""
    # Ticaret Gemileri
    MAVNA = "mavna"           # Küçük yük gemisi
    KALYON = "kalyon"         # Büyük ticaret gemisi
    FIRKATEYN = "firkateyn"   # Hızlı koruma gemisi
    
    # Savaş Gemileri
    KADIRGA = "kadirga"       # Kürekli savaş gemisi
    MAHON = "mahon"           # Ağır savaş gemisi (galleass)


@dataclass
class ShipDefinition:
    """Gemi tanımı"""
    ship_type: ShipType
    name: str
    description: str
    
    # Maliyet
    gold_cost: int
    wood_cost: int
    iron_cost: int
    rope_cost: int
    tar_cost: int
    sailcloth_cost: int
    
    # Özellikler
    build_time: int          # Tur sayısı
    crew_required: int       # Mürettebat
    cargo_capacity: int      # Yük kapasitesi (ticaret için)
    combat_power: int        # Savaş gücü
    speed: int               # Hız (1-10)
    is_warship: bool         # Savaş gemisi mi?


# Tüm gemi tanımları
SHIP_DEFINITIONS: Dict[ShipType, ShipDefinition] = {
    ShipType.MAVNA: ShipDefinition(
        ship_type=ShipType.MAVNA,
        name="Mavna",
        description="Küçük yük gemisi, kısa mesafe kıyı ticareti için ideal",
        gold_cost=500,
        wood_cost=50,
        iron_cost=10,
        rope_cost=20,
        tar_cost=15,
        sailcloth_cost=10,
        build_time=3,
        crew_required=15,
        cargo_capacity=50,
        combat_power=0,
        speed=4,
        is_warship=False
    ),
    
    ShipType.KALYON: ShipDefinition(
        ship_type=ShipType.KALYON,
        name="Kalyon",
        description="Büyük ticaret gemisi, uzun mesafe deniz ticareti için",
        gold_cost=1500,
        wood_cost=150,
        iron_cost=30,
        rope_cost=60,
        tar_cost=40,
        sailcloth_cost=50,
        build_time=7,
        crew_required=40,
        cargo_capacity=200,
        combat_power=5,
        speed=6,
        is_warship=False
    ),
    
    ShipType.FIRKATEYN: ShipDefinition(
        ship_type=ShipType.FIRKATEYN,
        name="Firkateyn",
        description="Hızlı koruma gemisi, ticaret kervanlarını korur",
        gold_cost=2000,
        wood_cost=100,
        iron_cost=50,
        rope_cost=50,
        tar_cost=30,
        sailcloth_cost=40,
        build_time=10,
        crew_required=60,
        cargo_capacity=30,
        combat_power=25,
        speed=8,
        is_warship=True
    ),
    
    ShipType.KADIRGA: ShipDefinition(
        ship_type=ShipType.KADIRGA,
        name="Kadırga",
        description="Kürekli savaş gemisi, 150 kürekçi, Akdeniz'in hakimi",
        gold_cost=3000,
        wood_cost=200,
        iron_cost=80,
        rope_cost=80,
        tar_cost=50,
        sailcloth_cost=30,
        build_time=12,
        crew_required=200,  # Kürekçiler dahil
        cargo_capacity=20,
        combat_power=50,
        speed=7,
        is_warship=True
    ),
    
    ShipType.MAHON: ShipDefinition(
        ship_type=ShipType.MAHON,
        name="Mahon",
        description="Ağır savaş gemisi (galleass), 32 kürek, topçu güvertesi",
        gold_cost=5000,
        wood_cost=300,
        iron_cost=150,
        rope_cost=120,
        tar_cost=80,
        sailcloth_cost=80,
        build_time=20,
        crew_required=300,
        cargo_capacity=50,
        combat_power=100,
        speed=5,
        is_warship=True
    )
}


@dataclass
class Ship:
    """Aktif gemi"""
    ship_id: str
    ship_type: ShipType
    name: str
    health: int = 100
    experience: int = 0
    
    def get_definition(self) -> ShipDefinition:
        return SHIP_DEFINITIONS[self.ship_type]
    
    def get_combat_power(self) -> int:
        """Deneyimle artırılmış savaş gücü"""
        base = self.get_definition().combat_power
        exp_bonus = base * (self.experience / 200)  # Max %50 bonus
        return int(base + exp_bonus)


@dataclass
class ShipConstruction:
    """İnşa halindeki gemi"""
    ship_type: ShipType
    turns_remaining: int
    custom_name: str = ""


class NavalSystem:
    """Deniz kuvvetleri yönetim sistemi"""
    
    def __init__(self):
        self.ships: List[Ship] = []
        self.construction_queue: List[ShipConstruction] = []
        self.total_ships_built: int = 0
        self.naval_victories: int = 0
        self.naval_defeats: int = 0
        self.ships_lost: int = 0
        
        # Audio
        self.audio = get_audio_manager()
    
    def can_build_ship(self, ship_type: ShipType, economy) -> tuple:
        """Gemi inşa edilebilir mi?"""
        definition = SHIP_DEFINITIONS[ship_type]
        res = economy.resources
        
        if res.gold < definition.gold_cost:
            return False, f"Yetersiz altın ({res.gold}/{definition.gold_cost})"
        if res.wood < definition.wood_cost:
            return False, f"Yetersiz kereste ({res.wood}/{definition.wood_cost})"
        if res.iron < definition.iron_cost:
            return False, f"Yetersiz demir ({res.iron}/{definition.iron_cost})"
        if res.rope < definition.rope_cost:
            return False, f"Yetersiz halat ({res.rope}/{definition.rope_cost})"
        if res.tar < definition.tar_cost:
            return False, f"Yetersiz katran ({res.tar}/{definition.tar_cost})"
        if res.sailcloth < definition.sailcloth_cost:
            return False, f"Yetersiz yelken bezi ({res.sailcloth}/{definition.sailcloth_cost})"
        
        return True, "İnşa edilebilir"
    
    def start_construction(self, ship_type: ShipType, economy, custom_name: str = "") -> bool:
        """Gemi inşasını başlat"""
        can_build, reason = self.can_build_ship(ship_type, economy)
        if not can_build:
            self.audio.speak(f"Gemi inşa edilemedi: {reason}", interrupt=True)
            return False
        
        definition = SHIP_DEFINITIONS[ship_type]
        
        # Kaynakları düş
        economy.resources.gold -= definition.gold_cost
        economy.resources.wood -= definition.wood_cost
        economy.resources.iron -= definition.iron_cost
        economy.resources.rope -= definition.rope_cost
        economy.resources.tar -= definition.tar_cost
        economy.resources.sailcloth -= definition.sailcloth_cost
        
        # Kuyruğa ekle
        self.construction_queue.append(ShipConstruction(
            ship_type=ship_type,
            turns_remaining=definition.build_time,
            custom_name=custom_name
        ))
        
        self.audio.speak(
            f"{definition.name} inşası başladı! {definition.build_time} tur sürecek.",
            interrupt=True
        )
        return True
    
    def process_construction(self):
        """İnşaatları işle (her tur çağrılır)"""
        completed = []
        
        for construction in self.construction_queue:
            construction.turns_remaining -= 1
            
            if construction.turns_remaining <= 0:
                completed.append(construction)
        
        for construction in completed:
            self.construction_queue.remove(construction)
            self._complete_ship(construction)
    
    def _complete_ship(self, construction: ShipConstruction):
        """Gemi inşasını tamamla"""
        definition = SHIP_DEFINITIONS[construction.ship_type]
        
        self.total_ships_built += 1
        ship_id = f"ship_{self.total_ships_built}"
        
        name = construction.custom_name or f"{definition.name} #{self.total_ships_built}"
        
        ship = Ship(
            ship_id=ship_id,
            ship_type=construction.ship_type,
            name=name
        )
        
        self.ships.append(ship)
        
        # Güçlendirilmiş bildirim
        self.audio.speak(
            f"🚢 GEMİ TAMAMLANDI! {name} denize indirildi! "
            f"Savaş gücü: {definition.combat_power}, Hız: {definition.speed}",
            interrupt=True
        )
    
    def get_fleet_power(self) -> int:
        """Toplam filo savaş gücü"""
        return sum(ship.get_combat_power() for ship in self.ships if ship.get_definition().is_warship)
    
    def get_trade_capacity(self) -> int:
        """Toplam ticaret kapasitesi"""
        return sum(ship.get_definition().cargo_capacity for ship in self.ships if not ship.get_definition().is_warship)
    
    def get_ship_counts(self) -> Dict[ShipType, int]:
        """Her türden kaç gemi var"""
        counts = {st: 0 for st in ShipType}
        for ship in self.ships:
            counts[ship.ship_type] += 1
        return counts
    
    def announce_fleet(self):
        """Filo durumunu duyur"""
        if not self.ships:
            self.audio.speak("Henüz geminiz yok. Tersane'de gemi inşa edebilirsiniz.", interrupt=True)
            return
        
        counts = self.get_ship_counts()
        parts = []
        
        for ship_type in ShipType:
            count = counts[ship_type]
            if count > 0:
                name = SHIP_DEFINITIONS[ship_type].name
                parts.append(f"{count} {name}")
        
        total_power = self.get_fleet_power()
        trade_cap = self.get_trade_capacity()
        
        self.audio.speak(
            f"Filo: {', '.join(parts)}. "
            f"Toplam savaş gücü: {total_power}. "
            f"Ticaret kapasitesi: {trade_cap}.",
            interrupt=True
        )
    
    def to_dict(self) -> Dict:
        """Kayıt için dictionary"""
        return {
            "ships": [
                {
                    "ship_id": s.ship_id,
                    "ship_type": s.ship_type.value,
                    "name": s.name,
                    "health": s.health,
                    "experience": s.experience
                }
                for s in self.ships
            ],
            "construction_queue": [
                {
                    "ship_type": c.ship_type.value,
                    "turns_remaining": c.turns_remaining,
                    "custom_name": c.custom_name
                }
                for c in self.construction_queue
            ],
            "total_ships_built": self.total_ships_built,
            "naval_victories": self.naval_victories,
            "naval_defeats": self.naval_defeats,
            "ships_lost": self.ships_lost
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'NavalSystem':
        """Dictionary'den yükle"""
        system = cls()
        
        for ship_data in data.get("ships", []):
            ship = Ship(
                ship_id=ship_data["ship_id"],
                ship_type=ShipType(ship_data["ship_type"]),
                name=ship_data["name"],
                health=ship_data.get("health", 100),
                experience=ship_data.get("experience", 0)
            )
            system.ships.append(ship)
        
        for const_data in data.get("construction_queue", []):
            construction = ShipConstruction(
                ship_type=ShipType(const_data["ship_type"]),
                turns_remaining=const_data["turns_remaining"],
                custom_name=const_data.get("custom_name", "")
            )
            system.construction_queue.append(construction)
        
        system.total_ships_built = data.get("total_ships_built", 0)
        system.naval_victories = data.get("naval_victories", 0)
        system.naval_defeats = data.get("naval_defeats", 0)
        system.ships_lost = data.get("ships_lost", 0)
        
        return system
