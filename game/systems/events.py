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
    
    # Cinsiyet filtresi (YENİ)
    # None = herkes, "male" = sadece erkek, "female" = sadece kadın
    gender_filter: Optional[str] = None
    
    # Zincir olay desteği
    chain_id: str = None  # Bu olay hangi zincire ait
    triggers_event: str = None  # Bu olay hangi olayı tetikler
    trigger_delay: int = 0  # Kaç tur sonra tetikler
    required_memory: Dict[str, any] = None  # Gerekli hafıza koşulları


@dataclass
class ChainTrigger:
    """Bekleyen zincir olay tetikleyicisi"""
    event_id: str  # Tetiklenecek olay ID'si
    turns_remaining: int  # Kaç tur kaldı
    source_event_id: str  # Tetikleyen olay
    choice_made: str  # Yapılan seçim
    memory_updates: Dict[str, any] = None  # Hafıza güncellemeleri


@dataclass
class EventChain:
    """Olay zinciri - birbiriyle bağlantılı olaylar"""
    chain_id: str
    name: str
    description: str
    events: List[str]  # Zincirdeki olay ID'leri
    total_stages: int
    current_stage: int = 0
    completed: bool = False
    started_turn: int = 0


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
    
    # ========== ZİNCİR OLAY 1: BÜYÜK VEBA SALGINI (5 aşama) ==========
    Event(
        id="plague_chain_1_signs",
        title="Veba Belirtileri",
        description="Birkaç köyde şüpheli hastalık vakaları görüldü. İnsanlar endişeli.",
        event_type=EventType.POPULATION,
        severity=EventSeverity.MODERATE,
        chain_id="plague_chain",
        min_turn=20,
        choices=[
            EventChoice(
                text="Karantina uygula",
                effects={'gold': -500, 'happiness': -10, 'trade_modifier': -5},
                description="Köyler karantinaya alındı. Ticaret yavaşladı."
            ),
            EventChoice(
                text="Hekimler gönder",
                effects={'gold': -800, 'happiness': 5},
                description="Hekimler hastalığı incelemeye başladı."
            ),
            EventChoice(
                text="Bekle ve gözle",
                effects={},
                description="Durum izleniyor..."
            )
        ]
    ),
    Event(
        id="plague_chain_2_spread",
        title="Veba Yayılıyor!",
        description="Hastalık hızla yayılıyor! Köyler panik içinde. Acil karar gerekli.",
        event_type=EventType.POPULATION,
        severity=EventSeverity.CRITICAL,
        chain_id="plague_chain",
        required_memory={'plague_started': True, 'plague_quarantine': False},
        choices=[
            EventChoice(
                text="Sert karantina uygula",
                effects={'gold': -1000, 'happiness': -20, 'trade_modifier': -15, 'population_loss': 200},
                description="Geç kaldık ama karantina başladı. Kayıplar var."
            ),
            EventChoice(
                text="Usta hekimler getirt",
                effects={'gold': -2000, 'population_loss': 100},
                description="Doğudan usta hekimler geldi."
            ),
            EventChoice(
                text="Dua ve oruç ilan et",
                effects={'happiness': 5, 'population_loss': 500},
                description="Halk dua etti ama kayıplar çok."
            )
        ]
    ),
    Event(
        id="plague_chain_2_contained",
        title="Karantina Sıkıntısı",
        description="Karantina işe yarıyor ama halk sıkıntıda. Yiyecek azalıyor.",
        event_type=EventType.POPULATION,
        severity=EventSeverity.MAJOR,
        chain_id="plague_chain",
        required_memory={'plague_started': True, 'plague_quarantine': True},
        choices=[
            EventChoice(
                text="Yiyecek dağıt",
                effects={'gold': -600, 'food': -300, 'happiness': 10},
                description="Halka yiyecek dağıtıldı, moral yükseldi."
            ),
            EventChoice(
                text="Karantinayı sıkılaştır",
                effects={'happiness': -15, 'population_loss': 50},
                description="Karantina sertleşti, bazıları kaçmaya çalıştı."
            ),
            EventChoice(
                text="Karantinayı gevşet",
                effects={'happiness': 5, 'trade_modifier': 5},
                description="Karantina gevşetildi, risk var ama halk rahatladı."
            )
        ]
    ),
    Event(
        id="plague_chain_3_peak",
        title="Veba Doruk Noktasında",
        description="Hastalık en yoğun döneminde. Her gün cenazeler kaldırılıyor.",
        event_type=EventType.POPULATION,
        severity=EventSeverity.CRITICAL,
        chain_id="plague_chain",
        required_memory={'plague_started': True},
        choices=[
            EventChoice(
                text="Toplu mezarlar kaz",
                effects={'gold': -300, 'happiness': -20, 'population_loss': 300},
                description="Cenazeler defnedildi ama halk çok üzgün."
            ),
            EventChoice(
                text="Şifalı otlar dağıt",
                effects={'gold': -500, 'population_loss': 200, 'happiness': 5},
                description="Ot tedavisi biraz işe yaradı."
            ),
            EventChoice(
                text="Padişahtan yardım iste",
                effects={'loyalty': -10, 'gold': 1000, 'population_loss': 250},
                description="Padişah yardım gönderdi ama zayıflığınızı gördü."
            )
        ]
    ),
    Event(
        id="plague_chain_4_end",
        title="Veba Sonu",
        description="Hastalık nihayet azalıyor. Ağır bir dönem geçirdik.",
        event_type=EventType.POPULATION,
        severity=EventSeverity.MAJOR,
        chain_id="plague_chain",
        required_memory={'plague_started': True},
        choices=[
            EventChoice(
                text="Şükür şenliği düzenle",
                effects={'gold': -400, 'happiness': 25, 'loyalty': 5},
                description="Büyük şenlik! Halk mutlu, padişah memnun."
            ),
            EventChoice(
                text="Yeniden inşa odaklan",
                effects={'gold': -800, 'wood': -200, 'happiness': 10},
                description="Hasar gören yerler onarılıyor."
            ),
            EventChoice(
                text="Normal hayata dön",
                effects={'happiness': 5},
                description="Yavaş yavaş normale dönülüyor."
            )
        ]
    ),
    
    # ========== ZİNCİR OLAY 2: YENİÇERİ İSYANI (4 aşama) ==========
    Event(
        id="janissary_chain_1_demand",
        title="Yeniçeri Maaş Talebi",
        description="Yeniçeriler toplanıp maaş artışı talep ediyor. Tehditkar tavırları var.",
        event_type=EventType.MILITARY,
        severity=EventSeverity.MAJOR,
        chain_id="janissary_chain",
        min_turn=25,
        choices=[
            EventChoice(
                text="Maaşları artır",
                effects={'gold': -2000, 'morale': 30},
                description="Yeniçeriler memnun oldu."
            ),
            EventChoice(
                text="Söz ver, sonra görüşelim",
                effects={'morale': -5},
                description="Geçici bir sakinlik sağlandı..."
            ),
            EventChoice(
                text="Reddet ve tehdit et",
                effects={'morale': -20},
                description="Yeniçeriler öfkelendi!"
            )
        ]
    ),
    Event(
        id="janissary_chain_2_unrest",
        title="Yeniçeri Kazan Kaldırma",
        description="Yeniçeriler kazanlarını kaldırdı! Bu geleneksel isyan işareti!",
        event_type=EventType.MILITARY,
        severity=EventSeverity.CRITICAL,
        chain_id="janissary_chain",
        required_memory={'janissary_angry': True},
        choices=[
            EventChoice(
                text="Hemen maaş artır",
                effects={'gold': -3000, 'morale': 20, 'loyalty': -5},
                description="Geç kalmış bir uzlaşma. İtibar zedelendi."
            ),
            EventChoice(
                text="Sadık birlikleri topla",
                effects={'gold': -500, 'soldiers': -30},
                description="Sadık askerler hazırlanıyor..."
            ),
            EventChoice(
                text="Kaç",
                effects={'loyalty': -30, 'happiness': -20},
                description="Vali geçici olarak kaçtı. Büyük utanç!"
            )
        ]
    ),
    Event(
        id="janissary_chain_3_revolt",
        title="Yeniçeri İsyanı Patladı!",
        description="Yeniçeriler isyan etti! Sokak savaşları var. Saray tehlikede!",
        event_type=EventType.MILITARY,
        severity=EventSeverity.CRITICAL,
        chain_id="janissary_chain",
        required_memory={'janissary_revolt': True},
        choices=[
            EventChoice(
                text="Savaş - bastır",
                effects={'soldiers': -100, 'morale': 20, 'gold': -1000},
                description="Kanlı çatışma! Kayıplar ağır ama isyan bastırıldı."
            ),
            EventChoice(
                text="Müzakere et",
                effects={'gold': -4000, 'morale': -10, 'loyalty': -10},
                description="Ağır bedel ödendi ama kan dökülmedi."
            ),
            EventChoice(
                text="Liderlerini suikastle öldür",
                effects={'gold': -800, 'morale': -30, 'happiness': -10},
                description="Liderler gizlice öldürüldü. İsyan dağıldı ama güven sarsıldı."
            )
        ]
    ),
    Event(
        id="janissary_chain_4_aftermath",
        title="İsyan Sonrası",
        description="İsyan bitti. Şimdi sonuçlarla yüzleşme zamanı.",
        event_type=EventType.MILITARY,
        severity=EventSeverity.MAJOR,
        chain_id="janissary_chain",
        required_memory={'janissary_resolved': True},
        choices=[
            EventChoice(
                text="Affet ve birleştir",
                effects={'happiness': 10, 'morale': 15, 'loyalty': 5},
                description="Af ilan edildi. Birlik sağlandı."
            ),
            EventChoice(
                text="Suçluları cezalandır",
                effects={'morale': -10, 'loyalty': 10, 'happiness': -5},
                description="İsyancılar cezalandırıldı. Padişah memnun."
            ),
            EventChoice(
                text="Yeniçeri ocağını reforma et",
                effects={'gold': -1500, 'morale': 5, 'military_bonus': 10},
                description="Yeniçeri sistemi modernleştirildi."
            )
        ]
    ),
    
    # ========== ZİNCİR OLAY 3: İPEK YOLU MACERASI (3 aşama) ==========
    Event(
        id="silkroad_chain_1_offer",
        title="Tüccar Teklifi",
        description="Zengin bir tüccar büyük bir kervan yolculuğu öneriyor. Yüksek kar vaat ediyor.",
        event_type=EventType.ECONOMIC,
        severity=EventSeverity.MODERATE,
        chain_id="silkroad_chain",
        min_turn=15,
        choices=[
            EventChoice(
                text="Büyük yatırım yap",
                effects={'gold': -2000},
                description="Büyük sermaye yatırıldı. Kervan yola çıktı."
            ),
            EventChoice(
                text="Küçük yatırım yap",
                effects={'gold': -800},
                description="Temkinli yatırım yapıldı."
            ),
            EventChoice(
                text="Reddet",
                effects={},
                description="Teklif reddedildi."
            )
        ]
    ),
    Event(
        id="silkroad_chain_2_journey",
        title="Kervan Tehlikede!",
        description="Kervanınız eşkıyaların pusuya düştü! Ne yapacaksınız?",
        event_type=EventType.ECONOMIC,
        severity=EventSeverity.MAJOR,
        chain_id="silkroad_chain",
        required_memory={'silkroad_invested': True},
        choices=[
            EventChoice(
                text="Muhafız gönder",
                effects={'gold': -500, 'soldiers': -20},
                description="Muhafızlar yola çıktı."
            ),
            EventChoice(
                text="Fidye öde",
                effects={'gold': -1000},
                description="Eşkıyalara fidye ödendi."
            ),
            EventChoice(
                text="Kendi başlarına bırак",
                effects={},
                description="Kervan kendi kaderine bırakıldı..."
            )
        ]
    ),
    Event(
        id="silkroad_chain_3_return",
        title="Kervan Dönüşü",
        description="Kervan nihayet döndü. Sonuçlar belli olacak.",
        event_type=EventType.ECONOMIC,
        severity=EventSeverity.MAJOR,
        chain_id="silkroad_chain",
        required_memory={'silkroad_invested': True},
        choices=[
            EventChoice(
                text="Karları al",
                effects={'gold': 4000, 'trade_modifier': 10},
                description="Muhteşem kar! Ticaret ilişkileri güçlendi."
            ),
            EventChoice(
                text="Tüccarla ortaklık kur",
                effects={'gold': 2000, 'trade_modifier': 20},
                description="Kalıcı ticaret ortaklığı kuruldu."
            ),
            EventChoice(
                text="Kayıpları kabul et",
                effects={'gold': -500},
                description="Yolculuk zarara uğradı."
            )
        ]
    ),
    
    # ========== ZİNCİR OLAY 4: PADİŞAH ZİYARETİ (4 aşama) ==========
    Event(
        id="sultan_chain_1_news",
        title="Padişah Geliyor!",
        description="Haberci geldi: Padişah hazretleri eyaletimizi ziyaret edecek! Büyük onur!",
        event_type=EventType.DIPLOMATIC,
        severity=EventSeverity.MAJOR,
        chain_id="sultan_chain",
        min_turn=30,
        choices=[
            EventChoice(
                text="Muhteşem karşılama hazırla",
                effects={'gold': -3000, 'loyalty': 10},
                description="Görkemli hazırlıklar başladı."
            ),
            EventChoice(
                text="Mütevazi karşılama",
                effects={'gold': -1000},
                description="Saygılı ama sade hazırlıklar."
            ),
            EventChoice(
                text="Erteleme talep et",
                effects={'loyalty': -15},
                description="Padişah memnun değil ama erteledi."
            )
        ]
    ),
    Event(
        id="sultan_chain_2_preparation",
        title="Hazırlık Günleri",
        description="Ziyaret yaklaşıyor. Son hazırlıklar yapılıyor.",
        event_type=EventType.DIPLOMATIC,
        severity=EventSeverity.MODERATE,
        chain_id="sultan_chain",
        required_memory={'sultan_visit': True},
        choices=[
            EventChoice(
                text="Askeri geçit töreni",
                effects={'gold': -500, 'morale': 15},
                description="Ordunuz geçit için hazırlanıyor."
            ),
            EventChoice(
                text="Halk şenliği",
                effects={'gold': -800, 'happiness': 15},
                description="Halk için büyük şenlik hazırlanıyor."
            ),
            EventChoice(
                text="Hediye hazırla",
                effects={'gold': -1500},
                description="Padişaha özel hediyeler hazırlandı."
            )
        ]
    ),
    Event(
        id="sultan_chain_3_visit",
        title="Padişah Geldi!",
        description="Padişah hazretleri eyalete teşrif etti. Herkes heyecanlı ve gergin.",
        event_type=EventType.DIPLOMATIC,
        severity=EventSeverity.CRITICAL,
        chain_id="sultan_chain",
        required_memory={'sultan_visit': True},
        choices=[
            EventChoice(
                text="Sadakatinizi bildirin",
                effects={'loyalty': 20},
                description="Padişahın önünde diz çöktünüz."
            ),
            EventChoice(
                text="Başarılarınızı sunun",
                effects={'loyalty': 10, 'gold': 500},
                description="Padişah eyaletin gelişimini takdir etti."
            ),
            EventChoice(
                text="Şikayet iletin",
                effects={'loyalty': -10, 'gold': 1000},
                description="Cesaretinizi beğendi ama temkinli."
            )
        ]
    ),
    Event(
        id="sultan_chain_4_aftermath",
        title="Ziyaret Sonrası",
        description="Padişah ayrıldı. Şimdi sonuçlar belli oluyor.",
        event_type=EventType.DIPLOMATIC,
        severity=EventSeverity.MAJOR,
        chain_id="sultan_chain",
        required_memory={'sultan_visit': True},
        choices=[
            EventChoice(
                text="Padişah memnun - terfi",
                effects={'loyalty': 15, 'gold': 2000, 'happiness': 10},
                description="Padişah sizi ödüllendirdi! Büyük onur."
            ),
            EventChoice(
                text="Normal ayrılış",
                effects={'loyalty': 5},
                description="Ziyaret başarıyla tamamlandı."
            ),
            EventChoice(
                text="Padişah soğuk ayrıldı",
                effects={'loyalty': -20, 'happiness': -10},
                description="Bir şeyler ters gitti. Endişe verici."
            )
        ]
    ),
    
    # ========== ZİNCİR OLAY 5: FETİH SEFERİ (5 aşama) ==========
    Event(
        id="conquest_chain_1_call",
        title="Sefere Çağrı",
        description="Padişah büyük sefer için asker topluyor. Katılım bekleniyor.",
        event_type=EventType.MILITARY,
        severity=EventSeverity.MAJOR,
        chain_id="conquest_chain",
        min_turn=35,
        choices=[
            EventChoice(
                text="Büyük ordu gönder",
                effects={'soldiers': -200, 'gold': -1000, 'loyalty': 20},
                description="Büyük bir kuvvet sefere katılıyor."
            ),
            EventChoice(
                text="Küçük birlik gönder",
                effects={'soldiers': -50, 'gold': -300, 'loyalty': 5},
                description="Sembolik katılım sağlandı."
            ),
            EventChoice(
                text="Mazeret bildir",
                effects={'loyalty': -25, 'gold': -500},
                description="Katılamadınız. Padişah kızgın."
            )
        ]
    ),
    Event(
        id="conquest_chain_2_march",
        title="Uzun Yürüyüş",
        description="Ordu seferde. Lojistik sorunlar çıkıyor.",
        event_type=EventType.MILITARY,
        severity=EventSeverity.MODERATE,
        chain_id="conquest_chain",
        required_memory={'conquest_joined': True},
        choices=[
            EventChoice(
                text="Ek erzak gönder",
                effects={'gold': -800, 'food': -500},
                description="Erzak konvoyu yola çıktı."
            ),
            EventChoice(
                text="Yağma izni ver",
                effects={'morale': 10, 'loyalty': -10},
                description="Askerler yağmaladı. Halk şikayetçi."
            ),
            EventChoice(
                text="Disiplin koru",
                effects={'morale': -10, 'soldiers': -20},
                description="Disiplin korundu ama kayıplar var."
            )
        ]
    ),
    Event(
        id="conquest_chain_3_siege",
        title="Kuşatma",
        description="Düşman kalesi kuşatıldı. Taktik kararlar gerekiyor.",
        event_type=EventType.MILITARY,
        severity=EventSeverity.CRITICAL,
        chain_id="conquest_chain",
        required_memory={'conquest_joined': True},
        choices=[
            EventChoice(
                text="Genel saldırı",
                effects={'soldiers': -80, 'morale': 20},
                description="Kanlı saldırı! Kayıplar ağır ama ilerleme var."
            ),
            EventChoice(
                text="Kuşatmayı sürdür",
                effects={'gold': -500, 'food': -300},
                description="Sabırlı kuşatma devam ediyor."
            ),
            EventChoice(
                text="Tünel kaz",
                effects={'gold': -1000, 'soldiers': -30},
                description="Gizli tünel kazılıyor."
            )
        ]
    ),
    Event(
        id="conquest_chain_4_battle",
        title="Büyük Savaş!",
        description="Nihai savaş başladı! Kaderi belirleyecek an.",
        event_type=EventType.MILITARY,
        severity=EventSeverity.CRITICAL,
        chain_id="conquest_chain",
        required_memory={'conquest_joined': True},
        choices=[
            EventChoice(
                text="Ön safta savaş",
                effects={'soldiers': -50, 'morale': 30, 'loyalty': 15},
                description="Kahramanca savaştınız! Zafer yakın."
            ),
            EventChoice(
                text="Taktik komuta",
                effects={'soldiers': -30, 'morale': 15},
                description="Akıllı taktiklerle avantaj sağladınız."
            ),
            EventChoice(
                text="Geride kal",
                effects={'morale': -20, 'loyalty': -10},
                description="Geride kaldınız. Dedikodular yayılıyor."
            )
        ]
    ),
    Event(
        id="conquest_chain_5_spoils",
        title="Zafer ve Ganimet",
        description="Savaş kazanıldı! Ganimetler paylaşılıyor.",
        event_type=EventType.MILITARY,
        severity=EventSeverity.MAJOR,
        chain_id="conquest_chain",
        required_memory={'conquest_victory': True},
        choices=[
            EventChoice(
                text="Büyük pay al",
                effects={'gold': 5000, 'loyalty': -10, 'iron': 500},
                description="Büyük ganimet! Ama kıskançlık var."
            ),
            EventChoice(
                text="Adil paylaş",
                effects={'gold': 2500, 'morale': 20, 'happiness': 10},
                description="Adil paylaşım. Herkes memnun."
            ),
            EventChoice(
                text="Padişaha bağışla",
                effects={'gold': 1000, 'loyalty': 25},
                description="Ganimetleri padişaha sundunuz. Büyük sadakat."
            )
        ]
    ),
]

