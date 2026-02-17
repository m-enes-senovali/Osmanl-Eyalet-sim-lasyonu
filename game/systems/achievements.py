# -*- coding: utf-8 -*-
"""
Osmanlı Eyalet Yönetim Simülasyonu - Başarı Sistemi
"""

import json
import os
from dataclasses import dataclass, field
from typing import Dict, List, Callable, Optional, Any
from enum import Enum
from datetime import datetime
from audio.audio_manager import get_audio_manager
try:
    from game.systems.military import UnitType
except ImportError:
    UnitType = None


class AchievementCategory(Enum):
    """Başarı kategorileri"""
    ECONOMIC = "economic"
    MILITARY = "military"
    DIPLOMATIC = "diplomatic"
    SOCIAL = "social"
    HIDDEN = "hidden"


@dataclass
class Achievement:
    """Başarı tanımı"""
    id: str
    name: str
    description: str
    category: AchievementCategory
    points: int
    condition_key: str  # Condition fonksiyonu için anahtar
    hidden: bool = False
    unlocked: bool = False
    unlock_date: Optional[str] = None
    progress: float = 0.0  # 0-100 arası ilerleme
    target_value: int = 1  # Hedef değeri
    current_value: int = 0


# Başarı tanımları
ACHIEVEMENTS: Dict[str, Achievement] = {}


