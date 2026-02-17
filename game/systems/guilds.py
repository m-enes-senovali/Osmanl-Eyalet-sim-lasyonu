# -*- coding: utf-8 -*-
"""
Osmanlı Eyalet Yönetim Simülasyonu - Lonca (Esnaf Loncası) Sistemi
16. yüzyıl Osmanlı ekonomisinin temel yapı taşı

Tarihsel Bağlam:
Osmanlı ekonomisi İaşe (Provisionism), Gelenekçilik ve Fiskalizm ilkelerine dayanır.
Lonca teşkilatı = üretim birimi + sosyal kontrol + vergi toplama + kalite güvencesi
Denetleyici: Kadı ve Muhtesip (İhtisab Ağası)

Hiyerarşi: Şeyh → Kethüda → Yiğitbaşı → Ehli Hibre → Usta → Kalfa → Çırak
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional
import random


# ═══════════════════════════════════════════
# LONCA HİYERARŞİSİ
# ═══════════════════════════════════════════

class GuildRank(Enum):
    """Lonca yönetim hiyerarşisi"""
    SEYH = "seyh"               # Manevi Lider / Pir — Ahilik geleneği
    KETHUDA = "kethuda"         # İdari Başkan — Devlet temsilcisi
    YIGITBASI = "yigitbasi"     # Disiplin Amiri — Saha sorumlusu
    EHLI_HIBRE = "ehli_hibre"   # Bilirkişi — Kalite kontrol


class GuildMemberRank(Enum):
    """Üretici hiyerarşisi (tüm loncalarda ortak)"""
    USTA = "usta"       # Master — bağımsız dükkan açabilir
    KALFA = "kalfa"     # Journeyman — ustanın yanında çalışır
    CIRAK = "cirak"     # Apprentice — eğitim görür


class GuildType(Enum):
    """Lonca türleri — zanaat kolları"""
    DEBBAG = "debbag"           # Debbağlar — Deri işleme
    SARAC = "sarac"             # Saraçlar — Eyer, koşum
    KASSAB = "kassab"           # Kasaplar — Et temini
    NANPAZ = "nanpaz"           # Ekmekçiler — Ekmek üretimi
    DULGER = "dulger"           # Dülgerler — İnşaat, gemi, araba
    KUYUMCU = "kuyumcu"         # Kuyumcular — Değerli maden işleme
    DEMIRCI = "demirci"         # Demirciler — Silah, alet, nal
    SIMKES = "simkes"           # Simkeşler — Gümüş tel, sırma


# ═══════════════════════════════════════════
# LONCA YÖNETİCİ VERİLERİ
# ═══════════════════════════════════════════

GUILD_HIERARCHY = {
    GuildRank.SEYH: {
        "role": "Manevi Lider / Pir",
        "function": "Dini törenleri (Şed kuşatma) yönetir, ahlaki disiplini ve Ahilik geleneklerini sağlar.",
        "authority_level": 1,
        "effect": "guild_stability",
        "stability_bonus": 10,
    },
    GuildRank.KETHUDA: {
        "role": "İdari Başkan / Devlet Temsilcisi",
        "function": "Hammadde dağıtımı (teavün), devletle iletişim, vergi toplama organizasyonu.",
        "authority_level": 2,
        "effect": "production_efficiency",
        "efficiency_bonus": 15,
    },
    GuildRank.YIGITBASI: {
        "role": "Disiplin Amiri / Saha Sorumlusu",
        "function": "Ceza uygulama, narh denetimi, çarşı güvenliği, hammadde alımı.",
        "authority_level": 3,
        "effect": "corruption_reduction",
        "corruption_reduction": 10,
    },
    GuildRank.EHLI_HIBRE: {
        "role": "Bilirkişi / Kalite Kontrol",
        "function": "Ürün kalitesini test eder, narh fiyatlarını belirlemede Kadı'ya danışmanlık yapar, "
                    "ustalık sınavlarını (icazet) yapar.",
        "authority_level": 4,
        "effect": "quality_assurance",
        "quality_bonus": 20,
    },
}


# ═══════════════════════════════════════════
# LONCA VERİ YAPISI
# ═══════════════════════════════════════════

@dataclass
class GuildMember:
    """Lonca üyesi"""
    name: str
    rank: GuildMemberRank
    skill: int = 50           # Beceri 0-100
    experience_years: int = 0  # Deneyim yılı
    
    @property
    def daily_output(self) -> float:
        """Günlük üretim miktarı (beceri bazlı)"""
        base = {
            GuildMemberRank.USTA: 1.0,
            GuildMemberRank.KALFA: 0.6,
            GuildMemberRank.CIRAK: 0.2,
        }
        return base.get(self.rank, 0.5) * (self.skill / 100)
    
    def can_promote(self) -> bool:
        """Terfi edebilir mi?"""
        if self.rank == GuildMemberRank.CIRAK:
            return self.experience_years >= 3 and self.skill >= 40
        elif self.rank == GuildMemberRank.KALFA:
            return self.experience_years >= 5 and self.skill >= 70
        return False


@dataclass
class Guild:
    """Bir lonca birimi"""
    guild_type: GuildType
    name_tr: str
    city: str = ""
    
    # Yönetim
    seyh_name: str = ""
    kethuda_name: str = ""
    
    # Üyeler
    usta_count: int = 5
    kalfa_count: int = 10
    cirak_count: int = 15
    
    # Ekonomik durum
    production_level: int = 50    # Üretim seviyesi 0-100
    quality_level: int = 50       # Kalite seviyesi 0-100
    narh_compliance: int = 100    # Narh uyumu 0-100 (100 = tam uyum)
    
    # Moral ve istikrar
    guild_morale: int = 70        # Lonca morali 0-100
    stability: int = 80           # İstikrar 0-100
    
    @property 
    def total_members(self) -> int:
        return self.usta_count + self.kalfa_count + self.cirak_count
    
    @property
    def daily_production(self) -> float:
        """Günlük toplam üretim"""
        return (self.usta_count * 1.0 + 
                self.kalfa_count * 0.6 + 
                self.cirak_count * 0.2) * (self.production_level / 100)
    
    @property
    def tax_contribution(self) -> float:
        """Vergi katkısı (akçe/çeyrek)"""
        return self.daily_production * 90 * 0.1  # %10 vergi, 90 gün/çeyrek


# ═══════════════════════════════════════════
# LONCA SİSTEMİ
# ═══════════════════════════════════════════

class GuildSystem:
    """
    Lonca yönetim sistemi
    
    Mekanikler:
    - Üretim: Usta/Kalfa/Çırak bazlı üretim kapasitesi
    - Narh: Fiyat denetimi — ihlal = ceza + kalite düşüşü
    - Muhtesip: Kadı'nın narh denetimi görevi
    - Terfi: Çırak→Kalfa→Usta (icazet sistemi)
    """
    
    def __init__(self):
        self.guilds: Dict[str, Guild] = {}
        self.muhtesip_active = True  # Muhtesip (narh denetçisi) aktif mi
        self.narh_strictness = 50    # Narh katılığı 0-100
    
    def create_guild(self, guild_type: GuildType, city: str) -> Guild:
        """Yeni lonca oluştur"""
        from game.systems.economy import CRAFT_SECTORS
        
        sector_key = guild_type.value
        sector = CRAFT_SECTORS.get(sector_key, {})
        name_tr = sector.get("name_tr", guild_type.value.title())
        
        guild = Guild(
            guild_type=guild_type,
            name_tr=name_tr,
            city=city,
            seyh_name=self._generate_guild_leader_name("Şeyh"),
            kethuda_name=self._generate_guild_leader_name("Kethüda"),
        )
        
        key = f"{city}_{guild_type.value}"
        self.guilds[key] = guild
        return guild
    
    def inspect_narh(self, guild_key: str) -> Dict:
        """
        Muhtesip narh denetimi — Kadı'nın yetkisiyle
        Narh ihlali tespit edilirse ceza uygulanır
        """
        guild = self.guilds.get(guild_key)
        if not guild:
            return {"result": "guild_not_found"}
        
        # Narh uyum kontrolü
        compliance = guild.narh_compliance
        violation = random.randint(0, 100) > compliance
        
        result = {
            "guild": guild.name_tr,
            "compliance": compliance,
            "violation_found": violation,
        }
        
        if violation:
            # Ceza: üretim düşer, moral düşer
            severity = random.choice(["minor", "major", "critical"])
            penalties = {
                "minor": {"morale": -5, "gold_fine": 100},
                "major": {"morale": -15, "gold_fine": 500, "production": -10},
                "critical": {"morale": -25, "gold_fine": 1000, "production": -20, "stability": -10},
            }
            result["severity"] = severity
            result["penalties"] = penalties[severity]
            
            # Cezayı uygula
            guild.guild_morale = max(0, guild.guild_morale + penalties[severity].get("morale", 0))
            guild.production_level = max(0, guild.production_level + penalties[severity].get("production", 0))
        else:
            result["reward"] = {"morale": 5, "quality": 5}
            guild.guild_morale = min(100, guild.guild_morale + 5)
            guild.quality_level = min(100, guild.quality_level + 5)
        
        return result
    
    def process_quarterly(self) -> Dict:
        """
        Çeyreklik lonca işlemleri
        - Üretim hesaplaması
        - Vergi toplama
        - Terfi kontrolleri
        - Moral güncellemesi
        """
        total_tax = 0
        total_production = 0
        events = []
        
        for key, guild in self.guilds.items():
            # Üretim
            production = guild.daily_production * 90
            total_production += production
            
            # Vergi
            tax = guild.tax_contribution
            total_tax += tax
            
            # Rastgele olay kontrolü
            if random.random() < 0.15:
                event = self._random_guild_event(guild)
                events.append(event)
            
            # Doğal moral değişimi
            if guild.guild_morale < 30:
                events.append({
                    "type": "guild_unrest",
                    "guild": guild.name_tr,
                    "message": f"{guild.name_tr} loncasında huzursuzluk artıyor!"
                })
        
        return {
            "total_tax": round(total_tax, 2),
            "total_production": round(total_production, 2),
            "guild_count": len(self.guilds),
            "events": events
        }
    
    def get_military_support(self) -> Dict:
        """
        Askeri sektörlerin lojistik desteği
        Debbağ, Saraç, Demirci → ordu donatımı
        Dülger → gemi/köprü inşaatı
        """
        from game.systems.economy import CRAFT_SECTORS
        
        support = {
            "leather": 0,      # Deri teçhizat
            "saddles": 0,      # Eyer/koşum
            "weapons": 0,      # Silah/nal
            "construction": 0, # İnşaat desteği
        }
        
        for key, guild in self.guilds.items():
            sector = CRAFT_SECTORS.get(guild.guild_type.value, {})
            if sector.get("sector_type") == "military":
                effect = sector.get("effect", "")
                output = guild.daily_production
                if effect == "military_supply":
                    support["leather"] += output
                elif effect == "cavalry_speed":
                    support["saddles"] += output
                elif effect == "weapon_production":
                    support["weapons"] += output
            elif sector.get("sector_type") == "construction":
                support["construction"] += guild.daily_production
        
        return support
    
    def _random_guild_event(self, guild: Guild) -> Dict:
        """Rastgele lonca olayı"""
        events = [
            {"type": "master_retirement", "effect": {"usta_count": -1}, 
             "message": f"{guild.name_tr}: bir usta emekli oldu."},
            {"type": "apprentice_joins", "effect": {"cirak_count": 2},
             "message": f"{guild.name_tr}: 2 yeni çırak katıldı."},
            {"type": "quality_improvement", "effect": {"quality": 5},
             "message": f"{guild.name_tr}: üretim kalitesi arttı."},
            {"type": "raw_material_shortage", "effect": {"production": -10},
             "message": f"{guild.name_tr}: hammadde sıkıntısı!"},
        ]
        event = random.choice(events)
        
        # Etkileri uygula
        effect = event.get("effect", {})
        if "usta_count" in effect:
            guild.usta_count = max(1, guild.usta_count + effect["usta_count"])
        if "cirak_count" in effect:
            guild.cirak_count += effect["cirak_count"]
        if "quality" in effect:
            guild.quality_level = min(100, guild.quality_level + effect["quality"])
        if "production" in effect:
            guild.production_level = max(0, guild.production_level + effect["production"])
        
        return event
    
    def _generate_guild_leader_name(self, title: str) -> str:
        """Lonca lideri ismi üret"""
        names = [
            "Mehmed", "Ahmed", "Mustafa", "Ali", "Hasan",
            "Hüseyin", "İbrahim", "Süleyman", "Yusuf", "Halil",
            "Kasım", "Mahmud", "Abdülkerim", "Haydar", "Cafer"
        ]
        surnames = ["Efendi", "Ağa", "Çelebi"]
        return f"{title} {random.choice(names)} {random.choice(surnames)}"
    
    def to_dict(self) -> Dict:
        """Kaydetmek için dict'e çevir"""
        return {
            "muhtesip_active": self.muhtesip_active,
            "narh_strictness": self.narh_strictness,
            "guilds": {
                key: {
                    "type": g.guild_type.value,
                    "city": g.city,
                    "usta": g.usta_count,
                    "kalfa": g.kalfa_count,
                    "cirak": g.cirak_count,
                    "production": g.production_level,
                    "quality": g.quality_level,
                    "morale": g.guild_morale,
                }
                for key, g in self.guilds.items()
            }
        }
