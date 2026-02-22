# -*- coding: utf-8 -*-
"""
Osmanlı Eyalet Yönetim Simülasyonu - Din ve Kültür Sistemi
1520 Dönemi Tarihi Gerçekliğine Uygun

Osmanlı dini yapısı:
- Şeyhülislam: En yüksek dini otorite
- Millet sistemi: Dini toplulukların özerkliği
- Vakıflar: Sosyal hizmetlerin temeli
- Medreseler: Eğitim kurumları
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from enum import Enum
import random
from audio.audio_manager import get_audio_manager


class Millet(Enum):
    """Dini topluluklar (1520 Osmanlı millet sistemi)"""
    MUSLIM = "muslim"              # Müslüman - Çoğunluk
    RUM_ORTHODOX = "rum"           # Rum Ortodoks
    ERMENI = "ermeni"              # Ermeni Gregoryen
    YAHUDI = "yahudi"              # Yahudi
    SURYANÎ = "suryani"            # Süryani


class UlemaRank(Enum):
    """Ulema makamları"""
    SEYHULISLAM = "seyhulislam"    # En yüksek makam - fetva verir
    KADIASKER = "kadiasker"        # Askeri kadı - Rumeli/Anadolu
    KADI = "kadi"                  # Yargıç
    MUDERRIS = "muderris"          # Medrese hocası
    MUFTU = "muftu"                # Yerel fetva makamı
    IMAM = "imam"                  # Cami imamı


class VakifType(Enum):
    """Vakıf türleri"""
    CAMI = "cami"                  # Cami - Dini ibadet
    MEDRESE = "medrese"            # Medrese - Eğitim
    IMARET = "imaret"              # İmaret - Yoksul besleme
    KERVANSARAY = "kervansaray"    # Kervansaray - Ticaret
    HASTANE = "hastane"            # Darüşşifa - Sağlık
    HAMAM = "hamam"                # Hamam - Hijyen
    CESME = "cesme"                # Çeşme/Su kemeri


@dataclass
class MilletStats:
    """Millet istatistikleri"""
    name: str
    name_tr: str
    leader_title: str
    population_ratio: float     # Toplam nüfusa oranı
    tax_modifier: float         # Vergi değiştirici
    trade_bonus: float          # Ticaret bonusu
    loyalty_base: int           # Temel sadakat
    special_ability: str
    historical_note: str


MILLET_DEFINITIONS = {
    Millet.MUSLIM: MilletStats(
        name="Muslim",
        name_tr="Müslüman",
        leader_title="—",  # Müslümanlar millet sistemi dışında, yönetici çoğunluk
        population_ratio=0.60,
        tax_modifier=1.0,
        trade_bonus=0.0,
        loyalty_base=80,
        special_ability="askerlik",
        historical_note="Yönetici çoğunluk - millet sistemi yalnızca gayrimüslimler için geçerlidir"
    ),
    Millet.RUM_ORTHODOX: MilletStats(
        name="Greek Orthodox",
        name_tr="Rum Ortodoks",
        leader_title="Patrik",
        population_ratio=0.20,
        tax_modifier=1.1,
        trade_bonus=0.15,
        loyalty_base=50,
        special_ability="denizcilik",
        historical_note="Balkanlar ve Ege'de yoğun, ticaret ve denizcilik bilgisi"
    ),
    Millet.ERMENI: MilletStats(
        name="Armenian",
        name_tr="Ermeni",
        leader_title="Patrik",
        population_ratio=0.08,
        tax_modifier=1.1,
        trade_bonus=0.20,
        loyalty_base=60,
        special_ability="zanaat",
        historical_note="Sarraflar ve zanaatkarlar arasında önemli yer"
    ),
    Millet.YAHUDI: MilletStats(
        name="Jewish",
        name_tr="Yahudi",
        leader_title="Hahambaşı",
        population_ratio=0.05,
        tax_modifier=1.0,
        trade_bonus=0.25,
        loyalty_base=70,
        special_ability="finans",
        historical_note="1492 İspanya sürgünü sonrası Osmanlı'ya sığındılar"
    ),
    Millet.SURYANÎ: MilletStats(
        name="Syriac",
        name_tr="Süryani",
        leader_title="Patrik",
        population_ratio=0.03,
        tax_modifier=1.1,
        trade_bonus=0.10,
        loyalty_base=55,
        special_ability="tercume",
        historical_note="Antik dil bilgisi, tercümanlık"
    ),
}


@dataclass
class UlemaStats:
    """Ulema makam istatistikleri"""
    name: str
    name_tr: str
    salary: int
    influence: int          # Etkisi (1-10)
    max_count: int          # Maksimum sayı
    effects: Dict


ULEMA_DEFINITIONS = {
    UlemaRank.SEYHULISLAM: UlemaStats(
        name="Shaykh al-Islam",
        name_tr="Şeyhülislam",
        salary=100,
        influence=10,
        max_count=1,
        effects={'legitimacy': 20, 'stability': 10}
    ),
    UlemaRank.KADIASKER: UlemaStats(
        name="Chief Military Judge",
        name_tr="Kadıasker",
        salary=50,
        influence=8,
        max_count=2,
        effects={'justice': 15, 'military_discipline': 5}
    ),
    UlemaRank.KADI: UlemaStats(
        name="Judge",
        name_tr="Kadı",
        salary=20,
        influence=5,
        max_count=10,
        effects={'justice': 5, 'order': 3}
    ),
    UlemaRank.MUDERRIS: UlemaStats(
        name="Professor",
        name_tr="Müderris",
        salary=15,
        influence=4,
        max_count=20,
        effects={'education': 5, 'science': 2}
    ),
    UlemaRank.MUFTU: UlemaStats(
        name="Mufti",
        name_tr="Müftü",
        salary=10,
        influence=3,
        max_count=5,
        effects={'piety': 3, 'happiness': 2}
    ),
    UlemaRank.IMAM: UlemaStats(
        name="Imam",
        name_tr="İmam",
        salary=5,
        influence=2,
        max_count=50,
        effects={'piety': 1, 'happiness': 1}
    ),
}


@dataclass
class VakifStats:
    """Vakıf türü istatistikleri"""
    name: str
    name_tr: str
    build_cost: int
    maintenance: int
    effects: Dict
    required_population: int


VAKIF_DEFINITIONS = {
    VakifType.CAMI: VakifStats(
        name="Mosque",
        name_tr="Cami",
        build_cost=500,
        maintenance=10,
        effects={'piety': 10, 'happiness': 5, 'loyalty': 3},
        required_population=1000
    ),
    VakifType.MEDRESE: VakifStats(
        name="Madrasa",
        name_tr="Medrese",
        build_cost=800,
        maintenance=20,
        effects={'education': 15, 'science': 5, 'ulema_capacity': 5},
        required_population=3000
    ),
    VakifType.IMARET: VakifStats(
        name="Soup Kitchen",
        name_tr="İmaret",
        build_cost=400,
        maintenance=15,
        effects={'happiness': 10, 'population_growth': 2},
        required_population=2000
    ),
    VakifType.KERVANSARAY: VakifStats(
        name="Caravanserai",
        name_tr="Kervansaray",
        build_cost=600,
        maintenance=10,
        effects={'trade_income': 15, 'caravan_safety': 10},
        required_population=1500
    ),
    VakifType.HASTANE: VakifStats(
        name="Hospital",
        name_tr="Darüşşifa",
        build_cost=1000,
        maintenance=25,
        effects={'health': 20, 'population_growth': 3},
        required_population=5000
    ),
    VakifType.HAMAM: VakifStats(
        name="Bathhouse",
        name_tr="Hamam",
        build_cost=300,
        maintenance=8,
        effects={'health': 5, 'happiness': 5, 'income': 10},
        required_population=500
    ),
    VakifType.CESME: VakifStats(
        name="Fountain",
        name_tr="Çeşme",
        build_cost=150,
        maintenance=3,
        effects={'health': 3, 'happiness': 2},
        required_population=200
    ),
}


@dataclass
class Vakif:
    """Aktif vakıf"""
    vakif_id: str
    vakif_type: VakifType
    name: str
    level: int = 1
    condition: int = 100      # Durum (0-100)
    income: int = 0           # Gelir (varsa)


@dataclass
class Ulema:
    """Aktif ulema görevlisi"""
    ulema_id: str
    rank: UlemaRank
    name: str
    skill: int = 5            # Beceri (1-10)
    loyalty: int = 70         # Sadakat (0-100)


class ReligionSystem:
    """Din ve Kültür yönetim sistemi (1520 dönemi)"""
    
    def __init__(self):
        # Millet durumları
        self.millet_states: Dict[Millet, Dict] = {}
        for millet in Millet:
            stats = MILLET_DEFINITIONS[millet]
            self.millet_states[millet] = {
                'loyalty': stats.loyalty_base,
                'population': 0,  # Population sisteminden güncellenir
                'unrest': 0,      # Huzursuzluk
                'autonomy': 30 if millet != Millet.MUSLIM else 0,  # Özerklik
            }
        
        # Ulema sistemi
        self.ulema: List[Ulema] = []
        self.ulema_counter = 0
        self.has_seyhulislam = True  # Başlangıçta var
        
        # Vakıflar
        self.vakifs: List[Vakif] = []
        self.vakif_counter = 0
        
        # Genel değerler
        self.piety = 50           # Dindarlık (0-100)
        self.legitimacy = 70      # Meşruiyet (0-100)
        self.tolerance = 60       # Hoşgörü (0-100)
        self.education_level = 30 # Eğitim seviyesi (0-100)
        
        # Kızılbaş sorunu (1520'de önemli)
        self.kizilbas_threat = 15   # Yavuz'un 1514 Çaldıran seferi sonrası azalmış tehdit
        self.kizilbas_suppressed = False
        
        # İstatistikler
        self.conversions = 0
        self.rebellions_suppressed = 0
        
        # Hile / Spam engelleme
        self.fetva_issued_this_turn = False
    
    def appoint_ulema(self, rank: UlemaRank, economy) -> Optional[Ulema]:
        """Ulema ata (Şeyhülislam hariç - o yalnızca Padişah tarafından atanır)"""
        audio = get_audio_manager()
        
        # Şeyhülislam yalnızca Padişah tarafından atanır, eyalet valisi atayamaz
        if rank == UlemaRank.SEYHULISLAM:
            audio.announce_action_result("Ulema atama", False, 
                "Şeyhülislam yalnızca Padişah tarafından atanır")
            return None
        
        stats = ULEMA_DEFINITIONS[rank]
        
        # Maksimum sayı kontrolü
        current_count = len([u for u in self.ulema if u.rank == rank])
        if current_count >= stats.max_count:
            audio.announce_action_result("Ulema atama", False, 
                f"Maksimum {stats.max_count} {stats.name_tr} atanabilir")
            return None
        
        # Maliyet kontrolü (bir yıllık maaş)
        cost = stats.salary * 4
        if not economy.can_afford(gold=cost):
            audio.announce_action_result("Ulema atama", False, "Yetersiz altın")
            return None
        
        economy.spend(gold=cost)
        
        self.ulema_counter += 1
        ulema = Ulema(
            ulema_id=f"ulema_{self.ulema_counter}",
            rank=rank,
            name=self._generate_ulema_name(rank),
            skill=random.randint(4, 8),
            loyalty=random.randint(60, 90)
        )
        
        self.ulema.append(ulema)
        
        audio.announce_action_result(
            f"{stats.name_tr} atandı",
            True,
            f"{ulema.name} göreve başladı"
        )
        
        return ulema
    
    def _generate_ulema_name(self, rank: UlemaRank) -> str:
        """16. yüzyıl Osmanlı ulema ismi üret"""
        # Dönemin bilinen müderris ve kadı isimleri
        scholar_names = [
            "Mehmed", "Ahmed", "Mustafa", "Ali", "Süleyman", "İbrahim",
            "Abdülkerim", "Abdurrahman", "Mahmud", "Kasım", "Haydar", "Lütfi"
        ]
        
        if rank == UlemaRank.SEYHULISLAM:
            # 1520-1566 dönemi gerçek şeyhülislamları
            return random.choice([
                "Zenbilli Ali Efendi", "Kemalpaşazade", "İbn-i Kemal",
                "Ebussuud Efendi", "Çivizade Muhyiddin", "Fenari Muhyiddin"
            ])
        elif rank == UlemaRank.KADIASKER:
            current_kadiaskers = [u.name for u in self.ulema if u.rank == UlemaRank.KADIASKER]
            if "Rumeli Kadıaskeri" not in [n.split(' - ')[0] for n in current_kadiaskers]:
                return f"Rumeli Kadıaskeri - {random.choice(scholar_names)} Efendi"
            else:
                return f"Anadolu Kadıaskeri - {random.choice(scholar_names)} Efendi"
        elif rank == UlemaRank.MUDERRIS:
            # Müderrisler — dönemin medrese hocaları
            surnames = ["Efendi", "Molla", "Hoca"]
            return f"{random.choice(surnames)} {random.choice(scholar_names)}"
        else:
            return f"{random.choice(scholar_names)} Efendi"
    
    def build_vakif(self, vakif_type: VakifType, economy, population: int, 
                    custom_name: str = None) -> Optional[Vakif]:
        """Vakıf inşa et"""
        audio = get_audio_manager()
        
        stats = VAKIF_DEFINITIONS[vakif_type]
        
        # Nüfus kontrolü
        if population < stats.required_population:
            audio.announce_action_result("Vakıf inşası", False,
                f"En az {stats.required_population} nüfus gerekli")
            return None
        
        # Maliyet kontrolü
        if not economy.can_afford(gold=stats.build_cost):
            audio.announce_action_result("Vakıf inşası", False, "Yetersiz altın")
            return None
        
        economy.spend(gold=stats.build_cost)
        
        self.vakif_counter += 1
        name = custom_name or f"{stats.name_tr} #{self.vakif_counter}"
        
        vakif = Vakif(
            vakif_id=f"vakif_{self.vakif_counter}",
            vakif_type=vakif_type,
            name=name
        )
        
        self.vakifs.append(vakif)
        
        # Dindarlık artışı
        self.piety = min(100, self.piety + 3)
        
        # Vakıf inşaat sesi
        audio.play_game_sound('construction', 'hammer')
        
        audio.announce_action_result(
            f"{stats.name_tr} inşası",
            True,
            f"{name} tamamlandı"
        )
        
        return vakif
    
    def process_turn(self, economy) -> Dict:
        """Tur sonunda din sistemini işle"""
        self.fetva_issued_this_turn = False
        
        results = {
            'income': 0,
            'expenses': 0,
            'events': [],
            'effects': {}
        }
        
        # Ulema maaşları
        for ulema in self.ulema:
            stats = ULEMA_DEFINITIONS[ulema.rank]
            results['expenses'] += stats.salary
        
        # Vakıf bakımları ve gelirleri
        for vakif in self.vakifs:
            stats = VAKIF_DEFINITIONS[vakif.vakif_type]
            results['expenses'] += stats.maintenance
            
            # Vakıf gelirleri (hamam gibi)
            if 'income' in stats.effects:
                income = stats.effects['income']
                results['income'] += income
                vakif.income = income
            
            # Vakıf yıpranması
            vakif.condition = max(0, vakif.condition - 1)
        
        # Masrafları öde
        if economy.can_afford(gold=results['expenses']):
            economy.spend(gold=results['expenses'])
        else:
            # Maaş ödeyemedik
            self.legitimacy = max(0, self.legitimacy - 5)
            results['events'].append("Ulema maaşları ödenmedi! Meşruiyet düştü.")
        
        # Gelirleri al
        economy.add_resources(gold=results['income'])
        
        # Millet sadakati hesapla
        for millet, state in self.millet_states.items():
            # Hoşgörü sadakati artırır
            if self.tolerance > 50:
                state['loyalty'] = min(100, state['loyalty'] + 1)
            
            # Düşük sadakat huzursuzluk yaratır
            if state['loyalty'] < 30:
                state['unrest'] = min(100, state['unrest'] + 5)
                if state['unrest'] > 70:
                    results['events'].append(f"{MILLET_DEFINITIONS[millet].name_tr} huzursuzluğu artıyor!")
        
        # Kızılbaş tehdidi
        if self.kizilbas_threat > 50 and not self.kizilbas_suppressed:
            if random.random() < 0.1:
                results['events'].append("Kızılbaş ayaklanması riski!")
                self.millet_states[Millet.MUSLIM]['unrest'] += 10
        
        # Eğitim seviyesi (medrese sayısına bağlı)
        medrese_count = len([v for v in self.vakifs if v.vakif_type == VakifType.MEDRESE])
        muderris_count = len([u for u in self.ulema if u.rank == UlemaRank.MUDERRIS])
        self.education_level = min(100, 20 + (medrese_count * 10) + (muderris_count * 5))
        
        # Dindarlık (cami ve imam sayısına bağlı)
        cami_count = len([v for v in self.vakifs if v.vakif_type == VakifType.CAMI])
        imam_count = len([u for u in self.ulema if u.rank == UlemaRank.IMAM])
        self.piety = min(100, 30 + (cami_count * 5) + (imam_count * 2))
        
        return results
    
    def issue_fetva(self, topic: str, economy) -> Dict:
        """Fetva yayınla (Şeyhülislam gerektirir)"""
        audio = get_audio_manager()
        
        if not self.has_seyhulislam:
            audio.announce_action_result("Fetva", False, "Şeyhülislam gerekli")
            return {'success': False}
            
        if getattr(self, 'fetva_issued_this_turn', False):
            audio.announce_action_result("Fetva", False, "Bu tur zaten bir fetva verildi")
            return {'success': False}
        
        # Fetva maliyeti
        cost = 50
        if not economy.can_afford(gold=cost):
            audio.announce_action_result("Fetva", False, "Yetersiz altın")
            return {'success': False}
        
        economy.spend(gold=cost)
        
        effects = {}
        
        # Fetva konusuna göre etki
        if topic == "cihad":
            effects['military_morale'] = 20
            effects['piety'] = 10
            audio.speak("Cihad fetvası: Askeri moral +20, Dindarlık +10", interrupt=False)
        elif topic == "ticaret":
            effects['trade_bonus'] = 10
            audio.speak("Ticaret fetvası: Ticaret geliri +10%", interrupt=False)
        elif topic == "vergi":
            effects['tax_legitimacy'] = 15
            audio.speak("Vergi fetvası: Vergi meşruiyeti +15", interrupt=False)
        elif topic == "kizilbas":
            self.kizilbas_threat = max(0, self.kizilbas_threat - 20)
            self.kizilbas_suppressed = True
            effects['kizilbas_threat'] = -20
            audio.speak("Kızılbaş karşıtı fetva: Tehdit azaldı", interrupt=False)
        
        self.legitimacy = min(100, self.legitimacy + 5)
        effects['legitimacy'] = 5
        
        self.fetva_issued_this_turn = True
        
        audio.announce_action_result("Fetva", True, f"Konu: {topic}")
        
        return {'success': True, 'effects': effects}
    
    def get_total_effects(self) -> Dict:
        """Tüm din sistemi etkilerini topla"""
        effects = {
            'piety': self.piety,
            'legitimacy': self.legitimacy,
            'education': self.education_level,
            'tolerance': self.tolerance,
            'happiness': 0,
            'trade_bonus': 0,
            'health': 0,
        }
        
        # Vakıf etkileri
        for vakif in self.vakifs:
            if vakif.condition > 50:  # Sadece iyi durumdaki vakıflar
                stats = VAKIF_DEFINITIONS[vakif.vakif_type]
                for key, value in stats.effects.items():
                    effects[key] = effects.get(key, 0) + value
        
        # Millet etkileri
        for millet, state in self.millet_states.items():
            stats = MILLET_DEFINITIONS[millet]
            if state['loyalty'] > 50:
                effects['trade_bonus'] += stats.trade_bonus * 10
                
        # Ulema Etkileri (Önceden yoktu, düzeltildi)
        for ulema in self.ulema:
            stats = ULEMA_DEFINITIONS[ulema.rank]
            for key, value in stats.effects.items():
                effects[key] = effects.get(key, 0) + value
        
        return effects
    
    def announce_status(self):
        """Din durumunu duyur"""
        audio = get_audio_manager()
        audio.speak("Din ve Kültür Durumu:", interrupt=True)
        audio.speak(f"Dindarlık: %{self.piety}", interrupt=False)
        audio.speak(f"Meşruiyet: %{self.legitimacy}", interrupt=False)
        audio.speak(f"Hoşgörü: %{self.tolerance}", interrupt=False)
        audio.speak(f"Eğitim: %{self.education_level}", interrupt=False)
        audio.speak(f"Vakıf sayısı: {len(self.vakifs)}", interrupt=False)
        audio.speak(f"Ulema sayısı: {len(self.ulema)}", interrupt=False)
        
        if self.kizilbas_threat > 30:
            audio.speak(f"Kızılbaş tehdidi: %{self.kizilbas_threat}", interrupt=False)
    
    def to_dict(self) -> Dict:
        """Kayıt için dictionary'e dönüştür"""
        return {
            'millet_states': {
                m.value: s for m, s in self.millet_states.items()
            },
            'ulema': [
                {
                    'ulema_id': u.ulema_id,
                    'rank': u.rank.value,
                    'name': u.name,
                    'skill': u.skill,
                    'loyalty': u.loyalty
                }
                for u in self.ulema
            ],
            'vakifs': [
                {
                    'vakif_id': v.vakif_id,
                    'vakif_type': v.vakif_type.value,
                    'name': v.name,
                    'level': v.level,
                    'condition': v.condition,
                    'income': v.income
                }
                for v in self.vakifs
            ],
            'ulema_counter': self.ulema_counter,
            'vakif_counter': self.vakif_counter,
            'piety': self.piety,
            'legitimacy': self.legitimacy,
            'tolerance': self.tolerance,
            'education_level': self.education_level,
            'kizilbas_threat': self.kizilbas_threat,
            'kizilbas_suppressed': self.kizilbas_suppressed,
            'has_seyhulislam': self.has_seyhulislam,
            'conversions': self.conversions,
            'rebellions_suppressed': self.rebellions_suppressed,
            'fetva_issued_this_turn': getattr(self, 'fetva_issued_this_turn', False)
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ReligionSystem':
        """Dictionary'den yükle"""
        system = cls()
        
        # Millet durumları
        for millet_value, state in data.get('millet_states', {}).items():
            try:
                millet = Millet(millet_value)
                system.millet_states[millet] = state
            except ValueError:
                pass
        
        # Ulema
        for u_data in data.get('ulema', []):
            ulema = Ulema(
                ulema_id=u_data['ulema_id'],
                rank=UlemaRank(u_data['rank']),
                name=u_data['name'],
                skill=u_data.get('skill', 5),
                loyalty=u_data.get('loyalty', 70)
            )
            system.ulema.append(ulema)
        
        # Vakıflar
        for v_data in data.get('vakifs', []):
            vakif = Vakif(
                vakif_id=v_data['vakif_id'],
                vakif_type=VakifType(v_data['vakif_type']),
                name=v_data['name'],
                level=v_data.get('level', 1),
                condition=v_data.get('condition', 100),
                income=v_data.get('income', 0)
            )
            system.vakifs.append(vakif)
        
        system.ulema_counter = data.get('ulema_counter', 0)
        system.vakif_counter = data.get('vakif_counter', 0)
        system.piety = data.get('piety', 50)
        system.legitimacy = data.get('legitimacy', 70)
        system.tolerance = data.get('tolerance', 60)
        system.education_level = data.get('education_level', 30)
        system.kizilbas_threat = data.get('kizilbas_threat', 15)
        system.kizilbas_suppressed = data.get('kizilbas_suppressed', False)
        system.has_seyhulislam = data.get('has_seyhulislam', True)
        system.conversions = data.get('conversions', 0)
        system.rebellions_suppressed = data.get('rebellions_suppressed', 0)
        system.fetva_issued_this_turn = data.get('fetva_issued_this_turn', False)
        
        return system
