# -*- coding: utf-8 -*-
"""
Osmanlı Eyalet Yönetim Simülasyonu - Askeri Sistem
"""

from dataclasses import dataclass
from typing import Dict, List
from enum import Enum
from audio.audio_manager import get_audio_manager


class UnitType(Enum):
    """Asker tipleri"""
    SIPAHI = "sipahi"           # Atlı birlik
    YENICHERI = "yenicheri"     # Yeniçeri
    AZAP = "azap"               # Hafif piyade
    TOPCU = "topcu"             # Topçu
    AKINCI = "akinci"           # Akıncı (keşif)


@dataclass
class UnitStats:
    """Birim istatistikleri"""
    name: str
    name_tr: str
    attack: int
    defense: int
    speed: int
    cost_gold: int
    cost_food: int
    maintenance: int  # Tur başına bakım
    train_time: int   # Eğitim süresi (tur)
    
    
UNIT_DEFINITIONS = {
    UnitType.SIPAHI: UnitStats(
        name="Sipahi",
        name_tr="Sipahi",
        attack=15,
        defense=10,
        speed=8,
        cost_gold=150,
        cost_food=50,
        maintenance=5,
        train_time=2
    ),
    UnitType.YENICHERI: UnitStats(
        name="Janissary",
        name_tr="Yeniçeri",
        attack=20,
        defense=15,
        speed=4,
        cost_gold=200,
        cost_food=80,
        maintenance=8,
        train_time=3
    ),
    UnitType.AZAP: UnitStats(
        name="Azap",
        name_tr="Azap",
        attack=8,
        defense=5,
        speed=5,
        cost_gold=50,
        cost_food=30,
        maintenance=2,
        train_time=1
    ),
    UnitType.TOPCU: UnitStats(
        name="Artillery",
        name_tr="Topçu",
        attack=30,
        defense=5,
        speed=2,
        cost_gold=500,
        cost_food=100,
        maintenance=15,
        train_time=4
    ),
    UnitType.AKINCI: UnitStats(
        name="Akinci",
        name_tr="Akıncı",
        attack=10,
        defense=3,
        speed=10,
        cost_gold=80,
        cost_food=40,
        maintenance=3,
        train_time=1
    ),
}


@dataclass
class TrainingQueue:
    """Eğitim kuyruğu öğesi"""
    unit_type: UnitType
    count: int
    turns_remaining: int


