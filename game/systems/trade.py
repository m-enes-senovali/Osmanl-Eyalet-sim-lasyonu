# -*- coding: utf-8 -*-
"""
Osmanlı Eyalet Yönetim Simülasyonu - Ticaret Sistemi
Ticaret yolları, kervanlar ve liman mekanikleri
"""

from dataclasses import dataclass
from typing import Dict, List, Optional
from enum import Enum
import random
from audio.audio_manager import get_audio_manager


class RouteType(Enum):
    """Ticaret yolu türleri"""
    LAND = "land"       # Kara yolu
    SEA = "sea"         # Deniz yolu
    SILK = "silk"       # İpek yolu (özel)


class CaravanStatus(Enum):
    """Kervan durumu"""
    PREPARING = "preparing"   # Hazırlanıyor
    TRAVELING = "traveling"   # Yolda
    TRADING = "trading"       # Ticaret yapıyor
    RETURNING = "returning"   # Dönüyor
    COMPLETED = "completed"   # Tamamlandı
    LOST = "lost"             # Kayboldu


class TradeGood(Enum):
    """Ticari mal türleri"""
    SILK = "ipek"          # Yüksek kar, uzun mesafe
    SPICE = "baharat"      # Orta kar, orta mesafe
    CLOTH = "kumaş"        # Düşük kar, kısa mesafe
    IRON = "demir"         # Savaş malzemesi
    WOOD = "kereste"       # İnşaat malzemesi
    SALT = "tuz"           # Günlük tüketim
    GRAIN = "tahıl"        # Temel gıda
    JEWELS = "mücevher"    # Lüks


# Temel mal fiyatları
BASE_PRICES = {
    TradeGood.SILK: 100,
    TradeGood.SPICE: 80,
    TradeGood.CLOTH: 30,
    TradeGood.IRON: 50,
    TradeGood.WOOD: 20,
    TradeGood.SALT: 25,
    TradeGood.GRAIN: 15,
    TradeGood.JEWELS: 150,
}


@dataclass
class MarketPrice:
    """Pazar fiyatı - dinamik değişen"""
    good: TradeGood
    base_price: int
    current_multiplier: float = 1.0  # 0.5 - 2.0 arası
    trend: float = 0.0  # -0.1 ile +0.1 arası (fiyat trendi)
    
    def get_current_price(self) -> int:
        """Güncel fiyatı hesapla"""
        return int(self.base_price * self.current_multiplier)
    
    def update_price(self, supply_change: float = 0.0, demand_change: float = 0.0):
        """Fiyatı güncelle (arz/talep değişimine göre)"""
        # Arz artarsa fiyat düşer, talep artarsa fiyat artar
        change = demand_change - supply_change + self.trend
        self.current_multiplier += change
        
        # Sınırlar içinde tut
        self.current_multiplier = max(0.5, min(2.0, self.current_multiplier))
        
        # Trend zamanla sıfıra yaklaşır
        self.trend *= 0.9


@dataclass
class TradeRoute:
    """Ticaret yolu"""
    route_id: str
    name: str
    route_type: RouteType
    start_region: str
    end_region: str
    base_income: int
    travel_time: int  # Tek yön tur sayısı
    risk_factor: float  # 0.0-1.0 (yüksek = tehlikeli)
    active: bool = True
    
    def get_total_time(self) -> int:
        """Toplam seyahat süresi (gidiş-dönüş)"""
        return self.travel_time * 2 + 1  # +1 ticaret için


@dataclass
class Caravan:
    """Ticaret kervanı"""
    caravan_id: str
    route: TradeRoute
    status: CaravanStatus
    turns_remaining: int
    goods_value: int  # Taşınan mal değeri
    protection: int = 0  # Koruma askeri sayısı
    
    def get_success_chance(self) -> float:
        """Başarı şansı"""
        base_chance = 1.0 - self.route.risk_factor
        protection_bonus = min(0.3, self.protection * 0.01)
        return min(0.95, base_chance + protection_bonus)


