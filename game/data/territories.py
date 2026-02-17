# -*- coding: utf-8 -*-
"""
Osmanlı Eyalet Yönetim Simülasyonu - Bölge Verileri (1520 Dönemi)
Tüm eyaletler, sancaklar, vasal ve komşu devletler
"""

from enum import Enum
from dataclasses import dataclass
from typing import Dict, List, Optional


class TerritoryType(Enum):
    """Bölge türleri"""
    OSMANLI_EYALET = "osmanli_eyalet"      # Doğrudan yönetim - büyük eyalet
    OSMANLI_SANCAK = "osmanli_sancak"      # Doğrudan yönetim - sancak
    VASAL = "vasal"                         # Yarı-bağımsız vasal devlet
    KOMSU_DEVLET = "komsu_devlet"          # Bağımsız komşu devlet


class Region(Enum):
    """Coğrafi bölgeler"""
    ANADOLU = "anadolu"
    BALKANLAR = "balkanlar"
    ORTADOGU = "ortadogu"
    AFRIKA = "afrika"
    ADALAR = "adalar"
    KARADENIZ = "karadeniz"
    AVRUPA = "avrupa"
    IRAN = "iran"


@dataclass
class Territory:
    """Bölge bilgisi"""
    name: str
    territory_type: TerritoryType
    region: Region
    capital: str
    is_coastal: bool = False
    starting_population: int = 15000
    special_resources: List[str] = None
    # Vergi/gelir tipi — Simülasyonun temel ekonomik parametresi
    # "salyanesiz" = Tımar sistemi (askeri güç sağlar, dirlik dağıtımı)
    # "salyaneli"  = Yıllık nakit vergi (altın sağlar, hazineye aktarılır)
    # "karma"      = Her ikisinin karışımı (Cezayir-i Bahr-i Sefid gibi)
    tax_type: str = "salyanesiz"
    # Komşular: (yön, bölge_adı) şeklinde
    neighbors_north: List[str] = None
    neighbors_south: List[str] = None
    neighbors_east: List[str] = None
    neighbors_west: List[str] = None
    
    def __post_init__(self):
        if self.special_resources is None:
            self.special_resources = []
        if self.neighbors_north is None:
            self.neighbors_north = []
        if self.neighbors_south is None:
            self.neighbors_south = []
        if self.neighbors_east is None:
            self.neighbors_east = []
        if self.neighbors_west is None:
            self.neighbors_west = []


# ============================================================
# TÜM BÖLGELER - 1520 Kanuni Sultan Süleyman Dönemi
# ============================================================

