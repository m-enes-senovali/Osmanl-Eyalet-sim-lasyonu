# -*- coding: utf-8 -*-
"""
Osmanlı Eyalet Yönetim Simülasyonu - Savaş Sistemi
Akın, kuşatma, savunma ve sefer mekanikleri
"""

from dataclasses import dataclass
from typing import Dict, List, Optional
from enum import Enum
import random
from audio.audio_manager import get_audio_manager


class BattleType(Enum):
    """Savaş türleri"""
    RAID = "raid"           # Akın - hızlı yağma
    SIEGE = "siege"         # Kuşatma - kale fethi
    DEFENSE = "defense"     # Savunma
    CAMPAIGN = "campaign"   # Sefer - büyük savaş


class BattlePhase(Enum):
    """Savaş aşamaları"""
    PREPARATION = "preparation"  # Hazırlık
    MARCH = "march"              # Yürüyüş
    COMBAT = "combat"            # Çatışma
    AFTERMATH = "aftermath"      # Sonuç


@dataclass
class Army:
    """Ordu birimi"""
    infantry: int = 0      # Piyade
    cavalry: int = 0       # Süvari
    artillery: int = 0     # Topçu
    morale: int = 100      # Moral (0-100)
    experience: int = 0    # Deneyim (0-100)
    
    def get_power(self) -> int:
        """Toplam güç hesapla"""
        base = self.infantry * 1 + self.cavalry * 2 + self.artillery * 3
        morale_mod = self.morale / 100
        exp_mod = 1 + (self.experience / 200)
        return int(base * morale_mod * exp_mod)
    
    def get_total_soldiers(self) -> int:
        return self.infantry + self.cavalry + self.artillery


@dataclass
class Battle:
    """Aktif savaş"""
    battle_id: str
    battle_type: BattleType
    attacker_name: str
    defender_name: str
    attacker_army: Army
    defender_army: Army
    phase: BattlePhase
    turns_remaining: int
    terrain_bonus: float = 1.0
    is_player_attacker: bool = True
    
    def get_status_text(self) -> str:
        phase_names = {
            BattlePhase.PREPARATION: "Hazırlık",
            BattlePhase.MARCH: "Yürüyüş",
            BattlePhase.COMBAT: "Çatışma",
            BattlePhase.AFTERMATH: "Sonuç"
        }
        return f"{phase_names[self.phase]} - {self.turns_remaining} tur kaldı"


@dataclass
class BattleResult:
    """Savaş sonucu"""
    victory: bool
    attacker_casualties: int
    defender_casualties: int
    loot_gold: int = 0
    loot_resources: Dict[str, int] = None
    territory_gained: str = None
    loyalty_change: int = 0
    morale_change: int = 0


