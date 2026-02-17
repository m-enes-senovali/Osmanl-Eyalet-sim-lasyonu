# -*- coding: utf-8 -*-
"""
Osmanlı Eyalet Yönetim Simülasyonu - HTTP Polling Sunucusu
REST API tabanlı çok oyunculu sunucu (Güçlendirilmiş)

Kullanım:
    pip install flask flask-cors
    python server_http.py --port 5000
    python server_http.py --port 5000 --production   (waitress ile)
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import random
import string
import uuid
from datetime import datetime, timedelta
import argparse
import json
import time
import threading
import atexit
from collections import defaultdict

app = Flask(__name__)
CORS(app)  # Cross-origin isteklere izin ver

# ========== YAPILANDIRMA ==========

PLAYER_TIMEOUT_SECONDS = 60       # Disconnected sayılma süresi
TURN_TIMEOUT_SECONDS = 30         # Tur zaman aşımı
MAX_PLAYERS_PER_ROOM = 10
MAX_NAME_LENGTH = 30
MAX_CHAT_LENGTH = 200
MAX_CHAT_HISTORY = 50
RATE_LIMIT_PER_MINUTE = 120       # IP başına dakikada max istek
ROOM_CREATE_LIMIT_PER_MINUTE = 5  # Oda oluşturma sınırı

# ========== VERİ DEPOSU ==========

try:
    from server_db import RoomDatabase
    _db = RoomDatabase()
    rooms = _db.load_rooms()
    if rooms:
        print(f"[DB] {len(rooms)} oda veritabanından yüklendi")
    else:
        rooms = {}
except Exception as e:
    print(f"[DB] Veritabanı yüklenemedi: {e}")
    _db = None
    rooms = {}


def _save_room(code: str):
    """Odayı veritabanına kaydet"""
    if _db and code in rooms:
        try:
            _db.save_room(code, rooms[code])
        except Exception:
            pass


def _delete_room_db(code: str):
    """Odayı veritabanından sil"""
    if _db:
        try:
            _db.delete_room(code)
        except Exception:
            pass


def _save_all_rooms():
    """Tüm odaları kaydet (kapanırken)"""
    if _db and rooms:
        try:
            _db.save_all(rooms)
            print(f"[DB] {len(rooms)} oda kaydedildi")
        except Exception as e:
            print(f"[DB] Kaydetme hatası: {e}")


atexit.register(_save_all_rooms)


@app.after_request
def auto_save_room(response):
    """POST isteklerinden sonra ilgili odayı otomatik kaydet"""
    if request.method == 'POST' and response.status_code == 200:
        # URL'den oda kodunu çıkar
        path = request.path
        if path.startswith('/room/') and '/' in path[6:]:
            code = path.split('/')[2]
            if code in rooms:
                _save_room(code)
        elif path == '/room/create':
            # Yeni oda oluşturuldu — response'dan kodu al
            try:
                data = response.get_json()
                if data and data.get('room_code'):
                    _save_room(data['room_code'])
            except Exception:
                pass
    return response

# ========== RATE LIMITING ==========

_rate_counters = defaultdict(list)   # IP -> [timestamp, ...]
_create_counters = defaultdict(list)  # IP -> [timestamp, ...]


def _check_rate_limit(ip: str, limit: int = RATE_LIMIT_PER_MINUTE,
                      counter: dict = None) -> bool:
    """IP bazlı rate limit kontrolü. True=izin ver, False=engelle."""
    if counter is None:
        counter = _rate_counters
    
    now = time.time()
    cutoff = now - 60
    
    # Eski kayıtları temizle
    counter[ip] = [t for t in counter[ip] if t > cutoff]
    
    if len(counter[ip]) >= limit:
        return False
    
    counter[ip].append(now)
    return True


@app.before_request
def rate_limit_check():
    """Her istek öncesi rate limit kontrolü"""
    ip = request.remote_addr or "unknown"
    
    if not _check_rate_limit(ip):
        return jsonify({
            'success': False,
            'error': 'Çok fazla istek. Lütfen bekleyin.'
        }), 429


# ========== EYALET LİSTESİ ==========

try:
    from game.data.territories import TERRITORIES, TerritoryType
    PROVINCES = [
        t.name for t in TERRITORIES.values()
        if t.territory_type in [
            TerritoryType.OSMANLI_EYALET,
            TerritoryType.OSMANLI_SANCAK,
            TerritoryType.VASAL
        ]
    ]
except ImportError:
    PROVINCES = [
        "Aydın Sancağı", "Selanik Sancağı", "Trabzon Eyaleti",
        "Rum Eyaleti", "Karaman Eyaleti", "Halep Eyaleti"
    ]

VALID_PROVINCES = set(PROVINCES)

# ========== YARDIMCI FONKSİYONLAR ==========


def generate_room_code():
    """6 karakterlik oda kodu oluştur"""
    while True:
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        if code not in rooms:
            return code


def log(message):
    """Sunucu logu"""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")


def sanitize_name(name: str) -> str:
    """İsim temizleme ve sınırlama"""
    if not name or not isinstance(name, str):
        return "Anonim"
    name = name.strip()[:MAX_NAME_LENGTH]
    # Temel XSS koruması
    name = name.replace('<', '').replace('>', '').replace('&', '')
    return name if name else "Anonim"


def sanitize_message(message: str) -> str:
    """Mesaj temizleme"""
    if not message or not isinstance(message, str):
        return ""
    message = message.strip()[:MAX_CHAT_LENGTH]
    message = message.replace('<', '&lt;').replace('>', '&gt;')
    return message


def validate_required_fields(data: dict, fields: list) -> str:
    """Gerekli alanları kontrol et. Hata varsa mesaj döndür, yoksa None."""
    if not data or not isinstance(data, dict):
        return "Geçersiz istek verisi"
    for field in fields:
        if field not in data or data[field] is None:
            return f"Eksik alan: {field}"
    return None


def now_iso():
    """ISO format şimdiki zaman"""
    return datetime.now().isoformat()


# ========== OYUNCU TEMİZLEME & TUR TIMEOUT ==========


def cleanup_stale_players(room: dict):
    """Disconnected oyuncuları tespit et ve tur kilitlermesini önle"""
    now = datetime.now()
    
    for pid, player in room['players'].items():
        try:
            last_seen = datetime.fromisoformat(player.get('last_seen', now_iso()))
            delta = (now - last_seen).total_seconds()
            
            if delta > PLAYER_TIMEOUT_SECONDS:
                if player.get('connected', True):
                    player['connected'] = False
                    log(f"[{room['code']}] {player['name']} zaman aşımı (disconnected)")
        except (ValueError, TypeError):
            pass
    
    # Tur kilitlermesi kontrolü — sırası gelen oyuncu disconnected ise tur geçir
    if room.get('game_started') and room.get('current_player_id'):
        current = room['players'].get(room['current_player_id'])
        if current and not current.get('connected', True):
            _auto_advance_turn(room, reason="disconnected")


def check_turn_timeout(room: dict):
    """Tur zaman aşımı kontrolü (30 saniye)"""
    if not room.get('game_started') or not room.get('turn_started_at'):
        return
    
    try:
        turn_start = datetime.fromisoformat(room['turn_started_at'])
        elapsed = (datetime.now() - turn_start).total_seconds()
        
        if elapsed > TURN_TIMEOUT_SECONDS:
            _auto_advance_turn(room, reason="timeout")
    except (ValueError, TypeError):
        pass


def _auto_advance_turn(room: dict, reason: str = "auto"):
    """Otomatik tur geçişi"""
    old_player_id = room.get('current_player_id')
    if not old_player_id:
        return
    
    player_ids = list(room['players'].keys())
    if not player_ids:
        return
    
    try:
        current_index = player_ids.index(old_player_id)
    except ValueError:
        current_index = 0
    
    # Bağlı bir sonraki oyuncuyu bul (sonsuz döngüyü önle)
    next_player_id = None
    for i in range(1, len(player_ids) + 1):
        candidate_index = (current_index + i) % len(player_ids)
        candidate_id = player_ids[candidate_index]
        candidate = room['players'].get(candidate_id)
        
        if candidate and candidate.get('connected', True):
            next_player_id = candidate_id
            break
        
        # Tüm tur döndüyse tur sayısını artır
        if candidate_index == 0:
            room['current_turn'] = room.get('current_turn', 1) + 1
    
    if next_player_id:
        # Eğer yeni index birinciyse (yani yeni tur) tur sayısını artır
        new_index = player_ids.index(next_player_id)
        if new_index <= current_index and next_player_id != old_player_id:
            room['current_turn'] = room.get('current_turn', 1) + 1
        
        room['current_player_id'] = next_player_id
        room['turn_started_at'] = now_iso()
        
        old_name = room['players'].get(old_player_id, {}).get('name', '?')
        new_name = room['players'].get(next_player_id, {}).get('name', '?')
        log(f"[{room['code']}] Otomatik tur geçişi ({reason}): {old_name} -> {new_name}")


def migrate_host(room: dict):
    """Host ayrıldıysa yeni host ata"""
    host_id = room.get('host_id')
    
    # Host hala odada mı?
    if host_id in room['players']:
        host = room['players'][host_id]
        if host.get('connected', True):
            return  # Host bağlı, geçiş gerekmez
    
    # Bağlı ilk oyuncuyu yeni host yap
    for pid, player in room['players'].items():
        if player.get('connected', True):
            room['host_id'] = pid
            log(f"[{room['code']}] Yeni host: {player['name']}")
            return
    
    # Hiç bağlı oyuncu yok — oda yetim
    log(f"[{room['code']}] Tüm oyuncular disconnected")


# ========== ODA YÖNETİMİ ==========

@app.route('/room/create', methods=['POST'])
def create_room():
    """Yeni oda oluştur"""
    # Rate limit — oda oluşturma
    ip = request.remote_addr or "unknown"
    if not _check_rate_limit(ip, ROOM_CREATE_LIMIT_PER_MINUTE, _create_counters):
        return jsonify({
            'success': False,
            'error': 'Çok fazla oda oluşturma denemesi. Lütfen bekleyin.'
        }), 429
    
    data = request.json
    err = validate_required_fields(data, ['player_id'])
    if err:
        return jsonify({'success': False, 'error': err}), 400
    
    player_id = data['player_id']
    player_name = sanitize_name(data.get('name', 'Anonim'))
    
    room_code = generate_room_code()
    
    rooms[room_code] = {
        'code': room_code,
        'host_id': player_id,
        'players': {
            player_id: {
                'id': player_id,
                'name': player_name,
                'province': '',
                'connected': True,
                'last_seen': now_iso()
            }
        },
        'game_started': False,
        'current_turn': 0,
        'current_player_id': None,
        'turn_started_at': None,
        'created_at': now_iso(),
        
        # Diplomasi sistemi
        'diplomacy': {
            'alliances': [],
            'trade_deals': [],
            'wars': [],
            'pending_proposals': []
        },
        
        # Oyuncu detaylı durumları
        'player_states': {}
    }
    
    log(f"Oda oluşturuldu: {room_code} - Host: {player_name} ({player_id})")
    
    return jsonify({
        'success': True,
        'room_code': room_code,
        'player_id': player_id,
        'room': rooms[room_code]
    })


@app.route('/room/<code>/join', methods=['POST'])
def join_room(code):
    """Odaya katıl"""
    if code not in rooms:
        return jsonify({'success': False, 'error': 'Oda bulunamadı'}), 404
    
    data = request.json
    err = validate_required_fields(data, ['player_id'])
    if err:
        return jsonify({'success': False, 'error': err}), 400
    
    player_id = data['player_id']
    player_name = sanitize_name(data.get('name', 'Anonim'))
    
    room = rooms[code]
    
    if room['game_started']:
        # Yeniden bağlanma kontrolü
        if player_id in room['players']:
            room['players'][player_id]['connected'] = True
            room['players'][player_id]['last_seen'] = now_iso()
            log(f"[{code}] Yeniden bağlandı: {player_name}")
            return jsonify({
                'success': True,
                'player_id': player_id,
                'room': room,
                'reconnected': True
            })
        return jsonify({'success': False, 'error': 'Oyun zaten başlamış'}), 400
    
    if len(room['players']) >= MAX_PLAYERS_PER_ROOM:
        return jsonify({'success': False, 'error': f'Oda dolu (max {MAX_PLAYERS_PER_ROOM} oyuncu)'}), 400
    
    room['players'][player_id] = {
        'id': player_id,
        'name': player_name,
        'province': '',
        'connected': True,
        'last_seen': now_iso()
    }
    
    log(f"[{code}] Oyuncu katıldı: {player_name} ({player_id})")
    
    return jsonify({
        'success': True,
        'player_id': player_id,
        'room': room
    })


@app.route('/room/<code>', methods=['GET'])
def get_room(code):
    """Oda durumunu al (POLLING) — temizlik ve timeout kontrolleri dahil"""
    if code not in rooms:
        return jsonify({'success': False, 'error': 'Oda bulunamadı'}), 404
    
    room = rooms[code]
    
    # İsteği yapan oyuncuyu güncelle
    player_id = request.args.get('player_id')
    if player_id and player_id in room['players']:
        room['players'][player_id]['last_seen'] = now_iso()
        room['players'][player_id]['connected'] = True
    
    # Bakım görevleri (her polling'de çalışır)
    cleanup_stale_players(room)
    check_turn_timeout(room)
    migrate_host(room)
    
    return jsonify({
        'success': True,
        'room': room
    })


@app.route('/room/<code>/select', methods=['POST'])
def select_province(code):
    """Eyalet seç"""
    if code not in rooms:
        return jsonify({'success': False, 'error': 'Oda bulunamadı'}), 404
    
    data = request.json
    err = validate_required_fields(data, ['player_id', 'province'])
    if err:
        return jsonify({'success': False, 'error': err}), 400
    
    player_id = data['player_id']
    province = data['province']
    
    room = rooms[code]
    
    if player_id not in room['players']:
        return jsonify({'success': False, 'error': 'Oyuncu bulunamadı'}), 404
    
    # Eyalet geçerli mi?
    if province not in VALID_PROVINCES:
        return jsonify({'success': False, 'error': 'Geçersiz eyalet adı'}), 400
    
    # Eyalet başkası tarafından seçilmiş mi?
    for pid, player in room['players'].items():
        if player['province'] == province and pid != player_id:
            return jsonify({'success': False, 'error': 'Bu eyalet zaten seçilmiş'}), 400
    
    room['players'][player_id]['province'] = province
    
    log(f"[{code}] {room['players'][player_id]['name']} eyalet seçti: {province}")
    
    return jsonify({
        'success': True,
        'room': room
    })


@app.route('/room/<code>/start', methods=['POST'])
def start_game(code):
    """Oyunu başlat"""
    if code not in rooms:
        return jsonify({'success': False, 'error': 'Oda bulunamadı'}), 404
    
    data = request.json
    err = validate_required_fields(data, ['player_id'])
    if err:
        return jsonify({'success': False, 'error': err}), 400
    
    player_id = data['player_id']
    room = rooms[code]
    
    if room['host_id'] != player_id:
        return jsonify({'success': False, 'error': 'Sadece host başlatabilir'}), 403
    
    if len(room['players']) < 2:
        return jsonify({'success': False, 'error': 'En az 2 oyuncu gerekli'}), 400
    
    # Herkes eyalet seçmiş mi?
    for player in room['players'].values():
        if not player['province']:
            return jsonify({
                'success': False,
                'error': f"{player['name']} eyalet seçmedi"
            }), 400
    
    room['game_started'] = True
    room['current_turn'] = 1
    room['current_player_id'] = list(room['players'].keys())[0]
    room['turn_started_at'] = now_iso()
    
    log(f"[{code}] Oyun başladı!")
    
    return jsonify({
        'success': True,
        'room': room
    })


@app.route('/room/<code>/end_turn', methods=['POST'])
def end_turn(code):
    """Turu bitir"""
    if code not in rooms:
        return jsonify({'success': False, 'error': 'Oda bulunamadı'}), 404
    
    data = request.json
    err = validate_required_fields(data, ['player_id'])
    if err:
        return jsonify({'success': False, 'error': err}), 400
    
    player_id = data['player_id']
    player_state = data.get('state', {})
    
    room = rooms[code]
    
    if room['current_player_id'] != player_id:
        return jsonify({'success': False, 'error': 'Sıra sizde değil'}), 400
    
    # Oyuncu durumunu kaydet
    room['players'][player_id]['state'] = player_state
    
    # Sıradaki oyuncuya geç
    player_ids = list(room['players'].keys())
    current_index = player_ids.index(player_id)
    next_index = (current_index + 1) % len(player_ids)
    
    room['current_player_id'] = player_ids[next_index]
    room['turn_started_at'] = now_iso()
    
    # İlk oyuncuya geri döndüyse tur sayısını artır
    if next_index == 0:
        room['current_turn'] += 1
    
    log(f"[{code}] Tur geçildi: {room['players'][player_id]['name']} -> "
        f"{room['players'][room['current_player_id']]['name']}")
    
    return jsonify({
        'success': True,
        'room': room
    })


@app.route('/room/<code>/chat', methods=['POST'])
def send_chat(code):
    """Sohbet mesajı gönder"""
    if code not in rooms:
        return jsonify({'success': False, 'error': 'Oda bulunamadı'}), 404
    
    data = request.json
    err = validate_required_fields(data, ['player_id'])
    if err:
        return jsonify({'success': False, 'error': err}), 400
    
    player_id = data['player_id']
    message = sanitize_message(data.get('message', ''))
    
    if not message:
        return jsonify({'success': False, 'error': 'Boş mesaj gönderilemez'}), 400
    
    room = rooms[code]
    
    if 'chat' not in room:
        room['chat'] = []
    
    room['chat'].append({
        'player_id': player_id,
        'player_name': room['players'].get(player_id, {}).get('name', 'Anonim'),
        'message': message,
        'time': now_iso()
    })
    
    # Son mesajları tut
    room['chat'] = room['chat'][-MAX_CHAT_HISTORY:]
    
    return jsonify({'success': True})


@app.route('/room/<code>/leave', methods=['POST'])
def leave_room(code):
    """Odadan ayrıl"""
    if code not in rooms:
        return jsonify({'success': False, 'error': 'Oda bulunamadı'}), 404
    
    data = request.json
    err = validate_required_fields(data, ['player_id'])
    if err:
        return jsonify({'success': False, 'error': err}), 400
    
    player_id = data['player_id']
    room = rooms[code]
    
    if player_id in room['players']:
        player_name = room['players'][player_id]['name']
        was_host = room['host_id'] == player_id
        was_current = room.get('current_player_id') == player_id
        
        del room['players'][player_id]
        log(f"[{code}] {player_name} ayrıldı")
        
        # Oda boşaldıysa sil
        if not room['players']:
            del rooms[code]
            _delete_room_db(code)
            log(f"[{code}] Oda silindi (boş)")
            return jsonify({'success': True})
        
        # Host ayrıldıysa yeni host ata
        if was_host:
            migrate_host(room)
        
        # Sırası olan oyuncu ayrıldıysa tur geçir
        if was_current and room.get('game_started'):
            _auto_advance_turn(room, reason="player_left")
    
    return jsonify({'success': True})


# ========== DİPLOMASİ SİSTEMİ ==========

@app.route('/room/<code>/diplomacy/propose', methods=['POST'])
def propose_diplomacy(code):
    """İttifak, ticaret veya barış teklifi"""
    if code not in rooms:
        return jsonify({'success': False, 'error': 'Oda bulunamadı'}), 404
    
    data = request.json
    err = validate_required_fields(data, ['from_player_id', 'to_player_id', 'type'])
    if err:
        return jsonify({'success': False, 'error': err}), 400
    
    from_player = data['from_player_id']
    to_player = data['to_player_id']
    proposal_type = data['type']
    terms = data.get('terms', {})
    
    # Tip kontrolü
    if proposal_type not in ('alliance', 'trade', 'peace'):
        return jsonify({'success': False, 'error': 'Geçersiz teklif tipi'}), 400
    
    room = rooms[code]
    
    if from_player not in room['players'] or to_player not in room['players']:
        return jsonify({'success': False, 'error': 'Oyuncu bulunamadı'}), 404
    
    if from_player == to_player:
        return jsonify({'success': False, 'error': 'Kendinize teklif gönderemezsiniz'}), 400
    
    proposal_id = str(uuid.uuid4())[:8]
    proposal = {
        'id': proposal_id,
        'type': proposal_type,
        'from_player_id': from_player,
        'to_player_id': to_player,
        'from_player': room['players'][from_player],
        'terms': terms if isinstance(terms, dict) else {},
        'created_at': now_iso()
    }
    
    room['diplomacy']['pending_proposals'].append(proposal)
    
    from_name = room['players'][from_player]['name']
    to_name = room['players'][to_player]['name']
    log(f"[{code}] {from_name} -> {to_name}: {proposal_type} teklifi")
    
    return jsonify({
        'success': True,
        'proposal_id': proposal_id,
        'room': room
    })


@app.route('/room/<code>/diplomacy/respond', methods=['POST'])
def respond_diplomacy(code):
    """Teklifi kabul veya reddet"""
    if code not in rooms:
        return jsonify({'success': False, 'error': 'Oda bulunamadı'}), 404
    
    data = request.json
    err = validate_required_fields(data, ['player_id', 'proposal_id'])
    if err:
        return jsonify({'success': False, 'error': err}), 400
    
    player_id = data['player_id']
    proposal_id = data['proposal_id']
    accept = bool(data.get('accept', False))
    
    room = rooms[code]
    
    # Teklifi bul
    proposal = None
    for p in room['diplomacy']['pending_proposals']:
        if p['id'] == proposal_id and p['to_player_id'] == player_id:
            proposal = p
            break
    
    if not proposal:
        return jsonify({'success': False, 'error': 'Teklif bulunamadı'}), 404
    
    # Tekliften kaldır
    room['diplomacy']['pending_proposals'].remove(proposal)
    
    result_message = ""
    
    if accept:
        if proposal['type'] == 'alliance':
            room['diplomacy']['alliances'].append({
                'players': [proposal['from_player_id'], proposal['to_player_id']],
                'formed_at': now_iso()
            })
            result_message = "İttifak kuruldu!"
            
        elif proposal['type'] == 'trade':
            gold = 100
            if isinstance(proposal.get('terms'), dict):
                gold = min(max(int(proposal['terms'].get('gold', 100)), 0), 10000)
            room['diplomacy']['trade_deals'].append({
                'from': proposal['from_player_id'],
                'to': proposal['to_player_id'],
                'gold_per_turn': gold,
                'formed_at': now_iso()
            })
            result_message = "Ticaret anlaşması yapıldı!"
            
        elif proposal['type'] == 'peace':
            wars = room['diplomacy']['wars']
            for war in wars[:]:
                if set([war['attacker'], war['defender']]) == \
                   set([proposal['from_player_id'], proposal['to_player_id']]):
                    wars.remove(war)
            result_message = "Barış yapıldı!"
    else:
        result_message = "Teklif reddedildi."
    
    from_name = room['players'].get(proposal['from_player_id'], {}).get('name', '?')
    to_name = room['players'].get(proposal['to_player_id'], {}).get('name', '?')
    log(f"[{code}] {to_name} {proposal['type']} teklifini "
        f"{'kabul etti' if accept else 'reddetti'}")
    
    return jsonify({
        'success': True,
        'accepted': accept,
        'message': result_message,
        'room': room
    })


@app.route('/room/<code>/diplomacy/war', methods=['POST'])
def declare_war(code):
    """Savaş ilan et"""
    if code not in rooms:
        return jsonify({'success': False, 'error': 'Oda bulunamadı'}), 404
    
    data = request.json
    err = validate_required_fields(data, ['attacker_id', 'defender_id'])
    if err:
        return jsonify({'success': False, 'error': err}), 400
    
    attacker_id = data['attacker_id']
    defender_id = data['defender_id']
    
    room = rooms[code]
    
    if attacker_id not in room['players'] or defender_id not in room['players']:
        return jsonify({'success': False, 'error': 'Oyuncu bulunamadı'}), 404
    
    if attacker_id == defender_id:
        return jsonify({'success': False, 'error': 'Kendinize savaş ilan edemezsiniz'}), 400
    
    # Zaten savaşta mı?
    for war in room['diplomacy']['wars']:
        if set([war['attacker'], war['defender']]) == set([attacker_id, defender_id]):
            return jsonify({'success': False, 'error': 'Zaten savaştasınız'}), 400
    
    # İttifağı iptal et
    alliances = room['diplomacy']['alliances']
    for alliance in alliances[:]:
        if set(alliance['players']) == set([attacker_id, defender_id]):
            alliances.remove(alliance)
    
    room['diplomacy']['wars'].append({
        'attacker': attacker_id,
        'defender': defender_id,
        'started_turn': room['current_turn']
    })
    
    attacker_name = room['players'][attacker_id]['name']
    defender_name = room['players'][defender_id]['name']
    log(f"[{code}] SAVAŞ! {attacker_name} -> {defender_name}")
    
    return jsonify({
        'success': True,
        'message': f"{attacker_name} {defender_name}'e savaş ilan etti!",
        'room': room
    })


@app.route('/room/<code>/attack', methods=['POST'])
def attack_player(code):
    """Saldırı yap ve sonucu hesapla"""
    if code not in rooms:
        return jsonify({'success': False, 'error': 'Oda bulunamadı'}), 404
    
    data = request.json
    err = validate_required_fields(data, ['attacker_id', 'defender_id'])
    if err:
        return jsonify({'success': False, 'error': err}), 400
    
    attacker_id = data['attacker_id']
    defender_id = data['defender_id']
    attacker_power = max(int(data.get('attacker_power', 100)), 1)
    
    room = rooms[code]
    
    # Savaşta mı kontrol et
    at_war = False
    for war in room['diplomacy']['wars']:
        if set([war['attacker'], war['defender']]) == set([attacker_id, defender_id]):
            at_war = True
            break
    
    if not at_war:
        return jsonify({'success': False, 'error': 'Savaş ilan etmelisiniz'}), 400
    
    # Savunmacı gücünü al
    defender_state = room.get('player_states', {}).get(defender_id, {})
    defender_power = max(int(defender_state.get('military_power', 100)), 1)
    
    # Savaş sonucunu hesapla
    ratio = attacker_power / defender_power
    luck = random.uniform(0.8, 1.2)
    effective_ratio = ratio * luck
    
    if effective_ratio > 1.5:
        result = 'decisive_victory'
        message = "Ezici zafer! Düşman ordusunun %50'si yok edildi."
        attacker_losses = int(attacker_power * 0.1)
        defender_losses = int(defender_power * 0.5)
        gold_plunder = 2000
    elif effective_ratio > 1.2:
        result = 'victory'
        message = "Zafer! Düşman ordusunun %30'u yok edildi."
        attacker_losses = int(attacker_power * 0.15)
        defender_losses = int(defender_power * 0.3)
        gold_plunder = 1000
    elif effective_ratio > 0.8:
        result = 'draw'
        message = 'Beraberlik. Her iki taraf da kayıp verdi.'
        attacker_losses = int(attacker_power * 0.2)
        defender_losses = int(defender_power * 0.2)
        gold_plunder = 0
    else:
        result = 'defeat'
        message = "Yenilgi! Ordunuzun %30'u kaybedildi."
        attacker_losses = int(attacker_power * 0.3)
        defender_losses = int(defender_power * 0.1)
        gold_plunder = 0
    
    attacker_name = room['players'][attacker_id]['name']
    defender_name = room['players'][defender_id]['name']
    log(f"[{code}] SAVAŞ SONUCU: {attacker_name} vs {defender_name} = {result}")
    
    return jsonify({
        'success': True,
        'result': result,
        'message': message,
        'attacker_losses': attacker_losses,
        'defender_losses': defender_losses,
        'gold_plunder': gold_plunder,
        'room': room
    })


@app.route('/room/<code>/sync_state', methods=['POST'])
def sync_player_state(code):
    """Oyuncu durumunu senkronize et (genişletilmiş)"""
    if code not in rooms:
        return jsonify({'success': False, 'error': 'Oda bulunamadı'}), 404
    
    data = request.json
    err = validate_required_fields(data, ['player_id', 'state'])
    if err:
        return jsonify({'success': False, 'error': err}), 400
    
    player_id = data['player_id']
    state = data.get('state', {})
    
    if not isinstance(state, dict):
        return jsonify({'success': False, 'error': 'Geçersiz state verisi'}), 400
    
    room = rooms[code]
    
    if player_id not in room['players']:
        return jsonify({'success': False, 'error': 'Oyuncu bulunamadı'}), 404
    
    # Genişletilmiş state (geriye dönük uyumlu)
    room['player_states'][player_id] = {
        # Temel
        'gold': int(state.get('gold', 0)),
        'military_power': int(state.get('military_power', 0)),
        'population': int(state.get('population', 0)),
        'happiness': int(state.get('happiness', 50)),
        'buildings': state.get('buildings', []),
        # Genişletilmiş alanlar
        'naval_power': int(state.get('naval_power', 0)),
        'guild_count': int(state.get('guild_count', 0)),
        'warfare_status': state.get('warfare_status', 'peace'),
        'loyalty': int(state.get('loyalty', 50)),
        'tax_income': int(state.get('tax_income', 0)),
        'total_soldiers': int(state.get('total_soldiers', 0)),
        'province_level': int(state.get('province_level', 1)),
        # Meta
        'updated_at': now_iso()
    }
    
    return jsonify({'success': True})


@app.route('/room/<code>/player/<player_id>/info', methods=['GET'])
def get_player_info(code, player_id):
    """Oyuncu bilgisini al"""
    if code not in rooms:
        return jsonify({'success': False, 'error': 'Oda bulunamadı'}), 404
    
    room = rooms[code]
    
    if player_id not in room['players']:
        return jsonify({'success': False, 'error': 'Oyuncu bulunamadı'}), 404
    
    player = room['players'][player_id]
    state = room.get('player_states', {}).get(player_id, {})
    
    return jsonify({
        'success': True,
        'player': player,
        'state': state
    })


@app.route('/provinces', methods=['GET'])
def get_provinces():
    """Eyalet listesini al"""
    return jsonify({'provinces': PROVINCES})


@app.route('/health', methods=['GET'])
def health_check():
    """Sunucu durumu (genişletilmiş)"""
    total_players = sum(len(r['players']) for r in rooms.values())
    active_games = sum(1 for r in rooms.values() if r.get('game_started'))
    
    return jsonify({
        'status': 'ok',
        'rooms': len(rooms),
        'total_players': total_players,
        'active_games': active_games,
        'time': now_iso(),
        'config': {
            'player_timeout': PLAYER_TIMEOUT_SECONDS,
            'turn_timeout': TURN_TIMEOUT_SECONDS,
            'max_players': MAX_PLAYERS_PER_ROOM,
            'rate_limit': RATE_LIMIT_PER_MINUTE
        }
    })


# ========== ANA FONKSİYON ==========

def main():
    parser = argparse.ArgumentParser(description='Osmanlı Oyunu HTTP Sunucusu')
    parser.add_argument('--host', default='0.0.0.0', help='Sunucu adresi')
    parser.add_argument('--port', type=int, default=5000, help='Port numarası')
    parser.add_argument('--production', action='store_true',
                        help='Production modu (waitress WSGI)')
    args = parser.parse_args()
    
    print(f"""
