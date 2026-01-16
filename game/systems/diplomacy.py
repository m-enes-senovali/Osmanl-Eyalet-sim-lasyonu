# -*- coding: utf-8 -*-
"""
Osmanlı Eyalet Yönetim Simülasyonu - Diplomasi Sistemi
"""

from dataclasses import dataclass
from typing import Dict, List, Optional
from enum import Enum
from audio.audio_manager import get_audio_manager


class RelationType(Enum):
    """İlişki türleri"""
    HOSTILE = "hostile"       # Düşman
    COLD = "cold"             # Soğuk
    NEUTRAL = "neutral"       # Nötr
    FRIENDLY = "friendly"     # Dostane
    ALLIED = "allied"         # Müttefik


@dataclass
class Relation:
    """İlişki durumu"""
    target: str
    value: int  # -100 ile +100 arası
    relation_type: RelationType = RelationType.NEUTRAL
    
    def update_type(self):
        """Değere göre ilişki türünü güncelle"""
        if self.value < -60:
            self.relation_type = RelationType.HOSTILE
        elif self.value < -20:
            self.relation_type = RelationType.COLD
        elif self.value < 20:
            self.relation_type = RelationType.NEUTRAL
        elif self.value < 60:
            self.relation_type = RelationType.FRIENDLY
        else:
            self.relation_type = RelationType.ALLIED

# Territories modülünden komşu ilişkilerini dinamik olarak oluştur
from game.data.territories import TERRITORIES, TerritoryType, get_all_neighbors


def _get_relation_value(territory, neighbor_name):
    """Komşu türüne göre ilişki değeri hesapla"""
    neighbor = TERRITORIES.get(neighbor_name)
    if not neighbor:
        return 0
    
    # Aynı imparatorluk içi yüksek ilişki
    if territory.territory_type in [TerritoryType.OSMANLI_EYALET, TerritoryType.OSMANLI_SANCAK]:
        if neighbor.territory_type in [TerritoryType.OSMANLI_EYALET, TerritoryType.OSMANLI_SANCAK]:
            return 70  # Osmanlı eyaletleri arası
        elif neighbor.territory_type == TerritoryType.VASAL:
            return 40  # Vasal devlet
        elif neighbor.territory_type == TerritoryType.KOMSU_DEVLET:
            # Devlete göre farklı ilişki
            if neighbor_name == "Safevi İmparatorluğu":
                return -50  # Ana düşman
            elif neighbor_name == "Venedik":
                return -30  # Rakip
            elif neighbor_name in ["Macaristan Krallığı", "Avusturya"]:
                return -20  # Potansiyel düşman
            else:
                return 0  # Nötr
    
    # Vasal için
    elif territory.territory_type == TerritoryType.VASAL:
        if neighbor.territory_type in [TerritoryType.OSMANLI_EYALET, TerritoryType.OSMANLI_SANCAK]:
            return 50  # Osmanlı ile iyi ilişki
        elif neighbor.territory_type == TerritoryType.VASAL:
            return 30  # Diğer vasallar
        else:
            return -10  # Dış devletler
    
    return 0


# Dinamik komşu sözlüğü oluştur
PROVINCE_NEIGHBORS = {}
for name, territory in TERRITORIES.items():
    neighbors = []
    all_neighbors = get_all_neighbors(territory)
    for neighbor_name in all_neighbors:
        if neighbor_name in TERRITORIES:  # Geçerli bölge mi kontrol
            relation_value = _get_relation_value(territory, neighbor_name)
            neighbors.append((neighbor_name, relation_value))
    if neighbors:
        PROVINCE_NEIGHBORS[name] = neighbors