class WarfareSystem:
    """Savaş yönetim sistemi"""
    
    # Erken oyun koruması - bu turdan önce saldırı yok
    EARLY_GAME_PROTECTION = 12
    
    def __init__(self):
        self.active_battles: List[Battle] = []
        self.war_history: List[Dict] = []
        self.peace_treaties: Dict[str, int] = {}  # hedef: kalan tur
        self.war_weariness = 0  # Savaş yorgunluğu
        self.battle_counter = 0
        
        # Savaş maliyetleri
        self.battle_costs = {
            BattleType.RAID: {'gold': 300, 'food': 200},
            BattleType.SIEGE: {'gold': 1500, 'food': 800, 'wood': 300},
            BattleType.CAMPAIGN: {'gold': 3000, 'food': 1500, 'iron': 200},
        }
        
        # Bekleyen akın raporu (RaidReportScreen için)
        self.pending_raid_report = None  # Akın tamamlanınca doldurulur
        
        # Bekleyen kuşatma savaşı (BattleScreen için)
        self.pending_siege_battle = None  # Kuşatma combat aşamasına gelince doldurulur
    
    def can_start_war(self, turn_count: int) -> tuple[bool, str]:
        """Savaş başlatılabilir mi?"""
        if turn_count < self.EARLY_GAME_PROTECTION:
            remaining = self.EARLY_GAME_PROTECTION - turn_count
            return False, f"Barış dönemi: {remaining} tur daha bekleyin"
        
        if len(self.active_battles) >= 2:
            return False, "Zaten 2 aktif savaşınız var"
        
        if self.war_weariness >= 80:
            return False, "Halk savaştan yorgun, dinlenme gerekli"
        
        return True, ""
    
    def start_raid(self, target: str, military_system, economy, turn_count: int) -> Optional[Battle]:
        """Akın başlat"""
        can_start, reason = self.can_start_war(turn_count)
        if not can_start:
            audio = get_audio_manager()
            audio.announce_action_result("Akın", False, reason)
            return None
        
        cost = self.battle_costs[BattleType.RAID]
        if not economy.can_afford(**cost):
            audio = get_audio_manager()
            audio.announce_action_result("Akın", False, "Yetersiz kaynak")
            return None
        
        # Maliyet al
        economy.spend(**cost)
        
        # Ordu oluştur (mevcut askerlerin %30'u)
        total = military_system.get_total_soldiers()
        raid_size = max(20, int(total * 0.3))
        
        attacker_army = Army(
            infantry=int(raid_size * 0.7),
            cavalry=int(raid_size * 0.3),
            morale=military_system.morale,
            experience=military_system.experience
        )
        
        # Düşman ordusu (rastgele)
        defender_army = Army(
            infantry=random.randint(30, 80),
            cavalry=random.randint(10, 30),
            morale=random.randint(50, 80)
        )
        
        self.battle_counter += 1
        battle = Battle(
            battle_id=f"battle_{self.battle_counter}",
            battle_type=BattleType.RAID,
            attacker_name="Sizin Ordunuz",
            defender_name=target,
            attacker_army=attacker_army,
            defender_army=defender_army,
            phase=BattlePhase.MARCH,
            turns_remaining=2,  # Akın hızlı
            is_player_attacker=True
        )
        
        self.active_battles.append(battle)
        self.war_weariness += 10
        
        audio = get_audio_manager()
        audio.announce_action_result(
            f"{target}'a akın",
            True,
            f"{raid_size} asker yola çıktı, 2 tur sonra çatışma"
        )
        
        return battle
    
    def start_siege(self, target: str, military_system, economy, turn_count: int) -> Optional[Battle]:
        """Kuşatma başlat"""
        can_start, reason = self.can_start_war(turn_count)
        if not can_start:
            audio = get_audio_manager()
            audio.announce_action_result("Kuşatma", False, reason)
            return None
        
        cost = self.battle_costs[BattleType.SIEGE]
        if not economy.can_afford(**cost):
            audio = get_audio_manager()
            audio.announce_action_result("Kuşatma", False, "Yetersiz kaynak")
            return None
        
        # Minimum asker kontrolü
        total = military_system.get_total_soldiers()
        if total < 100:
            audio = get_audio_manager()
            audio.announce_action_result("Kuşatma", False, "En az 100 asker gerekli")
            return None
        
        economy.spend(**cost)
        
        # Ordunun %60'ı
        siege_size = int(total * 0.6)
        
        attacker_army = Army(
            infantry=int(siege_size * 0.5),
            cavalry=int(siege_size * 0.2),
            artillery=int(siege_size * 0.3),
            morale=military_system.morale,
            experience=military_system.experience
        )
        
        # Güçlü savunma
        defender_army = Army(
            infantry=random.randint(80, 150),
            cavalry=random.randint(20, 50),
            artillery=random.randint(10, 30),
            morale=random.randint(60, 90)
        )
        
        self.battle_counter += 1
        battle = Battle(
            battle_id=f"battle_{self.battle_counter}",
            battle_type=BattleType.SIEGE,
            attacker_name="Sizin Ordunuz",
            defender_name=target,
            attacker_army=attacker_army,
            defender_army=defender_army,
            phase=BattlePhase.MARCH,
            turns_remaining=4,  # Kuşatma uzun sürer
            terrain_bonus=0.8,  # Savunan avantajlı
            is_player_attacker=True
        )
        
        self.active_battles.append(battle)
        self.war_weariness += 25
        
        audio = get_audio_manager()
        audio.announce_action_result(
            f"{target} kuşatması",
            True,
            f"{siege_size} asker yola çıktı. Yolculuk 4 tur, ardından 3 tur çatışma. Toplam 7 tur sonunda sonuç"
        )
        
        return battle
    
    def process_battles(self, military_system) -> List[BattleResult]:
        """Aktif savaşları işle"""
        results = []
        completed = []
        
        for battle in self.active_battles:
            battle.turns_remaining -= 1
            
            if battle.turns_remaining <= 0:
                if battle.phase == BattlePhase.MARCH:
                    battle.phase = BattlePhase.COMBAT
                    battle.turns_remaining = 1 if battle.battle_type == BattleType.RAID else 3
                    
                    audio = get_audio_manager()
                    
                    # Kuşatma savaşları için interaktif savaş ekranını aç
                    if battle.battle_type == BattleType.SIEGE:
                        audio.announce(f"{battle.defender_name} kuşatması başladı! Savaş ekranı açılıyor...")
                        # İşaret olarak combat_ready bayrağı koy
                        battle.combat_ready = True
                        # Savaş ekranı için veri hazırla
                        self.pending_siege_battle = {
                            'battle_id': battle.battle_id,
                            'target': battle.defender_name,
                            'attacker_army': {
                                'infantry': battle.attacker_army.infantry,
                                'cavalry': battle.attacker_army.cavalry,
                                'artillery': battle.attacker_army.artillery,
                                'morale': battle.attacker_army.morale
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
                    result = self._resolve_battle(battle, military_system)
                    results.append(result)
                    completed.append(battle)
        
        # Tamamlanan savaşları kaldır
        for battle in completed:
            self.active_battles.remove(battle)
            self.war_history.append({
                'target': battle.defender_name,
                'type': battle.battle_type.value,
                'victory': results[-1].victory if results else False
            })
        
        # Savaş yorgunluğu azalır
        if not self.active_battles:
            self.war_weariness = max(0, self.war_weariness - 5)
        
        return results
    
    def _resolve_battle(self, battle: Battle, military_system) -> BattleResult:
        """Savaş sonucunu hesapla"""
        attacker_power = battle.attacker_army.get_power()
        defender_power = int(battle.defender_army.get_power() * battle.terrain_bonus)
        
        # Rastgelelik ekle
        attacker_roll = attacker_power * random.uniform(0.8, 1.2)
        defender_roll = defender_power * random.uniform(0.8, 1.2)
        
        victory = attacker_roll > defender_roll
        
        # Kayıplar
        power_ratio = defender_power / max(1, attacker_power)
        attacker_casualties = int(battle.attacker_army.get_total_soldiers() * min(0.5, power_ratio * 0.3))
        defender_casualties = int(battle.defender_army.get_total_soldiers() * min(0.7, (1/max(0.5, power_ratio)) * 0.4))
        
        # Mevcut askerleri azalt (units dict yapısına uygun)
        from game.systems.military import UnitType
        
        # Kayıpları dağıt
        total_units = military_system.get_total_soldiers()
        if total_units > 0:
            for unit_type in military_system.units:
                if military_system.units[unit_type] > 0:
                    unit_loss = int(attacker_casualties * (military_system.units[unit_type] / total_units))
                    military_system.units[unit_type] = max(0, military_system.units[unit_type] - unit_loss)
        
        audio = get_audio_manager()
        
        if victory:
            # Zafer ödülleri (artırılmış)
            if battle.battle_type == BattleType.RAID:
                loot = random.randint(1500, 4000)
            elif battle.battle_type == BattleType.SIEGE:
                loot = random.randint(5000, 15000)
            else:
                loot = random.randint(2000, 6000)
            
            # Akın için detaylı rapor oluştur
            if battle.battle_type == BattleType.RAID:
                # Akın hikaye verileri
                encounters = ["patrol", "ambush", "surrender", "none"]
                encounter = random.choices(encounters, weights=[0.3, 0.15, 0.25, 0.3])[0]
                
                self.pending_raid_report = {
                    'target_name': battle.defender_name,
                    'raid_size': battle.attacker_army.get_total_soldiers(),
                    'villages_raided': random.randint(1, 4),
                    'encounter_type': encounter,
                    'loot_gold': loot,
                    'loot_food': random.randint(100, 500),
                    'prisoners_taken': random.randint(5, 30) if encounter != "ambush" else 0,
                    'enemy_killed': defender_casualties,
                    'our_casualties': attacker_casualties,
                    'victory': True,
                    'enemy_commander': random.choice([
                        "Kont Dracula", "Voyvoda Mircea", "Ban Petrović", 
                        "Despot Lazar", "Kral Mátyás", "Dük Ferdinand"
                    ]),
                    'special_event': random.choice([
                        "Akıncılar hazine dolu bir araba ele geçirdi!",
                        "Düşman casusları pusuya düşürüldü!",
                        "Yerel halk direniş göstermeden teslim oldu.",
                        None, None, None
                    ])
                }
                # Akın raporu ekranı açılacağı için kısa duyuru
                audio.speak("Akın tamamlandı! Rapor hazırlanıyor...", interrupt=True)
            else:
                audio.announce(f"ZAFER! {battle.defender_name} yenildi! {loot} altın yağma, {attacker_casualties} kayıp")
            
            # Deneyim kazanç
            military_system.experience = min(100, military_system.experience + 10)
            military_system.morale = min(100, military_system.morale + 15)
            
            return BattleResult(
                victory=True,
                attacker_casualties=attacker_casualties,
                defender_casualties=defender_casualties,
                loot_gold=loot,
                loyalty_change=10,
                morale_change=15
            )
        else:
            # Yenilgi durumunda da akın raporu oluştur
            if battle.battle_type == BattleType.RAID:
                self.pending_raid_report = {
                    'target_name': battle.defender_name,
                    'raid_size': battle.attacker_army.get_total_soldiers(),
                    'villages_raided': random.randint(0, 1),
                    'encounter_type': random.choice(["ambush", "patrol"]),
                    'loot_gold': 0,
                    'loot_food': 0,
                    'prisoners_taken': 0,
                    'enemy_killed': defender_casualties,
                    'our_casualties': attacker_casualties,
                    'victory': False,
                    'enemy_commander': random.choice([
                        "Kont Dracula", "Voyvoda Mircea", "Ban Petrović", 
                        "Despot Lazar", "Kral Mátyás", "Dük Ferdinand"
                    ]),
                    'special_event': None
                }
                audio.speak("Akın başarısız! Rapor hazırlanıyor...", interrupt=True)
            else:
                audio.announce(f"YENİLGİ! {battle.defender_name} karşısında {attacker_casualties} kayıp verdik")
            
            military_system.morale = max(0, military_system.morale - 20)
            
            return BattleResult(
                victory=False,
                attacker_casualties=attacker_casualties,
                defender_casualties=defender_casualties,
                loyalty_change=-15,
                morale_change=-20
            )
    
    def handle_enemy_attack(self, attacker: str, military_system, turn_count: int) -> Optional[Battle]:
        """Düşman saldırısını işle"""
        if turn_count < self.EARLY_GAME_PROTECTION:
            return None  # Erken oyunda saldırı yok
        
        # Düşman ordusu
        enemy_army = Army(
            infantry=random.randint(50, 120),
            cavalry=random.randint(20, 50),
            morale=random.randint(60, 85)
        )
        
        # Savunma ordusu - mevcut birliklerden oluştur
        from game.systems.military import UnitType
        total = military_system.get_total_soldiers()
        defender_army = Army(
            infantry=int(total * 0.6),
            cavalry=int(total * 0.3),
            artillery=int(total * 0.1),
            morale=military_system.morale,
            experience=military_system.experience
        )
        
        self.battle_counter += 1
        battle = Battle(
            battle_id=f"battle_{self.battle_counter}",
            battle_type=BattleType.DEFENSE,
            attacker_name=attacker,
            defender_name="Sizin Eyaletiniz",
            attacker_army=enemy_army,
            defender_army=defender_army,
            phase=BattlePhase.COMBAT,
            turns_remaining=2,
            terrain_bonus=1.3,  # Savunan avantajlı
            is_player_attacker=False
        )
        
        self.active_battles.append(battle)
        
        audio = get_audio_manager()
        audio.announce(f"UYARI! {attacker} saldırıya geçti! Savunmaya hazırlanın!")
        
        return battle
    
    def announce_status(self):
        """Savaş durumunu duyur"""
        audio = get_audio_manager()
        
        if not self.active_battles:
            audio.speak("Aktif savaş yok. Barış zamanı.", interrupt=True)
        else:
            audio.speak(f"{len(self.active_battles)} aktif savaş:", interrupt=True)
            for battle in self.active_battles:
                audio.speak(f"{battle.defender_name}: {battle.get_status_text()}", interrupt=False)
        
        audio.speak(f"Savaş yorgunluğu: yüzde {self.war_weariness}", interrupt=False)
    
    def to_dict(self) -> Dict:
        """Kayıt için dictionary'e dönüştür"""
        return {
            'war_history': self.war_history,
            'peace_treaties': self.peace_treaties,
            'war_weariness': self.war_weariness,
            'battle_counter': self.battle_counter
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'WarfareSystem':
        """Dictionary'den yükle"""
        system = cls()
        system.war_history = data.get('war_history', [])
        system.peace_treaties = data.get('peace_treaties', {})
        system.war_weariness = data.get('war_weariness', 0)
        system.battle_counter = data.get('battle_counter', 0)
        return system