def _init_achievements():
    """Tüm başarıları tanımla"""
    global ACHIEVEMENTS
    
    achievements_data = [
        # === EKONOMİK BAŞARILAR ===
        Achievement(
            id="treasury_master",
            name="Hazine Efendisi",
            description="100.000 altın biriktir",
            category=AchievementCategory.ECONOMIC,
            points=50,
            condition_key="gold_100k",
            target_value=100000
        ),
        Achievement(
            id="trade_emperor",
            name="Ticaret İmparatoru",
            description="5 aktif ticaret yolu kur",
            category=AchievementCategory.ECONOMIC,
            points=30,
            condition_key="trade_routes_5",
            target_value=5
        ),
        Achievement(
            id="master_builder",
            name="İnşaat Ustası",
            description="50 bina inşa et",
            category=AchievementCategory.ECONOMIC,
            points=40,
            condition_key="buildings_50",
            target_value=50
        ),
        Achievement(
            id="tax_reformer",
            name="Vergi Reformcusu",
            description="%0 isyan ile %20 vergi al",
            category=AchievementCategory.ECONOMIC,
            points=25,
            condition_key="high_tax_no_revolt"
        ),
        Achievement(
            id="wealthy_province",
            name="Zengin Eyalet",
            description="Tek turda 10.000 altın geliri elde et",
            category=AchievementCategory.ECONOMIC,
            points=35,
            condition_key="income_10k",
            target_value=10000
        ),
        Achievement(
            id="worker_army",
            name="İşçi Ordusu",
            description="100 işçi istihdam et",
            category=AchievementCategory.ECONOMIC,
            points=30,
            condition_key="workers_100",
            target_value=100
        ),
        
        # === ASKERİ BAŞARILAR ===
        Achievement(
            id="conqueror",
            name="Fatih",
            description="10 savaş kazan",
            category=AchievementCategory.MILITARY,
            points=50,
            condition_key="victories_10",
            target_value=10
        ),
        Achievement(
            id="sea_lord",
            name="Denizlerin Hakimi",
            description="50 gemi inşa et",
            category=AchievementCategory.MILITARY,
            points=40,
            condition_key="ships_50",
            target_value=50
        ),
        Achievement(
            id="artillery_master",
            name="Topçu Ocağı",
            description="100 top üret",
            category=AchievementCategory.MILITARY,
            points=35,
            condition_key="cannons_100",
            target_value=100
        ),
        Achievement(
            id="janissary_aga",
            name="Yeniçeri Ağası",
            description="10.000 yeniçeri topla",
            category=AchievementCategory.MILITARY,
            points=45,
            condition_key="janissaries_10k",
            target_value=10000
        ),
        Achievement(
            id="defender",
            name="Müdafi",
            description="5 savunma savaşı kazan",
            category=AchievementCategory.MILITARY,
            points=30,
            condition_key="defense_wins_5",
            target_value=5
        ),
        Achievement(
            id="raider",
            name="Akıncı Beyi",
            description="20 başarılı akın yap",
            category=AchievementCategory.MILITARY,
            points=25,
            condition_key="raids_20",
            target_value=20
        ),
        
        # === DİPLOMATİK BAŞARILAR ===
        Achievement(
            id="peacemaker",
            name="Barış Elçisi",
            description="5 ittifak kur",
            category=AchievementCategory.DIPLOMATIC,
            points=30,
            condition_key="alliances_5",
            target_value=5
        ),
        Achievement(
            id="spy_master",
            name="Casusluk Ustası",
            description="20 başarılı casusluk görevi tamamla",
            category=AchievementCategory.DIPLOMATIC,
            points=35,
            condition_key="spy_missions_20",
            target_value=20
        ),
        Achievement(
            id="negotiator",
            name="Müzakereci",
            description="10 başarılı müzakere tamamla",
            category=AchievementCategory.DIPLOMATIC,
            points=30,
            condition_key="negotiations_10",
            target_value=10
        ),
        Achievement(
            id="tribute_collector",
            name="Haraç Toplayıcı",
            description="3 devletten haraç al",
            category=AchievementCategory.DIPLOMATIC,
            points=25,
            condition_key="tributes_3",
            target_value=3
        ),
        
        # === SOSYAL BAŞARILAR ===
        Achievement(
            id="peoples_sultan",
            name="Halkın Sultanı",
            description="100.000 nüfusa ulaş",
            category=AchievementCategory.SOCIAL,
            points=45,
            condition_key="population_100k",
            target_value=100000
        ),
        Achievement(
            id="millet_father",
            name="Millet Babası",
            description="Tüm milletlerde %80+ sadakat sağla",
            category=AchievementCategory.SOCIAL,
            points=40,
            condition_key="all_millets_loyal"
        ),
        Achievement(
            id="religious_leader",
            name="Din Önderi",
            description="10 ulema ata",
            category=AchievementCategory.SOCIAL,
            points=25,
            condition_key="ulema_10",
            target_value=10
        ),
        Achievement(
            id="philanthropist",
            name="Hayırsever",
            description="20 vakıf inşa et",
            category=AchievementCategory.SOCIAL,
            points=30,
            condition_key="vakifs_20",
            target_value=20
        ),
        Achievement(
            id="educator",
            name="Eğitimci",
            description="Eğitim seviyesini %80'e çıkar",
            category=AchievementCategory.SOCIAL,
            points=35,
            condition_key="education_80",
            target_value=80
        ),
        Achievement(
            id="happy_realm",
            name="Mutlu Diyar",
            description="%90 halk mutluluğuna ulaş",
            category=AchievementCategory.SOCIAL,
            points=30,
            condition_key="happiness_90",
            target_value=90
        ),
        
        # === GİZLİ BAŞARILAR ===
        Achievement(
            id="survivor",
            name="Hayatta Kalan",
            description="???",
            category=AchievementCategory.HIDDEN,
            points=50,
            condition_key="turns_100",
            hidden=True,
            target_value=100
        ),
        Achievement(
            id="pacifist",
            name="Barışçı",
            description="???",
            category=AchievementCategory.HIDDEN,
            points=40,
            condition_key="no_war_50_turns",
            hidden=True,
            target_value=50
        ),
        Achievement(
            id="generous",
            name="Cömert",
            description="???",
            category=AchievementCategory.HIDDEN,
            points=30,
            condition_key="no_tax_10_turns",
            hidden=True,
            target_value=10
        ),
        Achievement(
            id="iron_fist",
            name="Demir Yumruk",
            description="???",
            category=AchievementCategory.HIDDEN,
            points=35,
            condition_key="crush_5_rebellions",
            hidden=True,
            target_value=5
        ),
    ]
    
    for ach in achievements_data:
        ACHIEVEMENTS[ach.id] = ach


# Başarıları yükle
_init_achievements()