TERRITORIES: Dict[str, Territory] = {
    
    # ========== ANADOLU BÖLGESİ ==========
    
    "Rum Eyaleti": Territory(
        name="Rum Eyaleti",
        territory_type=TerritoryType.OSMANLI_EYALET,
        region=Region.ANADOLU,
        capital="Sivas",
        is_coastal=False,
        starting_population=25000,
        special_resources=["tahıl", "at"],
        neighbors_north=["Trabzon Eyaleti", "Kastamonu Sancağı"],
        neighbors_south=["Karaman Eyaleti", "Dulkadir Eyaleti"],
        neighbors_east=["Diyarbekir Eyaleti"],
        neighbors_west=["Anadolu Eyaleti"]
    ),
    
    "Anadolu Eyaleti": Territory(
        name="Anadolu Eyaleti",
        territory_type=TerritoryType.OSMANLI_EYALET,
        region=Region.ANADOLU,
        capital="Kütahya",
        is_coastal=False,
        starting_population=30000,
        special_resources=["tahıl", "yün"],
        neighbors_north=["Kastamonu Sancağı", "Bolu Sancağı"],
        neighbors_south=["Karaman Eyaleti", "Hamid Sancağı"],
        neighbors_east=["Rum Eyaleti"],
        neighbors_west=["Saruhan Sancağı", "Aydın Sancağı"]
    ),
    
    "Karaman Eyaleti": Territory(
        name="Karaman Eyaleti",
        territory_type=TerritoryType.OSMANLI_EYALET,
        region=Region.ANADOLU,
        capital="Konya",
        is_coastal=False,
        starting_population=28000,
        special_resources=["tahıl", "halı"],
        neighbors_north=["Rum Eyaleti", "Anadolu Eyaleti"],
        neighbors_south=["Teke Sancağı"],
        neighbors_east=["Dulkadir Eyaleti"],
        neighbors_west=["Hamid Sancağı"]
    ),
    
    "Dulkadir Eyaleti": Territory(
        name="Dulkadir Eyaleti",
        territory_type=TerritoryType.OSMANLI_EYALET,
        region=Region.ANADOLU,
        capital="Maraş",
        is_coastal=False,
        starting_population=18000,
        special_resources=["tahıl"],
        neighbors_north=["Rum Eyaleti"],
        neighbors_south=["Halep Eyaleti"],
        neighbors_east=["Diyarbekir Eyaleti"],
        neighbors_west=["Karaman Eyaleti"]
    ),
    
    "Diyarbekir Eyaleti": Territory(
        name="Diyarbekir Eyaleti",
        territory_type=TerritoryType.OSMANLI_EYALET,
        region=Region.ANADOLU,
        capital="Diyarbakır",
        is_coastal=False,
        starting_population=20000,
        special_resources=["bakır", "demir"],
        neighbors_north=["Trabzon Eyaleti"],
        neighbors_south=["Musul Sancağı", "Rakka Sancağı"],
        neighbors_east=["Safevi İmparatorluğu"],
        neighbors_west=["Rum Eyaleti", "Dulkadir Eyaleti"]
    ),
    
    "Trabzon Eyaleti": Territory(
        name="Trabzon Eyaleti",
        territory_type=TerritoryType.OSMANLI_EYALET,
        region=Region.KARADENIZ,
        capital="Trabzon",
        is_coastal=True,
        starting_population=15000,
        special_resources=["fındık", "balık"],
        neighbors_north=["Kırım Hanlığı"],  # Deniz yoluyla
        neighbors_south=["Diyarbekir Eyaleti"],
        neighbors_east=["Gürcü Beylikleri", "Safevi İmparatorluğu"],
        neighbors_west=["Rum Eyaleti", "Kastamonu Sancağı"]
    ),
    
    "Kastamonu Sancağı": Territory(
        name="Kastamonu Sancağı",
        territory_type=TerritoryType.OSMANLI_SANCAK,
        region=Region.KARADENIZ,
        capital="Kastamonu",
        is_coastal=True,
        starting_population=12000,
        special_resources=["kereste", "bakır"],
        neighbors_north=["Kırım Hanlığı"],  # Deniz yoluyla
        neighbors_south=["Anadolu Eyaleti"],
        neighbors_east=["Trabzon Eyaleti", "Rum Eyaleti"],
        neighbors_west=["Bolu Sancağı"]
    ),
    
    "Bolu Sancağı": Territory(
        name="Bolu Sancağı",
        territory_type=TerritoryType.OSMANLI_SANCAK,
        region=Region.ANADOLU,
        capital="Bolu",
        is_coastal=False,
        starting_population=10000,
        special_resources=["kereste"],
        neighbors_north=[],  # Karadeniz
        neighbors_south=["Anadolu Eyaleti"],
        neighbors_east=["Kastamonu Sancağı"],
        neighbors_west=["Hüdavendigar Sancağı"]
    ),
    
    "Hüdavendigar Sancağı": Territory(
        name="Hüdavendigar Sancağı",
        territory_type=TerritoryType.OSMANLI_SANCAK,
        region=Region.ANADOLU,
        capital="Bursa",
        is_coastal=True,
        starting_population=35000,
        special_resources=["ipek", "tekstil"],
        neighbors_north=[],  # Marmara Denizi
        neighbors_south=["Anadolu Eyaleti"],
        neighbors_east=["Bolu Sancağı"],
        neighbors_west=["Karesi Sancağı"]
    ),
    
    "Karesi Sancağı": Territory(
        name="Karesi Sancağı",
        territory_type=TerritoryType.OSMANLI_SANCAK,
        region=Region.ANADOLU,
        capital="Balıkesir",
        is_coastal=True,
        starting_population=14000,
        special_resources=["zeytin"],
        neighbors_north=[],  # Marmara
        neighbors_south=["Saruhan Sancağı"],
        neighbors_east=["Hüdavendigar Sancağı"],
        neighbors_west=[]  # Ege Denizi
    ),
    
    "Saruhan Sancağı": Territory(
        name="Saruhan Sancağı",
        territory_type=TerritoryType.OSMANLI_SANCAK,
        region=Region.ANADOLU,
        capital="Manisa",
        is_coastal=False,
        starting_population=16000,
        special_resources=["üzüm", "pamuk"],
        neighbors_north=["Karesi Sancağı"],
        neighbors_south=["Aydın Sancağı"],
        neighbors_east=["Anadolu Eyaleti"],
        neighbors_west=[]  # Ege Denizi
    ),
    
    "Aydın Sancağı": Territory(
        name="Aydın Sancağı",
        territory_type=TerritoryType.OSMANLI_SANCAK,
        region=Region.ANADOLU,
        capital="Tire",
        is_coastal=True,
        starting_population=18000,
        special_resources=["incir", "pamuk"],
        neighbors_north=["Saruhan Sancağı"],
        neighbors_south=["Menteşe Sancağı"],
        neighbors_east=["Anadolu Eyaleti"],
        neighbors_west=["Sakız Adası", "Venedik"]  # Deniz
    ),
    
    "Menteşe Sancağı": Territory(
        name="Menteşe Sancağı",
        territory_type=TerritoryType.OSMANLI_SANCAK,
        region=Region.ANADOLU,
        capital="Muğla",
        is_coastal=True,
        starting_population=12000,
        special_resources=["bal"],
        neighbors_north=["Aydın Sancağı"],
        neighbors_south=["Teke Sancağı"],
        neighbors_east=["Hamid Sancağı"],
        neighbors_west=["Rodos", "Venedik"]  # Deniz
    ),
    
    "Teke Sancağı": Territory(
        name="Teke Sancağı",
        territory_type=TerritoryType.OSMANLI_SANCAK,
        region=Region.ANADOLU,
        capital="Antalya",
        is_coastal=True,
        starting_population=14000,
        special_resources=["kereste", "narenciye"],
        neighbors_north=["Hamid Sancağı", "Karaman Eyaleti"],
        neighbors_south=["Kıbrıs"],  # Deniz
        neighbors_east=[],
        neighbors_west=["Menteşe Sancağı"]
    ),
    
    "Hamid Sancağı": Territory(
        name="Hamid Sancağı",
        territory_type=TerritoryType.OSMANLI_SANCAK,
        region=Region.ANADOLU,
        capital="Isparta",
        is_coastal=False,
        starting_population=11000,
        special_resources=["gül", "halı"],
        neighbors_north=["Anadolu Eyaleti"],
        neighbors_south=["Teke Sancağı"],
        neighbors_east=["Karaman Eyaleti"],
        neighbors_west=["Menteşe Sancağı"]
    ),
    
    # ========== BALKANLAR ==========
    
    "Rumeli Eyaleti": Territory(
        name="Rumeli Eyaleti",
        territory_type=TerritoryType.OSMANLI_EYALET,
        region=Region.BALKANLAR,
        capital="Sofya",
        is_coastal=False,
        starting_population=40000,
        special_resources=["tahıl", "gümüş"],
        neighbors_north=["Silistre Sancağı", "Niğbolu Sancağı"],
        neighbors_south=["Selanik Sancağı", "Ohri Sancağı"],
        neighbors_east=[],  # Karadeniz
        neighbors_west=["Bosna Sancağı", "Semendire Sancağı"]
    ),
    
    "Selanik Sancağı": Territory(
        name="Selanik Sancağı",
        territory_type=TerritoryType.OSMANLI_SANCAK,
        region=Region.BALKANLAR,
        capital="Selanik",
        is_coastal=True,
        starting_population=25000,
        special_resources=["tekstil", "tuz"],
        neighbors_north=["Rumeli Eyaleti", "Üsküp Sancağı"],
        neighbors_south=["Mora Sancağı", "Yanya Sancağı"],
        neighbors_east=[],  # Ege Denizi
        neighbors_west=["Ohri Sancağı"]
    ),
    
    "Mora Sancağı": Territory(
        name="Mora Sancağı",
        territory_type=TerritoryType.OSMANLI_SANCAK,
        region=Region.BALKANLAR,
        capital="Tripoliçe",
        is_coastal=True,
        starting_population=15000,
        special_resources=["zeytin", "şarap"],
        neighbors_north=["Selanik Sancağı", "Yanya Sancağı"],
        neighbors_south=[],  # Akdeniz
        neighbors_east=[],  # Ege Denizi
        neighbors_west=["Venedik"]  # Deniz
    ),
    
    "Yanya Sancağı": Territory(
        name="Yanya Sancağı",
        territory_type=TerritoryType.OSMANLI_SANCAK,
        region=Region.BALKANLAR,
        capital="Yanya",
        is_coastal=True,
        starting_population=12000,
        special_resources=["zeytin"],
        neighbors_north=["Ohri Sancağı", "Arnavutluk Sancağı"],
        neighbors_south=["Mora Sancağı"],
        neighbors_east=["Selanik Sancağı"],
        neighbors_west=["Venedik"]  # Deniz (Korfu)
    ),
    
    "Ohri Sancağı": Territory(
        name="Ohri Sancağı",
        territory_type=TerritoryType.OSMANLI_SANCAK,
        region=Region.BALKANLAR,
        capital="Ohri",
        is_coastal=False,
        starting_population=10000,
        special_resources=["balık"],
        neighbors_north=["Üsküp Sancağı", "Kosova Sancağı"],
        neighbors_south=["Yanya Sancağı"],
        neighbors_east=["Selanik Sancağı", "Rumeli Eyaleti"],
        neighbors_west=["Arnavutluk Sancağı"]
    ),
    
    "Üsküp Sancağı": Territory(
        name="Üsküp Sancağı",
        territory_type=TerritoryType.OSMANLI_SANCAK,
        region=Region.BALKANLAR,
        capital="Üsküp",
        is_coastal=False,
        starting_population=14000,
        special_resources=["demir"],
        neighbors_north=["Kosova Sancağı"],
        neighbors_south=["Selanik Sancağı", "Ohri Sancağı"],
        neighbors_east=["Rumeli Eyaleti"],
        neighbors_west=[]
    ),
    
    "Kosova Sancağı": Territory(
        name="Kosova Sancağı",
        territory_type=TerritoryType.OSMANLI_SANCAK,
        region=Region.BALKANLAR,
        capital="Priştine",
        is_coastal=False,
        starting_population=12000,
        special_resources=["gümüş", "kurşun"],
        neighbors_north=["Semendire Sancağı"],
        neighbors_south=["Üsküp Sancağı", "Ohri Sancağı"],
        neighbors_east=["Rumeli Eyaleti"],
        neighbors_west=["Bosna Sancağı"]
    ),
    
    "Semendire Sancağı": Territory(
        name="Semendire Sancağı",
        territory_type=TerritoryType.OSMANLI_SANCAK,
        region=Region.BALKANLAR,
        capital="Semendire",
        is_coastal=False,
        starting_population=15000,
        special_resources=["tahıl"],
        neighbors_north=["Macaristan Krallığı"],
        neighbors_south=["Kosova Sancağı"],
        neighbors_east=["Vidin Sancağı"],
        neighbors_west=["Bosna Sancağı"]
    ),
    
    "Vidin Sancağı": Territory(
        name="Vidin Sancağı",
        territory_type=TerritoryType.OSMANLI_SANCAK,
        region=Region.BALKANLAR,
        capital="Vidin",
        is_coastal=False,
        starting_population=10000,
        special_resources=["tahıl"],
        neighbors_north=["Eflak Voyvodalığı"],
        neighbors_south=["Rumeli Eyaleti"],
        neighbors_east=["Niğbolu Sancağı"],
        neighbors_west=["Semendire Sancağı"]
    ),
    
    "Niğbolu Sancağı": Territory(
        name="Niğbolu Sancağı",
        territory_type=TerritoryType.OSMANLI_SANCAK,
        region=Region.BALKANLAR,
        capital="Niğbolu",
        is_coastal=False,
        starting_population=12000,
        special_resources=["tahıl"],
        neighbors_north=["Eflak Voyvodalığı"],
        neighbors_south=["Rumeli Eyaleti"],
        neighbors_east=["Silistre Sancağı"],
        neighbors_west=["Vidin Sancağı"]
    ),
    
    "Silistre Sancağı": Territory(
        name="Silistre Sancağı",
        territory_type=TerritoryType.OSMANLI_SANCAK,
        region=Region.BALKANLAR,
        capital="Silistre",
        is_coastal=True,
        starting_population=13000,
        special_resources=["balık", "tahıl"],
        neighbors_north=["Boğdan Voyvodalığı"],
        neighbors_south=["Rumeli Eyaleti"],
        neighbors_east=["Kırım Hanlığı"],  # Deniz
        neighbors_west=["Niğbolu Sancağı"]
    ),
    
    "Bosna Sancağı": Territory(
        name="Bosna Sancağı",
        territory_type=TerritoryType.OSMANLI_SANCAK,
        region=Region.BALKANLAR,
        capital="Saraybosna",
        is_coastal=False,
        starting_population=18000,
        special_resources=["demir", "gümüş"],
        neighbors_north=["Macaristan Krallığı"],
        neighbors_south=["Hersek Sancağı"],
        neighbors_east=["Semendire Sancağı", "Kosova Sancağı"],
        neighbors_west=["Venedik", "Avusturya"]
    ),
    
    "Hersek Sancağı": Territory(
        name="Hersek Sancağı",
        territory_type=TerritoryType.OSMANLI_SANCAK,
        region=Region.BALKANLAR,
        capital="Mostar",
        is_coastal=True,
        starting_population=10000,
        special_resources=["kereste"],
        neighbors_north=["Bosna Sancağı"],
        neighbors_south=["Arnavutluk Sancağı"],
        neighbors_east=["Kosova Sancağı"],
        neighbors_west=["Venedik", "Ragusa Cumhuriyeti"]
    ),
    
    "Arnavutluk Sancağı": Territory(
        name="Arnavutluk Sancağı",
        territory_type=TerritoryType.OSMANLI_SANCAK,
        region=Region.BALKANLAR,
        capital="İşkodra",
        is_coastal=True,
        starting_population=14000,
        special_resources=["zeytin"],
        neighbors_north=["Hersek Sancağı"],
        neighbors_south=["Yanya Sancağı"],
        neighbors_east=["Ohri Sancağı"],
        neighbors_west=["Venedik"]  # Deniz
    ),
    
    # ========== ORTADOĞU ==========
    
    "Halep Eyaleti": Territory(
        name="Halep Eyaleti",
        territory_type=TerritoryType.OSMANLI_EYALET,
        region=Region.ORTADOGU,
        capital="Halep",
        is_coastal=False,
        starting_population=35000,
        special_resources=["ipek", "baharat"],
        neighbors_north=["Dulkadir Eyaleti"],
        neighbors_south=["Şam Eyaleti"],
        neighbors_east=["Rakka Sancağı", "Safevi İmparatorluğu"],
        neighbors_west=[]  # Akdeniz kıyısına yakın
    ),
    
    "Şam Eyaleti": Territory(
        name="Şam Eyaleti",
        territory_type=TerritoryType.OSMANLI_EYALET,
        region=Region.ORTADOGU,
        capital="Şam",
        is_coastal=True,
        starting_population=40000,
        special_resources=["ipek", "cam"],
        neighbors_north=["Halep Eyaleti"],
        neighbors_south=["Mısır Eyaleti"],
        neighbors_east=["Rakka Sancağı"],
        neighbors_west=["Kıbrıs"]  # Deniz
    ),
    
    "Rakka Sancağı": Territory(
        name="Rakka Sancağı",
        territory_type=TerritoryType.OSMANLI_SANCAK,
        region=Region.ORTADOGU,
        capital="Rakka",
        is_coastal=False,
        starting_population=10000,
        special_resources=["tahıl"],
        neighbors_north=["Diyarbekir Eyaleti"],
        neighbors_south=["Şam Eyaleti"],
        neighbors_east=["Musul Sancağı"],
        neighbors_west=["Halep Eyaleti"]
    ),
    
    "Musul Sancağı": Territory(
        name="Musul Sancağı",
        territory_type=TerritoryType.OSMANLI_SANCAK,
        region=Region.ORTADOGU,
        capital="Musul",
        is_coastal=False,
        starting_population=15000,
        special_resources=["petrol", "tahıl"],
        neighbors_north=["Diyarbekir Eyaleti"],
        neighbors_south=[],
        neighbors_east=["Safevi İmparatorluğu"],
        neighbors_west=["Rakka Sancağı"]
    ),
    
    # ========== AFRİKA ==========
    
    "Mısır Eyaleti": Territory(
        name="Mısır Eyaleti",
        territory_type=TerritoryType.OSMANLI_EYALET,
        region=Region.AFRIKA,
        capital="Kahire",
        is_coastal=True,
        starting_population=80000,
        special_resources=["tahıl", "pamuk", "baharat"],
        tax_type="salyaneli",  # Yıllık nakit vergi — donanma finansmanı
        neighbors_north=["Şam Eyaleti"],
        neighbors_south=[],
        neighbors_east=[],
        neighbors_west=["Trablusgarp Eyaleti"]
    ),
    
    "Trablusgarp Eyaleti": Territory(
        name="Trablusgarp Eyaleti",
        territory_type=TerritoryType.OSMANLI_EYALET,
        region=Region.AFRIKA,
        capital="Trablus",
        is_coastal=True,
        starting_population=15000,
        special_resources=["tuz"],
        tax_type="salyaneli",  # Garp Ocakları — nakit vergi
        neighbors_north=["Venedik"],  # Deniz
        neighbors_south=[],
        neighbors_east=["Mısır Eyaleti"],
        neighbors_west=["Cezayir Eyaleti"]
    ),
    
    "Cezayir Eyaleti": Territory(
        name="Cezayir Eyaleti",
        territory_type=TerritoryType.OSMANLI_EYALET,
        region=Region.AFRIKA,
        capital="Cezayir",
        is_coastal=True,
        starting_population=20000,
        special_resources=["korsanlık"],
        tax_type="karma",  # Hem donanma hem korsanlık geliri — karma sistem
        neighbors_north=["İspanya"],  # Deniz
        neighbors_south=[],
        neighbors_east=["Trablusgarp Eyaleti"],
        neighbors_west=[]
    ),
    
    # ========== ADALAR ==========
    
    "Rodos": Territory(
        name="Rodos",
        territory_type=TerritoryType.KOMSU_DEVLET,  # 1522'de fethedilecek
        region=Region.ADALAR,
        capital="Rodos",
        is_coastal=True,
        starting_population=8000,
        special_resources=["denizcilik"],
        neighbors_north=["Menteşe Sancağı"],
        neighbors_south=["Kıbrıs"],
        neighbors_east=[],
        neighbors_west=["Mora Sancağı"]
    ),
    
    "Kıbrıs": Territory(
        name="Kıbrıs",
        territory_type=TerritoryType.KOMSU_DEVLET,  # Venedik kontrolünde
        region=Region.ADALAR,
        capital="Lefkoşa",
        is_coastal=True,
        starting_population=12000,
        special_resources=["bakır", "şarap"],
        neighbors_north=["Teke Sancağı"],
        neighbors_south=["Mısır Eyaleti"],
        neighbors_east=["Şam Eyaleti"],
        neighbors_west=["Rodos"]
    ),
    
    "Girit": Territory(
        name="Girit",
        territory_type=TerritoryType.KOMSU_DEVLET,  # Venedik kontrolünde
        region=Region.ADALAR,
        capital="Kandiye",
        is_coastal=True,
        starting_population=15000,
        special_resources=["şarap", "zeytin"],
        neighbors_north=["Mora Sancağı"],
        neighbors_south=["Mısır Eyaleti"],
        neighbors_east=["Rodos"],
        neighbors_west=[]
    ),
    
    # ========== VASAL DEVLETLER ==========
    
    "Kırım Hanlığı": Territory(
        name="Kırım Hanlığı",
        territory_type=TerritoryType.VASAL,
        region=Region.KARADENIZ,
        capital="Bahçesaray",
        is_coastal=True,
        starting_population=50000,
        special_resources=["at", "köle ticareti"],
        neighbors_north=["Lehistan-Litvanya"],
        neighbors_south=["Trabzon Eyaleti", "Kastamonu Sancağı"],  # Deniz
        neighbors_east=[],
        neighbors_west=["Boğdan Voyvodalığı", "Silistre Sancağı"]
    ),
    
    "Eflak Voyvodalığı": Territory(
        name="Eflak Voyvodalığı",
        territory_type=TerritoryType.VASAL,
        region=Region.BALKANLAR,
        capital="Bükreş",
        is_coastal=False,
        starting_population=30000,
        special_resources=["tahıl", "petrol"],
        neighbors_north=["Erdel Prensliği", "Boğdan Voyvodalığı"],
        neighbors_south=["Vidin Sancağı", "Niğbolu Sancağı"],
        neighbors_east=["Boğdan Voyvodalığı"],
        neighbors_west=["Macaristan Krallığı"]
    ),
    
    "Boğdan Voyvodalığı": Territory(
        name="Boğdan Voyvodalığı",
        territory_type=TerritoryType.VASAL,
        region=Region.BALKANLAR,
        capital="Yaş",
        is_coastal=True,
        starting_population=25000,
        special_resources=["tahıl", "bal"],
        neighbors_north=["Lehistan-Litvanya"],
        neighbors_south=["Silistre Sancağı"],
        neighbors_east=["Kırım Hanlığı"],
        neighbors_west=["Eflak Voyvodalığı", "Erdel Prensliği"]
    ),
    
    "Erdel Prensliği": Territory(
        name="Erdel Prensliği",
        territory_type=TerritoryType.VASAL,  # 1526 sonrası vasal olacak
        region=Region.BALKANLAR,
        capital="Kolozsvár",
        is_coastal=False,
        starting_population=35000,
        special_resources=["altın", "gümüş", "tuz"],
        neighbors_north=["Lehistan-Litvanya"],
        neighbors_south=["Eflak Voyvodalığı"],
        neighbors_east=["Boğdan Voyvodalığı"],
        neighbors_west=["Macaristan Krallığı"]
    ),
    
    "Ragusa Cumhuriyeti": Territory(
        name="Ragusa Cumhuriyeti",
        territory_type=TerritoryType.VASAL,
        region=Region.BALKANLAR,
        capital="Dubrovnik",
        is_coastal=True,
        starting_population=8000,
        special_resources=["ticaret", "denizcilik"],
        neighbors_north=["Hersek Sancağı"],
        neighbors_south=[],
        neighbors_east=["Arnavutluk Sancağı"],
        neighbors_west=["Venedik"]
    ),
    
    # ========== KOMŞU DEVLETLER ==========
    
    "Safevi İmparatorluğu": Territory(
        name="Safevi İmparatorluğu",
        territory_type=TerritoryType.KOMSU_DEVLET,
        region=Region.IRAN,
        capital="Tebriz",
        is_coastal=False,
        starting_population=150000,
        special_resources=["ipek", "halı", "at"],
        neighbors_north=["Gürcü Beylikleri"],
        neighbors_south=[],
        neighbors_east=[],
        neighbors_west=["Trabzon Eyaleti", "Diyarbekir Eyaleti", "Musul Sancağı"]
    ),
    
    "Gürcü Beylikleri": Territory(
        name="Gürcü Beylikleri",
        territory_type=TerritoryType.KOMSU_DEVLET,
        region=Region.KARADENIZ,
        capital="Tiflis",
        is_coastal=True,
        starting_population=20000,
        special_resources=["şarap"],
        neighbors_north=[],
        neighbors_south=["Safevi İmparatorluğu"],
        neighbors_east=[],
        neighbors_west=["Trabzon Eyaleti"]
    ),
    
    "Macaristan Krallığı": Territory(
        name="Macaristan Krallığı",
        territory_type=TerritoryType.KOMSU_DEVLET,
        region=Region.AVRUPA,
        capital="Budin",
        is_coastal=False,
        starting_population=100000,
        special_resources=["tahıl", "şarap", "altın"],
        neighbors_north=["Lehistan-Litvanya", "Avusturya"],
        neighbors_south=["Semendire Sancağı", "Bosna Sancağı"],
        neighbors_east=["Erdel Prensliği", "Eflak Voyvodalığı"],
        neighbors_west=["Avusturya", "Venedik"]
    ),
    
    "Lehistan-Litvanya": Territory(
        name="Lehistan-Litvanya",
        territory_type=TerritoryType.KOMSU_DEVLET,
        region=Region.AVRUPA,
        capital="Krakov",
        is_coastal=True,
        starting_population=120000,
        special_resources=["tahıl", "kereste", "kehribar"],
        neighbors_north=[],
        neighbors_south=["Boğdan Voyvodalığı", "Erdel Prensliği", "Macaristan Krallığı"],
        neighbors_east=["Kırım Hanlığı"],
        neighbors_west=["Avusturya"]
    ),
    
    "Venedik": Territory(
        name="Venedik",
        territory_type=TerritoryType.KOMSU_DEVLET,
        region=Region.AVRUPA,
        capital="Venedik",
        is_coastal=True,
        starting_population=60000,
        special_resources=["cam", "ticaret", "denizcilik"],
        neighbors_north=["Avusturya"],
        neighbors_south=["Mora Sancağı", "Yanya Sancağı"],  # Deniz
        neighbors_east=["Arnavutluk Sancağı", "Hersek Sancağı"],  # Deniz
        neighbors_west=["Papalık Devletleri"]
    ),
    
    "Avusturya": Territory(
        name="Avusturya",
        territory_type=TerritoryType.KOMSU_DEVLET,
        region=Region.AVRUPA,
        capital="Viyana",
        is_coastal=False,
        starting_population=80000,
        special_resources=["demir", "gümüş"],
        neighbors_north=["Lehistan-Litvanya"],
        neighbors_south=["Venedik", "Macaristan Krallığı"],
        neighbors_east=["Macaristan Krallığı"],
        neighbors_west=[]
    ),
    
    "Papalık Devletleri": Territory(
        name="Papalık Devletleri",
        territory_type=TerritoryType.KOMSU_DEVLET,
        region=Region.AVRUPA,
        capital="Roma",
        is_coastal=True,
        starting_population=40000,
        special_resources=["sanat", "din"],
        neighbors_north=["Venedik"],
        neighbors_south=["Napoli Krallığı"],
        neighbors_east=[],  # Adriyatik
        neighbors_west=[]
    ),
    
    "Napoli Krallığı": Territory(
        name="Napoli Krallığı",
        territory_type=TerritoryType.KOMSU_DEVLET,
        region=Region.AVRUPA,
        capital="Napoli",
        is_coastal=True,
        starting_population=50000,
        special_resources=["tahıl", "ipek"],
        neighbors_north=["Papalık Devletleri"],
        neighbors_south=[],  # Akdeniz
        neighbors_east=["Arnavutluk Sancağı"],  # Deniz
        neighbors_west=[]
    ),
    
    "İspanya": Territory(
        name="İspanya",
        territory_type=TerritoryType.KOMSU_DEVLET,
        region=Region.AVRUPA,
        capital="Madrid",
        is_coastal=True,
        starting_population=150000,
        special_resources=["altın", "gümüş", "yeni dünya"],
        neighbors_north=[],
        neighbors_south=["Cezayir Eyaleti"],  # Deniz
        neighbors_east=[],
        neighbors_west=[]
    ),
}


