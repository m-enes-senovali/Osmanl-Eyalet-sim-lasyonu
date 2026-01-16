# -*- coding: utf-8 -*-
"""
Osmanlı Eyalet Yönetim Simülasyonu - Çok Oyunculu Sunucu
WebSocket tabanlı gerçek zamanlı sunucu

Kullanım:
    python server.py --port 8765

Gerekli kütüphaneler:
    pip install websockets
"""

import asyncio
import json
import random
import string
import argparse
from datetime import datetime
from typing import Dict, Set, Optional
from dataclasses import dataclass, asdict

try:
    import websockets
    from websockets.server import serve
except ImportError:
    print("websockets kütüphanesi gerekli: pip install websockets")
    exit(1)


@dataclass
class Player:
    """Oyuncu bilgisi"""
    id: str
    name: str
    province: str
    websocket: any = None
    ready: bool = False
    connected: bool = True
    # Yeniden bağlanma için
    reconnect_token: str = ""
    last_activity: str = ""
    disconnect_time: str = ""
    # Oyuncu durumu (oyun içi)
    game_state: dict = None
    
    def __post_init__(self):
        if self.game_state is None:
            self.game_state = {
                "gold": 1000,
                "population": 10000,
                "army": 500,
                "resources": {
                    "food": 100,
                    "wood": 100,
                    "stone": 50,
                    "iron": 25
                },
                "buildings": []
            }
        if not self.reconnect_token:
            self.reconnect_token = ''.join(random.choices(string.ascii_letters + string.digits, k=32))
        if not self.last_activity:
            self.last_activity = datetime.now().isoformat()
    
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "province": self.province,
            "ready": self.ready,
            "connected": self.connected,
            "game_state": self.game_state
        }


@dataclass 
class GameRoom:
    """Oyun odası"""
    code: str
    host_id: str
    players: Dict[str, Player]
    max_players: int = 20  # Artırıldı (eskiden 6)
    game_started: bool = False
    current_turn: int = 0
    current_player_id: Optional[str] = None
    game_state: dict = None
    
    # Eyalet listesi - 1520 Osmanlı Dönemi (50+ bölge)
    PROVINCES = [
        # Anadolu Eyaletleri
        "Rum Eyaleti", "Anadolu Eyaleti", "Karaman Eyaleti", "Dulkadir Eyaleti",
        "Diyarbekir Eyaleti", "Trabzon Eyaleti",
        # Anadolu Sancakları
        "Kastamonu Sancağı", "Bolu Sancağı", "Hüdavendigar Sancağı", "Karesi Sancağı",
        "Saruhan Sancağı", "Aydın Sancağı", "Menteşe Sancağı", "Teke Sancağı", "Hamid Sancağı",
        # Balkan Eyaletleri
        "Rumeli Eyaleti",
        # Balkan Sancakları
        "Selanik Sancağı", "Mora Sancağı", "Yanya Sancağı", "Ohri Sancağı",
        "Üsküp Sancağı", "Kosova Sancağı", "Semendire Sancağı", "Vidin Sancağı",
        "Niğbolu Sancağı", "Silistre Sancağı", "Bosna Sancağı", "Hersek Sancağı", "Arnavutluk Sancağı",
        # Ortadoğu
        "Halep Eyaleti", "Şam Eyaleti", "Rakka Sancağı", "Musul Sancağı",
        # Afrika
        "Mısır Eyaleti", "Trablusgarp Eyaleti", "Cezayir Eyaleti",
        # Vasal Devletler
        "Kırım Hanlığı", "Eflak Voyvodalığı", "Boğdan Voyvodalığı", "Erdel Prensliği", "Ragusa Cumhuriyeti",
        # Komşu Devletler (oynanabilir)
        "Safevi İmparatorluğu", "Macaristan Krallığı", "Venedik", "Lehistan-Litvanya",
    ]
    
    def __post_init__(self):
        if self.game_state is None:
            self.game_state = {
                "year": 1520,
                "month": 1,
                "day": 1,
                "alliances": [],  # [(player1_id, player2_id), ...]
                "wars": [],       # [(attacker_id, defender_id, status), ...]
                "trade_agreements": [],
                "messages": []    # Oyun içi mesajlar
            }
    
    def get_available_provinces(self) -> list:
        """Müsait eyaletleri döndür"""
        taken = [p.province for p in self.players.values()]
        return [prov for prov in self.PROVINCES if prov not in taken]
    
    def to_dict(self):
        return {
            "code": self.code,
            "host_id": self.host_id,
            "players": {pid: p.to_dict() for pid, p in self.players.items()},
            "max_players": self.max_players,
            "game_started": self.game_started,
            "current_turn": self.current_turn,
            "current_player_id": self.current_player_id,
            "available_provinces": self.get_available_provinces()
        }