# ============================================================
# CİNSİYETE ÖZEL OLAYLAR (YENİ)
# ============================================================

# ERKEK ÖZEL OLAYLARI
MALE_EVENTS = [
    Event(
        id="raid_invitation",
        title="Akın Daveti",
        description="Macar sınırında bir akın planlanıyor. Komşu Sancakbeyi sizi de davet ediyor. Bizzat katılmak şeref meselesi.",
        event_type=EventType.MILITARY,
        severity=EventSeverity.MODERATE,
        gender_filter="male",  # Sadece erkek
        min_turn=20,
        choices=[
            EventChoice(
                text="Bizzat katıl",
                effects={'gold': 1500, 'soldiers': -30, 'morale': 25, 'loyalty': 10},
                description="Akına bizzat katıldınız. Zafer ve ganimet!"
            ),
            EventChoice(
                text="Birlik gönder, kendim kalmak",
                effects={'gold': 500, 'soldiers': -20, 'morale': 5},
                description="Birlik gönderdiniz ama katılmadınız. Bazıları dedikoduyor."
            ),
            EventChoice(
                text="Reddet",
                effects={'morale': -15, 'loyalty': -5},
                description="Akından uzak durdunuz. Savaşçılar hayal kırıklığına uğradı."
            )
        ]
    ),
    Event(
        id="yenicheri_loyalty_test",
        title="Yeniçeri Ağası ile Mülaakat",
        description="Yeniçeri Ağası sizinle özel görüşmek istiyor. Askeri konularda fikrinizi soruyor. Bu bir sadakat testi olabilir.",
        event_type=EventType.MILITARY,
        severity=EventSeverity.MODERATE,
        gender_filter="male",
        min_turn=30,
        choices=[
            EventChoice(
                text="Askeri deneyimimi paylaş",
                effects={'morale': 20, 'loyalty': 10},
                description="Askeri bilginiz Ağa'yı etkiledi. Saygınlığınız arttı."
            ),
            EventChoice(
                text="Diplomatik cevap ver",
                effects={'morale': 5, 'loyalty': 5},
                description="Dikkatli cevaplar verdiniz. Ağa tarafsız kaldı."
            ),
            EventChoice(
                text="Padişaha sadakatimi vurgula",
                effects={'loyalty': 20, 'morale': -5},
                description="Padişaha bağlılığınızı vurguladınız. Ağa memnun ama askerler soğuk."
            )
        ]
    ),
]

