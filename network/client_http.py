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
        self._poll_interval = 2.0  # 2 saniye (Rate limit dostu)
        
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
            if 'turn_ended' in self.callbacks:
                self.callbacks['turn_ended']({
                    'previous_player': old_room.get('current_player_id'),
                    'current_player': new_room.get('current_player_id')
                })
        
        # Sohbet mesajı var mı?
        old_chat = old_room.get('chat', [])
        new_chat = new_room.get('chat', [])
        if len(new_chat) > len(old_chat):
            for msg in new_chat[len(old_chat):]:
                if 'chat_message' in self.callbacks:
                    self.callbacks['chat_message'](msg)
                    
        # Diplomasi teklifleri
        old_props = old_room.get('diplomacy', {}).get('pending_proposals', [])
        new_props = new_room.get('diplomacy', {}).get('pending_proposals', [])
        if len(new_props) > len(old_props):
            for prop in new_props[len(old_props):]:
                if prop.get('to_player_id') == self.player_id:
                    if prop.get('type') == 'alliance' and 'alliance_proposal' in self.callbacks:
                        self.callbacks['alliance_proposal'](prop)
                    elif prop.get('type') == 'trade' and 'trade_proposal' in self.callbacks:
                        self.callbacks['trade_proposal'](prop)
        
        # Savaş İlanları
        old_wars = old_room.get('diplomacy', {}).get('wars', [])
        new_wars = new_room.get('diplomacy', {}).get('wars', [])
        if len(new_wars) > len(old_wars):
            for war in new_wars[len(old_wars):]:
                if 'war_declared' in self.callbacks:
                    self.callbacks['war_declared'](war)
                    
        # İttifak Kuruldu
        old_ally = old_room.get('diplomacy', {}).get('alliances', [])
        new_ally = new_room.get('diplomacy', {}).get('alliances', [])
        if len(new_ally) > len(old_ally):
            for ally in new_ally[len(old_ally):]:
                if 'alliance_formed' in self.callbacks:
                    self.callbacks['alliance_formed'](ally)
                    
        # Ticaret Kuruldu
        old_trade = old_room.get('diplomacy', {}).get('trade_deals', [])
        new_trade = new_room.get('diplomacy', {}).get('trade_deals', [])
        if len(new_trade) > len(old_trade):
            for trade in new_trade[len(old_trade):]:
                if 'trade_agreement_formed' in self.callbacks:
                    self.callbacks['trade_agreement_formed'](trade)
    
    def get_pending_messages(self) -> list:
        """Uyumluluk için - HTTP'de mesaj kuyruğu yok"""
        return []

    def get_pending_proposals(self) -> list:
        """Uyumluluk İçin - Bekleyen teklifleri döndür"""
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
            # State'i de senkronize et
            if player_state:
                self.sync_state(player_state)
            
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
    
    def sync_state(self, state: dict) -> bool:
        """Genişletilmiş oyuncu durumunu senkronize et"""
        try:
            r = requests.post(
                f"{self.server_url}/room/{self.room_code}/sync_state",
                json={'player_id': self.player_id, 'state': state},
                timeout=5
            )
            return r.status_code == 200
        except Exception:
            return False
    
    def build_state_from_game(self, game_manager) -> dict:
        """game_manager'dan sunucuya gönderilecek state sözlüğü oluştur"""
        gm = game_manager
        state = {
            'gold': getattr(gm.economy, 'gold', 0) if hasattr(gm, 'economy') else 0,
            'military_power': gm.military.get_total_power() if hasattr(gm, 'military') else 0,
            'total_soldiers': gm.military.get_total_soldiers() if hasattr(gm, 'military') else 0,
            'population': gm.population.total if hasattr(gm, 'population') else 0,
            'happiness': gm.population.happiness if hasattr(gm, 'population') else 50,
        }
        
        # Genişletilmiş alanlar (varsa)
        if hasattr(gm, 'naval'):
            state['naval_power'] = gm.naval.get_fleet_power()
        if hasattr(gm, 'guild_system'):
            state['guild_count'] = len(gm.guild_system.guilds)
        if hasattr(gm, 'warfare'):
            state['warfare_status'] = 'war' if gm.warfare.active_battles else 'peace'
        if hasattr(gm, 'loyalty_system'):
            state['loyalty'] = getattr(gm.loyalty_system, 'padisah_loyalty', 50)
        if hasattr(gm, 'economy'):
            state['tax_income'] = getattr(gm.economy, 'last_tax_income', 0)
        
        return state
    
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

    # ===== DIPLOMASI VE SAVAS METODLARI =====

    def is_allied_with(self, player_id: str) -> bool:
        if not self.room_data: return False
        for a in self.room_data.get('diplomacy', {}).get('alliances', []):
            if self.player_id in a and player_id in a:
                return True
        return False

    def is_at_war_with(self, player_id: str) -> bool:
        if not self.room_data: return False
        for w in self.room_data.get('diplomacy', {}).get('wars', []):
            if (w.get('attacker_id') == self.player_id and w.get('defender_id') == player_id) or \
               (w.get('defender_id') == self.player_id and w.get('attacker_id') == player_id):
                return True
        return False

    def propose_alliance(self, player_id: str):
        try:
            requests.post(f"{self.server_url}/room/{self.room_code}/diplomacy/propose", 
                          json={'from_player_id': self.player_id, 'to_player_id': player_id, 'type': 'alliance', 'terms': {}}, timeout=2)
        except: pass

    def propose_trade(self, player_id: str):
        try:
            requests.post(f"{self.server_url}/room/{self.room_code}/diplomacy/propose", 
                          json={'from_player_id': self.player_id, 'to_player_id': player_id, 'type': 'trade', 'terms': {}}, timeout=2)
        except: pass

    def declare_war(self, player_id: str):
        try:
            requests.post(f"{self.server_url}/room/{self.room_code}/diplomacy/war", 
                          json={'attacker_id': self.player_id, 'defender_id': player_id}, timeout=2)
        except: pass

    def attack(self, target_id: str, power: int) -> dict:
        try:
            r = requests.post(f"{self.server_url}/room/{self.room_code}/battle", 
                              json={'attacker_id': self.player_id, 'defender_id': target_id, 'power': power}, timeout=5)
            if r.status_code == 200: return r.json()
        except Exception as e:
            self.last_error = str(e)
        return {}

    def get_player_info(self, target_id: str) -> dict:
        try:
            r = requests.get(f"{self.server_url}/room/{self.room_code}/player/{target_id}", timeout=2)
            if r.status_code == 200: return r.json()
        except: pass
        return {}
        
    def respond_proposal(self, proposal_id: str, accept: bool) -> bool:
        try:
            r = requests.post(f"{self.server_url}/room/{self.room_code}/diplomacy/respond", 
                              json={'player_id': self.player_id, 'proposal_id': proposal_id, 'accept': accept}, timeout=2)
            return r.status_code == 200
        except Exception as e:
            self.last_error = str(e)
            return False

    def save_room(self) -> bool:
        """Sunucuda odayı kaydet"""
        try:
            r = requests.post(f"{self.server_url}/room/{self.room_code}/save", 
                              json={'player_id': self.player_id}, timeout=2)
            return r.status_code == 200
        except Exception as e:
            self.last_error = str(e)
            return False