class DiplomacySystem:
    """Diplomasi ve ilişkiler sistemi"""
    
    def __init__(self):
        # Padişah ilişkisi (en önemli!)
        self.sultan_loyalty = 90  # 0-100 (increased starting value)
        self.sultan_favor = 50    # 0-100 (lütuf)
        
        # Saraydaki kişiler
        self.sadrazam_relation = 50   # Sadrazam
        self.defterdar_relation = 50  # Defterdar (maliye)
        
        # Komşu eyaletler/beylikler (eyalete göre güncellenecek)
        self.neighbors: Dict[str, Relation] = {}
        
        # Görevler (padişahtan gelen emirler)
        self.active_missions: List[Dict] = []
        
        # Elçi gönderme bekleme süresi
        self.envoy_cooldown = 0
    
    def update_neighbors(self, province_name: str):
        """Eyalete göre komşuları güncelle"""
        self.neighbors.clear()
        neighbor_list = PROVINCE_NEIGHBORS.get(province_name, [
            ("Komşu Beylik", 20), ("Diğer Eyalet", 30)  # Varsayılan
        ])
        for name, value in neighbor_list:
            self.neighbors[name] = Relation(name, value)
    
    def get_loyalty_description(self) -> str:
        """Sadakat durumu açıklaması"""
        if self.sultan_loyalty >= 80:
            return "Çok Sadık"
        elif self.sultan_loyalty >= 60:
            return "Sadık"
        elif self.sultan_loyalty >= 40:
            return "Şüpheli"
        elif self.sultan_loyalty >= 20:
            return "Güvenilmez"
        else:
            return "Hain"
    
    def get_relation_type_name(self, relation_type: RelationType) -> str:
        """İlişki türü Türkçe adı"""
        names = {
            RelationType.HOSTILE: "Düşman",
            RelationType.COLD: "Soğuk",
            RelationType.NEUTRAL: "Nötr",
            RelationType.FRIENDLY: "Dostane",
            RelationType.ALLIED: "Müttefik"
        }
        return names.get(relation_type, "Bilinmiyor")
    
    def send_tribute_to_sultan(self, amount: int, economy) -> bool:
        """Padişaha haraç gönder"""
        if not economy.can_afford(gold=amount):
            audio = get_audio_manager()
            audio.announce_action_result("Haraç gönderme", False, "Yetersiz altın")
            return False
        
        economy.spend(gold=amount)
        
        # Sadakat artışı (miktara bağlı)
        loyalty_gain = min(20, amount // 500)
        favor_gain = min(15, amount // 700)
        
        self.sultan_loyalty = min(100, self.sultan_loyalty + loyalty_gain)
        self.sultan_favor = min(100, self.sultan_favor + favor_gain)
        
        audio = get_audio_manager()
        audio.announce_action_result(
            "Haraç gönderme",
            True,
            f"Sadakat +{loyalty_gain}, Lütuf +{favor_gain}"
        )
        
        return True
    
    def send_envoy(self, target: str) -> bool:
        """Elçi gönder"""
        if self.envoy_cooldown > 0:
            audio = get_audio_manager()
            audio.announce_action_result(
                "Elçi gönderme",
                False,
                f"{self.envoy_cooldown} tur bekle"
            )
            return False
        
        if target not in self.neighbors:
            return False
        
        # İlişkiyi iyileştir
        self.neighbors[target].value = min(100, self.neighbors[target].value + 15)
        self.neighbors[target].update_type()
        
        self.envoy_cooldown = 3  # 3 tur bekleme
        
        audio = get_audio_manager()
        audio.announce_action_result(
            f"{target}'a elçi gönderme",
            True,
            f"İlişki +15"
        )
        
        return True
    
    def propose_trade_agreement(self, target: str, economy) -> bool:
        """Ticaret anlaşması teklif et"""
        if target not in self.neighbors:
            return False
        
        relation = self.neighbors[target]
        
        # İlişki yeterince iyi mi?
        if relation.value < 0:
            audio = get_audio_manager()
            audio.announce_action_result(
                "Ticaret anlaşması",
                False,
                "İlişki çok kötü"
            )
            return False
        
        # Maliyet
        cost = 500
        if not economy.can_afford(gold=cost):
            audio = get_audio_manager()
            audio.announce_action_result("Ticaret anlaşması", False, "Yetersiz altın")
            return False
        
        economy.spend(gold=cost)
        
        # Başarı şansı
        import random
        success_chance = 50 + relation.value
        success = random.randint(1, 100) <= success_chance
        
        audio = get_audio_manager()
        if success:
            economy.trade_modifier += 0.1
            relation.value = min(100, relation.value + 10)
            relation.update_type()
            audio.announce_action_result(
                "Ticaret anlaşması",
                True,
                f"{target} ile anlaşma sağlandı! Ticaret +%10"
            )
        else:
            audio.announce_action_result(
                "Ticaret anlaşması",
                False,
                f"{target} teklifi reddetti"
            )
        
        return success
    
    def process_turn(self):
        """Tur sonunda diplomasiyi güncelle"""
        audio = get_audio_manager()
        
        # Elçi bekleme süresini azalt
        if self.envoy_cooldown > 0:
            self.envoy_cooldown -= 1
        
        # Sadakat doğal olarak çok yavaş azalır (sadece 70 üstünde ve %20 şansla)
        import random
        if self.sultan_loyalty > 70 and random.random() < 0.2:
            self.sultan_loyalty -= 1
        
        # Lütuf daha yavaş azalır
        if self.sultan_favor > 30 and random.random() < 0.5:
            self.sultan_favor -= 1
        
        # Düşük sadakat uyarısı
        if self.sultan_loyalty < 30:
            audio.announce("UYARI: Padişah sadakatinizden şüphe ediyor!")
        
        # Padişah görevi oluşturma şansı
        if not self.active_missions and self.sultan_loyalty > 20:
            import random
            if random.random() < 0.2:  # %20 şans
                self._create_random_mission()
    
    def _create_random_mission(self):
        """Rastgele padişah görevi oluştur"""
        import random
        missions = [
            {
                'type': 'tribute',
                'title': 'Haraç Talebi',
                'description': 'Padişah hazineye 2000 altın katkı bekliyor',
                'target': 2000,
                'reward_loyalty': 15,
                'turns_remaining': 5
            },
            {
                'type': 'military',
                'title': 'Asker Talebi',
                'description': 'Sefere 100 asker gönder',
                'target': 100,
                'reward_loyalty': 20,
                'turns_remaining': 4
            },
            {
                'type': 'suppress',
                'title': 'İsyan Bastır',
                'description': 'Eşkıyaları temizle',
                'target': 1,
                'reward_loyalty': 10,
                'turns_remaining': 3
            }
        ]
        
        mission = random.choice(missions)
        self.active_missions.append(mission)
        
        audio = get_audio_manager()
        audio.announce(f"Padişahtan Emir: {mission['title']}")
    
    def complete_mission(self, mission_index: int) -> bool:
        """Görevi tamamla"""
        if mission_index >= len(self.active_missions):
            return False
        
        mission = self.active_missions[mission_index]
        
        self.sultan_loyalty = min(100, self.sultan_loyalty + mission['reward_loyalty'])
        self.sultan_favor = min(100, self.sultan_favor + 10)
        
        audio = get_audio_manager()
        audio.announce_action_result(
            f"{mission['title']} görevi",
            True,
            f"Sadakat +{mission['reward_loyalty']}"
        )
        
        self.active_missions.remove(mission)
        return True
    
    def fail_mission(self, mission_index: int):
        """Görev başarısız"""
        if mission_index >= len(self.active_missions):
            return
        
        mission = self.active_missions[mission_index]
        
        self.sultan_loyalty = max(0, self.sultan_loyalty - 10)  # Reduced from -20
        self.sultan_favor = max(0, self.sultan_favor - 15)
        
        audio = get_audio_manager()
        audio.announce(f"UYARI: {mission['title']} görevi başarısız! Sadakat -20")
        
        self.active_missions.remove(mission)
    
    def announce_status(self):
        """Diplomasi durumunu ekran okuyucuya duyur"""
        audio = get_audio_manager()
        audio.speak("Diplomasi Durumu", interrupt=True)
        audio.announce_value("Padişah Sadakati", f"%{self.sultan_loyalty}")
        audio.announce_value("Durum", self.get_loyalty_description())
        audio.announce_value("Padişah Lütfu", f"%{self.sultan_favor}")
        
        audio.speak("Komşu İlişkileri:")
        for name, relation in self.neighbors.items():
            type_name = self.get_relation_type_name(relation.relation_type)
            audio.speak(f"{name}: {type_name} ({relation.value})")
        
        if self.active_missions:
            audio.speak("Aktif Görevler:")
            for mission in self.active_missions:
                audio.speak(f"{mission['title']}, {mission['turns_remaining']} tur kaldı")
    
    def to_dict(self) -> Dict:
        """Kayıt için dictionary'e dönüştür"""
        return {
            'sultan_loyalty': self.sultan_loyalty,
            'sultan_favor': self.sultan_favor,
            'sadrazam_relation': self.sadrazam_relation,
            'defterdar_relation': self.defterdar_relation,
            'neighbors': {
                k: {'value': v.value, 'type': v.relation_type.value}
                for k, v in self.neighbors.items()
            },
            'active_missions': self.active_missions,
            'envoy_cooldown': self.envoy_cooldown
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'DiplomacySystem':
        """Dictionary'den yükle"""
        system = cls()
        system.sultan_loyalty = data['sultan_loyalty']
        system.sultan_favor = data['sultan_favor']
        system.sadrazam_relation = data.get('sadrazam_relation', 50)
        system.defterdar_relation = data.get('defterdar_relation', 50)
        system.neighbors = {
            k: Relation(k, v['value'], RelationType(v['type']))
            for k, v in data['neighbors'].items()
        }
        system.active_missions = data.get('active_missions', [])
        system.envoy_cooldown = data.get('envoy_cooldown', 0)
        return system