# KADIN ÖZEL OLAYLARI
FEMALE_EVENTS = [
    Event(
        id="harem_letter",
        title="Saray Mektubu",
        description="Hürrem Sultan'dan gizli bir mektup geldi. Saray politikaları hakkında bilgi paylaşıyor ve tavsiye istiyor.",
        event_type=EventType.DIPLOMATIC,
        severity=EventSeverity.MODERATE,
        gender_filter="female",  # Sadece kadın
        min_turn=15,
        choices=[
            EventChoice(
                text="Değerli istihbarat paylaş",
                effects={'loyalty': 20, 'gold': 1000},
                description="Hürrem Sultan memnun. Saray desteğiniz güçlendi."
            ),
            EventChoice(
                text="Diplomatik cevap yaz",
                effects={'loyalty': 10},
                description="Dikkatli bir cevap yazdınız. İlişkiniz devam ediyor."
            ),
            EventChoice(
                text="Tarafsız kal",
                effects={'loyalty': -5},
                description="Saray politikalarından uzak durdunuz. Bazıları bunu zayıflık olarak gördü."
            )
        ]
    ),
    Event(
        id="skeptical_beys",
        title="Şüpheci Beyler",
        description="Bazı sancak beyleri kadın vali olarak yetkinliğinizi sorguluyor. Bir toplantı yapmanız gerekiyor.",
        event_type=EventType.DIPLOMATIC,
        severity=EventSeverity.MAJOR,
        gender_filter="female",
        min_turn=10,
        choices=[
            EventChoice(
                text="Diplomatik becerilerimi göster",
                effects={'happiness': 15, 'loyalty': 10},
                description="İkna edici konuşmanız beylerı etkiledi. Saygı kazandınız."
            ),
            EventChoice(
                text="Başarılarımı kanıtla",
                effects={'gold': -500, 'happiness': 10, 'morale': 10},
                description="Eyaletin başarılarını gösterdiniz. Şüpheler azaldı."
            ),
            EventChoice(
                text="Padişah fermanını göster",
                effects={'loyalty': 15, 'happiness': -5},
                description="Padişah otoritesini vurguladınız. Beyler sustu ama memnun değil."
            )
        ]
    ),
    Event(
        id="charity_event",
        title="Vakıf Açılışı Daveti",
        description="Yeni bir imaret vakfı açılışına davet edildiniz. Katılımınız toplumsal itibarınızı artırabilir.",
        event_type=EventType.POPULATION,
        severity=EventSeverity.MINOR,
        gender_filter="female",
        min_turn=20,
        choices=[
            EventChoice(
                text="Cömertçe bağış yap",
                effects={'gold': -1000, 'happiness': 25, 'loyalty': 5},
                description="Cömert bağışınız halk arasında büyük takdir topladı."
            ),
            EventChoice(
                text="Sembolik katılım",
                effects={'happiness': 10},
                description="Açılışa katıldınız. Halk memnun."
            ),
            EventChoice(
                text="Meşguliyetten özür dile",
                effects={'happiness': -5},
                description="Katılmadınız. Bazıları hayal kırıklığına uğradı."
            )
        ]
    ),
]

