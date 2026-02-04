# -*- coding: utf-8 -*-
"""
Osmanlı Eyalet Yönetim Simülasyonu - HTTP Polling İstemcisi
Basit REST API tabanlı çok oyunculu istemci
"""

import requests
import threading
import time
import uuid
from typing import Optional, Callable, Dict, Any
from queue import Queue


class HTTPNetworkClient:
    """HTTP Polling tabanlı ağ istemcisi"""
    
    def __init__(self):
        self.server_url = ""
        self.player_id = str(uuid.uuid4())
        self.player_name = "Oyuncu"
        self.room_code = None
        self.room_data = None
        self.is_host = False
        self.connected = False
        
        # Polling
        self._polling = False
        self._poll_thread = None
        self._poll_interval = 1.0  # 1 saniye
        
        # Callback'ler
        self.callbacks: Dict[str, Callable] = {}
        
        # Son hata
        self.last_error = None
    
    def is_available(self) -> bool:
        """requests kütüphanesi mevcut mu?"""
        try:
            import requests
            return True
        except ImportError:
            return False
    
    def connect(self, server_ip: str, port: int = 5000) -> bool:
        """Sunucuya bağlantıyı test et"""
        self.server_url = f"http://{server_ip}:{port}"
        
        try:
            r = requests.get(f"{self.server_url}/health", timeout=5)
            if r.status_code == 200:
                self.connected = True
                self.last_error = None
                print(f"[HTTP] Sunucu bağlantısı OK: {self.server_url}")
                return True
        except Exception as e:
            self.last_error = str(e)
            print(f"[HTTP] Bağlantı hatası: {e}")
        
        return False
    
    def start_connect(self, server_ip: str, port: int = 5000):
        """Non-blocking bağlantı başlat (arka planda)"""
        def _connect():
            self.connect(server_ip, port)
        
        threading.Thread(target=_connect, daemon=True).start()
    
    def is_connecting(self) -> bool:
        """Bağlantı devam ediyor mu?"""
        return False  # HTTP anında sonuç döner
    
    def get_connection_error(self) -> str:
        """Bağlantı hatası"""
        return self.last_error
    
    def disconnect(self):
        """Bağlantıyı kapat"""
        self._stop_polling()
        if self.room_code:
            try:
                requests.post(
                    f"{self.server_url}/room/{self.room_code}/leave",
                    json={'player_id': self.player_id},
                    timeout=2
                )
            except:
                pass
        
        self.connected = False
        self.room_code = None
        self.room_data = None
    
    # ===== POLLING =====
    
    def _start_polling(self):
        """Arka planda oda durumunu çekmeye başla"""
        if self._polling:
            return
        
        self._polling = True
        
        def poll_loop():
            while self._polling and self.room_code:
                try:
                    r = requests.get(
                        f"{self.server_url}/room/{self.room_code}",
                        params={'player_id': self.player_id},
                        timeout=5
                    )
                    
                    if r.status_code == 200:
                        data = r.json()
                        old_room = self.room_data
                        self.room_data = data.get('room')
                        
                        # Host kontrolü
                        if self.room_data:
                            self.is_host = self.room_data.get('host_id') == self.player_id
                        
                        # Değişiklik varsa callback çağır
                        if old_room != self.room_data:
                            self._on_room_updated(old_room, self.room_data)
                    
                except Exception as e:
                    print(f"[HTTP] Polling hatası: {e}")
                
                time.sleep(self._poll_interval)
        
        self._poll_thread = threading.Thread(target=poll_loop, daemon=True)
        self._poll_thread.start()
        print("[HTTP] Polling başladı")
    
    def _stop_polling(self):
        """Polling'i durdur"""
        self._polling = False
        print("[HTTP] Polling durduruldu")
    
    def _on_room_updated(self, old_room: dict, new_room: dict):
        """Oda güncellendiğinde callback'leri çağır"""
        if not old_room:
            return
        
        # Yeni oyuncu katıldı mı?
        old_players = set(old_room.get('players', {}).keys())
        new_players = set(new_room.get('players', {}).keys())
        
        for pid in new_players - old_players:
            if 'player_joined' in self.callbacks:
                player = new_room['players'][pid]
                self.callbacks['player_joined']({'player': player})
        
        # Oyuncu ayrıldı mı?
        for pid in old_players - new_players:
            if 'player_left' in self.callbacks:
                self.callbacks['player_left']({'player_id': pid})
        
        # Eyalet değişti mi?
        for pid, player in new_room.get('players', {}).items():
            old_player = old_room.get('players', {}).get(pid, {})
            if player.get('province') != old_player.get('province'):
                if 'province_selected' in self.callbacks:
                    self.callbacks['province_selected']({
                        'player_id': pid,
                        'province': player.get('province')
                    })
        
        # Oyun başladı mı?
        if new_room.get('game_started') and not old_room.get('game_started'):
            if 'game_started' in self.callbacks:
                self.callbacks['game_started']({'room': new_room})
        
        # Tur değişti mi?
        if new_room.get('current_player_id') != old_room.get('current_player_id'):
            if 'turn_changed' in self.callbacks:
                self.callbacks['turn_changed']({
                    'current_player_id': new_room.get('current_player_id'),
                    'turn': new_room.get('current_turn')
                })
    
    def get_pending_messages(self) -> list:
        """Uyumluluk için - HTTP'de mesaj kuyruğu yok"""
        return []
    
    def register_callback(self, event_type: str, callback: Callable):
        """Olay için callback kaydet"""
        self.callbacks[event_type] = callback
    
    # ===== ODA İŞLEMLERİ =====
    
    def create_room(self, player_name: str) -> bool:
        """Oda oluştur"""
        self.player_name = player_name
        
        try:
            r = requests.post(
                f"{self.server_url}/room/create",
                json={'player_id': self.player_id, 'name': player_name},
                timeout=5
            )
            
            if r.status_code == 200:
                data = r.json()
                self.room_code = data.get('room_code')
                self.room_data = data.get('room')
                self.is_host = True
                
                print(f"[HTTP] Oda oluşturuldu: {self.room_code}")
                
                if 'room_created' in self.callbacks:
                    self.callbacks['room_created'](data)
                
                self._start_polling()
                return True
        except Exception as e:
            self.last_error = str(e)
            print(f"[HTTP] Oda oluşturma hatası: {e}")
        
        return False
    
    def join_room(self, room_code: str, player_name: str) -> bool:
        """Odaya katıl"""
        self.player_name = player_name
        
        try:
            r = requests.post(
                f"{self.server_url}/room/{room_code}/join",
                json={'player_id': self.player_id, 'name': player_name},
                timeout=5
            )
            
            if r.status_code == 200:
                data = r.json()
                self.room_code = room_code
                self.room_data = data.get('room')
                self.is_host = False
                
                print(f"[HTTP] Odaya katıldı: {room_code}")
                
                if 'room_joined' in self.callbacks:
                    self.callbacks['room_joined'](data)
                
                self._start_polling()
                return True
            else:
                data = r.json()
                self.last_error = data.get('error', 'Bilinmeyen hata')
        except Exception as e:
            self.last_error = str(e)
            print(f"[HTTP] Katılma hatası: {e}")
        
        return False
    
    def select_province(self, province: str) -> bool:
        """Eyalet seç"""
        try:
            r = requests.post(
                f"{self.server_url}/room/{self.room_code}/select",
                json={'player_id': self.player_id, 'province': province},
                timeout=5
            )
            
            if r.status_code == 200:
                data = r.json()
                self.room_data = data.get('room')
                print(f"[HTTP] Eyalet seçildi: {province}")
                return True
            else:
                data = r.json()
                self.last_error = data.get('error', 'Seçim başarısız')
        except Exception as e:
            self.last_error = str(e)
        
        return False
    
    def start_game(self) -> bool:
        """Oyunu başlat"""
        try:
            r = requests.post(
                f"{self.server_url}/room/{self.room_code}/start",
                json={'player_id': self.player_id},
                timeout=5
            )
            
            if r.status_code == 200:
                data = r.json()
                self.room_data = data.get('room')
                print("[HTTP] Oyun başlatıldı!")
                return True
            else:
                data = r.json()
                self.last_error = data.get('error', 'Başlatma başarısız')
        except Exception as e:
            self.last_error = str(e)
        
        return False
    
    def end_turn(self, player_state: dict = None) -> bool:
        """Turu bitir"""
        try:
            r = requests.post(
                f"{self.server_url}/room/{self.room_code}/end_turn",
                json={'player_id': self.player_id, 'state': player_state or {}},
                timeout=5
            )
            
            if r.status_code == 200:
                data = r.json()
                self.room_data = data.get('room')
                return True
        except Exception as e:
            self.last_error = str(e)
        
        return False
    
    def send_chat(self, message: str):
        """Sohbet mesajı gönder"""
        try:
            requests.post(
                f"{self.server_url}/room/{self.room_code}/chat",
                json={'player_id': self.player_id, 'message': message},
                timeout=5
            )
        except:
            pass
    
    # ===== YARDIMCI METODLAR =====
    
    def get_players(self) -> list:
        """Odadaki oyuncuları al"""
        if not self.room_data:
            return []
        return list(self.room_data.get('players', {}).values())
    
    def get_my_player(self) -> Optional[dict]:
        """Kendi oyuncu bilgimi al"""
        if not self.room_data or not self.player_id:
            return None
        return self.room_data.get('players', {}).get(self.player_id)
    
    def get_available_provinces(self) -> list:
        """Müsait eyaletleri al"""
        # Tüm eyaletleri territories.py'den al
        try:
            from game.data.territories import TERRITORIES, TerritoryType
            all_provinces = [
                t.name for t in TERRITORIES.values() 
                if t.territory_type in [TerritoryType.OSMANLI_EYALET, TerritoryType.OSMANLI_SANCAK, TerritoryType.VASAL]
            ]
        except ImportError:
            # Fallback - statik liste
            all_provinces = [
                "Aydın Sancağı", "Selanik Sancağı", "Trabzon Eyaleti",
                "Rum Eyaleti", "Karaman Eyaleti", "Halep Eyaleti"
            ]
        
        if not self.room_data:
            return all_provinces
        
        taken = set()
        for player in self.room_data.get('players', {}).values():
            if player.get('province'):
                taken.add(player['province'])
        
        return [p for p in all_provinces if p not in taken]
    
    def is_my_turn(self) -> bool:
        """Sıra bende mi?"""
        if not self.room_data:
            return False
        return self.room_data.get('current_player_id') == self.player_id
    
    def is_game_started(self) -> bool:
        """Oyun başladı mı?"""
        if not self.room_data:
            return False
        return self.room_data.get('game_started', False)
