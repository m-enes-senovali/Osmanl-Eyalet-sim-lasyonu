# -*- coding: utf-8 -*-
"""
Osmanlı Eyalet Yönetim Simülasyonu - Askeri Sistem
1520 Dönemi Tarihi Gerçekliğine Uygun
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from enum import Enum
from audio.audio_manager import get_audio_manager


class MilitaryClass(Enum):
    """Askeri sınıf (1520 Osmanlı ordu yapısı)"""
    KAPIKULU = "kapikulu"    # Merkezi ordu - Padişaha bağlı
    EYALET = "eyalet"        # Eyalet kuvvetleri - Tımarlı sistem
    NAVAL = "naval"          # Donanma kuvvetleri


class UnitType(Enum):
    """Asker tipleri (1520 dönemi)"""
    # Kapıkulu Ordusu (Merkezi)
    YENICHERI = "yenicheri"         # Yeniçeri - Ağır piyade, tüfekli
    KAPIKULU_SIPAHI = "kapikulu_sipahi"  # Kapıkulu Süvarisi - Saray muhafızı
    TOPCU = "topcu"                 # Topçu Ocağı - Ağır silah
    CEBECI = "cebeci"               # Cebeci Ocağı - Silah üretimi/bakımı
    
    # Eyalet Kuvvetleri (Tımarlı)
    TIMARLI_SIPAHI = "timarli_sipahi"  # Tımarlı Sipahi - Tımar karşılığı
    AKINCI = "akinci"               # Akıncı - Hafif süvari, keşif
    AZAP = "azap"                   # Azap - Gönüllü hafif piyade
    
    # Donanma
    KADIRGA = "kadirga"             # Kadırga - Ana savaş gemisi
    BASTARDA = "bastarda"           # Baştarda - Kapudan Paşa gemisi (amiral)
    MAVNA = "mavna"                 # Mavna - Ağır top taşıma gemisi
    LEVENT = "levent"               # Levent - Deniz piyadeleri


@dataclass
class UnitStats:
    """Birim istatistikleri (1520 tarihi gerçekliği)"""
    name: str
    name_tr: str
    military_class: MilitaryClass
    attack: int
    defense: int
    speed: int
    cost_gold: int
    cost_food: int
    maintenance: int      # Tur başına bakım
    train_time: int       # Eğitim süresi (tur)
    requires_timar: bool = False      # Tımar gerektirir mi?
    requires_port: bool = False       # Liman gerektirir mi?
    requires_devshirme: bool = False  # Devşirme sistemi gerektirir mi? (Gayrimüslim nüfus)
    special_ability: str = ""         # Özel yetenek
    historical_note: str = ""         # Tarihi not
    

# 1520 Dönemi Birim Tanımları
# Maliyet referansı: Günlük ulufeler ve Narh defterleri
# Yeniçeri ulufesi: 5-8 akçe/gün = 450-720/çeyrek
# Azap yevmiyesi: 3 akçe/gün = 270/çeyrek
UNIT_DEFINITIONS = {
    # === KAPIKULU ORDUSU (Merkezi) ===
    UnitType.YENICHERI: UnitStats(
        name="Janissary",
        name_tr="Yeniçeri",
        military_class=MilitaryClass.KAPIKULU,
        attack=20,
        defense=15,
        speed=4,
        cost_gold=250,         # Eğitim maliyeti yüksek (Devşirme + Acemi Ocağı)
        cost_food=80,
        maintenance=8,         # Ulufe: 5-8 akçe/gün
        train_time=4,          # Uzun eğitim süreci
        requires_devshirme=True,
        special_ability="tufek",
        historical_note="Devşirme ile toplanan, Acemi Ocağı'nda yetişen elit tüfekli piyade. Cülus bahşişi ve sefer bahşişi talep eder."
    ),
    UnitType.KAPIKULU_SIPAHI: UnitStats(
        name="Kapikulu Cavalry",
        name_tr="Kapıkulu Süvarisi",
        military_class=MilitaryClass.KAPIKULU,
        attack=18,
        defense=12,
        speed=7,
        cost_gold=300,         # En pahalı kara birimi
        cost_food=90,
        maintenance=10,        # Yüksek ulufeli saray süvarisi
        train_time=4,
        requires_devshirme=True,
        special_ability="zirh",
        historical_note="Sipahi, Silahtar, Ulufeciler, Gurebalar — Padişah'ın özel muhafız süvarileri (6 bölük)"
    ),
    UnitType.TOPCU: UnitStats(
        name="Artillery",
        name_tr="Topçu",
        military_class=MilitaryClass.KAPIKULU,
        attack=35,
        defense=5,
        speed=1,
        cost_gold=500,         # Top dökümü çok pahalı (Tophane-i Amire)
        cost_food=80,
        maintenance=15,        # Barut + bakım
        train_time=5,
        special_ability="kusatma",
        historical_note="Kuşatma savaşının uzmanları — İstanbul'u fetheden toplar bu ocağın eseri. Şahi topları 17 ton ağırlığında."
    ),
    UnitType.CEBECI: UnitStats(
        name="Armorer Corps",
        name_tr="Cebeci",
        military_class=MilitaryClass.KAPIKULU,
        attack=8,
        defense=8,
        speed=3,
        cost_gold=120,         # Silah zanaatkarı
        cost_food=40,
        maintenance=5,
        train_time=2,
        special_ability="bakim",
        historical_note="Silah ve cephane üretimi/bakımı yapan ocak. Ordunun lojistik bel kemiği."
    ),
    
    # === EYALET KUVVETLERİ (Tımarlı) ===
    UnitType.TIMARLI_SIPAHI: UnitStats(
        name="Timar Cavalry",
        name_tr="Tımarlı Sipahi",
        military_class=MilitaryClass.EYALET,
        attack=14,
        defense=10,
        speed=7,
        cost_gold=0,           # Tımar topraktan geçinir — hazineye maliyeti YOK
        cost_food=30,          # Sadece sefer sırasında iaşe
        maintenance=0,         # Tımarından geçinir
        train_time=1,
        requires_timar=True,
        special_ability="timar",
        historical_note="Tımar sahibi — barışta çiftçi, savaşta süvari. Her 3000 akçelik tımar için 1 cebelü (atlı asker) besler."
    ),
    UnitType.AKINCI: UnitStats(
        name="Akinci Raider",
        name_tr="Akıncı",
        military_class=MilitaryClass.EYALET,
        attack=10,
        defense=4,
        speed=10,
        cost_gold=80,
        cost_food=30,
        maintenance=3,
        train_time=1,
        special_ability="akin",
        historical_note="Sınır boylarının hafif süvarileri — keşif, yağma ve düşman moralini bozma. Mihaloğlu, Turahanlı aileleri ünlü akıncı beyleri."
    ),
    UnitType.AZAP: UnitStats(
        name="Azap Infantry",
        name_tr="Azap",
        military_class=MilitaryClass.EYALET,
        attack=8,
        defense=6,
        speed=5,
        cost_gold=25,          # Çok ucuz — gönüllü halk piyadesi (rapordan: 200 akçe)
        cost_food=20,
        maintenance=1,         # Yevmiye: 3 akçe/gün
        train_time=1,
        special_ability="gonullu",
        historical_note="Anadolu'dan gönüllü toplanan bekar (azeb=bekar) hafif piyadeler. Garnizon ve kuşatma hizmetinde."
    ),
    
    # === DONANMA ===
    UnitType.KADIRGA: UnitStats(
        name="War Galley",
        name_tr="Kadırga",
        military_class=MilitaryClass.NAVAL,
        attack=25,
        defense=15,
        speed=5,
        cost_gold=800,         # Tarihsel: ~230.000 akçe, oyun ölçeğinde yüksek
        cost_food=150,
        maintenance=20,        # 150-200 kürekçi mürettebat
        train_time=6,
        requires_port=True,
        special_ability="deniz",
        historical_note="Akdeniz'in ana savaş gemisi — 150-200 kürekçi, 50-80 savaşçı. Kışın limana çekilmeli (mevsimsel kısıtlama)."
    ),
    UnitType.LEVENT: UnitStats(
        name="Marine",
        name_tr="Levent",
        military_class=MilitaryClass.NAVAL,
        attack=12,
        defense=8,
        speed=5,
        cost_gold=100,
        cost_food=50,
        maintenance=4,
        train_time=2,
        requires_port=True,
        special_ability="amfibi",
        historical_note="Denizci piyadeler — gemilerde ve kıyı baskınlarında görev yapar. Barbaros Hayreddin'in korsanları levent kökenlidir."
    ),
    UnitType.BASTARDA: UnitStats(
        name="Flagship Galley",
        name_tr="Baştarda",
        military_class=MilitaryClass.NAVAL,
        attack=30,
        defense=20,
        speed=4,
        cost_gold=1200,        # Kapudan Paşa gemisi — en pahalı gemi
        cost_food=200,
        maintenance=30,        # Büyük mürettebat
        train_time=8,
        requires_port=True,
        special_ability="komutan",  # Donanma morali bonusu
        historical_note="Kapudan Paşa'nın amiral gemisi — 26-36 oturak, kadırgadan büyük ve gösterişli. Donanma savaşında moral etkisi."
    ),
    UnitType.MAVNA: UnitStats(
        name="Heavy Transport",
        name_tr="Mavna",
        military_class=MilitaryClass.NAVAL,
        attack=20,
        defense=18,
        speed=3,
        cost_gold=600,         # Ağır lojistik gemisi
        cost_food=120,
        maintenance=15,
        train_time=5,
        requires_port=True,
        special_ability="top_taşıma",  # Denizde top ateşi desteği
        historical_note="İki direkli, geniş gövdeli top taşıma gemisi. Yüksek ateş gücü ve lojistik kapasitesi."
    ),
}


# Eski uyumluluk için alias
UnitType.SIPAHI = UnitType.TIMARLI_SIPAHI  # Geriye uyumluluk


@dataclass
class TrainingQueue:
    """Eğitim kuyruğu öğesi"""
    unit_type: UnitType
    count: int
    turns_remaining: int


class MilitarySystem:
    """Askeri yönetim sistemi (1520 dönemi)"""
    
    def __init__(self):
        # Mevcut birlikler - 1520 başlangıç değerleri
        self.units: Dict[UnitType, int] = {
            # Kapıkulu Ordusu
            UnitType.YENICHERI: 30,
            UnitType.KAPIKULU_SIPAHI: 20,
            UnitType.TOPCU: 5,
            UnitType.CEBECI: 10,
            # Eyalet Kuvvetleri
            UnitType.TIMARLI_SIPAHI: 50,
            UnitType.AKINCI: 25,
            UnitType.AZAP: 80,
            # Donanma
            UnitType.KADIRGA: 0,
            UnitType.BASTARDA: 0,
            UnitType.MAVNA: 0,
            UnitType.LEVENT: 0,
        }
        
        # Eğitim kuyruğu
        self.training_queue: List[TrainingQueue] = []
        
        # Savaş durumu
        self.at_war = False
        self.war_target = None
        self.morale = 100  # Moral 0-100
        self.experience = 0  # Deneyim 0-100
        
        # Kayıplar (istatistik için)
        self.total_losses = 0
        self.total_victories = 0
        
        # YENİ: Tımar sistemi entegrasyonu
        self.timar_capacity = 100  # Maksimum tımarlı sipahi sayısı
        self.available_timars = 50  # Mevcut boş tımar sayısı
        
        # YENİ: Donanma durumu (construction.py'den güncellenir)
        self.has_port = False
        self.port_level = 0
        
        # YENİ: Komutanlar
        self.commanders: List[Dict] = []
    
    def get_total_soldiers(self) -> int:
        """Toplam asker sayısı (donanma hariç)"""
        naval_units = [UnitType.KADIRGA, UnitType.BASTARDA, UnitType.MAVNA, UnitType.LEVENT]
        return sum(c for t, c in self.units.items() if t not in naval_units)
    
    def get_total_power(self, combat_type: str = "field") -> int:
        """
        Toplam askeri güç
        combat_type: "field" (meydan), "siege" (kuşatma), "defense" (savunma)
        """
        power = 0
        for unit_type, count in self.units.items():
            if unit_type not in UNIT_DEFINITIONS:
                continue
            stats = UNIT_DEFINITIONS[unit_type]
            base_power = count * (stats.attack + stats.defense)
            
            # Özel yetenek bonusları
            if combat_type == "siege" and stats.special_ability == "kusatma":
                base_power *= 2.0  # Topçu kuşatmada 2x güçlü
            elif combat_type == "defense" and stats.special_ability == "tufek":
                base_power *= 1.5  # Yeniçeri savunmada 1.5x güçlü
            elif combat_type == "field" and stats.special_ability == "zirh":
                base_power *= 1.3  # Kapıkulu süvarisi meydan savaşında güçlü
            
            power += int(base_power)
        return power
    
    def get_maintenance_cost(self) -> int:
        """Toplam bakım maliyeti (Cebeci indirimi dahil)"""
        cost = 0
        for unit_type, count in self.units.items():
            if unit_type not in UNIT_DEFINITIONS:
                continue
            stats = UNIT_DEFINITIONS[unit_type]
            cost += count * stats.maintenance
        
        # Cebeci indirimi: Her 10 cebeci için %10 indirim (max %30)
        cebeci_count = self.units.get(UnitType.CEBECI, 0)
        discount = min(0.30, cebeci_count * 0.01)  # Max %30 indirim
        cost = int(cost * (1 - discount))
        
        return cost
    
    @property
    def infantry(self) -> int:
        """Toplam piyade sayısı (Yeniçeri + Azap)"""
        return self.units.get(UnitType.YENICHERI, 0) + self.units.get(UnitType.AZAP, 0)
    
    @property
    def cavalry(self) -> int:
        """Toplam süvari sayısı"""
        return (self.units.get(UnitType.TIMARLI_SIPAHI, 0) + 
                self.units.get(UnitType.KAPIKULU_SIPAHI, 0) +
                self.units.get(UnitType.AKINCI, 0))
    
    @property
    def artillery_crew(self) -> int:
        """Toplam topçu mürettebatı sayısı"""
        return self.units.get(UnitType.TOPCU, 0)
    
    @property
    def raiders(self) -> int:
        """Toplam akıncı sayısı"""
        return self.units.get(UnitType.AKINCI, 0)
    
    @property
    def naval_strength(self) -> int:
        """Donanma gücü"""
        return (self.units.get(UnitType.KADIRGA, 0) * 40 +
                self.units.get(UnitType.BASTARDA, 0) * 60 +
                self.units.get(UnitType.MAVNA, 0) * 35 +
                self.units.get(UnitType.LEVENT, 0) * 20)
    
    def can_recruit(self, unit_type: UnitType, count: int, economy) -> tuple:
        """
        Asker alabilir mi kontrol et
        Returns: (can_recruit: bool, reason: str)
        """
        if unit_type not in UNIT_DEFINITIONS:
            return False, "Bilinmeyen birim tipi"
        
        stats = UNIT_DEFINITIONS[unit_type]
        total_gold = stats.cost_gold * count
        total_food = stats.cost_food * count
        
        # Kaynak kontrolü
        if not economy.can_afford(gold=total_gold, food=total_food):
            return False, "Yetersiz kaynak"
        
        # Tımar kontrolü
        if stats.requires_timar:
            current_timarli = self.units.get(UnitType.TIMARLI_SIPAHI, 0)
            if current_timarli + count > self.timar_capacity:
                return False, f"Yetersiz tımar. Mevcut kapasite: {self.timar_capacity}"
            if count > self.available_timars:
                return False, f"Sadece {self.available_timars} boş tımar var"
        
        # Liman kontrolü
        if stats.requires_port:
            if not self.has_port:
                return False, "Tersane gerekli. Önce tersane inşa edin"
        
        return True, ""
    
    def recruit(self, unit_type: UnitType, count: int, economy) -> bool:
        """Asker topla ve eğitime al"""
        can, reason = self.can_recruit(unit_type, count, economy)
        if not can:
            audio = get_audio_manager()
            audio.announce_action_result("Asker toplama", False, reason)
            return False
        
        stats = UNIT_DEFINITIONS[unit_type]
        total_gold = stats.cost_gold * count
        total_food = stats.cost_food * count
        
        # Kaynakları harca
        economy.spend(gold=total_gold, food=total_food)
        
        # Tımarlı sipahi için tımar kullan
        if stats.requires_timar:
            self.available_timars -= count
        
        # Eğitim kuyruğuna ekle
        self.training_queue.append(TrainingQueue(
            unit_type=unit_type,
            count=count,
            turns_remaining=stats.train_time
        ))
        
        audio = get_audio_manager()
        audio.announce_action_result(
            f"{stats.name_tr} toplama",
            True,
            f"{count} {stats.name_tr} eğitime alındı. {stats.train_time} tur sonra hazır."
        )
        
        return True
    
    def process_turn(self) -> List[str]:
        """Tur sonunda eğitimleri işle"""
        completed = []
        messages = []
        
        for item in self.training_queue:
            item.turns_remaining -= 1
            if item.turns_remaining <= 0:
                self.units[item.unit_type] += item.count
                completed.append(item)
        
        # Tamamlananları kaldır
        for item in completed:
            self.training_queue.remove(item)
            stats = UNIT_DEFINITIONS[item.unit_type]
            msg = f"{item.count} {stats.name_tr} eğitimini tamamladı!"
            messages.append(msg)
        
        # Moral düzeltme
        if self.morale < 100:
            self.morale = min(100, self.morale + 5)
            
        return messages
    
    def fight_bandits(self) -> dict:
        """Eşkıya/isyan bastırma savaşı"""
        total_power = self.get_total_power()
        # Eşkıya gücü sabit + ordu boyutunun küçük bir kısmı
        bandit_power = 100 + (self.get_total_soldiers() // 25)
        
        # Basit savaş hesabı
        victory = total_power > bandit_power * 1.2
        
        result = {
            'victory': victory,
            'our_power': total_power,
            'enemy_power': bandit_power,
            'losses': {}
        }
        
        if victory:
            # Zafer: Sadece hafif birliklerde küçük kayıplar (%2)
            from game.systems.military import UnitType
            light_units = {UnitType.AZAP, UnitType.AKINCI}
            for unit_type in light_units:
                if self.units.get(unit_type, 0) > 0:
                    loss = max(1, self.units[unit_type] // 50)
                    self.units[unit_type] -= loss
                    result['losses'][unit_type.value] = loss
            self.total_victories += 1
            self.morale = min(100, self.morale + 10)
        else:
            # Yenilgi: Tüm birliklerde orta kayıplar (%10)
            for unit_type in self.units:
                if self.units[unit_type] > 0:
                    loss = max(1, self.units[unit_type] // 10)
                    self.units[unit_type] -= loss
                    result['losses'][unit_type.value] = loss
            self.total_losses += 1
            self.morale = max(0, self.morale - 15)
        
        return result
    
    def apply_casualties(self, total_losses: int):
        """
        Savaş kayıplarını birliklere orantılı dağıt
        Multiplayer savaşlarında kullanılır
        """
        if total_losses <= 0:
            return
        
        total_soldiers = self.get_total_soldiers()
        if total_soldiers <= 0:
            return
        
        # Kayıpları birliklere orantılı dağıt
        remaining_losses = total_losses
        for unit_type, count in self.units.items():
            if count <= 0:
                continue
            
            # Bu birlik tipinin kayıp oranı
            ratio = count / total_soldiers
            unit_loss = int(remaining_losses * ratio)
            
            # En az 1 kayıp, en fazla mevcut sayı kadar
            unit_loss = max(0, min(unit_loss, count))
            
            self.units[unit_type] -= unit_loss
            remaining_losses -= unit_loss
        
        # Kalan kayıpları rastgele dağıt
        while remaining_losses > 0:
            for unit_type in self.units:
                if self.units[unit_type] > 0 and remaining_losses > 0:
                    self.units[unit_type] -= 1
                    remaining_losses -= 1
                    break
            else:
                break  # Hiç asker kalmadı
        
        self.total_losses += 1
        self.morale = max(0, self.morale - 10)
    
    def get_army_info(self) -> List[tuple]:
        """Ordu bilgisi listesi [(birim_adı, sayı, güç), ...]"""
        info = []
        for unit_type, count in self.units.items():
            stats = UNIT_DEFINITIONS[unit_type]
            power = count * (stats.attack + stats.defense)
            info.append((stats.name_tr, count, power))
        return info
    
    def announce_army(self):
        """Ordu bilgisini ekran okuyucuya duyur"""
        audio = get_audio_manager()
        audio.speak("Ordu Durumu", interrupt=True)
        audio.announce_value("Toplam Asker", str(self.get_total_soldiers()))
        audio.announce_value("Toplam Güç", str(self.get_total_power()))
        audio.announce_value("Moral", f"%{self.morale}")
        
        for unit_type, count in self.units.items():
            if count > 0:
                stats = UNIT_DEFINITIONS[unit_type]
                audio.announce_value(stats.name_tr, str(count))
        
        if self.training_queue:
            audio.speak("Eğitimdekiler:")
            for item in self.training_queue:
                stats = UNIT_DEFINITIONS[item.unit_type]
                audio.speak(f"{item.count} {stats.name_tr}, {item.turns_remaining} tur kaldı")
    
    def to_dict(self) -> Dict:
        """Kayıt için dictionary'e dönüştür"""
        return {
            'units': {k.value: v for k, v in self.units.items()},
            'training_queue': [
                {'type': t.unit_type.value, 'count': t.count, 'turns': t.turns_remaining}
                for t in self.training_queue
            ],
            'morale': self.morale,
            'experience': self.experience,
            'at_war': self.at_war,
            'total_losses': self.total_losses,
            'total_victories': self.total_victories,
            # YENİ alanlar
            'timar_capacity': self.timar_capacity,
            'available_timars': self.available_timars,
            'has_port': self.has_port,
            'port_level': self.port_level,
            'commanders': self.commanders,
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'MilitarySystem':
        """Dictionary'den yükle"""
        system = cls()
        
        # Birimleri yükle (eski save uyumluluğu için try-except)
        try:
            system.units = {UnitType(k): v for k, v in data['units'].items()}
        except ValueError:
            # Eski save dosyasında olmayan birimler için varsayılan kullan
            for k, v in data['units'].items():
                try:
                    system.units[UnitType(k)] = v
                except ValueError:
                    pass  # Eski birim, atla
        
        system.training_queue = [
            TrainingQueue(UnitType(t['type']), t['count'], t['turns'])
            for t in data.get('training_queue', [])
            if t['type'] in [ut.value for ut in UnitType]
        ]
        system.morale = data.get('morale', 100)
        system.experience = data.get('experience', 0)
        system.at_war = data.get('at_war', False)
        system.total_losses = data.get('total_losses', 0)
        system.total_victories = data.get('total_victories', 0)
        
        # YENİ alanlar
        system.timar_capacity = data.get('timar_capacity', 100)
        system.available_timars = data.get('available_timars', 50)
        system.has_port = data.get('has_port', False)
        system.port_level = data.get('port_level', 0)
        system.commanders = data.get('commanders', [])
        
        return system

