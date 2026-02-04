# -*- coding: utf-8 -*-
"""
Osmanlı Eyalet Yönetim Simülasyonu - Oyuncu Karakter Sistemi
Cinsiyet seçimi ve karakter yönetimi
"""

from dataclasses import dataclass, field
from typing import Dict, Optional
from enum import Enum


class Gender(Enum):
    """Cinsiyet seçenekleri"""
    MALE = "male"
    FEMALE = "female"


@dataclass
class GenderBonuses:
    """Cinsiyete göre bonus/malus değerleri"""
    # Erkek bonusları
    MALE_BONUSES = {
        'raid_power': 0.20,           # Akın gücü +%20
        'janissary_loyalty': 0.15,    # Yeniçeri sadakati +%15
        'siege_attack': 0.10,         # Kuşatma saldırı +%10
        'military_prestige': 0.10,    # Askeri prestij +%10
    }
    
    # Kadın bonusları
    FEMALE_BONUSES = {
        'diplomacy': 0.20,            # Diplomasi +%20
        'marriage_alliance': 0.25,    # Evlilik ittifakı +%25
        'espionage': 0.15,            # Casusluk +%15
        'vakif_effect': 0.30,         # Vakıf/hayır etkinliği +%30
        'textile_trade': 0.15,        # Tekstil ticareti +%15
        'population_growth': 0.10,    # Nüfus artışı +%10
    }
    
    # Kadın başlangıç zorlukları (zamanla azalır)
    FEMALE_INITIAL_MALUS = {
        'bey_loyalty': -0.20,         # Bey sadakati -%20 başlangıç
        'ulema_support': -0.15,       # Ulema desteği -%15 başlangıç
    }


@dataclass
class PlayerCharacter:
    """Oyuncu karakteri"""
    name: str
    gender: Gender
    
    # Başlangıç yılı ve yaş
    birth_year: int = 1490  # Yaklaşık 30 yaşında başlangıç
    
    # Deneyim ve itibar
    prestige: int = 50      # 0-100 prestij
    experience: int = 0     # Toplam deneyim
    
    # Başlangıç hikayesi seçimi
    background: str = "default"
    
    # Tur sayacı (malusların azalması için)
    turns_as_governor: int = 0
    
    def get_title(self, context: str = "general") -> str:
        """Bağlama göre unvan döndür"""
        from game.titles import get_title
        return get_title(context, self.gender)
    
    def get_full_title(self) -> str:
        """Tam unvan: İsim + Unvan"""
        title = self.get_title("governor")
        return f"{self.name} {title}"
    
    def get_bonus(self, bonus_type: str) -> float:
        """Belirli bir bonus tipinin değerini döndür"""
        if self.gender == Gender.MALE:
            return GenderBonuses.MALE_BONUSES.get(bonus_type, 0.0)
        else:
            return GenderBonuses.FEMALE_BONUSES.get(bonus_type, 0.0)
    
    def get_malus(self, malus_type: str) -> float:
        """
        Başlangıç maluslarını döndür (kadın için)
        Zamanla azalır: Her 10 turda %5 azalma
        """
        if self.gender == Gender.MALE:
            return 0.0
        
        base_malus = GenderBonuses.FEMALE_INITIAL_MALUS.get(malus_type, 0.0)
        
        # Her 10 turda malus %25 azalır, 40 turda sıfırlanır
        reduction = min(1.0, self.turns_as_governor / 40)
        
        return base_malus * (1 - reduction)
    
    def has_ability(self, ability: str) -> bool:
        """Belirli bir yeteneğe sahip mi?"""
        male_abilities = {'lead_raid', 'command_janissaries', 'duel'}
        female_abilities = {'harem_network', 'court_intrigue', 'charity_event'}
        
        if self.gender == Gender.MALE:
            return ability in male_abilities
        else:
            return ability in female_abilities
    
    def can_personally_lead_raid(self) -> bool:
        """Akına bizzat katılabilir mi?"""
        # Erkekler bizzat katılabilir, kadınlar komutan atar
        return self.gender == Gender.MALE
    
    def process_turn(self):
        """Tur geçişinde güncelleme"""
        self.turns_as_governor += 1
        
        # Her 20 turda prestij artışı (deneyim)
        if self.turns_as_governor % 20 == 0:
            self.prestige = min(100, self.prestige + 5)
            self.experience += 10
    
    def get_background_story(self) -> str:
        """Başlangıç hikayesi"""
        if self.gender == Gender.MALE:
            return (
                f"{self.name}, köklü bir Osmanlı ailesinden gelen bir beydir. "
                f"Dedeniz Fatih Sultan Mehmed'in komutanlarından biriydi. "
                f"Orduda yükselerek Kanuni Sultan Süleyman'ın güvenini kazandınız. "
                f"Şimdi Rumeli Eyaleti'ni yönetmekle görevlendirildiniz."
            )
        else:
            return (
                f"{self.name}, sarayda yetişen nadir kadınlardan biridir. "
                f"Hürrem Sultan'ın himayesinde siyaset ve yönetim öğrendiniz. "
                f"Zekânız ve diplomatik yeteneklerinizle Padişah'ın dikkatini çektiniz. "
                f"Alternatif bir kararla, Kanuni sizi Rumeli'ye vali atadı - tarihte bir ilk! "
                f"Bazı beyler şüpheyle baksa da, başarınızla onları ikna edeceksiniz."
            )
    
    def to_dict(self) -> Dict:
        """Kayıt için dictionary'e dönüştür"""
        return {
            'name': self.name,
            'gender': self.gender.value,
            'birth_year': self.birth_year,
            'prestige': self.prestige,
            'experience': self.experience,
            'background': self.background,
            'turns_as_governor': self.turns_as_governor
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'PlayerCharacter':
        """Dictionary'den yükle"""
        return cls(
            name=data['name'],
            gender=Gender(data['gender']),
            birth_year=data.get('birth_year', 1490),
            prestige=data.get('prestige', 50),
            experience=data.get('experience', 0),
            background=data.get('background', 'default'),
            turns_as_governor=data.get('turns_as_governor', 0)
        )


# Varsayılan erkek karakter (geriye uyumluluk için)
def create_default_character() -> PlayerCharacter:
    """Varsayılan karakter oluştur (eski kayıtlar için)"""
    return PlayerCharacter(
        name="Kasım",
        gender=Gender.MALE
    )
