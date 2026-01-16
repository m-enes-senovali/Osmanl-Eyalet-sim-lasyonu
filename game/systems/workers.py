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
    """İşçi türleri"""
    FARMER = "farmer"           # Çiftçi - yiyecek üretimi
    MINER = "miner"             # Madenci - demir üretimi
    LUMBERJACK = "lumberjack"   # Oduncu - kereste üretimi
    CRAFTSMAN = "craftsman"     # Usta - inşaat hızlandırma
    MERCHANT = "merchant"       # Tüccar - ticaret bonusu
    ENVOY = "envoy"             # Elçi - diplomasi


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
        return int(base * self.skill_level * self.efficiency)
    
    def get_bonus(self) -> Dict[str, float]:
        """Özel bonuslar"""
        bonuses = {}
        
        if self.worker_type == WorkerType.CRAFTSMAN:
            # İnşaat hızı bonusu
            bonuses['construction_speed'] = 0.1 * self.skill_level
        
        elif self.worker_type == WorkerType.MERCHANT:
            # Ticaret bonusu
            bonuses['trade_bonus'] = 0.05 * self.skill_level
        
        elif self.worker_type == WorkerType.ENVOY:
            # Diplomasi bonusu
            bonuses['diplomacy_bonus'] = 0.03 * self.skill_level
        
        return bonuses


# Türk isimleri
TURKISH_NAMES = [
    "Ahmet", "Mehmet", "Mustafa", "Ali", "Hüseyin",
    "Hasan", "Osman", "Yusuf", "İbrahim", "Mahmut",
    "Süleyman", "Halil", "Recep", "Kemal", "Cemal",
    "Fatih", "Serkan", "Emre", "Murat", "Can"
]


class WorkerSystem:
    """İşçi yönetim sistemi"""
    
    def __init__(self):
        self.workers: List[Worker] = []
        self.base_max_workers = 10  # Minimum işçi kapasitesi
        self.max_workers = 10
        self.name_index = 0
        
        # Başlangıç işçileri
        self._initialize_starting_workers()
    
    def update_max_workers_from_population(self, population: int):
        """Nüfusa göre maksimum işçi kapasitesini güncelle"""
        # Her 1000 nüfus = 1 potansiyel işçi
        calculated = population // 1000
        # Minimum 10, maksimum 100
        self.max_workers = max(self.base_max_workers, min(100, calculated))
    
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
        """Yeni işçi kirala"""
        if len(self.workers) >= self.max_workers:
            audio = get_audio_manager()
            audio.speak("Maksimum işçi sayısına ulaşıldı.", interrupt=True)
            return None
        
        worker = Worker(
            name=self._get_next_name(),
            worker_type=worker_type,
            skill_level=skill
        )
        self.workers.append(worker)
        
        # Otomatik görev atama
        self._auto_assign_task(worker)
        
        return worker
    
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
        
        for worker in self.workers:
            worker.turns_on_task += 1
            
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
        
        return {'production': production, 'bonuses': bonuses}
    
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
                    'turns': w.turns_on_task
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
                turns_on_task=w_data.get('turns', 0)
            )
            system.workers.append(worker)
        
        return system
