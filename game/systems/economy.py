# -*- coding: utf-8 -*-
"""
Osmanlı Eyalet Yönetim Simülasyonu - Ekonomi Sistemi
"""

from dataclasses import dataclass, field
from typing import Dict
from audio.audio_manager import get_audio_manager


@dataclass
class Resources:
    """Eyalet kaynakları"""
    gold: int = 15000   # Daha fazla başlangıç altını (10000 -> 15000)
    food: int = 10000   # Daha fazla başlangıç zahire (8000 -> 10000)
    wood: int = 5000    # Daha fazla kereste (4000 -> 5000)
    iron: int = 3000    # Daha fazla demir (2000 -> 3000)
    stone: int = 1000   # Taş (top üretimi için)
    rope: int = 500     # Halat (gemi inşası için)
    tar: int = 300      # Katran (gemi inşası için)
    sailcloth: int = 200  # Yelken bezi (gemi inşası için)
    
    def to_dict(self) -> Dict:
        return {
            'gold': self.gold,
            'food': self.food,
            'wood': self.wood,
            'iron': self.iron,
            'stone': self.stone,
            'rope': self.rope,
            'tar': self.tar,
            'sailcloth': self.sailcloth
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Resources':
        # Eski kayıtlarla uyumluluk
        defaults = {'stone': 1000, 'rope': 500, 'tar': 300, 'sailcloth': 200}
        for key, default_val in defaults.items():
            if key not in data:
                data[key] = default_val
        return cls(**data)


@dataclass
class Income:
    """Gelir kalemleri"""
    tax: int = 0          # Vergi geliri
    trade: int = 0        # Ticaret geliri
    tribute: int = 0      # Haraç
    
    @property
    def total(self) -> int:
        return self.tax + self.trade + self.tribute


@dataclass
class Expense:
    """Gider kalemleri"""
    military: int = 0      # Askeri harcamalar
    buildings: int = 0     # Bina bakımı
    tribute_to_sultan: int = 0  # Padişaha gönderilen
    
    @property
    def total(self) -> int:
        return self.military + self.buildings + self.tribute_to_sultan


@dataclass
class MarketPrices:
    """
    Dinamik pazar fiyatları - Arz-talep mekaniği
    Osmanlı ticaretinin temel malları
    """
    # Temel fiyatlar (altın cinsinden)
    grain_price: float = 1.0      # Zahire (buğday, arpa)
    silk_price: float = 10.0      # İpek (İpek Yolu)
    spice_price: float = 15.0     # Baharat (Hint-Arap ticareti)
    cloth_price: float = 5.0      # Kumaş
    salt_price: float = 2.0       # Tuz
    copper_price: float = 3.0     # Bakır
    
    # Fiyat değişim sınırları
    MIN_PRICE_MULT: float = 0.5   # Minimum %50
    MAX_PRICE_MULT: float = 2.0   # Maximum %200
    
    def adjust_price(self, good: str, supply: int, demand: int):
        """Arz-talep dengesine göre fiyat ayarla"""
        if supply <= 0:
            supply = 1
        
        ratio = demand / supply
        # Talep > Arz: fiyat artar
        # Arz > Talep: fiyat düşer
        
        price_attr = f"{good}_price"
        if hasattr(self, price_attr):
            base_prices = {
                'grain': 1.0, 'silk': 10.0, 'spice': 15.0,
                'cloth': 5.0, 'salt': 2.0, 'copper': 3.0
            }
            base = base_prices.get(good, 1.0)
            new_price = base * ratio
            
            # Sınırları uygula
            new_price = max(base * self.MIN_PRICE_MULT, 
                          min(base * self.MAX_PRICE_MULT, new_price))
            setattr(self, price_attr, round(new_price, 2))
    
    def get_price(self, good: str) -> float:
        """Mal fiyatını getir"""
        price_attr = f"{good}_price"
        return getattr(self, price_attr, 1.0)
    
    def to_dict(self) -> Dict:
        return {
            'grain_price': self.grain_price,
            'silk_price': self.silk_price,
            'spice_price': self.spice_price,
            'cloth_price': self.cloth_price,
            'salt_price': self.salt_price,
            'copper_price': self.copper_price
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'MarketPrices':
        return cls(
            grain_price=data.get('grain_price', 1.0),
            silk_price=data.get('silk_price', 10.0),
            spice_price=data.get('spice_price', 15.0),
            cloth_price=data.get('cloth_price', 5.0),
            salt_price=data.get('salt_price', 2.0),
            copper_price=data.get('copper_price', 3.0)
        )


class EconomySystem:
    """Ekonomi yönetim sistemi"""
    
    # Ticaret yolları ve bonusları
    TRADE_ROUTES = {
        'silk_road': {'name': 'İpek Yolu', 'bonus': 0.25, 'goods': ['silk', 'spice']},
        'mediterranean': {'name': 'Akdeniz', 'bonus': 0.20, 'goods': ['cloth', 'copper']},
        'black_sea': {'name': 'Karadeniz', 'bonus': 0.15, 'goods': ['grain', 'salt']},
        'indian_ocean': {'name': 'Hint Okyanusu', 'bonus': 0.30, 'goods': ['spice']}
    }
    
    def __init__(self):
        self.resources = Resources()
        self.income = Income()
        self.expense = Expense()
        self.market = MarketPrices()
        
        self.tax_rate = 0.15  # %15 vergi oranı
        self.trade_level = 1  # Ticaret seviyesi
        
        # Enflasyon sistemi
        self.inflation_rate = 0.0  # %0 başlangıç
        self.total_gold_in_circulation = 15000  # Başlangıç altını
        
        # Aktif ticaret yolları
        self.active_trade_routes = ['black_sea']  # Varsayılan
        
        # Modifiers
        self.tax_modifier = 1.0
        self.trade_modifier = 1.0
        self.expense_modifier = 1.0
    
    def calculate_inflation(self):
        """
        Enflasyon hesapla
        Fazla altın = fiyat artışı (tarihsel: Osmanlı 16. yy gümüş akışı)
        """
        # Referans altın miktarı
        reference_gold = 15000
        
        if self.resources.gold > reference_gold:
            # Fazla altın = enflasyon
            excess_ratio = (self.resources.gold - reference_gold) / reference_gold
            self.inflation_rate = min(0.50, excess_ratio * 0.1)  # Max %50
        else:
            # Az altın = deflasyon
            deficit_ratio = (reference_gold - self.resources.gold) / reference_gold
            self.inflation_rate = max(-0.20, -deficit_ratio * 0.05)  # Min -%20
        
        return self.inflation_rate
    
    def get_trade_route_bonus(self) -> float:
        """Aktif ticaret yollarından gelen bonus"""
        total_bonus = 0.0
        for route_id in self.active_trade_routes:
            if route_id in self.TRADE_ROUTES:
                total_bonus += self.TRADE_ROUTES[route_id]['bonus']
        return total_bonus
    
    def activate_trade_route(self, route_id: str) -> bool:
        """Ticaret yolu aç"""
        if route_id in self.TRADE_ROUTES and route_id not in self.active_trade_routes:
            self.active_trade_routes.append(route_id)
            return True
        return False
    
    def calculate_tax_income(self, population: int) -> int:
        """Vergi gelirini hesapla"""
        # Nüfus başına daha yüksek gelir (0.25 çarpan - eskiden 0.15)
        base_income = int(population * self.tax_rate * 0.25)
        return int(base_income * self.tax_modifier)
    
    def calculate_trade_income(self) -> int:
        """Ticaret gelirini hesapla"""
        # Temel ticaret geliri artırıldı (1500 altın/seviye - eskiden 1200)
        base_trade = 1500 * self.trade_level
        return int(base_trade * self.trade_modifier)
    
    def set_tax_rate(self, rate: float) -> bool:
        """
        Vergi oranını ayarla (0.05 - 0.40)
        Düşük vergi = yüksek memnuniyet
        Yüksek vergi = düşük memnuniyet
        """
        if 0.05 <= rate <= 0.40:
            old_rate = self.tax_rate
            self.tax_rate = rate
            
            audio = get_audio_manager()
            audio.announce_action_result(
                "Vergi oranı değiştirildi",
                True,
                f"Yeni oran: %{int(rate * 100)}"
            )
            return True
        return False
    
    def get_tax_happiness_effect(self) -> int:
        """Vergi oranının memnuniyet etkisini hesapla"""
        # %15 normal, her %5 = -5 memnuniyet
        base_rate = 0.15
        diff = self.tax_rate - base_rate
        return int(diff * 100 * -1)  # Her %1 için -1 memnuniyet
    
    def process_turn(self, population: int, military_count: int, building_maintenance: int):
        """Tur sonunda ekonomiyi güncelle"""
        audio = get_audio_manager()
        
        # Gelirleri hesapla
        self.income.tax = self.calculate_tax_income(population)
        self.income.trade = self.calculate_trade_income()
        self.income.tribute = 0  # Haraç şimdilik yok
        
        # Giderleri hesapla
        self.expense.military = int(military_count * 1.0 * self.expense_modifier)  # Asker başına 1 altın
        self.expense.buildings = int(building_maintenance * self.expense_modifier)
        self.expense.tribute_to_sultan = int(self.income.total * 0.02)  # %2 padişaha
        
        # Net değişim
        net = self.income.total - self.expense.total
        self.resources.gold += net
        
        # Düşük altın uyarısı
        if self.resources.gold < 500 and self.resources.gold > 0:
            audio.speak("Uyarı: Hazine çok düşük! Vergiyi artırın veya giderleri azaltın.", interrupt=False)
        
        # Bankrota karşı koruma - borç limiti
        if self.resources.gold < -2000:
            # Acil durum: Padişahtan borç al
            self.resources.gold += 1000
            audio.speak("Acil durum! Padişahtan 1000 altın borç alındı.", interrupt=True)
        
        return net
    
    def can_afford(self, gold: int = 0, food: int = 0, wood: int = 0, iron: int = 0) -> bool:
        """Bir masrafı karşılayabilir mi?"""
        return (
            self.resources.gold >= gold and
            self.resources.food >= food and
            self.resources.wood >= wood and
            self.resources.iron >= iron
        )
    
    def spend(self, gold: int = 0, food: int = 0, wood: int = 0, iron: int = 0) -> bool:
        """Kaynak harca"""
        if not self.can_afford(gold, food, wood, iron):
            audio = get_audio_manager()
            audio.announce_action_result("Harcama", False, "Yetersiz kaynak")
            return False
        
        self.resources.gold -= gold
        self.resources.food -= food
        self.resources.wood -= wood
        self.resources.iron -= iron
        return True
    
    def add_resources(self, gold: int = 0, food: int = 0, wood: int = 0, iron: int = 0):
        """Kaynak ekle"""
        self.resources.gold += gold
        self.resources.food += food
        self.resources.wood += wood
        self.resources.iron += iron
    
    def get_summary(self) -> dict:
        """Ekonomi özeti"""
        return {
            'resources': self.resources.to_dict(),
            'income': {
                'tax': self.income.tax,
                'trade': self.income.trade,
                'tribute': self.income.tribute,
                'total': self.income.total
            },
            'expense': {
                'military': self.expense.military,
                'buildings': self.expense.buildings,
                'tribute_to_sultan': self.expense.tribute_to_sultan,
                'total': self.expense.total
            },
            'net': self.income.total - self.expense.total,
            'tax_rate': self.tax_rate
        }
    
    def announce_summary(self):
        """Ekonomi özetini ekran okuyucuya duyur"""
        audio = get_audio_manager()
        audio.speak("Ekonomi Özeti", interrupt=True)
        audio.announce_value("Altın", str(self.resources.gold))
        audio.announce_value("Zahire", str(self.resources.food))
        audio.announce_value("Vergi Oranı", f"%{int(self.tax_rate * 100)}")
        audio.announce_value("Toplam Gelir", str(self.income.total))
        audio.announce_value("Toplam Gider", str(self.expense.total))
        net = self.income.total - self.expense.total
        audio.announce_value("Net", f"{'+' if net >= 0 else ''}{net}")
    
    def to_dict(self) -> Dict:
        """Kayıt için dictionary'e dönüştür"""
        return {
            'resources': self.resources.to_dict(),
            'market': self.market.to_dict(),
            'tax_rate': self.tax_rate,
            'trade_level': self.trade_level,
            'inflation_rate': self.inflation_rate,
            'active_trade_routes': self.active_trade_routes,
            'tax_modifier': self.tax_modifier,
            'trade_modifier': self.trade_modifier,
            'expense_modifier': self.expense_modifier
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'EconomySystem':
        """Dictionary'den yükle"""
        system = cls()
        system.resources = Resources.from_dict(data['resources'])
        system.tax_rate = data['tax_rate']
        system.trade_level = data['trade_level']
        system.tax_modifier = data.get('tax_modifier', 1.0)
        system.trade_modifier = data.get('trade_modifier', 1.0)
        system.expense_modifier = data.get('expense_modifier', 1.0)
        
        # Yeni alanlar (eski kayıtlarla uyumluluk)
        if 'market' in data:
            system.market = MarketPrices.from_dict(data['market'])
        if 'inflation_rate' in data:
            system.inflation_rate = data['inflation_rate']
        if 'active_trade_routes' in data:
            system.active_trade_routes = data['active_trade_routes']
        
        return system
