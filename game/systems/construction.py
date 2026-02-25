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
    IDARI = "idari"         # İdari yapılar (Mahkeme vb.)
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
    BAKERY = "bakery"              # Fırın (YENİ)
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
    SOUP_KITCHEN = "soup_kitchen"  # İmaret (YENİ)
    LIBRARY = "library"            # Kütüphane (YENİ)
    COURT = "court"                # Mahkeme / Kadı Konağı (YENİ)


@dataclass
class BuildingModuleStats:
    """Bina eklentisi/modül istatistikleri"""
    id: str
    name: str
    name_tr: str
    description: str
    cost_gold: int
    cost_wood: int
    cost_iron: int
    effects: Dict[str, int]  # {'science': 5, 'happiness': 2}
    historical_desc: str


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
    available_modules: Dict[str, BuildingModuleStats] = None  # Mevcut eklentiler


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
        },
        available_modules={
            'muvakkithane': BuildingModuleStats(
                id='muvakkithane',
                name="Timekeeper's Room",
                name_tr="Muvakkithane",
                description="Astronomi ve vakit hesaplama merkezi - Bilim üretir",
                cost_gold=300,
                cost_wood=50,
                cost_iron=20,
                effects={'science': 5, 'piety': 2},
                historical_desc="16. yy camilerinin bilim merkezi. Namaz vakitleri ve takvim burada hesaplanırdı."
            ),
            'hunkar_mahfili': BuildingModuleStats(
                id='hunkar_mahfili',
                name="Royal Lodge",
                name_tr="Hünkâr Mahfili",
                description="Padişahın güvenle ibadet ettiği özel loca - Prestij ve güvenlik",
                cost_gold=1000,
                cost_wood=200,
                cost_iron=50,
                effects={'legitimacy': 10, 'security': 5},
                historical_desc="Padişahın suikast riskine karşı korunarak namaz kıldığı, kafesli ve ayrı girişli bölüm."
            ),
            'sadaka_tasi': BuildingModuleStats(
                id='sadaka_tasi',
                name="Alms Stone",
                name_tr="Sadaka Taşı",
                description="Gizli yardım taşı - Sosyal adalet ve huzur",
                cost_gold=100,
                cost_wood=0,
                cost_iron=0,
                effects={'happiness': 5, 'unrest_reduction': 3},
                historical_desc="Veren elin alan eli görmediği, Osmanlı sosyal dayanışmasının zarif simgesi."
            ),
            'sadirvan': BuildingModuleStats(
                id='sadirvan',
                name="Fountain",
                name_tr="Şadırvan",
                description="Abdest ve su merkezi - Hijyen sağlar",
                cost_gold=250,
                cost_wood=30,
                cost_iron=10,
                effects={'health': 3, 'hygiene': 5},
                historical_desc="Cami avlusunun ortasında yer alan, estetik ve temizlik kaynağı su yapısı."
            ),
            'hazire': BuildingModuleStats(
                id='hazire',
                name="Graveyard",
                name_tr="Hazire",
                description="Önemli şahsiyetlerin mezarlığı - Maneviyat ve Tarih",
                cost_gold=150,
                cost_wood=0,
                cost_iron=10,
                effects={'piety': 5, 'culture': 3},
                historical_desc="Caminin kıble yönünde bulunan, ulema ve devlet büyüklerinin defnedildiği sessiz bahçe."
            )
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
        },
        available_modules={
            'dershane': BuildingModuleStats(
                id='dershane',
                name="Lecture Hall",
                name_tr="Dershane-i Umumî",
                description="Büyük derslik - Eğitim kapasitesini artırır",
                cost_gold=500,
                cost_wood=100,
                cost_iron=20,
                effects={'education': 10, 'ulema_capacity': 2},
                historical_desc="Medresenin en büyük kubbeli odası. Baş müderris burada ders verirdi."
            ),
            'hucreler': BuildingModuleStats(
                id='hucreler',
                name="Student Cells",
                name_tr="Talebe Hücreleri",
                description="Öğrenci odaları - Kapasite artışı",
                cost_gold=300,
                cost_wood=100,
                cost_iron=10,
                effects={'science': 5, 'pop_capacity': 100},
                historical_desc="Öğrencilerin (suhte) barındığı ocaklı küçük odalar."
            ),
            'hafiz_i_kutup': BuildingModuleStats(
                id='hafiz_i_kutup',
                name="Library Room",
                name_tr="Hafız-ı Kütüp Odası",
                description="El yazması eserler - Bilim ve Teknoloji",
                cost_gold=600,
                cost_wood=50,
                cost_iron=10,
                effects={'science': 10, 'tech_speed': 5},
                historical_desc="Nadide kitapların saklandığı kütüphane odası."
            ),
            'darulkurra': BuildingModuleStats(
                id='darulkurra',
                name="Quran School",
                name_tr="Darülkurrâ",
                description="Kuran ihtisas okulu - Dini prestij",
                cost_gold=400,
                cost_wood=50,
                cost_iron=0,
                effects={'piety': 10, 'ulema_loyalty': 5},
                historical_desc="Kuran okuma sanatının icra edildiği özel bölüm."
            )
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
        },
        available_modules={
            'ocakli_oda': BuildingModuleStats(
                id='ocakli_oda',
                name="Hearth Room",
                name_tr="Ocaklı Oda",
                description="Misafirlerin ısındığı ve yemek yediği oda",
                cost_gold=200,
                cost_wood=50,
                cost_iron=10,
                effects={'happiness': 5},
                historical_desc="Kış aylarında yolcuların ısınması için ocak bulunan odalar."
            ),
            'misafir_ahiri': BuildingModuleStats(
                id='misafir_ahiri',
                name="Guest Stable",
                name_tr="Misafir Ahırı",
                description="Yolcuların atları için barınak",
                cost_gold=150,
                cost_wood=100,
                cost_iron=0,
                effects={'trade_bonus': 5},
                historical_desc="Misafirlerin binek hayvanlarının bakıldığı yer."
            )
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
        },
        available_modules={
            'etmeydani': BuildingModuleStats(
                id='etmeydani',
                name="Muster Ground",
                name_tr="Etmeydanı",
                description="Yeniçerilerin toplanma ve yemek alanı - Moral ve Hız",
                cost_gold=500,
                cost_wood=100,
                cost_iron=20,
                effects={'morale': 10, 'train_speed': 1},
                historical_desc="Kazanların kaynadığı, törenlerin yapıldığı ve isyanların başladığı meydan."
            ),
            'orta_cami': BuildingModuleStats(
                id='orta_cami',
                name="Barracks Mosque",
                name_tr="Orta Cami",
                description="Ocak içi ibadethane - Disiplin sağlar",
                cost_gold=400,
                cost_wood=100,
                cost_iron=10,
                effects={'discipline': 5, 'piety': 2},
                historical_desc="Kışla avlusunda yer alan, Bektaşi geleneklerinin de yaşatıldığı cami."
            ),
            'talimgah': BuildingModuleStats(
                id='talimgah',
                name="Training Field",
                name_tr="Talimgâh/Ok Meydanı",
                description="Silah ve nişan eğitimi - Asker Kalitesi",
                cost_gold=300,
                cost_wood=0,
                cost_iron=20,
                effects={'unit_xp': 10},
                historical_desc="Okçuluk ve tüfek talimlerinin yapıldığı geniş arazi."
            ),
            'acemi_kogusu': BuildingModuleStats(
                id='acemi_kogusu',
                name="Recruit Quarters",
                name_tr="Acemi Oğlanları Koğuşu",
                description="Yeni askerlerin ilk eğitimi - İnsan Kaynağı",
                cost_gold=200,
                cost_wood=100,
                cost_iron=0,
                effects={'manpower_recovery': 5, 'unit_cost_reduction': 5},
                historical_desc="Devşirme gençlerin Türk-İslam geleneklerini öğrendiği hazırlık okulu."
            ),
            'tulumbaci': BuildingModuleStats(
                id='tulumbaci',
                name="Fire Brigade",
                name_tr="Tulumbacı Ocağı",
                description="İtfaiye teşkilatı - Yangın riskini azaltır",
                cost_gold=150,
                cost_wood=50,
                cost_iron=10,
                effects={'fire_risk': -50},
                historical_desc="Yangınlara müdahale eden, genellikle Yeniçerilerden oluşan ilk itfaiye birimi."
            )
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
        },
        available_modules={
            'ic_kale': BuildingModuleStats(
                id='ic_kale',
                name="Keep",
                name_tr="İç Kale",
                description="Son savunma hattı - Direnç artışı",
                cost_gold=1000,
                cost_wood=200,
                cost_iron=100,
                effects={'defense': 20, 'siege_resistance': 15},
                historical_desc="Kalenin en yüksek ve korunaklı, komutanın bulunduğu merkezi."
            ),
            'zindan': BuildingModuleStats(
                id='zindan',
                name="Dungeon",
                name_tr="Zindan",
                description="Esir ve suçluların tutulduğu yer - Güvenlik",
                cost_gold=500,
                cost_wood=50,
                cost_iron=50,
                effects={'security': 10, 'labor_force': 5},
                historical_desc="Kalenin altındaki karanlık ve nemli hapishane."
            ),
            'su_sarnici': BuildingModuleStats(
                id='su_sarnici',
                name="Cistern",
                name_tr="Su Sarnıcı",
                description="Kuşatma sırasında su ihtiyacı - Dayanıklılık",
                cost_gold=400,
                cost_wood=50,
                cost_iron=20,
                effects={'siege_endurance': 10},
                historical_desc="Yağmur sularının biriktirildiği yeraltı su deposu."
            ),
            'cephane': BuildingModuleStats(
                id='cephane',
                name="Armory",
                name_tr="Cephane",
                description="Silah ve mühimmat deposu",
                cost_gold=600,
                cost_wood=100,
                cost_iron=50,
                effects={'garrison_damage': 10},
                historical_desc="Barut, gülle ve tüfeklerin saklandığı korunaklı bina."
            )
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
        },
        available_modules={
            'dokum_firini': BuildingModuleStats(
                id='dokum_firini',
                name="Blast Furnace",
                name_tr="Döküm Fırını",
                description="Yüksek ısılı fırınlar - Ağır top üretimi",
                cost_gold=800,
                cost_wood=100,
                cost_iron=100,
                effects={'artillery_production': 1, 'siege_power': 10},
                historical_desc="Tunç topların döküldüğü devasa yüksek fırınlar."
            ),
            'kaliphane': BuildingModuleStats(
                id='kaliphane',
                name="Mould House",
                name_tr="Kalıphane",
                description="Hassas döküm kalıpları - Üretim kalitesi",
                cost_gold=400,
                cost_wood=50,
                cost_iron=20,
                effects={'production_efficiency': 10},
                historical_desc="Top kalıplarının milimetrik hazırlandığı atölye."
            ),
            'baruthane': BuildingModuleStats(
                id='baruthane',
                name="Gunpowder Mill",
                name_tr="Baruthane",
                description="Barut üretimi - Mühimmat sağlar",
                cost_gold=600,
                cost_wood=100,
                cost_iron=50,
                effects={'ammo_supply': 100},
                historical_desc="Güherçile, kükürt ve kömürden barut yapılan yer."
            ),
            'top_talimhane': BuildingModuleStats(
                id='top_talimhane',
                name="Artillery Range",
                name_tr="Top Talimhanesi",
                description="Atış denemeleri - İsabet oranı",
                cost_gold=300,
                cost_wood=0,
                cost_iron=10,
                effects={'artillery_accuracy': 10, 'unit_xp': 5},
                historical_desc="Yeni dökülen topların test edildiği açık alan."
            ),
            'komur_deposu': BuildingModuleStats(
                id='komur_deposu',
                name="Coal Store",
                name_tr="Ambar-ı Engişt",
                description="Kömür stoku - Üretim sürekliliği",
                cost_gold=200,
                cost_wood=100,
                cost_iron=10,
                effects={'production_consistency': 10},
                historical_desc="Döküm için hayati olan yüksek kalorili kömürün saklandığı depo."
            )
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
        },
        available_modules={
            'ates_kulesi': BuildingModuleStats(
                id='ates_kulesi',
                name="Signal Fire",
                name_tr="Ateş Kulesi",
                description="Haberleşme - İletişim hızı",
                cost_gold=150,
                cost_wood=50,
                cost_iron=0,
                effects={'early_warning': 1, 'unit_movement': 1},
                historical_desc="Düşman görüldüğünde yakılan işaret ateşi."
            ),
            'gozetleme_balkonu': BuildingModuleStats(
                id='gozetleme_balkonu',
                name="Lookout Post",
                name_tr="Cihannüma",
                description="Geniş görüş açısı - Keşif",
                cost_gold=200,
                cost_wood=50,
                cost_iron=10,
                effects={'scout_range': 2},
                historical_desc="Her yöne hakim, rüzgarlı gözetleme balkonu."
            )
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
        },
        available_modules={
            'kapan': BuildingModuleStats(
                id='kapan',
                name="Weigh House",
                name_tr="Kapan",
                description="Toptan mal tartım ve dağıtım merkezi - Gıda kontrolü",
                cost_gold=400,
                cost_wood=50,
                cost_iron=10,
                effects={'food_waste': -10, 'trade_efficiency': 5},
                historical_desc="Un, bal, yağ gibi temel gıdaların tartıldığı ve narhın denetlendiği merkez."
            ),
            'lonca_odasi': BuildingModuleStats(
                id='lonca_odasi',
                name="Guild Room",
                name_tr="Lonca Odası",
                description="Esnaf örgütlenme merkezi - Kalite kontrol",
                cost_gold=200,
                cost_wood=50,
                cost_iron=0,
                effects={'production_quality': 5, 'happiness': 2},
                historical_desc="Esnafın toplandığı, çıraklık-kalfalık törenlerinin yapıldığı oda."
            ),
            'sebil': BuildingModuleStats(
                id='sebil',
                name="Fountain",
                name_tr="Sebil",
                description="Ücretsiz su dağıtımı - Halk sevgisi",
                cost_gold=150,
                cost_wood=20,
                cost_iron=10,
                effects={'happiness': 3},
                historical_desc="Gelip geçene su dağıtılan hayır yapısı."
            )
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
        },
        available_modules={
            'kislik_ahir': BuildingModuleStats(
                id='kislik_ahir',
                name="Winter Stable",
                name_tr="Kışlık Ahır",
                description="Hayvanlar için sıcak barınak - Lojistik",
                cost_gold=300,
                cost_wood=100,
                cost_iron=10,
                effects={'caravan_speed': 5, 'logistics': 10},
                historical_desc="Yük hayvanlarının kışın korunduğu tonozlu alt katlar."
            ),
            'tamirhane': BuildingModuleStats(
                id='tamirhane',
                name="Repair Shop",
                name_tr="Tamirhane/Nalbant",
                description="Araba ve nal bakımı - Hareketlilik",
                cost_gold=200,
                cost_wood=50,
                cost_iron=50,
                effects={'trade_route_maintenance': -10},
                historical_desc="Kırılan tekerleklerin ve nalların yenilendiği atölye."
            ),
            'peykeli_ocak': BuildingModuleStats(
                id='peykeli_ocak',
                name="Hearth Area",
                name_tr="Peykeli Ocak",
                description="Isınma ve sosyalleşme - Haberleşme",
                cost_gold=150,
                cost_wood=50,
                cost_iron=10,
                effects={'intelligence': 2, 'happiness': 2},
                historical_desc="Yolcuların ateş başında sohbet edip haberleştiği alan."
            ),
            'kosk_mescit': BuildingModuleStats(
                id='kosk_mescit',
                name="Raised Mosque",
                name_tr="Köşk Mescit",
                description="Avludaki yükseltilmiş ibadethane - Prestij",
                cost_gold=300,
                cost_wood=50,
                cost_iron=10,
                effects={'piety': 3, 'manpower_recovery': 2},
                historical_desc="Kervansaray avlusunun ortasında, hayvanlardan izole dua mekanı."
            ),
            'kuleler': BuildingModuleStats(
                id='kuleler',
                name="Defense Towers",
                name_tr="Kuleli Sur",
                description="Eşkıya saldırılarına karşı koruma",
                cost_gold=500,
                cost_wood=100,
                cost_iron=50,
                effects={'security': 15, 'bandit_suppression': 20},
                historical_desc="Kervansarayı küçük bir kaleye çeviren savunma kuleleri."
            )
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
        },
        available_modules={
            'ahirlar': BuildingModuleStats(
                id='ahirlar',
                name="Stables",
                name_tr="Ahırlar",
                description="Binek hayvanları için yer - Ticaret Hızı",
                cost_gold=150,
                cost_wood=50,
                cost_iron=0,
                effects={'caravan_speed': 2},
                historical_desc="Yolcuların at ve katırlarının barındığı yer."
            ),
            'odalar': BuildingModuleStats(
                id='odalar',
                name="Rooms",
                name_tr="Odalar",
                description="Konaklama odaları - Kapasite",
                cost_gold=200,
                cost_wood=100,
                cost_iron=0,
                effects={'pop_capacity': 50, 'happiness': 2},
                historical_desc="Tüccarların geceyi geçirdiği üst kat odaları."
            ),
            'mahzen': BuildingModuleStats(
                id='mahzen',
                name="Cellar",
                name_tr="Mahzen",
                description="Mal deposu - Stok",
                cost_gold=200,
                cost_wood=50,
                cost_iron=10,
                effects={'resource_capacity': 500},
                historical_desc="Malların saklandığı serin alt kat depoları."
            )
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
        },
        available_modules={
            'yeralti_mahzeni': BuildingModuleStats(
                id='yeralti_mahzeni',
                name="Vault",
                name_tr="Yeraltı Mahzeni",
                description="Kıymetli evrak ve altın kasası - Hazine kapasitesi",
                cost_gold=600,
                cost_wood=50,
                cost_iron=100,
                effects={'treasury_limit': 2000, 'banking': 10},
                historical_desc="Demir kapılı, hırsızlığa karşı korunaklı yeraltı kasaları."
            ),
            'arasta': BuildingModuleStats(
                id='arasta',
                name="Arasta",
                name_tr="Arasta",
                description="Bitişik dükkanlar sırası - Ticaret hacmi",
                cost_gold=400,
                cost_wood=100,
                cost_iron=10,
                effects={'trade_bonus': 10},
                historical_desc="Bedestene bitişik, aynı işi yapan esnafın bulunduğu sokak."
            ),
            'sarraf_odasi': BuildingModuleStats(
                id='sarraf_odasi',
                name="Money Changer",
                name_tr="Sarraf Odası",
                description="Döviz bozdurma ve kredi - Finans",
                cost_gold=300,
                cost_wood=50,
                cost_iron=20,
                effects={'banking': 15, 'inflation_control': 5},
                historical_desc="Yabancı paraların akçeye çevrildiği ofisler."
            ),
            'dua_meydani': BuildingModuleStats(
                id='dua_meydani',
                name="Prayer Square",
                name_tr="Dua Meydanı",
                description="Esnafın toplanma yeri - Lonca sadakati",
                cost_gold=100,
                cost_wood=0,
                cost_iron=0,
                effects={'happiness': 5, 'production_quality': 2},
                historical_desc="Sabahları dükkanlar açılmadan esnafın bereket duası ettiği yer."
            )
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
        },
        available_modules={
            'sikke_atelyesi': BuildingModuleStats(
                id='sikke_atelyesi',
                name="Coin Workshop",
                name_tr="Sikke Atölyesi",
                description="Gümüş ve altın işleme - Üretim hızı",
                cost_gold=400,
                cost_wood=50,
                cost_iron=50,
                effects={'gold_per_turn': 10},
                historical_desc="Çekiçle veya presle sikkelerin basıldığı tezgahlar."
            ),
            'gumus_ocagi': BuildingModuleStats(
                id='gumus_ocagi',
                name="Silver Furnace",
                name_tr="Gümüş Ocağı",
                description="Maden eritme - Verimlilik",
                cost_gold=500,
                cost_wood=100,
                cost_iron=50,
                effects={'inflation_control': 10},
                historical_desc="Gümüşü saflaştırmak için kullanılan özel fırınlar."
            ),
            'vezn_odasi': BuildingModuleStats(
                id='vezn_odasi',
                name="Weighing Room",
                name_tr="Vezn Odası",
                description="Hassas tartım - Güvenilirlik",
                cost_gold=200,
                cost_wood=50,
                cost_iron=10,
                effects={'legitimacy': 3},
                historical_desc="Paraların gramajının kontrol edildiği oda."
            )
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
        },
        available_modules={
            'degirmen': BuildingModuleStats(
                id='degirmen',
                name="Mill",
                name_tr="Su Değirmeni",
                description="Tahıl öğütme - Gıda verimi",
                cost_gold=300,
                cost_wood=100,
                cost_iron=50,
                effects={'food_production': 100},
                historical_desc="Buğdayın una çevrildiği temel yapı."
            ),
            'ambar': BuildingModuleStats(
                id='ambar',
                name="Barn",
                name_tr="Tahıl Ambarı",
                description="Ürün saklama - Kayıp azaltma",
                cost_gold=200,
                cost_wood=100,
                cost_iron=10,
                effects={'food_waste': -10},
                historical_desc="Hasadın yağmurdan korunduğu ahşap depo."
            ),
            'sulama_kanali': BuildingModuleStats(
                id='sulama_kanali',
                name="Irrigation",
                name_tr="Sulama Kanalı",
                description="Su dağıtımı - Verim artışı",
                cost_gold=150,
                cost_wood=0,
                cost_iron=0,
                effects={'farm_output_bonus': 10},
                historical_desc="Tarlalara su taşıyan basit arıklar."
            )
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
        },
        available_modules={
            'tahkimat': BuildingModuleStats(
                id='tahkimat',
                name="Supports",
                name_tr="Ahşap Tahkimat",
                description="Göçük riskini azaltır - Güvenlik",
                cost_gold=200,
                cost_wood=100,
                cost_iron=20,
                effects={'mine_safety': 20, 'production_consistency': 5},
                historical_desc="Madencilerin hayatını koruyan direkler ve tavan destekleri."
            ),
            'havalandirma': BuildingModuleStats(
                id='havalandirma',
                name="Ventilation",
                name_tr="Havalandırma Bacası",
                description="Temiz hava akışı - İşçi sağlığı",
                cost_gold=300,
                cost_wood=50,
                cost_iron=10,
                effects={'health': 5, 'production_efficiency': 10},
                historical_desc="Derin kuyularda biriken zehirli gazları atan sistem."
            ),
            'cevher_yikama': BuildingModuleStats(
                id='cevher_yikama',
                name="Ore Washer",
                name_tr="Cevher Yıkama",
                description="Cevher saflaştırma - Kalite artışı",
                cost_gold=400,
                cost_wood=100,
                cost_iron=20,
                effects={'iron_quality': 10, 'production_bonus': 15},
                historical_desc="Suların gücüyle toprağın metalden ayrıştırıldığı havuzlar."
            )
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
        },
        available_modules={
            'hizare': BuildingModuleStats(
                id='hizare',
                name="Sawmill",
                name_tr="Hızare",
                description="Su gücüyle çalışan bıçkı - Üretim hızı",
                cost_gold=300,
                cost_wood=50,
                cost_iron=50,
                effects={'wood_production': 100},
                historical_desc="Tomrukların kalas haline getirildiği atölye."
            ),
            'kurutma_firin': BuildingModuleStats(
                id='kurutma_firin',
                name="Drying Kiln",
                name_tr="Kurutma Fırını",
                description="Kereste nemini alma - Kalite",
                cost_gold=200,
                cost_wood=50,
                cost_iron=20,
                effects={'wood_quality': 10, 'ship_build_speed_bonus': 5},
                historical_desc="Gemi yapımında kullanılacak ağaçların bekletildiği fırın."
            ),
            'katran_ocagi': BuildingModuleStats(
                id='katran_ocagi',
                name="Tar Kiln",
                name_tr="Katran Ocağı",
                description="Reçine isleme - Gemi malzemesi",
                cost_gold=150,
                cost_wood=50,
                cost_iron=10,
                effects={'tar_production': 10},
                historical_desc="Çam kütüklerinden katran elde edilen ocak."
            )
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
        },
        available_modules={
            'vinc_sistemi': BuildingModuleStats(
                id='vinc_sistemi',
                name="Crane",
                name_tr="Vinç Sistemi",
                description="Ağır taş kaldırma - İşgücü tasarrufu",
                cost_gold=300,
                cost_wood=100,
                cost_iron=50,
                effects={'build_speed': 2, 'labor_cost': -10},
                historical_desc="Büyük blokların taşınmasını sağlayan makara sistemi."
            ),
            'tas_kesim': BuildingModuleStats(
                id='tas_kesim',
                name="Stone Cutting",
                name_tr="Taş Kesim Atölyesi",
                description="Blok şekillendirme - İnşaat kalitesi",
                cost_gold=200,
                cost_wood=50,
                cost_iron=20,
                effects={'building_durability': 10},
                historical_desc="Taşların mimari projelere uygun kesildiği yer."
            ),
            'mermer_atel': BuildingModuleStats(
                id='mermer_atel',
                name="Marble Workshop",
                name_tr="Mermer Atölyesi",
                description="İnce işçilik - Prestij",
                cost_gold=400,
                cost_wood=50,
                cost_iron=20,
                effects={'culture': 5, 'legitimacy': 2},
                historical_desc="Sütun ve süslemelerin işlendiği sanat atölyesi."
            )
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
        },
        available_modules={
            'kapan_diresi': BuildingModuleStats(
                id='kapan_diresi',
                name="Weighing Office",
                name_tr="Kapan Dairesi",
                description="Mal giriş çıkış kontrolü - Verimlilik",
                cost_gold=200,
                cost_wood=50,
                cost_iron=0,
                effects={'resource_loss_reduction': 10},
                historical_desc="Malların tartılarak defterlere kaydedildiği ofis."
            ),
            'muhafiz': BuildingModuleStats(
                id='muhafiz',
                name="Guard Post",
                name_tr="Muhafız Kulübesi",
                description="Güvenlik - Hırsızlık önleme",
                cost_gold=150,
                cost_wood=50,
                cost_iron=10,
                effects={'security': 5, 'theft_reduction': 20},
                historical_desc="Ambarı koruyan bekçilerin yeri."
            ),
            'havalandirma_ambar': BuildingModuleStats(
                id='havalandirma_ambar',
                name="Ventilation",
                name_tr="Havalandırma Sistemi",
                description="Hava sirkülasyonu - Çürüme önleme",
                cost_gold=250,
                cost_wood=50,
                cost_iron=10,
                effects={'food_preservation': 15},
                historical_desc="Zahirenin bozulmasını önleyen hava kanalları."
            )
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
        },
        available_modules={
            'kemer_gozu': BuildingModuleStats(
                id='kemer_gozu',
                name="Arch Span",
                name_tr="Bakım Yolu",
                description="Kemer üstü yolu - Dayanıklılık",
                cost_gold=300,
                cost_wood=50,
                cost_iron=20,
                effects={'infrastructure_maintenance': -10},
                historical_desc="Su yolunun bakım ve onarımının yapıldığı geçit."
            ),
            'su_terazisi': BuildingModuleStats(
                id='su_terazisi',
                name="Water Balance",
                name_tr="Su Terazisi",
                description="Basınç dengeleme - Su kaybı önleme",
                cost_gold=400,
                cost_wood=50,
                cost_iron=20,
                effects={'water_efficiency': 20},
                historical_desc="Şehir içi şebekede su basıncını ayarlayan kuleler."
            ),
            'maksem': BuildingModuleStats(
                id='maksem',
                name="Distribution Tank",
                name_tr="Maksem",
                description="Su dağıtım merkezi - Kapsama alanı",
                cost_gold=500,
                cost_wood=100,
                cost_iron=50,
                effects={'pop_capacity': 2000, 'happiness': 5},
                historical_desc="Suyun mahallelere taksim edildiği (bölüştürüldüğü) ana depo."
            )
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
        },
        available_modules={
            'gemi_gozleri': BuildingModuleStats(
                id='gemi_gozleri',
                name="Ship Bays",
                name_tr="Gemi Gözleri",
                description="Kapalı inşa alanları - Hız",
                cost_gold=500,
                cost_wood=200,
                cost_iron=50,
                effects={'ship_build_speed': 1, 'naval_capacity': 2},
                historical_desc="Haliç kıyısında gemilerin inşa edildiği kemerli bölmeler."
            ),
            'lengerhane': BuildingModuleStats(
                id='lengerhane',
                name="Anchor House",
                name_tr="Lengerhane",
                description="Çapa ve zincir üretimi - Gemi dayanıklılığı",
                cost_gold=400,
                cost_wood=50,
                cost_iron=100,
                effects={'ship_quality': 5},
                historical_desc="Gemilerin demir aksamının üretildiği ocak."
            ),
            'ciplak_zindan': BuildingModuleStats(
                id='ciplak_zindan',
                name="Galley Slave Quarters",
                name_tr="Zindan",
                description="Kürek mahkumları koğuşu - İşgücü",
                cost_gold=300,
                cost_wood=100,
                cost_iron=20,
                effects={'ship_build_speed_bonus': 10},
                historical_desc="Tersane işçisi olarak çalıştırılan forsaların barınağı."
            ),
            'iplikhane': BuildingModuleStats(
                id='iplikhane',
                name="Sail Loft",
                name_tr="İplikhane",
                description="Yelken bezi ve halat hazırlığı",
                cost_gold=250,
                cost_wood=50,
                cost_iron=0,
                effects={'ship_speed': 5},
                historical_desc="Yelkenlerin dikildiği ve halatların örüldüğü yer."
            )
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
        },
        available_modules={
            'zift_kazani': BuildingModuleStats(
                id='zift_kazani',
                name="Tar Cauldron",
                name_tr="Zift Kazanı",
                description="Su yalıtımı - Gemi ömrü",
                cost_gold=200,
                cost_wood=50,
                cost_iron=20,
                effects={'ship_durability': 10},
                historical_desc="Gemilerin altına sürülen koruyucu ziftin kaynatıldığı yer."
            ),
            'kendir_havuzu': BuildingModuleStats(
                id='kendir_havuzu',
                name="Hemp Pool",
                name_tr="Kendir Havuzu",
                description="Halat hammaddesi işleme",
                cost_gold=150,
                cost_wood=50,
                cost_iron=0,
                effects={'rope_production': 20},
                historical_desc="Kenevirlerin yumuşatıldığı havuzlar."
            ),
            'yelken_bezirhane': BuildingModuleStats(
                id='yelken_bezirhane',
                name="Sailcloth Workshop",
                name_tr="Yelken Bezirhanesi",
                description="Yelken bezi üretimi - Hız",
                cost_gold=250,
                cost_wood=50,
                cost_iron=10,
                effects={'sailcloth_production': 10},
                historical_desc="Dayanıklı pamuklu bezlerin dokunduğu atölye."
            )
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
        },
        available_modules={
            'muzik_odasi': BuildingModuleStats(
                id='muzik_odasi',
                name="Music Therapy",
                name_tr="Müzik Şifahanesi",
                description="Ruh sağlığı tedavisi - Akıl sağlığı",
                cost_gold=300,
                cost_wood=50,
                cost_iron=0,
                effects={'happiness': 10, 'mental_health': 15},
                historical_desc="Hastalara su sesi ve makamlarla müzik terapisi uygulanan salon."
            ),
            'laboratuvar': BuildingModuleStats(
                id='laboratuvar',
                name="Laboratory",
                name_tr="Laboratuvar",
                description="İlaç yapımı - Tıp bilimi",
                cost_gold=400,
                cost_wood=50,
                cost_iron=20,
                effects={'science': 10, 'plague_resistance': 5},
                historical_desc="Hekimlerin ilaç terkipleri hazırladığı yer."
            ),
            'nebat_bahcesi': BuildingModuleStats(
                id='nebat_bahcesi',
                name="Herb Garden",
                name_tr="Nebat Bahçesi",
                description="Şifalı bitkiler - Sağlık masrafı düşüşü",
                cost_gold=200,
                cost_wood=20,
                cost_iron=10,
                effects={'health_upkeep': -10},
                historical_desc="İlaç yapımında kullanılan tıbbi bitkilerin yetiştirildiği bahçe."
            )
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
        },
        available_modules={
            'camekan': BuildingModuleStats(
                id='camekan',
                name="Dressing Hall",
                name_tr="Camekan",
                description="Giriş ve soyunma salonu - Kapasite",
                cost_gold=200,
                cost_wood=50,
                cost_iron=0,
                effects={'pop_capacity': 100, 'happiness': 2},
                historical_desc="Hamamın ortasında şadırvan bulunan yüksek kubbeli giriş salonu."
            ),
            'sicaklik': BuildingModuleStats(
                id='sicaklik',
                name="Hot Room",
                name_tr="Sıcaklık",
                description="Terleme ve kese alanı - Hijyen",
                cost_gold=300,
                cost_wood=20,
                cost_iron=10,
                effects={'hygiene': 15},
                historical_desc="Hamamın asıl yıkanılan, göbek taşının bulunduğu sıcak bölümü."
            ),
            'kulhan': BuildingModuleStats(
                id='kulhan',
                name="Furnace",
                name_tr="Külhan",
                description="Isıtma sistemi - Verimlilik",
                cost_gold=250,
                cost_wood=50,
                cost_iron=50,
                effects={'maintenance_reduction': 10},
                historical_desc="Hamamın suyunun ve zemininin ısıtıldığı ocak bölümü."
            )
        }
    ),
    BuildingType.SOUP_KITCHEN: BuildingStats(
        name="Soup Kitchen",
        name_tr="İmaret",
        description="Yoksullara yemek dağıtılan hayır kurumu",
        cost_gold=300,
        cost_wood=50,
        cost_iron=10,
        maintenance=15,
        build_time=2,
        max_level=3,
        category=BuildingCategory.SOSYAL,
        happiness_bonus=15,
        prerequisite="mosque",
        synergy_with=["mosque", "bakery"],
        synergy_bonus_desc="Cami ile: dindarlık +%10. Fırın ile: kapasite +%20.",
        historical_desc="İmaretler, külliyelerin önemli bir parçasıydı. Hürrem Sultan İmareti günde binlerce kişiye yemek verirdi.",
        level_names=["Aşevi", "İmaret", "Sultan İmareti"],
        unique_effects={
            'piety': 10,               # Dindarlık artışı
            'pop_growth': 5,           # Nüfus artışı desteklenir
            'unrest_reduction': 5      # Huzursuzluk düşüşü
        },
        available_modules={
            'fodla_firini': BuildingModuleStats(
                id='fodla_firini',
                name="Bread Oven",
                name_tr="Fodla Fırını",
                description="Ekmek üretimi - Gıda",
                cost_gold=200,
                cost_wood=50,
                cost_iron=10,
                effects={'food_production': 50},
                historical_desc="İmaretlerde dağıtılan özel ekmeklerin (fodla) pişirildiği fırın."
            ),
            'buzhane': BuildingModuleStats(
                id='buzhane',
                name="Ice House",
                name_tr="Buzhane",
                description="Gıda saklama - Verimlilik",
                cost_gold=150,
                cost_wood=50,
                cost_iron=0,
                effects={'food_waste': -5},
                historical_desc="Dağlardan getirilen karların saklandığı soğuk hava deposu."
            ),
            'et_kileri': BuildingModuleStats(
                id='et_kileri',
                name="Meat Pantry",
                name_tr="Et Kileri",
                description="Et saklama - Memnuniyet",
                cost_gold=250,
                cost_wood=50,
                cost_iron=10,
                effects={'happiness': 5},
                historical_desc="Kurban bayramlarında ve ziyafetlerde dağıtılacak etlerin saklandığı yer."
            )
        }
    ),
    BuildingType.LIBRARY: BuildingStats(
        name="Library",
        name_tr="Kütüphane",
        description="Bilgi ve kültür merkezi - eğitim seviyesini artırır",
        cost_gold=600,
        cost_wood=100,
        cost_iron=20,
        maintenance=20,
        build_time=3,
        max_level=3,
        category=BuildingCategory.SOSYAL,
        happiness_bonus=5,
        prerequisite="medrese",
        synergy_with=["medrese"],
        synergy_bonus_desc="Medrese ile: eğitim +%25.",
        historical_desc="Osmanlı kütüphaneleri cami ve medreselerden bağımsız yapılar haline gelmeye başlamıştı. I. Mahmud Kütüphanesi bunun ilk örneğidir.",
        level_names=["Kitaplık", "Kütüphane", "Enderun Kütüphanesi"],
        unique_effects={
            'education': 15,           # Eğitim seviyesi
            'science': 10,             # Bilim puanı
            'ulema_loyalty': 5         # Ulema memnuniyeti
        },
        available_modules={
            'okuma_salonu': BuildingModuleStats(
                id='okuma_salonu',
                name="Reading Hall",
                name_tr="Okuma Salonu",
                description="Rahle ve minderler - Eğitim hızı",
                cost_gold=200,
                cost_wood=50,
                cost_iron=0,
                effects={'education': 10},
                historical_desc="Halkın ve talebelerin kitap okuduğu aydınlık salon."
            ),
            'cilt_atelyesi': BuildingModuleStats(
                id='cilt_atelyesi',
                name="Bindery",
                name_tr="Cilt Atölyesi",
                description="Kitap onarımı ve cildi - Bilgi koruma",
                cost_gold=300,
                cost_wood=20,
                cost_iron=10,
                effects={'science': 5},
                historical_desc="El yazması kitapların ciltlendiği ve tamir edildiği sanat atölyesi."
            )
        }
    ),
    
    # ═══════════════════════════════════════════════════
    # ALTYAPI VE EKONOMİ (EK)
    # ═══════════════════════════════════════════════════
    BuildingType.BAKERY: BuildingStats(
        name="Bakery",
        name_tr="Has Fırın",
        description="Ekmek üretimi ve gıda güvenliği sağlar",
        cost_gold=200,
        cost_wood=30,
        cost_iron=10,
        maintenance=5,
        build_time=1,
        max_level=3,
        category=BuildingCategory.ALTYAPI,
        food_production=50,
        synergy_with=["farm", "soup_kitchen"],
        synergy_bonus_desc="Çiftlik ile: üretim +%10. İmaret ile: verim +%15.",
        historical_desc="Has Fırın, sarayın ve yeniçerilerin ekmek ihtiyacını karşılardı. Ekmek fiyatları ve kalitesi devlet kontrolündeydi.",
        level_names=["Fırın", "Kara Fırın", "Has Fırın"],
        unique_effects={
            'food_efficiency': 10,     # Gıda verimliliği
            'happiness': 2             # Tok halk mutludur
        },
        available_modules={
            'un_ambari': BuildingModuleStats(
                id='un_ambari',
                name="Flour Store",
                name_tr="Un Ambarı",
                description="Un stoklama - Süreklilik",
                cost_gold=150,
                cost_wood=50,
                cost_iron=0,
                effects={'food_production': 20},
                historical_desc="Değirmenlerden gelen unların saklandığı kuru depo."
            ),
            'hamurhane': BuildingModuleStats(
                id='hamurhane',
                name="Dough Room",
                name_tr="Hamurhane",
                description="Ekmek hazırlığı - Hız",
                cost_gold=200,
                cost_wood=20,
                cost_iron=10,
                effects={'food_efficiency': 10},
                historical_desc="Hamurların yoğurulduğu ve dinlendirildiği bölüm."
            )
        }
    ),
    BuildingType.COURT: BuildingStats(
        name="Court",
        name_tr="Kadı Konağı",
        description="Adalet ve hukuk merkezi - asayiş ve devlet otoritesi",
        cost_gold=800,
        cost_wood=200,
        cost_iron=20,
        maintenance=25,
        build_time=3,
        max_level=3,
        category=BuildingCategory.IDARI,
        happiness_bonus=5,
        prerequisite="medrese",
        synergy_with=["medrese", "barracks"],
        synergy_bonus_desc="Medrese ile: adalet +%20. Ocak ile: asayiş +%15.",
        historical_desc="Kadılar hem yargıç hem de belediye başkanıydı. Şer'iye sicilleri burada tutulurdu.",
        level_names=["Mahkeme", "Kadı Konağı", "Büyük Mahkeme"],
        unique_effects={
            'justice': 15,             # Adalet puanı
            'unrest_reduction': 10,    # Huzursuzluk düşüşü
            'corruption_reduction': 10 # Yolsuzluk önleme
        },
        available_modules={
            'sicil_odasi': BuildingModuleStats(
                id='sicil_odasi',
                name="Registry",
                name_tr="Sicil Odası",
                description="Kayıt tutma - Düzen",
                cost_gold=200,
                cost_wood=50,
                cost_iron=0,
                effects={'bureaucracy': 10, 'corruption_reduction': 5},
                historical_desc="Davaların ve kararların kaydedildiği defterlerin saklandığı oda."
            ),
            'hapis_hucre': BuildingModuleStats(
                id='hapis_hucre',
                name="Holding Cell",
                name_tr="Nezarethane",
                description="Suçlu tutma - Güvenlik",
                cost_gold=300,
                cost_wood=50,
                cost_iron=50,
                effects={'security': 10, 'unrest_reduction': 5},
                historical_desc="Yargılama öncesi suçluların bekletildiği bölüm."
            ),
            'kesif_heyeti': BuildingModuleStats(
                id='kesif_heyeti',
                name="Inspection Team",
                name_tr="Keşif Heyeti",
                description="Denetim - Gelir artışı",
                cost_gold=250,
                cost_wood=20,
                cost_iron=10,
                effects={'tax_efficiency': 5},
                historical_desc="Narh (fiyat) denetimi yapan görevliler odası."
            )
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
    installed_modules: List[str] = field(default_factory=list)  # Kurulu modüller
    
    def has_module(self, module_id: str) -> bool:
        """Bu modül kurulu mu?"""
        return module_id in self.installed_modules
    
    def install_module(self, module_id: str):
        """Modülü kur"""
        if module_id not in self.installed_modules:
            self.installed_modules.append(module_id)
    
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
        """Binanın özel etkisini seviye bazlı ve modülleriyle birlikte döndür"""
        stats = self.get_stats()
        total = 0
        if stats.unique_effects and effect_name in stats.unique_effects:
            base = stats.unique_effects[effect_name]
            total += int(base * (1 + (self.level - 1) * 0.3))  # Her seviye %30 artış
            
        # Kurulu modüllerden gelen etkileri ekle
        if stats.available_modules:
            for module_id in self.installed_modules:
                if module_id in stats.available_modules:
                    mod_stats = stats.available_modules[module_id]
                    if effect_name in mod_stats.effects:
                        total += mod_stats.effects[effect_name]
                        
        return total


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
    
    def get_building(self, building_type: BuildingType):
        """Bina nesnesini döndür (yoksa None)"""
        return self.buildings.get(building_type, None)
        
    def get_defense_bonus(self) -> int:
        """Kuşatmalarda kale ve kulelerden gelen savunma/moral bonusu"""
        bonus = 0
        if BuildingType.FORTRESS in self.buildings:
            bonus += self.buildings[BuildingType.FORTRESS].level * 2
        if BuildingType.WATCHTOWER in self.buildings:
            bonus += self.buildings[BuildingType.WATCHTOWER].level * 1
        return bonus
    
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
        
        # Kuyrukta bekleyen yükseltmeleri say
        pending_upgrades = sum(
            1 for q in self.construction_queue 
            if q.building_type == building_type and q.is_upgrade
        )
        effective_level = building.level + pending_upgrades
        if effective_level >= stats.max_level:
            return False, f"Maksimum seviye ({stats.max_level}). Kuyrukta {pending_upgrades} yükseltme bekliyor"
        
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
        next_level = building.level + 1
        level_name = building.get_level_name() # Mevcut seviye adı
        # Gelecek seviye adı için geçici trick:
        # Building sınıfının get_level_name metodu self.level kullanır.
        # Bu yüzden burada tam doğru ismi alamayabiliriz (statik liste lazım).
        # Ancak stats.level_names varsa oradan alabiliriz.
        
        target_name = f"Seviye {next_level}"
        if hasattr(stats, 'level_names') and len(stats.level_names) >= next_level:
            try:
                # Seviye 1 -> index 0
                target_name = f"{stats.level_names[next_level - 1]} (Seviye {next_level})"
            except IndexError:
                target_name = f"Seviye {next_level}"
            
        audio.announce_action_result(
            f"{stats.name_tr} Yükseltme",
            True,
            f"{target_name} seviyesine yükseltiliyor ({stats.max_level}. seviyeye kadar yükseltilebilir)"
        )
        
        return True
    
    def process_turn(self):
        """Tur sonunda inşaatları işle"""
        completed = []
        messages = []
        
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
                    msg = f"{stats.name_tr} yükseltildi: {level_name}!"
                    audio.announce(msg)
                    messages.append(msg)
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
                msg = f"{stats.name_tr} tamamlandı! ({level_name})"
                audio.announce(msg)
                messages.append(msg)
                # Sinerji bildirimi
                synergy_mult = self.get_synergy_multiplier(item.building_type)
                if synergy_mult > 1.0:
                    bonus_pct = int((synergy_mult - 1.0) * 100)
                    audio.announce(f"Sinerji bonusu aktif: +%{bonus_pct}")
        
        return messages
    
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
    
    def get_stone_production(self) -> int:
        """Taş üretimi (YENİ)"""
        if BuildingType.QUARRY in self.buildings:
            # Taş Ocağı seviye başına 50 taş
            return self.buildings[BuildingType.QUARRY].level * 50
        return 0
    
    def get_naval_supplies_production(self) -> Dict[str, int]:
        """Denizcilik malzemeleri üretimi (YENİ)"""
        production = {'rope': 0, 'tar': 0, 'sailcloth': 0}
        
        if BuildingType.ROPEMAKER in self.buildings:
            building = self.buildings[BuildingType.ROPEMAKER]
            # Halat Atölyesi ve alt modüllerinden gelen üretimleri topla
            production['rope'] = building.get_unique_effect('rope_production')
            production['tar'] = building.get_unique_effect('tar_production')
            production['sailcloth'] = building.get_unique_effect('sailcloth_production')
            
        return production
    
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
                k.value: {
                    'level': v.level,
                    'installed_modules': getattr(v, 'installed_modules', [])
                }
                for k, v in self.buildings.items()
            },
            'construction_queue': [
                {
                    'type': item.building_type.value,
                    'turns': item.turns_remaining,
                    'is_upgrade': item.is_upgrade,
                    'module_id': getattr(item, 'module_id', None)
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
                building = Building(bt, level=v['level'])
                building.installed_modules = v.get('installed_modules', [])
                system.buildings[bt] = building
            except ValueError:
                continue  # Bilinmeyen bina tipi (eski kayıt uyumluluğu)
        
        system.construction_queue = []
        for item in data.get('construction_queue', []):
            try:
                bt = BuildingType(item['type'])
                queue_item = ConstructionQueue(
                    bt,
                    item['turns'],
                    item.get('is_upgrade', False)
                )
                if 'module_id' in item and item['module_id']:
                    queue_item.module_id = item['module_id']
                system.construction_queue.append(queue_item)
            except ValueError:
                continue  # Bilinmeyen bina tipi
        
        return system