# Varsayılan ticaret yolları (1520 dönemi)
DEFAULT_ROUTES = [
    TradeRoute(
        route_id="silk_road",
        name="İpek Yolu",
        route_type=RouteType.SILK,
        start_region="Bursa",  # Osmanlı ipek merkezi
        end_region="Semerkand",  # Özbek Hanlığı - İpek Yolu kavşağı
        base_income=800,
        travel_time=4,
        risk_factor=0.25
    ),
    TradeRoute(
        route_id="spice_route",
        name="Baharat Yolu",
        route_type=RouteType.SEA,  # 1520'de deniz yolu artık önemli
        start_region="İskenderiye",  # Osmanlı Mısır'ı
        end_region="Cidde",  # Kızıldeniz limanı
        base_income=600,
        travel_time=3,
        risk_factor=0.20
    ),
    TradeRoute(
        route_id="mediterranean",
        name="Akdeniz Yolu",
        route_type=RouteType.SEA,
        start_region="İzmir",
        end_region="Venedik",
        base_income=700,
        travel_time=2,
        risk_factor=0.30  # Korsanlar
    ),
    TradeRoute(
        route_id="black_sea",
        name="Karadeniz Yolu",
        route_type=RouteType.SEA,
        start_region="Trabzon",
        end_region="Kefe",  # Kırım'daki Osmanlı limanı (Feodosya)
        base_income=500,
        travel_time=2,
        risk_factor=0.15
    ),
    TradeRoute(
        route_id="balkan_road",
        name="Rumeli Yolu",  # Daha dönemsel isim
        route_type=RouteType.LAND,
        start_region="Edirne",
        end_region="Ragusa",  # Dubrovnik - önemli ticaret ortağı
        base_income=400,
        travel_time=2,
        risk_factor=0.10
    ),
]


