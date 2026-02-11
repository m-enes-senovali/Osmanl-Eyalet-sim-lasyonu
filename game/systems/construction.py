# -*- coding: utf-8 -*-
"""
Osmanlı Eyalet Yönetim Simülasyonu - İnşaat Sistemi
1520 Dönemi Tarihi Gerçekliğine Uygun - Gelişmiş Bina Mekanikleri

Bina Kategorileri:
- Dini: Cami, Medrese, Tabhane
- Askeri: Ocak, Kale, Topçu Ocağı, Gözetleme Kulesi
- Ekonomi: Çarşı, Kervansaray, Han, Bedesten, Darphane
- Altyapı: Çiftlik, Maden, Kereste Ocağı, Taş Ocağı, Ambar, Su Kemeri, Tersane, Halat Atölyesi
- Sosyal: Darüşşifa, Hamam
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from enum import Enum
from audio.audio_manager import get_audio_manager


class BuildingCategory(Enum):
    """Bina kategorileri"""
    DINI = "dini"           # Dini yapılar
    ASKERI = "askeri"       # Askeri yapılar
    EKONOMI = "ekonomi"     # Ekonomik yapılar
    ALTYAPI = "altyapi"     # Altyapı yapıları
    SOSYAL = "sosyal"       # Sosyal yapılar


class BuildingType(Enum):
    """Bina tipleri"""
    # Dini
    MOSQUE = "mosque"              # Cami
    MEDRESE = "medrese"            # Medrese (eğitim)
    TABHANE = "tabhane"            # Tabhane (misafirhane) 🆕
    # Askeri
    BARRACKS = "barracks"          # Ocak
    FORTRESS = "fortress"          # Kale
    ARTILLERY_FOUNDRY = "artillery_foundry"  # Topçu Ocağı
    WATCHTOWER = "watchtower"      # Gözetleme Kulesi 🆕
    # Ekonomi
    MARKET = "market"              # Pazar/Çarşı
    CARAVANSERAI = "caravanserai"  # Kervansaray
    INN = "inn"                    # Han
    BEDESTEN = "bedesten"          # Bedesten (kapalı çarşı) 🆕
    MINT = "mint"                  # Darphane 🆕
    # Altyapı
    FARM = "farm"                  # Çiftlik
    MINE = "mine"                  # Maden
    LUMBER_MILL = "lumber_mill"    # Kereste Ocağı
    QUARRY = "quarry"              # Taş Ocağı
    WAREHOUSE = "warehouse"        # Ambar
    AQUEDUCT = "aqueduct"          # Su Kemeri 🆕
    SHIPYARD = "shipyard"          # Tersane
    ROPEMAKER = "ropemaker"        # Halat Atölyesi
    # Sosyal
    HOSPITAL = "hospital"          # Darüşşifa (hastane)
    BATH = "bath"                  # Hamam


@dataclass
class BuildingStats:
    """Bina istatistikleri - Gelişmiş"""
    name: str
    name_tr: str
    description: str
    cost_gold: int
    cost_wood: int
    cost_iron: int
    maintenance: int        # Tur başına bakım
    build_time: int         # İnşaat süresi (tur)
    max_level: int          # Maksimum yükseltme seviyesi
    category: BuildingCategory = BuildingCategory.ALTYAPI
    
    # Temel etkiler
    happiness_bonus: int = 0
    trade_bonus: int = 0
    military_bonus: int = 0
    food_production: int = 0
    resource_production: Dict = None
    requires_coastal: bool = False
    
    # Gelişmiş etkiler
    unique_effects: Dict = None         # Binanın özel mekanikleri
    prerequisite: str = None            # Ön koşul bina (BuildingType.value)
    synergy_with: List = None           # Sinerji sağlayan binalar
    synergy_bonus_desc: str = ""        # Sinerji açıklaması
    historical_desc: str = ""           # Tarihi bağlam (1520)
    level_names: List = None            # Seviye isimleri (ör: Mescit → Cami → Ulu Cami)


BUILDING_DEFINITIONS = {
    # ═══════════════════════════════════════════════════
    # DİNİ YAPILAR
    # ═══════════════════════════════════════════════════
    BuildingType.MOSQUE: BuildingStats(
        name="Mosque",
        name_tr="Cami",
        description="İbadet, toplumsal birlik ve meşruiyet kaynağı",
        cost_gold=1000,
        cost_wood=200,
        cost_iron=50,
        maintenance=20,
        build_time=3,
        max_level=5,
        category=BuildingCategory.DINI,
        happiness_bonus=10,
        synergy_with=["medrese", "tabhane"],
        synergy_bonus_desc="Medrese ile: eğitim +%15. Tabhane ile: dindarlık +%15",
        historical_desc="Osmanlı şehir hayatının merkezi. Külliye sisteminin çekirdeği olarak etrafında medrese, imaret, hamam gibi yapılar inşa edilirdi.",
        level_names=["Mescit", "Cami", "Ulu Cami", "Külliye", "Selatin Camii"],
        unique_effects={
            'piety': 5,           # Dindarlık artışı
            'legitimacy': 3,      # Meşruiyet artışı
            'unrest_reduction': 2  # Huzursuzluk azaltma
        }
    ),
    BuildingType.MEDRESE: BuildingStats(
        name="Medrese",
        name_tr="Medrese",
        description="İslami ilimler, hukuk ve tıp eğitimi merkezi",
        cost_gold=800,
        cost_wood=150,
        cost_iron=30,
        maintenance=15,
        build_time=2,
        max_level=5,
        category=BuildingCategory.DINI,
        happiness_bonus=5,
        prerequisite="mosque",
        synergy_with=["mosque", "hospital"],
        synergy_bonus_desc="Cami ile: ulema kapasitesi +2. Darüşşifa ile: bilim +%15",
        historical_desc="Sahn-ı Seman medreseleri Osmanlı'nın en prestijli eğitim kurumlarıydı. Kadı, müderris ve hekim yetiştirirlerdi.",
        level_names=["Sıbyan Mektebi", "Medrese", "Darülhadis", "Sahn Medresesi", "Süleymaniye Medresesi"],
        unique_effects={
            'education': 10,       # Eğitim artışı
            'ulema_capacity': 3,   # Daha fazla ulema atanabilir
            'science': 5,          # Bilim katkısı
            'kizilbas_reduction': 2  # Dini eğitim Kızılbaş tehditini azaltır
        }
    ),
    BuildingType.TABHANE: BuildingStats(
        name="Guesthouse",
        name_tr="Tabhane",
        description="Gezgin alimler, dervişler ve misafirler için konaklama",
        cost_gold=600,
        cost_wood=120,
        cost_iron=20,
        maintenance=12,
        build_time=2,
        max_level=3,
        category=BuildingCategory.DINI,
        happiness_bonus=5,
        prerequisite="mosque",
        synergy_with=["mosque", "caravanserai"],
        synergy_bonus_desc="Cami ile: dindarlık +%15. Kervansaray ile: kültürel gelir +%10",
        historical_desc="Külliye bünyesinde yolcuların üç gün ücretsiz ağırlandığı yer. Fatih Külliyesi'ndeki tabhane meşhurdur.",
        level_names=["Misafirhane", "Tabhane", "Dervişhane"],
        unique_effects={
            'piety': 3,
            'foreign_scholar': 2,   # Yabancı alim çekme
            'happiness': 3
        }
    ),

    # ═══════════════════════════════════════════════════
    # ASKERİ YAPILAR
    # ═══════════════════════════════════════════════════
    BuildingType.BARRACKS: BuildingStats(
        name="Barracks",
        name_tr="Ocak",
        description="Asker yetiştirilir ve barınır (Kapıkulu Ocağı)",
        cost_gold=1500,
        cost_wood=300,
        cost_iron=200,
        maintenance=30,
        build_time=4,
        max_level=5,
        category=BuildingCategory.ASKERI,
        military_bonus=20,
        synergy_with=["fortress", "artillery_foundry"],
        synergy_bonus_desc="Kale ile: moral +%15. Topçu Ocağı ile: eğitim hızı +%15",
        historical_desc="Acemi Ocağı'nda devşirme çocuklar eğitilir, ardından Yeniçeri Ocağı'na alınırdı. Ocak, askerlerin evi ve ailesi sayılırdı.",
        level_names=["Acemi Ocağı", "Yeniçeri Ocağı", "Ağa Kapısı", "Merkez Ocağı", "Hassa Ocağı"],
        unique_effects={
            'train_speed': 1,       # Eğitim süresi azaltma (tur)
            'morale': 5,            # Moral artışı
            'unit_capacity': 50     # Ek asker kapasitesi
        }
    ),
    BuildingType.FORTRESS: BuildingStats(
        name="Fortress",
        name_tr="Kale",
        description="Eyaletin ana savunma yapısı, kuşatmalara direnç sağlar",
        cost_gold=3000,
        cost_wood=500,
        cost_iron=400,
        maintenance=50,
        build_time=6,
        max_level=5,
        category=BuildingCategory.ASKERI,
        military_bonus=50,
        synergy_with=["barracks", "watchtower"],
        synergy_bonus_desc="Ocak ile: garnizon kapasitesi +%20. Gözetleme Kulesi ile: erken uyarı",
        historical_desc="Osmanlı sınır kaleleri (uç kaleleri) düşmana karşı ilk savunma hattıydı. Kale dizdarı tarafından yönetilirdi.",
        level_names=["Palanka", "Hisar", "Kale", "İç Kale", "Citadel"],
        unique_effects={
            'defense': 30,           # Savunma gücü
            'siege_resistance': 20,  # Kuşatma direnci
            'garrison_capacity': 100 # Garnizon kapasitesi
        }
    ),
    BuildingType.ARTILLERY_FOUNDRY: BuildingStats(
        name="Artillery Foundry",
        name_tr="Topçu Ocağı",
        description="Top üretimi - Darbzen, Balyemez, Kolunburna ve Şahi topları",
        cost_gold=2500,
        cost_wood=300,
        cost_iron=400,
        maintenance=50,
        build_time=6,
        max_level=5,
        category=BuildingCategory.ASKERI,
        military_bonus=50,
        prerequisite="barracks",
        synergy_with=["barracks", "mine", "fortress"],
        synergy_bonus_desc="Ocak ile: top mürettebatı kalitesi +%15. Maden ile: üretim hızı +%20",
        historical_desc="Tophane-i Amire'nin taşra kolu. Osmanlı topçuluğu 1453 İstanbul kuşatmasından beri Avrupa'nın en gelişmişiydi.",
        level_names=["Dökümhane", "Tophane", "Topçu Ocağı", "Büyük Tophane", "Tophane-i Amire"],
        unique_effects={
            'siege_power': 25,        # Kuşatma gücü
            'artillery_production': 1  # Tur başına top üretim kapasitesi
        }
    ),
    BuildingType.WATCHTOWER: BuildingStats(
        name="Watchtower",
        name_tr="Gözetleme Kulesi",
        description="Düşman hareketlerini erken tespit eder, casuslara karşı koruma sağlar",
        cost_gold=800,
        cost_wood=200,
        cost_iron=100,
        maintenance=12,
        build_time=2,
        max_level=3,
        category=BuildingCategory.ASKERI,
        military_bonus=10,
        prerequisite="fortress",
        synergy_with=["fortress"],
        synergy_bonus_desc="Kale ile: erken uyarı sistemi aktif",
        historical_desc="Sınır boylarında düşman hareketlerini izleyen kuleler. Ateş yakarak haberleşirlerdi.",
        level_names=["Bekçi Kulesi", "Gözetleme Kulesi", "İleri Karakol"],
        unique_effects={
            'espionage_defense': 15,  # Casusluk savunması
            'early_warning': 1,       # Erken uyarı (savaş bildirimi)
            'scout_range': 2          # Keşif menzili
        }
    ),

    # ═══════════════════════════════════════════════════
    # EKONOMİK YAPILAR
    # ═══════════════════════════════════════════════════
    BuildingType.MARKET: BuildingStats(
        name="Market",
        name_tr="Çarşı",
        description="Ticaret merkezi, esnaf loncalarının toplandığı yer",
        cost_gold=600,
        cost_wood=100,
        cost_iron=20,
        maintenance=10,
        build_time=2,
        max_level=5,
        category=BuildingCategory.EKONOMI,
        trade_bonus=150,
        synergy_with=["inn", "caravanserai", "bedesten"],
        synergy_bonus_desc="Han ile: gelir +%15. Bedesten ile: lüks ticaret +%20",
        historical_desc="Osmanlı çarşıları lonca sistemiyle yönetilirdi. Her esnaf kendi sokağında çalışırdı. Muhtesip (zabıta) fiyat ve kalite denetimi yapardı.",
        level_names=["Pazar Yeri", "Çarşı", "Arasta", "Büyük Çarşı", "Kapalıçarşı"],
        unique_effects={
            'gold_per_turn': 5,       # Tur başına ek altın
            'price_stability': 5,     # Fiyat istikrarı
            'employment': 50          # İstihdam
        }
    ),
    BuildingType.CARAVANSERAI: BuildingStats(
        name="Caravanserai",
        name_tr="Kervansaray",
        description="Kervan tüccarlarına konaklama ve güvenlik sağlar",
        cost_gold=1200,
        cost_wood=250,
        cost_iron=50,
        maintenance=25,
        build_time=3,
        max_level=5,
        category=BuildingCategory.EKONOMI,
        trade_bonus=300,
        prerequisite="market",
        synergy_with=["market", "inn", "tabhane"],
        synergy_bonus_desc="Han ile: kervan geliri +%20. Çarşı ile: ticaret güvenliği +%15",
        historical_desc="Kervanların güvenli konakladığı yapılardı. Osmanlı topraklarında her 30-40 km'de bir kervansaray bulunurdu.",
        level_names=["Menzilhane", "Kervansaray", "Büyük Han", "Sultan Hanı", "Selatin Kervansarayı"],
        unique_effects={
            'caravan_safety': 15,      # Kervan güvenliği
            'trade_routes': 1,         # Ek ticaret yolu kapasitesi
            'foreign_income': 10       # Yabancı tüccar geliri
        }
    ),
    BuildingType.INN: BuildingStats(
        name="Inn",
        name_tr="Han",
        description="Tüccar ve yolcuların konakladığı ticari yapı",
        cost_gold=600,
        cost_wood=200,
        cost_iron=30,
        maintenance=12,
        build_time=2,
        max_level=5,
        category=BuildingCategory.EKONOMI,
        happiness_bonus=3,
        prerequisite="market",
        synergy_with=["market", "caravanserai"],
        synergy_bonus_desc="Çarşı ile: nüfus artışı +%15. Kervansaray ile: kervan geliri +%20",
        historical_desc="Şehir içi ticari han. Alt katı dükkân ve depo, üst katı konaklama olarak kullanılırdı.",
        level_names=["Küçük Han", "Han", "Büyük Han", "Çifte Han", "Vezir Hanı"],
        unique_effects={
            'population_growth': 2,    # Nüfus artışı bonusu
            'caravan_income': 5,       # Kervan geliri
            'happiness': 3
        }
    ),
    BuildingType.BEDESTEN: BuildingStats(
        name="Covered Market",
        name_tr="Bedesten",
        description="Değerli malların güvenle satıldığı kapalı çarşı, bankerlik merkezi",
        cost_gold=1800,
        cost_wood=300,
        cost_iron=150,
        maintenance=30,
        build_time=4,
        max_level=3,
        category=BuildingCategory.EKONOMI,
        trade_bonus=400,
        prerequisite="market",
        synergy_with=["market", "caravanserai", "mint"],
        synergy_bonus_desc="Çarşı ile: lüks ticaret +%20. Darphane ile: finansal güç +%15",
        historical_desc="İstanbul Kapalıçarşısı'nın çekirdeği olan Bedesten, mücevher, ipek ve değerli kumaşların satıldığı güvenli yapıydı.",
        level_names=["Sandık Odası", "Bedesten", "Büyük Bedesten"],
        unique_effects={
            'luxury_trade': 15,       # Lüks mal ticareti geliri
            'gold_per_turn': 10,      # Tur başına ek altın
            'price_stability': 10,    # Fiyat istikrarı
            'banking': 5              # Sarraflık/bankerlik geliri
        }
    ),
    BuildingType.MINT: BuildingStats(
        name="Mint",
        name_tr="Darphane",
        description="Akçe ve sikke basımı - devletin mali gücünün simgesi",
        cost_gold=2000,
        cost_wood=150,
        cost_iron=300,
        maintenance=35,
        build_time=4,
        max_level=3,
        category=BuildingCategory.EKONOMI,
        prerequisite="mine",
        synergy_with=["mine", "bedesten"],
        synergy_bonus_desc="Maden ile: sikke üretimi +%25. Bedesten ile: finansal güç +%15",
        historical_desc="Darphane-i Amire İstanbul'daydı. Taşra darphaneleri de eyaletlerde sikke basardı. Akçe gümüş, sultani altın sikkeydi.",
        level_names=["Sikke Atölyesi", "Darphane", "Büyük Darphane"],
        unique_effects={
            'gold_per_turn': 15,      # Tur başına ek altın
            'inflation_control': 10,  # Enflasyon kontrolü
            'legitimacy': 5           # Para basma hakkı = meşruiyet
        }
    ),

    # ═══════════════════════════════════════════════════
    # ALTYAPI YAPILARI
    # ═══════════════════════════════════════════════════
    BuildingType.FARM: BuildingStats(
        name="Farm",
        name_tr="Çiftlik",
        description="Tahıl, sebze ve meyve üretimi - halkın temel gıda kaynağı",
        cost_gold=300,
        cost_wood=150,
        cost_iron=10,
        maintenance=5,
        build_time=2,
        max_level=5,
        category=BuildingCategory.ALTYAPI,
        food_production=600,
        synergy_with=["warehouse", "aqueduct"],
        synergy_bonus_desc="Ambar ile: zahire israfı -%15. Su Kemeri ile: verim +%25",
        historical_desc="Tımar sistemiyle yönetilen çiftlikler, hem asker besler hem devlete gelir sağlardı. Has, zeamet ve tımar olarak üç sınıftı.",
        level_names=["Tarla", "Çiftlik", "Has Çiftliği", "Büyük Çiftlik", "Sultan Çiftliği"],
        unique_effects={
            'farmer_efficiency': 5,    # Çiftçi verimliliği %
            'seasonal_bonus': 10       # Mevsimsel hasat bonusu
        }
    ),
    BuildingType.MINE: BuildingStats(
        name="Mine",
        name_tr="Maden",
        description="Demir, bakır ve gümüş madenciliği",
        cost_gold=800,
        cost_wood=200,
        cost_iron=50,
        maintenance=20,
        build_time=3,
        max_level=5,
        category=BuildingCategory.ALTYAPI,
        synergy_with=["quarry", "mint", "artillery_foundry"],
        synergy_bonus_desc="Taş Ocağı ile: üretim +%15. Darphane ile: sikke basımı. Topçu Ocağı ile: top malzemesi",
        historical_desc="Osmanlı madencilik geliri önemliydi. Srebrenica gümüş madenleri, Küre bakır madenleri devletin önemli gelir kaynaklarıydı.",
        level_names=["Ocak", "Maden", "Büyük Maden", "Has Madeni", "Sultan Madeni"],
        unique_effects={
            'iron_production': 150,
            'gold_from_ore': 3         # Cevherden ek altın geliri
        }
    ),
    BuildingType.LUMBER_MILL: BuildingStats(
        name="Lumber Mill",
        name_tr="Kereste Ocağı",
        description="Kereste üretimi - inşaat ve gemi yapımının temeli",
        cost_gold=500,
        cost_wood=50,
        cost_iron=100,
        maintenance=15,
        build_time=2,
        max_level=5,
        category=BuildingCategory.ALTYAPI,
        synergy_with=["shipyard"],
        synergy_bonus_desc="Tersane ile: gemi inşa hızı +%20",
        historical_desc="Osmanlı tersaneleri için kereste kritik önemdeydi. Karadeniz ormanları ana kereste kaynağıydı.",
        level_names=["Balta Gücü", "Kereste Ocağı", "Şeritçi Atölyesi", "Büyük Kereste Ocağı", "Has Ormanı"],
        unique_effects={
            'wood_production': 300,
            'build_speed': 1           # İnşaat hızı bonusu (tur azaltma)
        }
    ),
    BuildingType.QUARRY: BuildingStats(
        name="Quarry",
        name_tr="Taş Ocağı",
        description="Kesme taş ve mermer üretimi - kalıcı yapıların temeli",
        cost_gold=800,
        cost_wood=200,
        cost_iron=50,
        maintenance=20,
        build_time=3,
        max_level=5,
        category=BuildingCategory.ALTYAPI,
        synergy_with=["fortress", "mine"],
        synergy_bonus_desc="Kale ile: dayanıklılık +%20. Maden ile: üretim +%15",
        historical_desc="Marmara adalarının mermerleri Osmanlı'nın en değerli yapı taşıydı. Küfeki taşı İstanbul'un simgesiydi.",
        level_names=["Taş Kırağı", "Taş Ocağı", "Mermer Ocağı", "Büyük Taş Ocağı", "Has Ocak"],
        unique_effects={
            'stone_production': 100,
            'iron_bonus': 100,         # Ek demir üretimi
            'building_durability': 5   # Bina dayanıklılığı %
        }
    ),
    BuildingType.WAREHOUSE: BuildingStats(
        name="Warehouse",
        name_tr="Ambar",
        description="Zahire ve kaynak depolama - kıtlığa karşı güvence",
        cost_gold=400,
        cost_wood=300,
        cost_iron=50,
        maintenance=5,
        build_time=2,
        max_level=5,
        category=BuildingCategory.ALTYAPI,
        synergy_with=["farm"],
        synergy_bonus_desc="Çiftlik ile: zahire israfı -%15",
        historical_desc="Unkapanı ve Yağkapanı gibi büyük ambarlar şehirlerin hayat damarıydı. Kıtlık zamanlarında stratejik önem taşırdı.",
        level_names=["Depo", "Ambar", "Büyük Ambar", "Anbar-ı Amire", "Has Ambar"],
        unique_effects={
            'resource_capacity': 5000,  # Kaynak kapasitesi bonusu
            'pop_capacity': 3000,       # Nüfus kapasitesi bonusu
            'famine_resistance': 10     # Kıtlık direnci %
        }
    ),
    BuildingType.AQUEDUCT: BuildingStats(
        name="Aqueduct",
        name_tr="Su Kemeri",
        description="Şehre temiz su taşır - sağlık, tarım ve hijyen için hayati",
        cost_gold=1500,
        cost_wood=200,
        cost_iron=100,
        maintenance=20,
        build_time=4,
        max_level=3,
        category=BuildingCategory.ALTYAPI,
        happiness_bonus=5,
        synergy_with=["bath", "farm", "hospital"],
        synergy_bonus_desc="Hamam ile: hijyen +%25. Çiftlik ile: verim +%25. Darüşşifa ile: sağlık +%20",
        historical_desc="Mimar Sinan'ın Kırkçeşme ve Mağlova su kemerleri mühendislik harikaydı. 1520'de Kanuni dönemi su yatırımları başlamıştı.",
        level_names=["Çeşme", "Su Yolu", "Su Kemeri"],
        unique_effects={
            'health': 10,              # Sağlık artışı
            'farm_output_bonus': 15,   # Çiftlik verim bonusu %
            'pop_capacity': 5000,      # Su = daha fazla nüfus kapasitesi
            'plague_resistance': 10    # Veba direnci %
        }
    ),
    BuildingType.SHIPYARD: BuildingStats(
        name="Shipyard",
        name_tr="Tersane",
        description="Savaş gemisi ve ticaret gemisi inşası - deniz hakimiyetinin temeli",
        cost_gold=2000,
        cost_wood=500,
        cost_iron=200,
        maintenance=40,
        build_time=5,
        max_level=5,
        category=BuildingCategory.ALTYAPI,
        trade_bonus=500,
        military_bonus=30,
        requires_coastal=True,
        prerequisite="lumber_mill",
        synergy_with=["lumber_mill", "ropemaker"],
        synergy_bonus_desc="Kereste Ocağı ile: gemi inşa hızı +%20. Halat Atölyesi ile: gemi kalitesi +%15",
        historical_desc="Tersane-i Amire İstanbul'daki dev tersane. Galata'da yüzlerce gemi inşa edilirdi. Barbaros Hayrettin 1520'lerde donanmayı güçlendirdi.",
        level_names=["Çekek Yeri", "Tersane", "Büyük Tersane", "Amiral Tersanesi", "Tersane-i Amire"],
        unique_effects={
            'ship_build_speed': 1,     # Gemi inşa hızı
            'naval_capacity': 5,       # Donanma kapasitesi
            'sea_trade': 10            # Deniz ticareti geliri
        }
    ),
    BuildingType.ROPEMAKER: BuildingStats(
        name="Ropemaker",
        name_tr="Halat Atölyesi",
        description="Halat, katran ve yelken bezi üretir - gemi inşaatının olmazsa olmazı",
        cost_gold=800,
        cost_wood=200,
        cost_iron=30,
        maintenance=15,
        build_time=3,
        max_level=5,
        category=BuildingCategory.ALTYAPI,
        resource_production={'rope': 10, 'tar': 5, 'sailcloth': 3},
        requires_coastal=True,
        prerequisite="shipyard",
        synergy_with=["shipyard"],
        synergy_bonus_desc="Tersane ile: gemi kalitesi +%15",
        historical_desc="Tersane yanında kurulan atölyeler. Kenevir lifinden halat, çam reçinesinden katran üretilirdi.",
        level_names=["Kendir İşliği", "Halat Atölyesi", "Cebehane", "Büyük Atölye", "Has Atölye"],
        unique_effects={
            'ship_quality': 10,        # Gemi kalitesi
            'rope_production': 10,
            'tar_production': 5
        }
    ),

    # ═══════════════════════════════════════════════════
    # SOSYAL YAPILAR
    # ═══════════════════════════════════════════════════
    BuildingType.HOSPITAL: BuildingStats(
        name="Hospital",
        name_tr="Darüşşifa",
        description="Hastane ve tıp eğitimi merkezi - halkın şifa kaynağı",
        cost_gold=1500,
        cost_wood=200,
        cost_iron=100,
        maintenance=35,
        build_time=4,
        max_level=5,
        category=BuildingCategory.SOSYAL,
        happiness_bonus=10,
        prerequisite="medrese",
        synergy_with=["medrese", "bath", "aqueduct"],
        synergy_bonus_desc="Medrese ile: bilim +%15. Hamam ile: hijyen +%20. Su Kemeri ile: sağlık +%20",
        historical_desc="Darüşşifa'larda akıl hastaları bile müzikle tedavi edilirdi. Fatih ve Bayezid Darüşşifaları dönemin en gelişmiş hastaneleriydi.",
        level_names=["Şifahane", "Darüşşifa", "Bimarhane", "Büyük Darüşşifa", "Sultanî Darüşşifa"],
        unique_effects={
            'health': 15,              # Sağlık artışı
            'pop_capacity': 5000,      # Sağlıklı nüfus = daha fazla kapasite
            'plague_resistance': 15,   # Veba direnci %
            'science': 5               # Tıp bilimi katkısı
        }
    ),
    BuildingType.BATH: BuildingStats(
        name="Bath",
        name_tr="Hamam",
        description="Halk hamamı - hijyen, sosyal yaşam ve gelir kaynağı",
        cost_gold=400,
        cost_wood=80,
        cost_iron=20,
        maintenance=8,
        build_time=2,
        max_level=5,
        category=BuildingCategory.SOSYAL,
        happiness_bonus=5,
        synergy_with=["hospital", "aqueduct"],
        synergy_bonus_desc="Darüşşifa ile: hijyen +%20. Su Kemeri ile: kapasite +%25",
        historical_desc="Osmanlı hamamları hem hijyen hem sosyal merkezdiydi. Çifte hamam sistemiyle kadın ve erkek ayrı bölümlerde yıkanırdı.",
        level_names=["Küçük Hamam", "Hamam", "Çifte Hamam", "Büyük Hamam", "Sultan Hamamı"],
        unique_effects={
            'health': 5,               # Sağlık artışı
            'gold_income': 8,          # Hamam geliri
            'happiness': 5,
            'hygiene': 10              # Hijyen seviyesi
        }
    ),
}



@dataclass
class Building:
    """İnşa edilmiş bina"""
    building_type: BuildingType
    level: int = 1
    under_construction: bool = False
    construction_turns: int = 0
    
    def get_stats(self) -> BuildingStats:
        return BUILDING_DEFINITIONS[self.building_type]
    
    def get_effective_bonus(self, bonus_type: str) -> int:
        """Seviye bazlı etkin bonusu al"""
        stats = self.get_stats()
        base = getattr(stats, bonus_type, 0)
        return int(base * (1 + (self.level - 1) * 0.5))  # Her seviye %50 artış
    
    def get_level_name(self) -> str:
        """Binanın seviyesine göre tarihi ismini döndür"""
        stats = self.get_stats()
        if stats.level_names and self.level <= len(stats.level_names):
            return stats.level_names[self.level - 1]
        return f"Seviye {self.level}"
    
    def get_unique_effect(self, effect_name: str) -> int:
        """Binanın özel etkisini seviye bazlı döndür"""
        stats = self.get_stats()
        if stats.unique_effects and effect_name in stats.unique_effects:
            base = stats.unique_effects[effect_name]
            return int(base * (1 + (self.level - 1) * 0.3))  # Her seviye %30 artış
        return 0


@dataclass
class ConstructionQueue:
    """İnşaat kuyruğu öğesi"""
    building_type: BuildingType
    turns_remaining: int
    is_upgrade: bool = False


class ConstructionSystem:
    """İnşaat yönetim sistemi"""
    
    def __init__(self):
        # Mevcut binalar
        self.buildings: Dict[BuildingType, Building] = {}
        
        # İnşaat kuyruğu
        self.construction_queue: List[ConstructionQueue] = []
        
        # Başlangıç binaları
        self._initialize_starting_buildings()
    
    def _initialize_starting_buildings(self):
        """Başlangıç binalarını oluştur"""
        # Her eyalet bir cami ve çiftlik ile başlar
        self.buildings[BuildingType.MOSQUE] = Building(BuildingType.MOSQUE, level=1)
        self.buildings[BuildingType.FARM] = Building(BuildingType.FARM, level=1)
    
    def has_building(self, building_type: BuildingType) -> bool:
        """Bina var mı?"""
        return building_type in self.buildings
    
    def get_building_level(self, building_type: BuildingType) -> int:
        """Bina seviyesini al"""
        if building_type in self.buildings:
            return self.buildings[building_type].level
        return 0
    
    def check_prerequisite(self, building_type: BuildingType) -> tuple:
        """
        Ön koşul kontrolü
        Returns: (met: bool, reason: str)
        """
        stats = BUILDING_DEFINITIONS[building_type]
        if stats.prerequisite:
            prereq_type = BuildingType(stats.prerequisite)
            if prereq_type not in self.buildings:
                prereq_stats = BUILDING_DEFINITIONS[prereq_type]
                return False, f"Önce {prereq_stats.name_tr} inşa edilmeli"
        return True, ""
    
    def get_synergy_multiplier(self, building_type: BuildingType) -> float:
        """
        Sinerji bonusu çarpanı (mevcut sinerji binalarına göre)
        Her mevcut sinerji binası +%15 bonus verir
        """
        stats = BUILDING_DEFINITIONS[building_type]
        if not stats.synergy_with:
            return 1.0
        
        synergy_count = 0
        for synergy_value in stats.synergy_with:
            try:
                synergy_type = BuildingType(synergy_value)
                if synergy_type in self.buildings:
                    synergy_count += 1
            except ValueError:
                continue
        
        return 1.0 + (synergy_count * 0.15)
    
    def get_synergy_info(self, building_type: BuildingType) -> List[tuple]:
        """
        Sinerji bilgisi: [(bina_adı, var_mı), ...]
        """
        stats = BUILDING_DEFINITIONS[building_type]
        if not stats.synergy_with:
            return []
        
        result = []
        for synergy_value in stats.synergy_with:
            try:
                synergy_type = BuildingType(synergy_value)
                synergy_stats = BUILDING_DEFINITIONS[synergy_type]
                has_it = synergy_type in self.buildings
                result.append((synergy_stats.name_tr, has_it))
            except ValueError:
                continue
        return result
    
    def can_build(self, building_type: BuildingType, economy, is_coastal: bool = False) -> tuple:
        """
        İnşa edilebilir mi kontrol et
        Returns: (can_build: bool, reason: str)
        """
        # Zaten var mı?
        if building_type in self.buildings:
            return False, "Bu bina zaten mevcut"
        
        # İnşaat kuyruğunda mı?
        for item in self.construction_queue:
            if item.building_type == building_type:
                return False, "Bu bina zaten inşa ediliyor"
        
        stats = BUILDING_DEFINITIONS[building_type]
        
        # Ön koşul kontrolü
        prereq_met, prereq_reason = self.check_prerequisite(building_type)
        if not prereq_met:
            return False, prereq_reason
        
        # Kıyı şehri kontrolü
        if stats.requires_coastal and not is_coastal:
            return False, "Bu bina sadece kıyı şehirlerinde inşa edilebilir"
        
        # Kaynak kontrolü
        if not economy.can_afford(
            gold=stats.cost_gold,
            wood=stats.cost_wood,
            iron=stats.cost_iron
        ):
            return False, "Yetersiz kaynak"
        
        return True, ""
    
    def can_upgrade(self, building_type: BuildingType, economy) -> tuple:
        """
        Yükseltilebilir mi kontrol et
        Returns: (can_upgrade: bool, reason: str)
        """
        if building_type not in self.buildings:
            return False, "Bina mevcut değil"
        
        building = self.buildings[building_type]
        stats = building.get_stats()
        
        if building.level >= stats.max_level:
            return False, "Maksimum seviyeye ulaşıldı"
        
        # Yükseltme maliyeti (seviye * temel maliyet)
        multiplier = building.level + 1
        if not economy.can_afford(
            gold=int(stats.cost_gold * multiplier * 0.5),
            wood=int(stats.cost_wood * multiplier * 0.5),
            iron=int(stats.cost_iron * multiplier * 0.5)
        ):
            return False, "Yetersiz kaynak"
        
        return True, ""
    
    def start_construction(self, building_type: BuildingType, economy, is_coastal: bool = False) -> bool:
        """İnşaata başla"""
        can, reason = self.can_build(building_type, economy, is_coastal)
        if not can:
            audio = get_audio_manager()
            audio.announce_action_result("İnşaat", False, reason)
            return False
        
        stats = BUILDING_DEFINITIONS[building_type]
        
        # Kaynakları harca
        economy.spend(
            gold=stats.cost_gold,
            wood=stats.cost_wood,
            iron=stats.cost_iron
        )
        
        # Kuyruğa ekle
        self.construction_queue.append(ConstructionQueue(
            building_type=building_type,
            turns_remaining=stats.build_time
        ))
        
        audio = get_audio_manager()
        audio.play_ui_sound('build')  # İnşaat sesi
        audio.announce_action_result(
            f"{stats.name_tr} inşaatı",
            True,
            f"{stats.build_time} tur sonra tamamlanacak"
        )
        
        return True
    
    def start_upgrade(self, building_type: BuildingType, economy) -> bool:
        """Yükseltme başlat"""
        can, reason = self.can_upgrade(building_type, economy)
        if not can:
            audio = get_audio_manager()
            audio.announce_action_result("Yükseltme", False, reason)
            return False
        
        building = self.buildings[building_type]
        stats = building.get_stats()
        
        # Yükseltme maliyeti
        multiplier = building.level + 1
        economy.spend(
            gold=int(stats.cost_gold * multiplier * 0.5),
            wood=int(stats.cost_wood * multiplier * 0.5),
            iron=int(stats.cost_iron * multiplier * 0.5)
        )
        
        # Kuyruğa ekle
        self.construction_queue.append(ConstructionQueue(
            building_type=building_type,
            turns_remaining=max(1, stats.build_time // 2),
            is_upgrade=True
        ))
        
        audio = get_audio_manager()
        audio.announce_action_result(
            f"{stats.name_tr} yükseltme",
            True,
            f"Seviye {building.level + 1}'e yükseltiliyor"
        )
        
        return True
    
    def process_turn(self):
        """Tur sonunda inşaatları işle"""
        completed = []
        
        for item in self.construction_queue:
            item.turns_remaining -= 1
            if item.turns_remaining <= 0:
                completed.append(item)
        
        # Tamamlananları işle
        for item in completed:
            self.construction_queue.remove(item)
            stats = BUILDING_DEFINITIONS[item.building_type]
            audio = get_audio_manager()
            
            if item.is_upgrade:
                if item.building_type in self.buildings:
                    self.buildings[item.building_type].level += 1
                    building = self.buildings[item.building_type]
                    level_name = building.get_level_name()
                    audio.play_ui_sound('complete')
                    audio.announce(f"{stats.name_tr} yükseltildi: {level_name}!")
                    # Sinerji bildirimi
                    synergy_mult = self.get_synergy_multiplier(item.building_type)
                    if synergy_mult > 1.0:
                        bonus_pct = int((synergy_mult - 1.0) * 100)
                        audio.announce(f"Sinerji bonusu: +%{bonus_pct}")
            else:
                self.buildings[item.building_type] = Building(item.building_type, level=1)
                building = self.buildings[item.building_type]
                level_name = building.get_level_name()
                audio.play_ui_sound('complete')
                audio.announce(f"{stats.name_tr} tamamlandı! ({level_name})")
                # Sinerji bildirimi
                synergy_mult = self.get_synergy_multiplier(item.building_type)
                if synergy_mult > 1.0:
                    bonus_pct = int((synergy_mult - 1.0) * 100)
                    audio.announce(f"Sinerji bonusu aktif: +%{bonus_pct}")
    
    def get_total_maintenance(self) -> int:
        """Toplam bina bakım maliyeti"""
        total = 0
        for building in self.buildings.values():
            stats = building.get_stats()
            total += stats.maintenance * building.level
        return total
    
    def get_total_happiness_bonus(self) -> int:
        """Toplam mutluluk bonusu"""
        total = 0
        for building in self.buildings.values():
            total += building.get_effective_bonus('happiness_bonus')
        return total
    
    def get_total_trade_bonus(self) -> int:
        """Toplam ticaret bonusu"""
        total = 0
        for building in self.buildings.values():
            total += building.get_effective_bonus('trade_bonus')
        return total
    
    def get_total_military_bonus(self) -> int:
        """Toplam askeri bonus"""
        total = 0
        for building in self.buildings.values():
            total += building.get_effective_bonus('military_bonus')
        return total
    
    def get_food_production(self) -> int:
        """Toplam yiyecek üretimi"""
        total = 0
        for building in self.buildings.values():
            total += building.get_effective_bonus('food_production')
        return total
    
    def get_wood_production(self) -> int:
        """Toplam kereste üretimi (Kereste Ocağından)"""
        if BuildingType.LUMBER_MILL in self.buildings:
            building = self.buildings[BuildingType.LUMBER_MILL]
            return 300 * building.level  # Seviye başına 300 kereste
        return 0
    
    def get_iron_production(self) -> int:
        """Toplam demir üretimi (Maden ve Taş Ocağından)"""
        total = 0
        
        # Maden
        if BuildingType.MINE in self.buildings:
            building = self.buildings[BuildingType.MINE]
            total += 150 * building.level  # Seviye başına 150 demir
        
        # Taş Ocağı (ek demir)
        if BuildingType.QUARRY in self.buildings:
            building = self.buildings[BuildingType.QUARRY]
            total += 100 * building.level  # Seviye başına 100 ek demir
        
        return total
    
    def get_population_growth_bonus(self) -> float:
        """Han'dan nüfus artış bonusu"""
        if BuildingType.INN in self.buildings:
            building = self.buildings[BuildingType.INN]
            return 0.01 * building.level  # Seviye başına +1% nüfus artışı
        return 0.0
    
    def get_population_capacity(self) -> int:
        """Maksimum nüfus kapasitesi (taşıma kapasitesi)"""
        base_capacity = 50000  # Temel kapasite
        
        # Han bonusu: +10,000/seviye
        if BuildingType.INN in self.buildings:
            base_capacity += self.buildings[BuildingType.INN].level * 10000
        
        # Hastane bonusu (unique_effects)
        if BuildingType.HOSPITAL in self.buildings:
            base_capacity += self.buildings[BuildingType.HOSPITAL].get_unique_effect('pop_capacity')
        
        # Ambar bonusu (unique_effects)
        if BuildingType.WAREHOUSE in self.buildings:
            base_capacity += self.buildings[BuildingType.WAREHOUSE].get_unique_effect('pop_capacity')
        
        # Su Kemeri bonusu (unique_effects)
        if BuildingType.AQUEDUCT in self.buildings:
            base_capacity += self.buildings[BuildingType.AQUEDUCT].get_unique_effect('pop_capacity')
        
        return base_capacity
    
    def get_gold_per_turn(self) -> int:
        """Binalardan gelen toplam tur başına altın geliri"""
        total = 0
        for building_type, building in self.buildings.items():
            total += building.get_unique_effect('gold_per_turn')
            total += building.get_unique_effect('gold_income')
            total += building.get_unique_effect('gold_from_ore')
        return total
    
    def get_building_list(self) -> List[tuple]:
        """Bina listesi [(tip, isim, seviye), ...]"""
        result = []
        for building_type, building in self.buildings.items():
            stats = building.get_stats()
            result.append((building_type, stats.name_tr, building.level))
        return result
    
    def get_available_buildings(self) -> List[BuildingType]:
        """İnşa edilebilir binalar"""
        available = []
        for building_type in BuildingType:
            if building_type not in self.buildings:
                in_queue = any(
                    item.building_type == building_type 
                    for item in self.construction_queue
                )
                if not in_queue:
                    available.append(building_type)
        return available
    
    def announce_buildings(self):
        """Bina durumunu ekran okuyucuya duyur"""
        audio = get_audio_manager()
        audio.speak("Binalar", interrupt=True)
        
        if not self.buildings:
            audio.speak("Henüz bina yok")
            return
        
        for building_type, building in self.buildings.items():
            stats = building.get_stats()
            level_name = building.get_level_name()
            audio.speak(f"{stats.name_tr} ({level_name})")
        
        if self.construction_queue:
            audio.speak("İnşaat halinde:")
            for item in self.construction_queue:
                stats = BUILDING_DEFINITIONS[item.building_type]
                action = "yükseltiliyor" if item.is_upgrade else "inşa ediliyor"
                audio.speak(f"{stats.name_tr} {action}, {item.turns_remaining} tur kaldı")
    
    def to_dict(self) -> Dict:
        """Kayıt için dictionary'e dönüştür"""
        return {
            'buildings': {
                k.value: {'level': v.level}
                for k, v in self.buildings.items()
            },
            'construction_queue': [
                {
                    'type': item.building_type.value,
                    'turns': item.turns_remaining,
                    'is_upgrade': item.is_upgrade
                }
                for item in self.construction_queue
            ]
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ConstructionSystem':
        """Dictionary'den yükle (eski kayıtlarla uyumlu)"""
        system = cls()
        system.buildings = {}
        for k, v in data['buildings'].items():
            try:
                bt = BuildingType(k)
                system.buildings[bt] = Building(bt, level=v['level'])
            except ValueError:
                continue  # Bilinmeyen bina tipi (eski kayıt uyumluluğu)
        
        system.construction_queue = []
        for item in data.get('construction_queue', []):
            try:
                bt = BuildingType(item['type'])
                system.construction_queue.append(ConstructionQueue(
                    bt,
                    item['turns'],
                    item.get('is_upgrade', False)
                ))
            except ValueError:
                continue  # Bilinmeyen bina tipi
        
        return system
