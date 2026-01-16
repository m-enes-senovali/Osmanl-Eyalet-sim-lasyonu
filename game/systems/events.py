# -*- coding: utf-8 -*-
"""
Osmanlı Eyalet Yönetim Simülasyonu - Olay Sistemi
"""

import random
from dataclasses import dataclass
from typing import Dict, List, Callable, Optional
from enum import Enum
from audio.audio_manager import get_audio_manager


class EventType(Enum):
    """Olay türleri"""
    ECONOMIC = "economic"       # Ekonomik olaylar
    MILITARY = "military"       # Askeri olaylar
    POPULATION = "population"   # Halk olayları
    DIPLOMATIC = "diplomatic"   # Diplomatik olaylar
    NATURAL = "natural"         # Doğal afetler
    OPPORTUNITY = "opportunity" # Fırsatlar


class EventSeverity(Enum):
    """Olay ciddiyeti"""
    MINOR = "minor"       # Küçük
    MODERATE = "moderate" # Orta
    MAJOR = "major"       # Büyük
    CRITICAL = "critical" # Kritik


@dataclass
class EventChoice:
    """Olay seçeneği"""
    text: str
    effects: Dict[str, int]  # {etki_türü: değer}
    description: str
    next_stage: str = None  # Sonraki aşama ID'si (varsa)


@dataclass
class EventStage:
    """Çok aşamalı olay için aşama"""
    stage_id: str
    title: str
    description: str
    choices: List[EventChoice]


@dataclass
class Event:
    """Oyun olayı"""
    id: str
    title: str
    description: str
    event_type: EventType
    severity: EventSeverity
    choices: List[EventChoice]
    
    # Çok aşamalı olay desteği
    stages: Dict[str, EventStage] = None  # {stage_id: EventStage}
    is_multi_stage: bool = False
    
    # Oluşma koşulları
    min_year: int = 0
    max_year: int = 9999
    min_turn: int = 0  # Minimum tur (erken oyun koruması)
    condition_func: Optional[Callable] = None


