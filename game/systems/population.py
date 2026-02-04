# -*- coding: utf-8 -*-
"""
Osmanlı Eyalet Yönetim Simülasyonu - Nüfus/Halk Sistemi
"""

from dataclasses import dataclass
from typing import Dict
from audio.audio_manager import get_audio_manager


@dataclass
class PopulationGroups:
    """Nüfus grupları"""
    farmers: int = 6000      # Çiftçiler (reaya)
    merchants: int = 2000    # Tüccarlar
    artisans: int = 1500     # Zanaatkarlar (esnaf)
    soldiers: int = 500      # Asker aileleri
    scholars: int = 200      # Ulema (din adamları, müderrisler)
    
    @property
    def total(self) -> int:
        return self.farmers + self.merchants + self.artisans + self.soldiers + self.scholars
    
    def to_dict(self) -> Dict:
        return {
            'farmers': self.farmers,
            'merchants': self.merchants,
            'artisans': self.artisans,
            'soldiers': self.soldiers,
            'scholars': self.scholars
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'PopulationGroups':
        # Eski kayıtlarla uyumluluk
        data.setdefault('scholars', 200)
        return cls(**data)


class MigrationPolicy:
    """Göç politikaları - Osmanlı İskan politikası"""
    OPEN = 'open'          # Açık kapı - herkes hoşgeldin
    SELECTIVE = 'selective' # Seçici - sadece zanaatkarlar/tüccarlar
    RESTRICTED = 'restricted' # Kısıtlı - sadece yüksek nüfus bölgelerinden
    CLOSED = 'closed'      # Kapalı - göçe izin yok
    
    POLICY_EFFECTS = {
        'open': {'growth_bonus': 0.02, 'happiness_penalty': 0, 'unrest_mod': 5},
        'selective': {'growth_bonus': 0.01, 'happiness_penalty': 0, 'unrest_mod': 0},
        'restricted': {'growth_bonus': 0.005, 'happiness_penalty': 0, 'unrest_mod': -5},
        'closed': {'growth_bonus': 0.0, 'happiness_penalty': -5, 'unrest_mod': -10}
    }


class PopulationSystem:
    """Nüfus ve halk yönetim sistemi"""
    
    def __init__(self):
        self.population = PopulationGroups()
        self.happiness = 70        # Memnuniyet 0-100
        self.health = 80           # Sağlık durumu 0-100
        self.food_consumption = 0  # Hesaplanacak
        
        # Göç politikası
        self.migration_policy = MigrationPolicy.SELECTIVE
        
        # Eğitim sistemi
        self.education_level = 1  # 1-5 (1=temel medrese, 5=yüksek ilim)
        
        # Etkenler
        self.happiness_modifiers = {}  # {source: value}
        self.growth_rate = 0.02        # %2 doğal artış
        
        # İsyan durumu
        self.unrest = 0  # 0-100, 80+ isyan riski
        self.active_revolt = False
    
    def set_migration_policy(self, policy: str) -> bool:
        """Göç politikasını değiştir"""
        if policy in MigrationPolicy.POLICY_EFFECTS:
            self.migration_policy = policy
            audio = get_audio_manager()
            policy_names = {
                'open': 'Açık Kapı',
                'selective': 'Seçici',
                'restricted': 'Kısıtlı',
                'closed': 'Kapalı'
            }
            audio.speak(f"Göç politikası değiştirildi: {policy_names[policy]}", interrupt=True)
            return True
        return False
    
    def convert_profession(self, from_group: str, to_group: str, count: int) -> bool:
        """
        Meslek dönüşümü - Osmanlı lonca sistemi
        Örn: Çiftçi -> Zanaatkar (şehirlileşme)
        """
        audio = get_audio_manager()
        
        # Kaynak grubunda yeterli nüfus var mı?
        current = getattr(self.population, from_group, 0)
        if current < count + 100:  # Minimum 100 kalsın
            audio.speak(f"Yeterli {from_group} yok. En az 100 kalmalı.", interrupt=True)
            return False
        
        # Dönüşüm maliyeti: eğitim seviyesine göre
        education_cost = (5 - self.education_level) * 50  # Düşük eğitim = yüksek maliyet
        
        # Uygula
        setattr(self.population, from_group, current - count)
        target = getattr(self.population, to_group, 0)
        setattr(self.population, to_group, target + count)
        
        group_names = {
            'farmers': 'Çiftçi', 'merchants': 'Tüccar',
            'artisans': 'Zanaatkar', 'soldiers': 'Asker', 'scholars': 'Ulema'
        }
        
        audio.speak(
            f"{count} kişi {group_names[from_group]}'den {group_names[to_group]}'a dönüştü.",
            interrupt=True
        )
        return True
    
    def get_migration_effect(self) -> dict:
        """Aktif göç politikasının etkilerini al"""
        return MigrationPolicy.POLICY_EFFECTS.get(
            self.migration_policy,
            MigrationPolicy.POLICY_EFFECTS['selective']
        )
    
    def calculate_food_consumption(self) -> int:
        """Yiyecek tüketimini hesapla"""
        # Her kişi 0.02 yiyecek tüketir (dengelenmiş - eskiden 0.05)
        # Örnek: 10000 nüfus = 200 zahire/tur tüketim
        return int(self.population.total * 0.02)
    
    def calculate_happiness(self, tax_rate: float, has_mosque: bool, 
                           has_hospital: bool, security: int) -> int:
        """
        Memnuniyeti hesapla
        
        Etkileyen faktörler:
        - Vergi oranı: %15 normal, üstü düşürür
        - Cami: +10
        - Hastane: +10
        - Güvenlik (askeri güç): 0-20 arası bonus
        """
        base = 60
        
        # Vergi etkisi
        tax_effect = int((0.15 - tax_rate) * 100)  # %15'in altı artı
        
        # Bina etkileri
        mosque_bonus = 10 if has_mosque else 0
        hospital_bonus = 10 if has_hospital else 0
        
        # Güvenlik bonusu
        security_bonus = min(20, security // 50)
        
        # Toplam
        total = base + tax_effect + mosque_bonus + hospital_bonus + security_bonus
        
        # Modifiers
        for source, value in self.happiness_modifiers.items():
            total += value
        
        # Sınırla
        return max(0, min(100, total))
    
    def calculate_unrest(self) -> int:
        """İsyan riskini hesapla"""
        # Düşük memnuniyet = yüksek huzursuzluk
        unrest = (100 - self.happiness) * 0.8
        
        # Sağlık etkisi
        if self.health < 50:
            unrest += 20
        
        # Açlık (yiyecek yetersiz ise sonradan kontrol edilecek)
        
        return max(0, min(100, int(unrest)))
    
    def process_turn(self, food_available: int, tax_rate: float,
                    has_mosque: bool, has_hospital: bool, military_power: int,
                    population_capacity: int = 50000):
        """Tur sonunda nüfusu güncelle"""
        audio = get_audio_manager()
        
        # Yiyecek tüketimi
        self.food_consumption = self.calculate_food_consumption()
        food_shortage = food_available < self.food_consumption
        
        # Memnuniyet hesapla
        self.happiness = self.calculate_happiness(
            tax_rate, has_mosque, has_hospital, military_power
        )
        
        # Yiyecek yetersizliği
        if food_shortage:
            self.happiness -= 30
            self.health -= 10
            self.happiness_modifiers['food_shortage'] = -30
            audio.announce("Uyarı: Yiyecek yetersiz! Halk aç!")
        else:
            self.happiness_modifiers.pop('food_shortage', None)
        
        # Sağlık düzeltme
        if has_hospital and self.health < 100:
            self.health = min(100, self.health + 5)
        
        # Nüfus artışı/azalışı
        total_pop = self.population.total
        
        # YENİ: Azalan büyüme hızı (yüksek nüfusta yavaşlar)
        effective_growth = self.growth_rate
        if total_pop > 100000:
            effective_growth *= 0.25  # 100k+ → %25 hız
        elif total_pop > 50000:
            effective_growth *= 0.5   # 50k+ → %50 hız
        
        growth_modifier = self.happiness / 100 * effective_growth
        if food_shortage:
            growth_modifier = -0.05  # %5 düşüş
        
        change = int(total_pop * growth_modifier)
        
        # YENİ: Kapasite limiti kontrolü
        if total_pop + change > population_capacity:
            change = max(0, population_capacity - total_pop)
            if change == 0 and total_pop >= population_capacity:
                audio.announce("Nüfus kapasitesine ulaşıldı. Daha fazla Han veya Hastane inşa edin.")
        
        # Değişimi gruplara dağıt
        if change != 0:
            ratio_farmers = 0.6
            ratio_merchants = 0.2
            ratio_artisans = 0.15
            ratio_soldiers = 0.05
            
            self.population.farmers += int(change * ratio_farmers)
            self.population.merchants += int(change * ratio_merchants)
            self.population.artisans += int(change * ratio_artisans)
            self.population.soldiers += int(change * ratio_soldiers)
        
        # Minimum değerler
        self.population.farmers = max(100, self.population.farmers)
        self.population.merchants = max(50, self.population.merchants)
        self.population.artisans = max(50, self.population.artisans)
        self.population.soldiers = max(10, self.population.soldiers)
        
        # İsyan kontrolü
        self.unrest = self.calculate_unrest()
        
        if self.unrest >= 80 and not self.active_revolt:
            # İsyan başlat
            self.active_revolt = True
            audio.announce("UYARI: Halk isyan etti!")
        elif self.unrest < 50 and self.active_revolt:
            self.active_revolt = False
            audio.announce("İsyan bastırıldı.")
        
        return {
            'population_change': change,
            'happiness': self.happiness,
            'unrest': self.unrest,
            'food_shortage': food_shortage,
            'active_revolt': self.active_revolt
        }
    
    def add_happiness_modifier(self, source: str, value: int):
        """Memnuniyet modifiyeri ekle"""
        self.happiness_modifiers[source] = value
    
    def remove_happiness_modifier(self, source: str):
        """Memnuniyet modifiyeri kaldır"""
        self.happiness_modifiers.pop(source, None)
    
    def announce_status(self):
        """Nüfus durumunu ekran okuyucuya duyur"""
        audio = get_audio_manager()
        audio.speak("Halk Durumu", interrupt=True)
        audio.announce_value("Toplam Nüfus", str(self.population.total))
        audio.announce_value("Çiftçiler", str(self.population.farmers))
        audio.announce_value("Tüccarlar", str(self.population.merchants))
        audio.announce_value("Zanaatkarlar", str(self.population.artisans))
        audio.announce_value("Memnuniyet", f"%{self.happiness}")
        audio.announce_value("Sağlık", f"%{self.health}")
        audio.announce_value("Huzursuzluk", f"%{self.unrest}")
        
        if self.active_revolt:
            audio.speak("UYARI: Aktif isyan var!")
    
    def to_dict(self) -> Dict:
        """Kayıt için dictionary'e dönüştür"""
        return {
            'population': self.population.to_dict(),
            'happiness': self.happiness,
            'health': self.health,
            'unrest': self.unrest,
            'active_revolt': self.active_revolt,
            'happiness_modifiers': self.happiness_modifiers,
            'growth_rate': self.growth_rate,
            'migration_policy': self.migration_policy,
            'education_level': self.education_level
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'PopulationSystem':
        """Dictionary'den yükle"""
        system = cls()
        system.population = PopulationGroups.from_dict(data['population'])
        system.happiness = data['happiness']
        system.health = data['health']
        system.unrest = data['unrest']
        system.active_revolt = data['active_revolt']
        system.happiness_modifiers = data.get('happiness_modifiers', {})
        system.growth_rate = data.get('growth_rate', 0.02)
        system.migration_policy = data.get('migration_policy', MigrationPolicy.SELECTIVE)
        system.education_level = data.get('education_level', 1)
        return system