# Oynanabilir bölgeler listesi (çok oyunculu için)

# ════════════════════════════════════════════════════════════
# VASAL DEVLET HARAÇ VERİLERİ (1520-1566 Dönemi)
# Kaynak: Osmanlı Maliye Defterleri, Diplomatik Yazışmalar
# ════════════════════════════════════════════════════════════
VASSAL_TRIBUTE_DATA = {
    "Kırım Hanlığı": {
        "ruler_title": "Han",
        "tribute_min_gold": 0,
        "tribute_max_gold": 0,
        "military_obligation": True,
        "obligation_details": "Seferlere 50.000+ süvari ile katılım",
        "emtia_obligations": ["at", "esir"],
        "strategic_role": "Kuzey sınır güvenliği, Lehistan/Rusya tamponu",
        "special_ability": "slave_trade",
        "political_risk": "low",
        "historical_note": "Giray hanedanı — haraç ödemez, askeri güç sağlar. Osmanlı'nın en güçlü vasalı."
    },
    "Eflak Voyvodalığı": {
        "ruler_title": "Voyvoda",
        "tribute_min_gold": 14000,
        "tribute_max_gold": 24000,
        "military_obligation": True,
        "obligation_details": "Savaş zamanı asker ve zahire sağlama",
        "emtia_obligations": ["bal", "balmumu", "at", "tuz", "kereste"],
        "strategic_role": "Macaristan/Avusturya tamponu",
        "political_risk": "high",  # Boyar İsyanları ve Avusturya Etkisi
        "historical_note": "Haraç 14.000-24.000 Duka arası. Voyvoda İstanbul'dan atanır. Boyar isyanları riski yüksek."
    },
    "Boğdan Voyvodalığı": {
        "ruler_title": "Voyvoda",
        "tribute_min_gold": 4000,
        "tribute_max_gold": 12000,
        "military_obligation": True,
        "obligation_details": "Karadeniz güvenliği, zahire sağlama",
        "emtia_obligations": ["sığır", "koyun", "buğday"],
        "strategic_role": "Karadeniz güvenliği",
        "political_risk": "medium",  # Lehistan Etkisi ve Kazak Saldırıları
        "historical_note": "Yıllık 500-1000 baş sığır yükümlülüğü. Lehistan etkisi ve Kazak saldırıları riski."
    },
    "Erdel Prensliği": {
        "ruler_title": "Prens",
        "tribute_min_gold": 10000,
        "tribute_max_gold": 15000,
        "military_obligation": True,
        "obligation_details": "Seferde askeri destek, maden cevheri ve tuz sağlama",
        "emtia_obligations": ["maden_cevheri", "tuz"],
        "strategic_role": "Habsburg Avusturya'ya karşı denge unsuru",
        "political_risk": "medium_high",  # Habsburg Sınır Çatışmaları
        "historical_note": "1526 Mohaç sonrası vasal. Altın, gümüş, tuz madenleri stratejik önemde."
    },
    "Ragusa Cumhuriyeti": {
        "ruler_title": "Rektör",
        "tribute_min_gold": 12500,
        "tribute_max_gold": 12500,
        "military_obligation": False,
        "obligation_details": "Askeri yükümlülük yok",
        "emtia_obligations": [],
        "strategic_role": "Adriyatik istihbarat kaynağı",
        "special_ability": "spy_master",
        "privileges": ["Gümrüksüz ticaret (%2 muafiyet)", "İç işlerinde özerklik"],
        "political_risk": "low",  # Sadık Ticari Ortak
        "historical_note": "Sabit 12.500 Duka (750.000 Akçe). Venedik ve Avrupa saraylarından istihbarat toplar."
    }
}