class TradeSystem:
    """Ticaret yönetim sistemi"""
    
    def __init__(self):
        self.routes: Dict[str, TradeRoute] = {r.route_id: r for r in DEFAULT_ROUTES}
        self.active_caravans: List[Caravan] = []
        self.trade_agreements: Dict[str, int] = {}  # partner: bonus %
        self.total_trade_income = 0
        self.caravans_lost = 0
        self.caravans_completed = 0
        self.caravan_counter = 0
        
        # Liman durumu (tersane binası gerektirir)
        self.has_port = False
        self.port_level = 0
        
        # YENİ: Pazar fiyatları (dinamik)
        self.market_prices: Dict[TradeGood, MarketPrice] = {}
        for good, base_price in BASE_PRICES.items():
            self.market_prices[good] = MarketPrice(good, base_price)
        
        # YENİ: Tüccar ilişkileri (0-100, yüksek = iyi)
        # 1520 tarihi gerçekliğine uygun:
        # - Memlükler 1517'de fethedildi (artık Osmanlı parçası)
        # - Moğol İmparatorluğu 1368'de dağıldı
        self.merchant_relations: Dict[str, int] = {
            'venedik': 50,      # Venedik Cumhuriyeti - önemli ticaret ortağı
            'ceneviz': 45,      # Ceneviz Cumhuriyeti - rakip ama ticaret var
            'safevi': 30,       # Safevi Devleti - gerilimli ama ticaret var
            'ozbek': 40,        # Özbek Hanlığı - İpek Yolu ticareti
            'gucerat': 45,      # Gücerat Sultanlığı (Hint deniz ticareti)
            'ragusa': 55,       # Dubrovnik - Osmanlı'ya bağlı ticaret şehri
            'portekiz': 25,     # Portekiz - Hint Okyanusu'nda rakip
        }
        
        # YENİ: Mal deposu (envanter)
        self.inventory: Dict[TradeGood, int] = {good: 0 for good in TradeGood}
    
    def update_port_status(self, has_shipyard: bool, shipyard_level: int = 0):
        """Liman durumunu güncelle"""
        self.has_port = has_shipyard
        self.port_level = shipyard_level
    
    def get_available_routes(self) -> List[TradeRoute]:
        """Kullanılabilir yolları getir"""
        available = []
        for route in self.routes.values():
            if not route.active:
                continue
            
            # Deniz yolları liman gerektirir
            if route.route_type == RouteType.SEA and not self.has_port:
                continue
            
            available.append(route)
        
        return available
    
    def buy_good(self, good: TradeGood, quantity: int, economy, merchant: str = None) -> bool:
        """Mal satın al"""
        audio = get_audio_manager()
        
        if good not in self.market_prices:
            return False
        
        price = self.market_prices[good].get_current_price()
        
        # Tüccar ilişkisi indirimi
        if merchant and merchant in self.merchant_relations:
            relation = self.merchant_relations[merchant]
            discount = (relation - 50) / 200  # 50 ilişki = %0, 100 ilişki = %25 indirim
            price = int(price * (1 - discount))
        
        total_cost = price * quantity
        
        if not economy.can_afford(gold=total_cost):
            audio.announce_action_result("Mal alımı", False, "Yetersiz altın")
            return False
        
        economy.spend(gold=total_cost)
        self.inventory[good] += quantity
        
        # Talep arttı -> fiyat artışı
        self.market_prices[good].update_price(demand_change=0.02 * quantity)
        
        audio.announce_action_result(
            f"{quantity} {good.value} alındı",
            True,
            f"Toplam: {total_cost} altın"
        )
        return True
    
    def sell_good(self, good: TradeGood, quantity: int, economy, merchant: str = None) -> bool:
        """Mal sat"""
        audio = get_audio_manager()
        
        if good not in self.inventory or self.inventory[good] < quantity:
            audio.announce_action_result("Mal satışı", False, "Yetersiz mal")
            return False
        
        price = self.market_prices[good].get_current_price()
        
        # Tüccar ilişkisi primi
        if merchant and merchant in self.merchant_relations:
            relation = self.merchant_relations[merchant]
            bonus = (relation - 50) / 200  # 50 ilişki = %0, 100 ilişki = %25 prim
            price = int(price * (1 + bonus))
        
        total_income = price * quantity
        
        economy.add_resources(gold=total_income)
        self.inventory[good] -= quantity
        
        # Arz arttı -> fiyat düşüşü
        self.market_prices[good].update_price(supply_change=0.02 * quantity)
        
        audio.announce_action_result(
            f"{quantity} {good.value} satıldı",
            True,
            f"Kazanç: {total_income} altın"
        )
        return True
    
    def update_market(self, season: str = None, events: List[str] = None):
        """Pazar fiyatlarını güncelle (mevsim ve olaylara göre)"""
        # Mevsimsel etkiler
        if season:
            if season == "winter":
                self.market_prices[TradeGood.SALT].trend = 0.05  # Kışın tuz artar
                self.market_prices[TradeGood.GRAIN].trend = 0.03
                self.market_prices[TradeGood.CLOTH].trend = 0.04
            elif season == "summer":
                self.market_prices[TradeGood.SILK].trend = 0.03  # Yazın ipek artar
                self.market_prices[TradeGood.SPICE].trend = -0.02
            elif season == "spring":
                self.market_prices[TradeGood.GRAIN].trend = -0.05  # İlkbaharda hasat
        
        # Olay etkileri
        if events:
            for event in events:
                if "savaş" in event.lower() or "war" in event.lower():
                    self.market_prices[TradeGood.IRON].trend = 0.1
                    self.market_prices[TradeGood.WOOD].trend = 0.05
                if "kıtlık" in event.lower() or "famine" in event.lower():
                    self.market_prices[TradeGood.GRAIN].trend = 0.15
                if "veba" in event.lower() or "plague" in event.lower():
                    self.market_prices[TradeGood.SPICE].trend = 0.1  # İlaç olarak
        
        # Tüm fiyatları güncelle
        for price in self.market_prices.values():
            price.update_price()
    
    def get_price_info(self, good: TradeGood) -> Dict:
        """Mal fiyat bilgisi"""
        if good not in self.market_prices:
            return {}
        
        mp = self.market_prices[good]
        trend_text = "Yükseliyor" if mp.trend > 0.01 else "Düşüyor" if mp.trend < -0.01 else "Sabit"
        
        return {
            'name': good.value,
            'base_price': mp.base_price,
            'current_price': mp.get_current_price(),
            'multiplier': mp.current_multiplier,
            'trend': trend_text,
            'stock': self.inventory[good]
        }
    
    def announce_market_prices(self):
        """Pazar fiyatlarını duyur"""
        audio = get_audio_manager()
        audio.speak("Pazar Fiyatları:", interrupt=True)
        
        for good in TradeGood:
            info = self.get_price_info(good)
            audio.speak(
                f"{info['name']}: {info['current_price']} altın ({info['trend']}), Stok: {info['stock']}",
                interrupt=False
            )
    
    def send_caravan(self, route_id: str, economy, protection: int = 0) -> Optional[Caravan]:
        """Kervan gönder"""
        if route_id not in self.routes:
            return None
        
        route = self.routes[route_id]
        
        # Maliyet kontrolü
        cost = int(route.base_income * 0.3)  # Yatırım maliyeti
        if not economy.can_afford(gold=cost):
            audio = get_audio_manager()
            audio.announce_action_result("Kervan gönderme", False, f"{cost} altın gerekli")
            return None
        
        # Deniz yolu kontrolü
        if route.route_type == RouteType.SEA and not self.has_port:
            audio = get_audio_manager()
            audio.announce_action_result("Kervan gönderme", False, "Deniz yolu için Tersane gerekli")
            return None
        
        economy.spend(gold=cost)
        
        self.caravan_counter += 1
        caravan = Caravan(
            caravan_id=f"caravan_{self.caravan_counter}",
            route=route,
            status=CaravanStatus.TRAVELING,
            turns_remaining=route.get_total_time(),
            goods_value=route.base_income,
            protection=protection
        )
        
        self.active_caravans.append(caravan)
        
        audio = get_audio_manager()
        audio.announce_action_result(
            f"{route.name} kervanı",
            True,
            f"{route.get_total_time()} tur sonra dönecek"
        )
        
        return caravan
    
    def process_turn(self, economy) -> Dict:
        """Tur sonunda ticaret işle"""
        results = {
            'income': 0,
            'lost_caravans': 0,
            'completed_caravans': 0,
            'events': []
        }
        
        completed = []
        lost = []
        
        for caravan in self.active_caravans:
            caravan.turns_remaining -= 1
            
            # Yolda risk kontrolü
            if caravan.status == CaravanStatus.TRAVELING:
                if random.random() < caravan.route.risk_factor * 0.1:
                    # Tehlike!
                    if random.random() > caravan.get_success_chance():
                        caravan.status = CaravanStatus.LOST
                        lost.append(caravan)
                        results['events'].append(f"{caravan.route.name} kervanı kayboldu!")
                        continue
            
            if caravan.turns_remaining <= 0:
                # Kervan döndü
                caravan.status = CaravanStatus.COMPLETED
                
                # Gelir hesapla
                base_income = caravan.goods_value
                agreement_bonus = self.trade_agreements.get(caravan.route.end_region, 0) / 100
                port_bonus = self.port_level * 0.1 if caravan.route.route_type == RouteType.SEA else 0
                
                total_income = int(base_income * (1 + agreement_bonus + port_bonus))
                economy.add_resources(gold=total_income)
                
                results['income'] += total_income
                results['completed_caravans'] += 1
                completed.append(caravan)
                results['events'].append(f"{caravan.route.name} kervanı {total_income} altın getirdi!")
        
        # Temizlik
        for caravan in completed + lost:
            self.active_caravans.remove(caravan)
            if caravan.status == CaravanStatus.COMPLETED:
                self.caravans_completed += 1
            else:
                self.caravans_lost += 1
        
        results['lost_caravans'] = len(lost)
        self.total_trade_income += results['income']
        
        # Sonuçları duyur
        audio = get_audio_manager()
        if results['income'] > 0:
            audio.play_game_sound('economy', 'trade')  # Kervan varış sesi
            audio.speak(f"Ticaret geliri: {results['income']} altın", interrupt=False)
        if results['lost_caravans'] > 0:
            audio.play_game_sound('events', 'bad')  # Kayıp kervan sesi
            audio.speak(f"Kayıp kervan: {results['lost_caravans']}", interrupt=False)
        
        return results
    
    def establish_trade_agreement(self, partner: str, economy) -> bool:
        """Ticaret anlaşması kur"""
        cost = 500
        if not economy.can_afford(gold=cost):
            audio = get_audio_manager()
            audio.announce_action_result("Ticaret anlaşması", False, "Yetersiz altın")
            return False
        
        economy.spend(gold=cost)
        self.trade_agreements[partner] = 20  # %20 bonus
        
        audio = get_audio_manager()
        audio.announce_action_result(
            f"{partner} ticaret anlaşması",
            True,
            "Yüzde 20 ticaret bonusu"
        )
        return True
    
    def get_route_info(self, route_id: str) -> Optional[Dict]:
        """Yol bilgisi getir"""
        if route_id not in self.routes:
            return None
        
        route = self.routes[route_id]
        return {
            'name': route.name,
            'type': route.route_type.value,
            'income': route.base_income,
            'time': route.get_total_time(),
            'risk': int(route.risk_factor * 100),
            'cost': int(route.base_income * 0.3)
        }
    
    def announce_status(self):
        """Ticaret durumunu duyur"""
        audio = get_audio_manager()
        
        audio.speak("Ticaret Durumu:", interrupt=True)
        audio.speak(f"Aktif kervan: {len(self.active_caravans)}", interrupt=False)
        audio.speak(f"Toplam gelir: {self.total_trade_income} altın", interrupt=False)
        audio.speak(f"Başarılı: {self.caravans_completed}, Kayıp: {self.caravans_lost}", interrupt=False)
        
        if self.has_port:
            audio.speak(f"Liman aktif, seviye {self.port_level}", interrupt=False)
        
        # Aktif kervanları duyur
        if self.active_caravans:
            audio.speak("Yoldaki kervanlar:", interrupt=False)
            for caravan in self.active_caravans:
                audio.speak(
                    f"{caravan.route.name}: {caravan.turns_remaining} tur kaldı",
                    interrupt=False
                )
    
    def announce_routes(self):
        """Mevcut yolları duyur"""
        audio = get_audio_manager()
        available = self.get_available_routes()
        
        audio.speak(f"{len(available)} ticaret yolu mevcut:", interrupt=True)
        
        for route in available:
            risk_text = "Düşük" if route.risk_factor < 0.2 else "Orta" if route.risk_factor < 0.3 else "Yüksek"
            audio.speak(
                f"{route.name}: {route.base_income} altın, {route.get_total_time()} tur, risk {risk_text}",
                interrupt=False
            )
    
    def to_dict(self) -> Dict:
        """Kayıt için dictionary'e dönüştür"""
        # Market prices'ı serileştir
        market_data = {}
        for good, mp in self.market_prices.items():
            market_data[good.value] = {
                'multiplier': mp.current_multiplier,
                'trend': mp.trend
            }
        
        # Inventory'i serileştir
        inventory_data = {good.value: qty for good, qty in self.inventory.items()}
        
        return {
            'trade_agreements': self.trade_agreements,
            'total_trade_income': self.total_trade_income,
            'caravans_lost': self.caravans_lost,
            'caravans_completed': self.caravans_completed,
            'caravan_counter': self.caravan_counter,
            'has_port': self.has_port,
            'port_level': self.port_level,
            'market_prices': market_data,  # YENİ
            'merchant_relations': self.merchant_relations,  # YENİ
            'inventory': inventory_data,  # YENİ
            'active_caravans': [
                {
                    'caravan_id': c.caravan_id,
                    'route_id': c.route.route_id,
                    'turns_remaining': c.turns_remaining,
                    'goods_value': c.goods_value,
                    'protection': c.protection
                }
                for c in self.active_caravans
            ]
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'TradeSystem':
        """Dictionary'den yükle"""
        system = cls()
        system.trade_agreements = data.get('trade_agreements', {})
        system.total_trade_income = data.get('total_trade_income', 0)
        system.caravans_lost = data.get('caravans_lost', 0)
        system.caravans_completed = data.get('caravans_completed', 0)
        system.caravan_counter = data.get('caravan_counter', 0)
        system.has_port = data.get('has_port', False)
        system.port_level = data.get('port_level', 0)
        
        # YENİ: Market prices yükle
        for good_name, mp_data in data.get('market_prices', {}).items():
            for good in TradeGood:
                if good.value == good_name:
                    system.market_prices[good].current_multiplier = mp_data.get('multiplier', 1.0)
                    system.market_prices[good].trend = mp_data.get('trend', 0.0)
                    break
        
        # YENİ: Merchant relations yükle
        saved_relations = data.get('merchant_relations', {})
        system.merchant_relations.update(saved_relations)
        
        # YENİ: Inventory yükle
        for good_name, qty in data.get('inventory', {}).items():
            for good in TradeGood:
                if good.value == good_name:
                    system.inventory[good] = qty
                    break
        
        # Aktif kervanları yükle
        for c_data in data.get('active_caravans', []):
            route = system.routes.get(c_data['route_id'])
            if route:
                caravan = Caravan(
                    caravan_id=c_data.get('caravan_id', f"caravan_{system.caravan_counter}"),
                    route=route,
                    status=CaravanStatus.TRAVELING,
                    turns_remaining=c_data['turns_remaining'],
                    goods_value=c_data['goods_value'],
                    protection=c_data.get('protection', 0)
                )
                system.active_caravans.append(caravan)
        
        return system
