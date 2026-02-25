# -*- coding: utf-8 -*-
"""
Osmanlı Eyalet Yönetim Simülasyonu - Gelişmiş Savaş Sistemi
Akın, kuşatma, savunma ve sefer mekanikleri
+ Kuşatma Aşamaları, Birlik Avantajları, Arazi Etkileri, Özel Yetenekler
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from enum import Enum
from enum import Enum
import random
from audio.audio_manager import get_audio_manager
from game.systems.military import Commander, CommanderTrait


# ============================================================
# ENUM TANIMLARI
# ============================================================

class BattleType(Enum):
    """Savaş türleri"""
    RAID = "raid"                   # Akın - hızlı yağma
    SIEGE = "siege"                 # Kuşatma - kale fethi
    DEFENSE = "defense"             # Savunma
    CAMPAIGN = "campaign"           # Sefer - büyük savaş
    NAVAL_RAID = "naval_raid"       # Deniz akını - kıyı baskını
    NAVAL_DEFENSE = "naval_defense" # Deniz savunması


class BattlePhase(Enum):
    """Savaş aşamaları"""
    PREPARATION = "preparation"  # Hazırlık
    MARCH = "march"              # Yürüyüş
    COMBAT = "combat"            # Çatışma
    AFTERMATH = "aftermath"      # Sonuç


class SiegePhase(Enum):
    """
    Kuşatma aşamaları — Osmanlı kuşatma doktrini
    Rapor referansı: Rodos (1522), Budin (1541), Zigetvar (1566)
    """
    BLOCKADE = "blockade"        # 1. Abluka ve İhata — tedarik kesilir
    VIRE = "vire"                # 2. Vire (Eman) Teklifi — teslim çağrısı
                                 #    Kabul: Düşük ganimet, yüksek prestij, hızlı fetih
                                 #    Red: Yağma serbest, kuşatma devam
    TRENCHING = "trenching"      # 3. Metris — sıçan yolu (zigzag hendek) ve gabion
    BOMBARDMENT = "bombardment"  # 4. Top Dövmesi — surda gedik açma (Şahi/Darbzen)
    MINING = "mining"            # 5. Lağım — sur altına tünel + barut
                                 #    Risk: Karşı-lağım ile lağımcılar ölebilir
    ASSAULT = "assault"          # 6. Umumi Hücum — gedikten Yeniçeri saldırısı


class UnitType(Enum):
    """Birlik türleri"""
    INFANTRY = "infantry"      # Piyade (Yeniçeri)
    CAVALRY = "cavalry"        # Süvari (Sipahi, Akıncı)
    ARTILLERY = "artillery"    # Topçu
    ARCHER = "archer"          # Okçu
    SPEARMAN = "spearman"      # Mızrakçı


class TerrainType(Enum):
    """Arazi türleri"""
    PLAINS = "plains"          # Ova - normal
    FOREST = "forest"          # Orman - pusu avantajı
    MOUNTAIN = "mountain"      # Dağ - savunma avantajı
    RIVER = "river"            # Nehir geçişi - saldırı dezavantajı
    FORTRESS = "fortress"      # Kale - büyük savunma avantajı
    DESERT = "desert"          # Çöl - lojistik zorluğu
    SWAMP = "swamp"            # Bataklık - süvari dezavantajı


class WeatherType(Enum):
    """Hava durumu türleri"""
    CLEAR = "clear"            # Açık - normal
    RAIN = "rain"              # Yağmur - ateşli silahlar zayıf
    SNOW = "snow"              # Kar - moral kaybı, hareket yavaş
    FOG = "fog"                # Sis - pusu avantajı
    STORM = "storm"            # Fırtına - topçu kullanılamaz


class SpecialAbilityType(Enum):
    """Özel yetenek türleri"""
    JANISSARY_VOLLEY = "janissary_volley"    # Yeniçeri Ateşi
    AKINCI_RAID = "akinci_raid"               # Akıncı Baskını
    CANNON_BARRAGE = "cannon_barrage"         # Top Bombardımanı
    SAPPER_TUNNEL = "sapper_tunnel"           # Lağımcı Tüneli
    CAVALRY_CHARGE = "cavalry_charge"         # Süvari Şarjı
    DEFENSIVE_FORMATION = "defensive_formation"  # Savunma Düzeni


# ============================================================
# ARAZI VE HAVA MODİFİYERLERİ
# ============================================================

TERRAIN_MODIFIERS: Dict[TerrainType, Dict[str, float]] = {
    TerrainType.PLAINS: {
        "attack": 1.0, "defense": 1.0,
        "cavalry": 1.2, "artillery": 1.0, "infantry": 1.0
    },
    TerrainType.FOREST: {
        "attack": 0.9, "defense": 1.2,
        "cavalry": 0.5, "artillery": 0.4, "infantry": 1.1,
        "ambush_chance": 0.3
    },
    TerrainType.MOUNTAIN: {
        "attack": 0.7, "defense": 1.5,
        "cavalry": 0.4, "artillery": 0.8, "infantry": 1.0
    },
    TerrainType.RIVER: {
        "attack": 0.6, "defense": 1.0,
        "cavalry": 0.7, "artillery": 0.9, "infantry": 0.8
    },
    TerrainType.FORTRESS: {
        "attack": 0.5, "defense": 2.0,
        "cavalry": 0.3, "artillery": 1.5, "infantry": 0.8
    },
    TerrainType.DESERT: {
        "attack": 0.9, "defense": 0.8,
        "cavalry": 1.1, "artillery": 0.9, "infantry": 0.8,
        "morale_loss": 5
    },
    TerrainType.SWAMP: {
        "attack": 0.7, "defense": 1.1,
        "cavalry": 0.3, "artillery": 0.5, "infantry": 0.9
    },
}

WEATHER_MODIFIERS: Dict[WeatherType, Dict[str, float]] = {
    WeatherType.CLEAR: {"attack": 1.0, "defense": 1.0, "artillery": 1.0},
    WeatherType.RAIN: {"attack": 0.9, "defense": 1.0, "artillery": 0.2, "archer": 0.4},
    WeatherType.SNOW: {"attack": 0.8, "defense": 0.9, "artillery": 0.7, "morale_loss": 10, "movement": 0.5},
    WeatherType.FOG: {"attack": 0.85, "defense": 1.1, "artillery": 0.5, "ambush_chance": 0.4},
    WeatherType.STORM: {"attack": 0.7, "defense": 0.8, "artillery": 0.0, "morale_loss": 15},
}


# ============================================================
# BİRLİK AVANTAJ SİSTEMİ (Rock-Paper-Scissors)
# ============================================================

# (saldıran, savunan) -> çarpan
UNIT_ADVANTAGES: Dict[Tuple[UnitType, UnitType], float] = {
    # Süvari piyadeyı ezer
    (UnitType.CAVALRY, UnitType.INFANTRY): 1.5,
    (UnitType.CAVALRY, UnitType.ARCHER): 1.8,
    # Mızrakçı süvariyi durdurur
    (UnitType.SPEARMAN, UnitType.CAVALRY): 2.0,
    (UnitType.INFANTRY, UnitType.CAVALRY): 0.7,
    # Okçu piyadeyı vurur
    (UnitType.ARCHER, UnitType.INFANTRY): 1.3,
    (UnitType.ARCHER, UnitType.SPEARMAN): 1.4,
    # Piyade topçuyu ele geçirir
    (UnitType.INFANTRY, UnitType.ARTILLERY): 1.6,
    (UnitType.CAVALRY, UnitType.ARTILLERY): 2.0,
    # Topçu surlara karşı güçlü
    (UnitType.ARTILLERY, UnitType.INFANTRY): 1.2,
}


def get_unit_advantage(attacker_type: UnitType, defender_type: UnitType) -> float:
    """Birlik avantaj çarpanını al"""
    return UNIT_ADVANTAGES.get((attacker_type, defender_type), 1.0)


# ============================================================
# ÖZEL YETENEKLER
# ============================================================

@dataclass
class SpecialAbility:
    """Özel yetenek tanımı"""
    ability_type: SpecialAbilityType
    name_tr: str
    description: str
    cooldown: int  # Kaç tur beklemeli
    cost_morale: int = 0  # Moral maliyeti
    cost_ammo: int = 0  # Mühimmat maliyeti
    damage_multiplier: float = 1.0
    morale_damage: int = 0  # Düşmana moral hasarı
    special_effect: str = ""  # Özel efekt açıklaması


SPECIAL_ABILITIES: Dict[SpecialAbilityType, SpecialAbility] = {
    SpecialAbilityType.JANISSARY_VOLLEY: SpecialAbility(
        ability_type=SpecialAbilityType.JANISSARY_VOLLEY,
        name_tr="Yeniçeri Ateşi",
        description="Yeniçeriler yoğun tüfek ateşi açar. Yüksek hasar, toplu saldırı.",
        cooldown=3,
        cost_morale=10,
        cost_ammo=50,
        damage_multiplier=2.0,
        morale_damage=15,
        special_effect="Düşman piyadelerine ekstra hasar"
    ),
    SpecialAbilityType.AKINCI_RAID: SpecialAbility(
        ability_type=SpecialAbilityType.AKINCI_RAID,
        name_tr="Akıncı Baskını",
        description="Hafif süvariler düşman gerisine sızar ve kaos yaratır.",
        cooldown=2,
        cost_morale=5,
        damage_multiplier=1.5,
        morale_damage=25,
        special_effect="Düşman moralini çökertir"
    ),
    SpecialAbilityType.CANNON_BARRAGE: SpecialAbility(
        ability_type=SpecialAbilityType.CANNON_BARRAGE,
        name_tr="Top Bombardımanı",
        description="Tüm toplar aynı hedefe ateş açar. Sur yıkımında etkili.",
        cooldown=4,
        cost_ammo=100,
        damage_multiplier=2.5,
        morale_damage=20,
        special_effect="Kale surlarına %50 ekstra hasar"
    ),
    SpecialAbilityType.SAPPER_TUNNEL: SpecialAbility(
        ability_type=SpecialAbilityType.SAPPER_TUNNEL,
        name_tr="Lağımcı Tüneli",
        description="Lağımcılar sur altından tünel kazarak patlayıcı yerleştirir.",
        cooldown=5,
        cost_morale=15,
        damage_multiplier=3.0,
        morale_damage=30,
        special_effect="Sur çökertme şansı, çok riskli"
    ),
    SpecialAbilityType.CAVALRY_CHARGE: SpecialAbility(
        ability_type=SpecialAbilityType.CAVALRY_CHARGE,
        name_tr="Süvari Şarjı",
        description="Ağır süvariler düşman hattına dalar.",
        cooldown=2,
        cost_morale=10,
        damage_multiplier=1.8,
        morale_damage=15,
        special_effect="Düşman piyadesini dağıtır"
    ),
    SpecialAbilityType.DEFENSIVE_FORMATION: SpecialAbility(
        ability_type=SpecialAbilityType.DEFENSIVE_FORMATION,
        name_tr="Savunma Düzeni",
        description="Birlikler sıkı savunma pozisyonu alır.",
        cooldown=1,
        cost_morale=5,
        damage_multiplier=0.5,  # Düşük saldırı
        morale_damage=0,
        special_effect="Bu tur alınan hasar %50 azalır"
    ),
}


# ============================================================
# SAVAŞ RAPORU
# ============================================================

@dataclass
class BattleReport:
    """Detaylı savaş raporu"""
    battle_id: str
    battle_type: BattleType
    target_name: str
    victory: bool
    rounds_fought: int
    
    # Kayıplar
    player_infantry_lost: int = 0
    player_cavalry_lost: int = 0
    player_artillery_lost: int = 0
    enemy_infantry_lost: int = 0
    enemy_cavalry_lost: int = 0
    enemy_artillery_lost: int = 0
    
    # Taktik istatistikleri
    tactics_used: List[str] = field(default_factory=list)
    most_effective_tactic: str = ""
    abilities_used: List[str] = field(default_factory=list)
    
    # Sonuçlar
    loot_gold: int = 0
    loot_food: int = 0
    loot_iron: int = 0
    experience_gained: int = 0
    loyalty_change: int = 0
    
    # Arazi ve hava
    terrain: str = "plains"
    weather: str = "clear"
    
    def get_summary(self) -> str:
        """Rapor özeti"""
        result = "ZAFER" if self.victory else "YENİLGİ"
        total_player_loss = self.player_infantry_lost + self.player_cavalry_lost + self.player_artillery_lost
        total_enemy_loss = self.enemy_infantry_lost + self.enemy_cavalry_lost + self.enemy_artillery_lost
        
        return (
            f"{result}! {self.target_name} savaşı {self.rounds_fought} turda sona erdi. "
            f"Kayıplarımız: {total_player_loss}, Düşman kayıpları: {total_enemy_loss}. "
            f"Yağma: {self.loot_gold} altın."
        )


# ============================================================
# ORDU SINIFI (GELİŞTİRİLMİŞ)
# ============================================================

@dataclass
class Army:
    """Ordu birimi - geliştirilmiş"""
    infantry: int = 0        # Piyade
    cavalry: int = 0         # Süvari
    artillery: int = 0       # Topçu
    archers: int = 0         # Okçu (yeni)
    spearmen: int = 0        # Mızrakçı (yeni)
    morale: int = 100        # Moral (0-100)
    experience: int = 0      # Deneyim (0-100)
    ammo: int = 100          # Mühimmat (yeni)
    commander: Optional[Commander] = None # Ordu Komutanı
    
    # Özel yetenek bekleme süreleri
    ability_cooldowns: Dict[SpecialAbilityType, int] = field(default_factory=dict)
    
    def get_power(self, terrain: TerrainType = TerrainType.PLAINS,
                  weather: WeatherType = WeatherType.CLEAR) -> int:
        """Toplam güç hesapla - arazi ve hava etkileriyle"""
        terrain_mod = TERRAIN_MODIFIERS.get(terrain, {})
        weather_mod = WEATHER_MODIFIERS.get(weather, {})
        
        # Birlik güçleri (temel güç çarpanları)
        infantry_power = self.infantry * 1.0 * terrain_mod.get("infantry", 1.0)
        cavalry_power = self.cavalry * 2.0 * terrain_mod.get("cavalry", 1.0)
        artillery_power = self.artillery * 3.0 * terrain_mod.get("artillery", 1.0) * weather_mod.get("artillery", 1.0)
        archer_power = self.archers * 1.2 * weather_mod.get("archer", 1.0)
        spear_power = self.spearmen * 1.1
        
        base = infantry_power + cavalry_power + artillery_power + archer_power + spear_power
        
        # Moral ve deneyim çarpanları
        morale_mod = max(0.3, self.morale / 100)
        exp_mod = 1 + (self.experience / 200)
        
        return int(base * morale_mod * exp_mod)
    
    def get_total_soldiers(self) -> int:
        return self.infantry + self.cavalry + self.artillery + self.archers + self.spearmen
    
    def can_use_ability(self, ability_type: SpecialAbilityType) -> Tuple[bool, str]:
        """Yetenek kullanılabilir mi kontrol et"""
        ability = SPECIAL_ABILITIES.get(ability_type)
        if not ability:
            return False, "Bilinmeyen yetenek"
        
        # Bekleme süresi kontrolü
        cooldown = self.ability_cooldowns.get(ability_type, 0)
        if cooldown > 0:
            return False, f"{cooldown} tur beklemelisiniz"
        
        # Moral kontrolü
        if self.morale < ability.cost_morale:
            return False, "Yetersiz moral"
        
        # Mühimmat kontrolü
        if self.ammo < ability.cost_ammo:
            return False, "Yetersiz mühimmat"
        
        # Birlik kontrolü
        if ability_type == SpecialAbilityType.JANISSARY_VOLLEY and self.infantry < 50:
            return False, "En az 50 piyade gerekli"
        if ability_type == SpecialAbilityType.AKINCI_RAID and self.cavalry < 30:
            return False, "En az 30 süvari gerekli"
        if ability_type == SpecialAbilityType.CANNON_BARRAGE and self.artillery < 10:
            return False, "En az 10 topçu gerekli"
        if ability_type == SpecialAbilityType.CAVALRY_CHARGE and self.cavalry < 50:
            return False, "En az 50 süvari gerekli"
        
        return True, "Kullanılabilir"
    
    def use_ability(self, ability_type: SpecialAbilityType) -> Tuple[int, int]:
        """Yeteneği kullan, (hasar, moral_hasar) döndür"""
        ability = SPECIAL_ABILITIES.get(ability_type)
        if not ability:
            return 0, 0
        
        # Maliyetleri uygula
        self.morale -= ability.cost_morale
        self.ammo -= ability.cost_ammo
        
        # Bekleme süresini ayarla
        self.ability_cooldowns[ability_type] = ability.cooldown
        
        # Temel güce göre hasar hesapla
        base_damage = self.get_power() // 10
        damage = int(base_damage * ability.damage_multiplier)
        
        return damage, ability.morale_damage
    
    def tick_cooldowns(self):
        """Her tur bekleme sürelerini azalt"""
        for ability_type in list(self.ability_cooldowns.keys()):
            self.ability_cooldowns[ability_type] -= 1
            if self.ability_cooldowns[ability_type] <= 0:
                del self.ability_cooldowns[ability_type]


# ============================================================
# KUŞATMA DURUMU
# ============================================================

@dataclass
class SiegeState:
    """Kuşatma durumu - abluka, bombardıman, hücum aşamaları"""
    phase: SiegePhase = SiegePhase.BLOCKADE
    wall_integrity: int = 100  # Sur bütünlüğü (0-100)
    defender_supplies: int = 100  # Savunucu erzak (0-100)
    siege_duration: int = 0  # Kaç tur kuşatma sürüyor
    breaches: int = 0  # Sur gedikleri
    
    def get_phase_name(self) -> str:
        names = {
            SiegePhase.BLOCKADE: "Abluka",
            SiegePhase.BOMBARDMENT: "Bombardıman",
            SiegePhase.ASSAULT: "Genel Hücum"
        }
        return names.get(self.phase, "Bilinmeyen")
    
    def process_turn(self, attacker_artillery: int, has_supply_line: bool = True) -> Dict:
        """Kuşatma turunu işle"""
        self.siege_duration += 1
        result = {
            "wall_damage": 0,
            "supply_loss": 0,
            "surrender_chance": 0,
            "breach_created": False
        }
        
        if self.phase == SiegePhase.BLOCKADE:
            # Abluka - erzak kesilir
            supply_loss = random.randint(5, 15)
            if not has_supply_line:
                supply_loss += 10
            self.defender_supplies = max(0, self.defender_supplies - supply_loss)
            result["supply_loss"] = supply_loss
            
            # Açlık teslimi şansı
            if self.defender_supplies < 20:
                result["surrender_chance"] = (20 - self.defender_supplies) * 3
            
        elif self.phase == SiegePhase.BOMBARDMENT:
            # Bombardıman - surlar yıkılır
            wall_damage = attacker_artillery * random.uniform(0.5, 1.5)
            self.wall_integrity = max(0, self.wall_integrity - int(wall_damage))
            result["wall_damage"] = int(wall_damage)
            
            # Gedik açılma şansı
            if random.random() < 0.1 + (100 - self.wall_integrity) / 200:
                self.breaches += 1
                result["breach_created"] = True
        
        elif self.phase == SiegePhase.ASSAULT:
            # Hücum - yoğun kayıp ama hızlı sonuç
            pass  # Savaş ekranında işlenir
        
        return result
    
    def can_advance_phase(self) -> Tuple[bool, str]:
        """Bir sonraki aşamaya geçilebilir mi?"""
        if self.phase == SiegePhase.BLOCKADE:
            if self.defender_supplies < 50 or self.siege_duration >= 3:
                return True, "Abluka etkili oldu, bombardımana geçilebilir"
            return False, f"En az 3 tur veya erzak 50 altına inmeli (şu an: {self.defender_supplies})"
        
        elif self.phase == SiegePhase.BOMBARDMENT:
            if self.wall_integrity < 50 or self.breaches >= 1:
                return True, "Surlar zayıfladı, hücuma geçilebilir"
            return False, f"Sur bütünlüğü 50 altına inmeli veya gedik açılmalı (şu an: {self.wall_integrity})"
        
        return False, "Zaten son aşamada"


# ============================================================
# SAVAŞ SINIFI (GELİŞTİRİLMİŞ)
# ============================================================

@dataclass
class Battle:
    """Aktif savaş - geliştirilmiş"""
    battle_id: str
    battle_type: BattleType
    attacker_name: str
    defender_name: str
    attacker_army: Army
    defender_army: Army
    phase: BattlePhase
    turns_remaining: int
    terrain: TerrainType = TerrainType.PLAINS
    weather: WeatherType = WeatherType.CLEAR
    terrain_bonus: float = 1.0
    is_player_attacker: bool = True
    
    # Kuşatma durumu
    siege_state: Optional[SiegeState] = None
    
    # Savaş istatistikleri (rapor için)
    tactics_used: List[str] = field(default_factory=list)
    abilities_used: List[str] = field(default_factory=list)
    rounds_fought: int = 0
    
    def __post_init__(self):
        if self.battle_type == BattleType.SIEGE and self.siege_state is None:
            self.siege_state = SiegeState()
    
    def get_status_text(self) -> str:
        phase_names = {
            BattlePhase.PREPARATION: "Hazırlık",
            BattlePhase.MARCH: "Yürüyüş",
            BattlePhase.COMBAT: "Çatışma",
            BattlePhase.AFTERMATH: "Sonuç"
        }
        status = f"{phase_names[self.phase]} - {self.turns_remaining} tur kaldı"
        
        if self.siege_state:
            status += f" | Kuşatma: {self.siege_state.get_phase_name()}"
            status += f" | Sur: %{self.siege_state.wall_integrity}"
        
        return status
    
    def get_terrain_description(self) -> str:
        """Arazi açıklaması"""
        terrain_names = {
            TerrainType.PLAINS: "Ova - dengeli savaş alanı",
            TerrainType.FOREST: "Orman - süvari dezavantajı, pusu riski",
            TerrainType.MOUNTAIN: "Dağ - savunma avantajı, süvari zor",
            TerrainType.RIVER: "Nehir Geçişi - saldırı dezavantajı",
            TerrainType.FORTRESS: "Kale - güçlü savunma, topçu etkili",
            TerrainType.DESERT: "Çöl - moral kaybı, lojistik sorun",
            TerrainType.SWAMP: "Bataklık - süvari ve topçu dezavantajı"
        }
        return terrain_names.get(self.terrain, "Bilinmeyen arazi")


# ============================================================
# SAVAŞ SONUCU
# ============================================================

@dataclass
class BattleResult:
    """Savaş sonucu"""
    victory: bool
    attacker_casualties: int
    defender_casualties: int
    loot_gold: int = 0
    loot_food: int = 0
    loot_resources: Dict[str, int] = None
    territory_gained: str = None
    loyalty_change: int = 0
    morale_change: int = 0
    experience_gained: int = 0
    battle_report: Optional[BattleReport] = None


# ============================================================
# GELİŞMİŞ DÜŞMAN AI
# ============================================================

class EnemyAI:
    """Gelişmiş düşman yapay zekası"""
    
    def __init__(self):
        # Oyuncu taktik geçmişi (öğrenme için)
        self.player_tactic_history: List[str] = []
        self.counter_tactics = {
            "center_attack": "defend",
            "flank": "counter_flank",
            "defend": "artillery",
            "artillery": "charge",
            "feint": "hold",
            "demand_surrender": "attack"
        }
    
    def learn_player_tactic(self, tactic: str):
        """Oyuncu taktiğini öğren"""
        self.player_tactic_history.append(tactic)
        # Son 10 taktiği tut
        if len(self.player_tactic_history) > 10:
            self.player_tactic_history.pop(0)
    
    def predict_player_tactic(self) -> Optional[str]:
        """Oyuncunun olası taktiğini tahmin et"""
        if len(self.player_tactic_history) < 3:
            return None
        
        # En sık kullanılan taktiği bul
        from collections import Counter
        counter = Counter(self.player_tactic_history[-5:])
        most_common = counter.most_common(1)
        if most_common and most_common[0][1] >= 2:
            return most_common[0][0]
        return None
    
    def choose_tactic(self, enemy_morale: int, player_morale: int,
                     enemy_army: Army, terrain: TerrainType) -> str:
        """Akıllı taktik seçimi"""
        
        # Oyuncu taktiğini tahmin et ve karşılık ver
        predicted_tactic = self.predict_player_tactic()
        if predicted_tactic and random.random() < 0.6:  # %60 karşılık verme şansı
            counter = self.counter_tactics.get(predicted_tactic)
            if counter:
                return counter
        
        # Moral bazlı karar
        if enemy_morale > 80:
            # Yüksek moral - agresif
            if terrain == TerrainType.PLAINS and enemy_army.cavalry > 30:
                return random.choice(["charge", "flank", "charge"])
            return random.choice(["attack", "attack", "flank", "artillery"])
        
        elif enemy_morale > 50:
            # Orta moral - dengeli
            if enemy_army.artillery > 10:
                return random.choice(["artillery", "defend", "attack"])
            return random.choice(["flank", "defend", "attack"])
        
        elif enemy_morale > 25:
            # Düşük moral - savunmacı
            return random.choice(["defend", "defend", "retreat", "hold"])
        
        else:
            # Çok düşük moral - umutsuz
            if random.random() < 0.3:
                return "desperate_attack"  # Umutsuz saldırı
            return random.choice(["defend", "surrender_consider"])
    
    def get_tactic_result(self, tactic: str, enemy_army: Army, 
                          player_army: Army, terrain: TerrainType) -> Dict:
        """Taktik sonucunu hesapla"""
        terrain_mod = TERRAIN_MODIFIERS.get(terrain, {})
        attack_mod = terrain_mod.get("attack", 1.0)
        defense_mod = terrain_mod.get("defense", 1.0)
        
        result = {
            "damage_to_player": 0,
            "damage_to_enemy": 0,
            "morale_damage_to_player": 0,
            "morale_damage_to_enemy": 0,
            "message": ""
        }
        
        base_power = enemy_army.get_power(terrain)
        
        if tactic == "attack":
            damage = int(random.randint(15, 30) * attack_mod)
            result["damage_to_player"] = damage
            result["morale_damage_to_player"] = random.randint(5, 15)
            result["damage_to_enemy"] = random.randint(10, 20)
            result["message"] = f"Düşman merkez hücumu! {damage} hasar aldık."
        
        elif tactic == "charge":
            damage = int(random.randint(20, 40) * attack_mod * terrain_mod.get("cavalry", 1.0))
            result["damage_to_player"] = damage
            result["morale_damage_to_player"] = random.randint(10, 20)
            result["damage_to_enemy"] = random.randint(15, 30)
            result["message"] = f"Düşman süvari şarjı! Yoğun {damage} hasar!"
        
        elif tactic == "flank" or tactic == "counter_flank":
            damage = int(random.randint(10, 25) * attack_mod)
            result["damage_to_player"] = damage
            result["morale_damage_to_player"] = random.randint(8, 18)
            result["message"] = f"Düşman kanat manevrası! {damage} hasar."
        
        elif tactic == "defend" or tactic == "hold":
            result["damage_to_player"] = random.randint(5, 15)
            result["damage_to_enemy"] = 0
            result["message"] = "Düşman savunma pozisyonunda, kayıplarımız az."
        
        elif tactic == "artillery":
            damage = int(random.randint(15, 35) * terrain_mod.get("artillery", 1.0))
            result["damage_to_player"] = damage
            result["morale_damage_to_player"] = random.randint(5, 15)
            result["message"] = f"Düşman top ateşi! {damage} hasar."
        
        elif tactic == "desperate_attack":
            damage = random.randint(25, 50)
            result["damage_to_player"] = damage
            result["damage_to_enemy"] = random.randint(30, 60)
            result["morale_damage_to_player"] = random.randint(5, 15)
            result["morale_damage_to_enemy"] = 20
            result["message"] = f"Düşman umutsuz saldırı! Ağır kayıplar: {damage} hasar."
        
        elif tactic == "retreat":
            result["message"] = "Düşman geri çekiliyor..."
        
        elif tactic == "surrender_consider":
            result["message"] = "Düşman teslim olmayı düşünüyor..."
        
        return result


# ============================================================
# SAVAŞ YÖNETİM SİSTEMİ (GELİŞTİRİLMİŞ)
# ============================================================

class WarfareSystem:
    """Savaş yönetim sistemi - geliştirilmiş"""
    
    # Erken oyun koruması - bu turdan önce saldırı yok
    EARLY_GAME_PROTECTION = 12
    
    def __init__(self):
        self.active_battles: List[Battle] = []
        self.war_history: List[Dict] = []
        self.war_weariness = 0  # Savaş yorgunluğu
        self.battle_counter = 0
        
        # Gelişmiş AI
        self.enemy_ai = EnemyAI()
        
        # Savaş raporları
        self.battle_reports: List[BattleReport] = []
        
        # Savaş maliyetleri (dengelenmiş - zahire düşürüldü)
        self.battle_costs = {
            BattleType.RAID: {'gold': 300, 'food': 100},
            BattleType.SIEGE: {'gold': 1500, 'food': 400, 'wood': 300},
            BattleType.CAMPAIGN: {'gold': 3000, 'food': 800, 'iron': 200},
            BattleType.NAVAL_RAID: {'gold': 500, 'food': 150},  # Deniz akını
        }
        
        # Bekleyen akın raporu (RaidReportScreen için)
        self.pending_raid_report = None
        
        # Bekleyen kuşatma savaşı (BattleScreen için)
        self.pending_siege_battle = None
    
    def can_start_war(self, turn_count: int) -> Tuple[bool, str]:
        """Savaş başlatılabilir mi?"""
        if turn_count < self.EARLY_GAME_PROTECTION:
            return False, f"İlk {self.EARLY_GAME_PROTECTION} tur savaş başlatılamaz ({turn_count}/{self.EARLY_GAME_PROTECTION})"
        
        if self.war_weariness > 80:
            return False, "Ordu çok yorgun (savaş yorgunluğu > 80)"
        
        if len(self.active_battles) >= 2:
            return False, "Aynı anda en fazla 2 savaş yönetilebilir"
        
        return True, "Savaş başlatılabilir"
    
    def get_random_terrain(self, target: str) -> TerrainType:
        """Hedef bölgeye göre rastgele arazi"""
        # Basit eşleşme - gelecekte territories.py'den alınabilir
        if "Dağ" in target or "Kafkas" in target:
            return TerrainType.MOUNTAIN
        elif "Orman" in target or "Bosna" in target:
            return TerrainType.FOREST
        elif "Kale" in target or "Kale" in target:
            return TerrainType.FORTRESS
        elif "Nehir" in target or "Fırat" in target:
            return TerrainType.RIVER
        elif "Çöl" in target or "Mısır" in target:
            return TerrainType.DESERT
        else:
            return random.choice([TerrainType.PLAINS, TerrainType.PLAINS, TerrainType.FOREST])
    
    def get_random_weather(self) -> WeatherType:
        """Rastgele hava durumu"""
        weights = [0.5, 0.2, 0.1, 0.1, 0.1]  # Açık hava en olası
        return random.choices(list(WeatherType), weights=weights)[0]
    
    def start_raid(self, target: str, military_system, economy, turn_count: int, 
                   raid_bonus: float = 0.0, artillery_march_penalty: float = 0.0) -> Tuple[bool, str]:
        """
        Akın başlat
        raid_bonus: Liderlik bonusu (erkek bizzat: 0.20, kadın vekil: 0.0)
        artillery_march_penalty: Topçu ağırlığından yürüyüş cezası (0-2 tur)
        """
        can_start, reason = self.can_start_war(turn_count)
        if not can_start:
            return False, reason
        
        # Maliyet kontrolü
        costs = self.battle_costs[BattleType.RAID]
        if not economy.can_afford(**costs):
            return False, "Yetersiz kaynak (akın için altın ve zahire gerekli)"
        
        # Yeterli asker var mı?
        if military_system.get_total_soldiers() < 100:
            return False, "En az 100 asker gerekli"
        
        # Maliyeti al
        economy.spend(**costs)
        
        # Savaş oluştur
        self.battle_counter += 1
        terrain = self.get_random_terrain(target)
        weather = self.get_random_weather()
        
        # Liderlik bonusu uygula
        bonus_morale = int(military_system.morale * raid_bonus)
        bonus_exp = int(military_system.experience * raid_bonus)
        
        # Yürüyüş süresi + topçu ağırlık cezası
        march_turns = 2 + int(artillery_march_penalty)
        
        battle = Battle(
            battle_id=f"raid_{self.battle_counter}",
            battle_type=BattleType.RAID,
            attacker_name="Ordumuz",
            defender_name=target,
            attacker_army=Army(
                infantry=military_system.infantry,
                cavalry=military_system.cavalry,
                artillery=military_system.artillery_crew,
                morale=min(100, military_system.morale + bonus_morale),
                experience=min(100, military_system.experience + bonus_exp),
                commander=military_system.assigned_commander
            ),
            defender_army=Army(
                infantry=random.randint(50, 200),
                cavalry=random.randint(20, 80),
                artillery=random.randint(0, 10),
                morale=random.randint(60, 90)
            ),
            phase=BattlePhase.MARCH,
            turns_remaining=march_turns,
            terrain=terrain,
            weather=weather
        )
        
        self.active_battles.append(battle)
        self.war_weariness += 10
        
        audio = get_audio_manager()
        weather_name = {"clear": "Açık", "rain": "Yağmurlu", "snow": "Karlı", "fog": "Sisli", "storm": "Fırtınalı"}.get(weather.value, "Açık")
        march_msg = f"{target} bölgesine akın başlatıldı! Arazi: {battle.get_terrain_description()}, Hava: {weather_name}"
        if artillery_march_penalty > 0:
            march_msg += f". Topçu ağırlığı yürüyüşü yavaşlatıyor (+{int(artillery_march_penalty)} gün)."
        audio.announce(march_msg)
        
        return True, f"{target} bölgesine akın başlatıldı!"
    
    def start_siege(self, target: str, military_system, economy, turn_count: int,
                    artillery_march_penalty: float = 0.0) -> Tuple[bool, str]:
        """Kuşatma başlat — topçu ağırlığı yürüyüş süresini uzatır"""
        can_start, reason = self.can_start_war(turn_count)
        if not can_start:
            return False, reason
        
        # Maliyet kontrolü
        costs = self.battle_costs[BattleType.SIEGE]
        if not economy.can_afford(**costs):
            return False, "Yetersiz kaynak (kuşatma için altın, zahire ve kereste gerekli)"
        
        # Yeterli asker var mı?
        if military_system.get_total_soldiers() < 300:
            return False, "Kuşatma için en az 300 asker gerekli"
        
        # Topçu var mı?
        if military_system.artillery_crew < 5:
            return False, "Kuşatma için en az 5 topçu gerekli"
        
        # Maliyeti al
        economy.spend(**costs)
        
        # Savaş oluştur
        self.battle_counter += 1
        terrain = TerrainType.FORTRESS  # Kuşatma her zaman kale
        weather = self.get_random_weather()
        
        # Yürüyüş süresi + topçu ağırlık cezası
        march_turns = 3 + int(artillery_march_penalty)
        
        battle = Battle(
            battle_id=f"siege_{self.battle_counter}",
            battle_type=BattleType.SIEGE,
            attacker_name="Ordumuz",
            defender_name=target,
            attacker_army=Army(
                infantry=military_system.infantry,
                cavalry=military_system.cavalry,
                artillery=military_system.artillery_crew,
                morale=military_system.morale,
                experience=military_system.experience,
                ammo=100,
                commander=military_system.assigned_commander
            ),
            defender_army=Army(
                infantry=random.randint(200, 500),
                cavalry=random.randint(30, 100),
                artillery=random.randint(10, 30),
                morale=random.randint(70, 95)
            ),
            phase=BattlePhase.MARCH,
            turns_remaining=march_turns,
            terrain=terrain,
            weather=weather,
            siege_state=SiegeState()
        )
        
        self.active_battles.append(battle)
        self.war_weariness += 20
        
        audio = get_audio_manager()
        march_msg = f"{target} kuşatması başladı! Abluka aşamasından başlanacak."
        if artillery_march_penalty > 0:
            march_msg += f" Ağır topçu yürüyüşü yavaşlatıyor (+{int(artillery_march_penalty)} gün)."
        audio.announce(march_msg)
        
        return True, f"{target} kuşatması başlatıldı! {march_turns} tur içinde ulaşılacak."
    
    def start_naval_raid(self, target: str, naval_system, economy, turn_count: int, 
                        is_coastal: bool = False) -> Tuple[bool, str]:
        """Deniz akını başlat - sadece kıyı eyaletleri için"""
        if not is_coastal:
            return False, "Deniz akını için kıyı eyaletinde olmalısınız!"
        
        can_start, reason = self.can_start_war(turn_count)
        if not can_start:
            return False, reason
        
        # Filo kontrolü
        # Filo kontrolü (En az 3 savaş gemisi ve 100 savaş gücü)
        warship_count = sum(1 for s in naval_system.ships if s.get_definition().is_warship)
        if warship_count < 3:
            return False, "Deniz akını için en az 3 savaş gemisi gerekli!"
            
        fleet_power = naval_system.get_fleet_power()
        if fleet_power < 100:
            return False, "Donanmanız bu akın için fazla zayıf (En az 100 savaş gücü gerekli)."
        
        # Maliyet kontrolü
        costs = self.battle_costs[BattleType.NAVAL_RAID]
        if not economy.can_afford(**costs):
            return False, "Yetersiz kaynak (deniz akını için altın ve zahire gerekli)"
        
        # Maliyeti al
        economy.spend(**costs)
        
        # Deniz savaşı oluştur
        self.battle_counter += 1
        fleet_power = naval_system.get_fleet_power()
        
        # Düşman filosu oluştur (hedef bölgeye göre)
        enemy_warships = random.randint(1, 5)
        enemy_power = enemy_warships * random.randint(20, 40)
        
        battle = Battle(
            battle_id=f"naval_{self.battle_counter}",
            battle_type=BattleType.NAVAL_RAID,
            attacker_name="Osmanlı Donanması",
            defender_name=target,
            attacker_army=Army(
                infantry=0,  # Denizde kara kuvveti yok
                cavalry=0,
                artillery=fleet_power,  # Filo gücünü artillery olarak kullan
                morale=90,
                experience=10
            ),
            defender_army=Army(
                infantry=0,
                cavalry=0,
                artillery=enemy_power,
                morale=random.randint(60, 85)
            ),
            phase=BattlePhase.MARCH,
            turns_remaining=3,
            terrain=TerrainType.RIVER,  # Deniz olarak river kullan
            weather=self.get_random_weather()
        )
        
        self.active_battles.append(battle)
        self.war_weariness += 15
        
        audio = get_audio_manager()
        audio.announce(f"Donanma {target} hedefine yola çıktı! {warship_count} savaş gemisi.")
        
        return True, f"{target} bölgesine deniz akını başlatıldı!"

    
    def process_battles(self, military_system, artillery_power: int = 0, 
                        siege_bonus: int = 0, naval_power: int = 0,
                        naval_system=None) -> List[BattleResult]:
        """Aktif savaşları işle - topçu ve deniz gücü desteği ile"""
        results = []
        completed = []
        
        # Topçu ve deniz gücünü tutorya
        self._current_artillery_power = artillery_power
        self._current_siege_bonus = siege_bonus
        self._current_naval_power = naval_power
        
        for battle in self.active_battles:
            battle.turns_remaining -= 1
            
            if battle.turns_remaining <= 0:
                if battle.phase == BattlePhase.MARCH:
                    battle.phase = BattlePhase.COMBAT
                    battle.turns_remaining = 1 if battle.battle_type in (BattleType.RAID, BattleType.NAVAL_RAID) else 5
                    
                    audio = get_audio_manager()
                    
                    # Kuşatma savaşları için interaktif savaş ekranını aç
                    if battle.battle_type == BattleType.SIEGE:
                        audio.announce(f"{battle.defender_name} kuşatması başladı! Savaş ekranı açılıyor...")
                        battle.combat_ready = True
                        self.pending_siege_battle = {
                            'battle_id': battle.battle_id,
                            'target': battle.defender_name,
                            'terrain': battle.terrain.value,
                            'weather': battle.weather.value,
                            'siege_phase': battle.siege_state.phase.value if battle.siege_state else "blockade",
                            'wall_integrity': battle.siege_state.wall_integrity if battle.siege_state else 100,
                            'attacker_army': {
                                'infantry': battle.attacker_army.infantry,
                                'cavalry': battle.attacker_army.cavalry,
                                'artillery': battle.attacker_army.artillery,
                                'morale': battle.attacker_army.morale,
                                'ammo': battle.attacker_army.ammo
                            },
                            'defender_army': {
                                'infantry': battle.defender_army.infantry,
                                'cavalry': battle.defender_army.cavalry,
                                'artillery': battle.defender_army.artillery,
                                'morale': battle.defender_army.morale
                            }
                        }
                    else:
                        audio.announce(f"{battle.defender_name} ile çatışma başladı!")
                    
                elif battle.phase == BattlePhase.COMBAT:
                    result = self._resolve_battle(battle, military_system, naval_system)
                    results.append(result)
                    completed.append(battle)
        
        # Tamamlanan savaşları kaldır
        for battle in completed:
            self.active_battles.remove(battle)
            self.war_history.append({
                'target': battle.defender_name,
                'type': battle.battle_type.value,
                'victory': results[-1].victory if results else False,
                'terrain': battle.terrain.value,
                'weather': battle.weather.value
            })
        
        # Savaş yorgunluğu azalır
        if not self.active_battles:
            self.war_weariness = max(0, self.war_weariness - 5)
        
        return results
    
    def _resolve_battle(self, battle: Battle, military_system, naval_system=None) -> BattleResult:
        """Savaş sonucunu hesapla — hava durumu topçu etkisi dahil"""
        terrain = battle.terrain
        weather = battle.weather
        
        attacker_power = battle.attacker_army.get_power(terrain, weather)
        
        # Topçu ocağı bonusu ekle
        artillery_bonus = getattr(self, '_current_artillery_power', 0)
        siege_bonus = getattr(self, '_current_siege_bonus', 0)
        naval_bonus = getattr(self, '_current_naval_power', 0)
        morale_bonus = getattr(self, '_current_morale_damage', 0)
        
        # === HAVA DURUMU TOPÇU ETKİSİ ===
        # Yağmurda barut ıslanır, fırtınada topçu tamamen devre dışı
        weather_mods = WEATHER_MODIFIERS.get(weather, {})
        artillery_weather_mult = weather_mods.get('artillery', 1.0)
        
        artillery_bonus = int(artillery_bonus * artillery_weather_mult)
        siege_bonus = int(siege_bonus * artillery_weather_mult)
        
        # Hava durumu topçu mesajı
        if artillery_weather_mult < 1.0 and (artillery_bonus > 0 or siege_bonus > 0):
            audio = get_audio_manager()
            if artillery_weather_mult == 0:
                audio.speak("Fırtına! Topçu birliği tamamen devre dışı!", interrupt=False)
            elif artillery_weather_mult <= 0.3:
                audio.speak(f"Yağmur topçu etkinliğini ciddi düşürdü! (yüzde {int(artillery_weather_mult*100)})", interrupt=False)
            else:
                audio.speak(f"Hava koşulları topçuyu etkiliyor (yüzde {int(artillery_weather_mult*100)} etkinlik).", interrupt=False)
        
        # Savaş türüne göre bonus uygula
        if battle.battle_type == BattleType.SIEGE:
            attacker_power += artillery_bonus * 2  # Kuşatmada toplar çift etkili
            attacker_power += siege_bonus * 3  # Kuşatma bonusu daha fazla
        elif battle.battle_type == BattleType.NAVAL_RAID:
            attacker_power += naval_bonus * 2  # Deniz savaşında filo gücü çift etkili
        else:
            attacker_power += artillery_bonus  # Akınlarda normal etki
        
        # Savunucu arazi avantajı
        defense_mod = TERRAIN_MODIFIERS.get(terrain, {}).get("defense", 1.0)
        defender_power = int(battle.defender_army.get_power(terrain, weather) * defense_mod)
        
        # Rastgelelik ekle
        attacker_roll = random.uniform(0.8, 1.2)
        defender_roll = random.uniform(0.8, 1.2)
        
        final_attacker = int(attacker_power * attacker_roll)
        final_defender = int(defender_power * defender_roll)
        
        # Sonuç
        victory = final_attacker > final_defender
        
        # Kayıplar hesapla
        if victory:
            attacker_casualties = random.randint(20, 80)
            defender_casualties = random.randint(100, 300)
        else:
            attacker_casualties = random.randint(80, 200)
            defender_casualties = random.randint(30, 100)
        
        # Kayıpları uygula
        from game.systems.military import UnitType as MilitaryUnitType
        # Deneyim hesaplaması (Kara/Deniz ikisi de kullanıyor)
        exp_gain = 5 if victory else 2
        
        if battle.battle_type == BattleType.NAVAL_RAID and naval_system:
            # Gemi hasarları
            warships = [s for s in naval_system.ships if s.get_definition().is_warship]
            damage_roll = random.randint(10, 30)
            if not victory:
                damage_roll = int(damage_roll * 1.5)
                
            for ship in warships:
                dmg = int(damage_roll * random.uniform(0.5, 1.5))
                ship.health -= dmg
                if ship.health <= 0:
                    naval_system.ships.remove(ship)
                    naval_system.ships_lost += 1
            
            if victory:
                naval_system.naval_victories += 1
                for ship in warships:
                    ship.experience += min(50, random.randint(5, 15))
            else:
                naval_system.naval_defeats += 1
        else:
            # Standart kara savaşı asker kayıpları
            infantry_loss = int(attacker_casualties * 0.6)
            cavalry_loss = int(attacker_casualties * 0.3)
            artillery_loss = int(attacker_casualties * 0.1)
            
            # Piyade kayıpları (Yeniçeri ve Azap'a dağıt)
            yenicheri_loss = infantry_loss // 2
            azap_loss = infantry_loss - yenicheri_loss
            military_system.units[MilitaryUnitType.YENICHERI] = max(0, military_system.units.get(MilitaryUnitType.YENICHERI, 0) - yenicheri_loss)
            military_system.units[MilitaryUnitType.AZAP] = max(0, military_system.units.get(MilitaryUnitType.AZAP, 0) - azap_loss)
            
            # Süvari kayıpları (Sipahi)
            military_system.units[MilitaryUnitType.SIPAHI] = max(0, military_system.units.get(MilitaryUnitType.SIPAHI, 0) - cavalry_loss)
            
            # Topçu kayıpları
            military_system.units[MilitaryUnitType.TOPCU] = max(0, military_system.units.get(MilitaryUnitType.TOPCU, 0) - artillery_loss)
            
            
            # Kara ordusu deneyim kazan
            military_system.experience = min(100, military_system.experience + exp_gain)
        
        # Yağma
        loot_gold = 0
        loot_food = 0
        if victory:
            if battle.battle_type in (BattleType.RAID, BattleType.NAVAL_RAID):
                loot_gold = random.randint(500, 2000)
                loot_food = random.randint(100, 500)
                if battle.battle_type == BattleType.NAVAL_RAID:
                    loot_gold = int(loot_gold * 1.5)  # Deniz akınları daha karlı
            elif battle.battle_type == BattleType.SIEGE:
                loot_gold = random.randint(2000, 10000)
                loot_food = random.randint(500, 1500)
        
        # Savaş raporu oluştur
        report = BattleReport(
            battle_id=battle.battle_id,
            battle_type=battle.battle_type,
            target_name=battle.defender_name,
            victory=victory,
            rounds_fought=battle.rounds_fought,
            player_infantry_lost=int(attacker_casualties * 0.6),
            player_cavalry_lost=int(attacker_casualties * 0.3),
            player_artillery_lost=int(attacker_casualties * 0.1),
            enemy_infantry_lost=int(defender_casualties * 0.6),
            enemy_cavalry_lost=int(defender_casualties * 0.3),
            enemy_artillery_lost=int(defender_casualties * 0.1),
            tactics_used=battle.tactics_used,
            abilities_used=battle.abilities_used,
            loot_gold=loot_gold,
            loot_food=loot_food,
            experience_gained=exp_gain,
            terrain=battle.terrain.value,
            weather=battle.weather.value
        )
        self.battle_reports.append(report)
        
        # Akın raporu için pending_raid_report'u ayarla (RaidReportScreen için)
        if battle.battle_type in (BattleType.RAID, BattleType.NAVAL_RAID):
            # RaidStory formatına uygun veri
            encounter_types = ['resistance', 'ambush', 'surrender', 'fortified', 'chase']
            if battle.battle_type == BattleType.NAVAL_RAID:
                encounter_types = ['patrol', 'ambush', 'surrender', 'none']
            
            # Eyalet ölçeğine uygun, gerçekçi jenerik yerel düşman komutanları
            commanders = [
                # İsyancılar ve Eşkıyalar
                'Kızılca Ali', 'Deli Hasan', 'Kör Hüseyin', 'Softa Halil', 'Softa Mustafa',
                # Balkan/Macar/Hırvat sınır beyleri
                'István Kaptan', 'Farkas Vayvoda', 'Petar Hırvat', 'Mihail Voyvoda', 'Nikolas Kaptan',
                # Venedik/İtalyan/Şövalye denizcileri veya paralı askerleri
                'Capitano Marco', 'Conte Giovanni', 'Sir Pietro', 'Kaptan Andrea',
                # Safevi/İran sınır komutanları
                'Şahkulu Han', 'Hüseyin Mirza', 'Ali Kuli Han', 'Rıza Bey', 'Mahmud Han',
                # Memlük/Arap yerel emirleri
                'Emir Seyfeddin', 'Şeyh Mahmud', 'Mansur Bey', 'Emir Tarık'
            ]
            
            is_naval = battle.battle_type == BattleType.NAVAL_RAID
            
            self.pending_raid_report = {
                'target_name': battle.defender_name,
                'raid_size': max(1, battle.attacker_army.get_total_soldiers()) if not is_naval else max(1, int(battle.attacker_army.artillery / 20)),
                'villages_raided': random.randint(2, 8),
                'encounter_type': random.choice(encounter_types),
                'loot_gold': loot_gold,
                'loot_food': loot_food,
                'prisoners_taken': random.randint(10, 100) if victory else 0,
                'enemy_killed': defender_casualties,
                'our_casualties': attacker_casualties,
                'victory': victory,
                'enemy_commander': random.choice(commanders),
                'special_event': random.choice([None, None, 'hidden_treasure', 'ambush_survived', 'local_guide']),
                'is_naval': is_naval
            }
        
        # Audio bildirimi
        audio = get_audio_manager()
        if victory:
            audio.announce(f"ZAFER! {battle.defender_name} fethedildi! {loot_gold} altın yağma.")
        else:
            audio.announce(f"YENİLGİ! {battle.defender_name} saldırısı başarısız.")
        
        return BattleResult(
            victory=victory,
            attacker_casualties=attacker_casualties,
            defender_casualties=defender_casualties,
            loot_gold=loot_gold,
            loot_food=loot_food,
            loyalty_change=10 if victory else -10,
            morale_change=10 if victory else -20,
            experience_gained=exp_gain,
            battle_report=report
        )
    
    def handle_enemy_attack(self, attacker: str, military_system, turn_count: int) -> Optional[Battle]:
        """Düşman saldırısını işle"""
        if turn_count < self.EARLY_GAME_PROTECTION:
            return None
        
        # Saldırı şansı
        attack_chance = 0.05 + (turn_count - self.EARLY_GAME_PROTECTION) * 0.005
        attack_chance = min(0.15, attack_chance)
        
        if random.random() > attack_chance:
            return None
        
        # Saldırı oluştur
        self.battle_counter += 1
        terrain = self.get_random_terrain(attacker)
        weather = self.get_random_weather()
        
        battle = Battle(
            battle_id=f"defense_{self.battle_counter}",
            battle_type=BattleType.DEFENSE,
            attacker_name=attacker,
            defender_name="Eyaletimiz",
            attacker_army=Army(
                infantry=random.randint(100, 400),
                cavalry=random.randint(50, 150),
                artillery=random.randint(5, 20),
                morale=random.randint(70, 95)
            ),
            defender_army=Army(
                infantry=military_system.infantry,
                cavalry=military_system.cavalry,
                artillery=military_system.artillery,
                morale=military_system.morale
            ),
            phase=BattlePhase.COMBAT,
            turns_remaining=3,
            terrain=terrain,
            weather=weather,
            is_player_attacker=False
        )
        
        self.active_battles.append(battle)
        
        audio = get_audio_manager()
        audio.announce(f"DİKKAT! {attacker} eyaletimize saldırıyor! Savunmaya geçin!")
        
        return battle
    
    def announce_status(self):
        """Savaş durumunu duyur"""
        audio = get_audio_manager()
        
        if not self.active_battles:
            audio.speak("Aktif savaş yok.", interrupt=True)
        else:
            audio.speak(f"{len(self.active_battles)} aktif savaş var:", interrupt=True)
            for battle in self.active_battles:
                status = battle.get_status_text()
                audio.speak(f"{battle.defender_name}: {status}", interrupt=False)
    
    def get_available_abilities(self, army: Army) -> List[Tuple[SpecialAbility, bool, str]]:
        """Kullanılabilir özel yetenekleri listele"""
        result = []
        for ability_type, ability in SPECIAL_ABILITIES.items():
            can_use, reason = army.can_use_ability(ability_type)
            result.append((ability, can_use, reason))
        return result
    
    def to_dict(self) -> Dict:
        """Kayıt için dictionary'e dönüştür"""
        return {
            'war_weariness': self.war_weariness,
            'battle_counter': self.battle_counter,
            'war_history': self.war_history,
            'player_tactic_history': self.enemy_ai.player_tactic_history
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'WarfareSystem':
        """Dictionary'den yükle"""
        system = cls()
        system.war_weariness = data.get('war_weariness', 0)
        system.battle_counter = data.get('battle_counter', 0)
        system.war_history = data.get('war_history', [])
        system.enemy_ai.player_tactic_history = data.get('player_tactic_history', [])
        return system