# Olay tanımlamaları
EVENT_POOL = [
    # === EKONOMİK OLAYLAR ===
    Event(
        id="trade_caravan",
        title="Ticaret Kervanı",
        description="Uzak diyarlardan zengin bir kervan geçiyor. Ne yapacaksınız?",
        event_type=EventType.ECONOMIC,
        severity=EventSeverity.MINOR,
        choices=[
            EventChoice(
                text="Vergi al",
                effects={'gold': 300, 'trade_relation': -5},
                description="300 altın kazandınız ama tüccarlar kızmış olabilir"
            ),
            EventChoice(
                text="Koruma sağla",
                effects={'gold': -100, 'trade_modifier': 5, 'happiness': 2},
                description="Koruma için harcadınız ama ticaret ilişkileri güçlendi"
            ),
            EventChoice(
                text="Görmezden gel",
                effects={},
                description="Kervan geçip gitti"
            )
        ]
    ),
    Event(
        id="crop_failure",
        title="Hasat Sorunu",
        description="Bu yılın hasadı beklenenden kötü. Halk endişeli.",
        event_type=EventType.ECONOMIC,
        severity=EventSeverity.MODERATE,
        choices=[
            EventChoice(
                text="Yiyecek ithal et",
                effects={'gold': -500, 'food': 500, 'happiness': 5},
                description="Dışarıdan yiyecek getirttiniz"
            ),
            EventChoice(
                text="Vergiyi düşür",
                effects={'tax_modifier': -10, 'happiness': 10},
                description="Halk rahatladı ama gelirler düştü"
            ),
            EventChoice(
                text="Hiçbir şey yapma",
                effects={'happiness': -15, 'unrest': 10},
                description="Halk hoşnutsuz"
            )
        ]
    ),
    
    # === ASKERİ OLAYLAR ===
    Event(
        id="bandit_attack",
        title="Eşkıya Saldırısı",
        description="Eşkıya çeteleri köylere saldırıyor!",
        event_type=EventType.MILITARY,
        severity=EventSeverity.MODERATE,
        choices=[
            EventChoice(
                text="Ordu gönder",
                effects={'military_loss': 10, 'happiness': 10, 'loyalty': 5},
                description="Eşkıyalar bastırıldı, bazı kayıplar var"
            ),
            EventChoice(
                text="Fidye öde",
                effects={'gold': -800, 'happiness': -5},
                description="Fidye ödendi ama halk utandı"
            ),
            EventChoice(
                text="Yerel milisi görevlendir",
                effects={'happiness': -10, 'population_loss': 50},
                description="Köylüler savaştı, kayıplar oldu"
            )
        ]
    ),
    Event(
        id="deserters",
        title="Firariler",
        description="Birkaç asker firar etti ve dağlara kaçtı.",
        event_type=EventType.MILITARY,
        severity=EventSeverity.MINOR,
        choices=[
            EventChoice(
                text="Yakalama emri çıkar",
                effects={'gold': -200, 'morale': 5},
                description="Yakalanıp cezalandırıldılar"
            ),
            EventChoice(
                text="Af çıkar",
                effects={'morale': -10, 'happiness': 5},
                description="Affedildiler ama disiplin zayıfladı"
            ),
            EventChoice(
                text="Görmezden gel",
                effects={'morale': -5},
                description="Diğer askerler endişeli"
            )
        ]
    ),
    
    # === HALK OLAYLARI ===
    Event(
        id="plague",
        title="Salgın Hastalık",
        description="Eyalette salgın hastalık yayılıyor!",
        event_type=EventType.POPULATION,
        severity=EventSeverity.CRITICAL,
        choices=[
            EventChoice(
                text="Karantina uygula",
                effects={'gold': -1000, 'population_loss': 200, 'trade_modifier': -10},
                description="Salgın kontrol altına alındı ama ticaret durdu"
            ),
            EventChoice(
                text="Hekimler getir",
                effects={'gold': -2000, 'population_loss': 100, 'happiness': 5},
                description="Hekimler salgını yavaşlattı"
            ),
            EventChoice(
                text="Dua et",
                effects={'population_loss': 500, 'happiness': -20},
                description="Çok sayıda can kaybedildi"
            )
        ]
    ),
    Event(
        id="festival",
        title="Şenlik Talebi",
        description="Halk büyük bir şenlik istiyor.",
        event_type=EventType.POPULATION,
        severity=EventSeverity.MINOR,
        choices=[
            EventChoice(
                text="Şenlik düzenle",
                effects={'gold': -500, 'happiness': 20, 'loyalty': 5},
                description="Muhteşem bir şenlik oldu!"
            ),
            EventChoice(
                text="Küçük kutlama yap",
                effects={'gold': -200, 'happiness': 8},
                description="Mütevazı bir kutlama yapıldı"
            ),
            EventChoice(
                text="Reddet",
                effects={'happiness': -10},
                description="Halk hayal kırıklığına uğradı"
            )
        ]
    ),
    
    # === DİPLOMATİK OLAYLAR ===
    Event(
        id="sultan_gift",
        title="Padişahtan Hediye",
        description="Padişah sadakatinizi takdir ederek hediye gönderdi!",
        event_type=EventType.DIPLOMATIC,
        severity=EventSeverity.MINOR,
        choices=[
            EventChoice(
                text="Teşekkür et",
                effects={'gold': 1000, 'loyalty': 10},
                description="Padişahın lütfuna mazhar oldunuz"
            )
        ]
    ),
    Event(
        id="neighbor_dispute",
        title="Sınır Anlaşmazlığı",
        description="Komşu beylik sınır köylerimiz üzerinde hak iddia ediyor.",
        event_type=EventType.DIPLOMATIC,
        severity=EventSeverity.MODERATE,
        choices=[
            EventChoice(
                text="Savaş ilan et",
                effects={'neighbor_relation': -50, 'morale': 10, 'loyalty': 5},
                description="Savaş durumu, padişah memnun"
            ),
            EventChoice(
                text="Görüşme talep et",
                effects={'gold': -300, 'neighbor_relation': 10},
                description="Diplomatik çözüm arandı"
            ),
            EventChoice(
                text="Köyleri bırak",
                effects={'population_loss': 100, 'happiness': -15, 'loyalty': -10},
                description="Geri çekildiniz, halk ve padişah kızgın"
            )
        ]
    ),
    
    # === DOĞAL AFETLER ===
    Event(
        id="earthquake",
        title="Deprem",
        description="Şiddetli bir deprem büyük hasara yol açtı!",
        event_type=EventType.NATURAL,
        severity=EventSeverity.CRITICAL,
        choices=[
            EventChoice(
                text="Acil yardım başlat",
                effects={'gold': -1500, 'building_damage': 1, 'happiness': 10},
                description="Yardım çalışmaları başladı"
            ),
            EventChoice(
                text="Yeniden inşa odaklan",
                effects={'gold': -2000, 'wood': -500},
                description="Binalar onarılıyor"
            ),
            EventChoice(
                text="Durumu gözle",
                effects={'happiness': -25, 'population_loss': 300},
                description="Yardım gelmedi, çok kayıp var"
            )
        ]
    ),
    Event(
        id="drought",
        title="Kuraklık",
        description="Uzun süreli kuraklık hasatı tehdit ediyor.",
        event_type=EventType.NATURAL,
        severity=EventSeverity.MAJOR,
        choices=[
            EventChoice(
                text="Sulama kanalları kaz",
                effects={'gold': -800, 'food': 200},
                description="Kanallar biraz yardımcı oldu"
            ),
            EventChoice(
                text="Yiyecek depola",
                effects={'gold': -500, 'food': -200},
                description="Stoklar azaldı ama güvende"
            ),
            EventChoice(
                text="Bekle ve dua et",
                effects={'food': -500, 'happiness': -10},
                description="Kuraklık şiddetlendi"
            )
        ]
    ),
    
    # === FIRSATLAR ===
    Event(
        id="mine_discovery",
        title="Maden Keşfi",
        description="Dağlarda zengin bir maden yatağı keşfedildi!",
        event_type=EventType.OPPORTUNITY,
        severity=EventSeverity.MAJOR,
        choices=[
            EventChoice(
                text="Hemen işlet",
                effects={'gold': -1000, 'iron': 500, 'wood': -200},
                description="Maden işletmeye açıldı"
            ),
            EventChoice(
                text="Padişaha bildir",
                effects={'loyalty': 15, 'favor': 10},
                description="Padişah memnun oldu"
            ),
            EventChoice(
                text="Gizli tut",
                effects={'gold': 2000, 'loyalty': -20},
                description="Gizlice işlettin ama riskli"
            )
        ]
    ),
    Event(
        id="skilled_craftsman",
        title="Usta Zanaatkar",
        description="Ünlü bir zanaatkar eyaletinize yerleşmek istiyor.",
        event_type=EventType.OPPORTUNITY,
        severity=EventSeverity.MINOR,
        choices=[
            EventChoice(
                text="Karşıla ve destekle",
                effects={'gold': -300, 'trade_modifier': 5, 'happiness': 5},
                description="Usta işlerini kurdu"
            ),
            EventChoice(
                text="Sadece izin ver",
                effects={'trade_modifier': 2},
                description="Usta kendi başına yerleşti"
            ),
            EventChoice(
                text="Reddet",
                effects={},
                description="Usta başka yere gitti"
            )
        ]
    ),
    
    # === SAVAŞ OLAYLARI ===
    Event(
        id="enemy_raid",
        title="Düşman Akını",
        description="Eşkıyalar eyaletimize akın düzenledi! Köyler yağmalanıyor.",
        event_type=EventType.MILITARY,
        severity=EventSeverity.MAJOR,
        min_turn=15,  # Erken oyunda olmaz
        choices=[
            EventChoice(
                text="Askerlerle karşıla",
                effects={'gold': -200, 'soldiers': -20, 'morale': 10},
                description="Eşkıyalar püskürtüldü ama kayıp verdik"
            ),
            EventChoice(
                text="Fidye öde",
                effects={'gold': -800, 'happiness': -5},
                description="Eşkıyalar gitti ama hazine boşaldı"
            ),
            EventChoice(
                text="Savunmaya çekil",
                effects={'food': -300, 'happiness': -10},
                description="Köyler yağmalandı"
            )
        ]
    ),
    Event(
        id="conquest_opportunity",
        title="Fetih Fırsatı",
        description="Komşu beylikte iç savaş çıktı. Saldırı için uygun zaman!",
        event_type=EventType.MILITARY,
        severity=EventSeverity.MAJOR,
        min_turn=15,
        choices=[
            EventChoice(
                text="Saldırıya geç",
                effects={'gold': -500, 'soldiers': -30, 'neighbor_relation': -40, 'loyalty': 10},
                description="Savaş başladı, padişah memnun"
            ),
            EventChoice(
                text="Fırsatı bekle",
                effects={},
                description="Bekleyip gördük"
            ),
            EventChoice(
                text="Elçi gönder",
                effects={'gold': -200, 'neighbor_relation': 20},
                description="Barış sağlandı ve ittifak kuruldu"
            )
        ]
    ),
    Event(
        id="janissary_unrest",
        title="Yeniçeri Huzursuzluğu",
        description="Yeniçeriler maaş artışı talep ediyor. Tehditler var.",
        event_type=EventType.MILITARY,
        severity=EventSeverity.CRITICAL,
        min_turn=10,
        choices=[
            EventChoice(
                text="Maaşları artır",
                effects={'gold': -1500, 'morale': 30},
                description="Yeniçeriler memnun"
            ),
            EventChoice(
                text="Söz ver",
                effects={'morale': -10},
                description="Geçici sakinlik sağlandı"
            ),
            EventChoice(
                text="Reddet",
                effects={'morale': -40, 'soldiers': -50},
                description="İsyan çıktı, kayıplar var!"
            )
        ]
    ),
    
    # === TİCARET OLAYLARI ===
    Event(
        id="rich_caravan",
        title="Zengin Kervan",
        description="İpek Yolu'ndan zengin bir kervan geçiyor. Koruma teklif ediyorlar.",
        event_type=EventType.ECONOMIC,
        severity=EventSeverity.MODERATE,
        choices=[
            EventChoice(
                text="Koruma sağla",
                effects={'gold': 600, 'trade_modifier': 5},
                description="Tüccarlar memnun, ticaret arttı"
            ),
            EventChoice(
                text="Vergi al",
                effects={'gold': 400},
                description="Vergi alındı"
            ),
            EventChoice(
                text="Yağmala",
                effects={'gold': 1200, 'happiness': -15, 'loyalty': -10},
                description="Kervan yağmalandı ama itibar zedelendi"
            )
        ]
    ),
    Event(
        id="pirate_attack",
        title="Korsan Saldırısı",
        description="Korsanlar gemilerimize saldırdı! Deniz ticareti tehlikede.",
        event_type=EventType.ECONOMIC,
        severity=EventSeverity.MAJOR,
        choices=[
            EventChoice(
                text="Donanma gönder",
                effects={'gold': -800, 'trade_modifier': 10},
                description="Korsanlar temizlendi"
            ),
            EventChoice(
                text="Fidye öde",
                effects={'gold': -500},
                description="Gemiler kurtarıldı"
            ),
            EventChoice(
                text="Kayıpları kabul et",
                effects={'gold': -300, 'trade_modifier': -10},
                description="Mallar kayboldu"
            )
        ]
    ),
    Event(
        id="trade_embargo",
        title="Ticaret Ambargosu",
        description="Düşman beylik ticaret yolumuzu kapattı.",
        event_type=EventType.ECONOMIC,
        severity=EventSeverity.MAJOR,
        min_turn=12,
        choices=[
            EventChoice(
                text="Alternatif yol bul",
                effects={'gold': -600, 'trade_modifier': -5},
                description="Yeni yol bulundu ama maliyetli"
            ),
            EventChoice(
                text="Diplomatik çözüm",
                effects={'gold': -400, 'neighbor_relation': 10},
                description="Ambargo kaldırıldı"
            ),
            EventChoice(
                text="Savaş ilan et",
                effects={'neighbor_relation': -50, 'morale': 15, 'loyalty': 5},
                description="Savaş başladı!"
            )
        ]
    ),
    Event(
        id="silk_road_opening",
        title="İpek Yolu Açılışı",
        description="Doğu ile yeni ticaret anlaşması! Büyük fırsat.",
        event_type=EventType.OPPORTUNITY,
        severity=EventSeverity.MAJOR,
        choices=[
            EventChoice(
                text="Büyük yatırım yap",
                effects={'gold': -1500, 'trade_modifier': 25},
                description="Muazzam ticaret başladı!"
            ),
            EventChoice(
                text="Küçük yatırım",
                effects={'gold': -500, 'trade_modifier': 10},
                description="Orta düzeyde ticaret"
            ),
            EventChoice(
                text="Gözlemle",
                effects={},
                description="Fırsat kaçırıldı"
            )
        ]
    ),
]


