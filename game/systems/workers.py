# -*- coding: utf-8 -*-
"""
Osmanlı Eyalet Yönetim Simülasyonu - İşçi Sistemi
NPC işçiler ve görev atama.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional
from enum import Enum
from audio.audio_manager import get_audio_manager


class WorkerType(Enum):
    """İşçi türleri — 16. yy Osmanlı zanaat sınıfları"""
    FARMER = "farmer"           # Çiftçi (reaya) — yevmiye: 3-5 akçe/gün
    MINER = "miner"             # Madenci — yevmiye: 5-8 akçe/gün
    LUMBERJACK = "lumberjack"   # Baltacı (oduncu) — yevmiye: 4-6 akçe/gün
    CRAFTSMAN = "craftsman"     # Usta (taşçı/neccar) — yevmiye: 10-20 akçe/gün
    MERCHANT = "merchant"       # Tüccar (bezirgan) — ticaret bonusu
    ENVOY = "envoy"             # Çavuş/Elçi — diplomasi


class TaskType(Enum):
    """Görev türleri"""
    IDLE = "idle"                   # Boşta
    FARMING = "farming"             # Tarım
    MINING = "mining"               # Madencilik
    LOGGING = "logging"             # Kereste kesimi
    CONSTRUCTION = "construction"   # İnşaat
    TRADING = "trading"             # Ticaret
    DIPLOMACY = "diplomacy"         # Diplomasi görevi


@dataclass
class Worker:
    """İşçi NPC"""
    name: str
    worker_type: WorkerType
    skill_level: int = 1  # 1-5
    current_task: TaskType = TaskType.IDLE
    efficiency: float = 1.0  # Verimlilik çarpanı
    turns_on_task: int = 0
    experience: int = 0  # 0-100 deneyim puanı
    
    # Seviye için gereken deneyim eşikleri
    LEVEL_THRESHOLDS = [0, 20, 40, 60, 80]  # Level 1, 2, 3, 4, 5
    
    def gain_experience(self, amount: int = 1) -> bool:
        """Deneyim kazan, seviye atladıysa True döndür"""
        if self.current_task == TaskType.IDLE:
            return False  # Boşta deneyim kazanılmaz
        
        old_level = self.skill_level
        self.experience = min(100, self.experience + amount)
        
        # Seviye kontrolü
        for level, threshold in enumerate(self.LEVEL_THRESHOLDS):
            if self.experience >= threshold:
                self.skill_level = max(self.skill_level, level + 1)
        
        self.skill_level = min(5, self.skill_level)  # Max 5
        return self.skill_level > old_level
    
    def get_experience_progress(self) -> str:
        """Sonraki seviyeye ilerleme yüzdesi"""
        if self.skill_level >= 5:
            return "MAX"
        next_threshold = self.LEVEL_THRESHOLDS[self.skill_level]
        current = self.experience
        if self.skill_level > 1:
            prev_threshold = self.LEVEL_THRESHOLDS[self.skill_level - 1]
            current -= prev_threshold
            next_threshold -= prev_threshold
        return f"{int((current / next_threshold) * 100)}%"
    
    def get_production(self) -> int:
        """Tur başına üretim miktarı"""
        base_production = {
            WorkerType.FARMER: 50,
            WorkerType.MINER: 30,
            WorkerType.LUMBERJACK: 40,
            WorkerType.CRAFTSMAN: 0,  # Özel etki
            WorkerType.MERCHANT: 0,   # Özel etki
            WorkerType.ENVOY: 0       # Özel etki
        }
        base = base_production.get(self.worker_type, 0)
        # Deneyim bonusu: her 20 deneyim %5 ekstra
        exp_bonus = 1.0 + (self.experience / 400)  # Max %25 bonus
        return int(base * self.skill_level * self.efficiency * exp_bonus)
    
    def get_bonus(self) -> Dict[str, float]:
        """Özel bonuslar"""
        bonuses = {}
        
        # Deneyim çarpanı
        exp_multiplier = 1.0 + (self.experience / 200)  # Max %50 bonus
        
        if self.worker_type == WorkerType.CRAFTSMAN:
            # İnşaat hızı bonusu
            bonuses['construction_speed'] = 0.1 * self.skill_level * exp_multiplier
        
        elif self.worker_type == WorkerType.MERCHANT:
            # Ticaret bonusu
            bonuses['trade_bonus'] = 0.05 * self.skill_level * exp_multiplier
        
        elif self.worker_type == WorkerType.ENVOY:
            # Diplomasi bonusu
            bonuses['diplomacy_bonus'] = 0.03 * self.skill_level * exp_multiplier
        
        return bonuses


# ═══════════════════════════════════════════════════════════════
# 16. YÜZYIL OSMANLI İSİMLERİ
# Kaynak: Tahrir defterleri, Şer'iyye sicilleri, vakfiyeler
# ═══════════════════════════════════════════════════════════════

# Erkek isimleri — Kırsal/Türkmen (reaya köylüler)
_MALE_RURAL_TURKIC = [
    "Satılmış", "Dursun", "Durmuş", "Tanrıverdi", "Veli",
    "Budak", "Korkut", "Turgut", "Timurtaş", "Gündüz",
    "Umur", "Karaca", "Doğan", "Bayram", "Hızır",
]

# Erkek isimleri — Şehirli/İslami (medreseli, esnaf, bürokrat)
_MALE_URBAN_ISLAMIC = [
    "Mehmed", "Ahmed", "Mustafa", "Süleyman", "İbrahim",
    "Yusuf", "Halil", "Mahmud", "Abdülkerim", "Abdurrahman",
    "Kasım", "Selim", "Haydar", "Cafer", "Hamza",
]

# Erkek isimleri — Devşirme kökenli (saray ve ordu)
_MALE_DEVSHIRME = [
    "Hüsrev", "Rüstem", "Ferhad", "Lütfi", "Sinan",
    "İskender", "Davud", "Piyale", "Sokullu", "Pertev",
    "Kara", "Hadım", "Gedik", "Özdemir", "Nasuh",
]

# Tüm erkek isimleri (birleşik havuz)
TURKISH_MALE_NAMES = _MALE_RURAL_TURKIC + _MALE_URBAN_ISLAMIC + _MALE_DEVSHIRME

# Kadın isimleri — Saray/Farsça kökenli
_FEMALE_PALACE = [
    "Hürrem", "Mahidevran", "Nurbanu", "Gülbahar", "Mihrimah",
    "Gevherhan", "Şahhuban", "Nilüfer", "Gülruh", "Hümaşah",
    "Raziye", "Dilşad", "Gülşen", "Safiye", "Hafsa",
]

# Kadın isimleri — Reaya (halk) kadınları
_FEMALE_REAYA = [
    "Fatma", "Ayşe", "Emine", "Hatice", "Havva",
    "Hacer", "Şerife", "Hanife", "Zeliha", "Rukiye",
    "Halime", "Saliha", "Meryem", "Esma", "Ümmügülsüm",
]

# Tüm kadın isimleri (birleşik havuz)
TURKISH_FEMALE_NAMES = _FEMALE_PALACE + _FEMALE_REAYA

# Geriye uyumluluk için
TURKISH_NAMES = TURKISH_MALE_NAMES


class WorkerSystem:
    """İşçi yönetim sistemi"""
    
    def __init__(self):
        self.workers: List[Worker] = []
        self.name_index = 0
        
        # Başlangıç işçileri
        self._initialize_starting_workers()
    
    def _initialize_starting_workers(self):
        """Başlangıç işçilerini oluştur"""
        # 4 çiftçi (yiyecek üretimi için)
        for _ in range(4):
            self.hire_worker(WorkerType.FARMER)
        
        # 2 madenci (demir üretimi için)
        for _ in range(2):
            self.hire_worker(WorkerType.MINER)
        
        # 2 oduncu (kereste üretimi için)
        for _ in range(2):
            self.hire_worker(WorkerType.LUMBERJACK)
        
        # 1 usta (inşaat hızlandırma)
        self.hire_worker(WorkerType.CRAFTSMAN)
        
        # 1 tüccar (ticaret bonusu)
        self.hire_worker(WorkerType.MERCHANT)
    
    def _get_next_name(self) -> str:
        """Sonraki ismi al"""
        name = TURKISH_NAMES[self.name_index % len(TURKISH_NAMES)]
        self.name_index += 1
        return name
    
    def hire_worker(self, worker_type: WorkerType, skill: int = 1) -> Optional[Worker]:
        """Yeni işçi kirala (sınır yok)"""
        
        worker = Worker(
            name=self._get_next_name(),
            worker_type=worker_type,
            skill_level=skill
        )
        self.workers.append(worker)
        
        # Otomatik görev atama
        self._auto_assign_task(worker)
        
        return worker
    
    def hire_workers_bulk(self, worker_type: WorkerType, count: int, skill: int = 1) -> List[Worker]:
        """Toplu işçi kirala — N adet aynı türden işçi"""
        hired = []
        for _ in range(count):
            worker = self.hire_worker(worker_type, skill)
            if worker:
                hired.append(worker)
        return hired
    
    def _auto_assign_task(self, worker: Worker):
        """Otomatik görev atama"""
        task_map = {
            WorkerType.FARMER: TaskType.FARMING,
            WorkerType.MINER: TaskType.MINING,
            WorkerType.LUMBERJACK: TaskType.LOGGING,
            WorkerType.CRAFTSMAN: TaskType.CONSTRUCTION,
            WorkerType.MERCHANT: TaskType.TRADING,
            WorkerType.ENVOY: TaskType.DIPLOMACY
        }
        worker.current_task = task_map.get(worker.worker_type, TaskType.IDLE)
    
    def assign_task(self, worker_index: int, task: TaskType) -> bool:
        """Görev ata"""
        if worker_index >= len(self.workers):
            return False
        
        worker = self.workers[worker_index]
        worker.current_task = task
        worker.turns_on_task = 0
        
        audio = get_audio_manager()
        task_names = {
            TaskType.IDLE: "Boşta",
            TaskType.FARMING: "Tarım",
            TaskType.MINING: "Madencilik",
            TaskType.LOGGING: "Kereste kesimi",
            TaskType.CONSTRUCTION: "İnşaat",
            TaskType.TRADING: "Ticaret",
            TaskType.DIPLOMACY: "Diplomasi"
        }
        audio.speak(f"{worker.name} şimdi {task_names[task]} görevinde.", interrupt=True)
        return True
    
    def fire_worker(self, worker_index: int) -> bool:
        """İşçiyi işten çıkar"""
        if worker_index >= len(self.workers):
            return False
        
        worker = self.workers.pop(worker_index)
        audio = get_audio_manager()
        audio.speak(f"{worker.name} işten çıkarıldı.", interrupt=True)
        return True
    
    def process_turn(self) -> Dict[str, int]:
        """Tur sonunda işçileri işle"""
        production = {
            'food': 0,
            'wood': 0,
            'iron': 0
        }
        bonuses = {
            'construction_speed': 0.0,
            'trade_bonus': 0.0,
            'diplomacy_bonus': 0.0
        }
        level_ups = []
        
        audio = get_audio_manager()
        
        for worker in self.workers:
            worker.turns_on_task += 1
            
            # Deneyim kazan (çalışan işçiler)
            if worker.current_task != TaskType.IDLE:
                leveled_up = worker.gain_experience(1)
                if leveled_up:
                    level_ups.append((worker.name, worker.skill_level))
            
            # Uzun süreli görev bonusu
            if worker.turns_on_task > 5:
                worker.efficiency = min(1.5, 1.0 + worker.turns_on_task * 0.05)
            
            # Üretim
            if worker.current_task == TaskType.FARMING:
                production['food'] += worker.get_production()
            elif worker.current_task == TaskType.MINING:
                production['iron'] += worker.get_production()
            elif worker.current_task == TaskType.LOGGING:
                production['wood'] += worker.get_production()
            
            # Bonuslar
            for key, value in worker.get_bonus().items():
                if key in bonuses:
                    bonuses[key] += value
        
        # Seviye atlayan işçileri duyur
        for name, level in level_ups:
            audio.speak(f"{name} seviye {level} oldu!", interrupt=False)
        
        return {'production': production, 'bonuses': bonuses, 'level_ups': level_ups}
    
    def get_worker_count_by_type(self) -> Dict[WorkerType, int]:
        """Tür bazında işçi sayısı"""
        counts = {}
        for worker in self.workers:
            counts[worker.worker_type] = counts.get(worker.worker_type, 0) + 1
        return counts
    
    def get_workers_by_task(self, task: TaskType) -> int:
        """Belirli bir görevdeki işçi sayısı"""
        return sum(1 for w in self.workers if w.current_task == task)
    
    def get_idle_count(self) -> int:
        """Boştaki işçi sayısı"""
        return self.get_workers_by_task(TaskType.IDLE)
    
    def assign_idle_to_task(self, task: TaskType, count: int) -> int:
        """Boştaki işçileri göreve ata, atanan sayıyı döndür"""
        assigned = 0
        for worker in self.workers:
            if worker.current_task == TaskType.IDLE and assigned < count:
                worker.current_task = task
                worker.turns_on_task = 0
                assigned += 1
        return assigned
    
    def remove_from_task(self, task: TaskType, count: int) -> int:
        """Görevden işçi çek, çekilen sayıyı döndür"""
        removed = 0
        for worker in self.workers:
            if worker.current_task == task and removed < count:
                worker.current_task = TaskType.IDLE
                worker.turns_on_task = 0
                removed += 1
        return removed
    
    def announce_workers(self):
        """İşçileri duyur"""
        audio = get_audio_manager()
        audio.speak(f"Toplam {len(self.workers)} işçi:", interrupt=True)
        
        task_names = {
            TaskType.IDLE: "Boşta",
            TaskType.FARMING: "Tarım",
            TaskType.MINING: "Madencilik",
            TaskType.LOGGING: "Kereste",
            TaskType.CONSTRUCTION: "İnşaat",
            TaskType.TRADING: "Ticaret",
            TaskType.DIPLOMACY: "Diplomasi"
        }
        
        type_names = {
            WorkerType.FARMER: "Çiftçi",
            WorkerType.MINER: "Madenci",
            WorkerType.LUMBERJACK: "Oduncu",
            WorkerType.CRAFTSMAN: "Usta",
            WorkerType.MERCHANT: "Tüccar",
            WorkerType.ENVOY: "Elçi"
        }
        
        for i, worker in enumerate(self.workers):
            type_name = type_names.get(worker.worker_type, "İşçi")
            task_name = task_names.get(worker.current_task, "Bilinmiyor")
            audio.speak(
                f"{i+1}. {worker.name}, {type_name}, Lv{worker.skill_level}, {task_name}",
                interrupt=False
            )
    
    def get_hire_cost(self, worker_type: WorkerType) -> int:
        """İşe alma maliyeti"""
        costs = {
            WorkerType.FARMER: 100,
            WorkerType.MINER: 150,
            WorkerType.LUMBERJACK: 120,
            WorkerType.CRAFTSMAN: 300,
            WorkerType.MERCHANT: 250,
            WorkerType.ENVOY: 400
        }
        return costs.get(worker_type, 100)
    
    def to_dict(self) -> Dict:
        """Kayıt için dictionary'e dönüştür"""
        return {
            'workers': [
                {
                    'name': w.name,
                    'type': w.worker_type.value,
                    'skill': w.skill_level,
                    'task': w.current_task.value,
                    'efficiency': w.efficiency,
                    'turns': w.turns_on_task,
                    'experience': w.experience
                }
                for w in self.workers
            ],
            'name_index': self.name_index
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'WorkerSystem':
        """Dictionary'den yükle"""
        system = cls()
        system.workers = []  # Başlangıç işçilerini temizle
        system.name_index = data.get('name_index', 0)
        
        for w_data in data.get('workers', []):
            worker = Worker(
                name=w_data['name'],
                worker_type=WorkerType(w_data['type']),
                skill_level=w_data['skill'],
                current_task=TaskType(w_data['task']),
                efficiency=w_data.get('efficiency', 1.0),
                turns_on_task=w_data.get('turns', 0),
                experience=w_data.get('experience', 0)
            )
            system.workers.append(worker)
        
        return system
