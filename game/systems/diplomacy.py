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


class AIPersonality(Enum):
    """Komşu AI kişilikleri"""
    AGGRESSIVE = "aggressive"   # Saldırgan - Haraç reddetme, savaş eğilimi yüksek
    MERCANTILE = "mercantile"   # Ticari - Anlaşmalara açık, altın odaklı
    HONORABLE = "honorable"     # Onurlu - Vassalığı reddeder, evliliğe açık
    FEARFUL = "fearful"         # Korkak - Güç gösterisine boyun eğer
    PIOUS = "pious"             # Dindar - Dini konularda hassas, sadık


# Kişilik özellikleri - her kişiliğin diplomatik etkisi
PERSONALITY_TRAITS = {
    AIPersonality.AGGRESSIVE: {
        'tribute_modifier': -30,      # Haraç kabul etme şansı düşük
        'vassal_modifier': -20,       # Vassallaşma şansı düşük
        'marriage_modifier': -10,     # Evlilik şansı biraz düşük
        'trade_modifier': 0,          # Ticaret normal
        'war_tendency': 0.3,          # Savaş ihtimali yüksek
        'description': 'Saldırgan ve tehlikeli'
    },
    AIPersonality.MERCANTILE: {
        'tribute_modifier': 10,       # Altınla ikna edilebilir
        'vassal_modifier': 0,
        'marriage_modifier': 20,      # Zenginliğe değer verir
        'trade_modifier': 30,         # Ticarete çok açık
        'war_tendency': 0.1,
        'description': 'Ticaret ve zenginlik odaklı'
    },
    AIPersonality.HONORABLE: {
        'tribute_modifier': -20,      # Onuru kırılır
        'vassal_modifier': -40,       # Vassalığı kabul etmez
        'marriage_modifier': 30,      # Şerefli evliliğe açık
        'trade_modifier': 10,
        'war_tendency': 0.15,
        'description': 'Onurlu ve gururlu'
    },
    AIPersonality.FEARFUL: {
        'tribute_modifier': 30,       # Güçlüye boyun eğer
        'vassal_modifier': 40,        # Vassallaşmaya açık
        'marriage_modifier': 10,
        'trade_modifier': 0,
        'war_tendency': 0.05,         # Savaştan kaçınır
        'description': 'Korkak ve itaatkar'
    },
    AIPersonality.PIOUS: {
        'tribute_modifier': 0,
        'vassal_modifier': -10,
        'marriage_modifier': 15,      # Dini birlik önemli
        'trade_modifier': 0,
        'war_tendency': 0.1,
        'description': 'Dindar ve sadık'
    }
}