class MilitarySystem:
    """Askeri yönetim sistemi"""
    
    def __init__(self):
        # Mevcut birlikler
        self.units: Dict[UnitType, int] = {
            UnitType.SIPAHI: 50,
            UnitType.YENICHERI: 30,
            UnitType.AZAP: 100,
            UnitType.TOPCU: 5,
            UnitType.AKINCI: 20,
        }
        
        # Eğitim kuyruğu
        self.training_queue: List[TrainingQueue] = []
        
        # Savaş durumu
        self.at_war = False
        self.war_target = None
        self.morale = 100  # Moral 0-100
        self.experience = 0  # Deneyim 0-100
        
        # Kayıplar (istatistik için)
        self.total_losses = 0
        self.total_victories = 0
    
    def get_total_soldiers(self) -> int:
        """Toplam asker sayısı"""
        return sum(self.units.values())
    
    def get_total_power(self) -> int:
        """Toplam askeri güç"""
        power = 0
        for unit_type, count in self.units.items():
            stats = UNIT_DEFINITIONS[unit_type]
            power += count * (stats.attack + stats.defense)
        return power
    
    def get_maintenance_cost(self) -> int:
        """Toplam bakım maliyeti"""
        cost = 0
        for unit_type, count in self.units.items():
            stats = UNIT_DEFINITIONS[unit_type]
            cost += count * stats.maintenance
        return cost
    
    @property
    def infantry(self) -> int:
        """Toplam piyade sayısı (Yeniçeri + Azap)"""
        return self.units.get(UnitType.YENICHERI, 0) + self.units.get(UnitType.AZAP, 0)
    
    @property
    def cavalry(self) -> int:
        """Toplam süvari sayısı (Sipahi)"""
        return self.units.get(UnitType.SIPAHI, 0)
    
    @property
    def artillery_crew(self) -> int:
        """Toplam topçu mürettebatı sayısı"""
        return self.units.get(UnitType.TOPCU, 0)
    
    @property
    def raiders(self) -> int:
        """Toplam akıncı sayısı"""
        return self.units.get(UnitType.AKINCI, 0)
    
    def can_recruit(self, unit_type: UnitType, count: int, economy) -> tuple:
        """
        Asker alabilir mi kontrol et
        Returns: (can_recruit: bool, reason: str)
        """
        stats = UNIT_DEFINITIONS[unit_type]
        total_gold = stats.cost_gold * count
        total_food = stats.cost_food * count
        
        if not economy.can_afford(gold=total_gold, food=total_food):
            return False, "Yetersiz kaynak"
        
        return True, ""
    
    def recruit(self, unit_type: UnitType, count: int, economy) -> bool:
        """Asker topla ve eğitime al"""
        can, reason = self.can_recruit(unit_type, count, economy)
        if not can:
            audio = get_audio_manager()
            audio.announce_action_result("Asker toplama", False, reason)
            return False
        
        stats = UNIT_DEFINITIONS[unit_type]
        total_gold = stats.cost_gold * count
        total_food = stats.cost_food * count
        
        # Kaynakları harca
        economy.spend(gold=total_gold, food=total_food)
        
        # Eğitim kuyruğuna ekle
        self.training_queue.append(TrainingQueue(
            unit_type=unit_type,
            count=count,
            turns_remaining=stats.train_time
        ))
        
        audio = get_audio_manager()
        audio.announce_action_result(
            f"{stats.name_tr} toplama",
            True,
            f"{count} {stats.name_tr} eğitime alındı. {stats.train_time} tur sonra hazır."
        )
        
        return True
    
    def process_turn(self):
        """Tur sonunda eğitimleri işle"""
        completed = []
        
        for item in self.training_queue:
            item.turns_remaining -= 1
            if item.turns_remaining <= 0:
                self.units[item.unit_type] += item.count
                completed.append(item)
        
        # Tamamlananları kaldır
        for item in completed:
            self.training_queue.remove(item)
            audio = get_audio_manager()
            stats = UNIT_DEFINITIONS[item.unit_type]
            audio.announce(f"{item.count} {stats.name_tr} eğitimini tamamladı!")
        
        # Moral düzeltme
        if self.morale < 100:
            self.morale = min(100, self.morale + 5)
    
    def fight_bandits(self) -> dict:
        """Eşkıya/isyan bastırma savaşı"""
        total_power = self.get_total_power()
        bandit_power = 100 + (self.get_total_soldiers() // 10)
        
        # Basit savaş hesabı
        victory = total_power > bandit_power * 1.2
        
        result = {
            'victory': victory,
            'our_power': total_power,
            'enemy_power': bandit_power,
            'losses': {}
        }
        
        if victory:
            # Küçük kayıplar
            for unit_type in self.units:
                if self.units[unit_type] > 0:
                    loss = max(1, self.units[unit_type] // 20)
                    self.units[unit_type] -= loss
                    result['losses'][unit_type.value] = loss
            self.total_victories += 1
            self.morale = min(100, self.morale + 10)
        else:
            # Büyük kayıplar
            for unit_type in self.units:
                if self.units[unit_type] > 0:
                    loss = max(1, self.units[unit_type] // 5)
                    self.units[unit_type] -= loss
                    result['losses'][unit_type.value] = loss
            self.total_losses += 1
            self.morale = max(0, self.morale - 20)
        
        return result
    
    def get_army_info(self) -> List[tuple]:
        """Ordu bilgisi listesi [(birim_adı, sayı, güç), ...]"""
        info = []
        for unit_type, count in self.units.items():
            stats = UNIT_DEFINITIONS[unit_type]
            power = count * (stats.attack + stats.defense)
            info.append((stats.name_tr, count, power))
        return info
    
    def announce_army(self):
        """Ordu bilgisini ekran okuyucuya duyur"""
        audio = get_audio_manager()
        audio.speak("Ordu Durumu", interrupt=True)
        audio.announce_value("Toplam Asker", str(self.get_total_soldiers()))
        audio.announce_value("Toplam Güç", str(self.get_total_power()))
        audio.announce_value("Moral", f"%{self.morale}")
        
        for unit_type, count in self.units.items():
            if count > 0:
                stats = UNIT_DEFINITIONS[unit_type]
                audio.announce_value(stats.name_tr, str(count))
        
        if self.training_queue:
            audio.speak("Eğitimdekiler:")
            for item in self.training_queue:
                stats = UNIT_DEFINITIONS[item.unit_type]
                audio.speak(f"{item.count} {stats.name_tr}, {item.turns_remaining} tur kaldı")
    
    def to_dict(self) -> Dict:
        """Kayıt için dictionary'e dönüştür"""
        return {
            'units': {k.value: v for k, v in self.units.items()},
            'training_queue': [
                {'type': t.unit_type.value, 'count': t.count, 'turns': t.turns_remaining}
                for t in self.training_queue
            ],
            'morale': self.morale,
            'experience': self.experience,
            'at_war': self.at_war,
            'total_losses': self.total_losses,
            'total_victories': self.total_victories
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'MilitarySystem':
        """Dictionary'den yükle"""
        system = cls()
        system.units = {UnitType(k): v for k, v in data['units'].items()}
        system.training_queue = [
            TrainingQueue(UnitType(t['type']), t['count'], t['turns'])
            for t in data['training_queue']
        ]
        system.morale = data['morale']
        system.experience = data.get('experience', 0)
        system.at_war = data['at_war']
        system.total_losses = data.get('total_losses', 0)
        system.total_victories = data.get('total_victories', 0)
        return system
