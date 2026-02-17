# -*- coding: utf-8 -*-
"""
Osmanlı Eyalet Yönetim Simülasyonu - Casusluk Sistemi
1520 Dönemi Tarihi Gerçekliğine Uygun

Osmanlı istihbarat sistemi:
- Çavuşlar: Diplomatik görevliler + istihbaratçı
- Hafiyeler: İç güvenlik
- Gezgin Dervişler: Gizli ajanlar
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from enum import Enum
import random
from audio.audio_manager import get_audio_manager


class SpyType(Enum):
    """Casus tipleri (1520 dönemi)"""
    CAVUS = "cavus"              # Çavuş - Diplomatik casus
    HAFIYE = "hafiye"            # Hafiye - İç istihbarat
    DERVIS = "dervis"            # Gezgin Derviş - Gizli ajan
    TEBDIL = "tebdil"            # Tebdil gezenler - Kılık değiştirmiş ajan
    CARIYE = "cariye"            # Cariye - Saray casusesi (Kadın karakter özel)


class OperationType(Enum):
    """Casusluk operasyonları"""
    KESIF = "kesif"                  # Keşif - Düşman ordu/ekonomi bilgisi
    SABOTAJ = "sabotaj"              # Sabotaj - Üretim/ticaret zarara
    SUIKAST = "suikast"              # Suikast - Lider/komutan
    FITNE = "fitne"                  # Fitne - İsyan kışkırtma
    KARSI_ISTIHBARAT = "karsi"       # Karşı istihbarat - Düşman casusları yakala
    PROPAGANDA = "propaganda"         # Propaganda - Halk desteği kazanma
    HAREM_ISTIHBARATI = "harem"      # Harem İstihbaratı - Saray sırları (Kadın özel)


@dataclass
class SpyStats:
    """Casus istatistikleri"""
    name: str
    name_tr: str
    cost_gold: int
    maintenance: int
    skill: int              # Beceri seviyesi (1-10)
    stealth: int            # Gizlilik (1-10)
    speed: int              # Hareket hızı
    specialization: str     # Uzmanlık alanı
    historical_note: str


# Casus Tanımları
SPY_DEFINITIONS = {
    SpyType.CAVUS: SpyStats(
        name="Cavus",
        name_tr="Çavuş",
        cost_gold=200,
        maintenance=10,
        skill=7,
        stealth=5,
        speed=6,
        specialization="diplomasi",
        historical_note="Divan-ı Hümayun'un resmi görevlisi, yabancı saraylarda bulunur"
    ),
    SpyType.HAFIYE: SpyStats(
        name="Hafiye",
        name_tr="Hafiye",
        cost_gold=100,
        maintenance=5,
        skill=5,
        stealth=8,
        speed=7,
        specialization="ic_guvenlik",
        historical_note="Yeniçeri Ağası'na bağlı iç istihbarat elemanı"
    ),
    SpyType.DERVIS: SpyStats(
        name="Wandering Dervish",
        name_tr="Gezgin Derviş",
        cost_gold=150,
        maintenance=3,
        skill=6,
        stealth=9,
        speed=5,
        specialization="sizma",
        historical_note="Tekke ve zaviyeleri kullanarak bilgi toplayan gizli ajan"
    ),
    SpyType.TEBDIL: SpyStats(
        name="Disguised Agent",
        name_tr="Tebdil Gezen",
        cost_gold=180,
        maintenance=8,
        skill=8,
        stealth=7,
        speed=8,
        specialization="kesfetme",
        historical_note="Kılık değiştirerek dolaşan üst düzey ajan"
    ),
    SpyType.CARIYE: SpyStats(
        name="Palace Concubine",
        name_tr="Saray Cariyesi",
        cost_gold=250,
        maintenance=15,
        skill=8,
        stealth=9,
        speed=3,
        specialization="saray_sizma",
        historical_note="Saraylara yerleştirilen eğitimli cariye. Yüksek mevkilere erişim. (Kadın vali özel)"
    ),
}


@dataclass
class OperationStats:
    """Operasyon istatistikleri"""
    name: str
    name_tr: str
    base_cost: int
    duration: int           # Tur sayısı
    risk: float             # 0.0-1.0 (yüksek = tehlikeli)
    required_skill: int     # Gereken minimum beceri
    effects: Dict           # Başarı etkileri


OPERATION_DEFINITIONS = {
    OperationType.KESIF: OperationStats(
        name="Reconnaissance",
        name_tr="Keşif",
        base_cost=50,
        duration=2,
        risk=0.2,
        required_skill=3,
        effects={'intelligence': 1}  # Düşman bilgisi kazanılır
    ),
    OperationType.SABOTAJ: OperationStats(
        name="Sabotage",
        name_tr="Sabotaj",
        base_cost=150,
        duration=3,
        risk=0.5,
        required_skill=5,
        effects={'enemy_production': -20}  # Düşman üretimi azalır
    ),
    OperationType.SUIKAST: OperationStats(
        name="Assassination",
        name_tr="Suikast",
        base_cost=300,
        duration=4,
        risk=0.8,
        required_skill=8,
        effects={'enemy_morale': -30, 'enemy_leadership': -1}
    ),
    OperationType.FITNE: OperationStats(
        name="Incite Rebellion",
        name_tr="Fitne Çıkarma",
        base_cost=200,
        duration=5,
        risk=0.6,
        required_skill=7,
        effects={'enemy_stability': -25}
    ),
    OperationType.KARSI_ISTIHBARAT: OperationStats(
        name="Counter-Intelligence",
        name_tr="Karşı İstihbarat",
        base_cost=100,
        duration=1,
        risk=0.3,
        required_skill=4,
        effects={'security': 10}
    ),
    OperationType.PROPAGANDA: OperationStats(
        name="Propaganda",
        name_tr="Propaganda",
        base_cost=80,
        duration=2,
        risk=0.2,
        required_skill=4,
        effects={'happiness': 5, 'loyalty': 3}
    ),
    OperationType.HAREM_ISTIHBARATI: OperationStats(
        name="Harem Intelligence",
        name_tr="Harem İstihbaratı",
        base_cost=200,
        duration=3,
        risk=0.4,
        required_skill=6,
        effects={'sultan_loyalty': 15, 'intelligence': 2}  # Padişah sadakati + bilgi
    ),
}


@dataclass
class Spy:
    """Aktif casus"""
    spy_id: str
    spy_type: SpyType
    name: str                    # Casus ismi
    skill: int                   # Mevcut beceri
    experience: int = 0          # Deneyim
    location: str = "home"       # Konum
    status: str = "idle"         # idle, on_mission, captured, dead
    current_mission: Optional[str] = None
    turns_remaining: int = 0


@dataclass 
class Mission:
    """Aktif görev"""
    mission_id: str
    operation: OperationType
    spy_id: str
    target: str
    turns_remaining: int
    success_chance: float


class EspionageSystem:
    """Casusluk yönetim sistemi (1520 dönemi)"""
    
    def __init__(self):
        # Aktif casuslar
        self.spies: List[Spy] = []
        self.spy_counter = 0
        
        # Aktif görevler
        self.active_missions: List[Mission] = []
        self.mission_counter = 0
        
        # İstihbarat ve güvenlik
        self.intelligence_level = 0       # Düşman hakkında bilgi
        self.security_level = 50          # İç güvenlik (0-100)
        self.known_enemy_spies = 0        # Yakalanan düşman casusları
        
        # Hedef devletler (1520 dönemi)
        self.targets: Dict[str, Dict] = {
            'safevi': {'name': 'Safevi Devleti', 'difficulty': 7, 'relations': -20},
            'venedik': {'name': 'Venedik Cumhuriyeti', 'difficulty': 8, 'relations': 30},
            'macaristan': {'name': 'Macaristan Krallığı', 'difficulty': 5, 'relations': -30},
            'memluk': {'name': 'Mısır Eyaleti', 'difficulty': 3, 'relations': 50},  # Artık Osmanlı parçası
            'rodos': {'name': 'Rodos Şövalyeleri', 'difficulty': 6, 'relations': -50},
        }
        
        # İstatistikler
        self.successful_missions = 0
        self.failed_missions = 0
        self.spies_lost = 0
    
    def recruit_spy(self, spy_type: SpyType, economy) -> Optional[Spy]:
        """Casus topla"""
        audio = get_audio_manager()
        
        if spy_type not in SPY_DEFINITIONS:
            return None
        
        stats = SPY_DEFINITIONS[spy_type]
        
        if not economy.can_afford(gold=stats.cost_gold):
            audio.announce_action_result("Casus toplama", False, "Yetersiz altın")
            return None
        
        economy.spend(gold=stats.cost_gold)
        
        self.spy_counter += 1
        spy = Spy(
            spy_id=f"spy_{self.spy_counter}",
            spy_type=spy_type,
            name=self._generate_spy_name(spy_type),
            skill=stats.skill + random.randint(-1, 2),
        )
        
        self.spies.append(spy)
        
        audio.announce_action_result(
            f"{stats.name_tr} toplandı",
            True,
            f"{spy.name} hizmetinize girdi"
        )
        
        return spy
    
    def _generate_spy_name(self, spy_type: SpyType = None) -> str:
        """Rastgele 16. yüzyıl Osmanlı ismi üret"""
        if spy_type == SpyType.CARIYE:
            # Saray cariyeleri — Slav, Kafkas ve sarayda verilen isimler
            first_names = [
                "Hürrem", "Mahidevran", "Nurbanu", "Gülbahar", "Nilüfer",
                "Gülfem", "Dilşad", "Gülruh", "Şahhuban", "Gevherhan",
                "Raziye", "Hümaşah", "Gülşen", "Safiye", "Kösem",
                "Hatice", "Mihrimah", "Fatma", "Ayşe", "Hafsa"
            ]
            titles = ["Hatun", "Kadın", "Sultan", ""]
        elif spy_type == SpyType.DERVIS:
            # Gezgin dervişler — Sufi/tasavvuf isimleri
            first_names = [
                "Abdülkadir", "Şeyh Bedreddin", "Hacı Bayram", "Akşemseddin",
                "Emir Sultan", "Molla Hüsrev", "Baba İlyas", "Şeyh Vefa",
                "Abdal Musa", "Sarı Saltuk", "Hızır", "İlyas"
            ]
            titles = ["Dede", "Baba", "Efendi", ""]
        else:
            # Devşirme/askeri kökenli casuslar
            first_names = [
                "Hüsrev", "Rüstem", "Ferhad", "Lütfi", "Sinan",
                "İskender", "Davud", "Piyale", "Pertev", "Nasuh",
                "Mehmed", "Ahmed", "Mustafa", "Ali", "Hasan",
                "Mahmud", "Süleyman", "İbrahim", "Osman", "Kasım"
            ]
            titles = ["Ağa", "Efendi", "Bey", "Çelebi", ""]
        return f"{random.choice(first_names)} {random.choice(titles)}".strip()
    
    def start_mission(self, spy_id: str, operation: OperationType, 
                      target: str, economy, player=None) -> Optional[Mission]:
        """Görev başlat - player: kadın casusluk bonusu için"""
        audio = get_audio_manager()
        
        # Casusu bul
        spy = None
        for s in self.spies:
            if s.spy_id == spy_id and s.status == "idle":
                spy = s
                break
        
        if not spy:
            audio.announce_action_result("Görev", False, "Uygun casus bulunamadı")
            return None
        
        op_stats = OPERATION_DEFINITIONS[operation]
        
        # Maliyet kontrolü
        if not economy.can_afford(gold=op_stats.base_cost):
            audio.announce_action_result("Görev", False, "Yetersiz altın")
            return None
        
        # Beceri kontrolü
        if spy.skill < op_stats.required_skill:
            audio.announce_action_result("Görev", False, 
                f"Bu görev için en az {op_stats.required_skill} beceri gerekli")
            return None
        
        economy.spend(gold=op_stats.base_cost)
        
        # Başarı şansı hesapla
        target_difficulty = self.targets.get(target, {}).get('difficulty', 5)
        base_chance = (spy.skill * 10) - (target_difficulty * 5) - (op_stats.risk * 30)
        
        # Kadın karakter: Casusluk bonusu (+%15 başarı şansı)
        if player:
            espionage_bonus = player.get_bonus('espionage')
            if espionage_bonus > 0:
                base_chance += espionage_bonus * 100  # 0.15 * 100 = +15
        
        success_chance = max(10, min(90, base_chance))
        
        self.mission_counter += 1
        mission = Mission(
            mission_id=f"mission_{self.mission_counter}",
            operation=operation,
            spy_id=spy_id,
            target=target,
            turns_remaining=op_stats.duration,
            success_chance=success_chance
        )
        
        spy.status = "on_mission"
        spy.current_mission = mission.mission_id
        spy.location = target
        
        self.active_missions.append(mission)
        
        target_name = self.targets.get(target, {}).get('name', target)
        audio.announce_action_result(
            f"{op_stats.name_tr} görevi",
            True,
            f"{spy.name} {target_name}'ye gönderildi. {mission.turns_remaining} tur sürecek"
        )
        
        return mission
    
    def process_turn(self) -> Dict:
        """Tur sonunda görevleri işle"""
        results = {
            'completed': [],
            'failed': [],
            'captured': [],
            'experience_gained': 0
        }
        
        completed_missions = []
        
        for mission in self.active_missions:
            mission.turns_remaining -= 1
            
            if mission.turns_remaining <= 0:
                # Görev tamamlandı, sonucu belirle
                success = random.random() * 100 < mission.success_chance
                
                # Casusu bul
                spy = next((s for s in self.spies if s.spy_id == mission.spy_id), None)
                if not spy:
                    continue
                
                op_stats = OPERATION_DEFINITIONS[mission.operation]
                
                if success:
                    # Başarılı
                    spy.experience += 10
                    spy.status = "idle"
                    spy.location = "home"
                    spy.current_mission = None
                    self.successful_missions += 1
                    
                    results['completed'].append({
                        'spy': spy.name,
                        'operation': op_stats.name_tr,
                        'target': mission.target,
                        'effects': op_stats.effects
                    })
                    results['experience_gained'] += 10
                else:
                    # Başarısız - yakalanma riski
                    capture_chance = op_stats.risk * 0.5
                    if random.random() < capture_chance:
                        # Yakalandı
                        spy.status = "captured"
                        self.spies_lost += 1
                        results['captured'].append(spy.name)
                    else:
                        # Kaçtı
                        spy.status = "idle"
                        spy.location = "home"
                        spy.current_mission = None
                    
                    self.failed_missions += 1
                    results['failed'].append({
                        'spy': spy.name,
                        'operation': op_stats.name_tr,
                        'target': mission.target
                    })
                
                completed_missions.append(mission)
        
        # Tamamlanan görevleri kaldır
        for mission in completed_missions:
            self.active_missions.remove(mission)
        
        # Güvenlik zamanla düşer
        self.security_level = max(0, self.security_level - 1)
        
        # Sonuçları duyur
        audio = get_audio_manager()
        if results['completed']:
            for r in results['completed']:
                audio.speak(f"Başarılı: {r['spy']} - {r['operation']}", interrupt=False)
        if results['failed']:
            for r in results['failed']:
                audio.speak(f"Başarısız: {r['spy']} - {r['operation']}", interrupt=False)
        if results['captured']:
            for name in results['captured']:
                audio.speak(f"Yakalandı: {name}", interrupt=False)
        
        return results
    
    def get_spy_count(self) -> int:
        """Aktif casus sayısı"""
        return len([s for s in self.spies if s.status != "dead"])
    
    def get_available_spies(self) -> List[Spy]:
        """Müsait casuslar"""
        return [s for s in self.spies if s.status == "idle"]
    
    def detect_enemy_spies(self) -> Dict:
        """
        Karşı istihbarat - düşman casuslarını tespit et
        Güvenlik seviyesine göre şans
        """
        audio = get_audio_manager()
        
        detection_chance = self.security_level / 100 * 0.3  # Max %30
        detected = 0
        
        # Simüle edilen düşman casusu
        if random.random() < detection_chance:
            detected += 1
            self.known_enemy_spies += 1
            self.security_level = min(100, self.security_level + 5)
            
            # Rastgele düşman kaynağı
            enemies = ['Safevi', 'Venedik', 'Macar', 'Şövalye']
            source = random.choice(enemies)
            
            audio.speak(
                f"Karşı istihbarat başarılı! {source} casusu yakalandı! "
                f"Güvenlik +5. Toplam yakalanan: {self.known_enemy_spies}",
                interrupt=True
            )
            
        return {
            'detected': detected,
            'security_level': self.security_level,
            'known_enemy_spies': self.known_enemy_spies
        }
    
    def rescue_spy(self, spy_id: str, economy) -> bool:
        """
        Yakalanmış casusu kurtarmaya çalış
        Fidye veya kurtarma operasyonu
        """
        audio = get_audio_manager()
        
        # Yakalanmış casusu bul
        spy = next((s for s in self.spies if s.spy_id == spy_id and s.status == "captured"), None)
        
        if not spy:
            audio.speak("Kurtarılacak yakalanmış casus bulunamadı.", interrupt=True)
            return False
        
        # Fidye maliyeti
        ransom_cost = 500
        
        if not economy.can_afford(gold=ransom_cost):
            audio.speak(f"Fidye için {ransom_cost} altın gerekli.", interrupt=True)
            return False
        
        economy.spend(gold=ransom_cost)
        
        # %60 başarı şansı
        if random.random() < 0.6:
            spy.status = "idle"
            spy.location = "home"
            audio.speak(f"{spy.name} kurtarıldı ve geri döndü!", interrupt=True)
            return True
        else:
            # Başarısız - casus öldü
            spy.status = "dead"
            audio.speak(f"Kurtarma başarısız! {spy.name} idam edildi.", interrupt=True)
            return False
    
    def announce_status(self):
        """Casusluk durumunu duyur"""
        audio = get_audio_manager()
        audio.speak("Casusluk Durumu:", interrupt=True)
        audio.speak(f"Toplam casus: {self.get_spy_count()}", interrupt=False)
        audio.speak(f"Müsait: {len(self.get_available_spies())}", interrupt=False)
        audio.speak(f"Aktif görev: {len(self.active_missions)}", interrupt=False)
        audio.speak(f"Güvenlik: %{self.security_level}", interrupt=False)
        audio.speak(f"Başarılı: {self.successful_missions}, Başarısız: {self.failed_missions}", 
                   interrupt=False)
    
    def to_dict(self) -> Dict:
        """Kayıt için dictionary'e dönüştür"""
        return {
            'spies': [
                {
                    'spy_id': s.spy_id,
                    'spy_type': s.spy_type.value,
                    'name': s.name,
                    'skill': s.skill,
                    'experience': s.experience,
                    'location': s.location,
                    'status': s.status,
                    'current_mission': s.current_mission,
                    'turns_remaining': s.turns_remaining
                }
                for s in self.spies
            ],
            'active_missions': [
                {
                    'mission_id': m.mission_id,
                    'operation': m.operation.value,
                    'spy_id': m.spy_id,
                    'target': m.target,
                    'turns_remaining': m.turns_remaining,
                    'success_chance': m.success_chance
                }
                for m in self.active_missions
            ],
            'spy_counter': self.spy_counter,
            'mission_counter': self.mission_counter,
            'intelligence_level': self.intelligence_level,
            'security_level': self.security_level,
            'known_enemy_spies': self.known_enemy_spies,
            'successful_missions': self.successful_missions,
            'failed_missions': self.failed_missions,
            'spies_lost': self.spies_lost
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'EspionageSystem':
        """Dictionary'den yükle"""
        system = cls()
        
        for s_data in data.get('spies', []):
            spy = Spy(
                spy_id=s_data['spy_id'],
                spy_type=SpyType(s_data['spy_type']),
                name=s_data['name'],
                skill=s_data['skill'],
                experience=s_data.get('experience', 0),
                location=s_data.get('location', 'home'),
                status=s_data.get('status', 'idle'),
                current_mission=s_data.get('current_mission'),
                turns_remaining=s_data.get('turns_remaining', 0)
            )
            system.spies.append(spy)
        
        for m_data in data.get('active_missions', []):
            mission = Mission(
                mission_id=m_data['mission_id'],
                operation=OperationType(m_data['operation']),
                spy_id=m_data['spy_id'],
                target=m_data['target'],
                turns_remaining=m_data['turns_remaining'],
                success_chance=m_data['success_chance']
            )
            system.active_missions.append(mission)
        
        system.spy_counter = data.get('spy_counter', 0)
        system.mission_counter = data.get('mission_counter', 0)
        system.intelligence_level = data.get('intelligence_level', 0)
        system.security_level = data.get('security_level', 50)
        system.known_enemy_spies = data.get('known_enemy_spies', 0)
        system.successful_missions = data.get('successful_missions', 0)
        system.failed_missions = data.get('failed_missions', 0)
        system.spies_lost = data.get('spies_lost', 0)
        
        return system