class EventSystem:
    """Olay yönetim sistemi"""
    
    def __init__(self):
        self.current_event: Optional[Event] = None
        self.current_stage: Optional[str] = None  # Çok aşamalı olaylar için
        self.event_history: List[str] = []
        self.events_this_year: int = 0
        self.max_events_per_year: int = 3
        
        # Olay ağırlıkları
        self.event_weights = {
            EventType.ECONOMIC: 25,
            EventType.MILITARY: 20,
            EventType.POPULATION: 20,
            EventType.DIPLOMATIC: 15,
            EventType.NATURAL: 10,
            EventType.OPPORTUNITY: 10,
        }
    
    def check_for_event(self, year: int, game_state: dict) -> Optional[Event]:
        """
        Olay kontrolü yap
        Returns: Event veya None
        """
        if self.current_event:
            return None
        
        if self.events_this_year >= self.max_events_per_year:
            return None
        
        # Olay şansı (%30 base + duruma göre)
        base_chance = 30
        
        # Düşük memnuniyet daha fazla olay
        if game_state.get('happiness', 70) < 50:
            base_chance += 15
        
        # Savaş durumunda daha fazla askeri olay
        if game_state.get('at_war', False):
            self.event_weights[EventType.MILITARY] = 35
        
        if random.randint(1, 100) > base_chance:
            return None
        
        # Olay türü seç
        event_type = self._weighted_random_type()
        
        # Bu türden uygun olay seç
        candidates = [
            e for e in EVENT_POOL 
            if e.event_type == event_type
            and e.min_year <= year <= e.max_year
            and e.id not in self.event_history[-10:]  # Son 10 olayda tekrar yok
        ]
        
        if not candidates:
            return None
        
        event = random.choice(candidates)
        self.current_event = event
        self.events_this_year += 1
        
        return event
    
    def _weighted_random_type(self) -> EventType:
        """Ağırlıklı rastgele olay türü seç"""
        total = sum(self.event_weights.values())
        r = random.randint(1, total)
        
        cumulative = 0
        for event_type, weight in self.event_weights.items():
            cumulative += weight
            if r <= cumulative:
                return event_type
        
        return EventType.ECONOMIC
    
    def make_choice(self, choice_index: int) -> Dict[str, int]:
        """
        Olay seçimi yap
        Returns: Etkilerin dictionary'si
        """
        if not self.current_event:
            return {}
        
        # Mevcut aşamadaki seçenekler
        if self.current_stage and self.current_event.stages:
            stage = self.current_event.stages.get(self.current_stage)
            if stage:
                choices = stage.choices
            else:
                choices = self.current_event.choices
        else:
            choices = self.current_event.choices
        
        if choice_index >= len(choices):
            return {}
        
        choice = choices[choice_index]
        
        audio = get_audio_manager()
        audio.speak(choice.description, interrupt=True)
        
        # Etkileri topla
        effects = choice.effects.copy()
        
        # Sonraki aşama var mı?
        if choice.next_stage and self.current_event.stages:
            next_s = self.current_event.stages.get(choice.next_stage)
            if next_s:
                # Sonraki aşamaya geç
                self.current_stage = choice.next_stage
                audio.speak(f"Aşama: {next_s.title}", interrupt=False)
                audio.speak(next_s.description, interrupt=False)
                audio.speak("Seçenekler:", interrupt=False)
                for i, c in enumerate(next_s.choices, 1):
                    audio.speak(f"{i}. {c.text}", interrupt=False)
                return effects  # Olay devam ediyor
        
        # Olay tamamlandı
        self.event_history.append(self.current_event.id)
        self.current_event = None
        self.current_stage = None
        
        return effects
    
    def dismiss_event(self):
        """Olayı kapat (hiçbir şey yapma)"""
        if self.current_event:
            self.event_history.append(self.current_event.id)
            self.current_event = None
    
    def reset_yearly(self):
        """Yıllık sayacı sıfırla"""
        self.events_this_year = 0
    
    def announce_event(self):
        """Olayı ekran okuyucuya duyur"""
        if not self.current_event:
            return
        
        audio = get_audio_manager()
        
        # Ciddiyet duyurusu
        severity_names = {
            EventSeverity.MINOR: "Küçük",
            EventSeverity.MODERATE: "Orta",
            EventSeverity.MAJOR: "Büyük",
            EventSeverity.CRITICAL: "Kritik"
        }
        
        severity = severity_names.get(self.current_event.severity, "")
        audio.announce(f"{severity} Olay: {self.current_event.title}")
        audio.speak(self.current_event.description, interrupt=False)
        
        audio.speak("Seçenekler:")
        for i, choice in enumerate(self.current_event.choices, 1):
            audio.speak(f"{i}. {choice.text}")
    
    def get_current_event_info(self) -> Optional[Dict]:
        """Mevcut olay bilgisi"""
        if not self.current_event:
            return None
        
        return {
            'title': self.current_event.title,
            'description': self.current_event.description,
            'type': self.current_event.event_type.value,
            'severity': self.current_event.severity.value,
            'choices': [
                {'text': c.text, 'description': c.description}
                for c in self.current_event.choices
            ]
        }
    
    def to_dict(self) -> Dict:
        """Kayıt için dictionary'e dönüştür"""
        return {
            'event_history': self.event_history,
            'events_this_year': self.events_this_year,
            'current_event_id': self.current_event.id if self.current_event else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'EventSystem':
        """Dictionary'den yükle"""
        system = cls()
        system.event_history = data.get('event_history', [])
        system.events_this_year = data.get('events_this_year', 0)
        
        # Aktif olayı geri yükle
        current_id = data.get('current_event_id')
        if current_id:
            for event in EVENT_POOL:
                if event.id == current_id:
                    system.current_event = event
                    break
        
        return system
