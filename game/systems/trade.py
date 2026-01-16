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


# Varsayılan ticaret yolları
DEFAULT_ROUTES = [
    TradeRoute(
        route_id="silk_road",
        name="İpek Yolu",
        route_type=RouteType.SILK,
        start_region="Anadolu",
        end_region="Çin Sınırı",
        base_income=800,
        travel_time=4,
        risk_factor=0.25
    ),
    TradeRoute(
        route_id="spice_route",
        name="Baharat Yolu",
        route_type=RouteType.LAND,
        start_region="Halep",
        end_region="Hindistan",
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
        end_region="Kırım",
        base_income=500,
        travel_time=2,
        risk_factor=0.15
    ),
    TradeRoute(
        route_id="balkan_road",
        name="Balkan Yolu",
        route_type=RouteType.LAND,
        start_region="Edirne",
        end_region="Belgrad",
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
            audio.speak(f"Ticaret geliri: {results['income']} altın", interrupt=False)
        if results['lost_caravans'] > 0:
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
        return {
            'trade_agreements': self.trade_agreements,
            'total_trade_income': self.total_trade_income,
            'caravans_lost': self.caravans_lost,
            'caravans_completed': self.caravans_completed,
            'caravan_counter': self.caravan_counter,
            'has_port': self.has_port,
            'port_level': self.port_level,
            'active_caravans': [
                {
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
        
        # Aktif kervanları yükle
        for c_data in data.get('active_caravans', []):
            route = system.routes.get(c_data['route_id'])
            if route:
                caravan = Caravan(
                    caravan_id=f"caravan_{system.caravan_counter}",
                    route=route,
                    status=CaravanStatus.TRAVELING,
                    turns_remaining=c_data['turns_remaining'],
                    goods_value=c_data['goods_value'],
                    protection=c_data.get('protection', 0)
                )
                system.active_caravans.append(caravan)
        
        return system
