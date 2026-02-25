# -*- coding: utf-8 -*-
"""
Osmanlı Eyalet Yönetim Simülasyonu - Topçu Sistemi (Geliştirilmiş)
Top üretimi ve topçu yönetimi (Topçu Ocağı)

Tarihi Kaynak: Gábor Ágoston, "Guns for the Sultan"
7 top türü, bronz/demir malzeme tercihi, yıpranma/patlama mekaniği,
barut tüketimi ve detaylı savaş istatistikleri.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from enum import Enum
import random
from audio.audio_manager import get_audio_manager


class CannonType(Enum):
    """Top türleri — tarihi Osmanlı sınıflandırması"""
    DARBZEN = "darbzen"           # Hafif sahra topu
    ABUS = "abus"                 # Küçük sahra / savunma topu
    PRANGI = "prangi"             # Hafif donanma / kale topu
    KOLUNBURNA = "kolunburna"     # Uzun menzilli delici (Culverin)
    HAVAN = "havan"               # Aşırtma / havan topu (Mortar)
    BALYEMEZ = "balyemez"         # Ağır batarya / kuşatma topu
    SAHI = "sahi"                 # Kale yıkıcı dev bombard


class CannonMaterial(Enum):
    """Top malzeme türleri"""
    BRONZE = "bronze"   # Tunç (bakır + kalay) — pahalı, güvenilir
    IRON = "iron"       # Dökme demir — ucuz, riskli


class AmmoType(Enum):
    """Mühimmat türleri — tarihi Osmanlı cephaneliği"""
    STONE_BALL = "stone_ball"       # Taş gülle — ucuz, sur hasarı
    IRON_BALL = "iron_ball"         # Demir gülle — standart
    GRAPESHOT = "grapeshot"         # Saçma (kartaca) — piyade kırıcı
    INCENDIARY = "incendiary"       # Ateşli gülle — yangın, moral yıkıcı
    CHAIN_SHOT = "chain_shot"       # Zincirli gülle — denizde gemi kırıcı


# Mühimmat çarpan tablosu
# Her mühimmat türü savaş istatistiklerini farklı etkiler
AMMO_MULTIPLIERS = {
    AmmoType.STONE_BALL: {
        'name': 'Taş Gülle',
        'description': 'Ucuz, bol. Sur hasarında etkili. Varsayılan mühimmat.',
        'siege_mult': 1.5,      # Sur hasarı ×1.5
        'field_mult': 0.5,      # Birlik hasarı ×0.5
        'morale_mult': 0.5,     # Moral hasarı ×0.5
        'gunpowder_mult': 1.0,  # Barut tüketimi normal
        'iron_cost': 0,         # Ek demir maliyeti yok (taştan)
    },
    AmmoType.IRON_BALL: {
        'name': 'Demir Gülle',
        'description': 'Standart demir mermi. Dengeli performans.',
        'siege_mult': 1.0,
        'field_mult': 1.0,
        'morale_mult': 0.7,
        'gunpowder_mult': 1.0,
        'iron_cost': 1,         # Atış başı 1 demir
    },
    AmmoType.GRAPESHOT: {
        'name': 'Saçma (Kartaca)',
        'description': 'Küçük metal parçaları. Kısa menzilde piyade kırıcı. Surlara etkisiz.',
        'siege_mult': 0.0,      # Surlara etkisiz
        'field_mult': 2.0,      # Birlik hasarı ×2
        'morale_mult': 1.5,     # Yüksek moral etkisi
        'gunpowder_mult': 1.0,
        'iron_cost': 1,
    },
    AmmoType.INCENDIARY: {
        'name': 'Ateşli Gülle',
        'description': 'Yanıcı madde dolu. Yangın çıkarır, moral yıkıcı. Çok barut yer.',
        'siege_mult': 0.3,      # Surlara az etki
        'field_mult': 0.5,      # Birlik hasarı düşük
        'morale_mult': 2.5,     # Çok yüksek moral hasarı (yangın paniği)
        'gunpowder_mult': 2.0,  # Çift barut tüketimi
        'iron_cost': 0,
    },
    AmmoType.CHAIN_SHOT: {
        'name': 'Zincirli Gülle',
        'description': 'İki gülle zincirle bağlı. Denizde gemi hız kırıcı.',
        'siege_mult': 0.1,
        'field_mult': 0.3,
        'morale_mult': 0.5,
        'gunpowder_mult': 1.0,
        'iron_cost': 2,         # Zincir + 2 gülle
        'naval_speed_reduction': 0.5,  # Gemi hızını yarıya düşürür
    },
}


@dataclass
class CannonDefinition:
    """Top tanımı — genişletilmiş"""
    cannon_type: CannonType
    name: str
    description: str
    historical_note: str
    
    # Maliyet
    gold_cost: int
    iron_cost: int           # Demir malzeme seçiminde temel maliyet
    copper_cost: int = 0     # Bakır (bronz seçimi için)
    stone_cost: int = 0      # Taş gülle maliyeti
    
    # Zaman
    build_time: int = 2      # Tur (gün) sayısı
    
    # Mürettebat
    crew_required: int = 3   # Gerekli topçu sayısı
    
    # Savaş istatistikleri
    field_power: int = 10    # Sahra savaşı gücü (piyade/süvari hasarı)
    siege_power: int = 5     # Kuşatma gücü (sur hasarı)
    morale_damage: int = 5   # Düşman moraline verilen hasar
    range_level: int = 3     # Menzil (1-10)
    daily_fire_rate: int = 20  # Günlük atış kapasitesi
    
    # Lojistik
    mobility: int = 8        # Manevra kabiliyeti (1-10, 10=en hafif)
    weight: int = 50         # Ağırlık (kg, taşıma hesabı)
    
    # Risk ve bakım
    maintenance: int = 2     # Günlük bakım maliyeti (altın)
    base_burst_risk: int = 2 # Temel patlama riski (%, bronz)
    iron_burst_risk: int = 15 # Demir versiyonunda patlama riski (%)
    
    # Barut tüketimi
    gunpowder_per_shot: int = 1  # Atış başı barut tüketimi
    
    # Özel
    is_naval: bool = False   # Deniz topu mu?
    can_be_iron: bool = True # Demir olarak üretilebilir mi?
    
    # Maliyet hesaplama
    def get_cost(self, material: CannonMaterial) -> dict:
        """Malzemeye göre üretim maliyeti"""
        if material == CannonMaterial.BRONZE:
            return {
                'gold': self.gold_cost,
                'iron': max(5, self.iron_cost // 4),  # Az demir (aletler için)
                'copper': self.copper_cost or self.iron_cost,  # Bakır = temel demir maliyeti
                'stone': self.stone_cost
            }
        else:
            return {
                'gold': self.gold_cost // 2,  # Demir top yarı fiyat
                'iron': self.iron_cost,
                'copper': 0,
                'stone': self.stone_cost
            }
    
    def get_burst_risk(self, material: CannonMaterial) -> int:
        """Malzemeye göre patlama riski"""
        if material == CannonMaterial.BRONZE:
            return self.base_burst_risk
        return self.iron_burst_risk


# ══════════════════════════════════════════════════
# TÜM TOP TANIMLARI — 7 Tarihi Top Türü
# ══════════════════════════════════════════════════

CANNON_DEFINITIONS: Dict[CannonType, CannonDefinition] = {
    
    # ─── SAHRA TOPLARI (Meydan Muharebesi) ───
    
    CannonType.DARBZEN: CannonDefinition(
        cannon_type=CannonType.DARBZEN,
        name="Darbzen",
        description="Hafif sahra topu. 0.15-2.5 kg mermi. Hızlı ateş, kolay taşınır.",
        historical_note="Osmanlı ordusundaki en yaygın top. Mohaç'ta yüzlercesi kullanıldı. "
                        "Bir ata veya iki beygire yüklenebilecek kadar hafiftir (~56 kg).",
        gold_cost=200,
        iron_cost=20,
        copper_cost=15,
        stone_cost=5,
        build_time=2,
        crew_required=3,
        field_power=15,
        siege_power=3,
        morale_damage=5,
        range_level=4,
        daily_fire_rate=40,
        mobility=9,
        weight=57,
        maintenance=2,
        base_burst_risk=1,
        iron_burst_risk=10,
        gunpowder_per_shot=1
    ),
    
    CannonType.ABUS: CannonDefinition(
        cannon_type=CannonType.ABUS,
        name="Abus",
        description="Küçük sahra ve savunma topu. Seri ateş. Tabur Cengi formasyonunda idealdir.",
        historical_note="Mohaç Meydan Muharebesi'nde (1526) yüzlerce Abus topu zincirle "
                        "birbirine bağlanarak geçilmez ateş duvarı oluşturuldu.",
        gold_cost=150,
        iron_cost=15,
        copper_cost=10,
        stone_cost=3,
        build_time=1,
        crew_required=2,
        field_power=10,
        siege_power=1,
        morale_damage=3,
        range_level=3,
        daily_fire_rate=60,
        mobility=10,
        weight=30,
        maintenance=1,
        base_burst_risk=1,
        iron_burst_risk=8,
        gunpowder_per_shot=1,
    ),
    
    CannonType.KOLUNBURNA: CannonDefinition(
        cannon_type=CannonType.KOLUNBURNA,
        name="Kolunburna",
        description="Uzun menzilli delici top (Culverin). 3-12 kg mermi. Zırhlı hedeflere etkili.",
        historical_note="Avrupa'nın Culverin sınıfının karşılığı. Düz yörüngeyle (flat trajectory) "
                        "yüksek çıkış hızıyla ateş eder. Düşman topçusunu susturmak için ideal.",
        gold_cost=700,
        iron_cost=70,
        copper_cost=60,
        stone_cost=20,
        build_time=5,
        crew_required=6,
        field_power=30,
        siege_power=12,
        morale_damage=8,
        range_level=9,
        daily_fire_rate=15,
        mobility=5,
        weight=800,
        maintenance=7,
        base_burst_risk=2,
        iron_burst_risk=15,
        gunpowder_per_shot=3,
    ),
    
    # ─── KUŞATMA TOPLARI ───
    
    CannonType.HAVAN: CannonDefinition(
        cannon_type=CannonType.HAVAN,
        name="Havan",
        description="Aşırtma topu (Mortar). Parabolik yörünge. Surların arkasını vurur.",
        historical_note="Kısa namlulu, kalın gövdeli. Doğrudan görüş hattına ihtiyaç duymaz. "
                        "Kale içindeki savunmacılara, mühimmat depolarına ve binalara hasar verir.",
        gold_cost=500,
        iron_cost=50,
        copper_cost=40,
        stone_cost=30,
        build_time=4,
        crew_required=5,
        field_power=8,
        siege_power=15,
        morale_damage=25,      # Çok yüksek moral hasarı — kale içi terör
        range_level=5,
        daily_fire_rate=12,
        mobility=6,
        weight=600,
        maintenance=5,
        base_burst_risk=3,
        iron_burst_risk=18,
        gunpowder_per_shot=3,
    ),
    
    CannonType.BALYEMEZ: CannonDefinition(
        cannon_type=CannonType.BALYEMEZ,
        name="Balyemez",
        description="Ağır batarya topu. 6-74 kg mermi. Uzun menzil, sur dövme uzmanı.",
        historical_note="İtalyanca 'pallamezza'dan türetilmiş. İstanbul ve Budin tophanelerinde "
                        "dökülmüştür. Kuşatmada sur hasarı için ana silah. Karşı batarya aracıdır.",
        gold_cost=1200,
        iron_cost=100,
        copper_cost=90,
        stone_cost=40,
        build_time=7,
        crew_required=15,
        field_power=15,
        siege_power=40,
        morale_damage=12,
        range_level=7,
        daily_fire_rate=8,
        mobility=3,
        weight=3000,
        maintenance=10,
        base_burst_risk=3,
        iron_burst_risk=20,
        gunpowder_per_shot=5,
    ),
    
    CannonType.SAHI: CannonDefinition(
        cannon_type=CannonType.SAHI,
        name="Şahi",
        description="Dev kale yıkıcı bombard. 400-680 kg taş gülle. İstanbul'un fatihi.",
        historical_note="8.2m uzunluk, 760-915mm namlu çapı, 18-30 ton ağırlık. "
                        "1453'te Macar Urban tarafından Edirne'de dökülmüştür. Kalıp hazırlama, "
                        "dökme ve soğutma 3 ay sürmüştür. 60-90 çift öküzle taşınmış, "
                        "200-400 asker refakat etmiştir. Günde sadece 7 atış yapabilirdi.",
        gold_cost=5000,
        iron_cost=300,
        copper_cost=250,
        stone_cost=150,
        build_time=90,          # 3 ay = 90 gün (tarihi gerçek)
        crew_required=200,      # Tarihi: 200 asker + sivilller
        field_power=5,          # Saha savaşında kullanışsız
        siege_power=100,        # Devasa sur hasarı
        morale_damage=40,       # Muazzam psikolojik etki
        range_level=4,          # Ağır olduğu için menzil düşük
        daily_fire_rate=7,      # Tarihi: günde sadece 7 atış
        mobility=1,             # Neredeyse taşınamaz
        weight=20000,           # 20 ton
        maintenance=30,
        base_burst_risk=5,
        iron_burst_risk=30,
        gunpowder_per_shot=20,
        can_be_iron=False,      # Şahi sadece tunç olabilir
    ),
    
    # ─── DONANMA TOPLARI ───
    
    CannonType.PRANGI: CannonDefinition(
        cannon_type=CannonType.PRANGI,
        name="Prangi",
        description="Hafif donanma topu. 0.5-1 kg mermi. Gemi montajı ve kale savunması.",
        historical_note="Şahalaz, Prangi ve Şayha — nehir gemilerinde (şayka) ve kalyonlarda "
                        "kullanılan küçük çaplı toplar. Mürettebat öldürmeye yönelik antipersonel silah. "
                        "Ortalama 20-40 kg ağırlığında.",
        gold_cost=100,
        iron_cost=10,
        copper_cost=8,
        stone_cost=2,
        build_time=1,
        crew_required=2,
        field_power=5,
        siege_power=1,
        morale_damage=2,
        range_level=2,
        daily_fire_rate=80,    # Çok seri ateş
        mobility=10,
        weight=30,
        maintenance=1,
        base_burst_risk=1,
        iron_burst_risk=8,
        gunpowder_per_shot=1,
        is_naval=True,
    ),
}


@dataclass
class Cannon:
    """Aktif top — genişletilmiş"""
    cannon_id: str
    cannon_type: CannonType
    name: str
    material: str = "bronze"      # "bronze" veya "iron"
    condition: int = 100          # Durum (0-100)
    shots_fired: int = 0          # Toplam atış sayısı
    experience: int = 0           # Mürettebat tecrübesi (0-100)
    damaged: bool = False         # Hasarlı mı (tamir gerekir)?
    selected_ammo: str = "stone_ball"  # Seçili mühimmat (AmmoType.value)
    
    def get_definition(self) -> CannonDefinition:
        return CANNON_DEFINITIONS[self.cannon_type]
    
    def get_material_enum(self) -> CannonMaterial:
        return CannonMaterial(self.material)
    
    def get_ammo_type(self) -> AmmoType:
        """Seçili mühimmat türünü al"""
        try:
            return AmmoType(self.selected_ammo)
        except ValueError:
            return AmmoType.STONE_BALL
    
    def get_ammo_multipliers(self) -> dict:
        """Seçili mühimmatın çarpanlarını al"""
        return AMMO_MULTIPLIERS[self.get_ammo_type()]
    
    def get_power(self, combat_type: str = "field") -> int:
        """Duruma, tecrübeye ve mühimmata göre savaş gücü"""
        defn = self.get_definition()
        ammo = self.get_ammo_multipliers()
        
        if combat_type == "siege":
            base = defn.siege_power * ammo['siege_mult']
        else:
            base = defn.field_power * ammo['field_mult']
        
        # Durum çarpanı
        condition_mult = self.condition / 100
        
        # Tecrübe bonusu (%0 - %50 arası)
        exp_mult = 1.0 + (self.experience / 200)
        
        # Hasarlıysa yarı güç
        if self.damaged:
            condition_mult *= 0.5
        
        return int(base * condition_mult * exp_mult)
    
    def get_morale_damage(self) -> int:
        """Moral hasarı — mühimmat çarpanı uygulanır"""
        defn = self.get_definition()
        ammo = self.get_ammo_multipliers()
        condition_mult = self.condition / 100
        return int(defn.morale_damage * condition_mult * ammo['morale_mult'])
    
    def get_burst_risk(self) -> int:
        """Mevcut patlama riski (%, durum ve malzemeye bağlı)"""
        defn = self.get_definition()
        base_risk = defn.get_burst_risk(self.get_material_enum())
        
        # Düşük kondisyon riski artırır
        condition_factor = 1.0 + ((100 - self.condition) / 100)
        
        # Çok atış yapılmışsa risk artar
        fatigue_factor = 1.0 + (self.shots_fired / 500)
        
        return min(50, int(base_risk * condition_factor * fatigue_factor))
    
    def fire(self) -> dict:
        """
        Bir atış yap — yıpranma, patlama kontrolü, barut tüketimi.
        Mühimmat çarpanı uygulanır.
        Returns: {'success': bool, 'burst': bool, 'gunpowder_used': int,
                  'iron_used': int, 'wear': int, 'message': str}
        """
        defn = self.get_definition()
        ammo = self.get_ammo_multipliers()
        
        gunpowder_cost = int(defn.gunpowder_per_shot * ammo['gunpowder_mult'])
        iron_cost = ammo.get('iron_cost', 0)
        
        result = {
            'success': True,
            'burst': False,
            'gunpowder_used': gunpowder_cost,
            'iron_used': iron_cost,
            'wear': 0,
            'message': ''
        }
        
        self.shots_fired += 1
        
        # Yıpranma
        if self.material == "iron":
            wear = random.randint(1, 3)  # Demir: 1-3 yıpranma
        else:
            wear = random.randint(0, 1)  # Bronz: 0-1 yıpranma
        
        self.condition = max(0, self.condition - wear)
        result['wear'] = wear
        
        # Patlama riski kontrolü
        burst_chance = self.get_burst_risk()
        if random.randint(1, 100) <= burst_chance:
            result['burst'] = True
            result['success'] = False
            result['message'] = f"{self.name} yarıldı ve patladı! Mürettebat kaybı!"
            return result
        
        # Hasar kontrolü (condition çok düşükse)
        if self.condition < 20 and not self.damaged:
            if random.randint(1, 100) <= 30:
                self.damaged = True
                result['message'] = f"{self.name} hasarlı! Tamir gerekiyor."
        
        # Tecrübe kazanımı
        if self.experience < 100:
            self.experience = min(100, self.experience + 1)
        
        return result
    
    def repair(self, cost_gold: int = 0) -> bool:
        """Topu tamir et — condition yarısına kadar yükselir"""
        if not self.damaged and self.condition > 50:
            return False
        self.damaged = False
        self.condition = min(100, self.condition + 40)
        return True
    
    def to_dict(self) -> dict:
        return {
            'cannon_id': self.cannon_id,
            'cannon_type': self.cannon_type.value,
            'name': self.name,
            'material': self.material,
            'condition': self.condition,
            'shots_fired': self.shots_fired,
            'experience': self.experience,
            'damaged': self.damaged,
            'selected_ammo': self.selected_ammo
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Cannon':
        return cls(
            cannon_id=data['cannon_id'],
            cannon_type=CannonType(data['cannon_type']),
            name=data['name'],
            material=data.get('material', 'bronze'),
            condition=data.get('condition', 100),
            shots_fired=data.get('shots_fired', 0),
            experience=data.get('experience', 0),
            damaged=data.get('damaged', False),
            selected_ammo=data.get('selected_ammo', 'stone_ball')
        )


@dataclass
class CannonProduction:
    """Üretim halindeki top"""
    cannon_type: CannonType
    turns_remaining: int
    custom_name: str = ""
    material: str = "bronze"


class ArtillerySystem:
    """Topçu yönetim sistemi (Topçu Ocağı) — Geliştirilmiş"""
    
    def __init__(self):
        self.cannons: List[Cannon] = []
        self.production_queue: List[CannonProduction] = []
        self.total_cannons_produced: int = 0
        self.cannons_destroyed: int = 0
        self.total_gunpowder_used: int = 0
        
        # Audio
        self.audio = get_audio_manager()
    
    def can_produce_cannon(self, cannon_type: CannonType, economy,
                           material: CannonMaterial = CannonMaterial.BRONZE) -> tuple:
        """Top üretilebilir mi? — malzeme tercihi dahil"""
        definition = CANNON_DEFINITIONS[cannon_type]
        
        # Şahi sadece bronz
        if cannon_type == CannonType.SAHI and material == CannonMaterial.IRON:
            return False, "Şahi topu sadece tunçtan dökülür!"
        
        if not definition.can_be_iron and material == CannonMaterial.IRON:
            return False, f"{definition.name} sadece tunçtan üretilebilir."
        
        costs = definition.get_cost(material)
        res = economy.resources
        
        if res.gold < costs['gold']:
            return False, f"Yetersiz altın ({res.gold:,}/{costs['gold']:,})"
        if res.iron < costs['iron']:
            return False, f"Yetersiz demir ({res.iron:,}/{costs['iron']:,})"
        if costs.get('copper', 0) > 0 and hasattr(res, 'copper'):
            if res.copper < costs['copper']:
                return False, f"Yetersiz bakır ({res.copper:,}/{costs['copper']:,})"
        if costs.get('stone', 0) > 0 and res.stone < costs['stone']:
            return False, f"Yetersiz taş ({res.stone:,}/{costs['stone']:,})"
        
        return True, "Üretilebilir"
    
    def start_production(self, cannon_type: CannonType, economy,
                         material: CannonMaterial = CannonMaterial.BRONZE,
                         custom_name: str = "",
                         foundry_level: int = 1) -> bool:
        """
        Top üretimini başlat — malzeme tercihi + Tophane seviye bonusu dahil.
        foundry_level: Tophane binasının seviyesi (1-5)
          - Her seviye üretim süresini %10 düşürür
          - Kapasite: 5 + 2*seviye
        """
        # Kapasite kontrolü
        max_cap = self.get_max_capacity(foundry_level)
        current_count = len(self.cannons) + len(self.production_queue)
        if current_count >= max_cap:
            self.audio.speak(
                f"Top kapasitesi dolu! ({current_count}/{max_cap}). "
                f"Tophane'yi yükseltin veya eski topları erit.",
                interrupt=True
            )
            return False
        
        can_produce, reason = self.can_produce_cannon(cannon_type, economy, material)
        if not can_produce:
            self.audio.speak(f"Top üretilemedi: {reason}", interrupt=True)
            return False
        
        definition = CANNON_DEFINITIONS[cannon_type]
        costs = definition.get_cost(material)
        
        # Kaynakları düş
        economy.resources.gold -= costs['gold']
        economy.resources.iron -= costs['iron']
        if costs.get('copper', 0) > 0 and hasattr(economy.resources, 'copper'):
            economy.resources.copper -= costs['copper']
        if costs.get('stone', 0) > 0:
            economy.resources.stone -= costs['stone']
        
        # Demir top daha hızlı üretilir
        build_time = definition.build_time
        if material == CannonMaterial.IRON:
            build_time = max(1, build_time // 2)
        
        # Tophane seviye bonusu: her seviye %10 hızlandırır
        level_reduction = 1.0 - (foundry_level - 1) * 0.10  # Sev1=1.0, Sev3=0.8, Sev5=0.6
        build_time = max(1, int(build_time * level_reduction))
        
        # Kuyruğa ekle
        self.production_queue.append(CannonProduction(
            cannon_type=cannon_type,
            turns_remaining=build_time,
            custom_name=custom_name,
            material=material.value
        ))
        
        mat_name = "tunç" if material == CannonMaterial.BRONZE else "demir"
        self.audio.speak(
            f"{mat_name.capitalize()} {definition.name} üretimi başladı! "
            f"{build_time} gün sürecek.",
            interrupt=True
        )
        return True
    
    def process_production(self) -> List[str]:
        """Üretimi işle (her tur çağrılır). Mesaj listesi döner."""
        completed = []
        messages = []
        
        for production in self.production_queue:
            production.turns_remaining -= 1
            
            if production.turns_remaining <= 0:
                completed.append(production)
        
        for production in completed:
            self.production_queue.remove(production)
            msg = self._complete_cannon(production)
            if msg:
                messages.append(msg)
        
        return messages
    
    def _complete_cannon(self, production: CannonProduction) -> str:
        """Top üretimini tamamla"""
        definition = CANNON_DEFINITIONS[production.cannon_type]
        
        self.total_cannons_produced += 1
        cannon_id = f"cannon_{self.total_cannons_produced}"
        
        name = production.custom_name or f"{definition.name} #{self.total_cannons_produced}"
        
        cannon = Cannon(
            cannon_id=cannon_id,
            cannon_type=production.cannon_type,
            name=name,
            material=production.material
        )
        
        self.cannons.append(cannon)
        
        mat_name = "Tunç" if production.material == "bronze" else "Demir"
        burst_risk = definition.get_burst_risk(CannonMaterial(production.material))
        
        msg = (f"TOP TAMAMLANDI! {mat_name} {name} topçu birliğine katıldı. "
               f"Sahra gücü: {definition.field_power}, Kuşatma gücü: {definition.siege_power}, "
               f"Patlama riski: %{burst_risk}")
        
        self.audio.speak(msg, interrupt=True)
        return msg
    
    def fire_all(self, combat_type: str = "field") -> dict:
        """
        Tüm toplarla ateş et — savaş ve kuşatma sistemiyle entegrasyon.
        Returns: {
            'total_damage': int, 'morale_damage': int, 'gunpowder_used': int,
            'bursts': int, 'burst_names': list, 'messages': list
        }
        """
        result = {
            'total_damage': 0,
            'morale_damage': 0,
            'gunpowder_used': 0,
            'bursts': 0,
            'burst_names': [],
            'messages': []
        }
        
        burst_cannons = []
        
        for cannon in self.cannons:
            if cannon.condition <= 0:
                continue
            
            # Ateş et
            fire_result = cannon.fire()
            result['gunpowder_used'] += fire_result['gunpowder_used']
            
            if fire_result['burst']:
                burst_cannons.append(cannon)
                result['bursts'] += 1
                result['burst_names'].append(cannon.name)
                result['messages'].append(fire_result['message'])
            elif fire_result['success']:
                result['total_damage'] += cannon.get_power(combat_type)
                result['morale_damage'] += cannon.get_morale_damage()
                
                if fire_result.get('message'):
                    result['messages'].append(fire_result['message'])
        
        # Patlayan topları kaldır
        for burst in burst_cannons:
            self.cannons.remove(burst)
            self.cannons_destroyed += 1
        
        self.total_gunpowder_used += result['gunpowder_used']
        
        return result
    
    def get_total_power(self, combat_type: str = "field") -> int:
        """Toplam topçu gücü"""
        return sum(c.get_power(combat_type) for c in self.cannons if c.condition > 0)
    
    def get_siege_bonus(self) -> int:
        """Toplam kuşatma bonusu"""
        return sum(c.get_power("siege") for c in self.cannons if c.condition > 0)
    
    def get_morale_damage(self) -> int:
        """Toplam moral hasarı kapasitesi"""
        return sum(c.get_morale_damage() for c in self.cannons if c.condition > 0)
    
    def get_maintenance_cost(self) -> int:
        """Toplam topçu bakım maliyeti"""
        return sum(c.get_definition().maintenance for c in self.cannons)
    
    def get_gunpowder_consumption(self) -> int:
        """Günlük tahmini barut tüketimi (tüm toplar bir kez ateş etse)"""
        return sum(c.get_definition().gunpowder_per_shot for c in self.cannons if c.condition > 0)
    
    def get_cannon_counts(self) -> Dict[CannonType, int]:
        """Her türden kaç top var"""
        counts = {ct: 0 for ct in CannonType}
        for cannon in self.cannons:
            counts[cannon.cannon_type] += 1
        return counts
    
    def get_damaged_count(self) -> int:
        """Hasarlı top sayısı"""
        return sum(1 for c in self.cannons if c.damaged or c.condition < 30)
    
    def get_total_weight(self) -> int:
        """Toplam topçu ağırlığı (kg) — lojistik hesabı için"""
        return sum(c.get_definition().weight for c in self.cannons)
    
    def get_max_capacity(self, foundry_level: int = 1) -> int:
        """
        Tophane seviyesine göre maksimum top kapasitesi.
        Sev1=7, Sev2=9, Sev3=11, Sev4=13, Sev5=15
        """
        return 5 + foundry_level * 2
    
    def get_foundry_bonuses(self, foundry_level: int = 1) -> dict:
        """
        Tophane seviye bonusları.
        UI gösterimi ve bilgilendirme için.
        """
        return {
            'level': foundry_level,
            'max_cannons': self.get_max_capacity(foundry_level),
            'build_speed_bonus': f"%{(foundry_level - 1) * 10}",  # Sev1=0%, Sev5=40%
            'barut_per_turn': 3 + foundry_level * 2,  # Baruthane modülüyle
            'description': self._get_level_description(foundry_level),
        }
    
    def _get_level_description(self, level: int) -> str:
        """Tophane seviye açıklamaları"""
        descriptions = {
            1: "Basit dökümhane. Temel toplar üretilebilir.",
            2: "Geliştirilmiş fırınlar. Üretim hızlanır.",
            3: "Usta dökümcüler. Kaliteli toplar.",
            4: "Kraliyet Tophane-i Âmire. Yüksek kapasite.",
            5: "Tophane-i Âmire: Sultanın dökümhanesi. En yüksek kapasite ve hız.",
        }
        return descriptions.get(level, descriptions[1])
    
    def get_march_speed_penalty(self) -> float:
        """
        Topçu ağırlığına göre yürüyüş cezası.
        Ağır toplar (Balyemez, Şahi) ordu hareketini yavaşlatır.
        
        Returns: 0.0 - 2.0 arası ek tur (yürüyüş süresi uzaması)
          0 kg      = +0 tur
          5,000 kg  = +1 tur
          20,000 kg = +2 tur
        """
        total_weight = self.get_total_weight()
        if total_weight <= 500:  # Hafif toplar (Abus, Prangi)
            return 0.0
        elif total_weight <= 2000:  # Orta toplar
            return 0.5
        elif total_weight <= 5000:  # Ağır toplar
            return 1.0
        elif total_weight <= 15000:  # Çok ağır
            return 1.5
        else:  # Şahi / dev batarya
            return 2.0
    
    def get_total_crew_required(self) -> int:
        """Tüm toplar için gereken toplam mürettebat"""
        return sum(c.get_definition().crew_required for c in self.cannons if c.condition > 0)
    
    def get_crew_effectiveness(self, military_system) -> float:
        """
        Topçu-Cebeci personel oranına göre etkinlik çarpanı.
        
        Topçu (TOPCU): Topları ateşleyen mürettebat
        - Yeterli topçu yoksa atış hızı ve isabet düşer
        
        Cebeci (CEBECI): Mühimmat taşıyıcı
        - Yeterli cebeci yoksa yeniden doldurma yavaşlar
        
        Returns: 0.0 - 1.3 arası çarpan (1.0 = tam kadro)
        """
        if not self.cannons:
            return 1.0
        
        from game.systems.military import UnitType as MilitaryUnitType
        
        crew_needed = self.get_total_crew_required()
        if crew_needed == 0:
            return 1.0
        
        # Mevcut topçu sayısı
        topcu_count = military_system.units.get(MilitaryUnitType.TOPCU, 0)
        
        # Mevcut cebeci sayısı
        cebeci_count = military_system.units.get(MilitaryUnitType.CEBECI, 0)
        
        # Topçu oranı — ana etkinlik çarpanı
        topcu_ratio = min(1.0, topcu_count / crew_needed)
        
        # Cebeci bonusu — mühimmat taşıma (ihtiyacın %30'u kadar cebeci ideal)
        cebeci_needed = max(1, crew_needed // 3)
        cebeci_ratio = min(1.0, cebeci_count / cebeci_needed)
        cebeci_bonus = cebeci_ratio * 0.3  # Max %30 bonus
        
        # Toplam etkinlik: topçu oranı + cebeci bonusu
        effectiveness = topcu_ratio + cebeci_bonus
        
        return min(1.3, max(0.1, effectiveness))  # Min %10, Max %130
    
    def repair_all(self, economy) -> int:
        """Tüm hasarlı topları tamir et. Toplam maliyet döner."""
        total_cost = 0
        repaired = 0
        
        for cannon in self.cannons:
            if cannon.damaged or cannon.condition < 50:
                repair_cost = cannon.get_definition().gold_cost // 5
                if economy.resources.gold >= repair_cost:
                    economy.resources.gold -= repair_cost
                    cannon.repair()
                    total_cost += repair_cost
                    repaired += 1
        
        if repaired > 0:
            self.audio.speak(
                f"{repaired} top tamir edildi. Toplam maliyet: {total_cost:,} altın.",
                interrupt=True
            )
        else:
            self.audio.speak("Tamir gerektiren top yok.", interrupt=True)
        
        return total_cost
    
    def announce_artillery(self):
        """Topçu durumunu duyur — detaylı"""
        if not self.cannons:
            self.audio.speak(
                "Henüz topunuz yok. Topçu Ocağı'nda top üretebilirsiniz.",
                interrupt=True
            )
            return
        
        counts = self.get_cannon_counts()
        parts = []
        
        for cannon_type in CannonType:
            count = counts[cannon_type]
            if count > 0:
                name = CANNON_DEFINITIONS[cannon_type].name
                parts.append(f"{count} {name}")
        
        total_field = self.get_total_power("field")
        total_siege = self.get_total_power("siege")
        total_morale = self.get_morale_damage()
        damaged = self.get_damaged_count()
        
        self.audio.speak(
            f"Topçu birliği: {', '.join(parts)}.",
            interrupt=True
        )
        self.audio.speak(
            f"Sahra gücü: {total_field}. Kuşatma gücü: {total_siege}. "
            f"Moral hasarı: {total_morale}.",
            interrupt=False
        )
        
        if damaged > 0:
            self.audio.speak(f"Dikkat: {damaged} top hasarlı veya yıpranmış!", interrupt=False)
        
        # Malzeme dağılımı
        bronze_count = sum(1 for c in self.cannons if c.material == "bronze")
        iron_count = sum(1 for c in self.cannons if c.material == "iron")
        if iron_count > 0:
            self.audio.speak(
                f"Malzeme: {bronze_count} tunç, {iron_count} demir top.",
                interrupt=False
            )
    
    def to_dict(self) -> Dict:
        """Kayıt için dictionary"""
        return {
            "cannons": [c.to_dict() for c in self.cannons],
            "production_queue": [
                {
                    "cannon_type": p.cannon_type.value,
                    "turns_remaining": p.turns_remaining,
                    "custom_name": p.custom_name,
                    "material": p.material
                }
                for p in self.production_queue
            ],
            "total_cannons_produced": self.total_cannons_produced,
            "cannons_destroyed": self.cannons_destroyed,
            "total_gunpowder_used": self.total_gunpowder_used
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ArtillerySystem':
        """Dictionary'den yükle — eski kayıtlarla uyumlu"""
        system = cls()
        
        for cannon_data in data.get("cannons", []):
            try:
                cannon = Cannon.from_dict(cannon_data)
                system.cannons.append(cannon)
            except (ValueError, KeyError):
                pass
        
        for prod_data in data.get("production_queue", []):
            try:
                production = CannonProduction(
                    cannon_type=CannonType(prod_data["cannon_type"]),
                    turns_remaining=prod_data["turns_remaining"],
                    custom_name=prod_data.get("custom_name", ""),
                    material=prod_data.get("material", "bronze")
                )
                system.production_queue.append(production)
            except (ValueError, KeyError):
                pass
        
        system.total_cannons_produced = data.get("total_cannons_produced", 0)
        system.cannons_destroyed = data.get("cannons_destroyed", 0)
        system.total_gunpowder_used = data.get("total_gunpowder_used", 0)
        
        return system
