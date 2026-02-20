# -*- coding: utf-8 -*-
"""
Osmanlı Eyalet Yönetim Simülasyonu - Geçmiş Olaylar Sistemi
Oyun içindeki önemli olayların kaydını tutar ve görüntülenmesini sağlar.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
import time

@dataclass
class HistoryEntry:
    """Geçmiş olay kaydı"""
    turn: int
    year: int
    message: str
    category: str = "general"  # general, economic, military, diplomatic, event
    real_time: float = field(default_factory=time.time)

class HistorySystem:
    """Geçmiş olayları yöneten sistem"""
    
    def __init__(self):
        self.entries: List[HistoryEntry] = []
        self.max_entries = 100  # En son 100 olayı sakla
    
    def add_entry(self, turn: int, year: int, message: str, category: str = "general"):
        """Yeni bir olay kaydı ekle"""
        entry = HistoryEntry(turn, year, message, category)
        self.entries.append(entry)
        
        # Sınırı aşarsa en eskileri sil
        if len(self.entries) > self.max_entries:
            self.entries = self.entries[-self.max_entries:]
            
    def get_entries(self, category: str = None) -> List[HistoryEntry]:
        """Kayıtları getir (isteğe bağlı kategori filtresi)"""
        if category and category != "all":
            return [e for e in self.entries if e.category == category]
        return self.entries
    
    def clear(self):
        """Tüm geçmişi temizle"""
        self.entries = []
        
    def to_dict(self) -> Dict:
        """Sistemi sözlük olarak döndür (kayıt için)"""
        return {
            'entries': [
                {
                    'turn': e.turn,
                    'year': e.year,
                    'message': e.message,
                    'category': e.category,
                    'real_time': e.real_time
                }
                for e in self.entries
            ]
        }
    
    def from_dict(self, data: Dict):
        """Sözlükten sistemi yükle"""
        self.entries = []
        if not data:
            return
            
        for entry_data in data.get('entries', []):
            entry = HistoryEntry(
                turn=entry_data.get('turn', 0),
                year=entry_data.get('year', 1520),
                message=entry_data.get('message', ""),
                category=entry_data.get('category', "general"),
                real_time=entry_data.get('real_time', 0.0)
            )
            self.entries.append(entry)