PLAYABLE_TERRITORIES = [
    name for name, t in TERRITORIES.items()
    if t.territory_type in [TerritoryType.OSMANLI_EYALET, TerritoryType.OSMANLI_SANCAK, TerritoryType.VASAL]
]

# Tüm bölge isimleri
ALL_TERRITORY_NAMES = list(TERRITORIES.keys())


def get_territory(name: str) -> Optional[Territory]:
    """Bölge bilgisi al"""
    return TERRITORIES.get(name)


def get_neighbors_with_direction(territory: Territory) -> Dict[str, List[str]]:
    """Yönlere göre komşuları al"""
    return {
        "kuzey": territory.neighbors_north,
        "güney": territory.neighbors_south,
        "doğu": territory.neighbors_east,
        "batı": territory.neighbors_west
    }


def get_all_neighbors(territory: Territory) -> List[str]:
    """Tüm komşuları al"""
    all_neighbors = []
    all_neighbors.extend(territory.neighbors_north)
    all_neighbors.extend(territory.neighbors_south)
    all_neighbors.extend(territory.neighbors_east)
    all_neighbors.extend(territory.neighbors_west)
    return all_neighbors


def get_territories_by_type(territory_type: TerritoryType) -> List[Territory]:
    """Türe göre bölgeleri al"""
    return [t for t in TERRITORIES.values() if t.territory_type == territory_type]


def get_territories_by_region(region: Region) -> List[Territory]:
    """Bölgeye göre toprakları al"""
    return [t for t in TERRITORIES.values() if t.region == region]