@dataclass
class Relation:
    """İlişki durumu"""
    target: str
    value: int  # -100 ile +100 arası
    relation_type: RelationType = RelationType.NEUTRAL
    personality: AIPersonality = AIPersonality.MERCANTILE  # Varsayılan kişilik
    
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
    
    def get_personality_modifier(self, action_type: str) -> int:
        """Kişiliğe göre diplomatik eylem modifiyeri"""
        traits = PERSONALITY_TRAITS.get(self.personality, {})
        return traits.get(f'{action_type}_modifier', 0)
    
    def get_personality_description(self) -> str:
        """Kişilik açıklaması"""
        traits = PERSONALITY_TRAITS.get(self.personality, {})
        return traits.get('description', 'Bilinmiyor')

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
        self.sadrazam_relation = 65    # Sadrazam (1520: Piri Mehmed Paşa, Yavuz'dan devralındı)
        self.basdefterdar_relation = 50  # Başdefterdar (maliye başkanı)
        
        # Komşu eyaletler/beylikler (eyalete göre güncellenecek)
        self.neighbors: Dict[str, Relation] = {}
        
        # Görevler (padişahtan gelen emirler)
        self.active_missions: List[Dict] = []
        
        # === YENİ: Vassaller ve İttifaklar ===
        self.vassals: List[Dict] = []  # Vassal devletler
        self.marriage_alliances: List[Dict] = []  # Evlilik ittifakları
        self.tribute_income = 0  # Vassallerden gelen haraç
        
        # === PRESTİJ SİSTEMİ ===
        self.prestige = 100  # Başlangıç prestiji (0-500)
        self.prestige_history: List[Dict] = []  # Prestij geçmişi
        
        # === OLAY ZİNCİRLERİ ===
        self.event_chains: List[Dict] = []  # Aktif olay zincirleri
        self.completed_chains: List[str] = []  # Tamamlanan zincirler
        
        # === MOMENTUM SİSTEMİ ===
        self.relationship_momentum: List[Dict] = []  # Bekleyen ilişki değişimleri
        
        # Elçi gönderme bekleme süresi
        self.envoy_cooldown = 0
    
    def update_neighbors(self, province_name: str):
        """Eyalete göre komşuları güncelle"""
        import random
        
        self.neighbors.clear()
        neighbor_list = PROVINCE_NEIGHBORS.get(province_name, [
            ("Komşu Beylik", 20), ("Diğer Eyalet", 30)  # Varsayılan
        ])
        
        # Rastgele kişilik atama
        personalities = list(AIPersonality)
        
        for name, value in neighbor_list:
            personality = random.choice(personalities)
            self.neighbors[name] = Relation(name, value, RelationType.NEUTRAL, personality)
    
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
    
    def send_envoy(self, target: str, player=None) -> bool:
        """Elçi gönder - player: cinsiyet bonusu için"""
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
        
        # Temel ilişki artışı
        base_improvement = 15
        
        # Kadın karakter diplomasi bonusu (+%20 = +3)
        bonus_text = ""
        if player:
            diplomacy_bonus = player.get_bonus('diplomacy')
            extra = int(base_improvement * diplomacy_bonus)
            base_improvement += extra
            if extra > 0:
                bonus_text = f" (Diplomasi bonusu: +{extra})"
        
        # İlişkiyi iyileştir
        self.neighbors[target].value = min(100, self.neighbors[target].value + base_improvement)
        self.neighbors[target].update_type()
        
        self.envoy_cooldown = 3  # 3 tur bekleme
        
        audio = get_audio_manager()
        audio.announce_action_result(
            f"{target}'a elçi gönderme",
            True,
            f"İlişki +{base_improvement}{bonus_text}"
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
    
    def propose_marriage(self, target: str, economy, player=None) -> bool:
        """
        Evlilik ittifakı teklif et
        player: PlayerCharacter (cinsiyet bonusu için)
        """
        audio = get_audio_manager()
        
        if target not in self.neighbors:
            audio.speak("Bu bölge ile evlilik ittifakı kurulamaz.", interrupt=True)
            return False
        
        # Zaten evlilik var mı?
        for marriage in self.marriage_alliances:
            if marriage['partner'] == target:
                audio.speak(f"{target} ile zaten evlilik ittifakınız var.", interrupt=True)
                return False
        
        # İlişki kontrolü (en az nötr)
        relation = self.neighbors[target]
        if relation.value < 0:
            audio.speak(f"{target} ile ilişkileriniz çok kötü. Önce elçi gönderin.", interrupt=True)
            return False
        
        # Çeyiz maliyeti
        dowry_cost = 10000
        if not economy.can_afford(gold=dowry_cost):
            audio.speak(f"Çeyiz için {dowry_cost} altın gerekli.", interrupt=True)
            return False
        
        # Başarı şansı (ilişkiye göre)
        import random
        success_chance = 40 + relation.value  # %40 + ilişki değeri
        
        # Kadın karakter evlilik bonusu (+%25)
        marriage_bonus = 0
        is_female = False
        if player:
            marriage_bonus = player.get_bonus('marriage_alliance')
            is_female = player.gender.value == 'female'
        success_chance += int(marriage_bonus * 100)
        
        success = random.randint(1, 100) <= success_chance
        
        economy.spend(gold=dowry_cost)
        
        if success:
            self.marriage_alliances.append({
                'partner': target,
                'turns_active': 0,
                'relation_bonus': 20
            })
            relation.value += 30
            relation.update_type()
            
            # Cinsiyete göre farklı mesaj
            if is_female:
                message = f"{target} beyinin oğlu ile evlilik ittifakı kuruldu! +30 ilişki"
            else:
                message = f"{target} ile hanedan evliliği kuruldu! +30 ilişki"
            
            audio.announce_action_result("Evlilik ittifakı", True, message)
        else:
            relation.value -= 10
            relation.update_type()
            audio.announce_action_result(
                "Evlilik ittifakı",
                False,
                f"{target} teklifi reddetti"
            )
        
        return success
    
    def demand_tribute(self, target: str, military_power: int) -> tuple:
        """Komşudan haraç talep et"""
        audio = get_audio_manager()
        
        if target not in self.neighbors:
            audio.speak("Bu bölgeden haraç talep edilemez.", interrupt=True)
            return False, 0
        
        # Askeri güç kontrolü
        min_power = 500
        if military_power < min_power:
            audio.speak(f"Haraç talebi için en az {min_power} askeri güç gerekli.", interrupt=True)
            return False, 0
        
        relation = self.neighbors[target]
        
        # Başarı şansı (güce ve ilişkiye göre)
        import random
        power_bonus = min(30, (military_power - min_power) // 50)
        success_chance = 30 + power_bonus - (relation.value // 2)
        success = random.randint(1, 100) <= max(10, success_chance)
        
        if success:
            tribute_amount = random.randint(500, 2000)
            relation.value -= 20  # İlişki bozulur
            relation.update_type()
            audio.announce_action_result(
                "Haraç talebi",
                True,
                f"{target} {tribute_amount} altın haraç ödedi"
            )
            return True, tribute_amount
        else:
            relation.value -= 30  # Daha fazla bozulur
            relation.update_type()
            audio.announce_action_result(
                "Haraç talebi",
                False,
                f"{target} haraç ödemeyi reddetti ve düşmanlık arttı"
            )
            return False, 0
    
    def make_vassal(self, target: str, military_power: int) -> bool:
        """Komşuyu vassal yap (savaş sonrası veya güçlü diplomasi)"""
        audio = get_audio_manager()
        
        if target not in self.neighbors:
            audio.speak("Bu bölge vassal yapılamaz.", interrupt=True)
            return False
        
        # Zaten vassal mı?
        for vassal in self.vassals:
            if vassal['name'] == target:
                audio.speak(f"{target} zaten sizin vassalınız.", interrupt=True)
                return False
        
        # Çok yüksek güç gerekli
        min_power = 1500
        if military_power < min_power:
            audio.speak(f"Vassallaştırma için en az {min_power} askeri güç gerekli.", interrupt=True)
            return False
        
        relation = self.neighbors[target]
        
        import random
        power_bonus = min(40, (military_power - min_power) // 100)
        success_chance = 20 + power_bonus
        
        # Dostane ilişki varsa şans artar
        if relation.value > 30:
            success_chance += 20
        
        success = random.randint(1, 100) <= success_chance
        
        if success:
            tribute = random.randint(100, 500)  # Yıllık haraç
            self.vassals.append({
                'name': target,
                'tribute': tribute,
                'loyalty': 50,
                'military_support': random.randint(50, 150)
            })
            relation.value = 50  # Vassal ilişkisi
            relation.update_type()
            audio.announce_action_result(
                "Vassallaştırma",
                True,
                f"{target} artık vassalınız! Yıllık {tribute} altın haraç ödeyecek"
            )
            return True
        else:
            relation.value -= 40
            relation.update_type()
            audio.announce_action_result(
                "Vassallaştırma",
                False,
                f"{target} vassallığı reddetti ve düşman oldu"
            )
            return False
    
    def process_turn(self) -> List[str]:
        """Tur sonunda diplomasiyi güncelle"""
        audio = get_audio_manager()
        import random
        messages = []
        
        # Elçi bekleme süresini azalt
        if self.envoy_cooldown > 0:
            self.envoy_cooldown -= 1
        
        # === VASSAL HARAÇLARI ===
        self.tribute_income = 0
        for vassal in self.vassals:
            # Günlük haraç (yıllık / 360 ≈ tribute / 12 per month)
            daily_tribute = vassal['tribute'] // 30
            self.tribute_income += daily_tribute
            
            # Vassal sadakati zamanla azalabilir
            if random.random() < 0.1:  # %10 şans
                vassal['loyalty'] = max(0, vassal['loyalty'] - 1)
                if vassal['loyalty'] < 20:
                    msg = f"⚠ {vassal['name']} vassalınız isyan düşünüyor!"
                    audio.speak(msg, interrupt=False)
                    messages.append(msg)
        
        # === EVLİLİK İTTİFAKLARI ===
        for marriage in self.marriage_alliances:
            marriage['turns_active'] += 1
            # İlişki bonusu devam eder
            if marriage['partner'] in self.neighbors:
                self.neighbors[marriage['partner']].value = min(100, 
                    self.neighbors[marriage['partner']].value + 1)
        
        # Sadakat doğal olarak çok yavaş azalır (sadece 70 üstünde ve %20 şansla)
        if self.sultan_loyalty > 70 and random.random() < 0.2:
            self.sultan_loyalty -= 1
        
        # Lütuf daha yavaş azalır
        if self.sultan_favor > 30 and random.random() < 0.5:
            self.sultan_favor -= 1
        
        # Düşük sadakat uyarısı
        if self.sultan_loyalty < 30:
            msg = "UYARI: Padişah sadakatinizden şüphe ediyor!"
            audio.announce(msg)
            messages.append(msg)
        
        # === OLAY ZİNCİRLERİNİ İŞLE ===
        chain_msgs = self.process_event_chains()
        if chain_msgs:
            messages.extend(chain_msgs)
        
        # === MOMENTUM DEĞİŞİMLERİNİ UYGULA ===
        self.process_momentum()
        
        # Padişah görevi oluşturma şansı
        if not self.active_missions and self.sultan_loyalty > 20:
            if random.random() < 0.2:  # %20 şans
                self._create_random_mission()
                
        return messages

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
            'basdefterdar_relation': self.basdefterdar_relation,
            'neighbors': {
                k: {
                    'value': v.value, 
                    'type': v.relation_type.value,
                    'personality': v.personality.value
                }
                for k, v in self.neighbors.items()
            },
            'active_missions': self.active_missions,
            'envoy_cooldown': self.envoy_cooldown,
            'vassals': self.vassals,
            'marriage_alliances': self.marriage_alliances,
            'prestige': self.prestige,
            'prestige_history': self.prestige_history[-10:],  # Son 10 kayıt
            'event_chains': self.event_chains,
            'completed_chains': self.completed_chains,
            'relationship_momentum': self.relationship_momentum
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'DiplomacySystem':
        """Dictionary'den yükle"""
        system = cls()
        system.sultan_loyalty = data['sultan_loyalty']
        system.sultan_favor = data['sultan_favor']
        system.sadrazam_relation = data.get('sadrazam_relation', 65)
        system.basdefterdar_relation = data.get('basdefterdar_relation', 
            data.get('defterdar_relation', 50))  # Eski kayıtlarla uyumluluk
        
        # Komşuları kişilikle birlikte yükle
        system.neighbors = {}
        for k, v in data['neighbors'].items():
            personality = AIPersonality(v.get('personality', 'mercantile'))
            system.neighbors[k] = Relation(k, v['value'], RelationType(v['type']), personality)
        
        system.active_missions = data.get('active_missions', [])
        system.envoy_cooldown = data.get('envoy_cooldown', 0)
        system.vassals = data.get('vassals', [])
        system.marriage_alliances = data.get('marriage_alliances', [])
        system.tribute_income = 0
        
        # Yeni sistemler
        system.prestige = data.get('prestige', 100)
        system.prestige_history = data.get('prestige_history', [])
        system.event_chains = data.get('event_chains', [])
        system.completed_chains = data.get('completed_chains', [])
        system.relationship_momentum = data.get('relationship_momentum', [])
        
        return system
    
    # ===================================================================
    # PRESTİJ SİSTEMİ
    # ===================================================================
    
    def add_prestige(self, amount: int, reason: str):
        """Prestij ekle"""
        old_prestige = self.prestige
        self.prestige = min(500, self.prestige + amount)
        
        self.prestige_history.append({
            'amount': amount,
            'reason': reason,
            'new_total': self.prestige
        })
        
        audio = get_audio_manager()
        if amount >= 50:
            audio.speak(f"Büyük prestij kazancı: +{amount} ({reason})", interrupt=False)
    
    def spend_prestige(self, amount: int, reason: str) -> bool:
        """Prestij harca, başarılıysa True döndür"""
        if self.prestige < amount:
            return False
        
        self.prestige -= amount
        self.prestige_history.append({
            'amount': -amount,
            'reason': reason,
            'new_total': self.prestige
        })
        return True
    
    def get_prestige_level(self) -> str:
        """Prestij seviyesi açıklaması"""
        if self.prestige >= 400:
            return "Efsanevi"
        elif self.prestige >= 300:
            return "Şanlı"
        elif self.prestige >= 200:
            return "Saygın"
        elif self.prestige >= 100:
            return "Normal"
        elif self.prestige >= 50:
            return "Zayıf"
        else:
            return "Düşmüş"
    
    def get_prestige_modifier(self) -> int:
        """Prestije göre diplomatik bonus"""
        return (self.prestige - 100) // 20  # Her 20 prestij = +1% bonus
    
    # ===================================================================
    # OLAY ZİNCİRLERİ (EVENT CHAINS)
    # ===================================================================
    
    def start_event_chain(self, chain_type: str, target: str, initial_data: dict = None):
        """Yeni olay zinciri başlat"""
        chain_id = f"{chain_type}_{target}_{len(self.event_chains)}"
        
        chain = {
            'id': chain_id,
            'type': chain_type,
            'target': target,
            'stage': 0,
            'turns_in_stage': 0,
            'data': initial_data or {},
            'started_turn': 0,
            'outcomes': []
        }
        
        self.event_chains.append(chain)
        return chain_id
    
    def advance_event_chain(self, chain_id: str, outcome: str = None):
        """Olay zincirini ilerlet"""
        for chain in self.event_chains:
            if chain['id'] == chain_id:
                if outcome:
                    chain['outcomes'].append(outcome)
                chain['stage'] += 1
                chain['turns_in_stage'] = 0
                return True
        return False
    
    def complete_event_chain(self, chain_id: str, success: bool):
        """Olay zincirini tamamla"""
        for i, chain in enumerate(self.event_chains):
            if chain['id'] == chain_id:
                self.completed_chains.append(chain_id)
                self.event_chains.pop(i)
                return chain
        return None
    
    def get_active_chain_for_target(self, target: str, chain_type: str = None):
        """Hedef için aktif zincir bul"""
        for chain in self.event_chains:
            if chain['target'] == target:
                if chain_type is None or chain['type'] == chain_type:
                    return chain
        return None
    
    def process_event_chains(self) -> List[str]:
        """Olay zincirlerini işle (her turda çağrılır) ve mesajları döndür"""
        import random
        audio = get_audio_manager()
        messages = []
        
        chains_to_remove = []
        
        for chain in self.event_chains:
            chain['turns_in_stage'] += 1
            chain_type = chain['type']
            stage = chain['stage']
            target = chain['target']
            
            # ============ EVLİLİK ZİNCİRİ ============
            if chain_type == 'marriage':
                if stage == 0:  # Elçi gönderildi, cevap bekleniyor
                    if chain['turns_in_stage'] >= 3:
                        # Cevap geldi
                        if random.random() < 0.7:  # %70 olumlu cevap
                            msg = f"{target}'den elçi geldi: Evlilik teklifiniz değerlendiriliyor."
                            audio.speak(msg, interrupt=False)
                            messages.append(msg)
                            self.advance_event_chain(chain['id'], 'positive_response')
                        else:
                            msg = f"{target}'den haber: Şu an evlilik için uygun değiliz."
                            audio.speak(msg, interrupt=False)
                            messages.append(msg)
                            self.complete_event_chain(chain['id'], False)
                            chains_to_remove.append(chain['id'])
                
                elif stage == 1:  # Pazarlık aşaması
                    if chain['turns_in_stage'] >= 2:
                        # Çeyiz pazarlığı tamamlandı
                        msg = f"{target} ile çeyiz pazarlığı tamamlandı. Düğün hazırlıkları başlıyor!"
                        audio.speak(msg, interrupt=False)
                        messages.append(msg)
                        self.advance_event_chain(chain['id'], 'dowry_agreed')
                
                elif stage == 2:  # Düğün hazırlıkları
                    if chain['turns_in_stage'] >= 5:
                        # Düğün töreni
                        msg = f"BÜYÜK DÜĞÜN TÖRENİ! {target} ile hanedan evliliği kutlanıyor!"
                        audio.speak(msg, interrupt=False)
                        messages.append(msg)
                        self.add_prestige(75, f"{target} ile hanedan evliliği")
                        
                        # Evlilik ittifakını ekle
                        self.marriage_alliances.append({
                            'partner': target,
                            'turns_active': 0,
                            'relation_bonus': 30,
                            'yearly_gift': chain['data'].get('yearly_gift', 0),
                            'from_chain': True
                        })
                        
                        # İlişkiyi güncelle
                        if target in self.neighbors:
                            self.neighbors[target].value += 40
                            self.neighbors[target].update_type()
                        
                        self.complete_event_chain(chain['id'], True)
                        chains_to_remove.append(chain['id'])
            
            # ============ VASSAL ZİNCİRİ ============
            elif chain_type == 'vassal':
                if stage == 0:  # Ultimatom gönderildi
                    if chain['turns_in_stage'] >= 2:
                        # Cevap
                        power = chain['data'].get('military_power', 0)
                        chance = 30 + (power - 1000) // 100
                        
                        if random.randint(1, 100) <= chance:
                            msg = f"{target} boyun eğmeyi kabul etti! Şartlar görüşülecek."
                            audio.speak(msg, interrupt=False)
                            messages.append(msg)
                            self.advance_event_chain(chain['id'], 'submission')
                        else:
                            msg = f"{target} vassallığı reddetti! Savaş kapıda olabilir."
                            audio.speak(msg, interrupt=False)
                            messages.append(msg)
                            if target in self.neighbors:
                                self.neighbors[target].value -= 30
                                self.neighbors[target].update_type()
                            self.complete_event_chain(chain['id'], False)
                            chains_to_remove.append(chain['id'])
                
                elif stage == 1:  # Şartlar görüşülüyor
                    if chain['turns_in_stage'] >= 3:
                        # Vassallaşma tamamlandı
                        tribute = chain['data'].get('tribute', 200)
                        msg = f"{target} artık resmi olarak vassalınız! Yıllık {tribute} altın haraç ödeyecek."
                        audio.speak(msg, interrupt=False)
                        messages.append(msg)
                        
                        self.vassals.append({
                            'name': target,
                            'tribute': tribute,
                            'loyalty': 60,
                            'autonomy': chain['data'].get('autonomy', 50),
                            'military_support': 100,
                            'from_chain': True
                        })
                        
                        self.add_prestige(150, f"{target}'ı vassallaştırdınız")
                        
                        if target in self.neighbors:
                            self.neighbors[target].value = 60
                            self.neighbors[target].update_type()
                        
                        self.complete_event_chain(chain['id'], True)
                        chains_to_remove.append(chain['id'])
            
            # ============ BARIŞ ANTLAŞMASI ZİNCİRİ ============
            elif chain_type == 'peace':
                if stage == 0:  # Barış teklifi gönderildi
                    if chain['turns_in_stage'] >= 4:
                        if random.random() < 0.6:
                            msg = f"{target} barış anlaşmasını kabul etti!"
                            audio.speak(msg, interrupt=False)
                            messages.append(msg)
                            if target in self.neighbors:
                                self.neighbors[target].value = 0
                                self.neighbors[target].update_type()
                            self.add_prestige(30, f"{target} ile barış")
                            self.complete_event_chain(chain['id'], True)
                        else:
                            msg = f"{target} barışı reddetti. Savaş devam ediyor."
                            audio.speak(msg, interrupt=False)
                            messages.append(msg)
                            self.complete_event_chain(chain['id'], False)
                        chains_to_remove.append(chain['id'])
        
        # Tamamlanan zincirleri temizle
        self.event_chains = [c for c in self.event_chains if c['id'] not in chains_to_remove]
        return messages
    
    # ===================================================================
    # MOMENTUM SİSTEMİ
    # ===================================================================
    
    def add_relationship_momentum(self, target: str, total_change: int, turns: int, reason: str):
        """Yavaş yavaş uygulanacak ilişki değişimi ekle"""
        per_turn = total_change / turns
        
        self.relationship_momentum.append({
            'target': target,
            'remaining_change': total_change,
            'per_turn': per_turn,
            'turns_left': turns,
            'reason': reason
        })
    
    def process_momentum(self):
        """Momentum değişimlerini uygula (her turda çağrılır)"""
        completed = []
        
        for i, momentum in enumerate(self.relationship_momentum):
            target = momentum['target']
            per_turn = momentum['per_turn']
            
            if target in self.neighbors:
                self.neighbors[target].value += int(per_turn)
                self.neighbors[target].update_type()
            
            momentum['remaining_change'] -= per_turn
            momentum['turns_left'] -= 1
            
            if momentum['turns_left'] <= 0:
                completed.append(i)
        
        # Tamamlanmış momentumları temizle (tersten)
        for i in reversed(completed):
            self.relationship_momentum.pop(i)