╔════════════════════════════════════════════════════════════════╗
║     OSMANLI EYALET YÖNETİM SİMÜLASYONU - HTTP SUNUCU          ║
╠════════════════════════════════════════════════════════════════╣
║  Host: {args.host:<15}                                        
║  Port: {args.port:<15}                                        
║  Mode: {'PRODUCTION (waitress)' if args.production else 'DEVELOPMENT (flask)' :<25}          
║  URL:  http://{args.host}:{args.port:<30}              
╠════════════════════════════════════════════════════════════════╣
║  Güvenlik:                                                     
║    Oyuncu timeout:  {PLAYER_TIMEOUT_SECONDS}sn                                      
║    Tur timeout:     {TURN_TIMEOUT_SECONDS}sn                                      
║    Rate limit:      {RATE_LIMIT_PER_MINUTE}/dk                                    
║    Max oyuncu/oda:  {MAX_PLAYERS_PER_ROOM}                                       
╠════════════════════════════════════════════════════════════════╣
║  Endpoints:                                                    
║    POST /room/create        - Oda oluştur                      
║    POST /room/<code>/join   - Odaya katıl                      
║    GET  /room/<code>        - Oda durumu (polling)             
║    POST /room/<code>/select - Eyalet seç                       
║    POST /room/<code>/start  - Oyunu başlat                     
║    POST /room/<code>/end_turn - Tur bitir                      
║    POST /room/<code>/chat   - Sohbet                           
║    POST /room/<code>/leave  - Odadan ayrıl                     
║    POST /room/<code>/diplomacy/propose  - Teklif               
║    POST /room/<code>/diplomacy/respond  - Yanıtla              
║    POST /room/<code>/diplomacy/war      - Savaş ilanı          
║    POST /room/<code>/attack             - Saldırı              
║    POST /room/<code>/sync_state         - Durum senkronize     
║    GET  /room/<code>/player/<id>/info   - Oyuncu bilgisi       
║    GET  /provinces          - Eyalet listesi                   
║    GET  /health             - Sunucu durumu                    
╚════════════════════════════════════════════════════════════════╝
    """)
    
    if args.production:
        try:
            from waitress import serve
            log("Production modu: waitress başlatılıyor...")
            serve(app, host=args.host, port=args.port, threads=4)
        except ImportError:
            log("UYARI: waitress bulunamadı! pip install waitress")
            log("Development modu ile başlatılıyor...")
            app.run(host=args.host, port=args.port, debug=False)
    else:
        app.run(host=args.host, port=args.port, debug=True)


if __name__ == "__main__":
    main()