# === YENİ ERKEK OLAYLARI ===
MALE_EVENTS.extend([
    Event(
        id="wrestling_match",
        title="Güreş Meydanı Daveti",
        description="Yeniçeriler aranızda bir güreş müsabakası düzenlemek istiyor. Katılmanız askeri saygınlığınızı artırabilir.",
        event_type=EventType.MILITARY,
        severity=EventSeverity.MINOR,
        gender_filter="male",
        min_turn=15,
        choices=[
            EventChoice(
                text="Bizzat katıl ve güreş",
                effects={'morale': 20, 'happiness': 10, 'gold': -100},
                description="Güreştiniz ve askerlerinizin saygısını kazandınız!"
            ),
            EventChoice(
                text="Seyirci olarak katıl",
                effects={'morale': 10, 'happiness': 5},
                description="Müsabakayı izlediniz. Askerler memnun."
            ),
            EventChoice(
                text="Reddet, meşgulüm",
                effects={'morale': -5},
                description="Askerler hayal kırıklığına uğradı."
            )
        ]
    ),
    Event(
        id="frontier_patrol",
        title="Serhat Devriyesi",
        description="Sınır boylarındaki akıncı beyleri sizinle birlikte devriye gezmek istiyor. Tehlikeli ama nüfuz kazandırır.",
        event_type=EventType.MILITARY,
        severity=EventSeverity.MODERATE,
        gender_filter="male",
        min_turn=25,
        choices=[
            EventChoice(
                text="Akıncılarla birlikte devri",
                effects={'morale': 15, 'loyalty': 10, 'gold': -200},
                description="Sınır boylarını gezdiniz. Akıncılar sizi benimsedi."
            ),
            EventChoice(
                text="Komutan gönder",
                effects={'morale': 5, 'loyalty': 5},
                description="Güvenilir bir komutan gönderdiniz. İlişkiler sürdü."
            ),
            EventChoice(
                text="Askeri tatbikat düzenle",
                effects={'morale': 10, 'gold': -500, 'happiness': -5},
                description="Tatbikat başarılı oldu ama masraflıydı."
            )
        ]
    ),
    Event(
        id="hunting_party",
        title="Av Partisi",
        description="Komşu sancak beyleri sizi büyük bir av partisine davet ediyor. Diplomatik ilişkileri güçlendirmek için bir fırsat.",
        event_type=EventType.DIPLOMATIC,
        severity=EventSeverity.MINOR,
        gender_filter="male",
        min_turn=10,
        choices=[
            EventChoice(
                text="Büyük bir av ziyafeti ver",
                effects={'gold': -800, 'happiness': 15, 'loyalty': 10},
                description="Gösterişli ziyafetiniz beyleri etkiledi. İttifaklar güçlendi."
            ),
            EventChoice(
                text="Sade bir av organize et",
                effects={'happiness': 8, 'loyalty': 5},
                description="Samimi bir av günü geçirdiniz. İlişkiler iyileşti."
            ),
            EventChoice(
                text="Avı reddet, divan işleri var",
                effects={'loyalty': -5, 'gold': 200},
                description="İş odaklı kararınız bazı beyleri soğuttu."
            )
        ]
    ),
])