class GameServer:
    """Ana sunucu sınıfı"""
    
    def __init__(self, host: str = "0.0.0.0", port: int = 8765):
        self.host = host
        self.port = port
        self.rooms: Dict[str, GameRoom] = {}
        self.player_room_map: Dict[str, str] = {}  # player_id -> room_code
        self.connections: Dict[str, any] = {}  # player_id -> websocket
        
    def generate_room_code(self) -> str:
        """6 karakterlik oda kodu oluştur"""
        while True:
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
            if code not in self.rooms:
                return code
    
    def generate_player_id(self) -> str:
        """Benzersiz oyuncu ID'si oluştur"""
        return ''.join(random.choices(string.ascii_lowercase + string.digits, k=12))
    
    async def broadcast_to_room(self, room_code: str, message: dict, exclude_id: str = None):
        """Odadaki tüm oyunculara mesaj gönder"""
        if room_code not in self.rooms:
            return
        
        room = self.rooms[room_code]
        for player_id, player in room.players.items():
            if player_id != exclude_id and player.websocket:
                try:
                    await player.websocket.send(json.dumps(message))
                except:
                    pass
    
    async def send_to_player(self, player_id: str, message: dict):
        """Belirli bir oyuncuya mesaj gönder"""
        if player_id in self.connections:
            try:
                await self.connections[player_id].send(json.dumps(message))
            except:
                pass
    
    async def handle_create_room(self, websocket, data: dict) -> dict:
        """Yeni oda oluştur"""
        player_name = data.get("player_name", "Anonim")
        
        room_code = self.generate_room_code()
        player_id = self.generate_player_id()
        
        player = Player(
            id=player_id,
            name=player_name,
            province="",
            websocket=websocket
        )
        
        room = GameRoom(
            code=room_code,
            host_id=player_id,
            players={player_id: player}
        )
        
        self.rooms[room_code] = room
        self.player_room_map[player_id] = room_code
        self.connections[player_id] = websocket
        
        print(f"[{datetime.now()}] Oda oluşturuldu: {room_code} - Host: {player_name}")
        
        return {
            "type": "room_created",
            "success": True,
            "room_code": room_code,
            "player_id": player_id,
            "reconnect_token": player.reconnect_token,
            "room": room.to_dict()
        }
    
    async def handle_join_room(self, websocket, data: dict) -> dict:
        """Odaya katıl"""
        room_code = data.get("room_code", "").upper()
        player_name = data.get("player_name", "Anonim")
        
        if room_code not in self.rooms:
            return {"type": "error", "message": "Oda bulunamadı"}
        
        room = self.rooms[room_code]
        
        if room.game_started:
            return {"type": "error", "message": "Oyun zaten başlamış"}
        
        if len(room.players) >= room.max_players:
            return {"type": "error", "message": "Oda dolu"}
        
        player_id = self.generate_player_id()
        player = Player(
            id=player_id,
            name=player_name,
            province="",
            websocket=websocket
        )
        
        room.players[player_id] = player
        self.player_room_map[player_id] = room_code
        self.connections[player_id] = websocket
        
        print(f"[{datetime.now()}] {player_name} odaya katıldı: {room_code}")
        
        # Diğer oyunculara bildir
        await self.broadcast_to_room(room_code, {
            "type": "player_joined",
            "player": player.to_dict(),
            "room": room.to_dict()
        }, exclude_id=player_id)
        
        return {
            "type": "room_joined",
            "success": True,
            "player_id": player_id,
            "reconnect_token": player.reconnect_token,
            "room": room.to_dict()
        }
    
    async def handle_select_province(self, websocket, data: dict) -> dict:
        """Eyalet seç"""
        player_id = data.get("player_id")
        province = data.get("province")
        
        if player_id not in self.player_room_map:
            return {"type": "error", "message": "Oyuncu bulunamadı"}
        
        room_code = self.player_room_map[player_id]
        room = self.rooms[room_code]
        
        if province not in room.get_available_provinces():
            return {"type": "error", "message": "Bu eyalet müsait değil"}
        
        room.players[player_id].province = province
        
        print(f"[{datetime.now()}] {room.players[player_id].name} eyalet seçti: {province}")
        
        # Herkese bildir
        await self.broadcast_to_room(room_code, {
            "type": "province_selected",
            "player_id": player_id,
            "province": province,
            "room": room.to_dict()
        })
        
        return {"type": "success", "message": f"{province} seçildi"}
    
    async def handle_ready(self, websocket, data: dict) -> dict:
        """Hazır durumunu değiştir"""
        player_id = data.get("player_id")
        ready = data.get("ready", True)
        
        if player_id not in self.player_room_map:
            return {"type": "error", "message": "Oyuncu bulunamadı"}
        
        room_code = self.player_room_map[player_id]
        room = self.rooms[room_code]
        player = room.players[player_id]
        
        if not player.province:
            return {"type": "error", "message": "Önce eyalet seçmelisiniz"}
        
        player.ready = ready
        
        # Herkese bildir
        await self.broadcast_to_room(room_code, {
            "type": "player_ready",
            "player_id": player_id,
            "ready": ready,
            "room": room.to_dict()
        })
        
        # Tüm oyuncular hazır mı kontrol et
        all_ready = all(p.ready and p.province for p in room.players.values())
        if all_ready and len(room.players) >= 2:
            await self.broadcast_to_room(room_code, {
                "type": "all_ready",
                "message": "Tüm oyuncular hazır! Host oyunu başlatabilir."
            })
        
        return {"type": "success"}
    
    async def handle_start_game(self, websocket, data: dict) -> dict:
        """Oyunu başlat (sadece host)"""
        player_id = data.get("player_id")
        
        if player_id not in self.player_room_map:
            return {"type": "error", "message": "Oyuncu bulunamadı"}
        
        room_code = self.player_room_map[player_id]
        room = self.rooms[room_code]
        
        if room.host_id != player_id:
            return {"type": "error", "message": "Sadece host oyunu başlatabilir"}
        
        if len(room.players) < 2:
            return {"type": "error", "message": "En az 2 oyuncu gerekli"}
        
        # Tüm oyuncular eyalet seçmiş mi?
        for p in room.players.values():
            if not p.province:
                return {"type": "error", "message": f"{p.name} henüz eyalet seçmedi"}
        
        room.game_started = True
        room.current_turn = 1
        room.current_player_id = list(room.players.keys())[0]
        
        print(f"[{datetime.now()}] Oyun başladı: {room_code}")
        
        # Herkese bildir
        await self.broadcast_to_room(room_code, {
            "type": "game_started",
            "room": room.to_dict(),
            "first_player": room.players[room.current_player_id].to_dict()
        })
        
        return {"type": "success"}
    
    async def handle_end_turn(self, websocket, data: dict) -> dict:
        """Turu bitir"""
        player_id = data.get("player_id")
        player_state = data.get("state", {})  # Oyuncunun güncel durumu
        
        if player_id not in self.player_room_map:
            return {"type": "error", "message": "Oyuncu bulunamadı"}
        
        room_code = self.player_room_map[player_id]
        room = self.rooms[room_code]
        
        if room.current_player_id != player_id:
            return {"type": "error", "message": "Sıra sizde değil"}
        
        # Sıradaki oyuncuya geç
        player_ids = list(room.players.keys())
        current_index = player_ids.index(player_id)
        next_index = (current_index + 1) % len(player_ids)
        
        room.current_player_id = player_ids[next_index]
        
        # Eğer tur tamamlandıysa
        if next_index == 0:
            room.current_turn += 1
            room.game_state["day"] += 1
            
            # Ay geçişi
            days_in_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
            if room.game_state["day"] > days_in_month[room.game_state["month"] - 1]:
                room.game_state["day"] = 1
                room.game_state["month"] += 1
                
                if room.game_state["month"] > 12:
                    room.game_state["month"] = 1
                    room.game_state["year"] += 1
        
        # Herkese bildir
        await self.broadcast_to_room(room_code, {
            "type": "turn_ended",
            "previous_player": player_id,
            "current_player": room.current_player_id,
            "room": room.to_dict(),
            "game_state": room.game_state
        })
        
        return {"type": "success", "next_player": room.current_player_id}
    
    async def handle_diplomacy_action(self, websocket, data: dict) -> dict:
        """Diplomasi aksiyonu (ittifak, savaş, ticaret)"""
        player_id = data.get("player_id")
        action = data.get("action")  # "propose_alliance", "declare_war", "propose_trade"
        target_id = data.get("target_id")
        
        if player_id not in self.player_room_map:
            return {"type": "error", "message": "Oyuncu bulunamadı"}
        
        room_code = self.player_room_map[player_id]
        room = self.rooms[room_code]
        
        if target_id not in room.players:
            return {"type": "error", "message": "Hedef oyuncu bulunamadı"}
        
        player = room.players[player_id]
        target = room.players[target_id]
        
        if action == "propose_alliance":
            # İttifak teklifi
            await self.send_to_player(target_id, {
                "type": "alliance_proposal",
                "from_player": player.to_dict(),
                "message": f"{player.name} ({player.province}) size ittifak teklif ediyor!"
            })
            return {"type": "success", "message": "İttifak teklifi gönderildi"}
        
        elif action == "declare_war":
            # Savaş ilanı
            war_id = f"war_{room.current_turn}_{player_id[:4]}_{target_id[:4]}"
            
            room.game_state["wars"].append({
                "id": war_id,
                "attacker": player_id,
                "defender": target_id,
                "status": "active",
                "started_turn": room.current_turn,
                "battles": []
            })
            
            await self.broadcast_to_room(room_code, {
                "type": "war_declared",
                "war_id": war_id,
                "attacker": player.to_dict(),
                "defender": target.to_dict(),
                "message": f"⚔️ {player.name} ({player.province}), {target.name} ({target.province})'e savaş ilan etti!"
            })
            return {"type": "success", "message": "Savaş ilan edildi"}
        
        elif action == "battle":
            # Savaş saldırısı - basit savaş mekaniği
            import random
            
            attacker_army = player.game_state.get("army", 100)
            defender_army = target.game_state.get("army", 100)
            
            # Basit savaş hesabı
            attacker_strength = attacker_army * random.uniform(0.8, 1.2)
            defender_strength = defender_army * random.uniform(0.8, 1.2)
            
            if attacker_strength > defender_strength:
                # Saldırgan kazandı
                attacker_losses = int(attacker_army * random.uniform(0.1, 0.3))
                defender_losses = int(defender_army * random.uniform(0.4, 0.7))
                winner = "attacker"
                result_msg = f"🏆 {player.name} savaşı kazandı!"
            else:
                # Savunan kazandı
                attacker_losses = int(attacker_army * random.uniform(0.4, 0.7))
                defender_losses = int(defender_army * random.uniform(0.1, 0.3))
                winner = "defender"
                result_msg = f"🛡️ {target.name} savunmayı başardı!"
            
            # Kayıpları uygula
            player.game_state["army"] = max(0, attacker_army - attacker_losses)
            target.game_state["army"] = max(0, defender_army - defender_losses)
            
            await self.broadcast_to_room(room_code, {
                "type": "battle_result",
                "attacker": player.to_dict(),
                "defender": target.to_dict(),
                "winner": winner,
                "attacker_losses": attacker_losses,
                "defender_losses": defender_losses,
                "message": f"{result_msg} Saldırgan kayıp: {attacker_losses}, Savunan kayıp: {defender_losses}"
            })
            return {"type": "success", "message": result_msg}
        
        elif action == "propose_trade":
            # Ticaret anlaşması teklifi
            await self.send_to_player(target_id, {
                "type": "trade_proposal",
                "from_player": player.to_dict(),
                "from_player_id": player_id,
                "message": f"{player.name} ({player.province}) ticaret anlaşması teklif ediyor!"
            })
            return {"type": "success", "message": "Ticaret teklifi gönderildi"}
        
        elif action == "accept_alliance":
            # İttifak kabul
            room.game_state["alliances"].append({
                "player1": player_id,
                "player2": target_id,
                "started_turn": room.current_turn
            })
            
            await self.broadcast_to_room(room_code, {
                "type": "alliance_formed",
                "player1": player.to_dict(),
                "player2": target.to_dict(),
                "message": f"🤝 {player.name} ve {target.name} ittifak kurdu!"
            })
            return {"type": "success", "message": "İttifak kuruldu"}
        
        elif action == "reject_alliance":
            # İttifak red
            await self.send_to_player(target_id, {
                "type": "alliance_rejected",
                "from_player": player.to_dict(),
                "message": f"{player.name} ittifak teklifinizi reddetti."
            })
            return {"type": "success", "message": "İttifak reddedildi"}
        
        elif action == "accept_trade":
            # Ticaret kabul
            room.game_state["trade_agreements"].append({
                "player1": player_id,
                "player2": target_id,
                "started_turn": room.current_turn
            })
            
            await self.broadcast_to_room(room_code, {
                "type": "trade_agreement_formed",
                "player1": player.to_dict(),
                "player2": target.to_dict(),
                "message": f"💰 {player.name} ve {target.name} ticaret anlaşması imzaladı!"
            })
            return {"type": "success", "message": "Ticaret anlaşması kuruldu"}
        
        elif action == "reject_trade":
            # Ticaret red
            await self.send_to_player(target_id, {
                "type": "trade_rejected",
                "from_player": player.to_dict(),
                "message": f"{player.name} ticaret teklifinizi reddetti."
            })
            return {"type": "success", "message": "Ticaret reddedildi"}
        
        return {"type": "error", "message": "Geçersiz aksiyon"}
    
    async def handle_chat(self, websocket, data: dict) -> dict:
        """Sohbet mesajı"""
        player_id = data.get("player_id")
        message = data.get("message", "")
        
        if player_id not in self.player_room_map:
            return {"type": "error", "message": "Oyuncu bulunamadı"}
        
        room_code = self.player_room_map[player_id]
        room = self.rooms[room_code]
        player = room.players[player_id]
        
        # Herkese gönder
        await self.broadcast_to_room(room_code, {
            "type": "chat_message",
            "from_player": player.to_dict(),
            "message": message,
            "timestamp": datetime.now().isoformat()
        })
        
        return {"type": "success"}
    
    async def handle_update_state(self, websocket, data: dict) -> dict:
        """Oyuncu durumunu güncelle ve senkronize et"""
        player_id = data.get("player_id")
        new_state = data.get("state", {})
        
        if player_id not in self.player_room_map:
            return {"type": "error", "message": "Oyuncu bulunamadı"}
        
        room_code = self.player_room_map[player_id]
        room = self.rooms[room_code]
        player = room.players[player_id]
        
        # Durumu güncelle
        player.game_state.update(new_state)
        
        # Diğer oyunculara bildir
        await self.broadcast_to_room(room_code, {
            "type": "player_state_updated",
            "player_id": player_id,
            "player": player.to_dict()
        }, exclude_id=player_id)
        
        return {"type": "success"}
    
    async def handle_reconnect(self, websocket, data: dict) -> dict:
        """Oyuncu yeniden bağlanıyor"""
        room_code = data.get("room_code", "").upper()
        player_id = data.get("player_id")
        reconnect_token = data.get("reconnect_token")
        
        if room_code not in self.rooms:
            return {"type": "error", "message": "Oda bulunamadı veya süresi dolmuş"}
        
        room = self.rooms[room_code]
        
        if player_id not in room.players:
            return {"type": "error", "message": "Oyuncu bu odada bulunamadı"}
        
        player = room.players[player_id]
        
        # Token doğrulama
        if player.reconnect_token != reconnect_token:
            return {"type": "error", "message": "Geçersiz yeniden bağlanma tokeni"}
        
        # Oyuncuyu yeniden bağla
        player.websocket = websocket
        player.connected = True
        player.last_activity = datetime.now().isoformat()
        player.disconnect_time = ""
        
        self.connections[player_id] = websocket
        self.player_room_map[player_id] = room_code
        
        print(f"[{datetime.now()}] {player.name} yeniden bağlandı: {room_code}")
        
        # Diğer oyunculara bildir
        await self.broadcast_to_room(room_code, {
            "type": "player_reconnected",
            "player": player.to_dict(),
            "room": room.to_dict()
        }, exclude_id=player_id)
        
        return {
            "type": "reconnected",
            "success": True,
            "player_id": player_id,
            "room": room.to_dict()
        }
    
    def save_room_to_file(self, room_code: str) -> bool:
        """Odayı dosyaya kaydet"""
        import os
        
        if room_code not in self.rooms:
            return False
        
        room = self.rooms[room_code]
        
        # Kayıt verisi oluştur
        save_data = {
            "code": room.code,
            "host_id": room.host_id,
            "max_players": room.max_players,
            "game_started": room.game_started,
            "current_turn": room.current_turn,
            "current_player_id": room.current_player_id,
            "game_state": room.game_state,
            "saved_at": datetime.now().isoformat(),
            "players": {}
        }
        
        # Oyuncuları kaydet
        for pid, player in room.players.items():
            save_data["players"][pid] = {
                "id": player.id,
                "name": player.name,
                "province": player.province,
                "ready": player.ready,
                "reconnect_token": player.reconnect_token,
                "game_state": player.game_state
            }
        
        # Kayıt dizini oluştur
        save_dir = os.path.join(os.path.dirname(__file__), "saved_rooms")
        os.makedirs(save_dir, exist_ok=True)
        
        save_path = os.path.join(save_dir, f"{room_code}.json")
        
        try:
            with open(save_path, "w", encoding="utf-8") as f:
                json.dump(save_data, f, ensure_ascii=False, indent=2)
            print(f"[{datetime.now()}] Oda kaydedildi: {room_code}")
            return True
        except Exception as e:
            print(f"[{datetime.now()}] Oda kaydetme hatası: {e}")
            return False
    
    def load_room_from_file(self, room_code: str) -> bool:
        """Odayı dosyadan yükle"""
        import os
        
        save_path = os.path.join(os.path.dirname(__file__), "saved_rooms", f"{room_code}.json")
        
        if not os.path.exists(save_path):
            return False
        
        try:
            with open(save_path, "r", encoding="utf-8") as f:
                save_data = json.load(f)
            
            # Oyuncuları oluştur
            players = {}
            for pid, pdata in save_data["players"].items():
                player = Player(
                    id=pdata["id"],
                    name=pdata["name"],
                    province=pdata["province"],
                    ready=pdata["ready"],
                    connected=False,  # Yeniden bağlanmayı bekle
                    reconnect_token=pdata["reconnect_token"],
                    game_state=pdata["game_state"]
                )
                players[pid] = player
            
            # Odayı oluştur
            room = GameRoom(
                code=save_data["code"],
                host_id=save_data["host_id"],
                players=players,
                max_players=save_data["max_players"],
                game_started=save_data["game_started"],
                current_turn=save_data["current_turn"],
                current_player_id=save_data["current_player_id"],
                game_state=save_data["game_state"]
            )
            
            self.rooms[room_code] = room
            
            print(f"[{datetime.now()}] Oda yüklendi: {room_code}")
            return True
            
        except Exception as e:
            print(f"[{datetime.now()}] Oda yükleme hatası: {e}")
            return False
    
    async def handle_save_room(self, websocket, data: dict) -> dict:
        """Odayı kaydet (sadece host)"""
        player_id = data.get("player_id")
        
        if player_id not in self.player_room_map:
            return {"type": "error", "message": "Oyuncu bulunamadı"}
        
        room_code = self.player_room_map[player_id]
        room = self.rooms[room_code]
        
        # Sadece host kaydedebilir
        if room.host_id != player_id:
            return {"type": "error", "message": "Sadece host odayı kaydedebilir"}
        
        if self.save_room_to_file(room_code):
            # Herkese bildir
            await self.broadcast_to_room(room_code, {
                "type": "room_saved",
                "room_code": room_code,
                "message": f"Oda kaydedildi: {room_code}"
            })
            return {"type": "success", "message": f"Oda kaydedildi: {room_code}"}
        else:
            return {"type": "error", "message": "Oda kaydedilemedi"}
    
    async def handle_load_room(self, websocket, data: dict) -> dict:
        """Kaydedilmiş odayı yükle"""
        room_code = data.get("room_code", "").upper()
        player_name = data.get("player_name", "Anonim")
        
        if room_code in self.rooms:
            return {"type": "error", "message": "Bu oda zaten aktif"}
        
        if not self.load_room_from_file(room_code):
            return {"type": "error", "message": "Kaydedilmiş oda bulunamadı"}
        
        return {
            "type": "room_loaded",
            "success": True,
            "room_code": room_code,
            "room": self.rooms[room_code].to_dict(),
            "message": f"Oda yüklendi: {room_code}. Oyuncular yeniden bağlanabilir."
        }
    
    async def handle_disconnect(self, player_id: str):
        """Oyuncu bağlantısı koptuğunda"""
        if player_id not in self.player_room_map:
            return
        
        room_code = self.player_room_map[player_id]
        if room_code not in self.rooms:
            return
        
        room = self.rooms[room_code]
        if player_id not in room.players:
            return
        
        player = room.players[player_id]
        player.connected = False
        player.websocket = None
        
        print(f"[{datetime.now()}] {player.name} bağlantısı koptu")
        
        # Diğerlerine bildir
        await self.broadcast_to_room(room_code, {
            "type": "player_disconnected",
            "player": player.to_dict(),
            "room": room.to_dict()
        })
        
        # Eğer herkes çıktıysa odayı sil
        if all(not p.connected for p in room.players.values()):
            del self.rooms[room_code]
            print(f"[{datetime.now()}] Oda silindi: {room_code}")
    
    async def handler(self, websocket):
        """Ana WebSocket handler"""
        player_id = None
        
        try:
            async for message in websocket:
                try:
                    data = json.loads(message)
                    action = data.get("action", "")
                    
                    if action == "create_room":
                        response = await self.handle_create_room(websocket, data)
                        player_id = response.get("player_id")
                    
                    elif action == "join_room":
                        response = await self.handle_join_room(websocket, data)
                        player_id = response.get("player_id")
                    
                    elif action == "select_province":
                        response = await self.handle_select_province(websocket, data)
                    
                    elif action == "ready":
                        response = await self.handle_ready(websocket, data)
                    
                    elif action == "start_game":
                        response = await self.handle_start_game(websocket, data)
                    
                    elif action == "end_turn":
                        response = await self.handle_end_turn(websocket, data)
                    
                    elif action == "diplomacy":
                        response = await self.handle_diplomacy_action(websocket, data)
                    
                    elif action == "chat":
                        response = await self.handle_chat(websocket, data)
                    
                    elif action == "update_state":
                        response = await self.handle_update_state(websocket, data)
                    
                    elif action == "reconnect":
                        response = await self.handle_reconnect(websocket, data)
                        if response.get("success"):
                            player_id = response.get("player_id")
                    
                    elif action == "save_room":
                        response = await self.handle_save_room(websocket, data)
                    
                    elif action == "load_room":
                        response = await self.handle_load_room(websocket, data)
                    
                    elif action == "ping":
                        response = {"type": "pong"}
                    
                    else:
                        response = {"type": "error", "message": f"Bilinmeyen aksiyon: {action}"}
                    
                    await websocket.send(json.dumps(response))
                    
                except json.JSONDecodeError:
                    await websocket.send(json.dumps({"type": "error", "message": "Geçersiz JSON"}))
                    
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            if player_id:
                await self.handle_disconnect(player_id)
                if player_id in self.connections:
                    del self.connections[player_id]
                if player_id in self.player_room_map:
                    del self.player_room_map[player_id]
    
    async def start(self):
        """Sunucuyu başlat"""
        print(f"""
╔════════════════════════════════════════════════════════════╗
║     OSMANLI EYALET YÖNETİM SİMÜLASYONU - SUNUCU           ║
╠════════════════════════════════════════════════════════════╣
║  Host: {self.host}                                         
║  Port: {self.port}                                         
║  Başlatıldı: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
╠════════════════════════════════════════════════════════════╣
║  Oyuncular ws://{self.host}:{self.port} adresine bağlanmalı
╚════════════════════════════════════════════════════════════╝
        """)
        
        async with serve(self.handler, self.host, self.port):
            await asyncio.Future()  # Sonsuza kadar çalış


def main():
    parser = argparse.ArgumentParser(description='Osmanlı Oyunu Sunucusu')
    parser.add_argument('--host', default='0.0.0.0', help='Sunucu adresi')
    parser.add_argument('--port', type=int, default=8765, help='Port numarası')
    args = parser.parse_args()
    
    server = GameServer(host=args.host, port=args.port)
    asyncio.run(server.start())


if __name__ == "__main__":
    main()
