# -*- coding: utf-8 -*-
"""
Osmanlı Eyalet Yönetim Simülasyonu - SQLite Oda Persistence
Sunucu kapanırsa veri kaybını önler
"""

import sqlite3
import json
import os
from datetime import datetime


class RoomDatabase:
    """SQLite tabanlı oda veritabanı"""
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            base = os.path.dirname(os.path.abspath(__file__))
            db_path = os.path.join(base, 'server_rooms.db')
        
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Veritabanı ve tabloları oluştur"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS rooms (
                code TEXT PRIMARY KEY,
                data TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                game_started INTEGER DEFAULT 0
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def save_room(self, code: str, room_data: dict):
        """Odayı kaydet veya güncelle"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        now = datetime.now().isoformat()
        data_json = json.dumps(room_data, ensure_ascii=False, default=str)
        game_started = 1 if room_data.get('game_started') else 0
        
        cursor.execute('''
            INSERT OR REPLACE INTO rooms (code, data, created_at, updated_at, game_started)
            VALUES (?, ?, COALESCE((SELECT created_at FROM rooms WHERE code = ?), ?), ?, ?)
        ''', (code, data_json, code, now, now, game_started))
        
        conn.commit()
        conn.close()
    
    def load_rooms(self) -> dict:
        """Tüm odaları yükle"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT code, data FROM rooms')
        rows = cursor.fetchall()
        conn.close()
        
        rooms = {}
        for code, data_json in rows:
            try:
                rooms[code] = json.loads(data_json)
            except (json.JSONDecodeError, TypeError):
                pass
        
        return rooms
    
    def delete_room(self, code: str):
        """Odayı sil"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM rooms WHERE code = ?', (code,))
        conn.commit()
        conn.close()
    
    def save_all(self, rooms: dict):
        """Tüm odaları toplu kaydet"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        now = datetime.now().isoformat()
        
        for code, room_data in rooms.items():
            data_json = json.dumps(room_data, ensure_ascii=False, default=str)
            game_started = 1 if room_data.get('game_started') else 0
            
            cursor.execute('''
                INSERT OR REPLACE INTO rooms (code, data, created_at, updated_at, game_started)
                VALUES (?, ?, COALESCE((SELECT created_at FROM rooms WHERE code = ?), ?), ?, ?)
            ''', (code, data_json, code, now, now, game_started))
        
        conn.commit()
        conn.close()
    
    def cleanup_old_rooms(self, hours: int = 24):
        """Eski odaları temizle"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cutoff = datetime.now().isoformat()
        cursor.execute('''
            DELETE FROM rooms 
            WHERE updated_at < datetime(?, '-' || ? || ' hours')
        ''', (cutoff, hours))
        
        deleted = cursor.rowcount
        conn.commit()
        conn.close()
        
        return deleted
