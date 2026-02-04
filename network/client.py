# -*- coding: utf-8 -*-
"""
Osmanlı Eyalet Yönetim Simülasyonu - Çok Oyunculu İstemci
Oyun tarafından kullanılan ağ modülü
"""

import asyncio
import json
import threading
from typing import Callable, Dict, Optional, Any
from queue import Queue

try:
    import websockets
    from websockets.sync.client import connect
    WEBSOCKETS_AVAILABLE = True
except ImportError:
    WEBSOCKETS_AVAILABLE = False
    print("Çok oyunculu mod için: pip install websockets")


class NetworkClient:
    """Çok oyunculu ağ istemcisi"""
    
    def __init__(self):
        self.connected = False
        self.websocket = None
        self.player_id: Optional[str] = None
        self.room_code: Optional[str] = None
        self.room_data: Optional[dict] = None
        self.is_host: bool = False
        
        # Yeniden bağlanma için
        self.reconnect_token: Optional[str] = None
        self._auto_reconnect = True
        self._reconnect_attempts = 0
        self._max_reconnect_attempts = 5
        
        # Mesaj kuyruğu (ana thread ile iletişim için)
        self.incoming_messages: Queue = Queue()
        self.outgoing_messages: Queue = Queue()
        
        # Callback'ler
        self.callbacks: Dict[str, Callable] = {}
        
        # Bekleyen teklifler (ittifak/ticaret)
        self.pending_proposals: list = []
        
        # Bağlantı thread'i
        self._thread: Optional[threading.Thread] = None
        self._running = False
        self._server_uri = ""
    
    def is_available(self) -> bool:
        """WebSocket kütüphanesi mevcut mu?"""
        return WEBSOCKETS_AVAILABLE
    
    def connect(self, server_ip: str, port: int = 8765, blocking: bool = True) -> bool:
        """Sunucuya bağlan (blocking=False ile non-blocking mod)"""
        if not WEBSOCKETS_AVAILABLE:
            print("websockets kütüphanesi yüklü değil!")
            return False
        
        # Önceki bağlantıyı kapat
        if self._running:
            self.disconnect()
        
        self._server_uri = f"ws://{server_ip}:{port}"
        self._running = True
        self._connection_error = None
        
        print(f"Bağlanılıyor: {self._server_uri}")
        
        # Arka plan thread'i başlat
        self._thread = threading.Thread(target=self._connection_loop, daemon=True)
        self._thread.start()
        
        # Non-blocking mod - hemen dön
        if not blocking:
            return True
        
        # Bağlantı için bekle (maksimum 3 saniye)
        import time
        for _ in range(30):  # 30 x 0.1s = 3 saniye
            time.sleep(0.1)
            if self.connected:
                print("Bağlantı başarılı!")
                return True
            if self._connection_error:
                print(f"Bağlantı hatası: {self._connection_error}")
                return False
        
        print("Bağlantı zaman aşımı!")
        return False
    
    def start_connect(self, server_ip: str, port: int = 8765) -> None:
        """Non-blocking bağlantı başlat (is_connecting ile kontrol et)"""
        self.connect(server_ip, port, blocking=False)
    
    def is_connecting(self) -> bool:
        """Bağlantı devam ediyor mu?"""
        return self._running and not self.connected and not self._connection_error
    
    def get_connection_error(self) -> str:
        """Bağlantı hatası varsa döndür"""
        return self._connection_error
    
    def _connection_loop(self):
        """Arka plan bağlantı döngüsü"""
        try:
            print(f"WebSocket bağlantısı açılıyor: {self._server_uri}")
            with connect(self._server_uri, open_timeout=5) as ws:
                self.websocket = ws
                self.connected = True
                print("WebSocket bağlantısı açıldı!")
                
                while self._running:
                    # Önce giden mesajları gönder
                    while not self.outgoing_messages.empty():
                        msg = self.outgoing_messages.get()
                        print(f"Mesaj gönderiliyor: {msg}")
                        ws.send(json.dumps(msg))
                        print("Mesaj gönderildi!")
                    
                    # Gelen mesajları al (timeout ile)
                    try:
                        # websockets sync client için timeout
                        response = ws.recv(timeout=0.1)
                        print(f"Mesaj alındı: {response[:100]}...")
                        data = json.loads(response)
                        # SADECE kuyruğa ekle - işleme ana thread'de yapılacak!
                        self.incoming_messages.put(data)
                        # NOT: _handle_message burada ÇAĞRILMIYOR artık
                    except TimeoutError:
                        pass
                    except Exception as e:
                        err_str = str(e).lower()
                        if "timed out" not in err_str and "timeout" not in err_str:
                            print(f"Mesaj alma hatası: {e}")
                        
        except Exception as e:
            self._connection_error = str(e)
            print(f"Bağlantı hatası: {e}")
            self.connected = False
    
    def disconnect(self):
        """Bağlantıyı kapat"""
        self._running = False
        self.connected = False
        if self.websocket:
            try:
                self.websocket.close()
            except:
                pass
        self.websocket = None
    
    def _send(self, data: dict):
        """Mesaj gönder (kuyruk üzerinden)"""
        if self.connected:
            print(f"Mesaj kuyruğa eklendi: {data}")
            self.outgoing_messages.put(data)
        else:
            print(f"Mesaj gönderilemedi (bağlı değil): {data}")
    
    def _handle_message(self, data: dict):
        """Gelen mesajı işle (SADECE VERİ GÜNCELLEMELERİ - callback yok!)"""
        # Room bilgisini güncelle
        if "room" in data:
            self.room_data = data["room"]
        
        # NOT: player_id güncellenmez - sadece get_pending_messages'da
        # room_created/room_joined mesajlarında güncellenir.
        # Diğer mesajlardaki player_id başka oyuncuların ID'si olabilir!
        
        # Room code güncelle
        if "room_code" in data:
            self.room_code = data["room_code"]
        
        # Reconnect token güncelle
        if "reconnect_token" in data:
            self.reconnect_token = data["reconnect_token"]
        
        # NOT: is_host ve callback'ler get_pending_messages'da ana thread'de işlenir
    
    def register_callback(self, message_type: str, callback: Callable):
        """Mesaj tipi için callback kaydet"""
        self.callbacks[message_type] = callback
    
    def get_pending_messages(self) -> list:
        """Bekleyen mesajları al ve işle (ANA THREAD'DE - tüm işlemler burada)"""
        messages = []
        while not self.incoming_messages.empty():
            data = self.incoming_messages.get()
            messages.append(data)
            
            msg_type = data.get("type", "")
            
            # DEBUG: Mesaj geldiğinde logla
            print(f"[DEBUG] Mesaj alındı: type={msg_type}, player_id_in_msg={data.get('player_id')}, my_player_id={self.player_id}")
            
            # 1. ÖNCE state'i güncelle (mesajdaki verilerle)
            if "room" in data:
                self.room_data = data["room"]
            
            # player_id SADECE kendi oyuncumuza atanan mesajlarda güncellenmeli
            # (room_created, room_joined) - diğer oyuncuların eylemlerinde değil!
            if "player_id" in data and msg_type in ("room_created", "room_joined"):
                old_id = self.player_id
                self.player_id = data["player_id"]
                print(f"[DEBUG] player_id GÜNCELLENDİ: {old_id} -> {self.player_id} (mesaj: {msg_type})")
            
            if "room_code" in data:
                self.room_code = data["room_code"]
            
            if "reconnect_token" in data:
                self.reconnect_token = data["reconnect_token"]
            
            # 2. SONRA is_host'u hesapla (güncel verilerle)
            if self.room_data and self.player_id:
                self.is_host = self.room_data.get("host_id") == self.player_id
            
            # DEBUG: Kendi oyuncu bilgimizi logla
            my_player = self.get_my_player()
            if my_player:
                print(f"[DEBUG] Benim bilgim: name={my_player.get('name')}, province={my_player.get('province')}")
            
            # 3. Teklif işleme
            if msg_type in ("alliance_proposal", "trade_proposal"):
                proposal = {
                    "id": f"{msg_type}_{data.get('from_player', {}).get('id', 'unknown')}",
                    "type": "alliance" if msg_type == "alliance_proposal" else "trade",
                    "from_player": data.get("from_player", {}),
                    "from_player_id": data.get("from_player_id") or data.get("from_player", {}).get("id"),
                    "message": data.get("message", "")
                }
                self.pending_proposals.append(proposal)
                print(f"[DEBUG] Yeni teklif eklendi: {proposal}")
            
            # 4. EN SON callback'i çağır
            if msg_type in self.callbacks:
                try:
                    self.callbacks[msg_type](data)
                except Exception as e:
                    print(f"Callback hatası ({msg_type}): {e}")
        
        return messages
    
    # ===== OYUN AKSIYONLARI =====
    
    def create_room(self, player_name: str):
        """Yeni oda oluştur"""
        self._send({
            "action": "create_room",
            "player_name": player_name
        })
    
    def join_room(self, room_code: str, player_name: str):
        """Odaya katıl"""
        self._send({
            "action": "join_room",
            "room_code": room_code.upper(),
            "player_name": player_name
        })
    
    def select_province(self, province: str):
        """Eyalet seç"""
        self._send({
            "action": "select_province",
            "player_id": self.player_id,
            "province": province
        })
    
    def set_ready(self, ready: bool = True):
        """Hazır durumunu ayarla"""
        self._send({
            "action": "ready",
            "player_id": self.player_id,
            "ready": ready
        })
    
    def start_game(self):
        """Oyunu başlat (sadece host)"""
        if self.is_host:
            self._send({
                "action": "start_game",
                "player_id": self.player_id
            })
    
    def end_turn(self, player_state: dict = None):
        """Turu bitir"""
        self._send({
            "action": "end_turn",
            "player_id": self.player_id,
            "state": player_state or {}
        })
    
    def propose_alliance(self, target_player_id: str):
        """İttifak teklif et"""
        self._send({
            "action": "diplomacy",
            "player_id": self.player_id,
            "target_id": target_player_id,
            "action": "propose_alliance"
        })
    
    def declare_war(self, target_player_id: str):
        """Savaş ilan et"""
        self._send({
            "action": "diplomacy",
            "player_id": self.player_id,
            "target_id": target_player_id,
            "action": "declare_war"
        })
    
    def propose_trade(self, target_player_id: str):
        """Ticaret teklif et"""
        self._send({
            "action": "diplomacy",
            "player_id": self.player_id,
            "target_id": target_player_id,
            "action": "propose_trade"
        })
    
    def attack(self, target_player_id: str):
        """Savaş saldırısı yap"""
        self._send({
            "action": "diplomacy",
            "player_id": self.player_id,
            "target_id": target_player_id,
            "action": "battle"
        })
    
    def accept_alliance(self, from_player_id: str):
        """İttifak teklifini kabul et"""
        self._send({
            "action": "diplomacy",
            "player_id": self.player_id,
            "target_id": from_player_id,
            "action": "accept_alliance"
        })
    
    def reject_alliance(self, from_player_id: str):
        """İttifak teklifini reddet"""
        self._send({
            "action": "diplomacy",
            "player_id": self.player_id,
            "target_id": from_player_id,
            "action": "reject_alliance"
        })
    
    def accept_trade(self, from_player_id: str):
        """Ticaret teklifini kabul et"""
        self._send({
            "action": "diplomacy",
            "player_id": self.player_id,
            "target_id": from_player_id,
            "action": "accept_trade"
        })
    
    def reject_trade(self, from_player_id: str):
        """Ticaret teklifini reddet"""
        self._send({
            "action": "diplomacy",
            "player_id": self.player_id,
            "target_id": from_player_id,
            "action": "reject_trade"
        })
    
    def send_chat(self, message: str):
        """Sohbet mesajı gönder"""
        self._send({
            "action": "chat",
            "player_id": self.player_id,
            "message": message
        })
    
    def update_state(self, state: dict):
        """Oyuncu durumunu güncelle ve senkronize et"""
        self._send({
            "action": "update_state",
            "player_id": self.player_id,
            "state": state
        })
    
    def reconnect(self) -> bool:
        """Önceki odaya yeniden bağlan"""
        if not self.room_code or not self.player_id or not self.reconnect_token:
            print("Yeniden bağlanma bilgileri eksik!")
            return False
        
        self._send({
            "action": "reconnect",
            "room_code": self.room_code,
            "player_id": self.player_id,
            "reconnect_token": self.reconnect_token
        })
        return True
    
    def save_room(self):
        """Odayı kaydet (sadece host)"""
        if not self.is_host:
            print("Sadece host odayı kaydedebilir!")
            return
        
        self._send({
            "action": "save_room",
            "player_id": self.player_id
        })
    
    def load_room(self, room_code: str):
        """Kaydedilmiş odayı yükle"""
        self._send({
            "action": "load_room",
            "room_code": room_code
        })
    
    def ping(self):
        """Bağlantı kontrolü"""
        self._send({"action": "ping"})
    
    # ===== YARDIMCI METODLAR =====
    
    def get_players(self) -> list:
        """Odadaki oyuncuları al"""
        if not self.room_data:
            return []
        return list(self.room_data.get("players", {}).values())
    
    def get_my_player(self) -> Optional[dict]:
        """Kendi oyuncu bilgimizi al"""
        if not self.room_data or not self.player_id:
            return None
        return self.room_data.get("players", {}).get(self.player_id)
    
    def get_available_provinces(self) -> list:
        """Müsait eyaletleri al"""
        if not self.room_data:
            return []
        return self.room_data.get("available_provinces", [])
    
    def is_my_turn(self) -> bool:
        """Sıra bende mi?"""
        if not self.room_data:
            return False
        return self.room_data.get("current_player_id") == self.player_id
    
    def is_game_started(self) -> bool:
        """Oyun başladı mı?"""
        if not self.room_data:
            return False
        return self.room_data.get("game_started", False)
    
    def is_allied_with(self, player_id: str) -> bool:
        """Belirtilen oyuncuyla ittifakta mıyız?"""
        if not self.room_data or not self.player_id:
            return False
        
        # game_state sunucu tarafından room.to_dict()'e eklendi
        game_state = self.room_data.get("game_state", {})
        alliances = game_state.get("alliances", [])
        
        # Alliance: {"player1": id, "player2": id}
        for alliance in alliances:
            p1 = alliance.get("player1")
            p2 = alliance.get("player2")
            if (p1 == self.player_id and p2 == player_id) or (p1 == player_id and p2 == self.player_id):
                return True
        return False
    
    def is_at_war_with(self, player_id: str) -> bool:
        """Belirtilen oyuncuyla savaşta mıyız?"""
        if not self.room_data or not self.player_id:
            return False
        
        # game_state sunucu tarafından room.to_dict()'e eklendi
        game_state = self.room_data.get("game_state", {})
        wars = game_state.get("wars", [])
        
        # War: {"attacker": id, "defender": id, "status": "active"}
        for war in wars:
            if war.get("status") != "active":
                continue
            att = war.get("attacker")
            dfd = war.get("defender")
            if (att == self.player_id and dfd == player_id) or (att == player_id and dfd == self.player_id):
                return True
        return False
    
    def get_pending_proposals(self) -> list:
        """Bekleyen teklifleri döndür"""
        return self.pending_proposals
    
    def clear_proposal(self, proposal_id: str):
        """Yanıtlanan teklifi sil"""
        self.pending_proposals = [p for p in self.pending_proposals if p.get("id") != proposal_id]


# Tekil instance
_network_client: Optional[NetworkClient] = None


def get_network_client() -> NetworkClient:
    """Ağ istemcisi instance'ını al"""
    global _network_client
    if _network_client is None:
        _network_client = NetworkClient()
    return _network_client
