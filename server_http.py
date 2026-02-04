# -*- coding: utf-8 -*-
"""
Osmanlı Eyalet Yönetim Simülasyonu - HTTP Polling Sunucusu
Basit REST API tabanlı çok oyunculu sunucu

Kullanım:
    pip install flask flask-cors
    python server_http.py --port 5000
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import random
import string
import uuid
from datetime import datetime
import argparse
import json

app = Flask(__name__)
CORS(app)  # Cross-origin isteklere izin ver

# Bellek içi veri deposu
rooms = {}

# Eyalet listesi - territories.py'den dinamik olarak al
try:
    from game.data.territories import TERRITORIES, TerritoryType
    PROVINCES = [
        t.name for t in TERRITORIES.values() 
        if t.territory_type in [TerritoryType.OSMANLI_EYALET, TerritoryType.OSMANLI_SANCAK, TerritoryType.VASAL]
    ]
except ImportError:
    # Fallback - statik liste
    PROVINCES = [
        "Aydın Sancağı", "Selanik Sancağı", "Trabzon Eyaleti",
        "Rum Eyaleti", "Karaman Eyaleti", "Halep Eyaleti"
    ]

def generate_room_code():
    """6 karakterlik oda kodu oluştur"""
    while True:
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        if code not in rooms:
            return code

def log(message):
    """Sunucu logu"""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")


# ========== ODA YÖNETİMİ ==========

@app.route('/room/create', methods=['POST'])
def create_room():
    """Yeni oda oluştur"""
    data = request.json
    player_id = data.get('player_id', str(uuid.uuid4()))
    player_name = data.get('name', 'Anonim')
    
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
                'last_seen': datetime.now().isoformat()
            }
        },
        'game_started': False,
        'current_turn': 0,
        'current_player_id': None,
        'created_at': datetime.now().isoformat(),
        
        # Diplomasi sistemi
        'diplomacy': {
            'alliances': [],       # [(player1_id, player2_id), ...]
            'trade_deals': [],     # [{'from': id, 'to': id, 'gold_per_turn': 100}, ...]
            'wars': [],            # [{'attacker': id, 'defender': id, 'started_turn': 1}, ...]
            'pending_proposals': [] # [{'id': uuid, 'type': 'alliance'/'trade'/'peace', 'from': id, 'to': id, 'terms': {}}, ...]
        },
        
        # Oyuncu detaylı durumları (tur sonunda güncellenir)
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
    player_id = data.get('player_id', str(uuid.uuid4()))
    player_name = data.get('name', 'Anonim')
    
    room = rooms[code]
    
    if room['game_started']:
        return jsonify({'success': False, 'error': 'Oyun zaten başlamış'}), 400
    
    if len(room['players']) >= 10:
        return jsonify({'success': False, 'error': 'Oda dolu (max 10 oyuncu)'}), 400
    
    room['players'][player_id] = {
        'id': player_id,
        'name': player_name,
        'province': '',
        'connected': True,
        'last_seen': datetime.now().isoformat()
    }
    
    log(f"[{code}] Oyuncu katıldı: {player_name} ({player_id})")
    
    return jsonify({
        'success': True,
        'player_id': player_id,
        'room': room
    })


@app.route('/room/<code>', methods=['GET'])
def get_room(code):
    """Oda durumunu al (POLLING)"""
    if code not in rooms:
        return jsonify({'success': False, 'error': 'Oda bulunamadı'}), 404
    
    # İsteği yapan oyuncuyu güncelle
    player_id = request.args.get('player_id')
    if player_id and player_id in rooms[code]['players']:
        rooms[code]['players'][player_id]['last_seen'] = datetime.now().isoformat()
        rooms[code]['players'][player_id]['connected'] = True
    
    return jsonify({
        'success': True,
        'room': rooms[code]
    })


@app.route('/room/<code>/select', methods=['POST'])
def select_province(code):
    """Eyalet seç"""
    if code not in rooms:
        return jsonify({'success': False, 'error': 'Oda bulunamadı'}), 404
    
    data = request.json
    player_id = data.get('player_id')
    province = data.get('province')
    
    room = rooms[code]
    
    if player_id not in room['players']:
        return jsonify({'success': False, 'error': 'Oyuncu bulunamadı'}), 404
    
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
    player_id = data.get('player_id')
    
    room = rooms[code]
    
    if room['host_id'] != player_id:
        return jsonify({'success': False, 'error': 'Sadece host başlatabilir'}), 403
    
    if len(room['players']) < 2:
        return jsonify({'success': False, 'error': 'En az 2 oyuncu gerekli'}), 400
    
    # Herkes eyalet seçmiş mi?
    for player in room['players'].values():
        if not player['province']:
            return jsonify({'success': False, 'error': f"{player['name']} eyalet seçmedi"}), 400
    
    room['game_started'] = True
    room['current_turn'] = 1
    room['current_player_id'] = list(room['players'].keys())[0]
    
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
    player_id = data.get('player_id')
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
    
    # İlk oyuncuya geri döndüyse tur sayısını artır
    if next_index == 0:
        room['current_turn'] += 1
    
    log(f"[{code}] Tur geçildi: {room['players'][player_id]['name']} -> {room['players'][room['current_player_id']]['name']}")
    
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
    player_id = data.get('player_id')
    message = data.get('message', '')
    
    room = rooms[code]
    
    if 'chat' not in room:
        room['chat'] = []
    
    room['chat'].append({
        'player_id': player_id,
        'player_name': room['players'].get(player_id, {}).get('name', 'Anonim'),
        'message': message,
        'time': datetime.now().isoformat()
    })
    
    # Son 50 mesajı tut
    room['chat'] = room['chat'][-50:]
    
    return jsonify({'success': True})


@app.route('/room/<code>/leave', methods=['POST'])
def leave_room(code):
    """Odadan ayrıl"""
    if code not in rooms:
        return jsonify({'success': False, 'error': 'Oda bulunamadı'}), 404
    
    data = request.json
    player_id = data.get('player_id')
    
    room = rooms[code]
    
    if player_id in room['players']:
        player_name = room['players'][player_id]['name']
        del room['players'][player_id]
        log(f"[{code}] {player_name} ayrıldı")
        
        # Oda boşaldıysa sil
        if not room['players']:
            del rooms[code]
            log(f"[{code}] Oda silindi (boş)")
    
    return jsonify({'success': True})


# ========== DİPLOMASİ SİSTEMİ ==========

@app.route('/room/<code>/diplomacy/propose', methods=['POST'])
def propose_diplomacy(code):
    """İttifak, ticaret veya barış teklifi"""
    if code not in rooms:
        return jsonify({'success': False, 'error': 'Oda bulunamadı'}), 404
    
    data = request.json
    from_player = data.get('from_player_id')
    to_player = data.get('to_player_id')
    proposal_type = data.get('type')  # 'alliance', 'trade', 'peace'
    terms = data.get('terms', {})
    
    room = rooms[code]
    
    if from_player not in room['players'] or to_player not in room['players']:
        return jsonify({'success': False, 'error': 'Oyuncu bulunamadı'}), 404
    
    proposal_id = str(uuid.uuid4())[:8]
    proposal = {
        'id': proposal_id,
        'type': proposal_type,
        'from_player_id': from_player,
        'to_player_id': to_player,
        'from_player': room['players'][from_player],
        'terms': terms,
        'created_at': datetime.now().isoformat()
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
    player_id = data.get('player_id')
    proposal_id = data.get('proposal_id')
    accept = data.get('accept', False)
    
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
                'formed_at': datetime.now().isoformat()
            })
            result_message = f"İttifak kuruldu!"
            
        elif proposal['type'] == 'trade':
            room['diplomacy']['trade_deals'].append({
                'from': proposal['from_player_id'],
                'to': proposal['to_player_id'],
                'gold_per_turn': proposal['terms'].get('gold', 100),
                'formed_at': datetime.now().isoformat()
            })
            result_message = f"Ticaret anlaşması yapıldı!"
            
        elif proposal['type'] == 'peace':
            # Savaşı sonlandır
            wars = room['diplomacy']['wars']
            for war in wars[:]:
                if set([war['attacker'], war['defender']]) == set([proposal['from_player_id'], proposal['to_player_id']]):
                    wars.remove(war)
            result_message = f"Barış yapıldı!"
    else:
        result_message = f"Teklif reddedildi."
    
    from_name = room['players'][proposal['from_player_id']]['name']
    to_name = room['players'][proposal['to_player_id']]['name']
    log(f"[{code}] {to_name} {proposal['type']} teklifini {'kabul etti' if accept else 'reddetti'}")
    
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
    attacker_id = data.get('attacker_id')
    defender_id = data.get('defender_id')
    
    room = rooms[code]
    
    if attacker_id not in room['players'] or defender_id not in room['players']:
        return jsonify({'success': False, 'error': 'Oyuncu bulunamadı'}), 404
    
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
    attacker_id = data.get('attacker_id')
    defender_id = data.get('defender_id')
    attacker_power = data.get('attacker_power', 100)
    
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
    defender_power = defender_state.get('military_power', 100)
    
    # Savaş sonucunu hesapla
    import random
    ratio = attacker_power / max(defender_power, 1)
    luck = random.uniform(0.8, 1.2)
    effective_ratio = ratio * luck
    
    if effective_ratio > 1.5:
        result = 'decisive_victory'
        message = 'Ezici zafer! Düşman ordusunun %50\'si yok edildi.'
        attacker_losses = int(attacker_power * 0.1)
        defender_losses = int(defender_power * 0.5)
        gold_plunder = 2000
    elif effective_ratio > 1.2:
        result = 'victory'
        message = 'Zafer! Düşman ordusunun %30\'u yok edildi.'
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
        message = 'Yenilgi! Ordunuzun %30\'u kaybedildi.'
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
    """Oyuncu durumunu senkronize et"""
    if code not in rooms:
        return jsonify({'success': False, 'error': 'Oda bulunamadı'}), 404
    
    data = request.json
    player_id = data.get('player_id')
    state = data.get('state', {})
    
    room = rooms[code]
    
    if player_id not in room['players']:
        return jsonify({'success': False, 'error': 'Oyuncu bulunamadı'}), 404
    
    room['player_states'][player_id] = {
        'gold': state.get('gold', 0),
        'military_power': state.get('military_power', 0),
        'population': state.get('population', 0),
        'happiness': state.get('happiness', 50),
        'buildings': state.get('buildings', []),
        'updated_at': datetime.now().isoformat()
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
    """Sunucu durumu"""
    return jsonify({
        'status': 'ok',
        'rooms': len(rooms),
        'time': datetime.now().isoformat()
    })


def main():
    parser = argparse.ArgumentParser(description='Osmanlı Oyunu HTTP Sunucusu')
    parser.add_argument('--host', default='0.0.0.0', help='Sunucu adresi')
    parser.add_argument('--port', type=int, default=5000, help='Port numarası')
    args = parser.parse_args()
    
    print(f"""
╔════════════════════════════════════════════════════════════╗
║     OSMANLI EYALET YÖNETİM SİMÜLASYONU - HTTP SUNUCU       ║
╠════════════════════════════════════════════════════════════╣
║  Host: {args.host}                                         
║  Port: {args.port}                                         
║  URL:  http://{args.host}:{args.port}                      
╠════════════════════════════════════════════════════════════╣
║  Endpoints:                                                
║    POST /room/create      - Oda oluştur                    
║    POST /room/<code>/join - Odaya katıl                    
║    GET  /room/<code>      - Oda durumu (polling)           
║    POST /room/<code>/select - Eyalet seç                   
║    POST /room/<code>/start  - Oyunu başlat                 
║    GET  /health           - Sunucu durumu                  
╚════════════════════════════════════════════════════════════╝
    """)
    
    app.run(host=args.host, port=args.port, debug=True)


if __name__ == "__main__":
    main()