# === YENİ KADIN OLAYLARI ===
FEMALE_EVENTS.extend([
    Event(
        id="court_physician",
        title="Saray Hekimi Talebi",
        description="Eyalet halkı arasında hastalık yayılıyor. Saray hekimlerinden yardım isteyebilirsiniz - sarayla bağlantılarınız bunu kolaylaştırır.",
        event_type=EventType.POPULATION,
        severity=EventSeverity.MODERATE,
        gender_filter="female",
        min_turn=15,
        choices=[
            EventChoice(
                text="Saray hekimleri çağır",
                effects={'gold': -600, 'happiness': 25, 'loyalty': 5},
                description="Saray hekimleri geldi. Hastalık kontrol altına alındı. Halk minnettar."
            ),
            EventChoice(
                text="Yerel hekimleri destekle",
                effects={'gold': -300, 'happiness': 15},
                description="Yerel hekimlere kaynak sağladınız. Durumu idare ettiler."
            ),
            EventChoice(
                text="Dua ve sabır tavsiye et",
                effects={'happiness': -10, 'loyalty': 5},
                description="Dindar bir tutum takındınız. Ulema memnun ama halk endişeli."
            )
        ]
    ),
    Event(
        id="valide_sultan_diplomacy",
        title="Valide Sultan'ın Ricası",
        description="Valide Sultan, komşu eyaletle arası bozulan bir paşayı barıştırmanızı rica ediyor. Başarırsanız saray nezdinde itibarınız artar.",
        event_type=EventType.DIPLOMATIC,
        severity=EventSeverity.MAJOR,
        gender_filter="female",
        min_turn=30,
        choices=[
            EventChoice(
                text="Arabuluculuk yap",
                effects={'gold': -400, 'loyalty': 20, 'happiness': 10},
                description="Diplomatik zekanızla tarafları barıştırdınız. Valide Sultan çok memnun."
            ),
            EventChoice(
                text="Mektupla çöz",
                effects={'loyalty': 10},
                description="Yazışmalarla durumu yatıştırdınız. Kısmen başarılı."
            ),
            EventChoice(
                text="Karışmamayı tercih et",
                effects={'loyalty': -10},
                description="Saray politikasından uzak durdunuz. Valide Sultan kırgın."
            )
        ]
    ),
    Event(
        id="harem_network_intel",
        title="Harem Ağından İstihbarat",
        description="Saraylardaki güvenilir cariyeleriniz önemli bir bilgi getirdi: Rakip bir paşa sizin yerinize atanmak için çalışıyor.",
        event_type=EventType.DIPLOMATIC,
        severity=EventSeverity.MAJOR,
        gender_filter="female",
        min_turn=20,
        choices=[
            EventChoice(
                text="Padişaha sadakat mektubu yaz",
                effects={'gold': -1000, 'loyalty': 25},
                description="Hediyelerle birlikte sadakat mektubunuz padişahı etkiledi."
            ),
            EventChoice(
                text="Rakibi gizlice araştır",
                effects={'gold': -500, 'loyalty': 15, 'happiness': -5},
                description="Rakibin zayıf noktalarını buldunuz. Konumunuz güçlendi."
            ),
            EventChoice(
                text="Halkın desteğini göster",
                effects={'gold': -300, 'happiness': 20, 'loyalty': 10},
                description="Eyaletteki başarılarınızı belgelettiniz. En iyi savunma başarıdır."
            )
        ]
    ),
])

