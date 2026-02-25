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
    # Ticaret / Lojistik Gemileri
    MAVNA = "mavna"           # Ağır top taşıma + yük gemisi (dual-role)
    KALYON = "kalyon"         # Büyük ticaret gemisi
    FIRKATEYN = "firkateyn"   # Hızlı koruma gemisi
    
    # Savaş Gemileri
    KADIRGA = "kadirga"       # Kürekli savaş gemisi
    BASTARDA = "bastarda"     # Kapudan Paşa amiral gemisi (flagship)
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
    maintenance: int         # Günlük bakım maliyeti (altın)


# Tüm gemi tanımları
SHIP_DEFINITIONS: Dict[ShipType, ShipDefinition] = {
    ShipType.MAVNA: ShipDefinition(
        ship_type=ShipType.MAVNA,
        name="Mavna",
        description="İki direkli, geniş gövdeli ağır gemi — top taşıma ve yük lojistiği. "
                    "Kıyı bombardımanı ve kuşatma desteğinde kullanılır.",
        gold_cost=600,
        wood_cost=80,
        iron_cost=30,
        rope_cost=30,
        tar_cost=20,
        sailcloth_cost=20,
        build_time=5,
        crew_required=40,
        cargo_capacity=80,         # Yüksek yük + top kapasitesi
        combat_power=20,           # Top ateşi desteği — savaş rolü
        speed=3,                   # Ağır ve yavaş
        is_warship=True,           # Askeri rol de var
        maintenance=15             # Orta bakım
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
        is_warship=False,
        maintenance=15  # Büyük ticaret gemisi
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
        is_warship=True,
        maintenance=25  # Savaş gemisi, yüksek bakım
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
        is_warship=True,
        maintenance=50  # Büyük mürettebat
    ),
    
    ShipType.BASTARDA: ShipDefinition(
        ship_type=ShipType.BASTARDA,
        name="Baştarda",
        description="Kapudan Paşa'nın amiral gemisi — 26-36 oturak, kadırgadan büyük ve gösterişli. "
                    "Donanma savaşında moral etkisi sağlar.",
        gold_cost=4000,
        wood_cost=250,
        iron_cost=100,
        rope_cost=100,
        tar_cost=60,
        sailcloth_cost=50,
        build_time=15,
        crew_required=250,
        cargo_capacity=30,
        combat_power=80,           # Yüksek savaş gücü + moral bonusu
        speed=6,                   # Kadırgadan biraz yavaş
        is_warship=True,
        maintenance=60             # Amiral gemisi — yüksek bakım
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
        is_warship=True,
        maintenance=80  # En büyük gemi, en yüksek bakım
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
    max_health: int = 100
    bonus_speed: int = 0
    
    def get_definition(self) -> ShipDefinition:
        return SHIP_DEFINITIONS[self.ship_type]
    
    def get_combat_power(self) -> int:
        """Deneyimle artırılmış savaş gücü"""
        base = self.get_definition().combat_power
        health_mod = max(0.1, self.health / max(1, self.max_health))
        exp_bonus = base * (self.experience / 200)  # Max %50 bonus
        return int((base + exp_bonus) * health_mod)
        
    def get_speed(self) -> int:
        """Gemi hızı (Eklenti ve temel hızı toplar)"""
        return self.get_definition().speed + self.bonus_speed


@dataclass
class ShipConstruction:
    """İnşa halindeki gemi"""
    ship_type: ShipType
    turns_remaining: int
    custom_name: str = ""
    quality_bonus: int = 0
    durability_bonus: int = 0
    speed_bonus: int = 0

@dataclass
class ShipRepair:
    """Tamir edilen gemi"""
    ship: Ship
    turns_remaining: int
    gold_cost: int
    wood_cost: int


class NavalSystem:
    """Deniz kuvvetleri yönetim sistemi"""
    
    def __init__(self):
        self.ships: List[Ship] = []
        self.construction_queue: List[ShipConstruction] = []
        self.repair_queue: List[ShipRepair] = []
        self.total_ships_built: int = 0
        self.naval_victories: int = 0
        self.naval_defeats: int = 0
        self.ships_lost: int = 0
        
        # Audio
        self.audio = get_audio_manager()
    
    def can_build_ship(self, ship_type: ShipType, economy, construction_system=None) -> tuple:
        """Gemi inşa edilebilir mi?"""
        # Tersane kontrolü - Tersane olmadan gemi yapılamaz!
        if construction_system:
            from game.systems.construction import BuildingType
            if not construction_system.has_building(BuildingType.SHIPYARD):
                return False, "Tersane inşa edilmeden gemi yapılamaz!"
        
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
    
    def start_construction(self, ship_type: ShipType, economy, construction_system=None, custom_name: str = "") -> bool:
        """Gemi inşasını başlat"""
        can_build, reason = self.can_build_ship(ship_type, economy, construction_system)
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
        
        # Eklenti bonuslarını hesapla
        q_bonus = 0
        d_bonus = 0
        s_bonus = 0
        if construction_system:
            from game.systems.construction import BuildingType
            if construction_system.has_building(BuildingType.SHIPYARD):
                sy = construction_system.buildings[BuildingType.SHIPYARD]
                q_bonus += sy.get_unique_effect('ship_quality')
                d_bonus += sy.get_unique_effect('ship_durability')
                s_bonus += sy.get_unique_effect('ship_speed')
            if construction_system.has_building(BuildingType.ROPEMAKER):
                rm = construction_system.buildings[BuildingType.ROPEMAKER]
                q_bonus += rm.get_unique_effect('ship_quality')
                d_bonus += rm.get_unique_effect('ship_durability')
                s_bonus += rm.get_unique_effect('ship_speed')
        
        # Kuyruğa ekle
        self.construction_queue.append(ShipConstruction(
            ship_type=ship_type,
            turns_remaining=definition.build_time,
            custom_name=custom_name,
            quality_bonus=q_bonus,
            durability_bonus=d_bonus,
            speed_bonus=s_bonus
        ))
        
        self.audio.speak(
            f"{definition.name} inşası başladı! {definition.build_time} tur sürecek.",
            interrupt=True
        )
        return True
    
    def process_construction(self):
        """İnşaatları işle (her tur çağrılır)"""
        build_speed_mod = 1 # Placeholder for potential future modifiers
        # İnşa edilenler
        completed = []
        for construction in self.construction_queue:
            construction.turns_remaining -= int(1 * build_speed_mod)
            if construction.turns_remaining <= 0:
                completed.append(construction)
        
        for construction in completed:
            self.construction_queue.remove(construction)
            self._complete_ship(construction)
            
        # Tamir edilenler
        repaired = []
        for repair in self.repair_queue:
            repair.turns_remaining -= int(1 * build_speed_mod)
            if repair.turns_remaining <= 0:
                repaired.append(repair)
                
        for repair in repaired:
            self.repair_queue.remove(repair)
            repair.ship.health = repair.ship.max_health
            self.audio.speak(f"{repair.ship.name} isimli geminin tamiri tamamlandı, göreve hazır.", interrupt=False)
    
    def _complete_ship(self, construction: ShipConstruction):
        """Gemi inşasını tamamla"""
        definition = SHIP_DEFINITIONS[construction.ship_type]
        
        self.total_ships_built += 1
        ship_id = f"ship_{self.total_ships_built}"
        
        name = construction.custom_name or f"{definition.name} {self.total_ships_built}"
        
        # Bonusları entegre et: Quality->Experience, Durability->Max Health, Speed->Bonus Speed
        base_exp = construction.quality_bonus * 2
        base_dur = 100 + construction.durability_bonus
        
        ship = Ship(
            ship_id=ship_id,
            ship_type=construction.ship_type,
            name=name,
            experience=base_exp,
            max_health=base_dur,
            health=base_dur,
            bonus_speed=construction.speed_bonus
        )
        
        self.ships.append(ship)
        
        # Güçlendirilmiş bildirim
        self.audio.speak(
            f"🚢 GEMİ TAMAMLANDI! {name} denize indirildi! "
            f"Savaş gücü: {ship.get_combat_power()}, Hız: {ship.get_speed()}",
            interrupt=True
        )
    
    def get_fleet_power(self) -> int:
        """Toplam filo savaş gücü"""
        return sum(ship.get_combat_power() for ship in self.ships if ship.get_definition().is_warship)
    
    def get_trade_capacity(self) -> int:
        """Toplam ticaret kapasitesi"""
        return sum(ship.get_definition().cargo_capacity for ship in self.ships if not ship.get_definition().is_warship)
    
    def get_maintenance_cost(self) -> int:
        """Toplam filo bakım maliyeti"""
        return sum(ship.get_definition().maintenance for ship in self.ships)
    
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
        
    def repair_fleet(self, economy) -> tuple:
        """Toplu gemiyi tamir sırasına ekle"""
        # Formally already repairing ships shouldn't be queued again
        already_repairing = {r.ship.ship_id for r in self.repair_queue}
        damaged_ships = [s for s in self.ships if s.health < s.max_health and s.ship_id not in already_repairing]
        
        if not damaged_ships:
            if already_repairing:
                return False, "Hasarlı gemileriniz zaten şu an tersanede onarımda."
            return False, "Bütün gemiler zaten sapasağlam."
            
        total_missing_health = sum(s.max_health - s.health for s in damaged_ships)
        
        # Tamir maliyeti formülü
        gold_cost = int(total_missing_health * 1.5)
        wood_cost = int(total_missing_health * 0.5)
        
        if economy.resources.gold < gold_cost or economy.resources.wood < wood_cost:
            return False, f"Yetersiz kaynak. Tamir için {gold_cost} altın ve {wood_cost} kereste gerekli."
            
        economy.resources.gold -= gold_cost
        economy.resources.wood -= wood_cost
        
        # Tamir süreleri hasara ve gemi büyüklüğüne göre (min 1, max 7 tur)
        queued_count = 0
        max_turns = 1
        for ship in damaged_ships:
            def_speed = max(3, ship.get_definition().build_time // 3)
            damage_ratio = (ship.max_health - ship.health) / ship.max_health
            turns = max(1, int(def_speed * damage_ratio * 2))
            max_turns = max(max_turns, turns)
            
            self.repair_queue.append(ShipRepair(
                ship=ship,
                turns_remaining=turns,
                gold_cost=int((ship.max_health - ship.health) * 1.5),
                wood_cost=int((ship.max_health - ship.health) * 0.5)
            ))
            queued_count += 1
            
        return True, f"{gold_cost} altın ve {wood_cost} kereste harcanarak {queued_count} gemi onarım sırasına alındı. Onarımlar {max_turns} tur içinde tamamlanacak."
    
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
            "repair_queue": [
                {
                    "ship_id": r.ship.ship_id,
                    "turns_remaining": r.turns_remaining,
                    "gold_cost": r.gold_cost,
                    "wood_cost": r.wood_cost
                }
                for r in self.repair_queue
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
            
        for rep_data in data.get("repair_queue", []):
            # Eşleşen gemiyi bul
            matching_ship = next((s for s in system.ships if s.ship_id == rep_data["ship_id"]), None)
            if matching_ship:
                system.repair_queue.append(ShipRepair(
                    ship=matching_ship,
                    turns_remaining=rep_data["turns_remaining"],
                    gold_cost=rep_data.get("gold_cost", 0),
                    wood_cost=rep_data.get("wood_cost", 0)
                ))
        
        system.total_ships_built = data.get("total_ships_built", 0)
        system.naval_victories = data.get("naval_victories", 0)
        system.naval_defeats = data.get("naval_defeats", 0)
        system.ships_lost = data.get("ships_lost", 0)
        
        return system

    def conduct_raid(self, difficulty: str) -> dict:
        """
        Deniz akını düzenle
        difficulty: 'easy' (Ticaret Rotası), 'medium' (Sahil Kasabası), 'hard' (Liman Kalesi)
        """
        import random
        
        # Savaş gemilerini seç
        warships = [s for s in self.ships if s.get_definition().is_warship and s.health > 50]
        if not warships:
            return {'success': False, 'message': "Akın için savaşa hazır geminiz yok!"}
            
        fleet_power = sum(s.get_combat_power() for s in warships)
        
        targets = {
            'easy': {'name': 'Ticaret Rotası', 'power': 30, 'gold': (500, 1000), 'damage': (0, 10)},
            'medium': {'name': 'Sahil Kasabası', 'power': 80, 'gold': (1000, 2500), 'damage': (10, 30)},
            'hard': {'name': 'Liman Kalesi', 'power': 200, 'gold': (3000, 6000), 'damage': (20, 50)}
        }
        
        target = targets.get(difficulty, targets['easy'])
        enemy_power = target['power'] * random.uniform(0.8, 1.2)
        
        # Savaş sonucu
        success_chance = fleet_power / (fleet_power + enemy_power)
        roll = random.random()
        
        result = {'success': False, 'gold': 0, 'message': "", 'ships_lost': []}
        
        if roll < success_chance:
            # Zafer
            result['success'] = True
            result['gold'] = random.randint(*target['gold'])
            self.naval_victories += 1
            
            # Gemi deneyimi
            for ship in warships:
                ship.experience += random.randint(5, 15)
                
            result['message'] = f"ZAFER! {target['name']} yağmalandı. {result['gold']} altın kazanıldı."
        else:
            # Yenilgi
            self.naval_defeats += 1
            result['message'] = f"YENİLGİ! {target['name']} savunması yarılamadı."
        
        # Hasar hesaplama (her durumda hasar alınabilir)
        damage_roll = random.randint(*target['damage'])
        if not result['success']:
            damage_roll *= 1.5  # Yenilgide daha çok hasar
            
        loss_text = []
        for ship in warships:
            # Her gemiye hasar
            dmg = int(damage_roll * random.uniform(0.5, 1.5))
            ship.health -= dmg
            
            if ship.health <= 0:
                self.ships.remove(ship)
                self.ships_lost += 1
                result['ships_lost'].append(ship.name)
                loss_text.append(f"{ship.name} battı!")
            else:
                loss_text.append(f"{ship.name} -%{dmg} can")
                
        if loss_text:
            result['message'] += " Hasar: " + ", ".join(loss_text)
            
        return result