class AchievementSystem:
    """Başarı yönetim sistemi"""
    
    SAVE_FILE = "achievements.json"
    
    def __init__(self):
        self.audio = get_audio_manager()
        self.achievements: Dict[str, Achievement] = {}
        self.total_points = 0
        self.unlocked_count = 0
        
        # İstatistikler (başarı kontrolü için)
        self.stats = {
            'total_gold_earned': 0,
            'buildings_built': 0,
            'battles_won': 0,
            'ships_built': 0,
            'cannons_produced': 0,
            'spy_missions_completed': 0,
            'alliances_formed': 0,
            'negotiations_completed': 0,
            'raids_completed': 0,
            'rebellions_crushed': 0,
            'defense_victories': 0,
            'turns_played': 0,
            'turns_without_war': 0,
            'turns_without_tax': 0,
        }
        
        self._init_achievements()
        self._load_progress()
    
    def _init_achievements(self):
        """Başarıları kopyala (global değişmemesi için)"""
        import copy
        for ach_id, ach in ACHIEVEMENTS.items():
            self.achievements[ach_id] = copy.copy(ach)
    
    def _load_progress(self):
        """Kaydedilmiş ilerlemeyi yükle"""
        save_path = self._get_save_path()
        if os.path.exists(save_path):
            try:
                with open(save_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # İstatistikleri yükle
                self.stats.update(data.get('stats', {}))
                
                # Başarı durumlarını yükle
                for ach_id, ach_data in data.get('achievements', {}).items():
                    if ach_id in self.achievements:
                        ach = self.achievements[ach_id]
                        ach.unlocked = ach_data.get('unlocked', False)
                        ach.unlock_date = ach_data.get('unlock_date')
                        ach.progress = ach_data.get('progress', 0)
                        ach.current_value = ach_data.get('current_value', 0)
                
                self._update_counts()
                
            except Exception as e:
                print(f"Başarı yükleme hatası: {e}")
    
    def _get_save_path(self) -> str:
        """Kayıt dosyası yolunu al"""
        save_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'save')
        os.makedirs(save_dir, exist_ok=True)
        return os.path.join(save_dir, self.SAVE_FILE)
    
    def save_progress(self):
        """İlerlemeyi kaydet"""
        save_path = self._get_save_path()
        
        data = {
            'stats': self.stats,
            'achievements': {}
        }
        
        for ach_id, ach in self.achievements.items():
            data['achievements'][ach_id] = {
                'unlocked': ach.unlocked,
                'unlock_date': ach.unlock_date,
                'progress': ach.progress,
                'current_value': ach.current_value
            }
        
        try:
            with open(save_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Başarı kayıt hatası: {e}")
    
    def _update_counts(self):
        """Toplam puan ve açılan sayısını güncelle"""
        self.total_points = 0
        self.unlocked_count = 0
        
        for ach in self.achievements.values():
            if ach.unlocked:
                self.total_points += ach.points
                self.unlocked_count += 1
    
    def check_achievements(self, game_manager) -> List[Achievement]:
        """
        Tüm başarıları kontrol et.
        Yeni açılanları döndür.
        """
        newly_unlocked = []
        
        for ach in self.achievements.values():
            if ach.unlocked:
                continue
            
            # Koşulu kontrol et
            result = self._check_condition(ach, game_manager)
            
            if result:
                ach.unlocked = True
                ach.unlock_date = datetime.now().strftime("%Y-%m-%d %H:%M")
                ach.progress = 100.0
                ach.current_value = ach.target_value
                newly_unlocked.append(ach)
            else:
                # İlerlemeyi güncelle
                progress = self._get_progress(ach, game_manager)
                ach.progress = min(100.0, progress)
                ach.current_value = self._get_current_value(ach, game_manager)
        
        if newly_unlocked:
            self._update_counts()
            self.save_progress()
            
            # Duyuru
            for ach in newly_unlocked:
                self._announce_unlock(ach)
        
        return newly_unlocked
    
    def _check_condition(self, ach: Achievement, gm) -> bool:
        """Başarı koşulunu kontrol et — tüm erişimler güvenli"""
        key = ach.condition_key
        
        try:
            # Ekonomik
            if key == "gold_100k":
                return gm.economy.resources.gold >= 100000
            elif key == "trade_routes_5":
                return len(getattr(gm.economy, 'active_trade_routes', [])) >= 5
            elif key == "buildings_50":
                return self.stats['buildings_built'] >= 50
            elif key == "high_tax_no_revolt":
                tax_rate = getattr(gm.economy, 'tax_rate', 0)
                happiness = getattr(gm.population, 'happiness', 0)
                return tax_rate >= 0.20 and happiness >= 70
            elif key == "income_10k":
                # Gelir hesapla
                try:
                    income = gm.economy.calculate_tax_income() + gm.economy.calculate_trade_income()
                    return income >= 10000
                except Exception:
                    return False
            elif key == "workers_100":
                return len(gm.workers.workers) >= 100
            
            # Askeri
            elif key == "victories_10":
                return self.stats['battles_won'] >= 10
            elif key == "ships_50":
                return len(getattr(gm.naval, 'ships', [])) >= 50
            elif key == "cannons_100":
                return len(getattr(gm.artillery, 'cannons', [])) >= 100
            elif key == "janissaries_10k":
                if UnitType:
                    return gm.military.units.get(UnitType.YENICHERI, 0) >= 10000
                return False
            elif key == "defense_wins_5":
                return self.stats.get('defense_victories', 0) >= 5
            elif key == "raids_20":
                return self.stats['raids_completed'] >= 20
            
            # Diplomatik
            elif key == "alliances_5":
                alliances = len(getattr(gm.diplomacy, 'marriage_alliances', []))
                return alliances >= 5
            elif key == "spy_missions_20":
                return getattr(gm.espionage, 'successful_missions', 0) >= 20
            elif key == "negotiations_10":
                return self.stats['negotiations_completed'] >= 10
            elif key == "tributes_3":
                vassals = len(getattr(gm.diplomacy, 'vassals', []))
                return vassals >= 3
            
            # Sosyal
            elif key == "population_100k":
                return gm.population.population.total >= 100000
            elif key == "all_millets_loyal":
                for state in gm.religion.millet_states.values():
                    if state.get('loyalty', 0) < 80:
                        return False
                return True
            elif key == "ulema_10":
                return len(gm.religion.ulema) >= 10
            elif key == "vakifs_20":
                return len(gm.religion.vakifs) >= 20
            elif key == "education_80":
                return gm.religion.education_level >= 80
            elif key == "happiness_90":
                return gm.population.happiness >= 90
            
            # Gizli
            elif key == "turns_100":
                return self.stats['turns_played'] >= 100
            elif key == "no_war_50_turns":
                return self.stats['turns_without_war'] >= 50
            elif key == "no_tax_10_turns":
                return self.stats['turns_without_tax'] >= 10
            elif key == "crush_5_rebellions":
                return self.stats['rebellions_crushed'] >= 5
        except Exception:
            pass
        
        return False
    
    def _get_progress(self, ach: Achievement, gm) -> float:
        """Başarı ilerlemesini hesapla (%)"""
        if ach.target_value <= 1:
            return 0.0
        
        current = self._get_current_value(ach, gm)
        return (current / ach.target_value) * 100.0
    
    def _get_current_value(self, ach: Achievement, gm) -> int:
        """Mevcut değeri al — tüm başarılar için"""
        key = ach.condition_key
        
        try:
            # Ekonomik
            if key == "gold_100k":
                return int(gm.economy.resources.gold)
            elif key == "trade_routes_5":
                return len(getattr(gm.economy, 'active_trade_routes', []))
            elif key == "buildings_50":
                return self.stats['buildings_built']
            elif key == "income_10k":
                try:
                    return int(gm.economy.calculate_tax_income() + gm.economy.calculate_trade_income())
                except Exception:
                    return 0
            elif key == "workers_100":
                return len(gm.workers.workers)
            
            # Askeri
            elif key == "victories_10":
                return self.stats['battles_won']
            elif key == "ships_50":
                return len(getattr(gm.naval, 'ships', []))
            elif key == "cannons_100":
                return len(getattr(gm.artillery, 'cannons', []))
            elif key == "janissaries_10k":
                if UnitType:
                    return gm.military.units.get(UnitType.YENICHERI, 0)
                return 0
            elif key == "defense_wins_5":
                return self.stats.get('defense_victories', 0)
            elif key == "raids_20":
                return self.stats['raids_completed']
            
            # Diplomatik
            elif key == "alliances_5":
                return len(getattr(gm.diplomacy, 'marriage_alliances', []))
            elif key == "spy_missions_20":
                return getattr(gm.espionage, 'successful_missions', 0)
            elif key == "negotiations_10":
                return self.stats['negotiations_completed']
            elif key == "tributes_3":
                return len(getattr(gm.diplomacy, 'vassals', []))
            
            # Sosyal
            elif key == "population_100k":
                return gm.population.population.total
            elif key == "ulema_10":
                return len(gm.religion.ulema)
            elif key == "vakifs_20":
                return len(gm.religion.vakifs)
            elif key == "education_80":
                return int(gm.religion.education_level)
            elif key == "happiness_90":
                return int(gm.population.happiness)
            
            # Gizli
            elif key == "turns_100":
                return self.stats['turns_played']
            elif key == "no_war_50_turns":
                return self.stats['turns_without_war']
            elif key == "no_tax_10_turns":
                return self.stats['turns_without_tax']
            elif key == "crush_5_rebellions":
                return self.stats['rebellions_crushed']
        except Exception:
            pass
        
        return 0
    
    def _announce_unlock(self, ach: Achievement):
        """Başarı açıldığını duyur"""
        if ach.hidden:
            self.audio.speak(f"Gizli başarı açıldı: {ach.name}!", interrupt=True)
        else:
            self.audio.speak(f"Başarı açıldı: {ach.name}! {ach.points} puan", interrupt=True)
    
    def increment_stat(self, stat_name: str, amount: int = 1):
        """İstatistik artır"""
        if stat_name in self.stats:
            self.stats[stat_name] += amount
    
    def reset_stat(self, stat_name: str):
        """İstatistik sıfırla (örn: turns_without_war)"""
        if stat_name in self.stats:
            self.stats[stat_name] = 0
    
    def on_turn_end(self, game_manager):
        """Tur sonu güncellemeleri"""
        self.stats['turns_played'] += 1
        
        # Savaşsız tur kontrolü
        try:
            at_war = len(game_manager.warfare.active_battles) > 0
            if not at_war:
                self.stats['turns_without_war'] += 1
            else:
                self.stats['turns_without_war'] = 0
        except Exception:
            self.stats['turns_without_war'] += 1
        
        # Vergisiz tur kontrolü
        try:
            if game_manager.economy.tax_rate == 0:
                self.stats['turns_without_tax'] += 1
            else:
                self.stats['turns_without_tax'] = 0
        except Exception:
            pass
        
        # Başarıları kontrol et
        self.check_achievements(game_manager)
    
    def get_achievements_by_category(self, category: AchievementCategory) -> List[Achievement]:
        """Kategoriye göre başarıları al"""
        return [a for a in self.achievements.values() if a.category == category]
    
    def get_unlocked_achievements(self) -> List[Achievement]:
        """Açılmış başarıları al"""
        return [a for a in self.achievements.values() if a.unlocked]
    
    def get_locked_achievements(self, include_hidden: bool = False) -> List[Achievement]:
        """Kilitli başarıları al"""
        result = []
        for a in self.achievements.values():
            if not a.unlocked:
                if a.hidden and not include_hidden:
                    continue
                result.append(a)
        return result
    
    def get_completion_percentage(self) -> float:
        """Tamamlanma yüzdesini al"""
        total = len(self.achievements)
        if total == 0:
            return 0.0
        return (self.unlocked_count / total) * 100.0
    
    def to_dict(self) -> Dict:
        """Kayıt için dict'e dönüştür"""
        return {
            'stats': self.stats,
            'achievements': {
                ach_id: {
                    'unlocked': ach.unlocked,
                    'unlock_date': ach.unlock_date,
                    'progress': ach.progress,
                    'current_value': ach.current_value
                }
                for ach_id, ach in self.achievements.items()
            }
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'AchievementSystem':
        """Dict'ten yükle"""
        system = cls()
        system.stats.update(data.get('stats', {}))
        
        for ach_id, ach_data in data.get('achievements', {}).items():
            if ach_id in system.achievements:
                ach = system.achievements[ach_id]
                ach.unlocked = ach_data.get('unlocked', False)
                ach.unlock_date = ach_data.get('unlock_date')
                ach.progress = ach_data.get('progress', 0)
                ach.current_value = ach_data.get('current_value', 0)
        
        system._update_counts()
        return system


# Global instance
_achievement_system: Optional[AchievementSystem] = None


def get_achievement_system() -> AchievementSystem:
    """Global AchievementSystem instance"""
    global _achievement_system
    if _achievement_system is None:
        _achievement_system = AchievementSystem()
    return _achievement_system