# Cinsiyete özel olayları havuza ekle
EVENT_POOL.extend(MALE_EVENTS)
EVENT_POOL.extend(FEMALE_EVENTS)

CELALI_EVENTS = [
    Event(
        id="celali_chain_1_rumors",
        title="Celali Eşkıyası",
        description="Anadolu'da dirlik düzeni bozuldu. Bir asi lideri asker toplayıp yolları kesmeye başladı.",
        event_type=EventType.MILITARY,
        severity=EventSeverity.MODERATE,
        chain_id="celali_chain",
        min_year=1550,
        condition_func=lambda state: state.get('unrest', 0) > 40,
        choices=[
            EventChoice(
                text="Asker gönderip ez",
                effects={'gold': -500, 'soldiers': -50},
                description="Ordumuz isyancıları dağıtmayı denedi. Masraflı ve kanlı oldu."
            ),
            EventChoice(
                text="Lidere paşalık ver (Rüşvet)",
                effects={'gold': -1000, 'loyalty': -10},
                description="İsyancı lideri parayla satın aldınız ama sarayda itibarınız sarsıldı."
            ),
            EventChoice(
                text="Görmezden gel",
                effects={'happiness': -10, 'unrest': 15},
                description="Halk kaderine terk edildi. İsyan büyüyor..."
            )
        ]
    ),
    Event(
        id="celali_chain_2_uprising",
        title="Büyük Celali Kalkışması",
        description="Önü alınamayan isyancılar büyük bir şehri kuşattı! Acil müdahale şart.",
        event_type=EventType.MILITARY,
        severity=EventSeverity.MAJOR,
        chain_id="celali_chain",
        choices=[
            EventChoice(
                text="Topyekün sefere çık",
                effects={'gold': -1500, 'soldiers': -150, 'happiness': 5},
                description="Merkez ordu sefere çıktı. İsyancılarla amansız bir savaş başladı."
            ),
            EventChoice(
                text="Müzakere et",
                effects={'gold': -500, 'loyalty': -20, 'unrest': 10},
                description="Sarayın onaylamadığı zayıf bir taviz verdiniz. Otorite sarsıldı."
            )
        ]
    ),
    Event(
        id="celali_chain_3_climax",
        title="İsyanın Bastırılması",
        description="Aylardır süren çatışmalar ve müzakereler sonucunda Celali isyancıları nihayet dağıldı.",
        event_type=EventType.MILITARY,
        severity=EventSeverity.MODERATE,
        chain_id="celali_chain",
        choices=[
            EventChoice(
                text="Liderleri idam et",
                effects={'happiness': 10, 'loyalty': 15, 'unrest': -20},
                description="İbretialem için sert bir ceza verdiniz."
            ),
            EventChoice(
                text="Genel af ilan et",
                effects={'happiness': 20, 'unrest': -10},
                description="Halk affınızı sevinçle karşıladı ancak tehlike geçmiş sayılmaz."
            )
        ]
    )
]

SUCCESSION_EVENTS = [
    Event(
        id="succession_chain_1_news",
        title="Taht Kavgaları",
        description="Padişahın hastalığı ağırlaştı. Şehzadeler arasında taht mücadelesi baş gösterdi. Tarafınızı seçin!",
        event_type=EventType.DIPLOMATIC,
        severity=EventSeverity.CRITICAL,
        chain_id="succession_chain",
        min_turn=40,
        condition_func=lambda state: state.get('loyalty', 100) < 40,
        choices=[
            EventChoice(
                text="Büyük Şehzadeyi destekle",
                effects={'gold': -500, 'loyalty': 0},
                description="Geleneksel verasete uygun olarak büyük şehzadeye biat ettiniz."
            ),
            EventChoice(
                text="Güçlü Şehzadeyi destekle",
                effects={'gold': -1000, 'soldiers': -50},
                description="Ordunun ve Yeniçerinin sevdiği güçlü adaya asker desteği verdiniz."
            ),
            EventChoice(
                text="Tarafsız kal",
                effects={'happiness': -5, 'trade_modifier': -10},
                description="Merkezin gazabından korkup sessiz kaldınız. Ticaret durma noktasına geldi."
            )
        ]
    ),
    Event(
        id="succession_chain_2_civil_war",
        title="Kanlı Çarpışmalar",
        description="Şehzade orduları karşı karşıya geldi. Desteklediğiniz adayın durumu kritik.",
        event_type=EventType.MILITARY,
        severity=EventSeverity.CRITICAL,
        chain_id="succession_chain",
        choices=[
            EventChoice(
                text="Bütün ordularla desteğe git",
                effects={'gold': -800, 'soldiers': -200, 'unrest': 15},
                description="Kendinizi ateşe attınız. Zafer ya da ölüm!"
            ),
            EventChoice(
                text="Sınırları koru",
                effects={'happiness': 5},
                description="Kavgadan uzak durup eyaletin güvenliğine odaklandınız."
            )
        ]
    ),
    Event(
        id="succession_chain_3_result",
        title="Yeni Padişah Cülusu",
        description="Kanlı mücadele bitti ve yeni Padişah tahta çıktı. Sizin tarafınızdaki duruşunuz değerlendirilecek.",
        event_type=EventType.DIPLOMATIC,
        severity=EventSeverity.MAJOR,
        chain_id="succession_chain",
        choices=[
            EventChoice(
                text="Biat törenine katıl",
                effects={'gold': -300, 'happiness': 15},
                description="Yeni padişaha sadakatinizi bildirdiniz. Cülus bahşişleri dağıtıldı."
            )
        ]
    )
]

EVENT_POOL.extend(CELALI_EVENTS + SUCCESSION_EVENTS)

# Genişletilmiş olayları dahil et
try:
    from game.systems.events_expanded import get_expanded_events
    EVENT_POOL.extend(get_expanded_events())
except ImportError:
    pass  # events_expanded.py henüz yok


class EventSystem:
    """Olay yönetim sistemi"""
    
    def __init__(self):
        self.current_event: Optional[Event] = None
        self.current_stage: Optional[str] = None  # Çok aşamalı olaylar için
        self.event_history: List[str] = []
        self.events_this_year: int = 0
        self.max_events_per_year: int = 5
        
        # YENİ: Olay hafızası - seçimlerin kalıcı etkileri
        self.event_memory: Dict[str, any] = {}
        
        # YENİ: Bekleyen zincir tetikleyiciler
        self.pending_triggers: List[ChainTrigger] = []
        
        # YENİ: Aktif olay zincirleri
        self.active_chains: Dict[str, EventChain] = {}
        
        # Olay ağırlıkları
        self.event_weights = {
            EventType.ECONOMIC: 25,
            EventType.MILITARY: 20,
            EventType.POPULATION: 20,
            EventType.DIPLOMATIC: 15,
            EventType.NATURAL: 10,
            EventType.OPPORTUNITY: 10,
        }
        
        # Oyuncu unvanı (olay duyurularında kişiselleştirme)
        self.player_title: Optional[str] = None
    
    def check_for_event(self, year: int, game_state: dict) -> Optional[Event]:
        """
        Olay kontrolü yap
        Returns: Event veya None
        """
        if self.current_event:
            return None
        
        # YENİ: Önce bekleyen zincir tetikleyicileri kontrol et
        triggered_event = self._check_pending_triggers()
        if triggered_event:
            self.current_event = triggered_event
            self.events_this_year += 1
            return triggered_event
        
        if self.events_this_year >= self.max_events_per_year:
            return None
        
        # Olay şansı (%40 base + duruma göre)
        base_chance = 40
        
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
        
        # Bu türden uygun olay seç (hafıza koşullarını da kontrol et)
        # Oyuncu cinsiyetini ve unvanını al
        player_gender = game_state.get('player_gender', 'male')
        current_turn = game_state.get('turn_count', 0)
        self.player_title = game_state.get('player_title', None)
        
        candidates = [
            e for e in EVENT_POOL 
            if e.event_type == event_type
            and e.min_year <= year <= e.max_year
            and e.min_turn <= current_turn  # Minimum tur kontrolü
            and e.id not in self.event_history[-5:]  # Son 5 olayda tekrar yok
            and self._check_memory_requirements(e)  # Hafıza koşulları
            and (e.gender_filter is None or e.gender_filter == player_gender)  # Cinsiyet filtresi
        ]
        
        if not candidates:
            return None
        
        event = random.choice(candidates)
        self.current_event = event
        self.events_this_year += 1
        
        return event
    
    def _check_pending_triggers(self) -> Optional[Event]:
        """Bekleyen tetikleyicileri kontrol et ve uygun olanı döndür"""
        for trigger in self.pending_triggers[:]:  # Kopya üzerinde iterasyon
            trigger.turns_remaining -= 1
            if trigger.turns_remaining <= 0:
                # Bu tetikleyiciyi kaldır
                self.pending_triggers.remove(trigger)
                
                # Hafıza güncellemelerini uygula
                if trigger.memory_updates:
                    self.event_memory.update(trigger.memory_updates)
                
                # Olayı bul ve döndür
                for event in EVENT_POOL:
                    if event.id == trigger.event_id:
                        return event
        return None
    
    def _check_memory_requirements(self, event: Event) -> bool:
        """Olayın hafıza gereksinimlerini kontrol et"""
        if not event.required_memory:
            return True
        
        for key, required_value in event.required_memory.items():
            actual_value = self.event_memory.get(key)
            if actual_value != required_value:
                return False
        return True
    
    def add_trigger(self, event_id: str, delay: int, source_event: str, 
                   choice: str, memory_updates: Dict = None):
        """Yeni zincir tetikleyici ekle"""
        trigger = ChainTrigger(
            event_id=event_id,
            turns_remaining=delay,
            source_event_id=source_event,
            choice_made=choice,
            memory_updates=memory_updates
        )
        self.pending_triggers.append(trigger)
    
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
        
        # YENİ: Zincir olay işleme
        self._process_chain_event(self.current_event, choice_index)
        
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
    
    def _process_chain_event(self, event: Event, choice_index: int):
        """Zincir olay mantığını işle - seçime göre sonraki olayı tetikle"""
        if not event.chain_id:
            return
        
        chain_id = event.chain_id
        choice_text = event.choices[choice_index].text if choice_index < len(event.choices) else ""
        
        # === VEBA ZİNCİRİ ===
        if event.id == "plague_chain_1_signs":
            self.event_memory['plague_started'] = True
            if choice_index == 0:  # Karantina
                self.event_memory['plague_quarantine'] = True
                self.add_trigger("plague_chain_2_contained", 3, event.id, choice_text,
                               {'plague_handling': 'quarantine'})
            elif choice_index == 1:  # Hekimler
                self.event_memory['plague_quarantine'] = False
                self.add_trigger("plague_chain_2_spread", 4, event.id, choice_text,
                               {'plague_handling': 'doctors'})
            else:  # Bekle
                self.event_memory['plague_quarantine'] = False
                self.add_trigger("plague_chain_2_spread", 2, event.id, choice_text,
                               {'plague_handling': 'waited'})
        
        elif event.id in ["plague_chain_2_spread", "plague_chain_2_contained"]:
            self.add_trigger("plague_chain_3_peak", 3, event.id, choice_text)
        
        elif event.id == "plague_chain_3_peak":
            self.add_trigger("plague_chain_4_end", 4, event.id, choice_text)
            
        elif event.id == "plague_chain_4_end":
            self.event_memory['plague_resolved'] = True
        
        # === YENİÇERİ ZİNCİRİ ===
        elif event.id == "janissary_chain_1_demand":
            if choice_index == 0:  # Maaş artır - zincir biter
                self.event_memory['janissary_resolved'] = True
            elif choice_index == 1:  # Söz ver
                self.event_memory['janissary_angry'] = True
                self.add_trigger("janissary_chain_2_unrest", 5, event.id, choice_text)
            else:  # Reddet
                self.event_memory['janissary_angry'] = True
                self.add_trigger("janissary_chain_2_unrest", 2, event.id, choice_text)
        
        elif event.id == "janissary_chain_2_unrest":
            if choice_index == 0:  # Hemen maaş - zincir biter
                self.event_memory['janissary_resolved'] = True
            elif choice_index == 1:  # Sadık birlikler
                self.event_memory['janissary_revolt'] = True
                self.add_trigger("janissary_chain_3_revolt", 2, event.id, choice_text)
            else:  # Kaç
                self.event_memory['janissary_revolt'] = True
                self.add_trigger("janissary_chain_3_revolt", 1, event.id, choice_text)
        
        elif event.id == "janissary_chain_3_revolt":
            self.event_memory['janissary_resolved'] = True
            self.add_trigger("janissary_chain_4_aftermath", 2, event.id, choice_text)
            
        elif event.id == "janissary_chain_4_aftermath":
            self.event_memory['janissary_resolved'] = True
        
        # === İPEK YOLU ZİNCİRİ ===
        elif event.id == "silkroad_chain_1_offer":
            if choice_index in [0, 1]:  # Yatırım yaptı
                self.event_memory['silkroad_invested'] = True
                self.event_memory['silkroad_big_investment'] = (choice_index == 0)
                self.add_trigger("silkroad_chain_2_journey", 5, event.id, choice_text)
            else:
                self.event_memory['silkroad_resolved'] = True
        
        elif event.id == "silkroad_chain_2_journey":
            self.add_trigger("silkroad_chain_3_return", 4, event.id, choice_text,
                           {'silkroad_protected': choice_index == 0})
                           
        elif event.id == "silkroad_chain_3_return":
            self.event_memory['silkroad_resolved'] = True
        
        # === PADİŞAH ZİYARETİ ZİNCİRİ ===
        elif event.id == "sultan_chain_1_news":
            if choice_index != 2:  # Erteleme değilse
                self.event_memory['sultan_visit'] = True
                self.event_memory['sultan_grand'] = (choice_index == 0)
                self.add_trigger("sultan_chain_2_preparation", 3, event.id, choice_text)
            else:
                self.event_memory['sultan_visited'] = True
        
        elif event.id == "sultan_chain_2_preparation":
            self.add_trigger("sultan_chain_3_visit", 3, event.id, choice_text)
        
        elif event.id == "sultan_chain_3_visit":
            self.add_trigger("sultan_chain_4_aftermath", 2, event.id, choice_text)
            
        elif event.id == "sultan_chain_4_aftermath":
            self.event_memory['sultan_visited'] = True
        
        # === FETİH SEFERİ ZİNCİRİ ===
        elif event.id == "conquest_chain_1_call":
            if choice_index in [0, 1]:  # Katıldı
                self.event_memory['conquest_joined'] = True
                self.event_memory['conquest_big_army'] = (choice_index == 0)
                self.add_trigger("conquest_chain_2_march", 4, event.id, choice_text)
            else:
                self.event_memory['conquest_completed'] = True
        
        elif event.id == "conquest_chain_2_march":
            self.add_trigger("conquest_chain_3_siege", 5, event.id, choice_text)
        
        elif event.id == "conquest_chain_3_siege":
            self.add_trigger("conquest_chain_4_battle", 4, event.id, choice_text)
        
        elif event.id == "conquest_chain_4_battle":
            self.event_memory['conquest_victory'] = True
            self.add_trigger("conquest_chain_5_spoils", 2, event.id, choice_text)
            
        elif event.id == "conquest_chain_5_spoils":
            self.event_memory['conquest_completed'] = True
            
        # === CELALİ İSYANI ZİNCİRİ ===
        elif event.id == "celali_chain_1_rumors":
            self.event_memory['celali_active'] = True
            if choice_index == 0:  # Ez
                self.add_trigger("celali_chain_2_uprising", 5, event.id, choice_text, {'celali_handling': 'brute_force'})
            elif choice_index == 1:  # Rüşvet
                self.add_trigger("celali_chain_2_uprising", 8, event.id, choice_text, {'celali_handling': 'bribe'})
            else:  # Bekle
                self.add_trigger("celali_chain_2_uprising", 3, event.id, choice_text, {'celali_handling': 'waited'})
                
        elif event.id == "celali_chain_2_uprising":
            self.add_trigger("celali_chain_3_climax", 4, event.id, choice_text)
            
        elif event.id == "celali_chain_3_climax":
            self.event_memory['celali_resolved'] = True
            
        # === TAHT KAVGALARI ZİNCİRİ ===
        elif event.id == "succession_chain_1_news":
            self.event_memory['succession_crisis'] = True
            if choice_index == 0:
                self.event_memory['succession_side'] = 'elder'
            elif choice_index == 1:
                self.event_memory['succession_side'] = 'strong'
            else:
                self.event_memory['succession_side'] = 'neutral'
            self.add_trigger("succession_chain_2_civil_war", 3, event.id, choice_text)
            
        elif event.id == "succession_chain_2_civil_war":
            self.add_trigger("succession_chain_3_result", 3, event.id, choice_text)
            
        elif event.id == "succession_chain_3_result":
            self.event_memory['succession_resolved'] = True
            # Ekstra sonuç: Eğer taraf seçildiyse sadakat bonusu/malusu
            side = self.event_memory.get('succession_side', 'neutral')
            if side == 'strong':
                self.event_memory['succession_loyalty_boost'] = True
    
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
        
        # Kişiselleştirilmiş duyuru
        if self.player_title:
            audio.announce(f"{self.player_title}! {severity} Olay: {self.current_event.title}")
        else:
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
        # Pending triggers'ı serileştir
        triggers_data = []
        for trigger in self.pending_triggers:
            triggers_data.append({
                'event_id': trigger.event_id,
                'turns_remaining': trigger.turns_remaining,
                'source_event_id': trigger.source_event_id,
                'choice_made': trigger.choice_made,
                'memory_updates': trigger.memory_updates
            })
        
        return {
            'event_history': self.event_history,
            'events_this_year': self.events_this_year,
            'current_event_id': self.current_event.id if self.current_event else None,
            'event_memory': self.event_memory,  # YENİ
            'pending_triggers': triggers_data,  # YENİ
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'EventSystem':
        """Dictionary'den yükle"""
        system = cls()
        system.event_history = data.get('event_history', [])
        system.events_this_year = data.get('events_this_year', 0)
        
        # YENİ: Event memory'yi yükle
        system.event_memory = data.get('event_memory', {})
        
        # YENİ: Pending triggers'ı yükle
        for trigger_data in data.get('pending_triggers', []):
            trigger = ChainTrigger(
                event_id=trigger_data['event_id'],
                turns_remaining=trigger_data['turns_remaining'],
                source_event_id=trigger_data['source_event_id'],
                choice_made=trigger_data['choice_made'],
                memory_updates=trigger_data.get('memory_updates')
            )
            system.pending_triggers.append(trigger)
        
        # Aktif olayı geri yükle
        current_id = data.get('current_event_id')
        if current_id:
            for event in EVENT_POOL:
                if event.id == current_id:
                    system.current_event = event
                    break
        
        return system
