# -*- coding: utf-8 -*-
"""
Osmanlı Eyalet Yönetim Simülasyonu - Çok Oyunculu Lobi Ekranı
Oda oluşturma, katılma ve oyuncu bekleme
"""

import pygame
from ui.screen_manager import BaseScreen, ScreenType
from ui.components import Button, Panel, MenuList
from ui.text_input import AccessibleTextInput
from config import COLORS, FONTS, SCREEN_WIDTH, SCREEN_HEIGHT, MULTIPLAYER, get_font


class MultiplayerLobbyScreen(BaseScreen):
    """Çok oyunculu lobi ekranı"""
    
    def __init__(self, screen_manager):
        super().__init__(screen_manager)
        
        # Durum
        self.state = "menu"  # "menu", "connecting", "lobby", "province_select"
        self.error_message = ""
        self.player_name = "Oyuncu"
        
        # Varsayılan sunucu config'den alınır
        self.server_ip = MULTIPLAYER['default_server']
        self.server_port = MULTIPLAYER['default_port']
        
        # Network client
        self.network = None
        
        # Erişilebilir metin girişleri
        self.name_input = AccessibleTextInput(
            x=200, y=300, width=400, height=40,
            label="Oyuncu İsmi", placeholder="İsminizi yazın", max_length=20
        )
        self.name_input.set_text(self.player_name)
        
        self.room_code_input = AccessibleTextInput(
            x=200, y=300, width=400, height=40,
            label="Oda Kodu", placeholder="6 karakterlik kod", max_length=6
        )
        
        # Sohbet mesajı girişi
        self.chat_input = AccessibleTextInput(
            x=200, y=300, width=400, height=40,
            label="Mesaj", placeholder="Mesajınızı yazın", max_length=100
        )
        
        # Ana menü
        self.main_menu = MenuList(
            x=200,
            y=200,
            width=400,
            item_height=50
        )
        
        # Oyuncu listesi paneli
        self.players_panel = Panel(50, 100, 400, 400, "Oyuncular")
        
        # Eyalet seçim menüsü
        self.province_menu = MenuList(
            x=500,
            y=150,
            width=350,
            item_height=45
        )
        
        # Aksiyon menüsü (lobi içi)
        self.action_menu = MenuList(
            x=500,
            y=400,
            width=350,
            item_height=45
        )
        
        self.back_button = Button(
            x=20,
            y=SCREEN_HEIGHT - 70,
            width=150,
            height=50,
            text="Geri",
            shortcut="escape",
            callback=self._go_back
        )
        
        self._header_font = None
        self._input_mode = None  # "name", "room_code", "server_ip"
    
    def get_header_font(self):
        if self._header_font is None:
            self._header_font = get_font(FONTS['header'])
        return self._header_font
    
    def on_enter(self):
        from network import get_network_client  # HTTP client
        self.network = get_network_client()
        
        # Network client'ı diğer ekranlarla paylaş
        self.screen_manager._shared_network = self.network
        
        self.state = "menu"
        self._setup_main_menu()
        
        # Callback'leri kaydet
        self._register_callbacks()
    
    def _register_callbacks(self):
        """Ağ callback'lerini kaydet"""
        if not self.network:
            return
        
        self.network.register_callback("room_created", self._on_room_created)
        self.network.register_callback("room_joined", self._on_room_joined)
        self.network.register_callback("player_joined", self._on_player_joined)
        self.network.register_callback("player_disconnected", self._on_player_disconnected)
        self.network.register_callback("province_selected", self._on_province_selected)
        self.network.register_callback("player_ready", self._on_player_ready)
        self.network.register_callback("all_ready", self._on_all_ready)
        self.network.register_callback("game_started", self._on_game_started)
        self.network.register_callback("error", self._on_error)
        self.network.register_callback("chat_message", self._on_chat_message)
    
    def _setup_main_menu(self):
        """Ana menüyü ayarla"""
        self.main_menu.clear()
        self.main_menu.add_item("Oda Oluştur", self._create_room)
        self.main_menu.add_item("Odaya Katıl", self._join_room_prompt)
        self.main_menu.add_item("İsim Değiştir", self._change_name)
        self.main_menu.add_item("Ana Menüye Dön", self._go_back)
    
    def _setup_lobby_menu(self):
        """Lobi menüsünü ayarla (DÜZELTİLDİ: Ready yerine Eyalet Kontrolü)"""
        self.action_menu.clear()
        
        my_player = self.network.get_my_player() if self.network else None
        
        # Eyalet seçmediyse seç butonu göster
        if my_player and not my_player.get("province"):
            self.action_menu.add_item("Eyalet Seç", self._select_province_prompt)
        
        # Eyalet seçtiyse bilgi göster
        if my_player and my_player.get("province"):
            province_name = my_player.get("province")
            self.action_menu.add_item(f"Seçilen: {province_name}", None)
        
        # Host ise başlat butonu kontrolü
        if self.network and self.network.is_host:
            players = self.network.get_players()
            
            # 1. Sadece "Bağlı (Connected)" olan oyuncuları listeye al (Eski hayalet oyuncular engellemesin)
            active_players = [p for p in players if p.get("connected")]
            
            # 2. "ready" durumuna BAKMA. Sadece "province" (eyalet) seçmişler mi ona bak.
            # p.get("province") boş değilse eyalet seçmiş demektir.
            all_have_province = all(p.get("province") for p in active_players)
            
            # En az 2 oyuncu var mı ve hepsinin eyaleti var mı?
            if len(active_players) >= 2 and all_have_province:
                self.action_menu.add_item("OYUNU BASLAT", self._start_game)
            elif len(active_players) < 2:
                self.action_menu.add_item("Bekleniyor... (2+ oyuncu gerekli)", None)
            else:
                self.action_menu.add_item("Bekleniyor... (Herkesin seçmesi bekleniyor)", None)
        
        self.action_menu.add_item("Mesaj Gönder", self._send_chat_prompt)
        self.action_menu.add_item("Odadan Ayrıl", self._leave_room)
    
    def _setup_province_menu(self):
        """Eyalet seçim menüsünü ayarla"""
        self.province_menu.clear()
        
        if not self.network:
            return
        
        available = self.network.get_available_provinces()
        for province in available:
            self.province_menu.add_item(
                province,
                lambda p=province: self._select_province(p)
            )
        
        self.province_menu.add_item("← Geri", lambda: self._set_state("lobby"))
    
    def _update_players_panel(self):
        """Oyuncu panelini güncelle"""
        self.players_panel.clear()
        
        if not self.network or not self.network.room_data:
            return
        
        room = self.network.room_data
        
        # Sadece bağlı oyuncuları say
        active_count = len([p for p in room.get('players', {}).values() if p.get('connected')])
        
        self.players_panel.add_item("Oda Kodu", room.get("code", "???"))
        self.players_panel.add_item("Aktif Oyuncular", f"{active_count}")
        self.players_panel.add_item("", "")
        
        for pid, player in room.get("players", {}).items():
            connected = player.get("connected")
            
            # Paneldeki işareti de "Ready"e göre değil "Eyalet var mı"ya göre yapalım
            has_province = bool(player.get("province"))
            status = "[Hazir]" if has_province else "[Bekliyor]"
            
            if not connected:
                status = "[Cevrimdisi]"
            
            province = player.get("province", "Seçilmedi")
            name = player.get("name", "?")
            
            # Host işareti
            if pid == room.get("host_id"):
                name = f"[HOST] {name}"
            
            self.players_panel.add_item(f"{status} {name}", province)
    
    def announce_screen(self):
        self.audio.announce_screen_change("Çok Oyunculu Lobi")
        
        if not self.network or not self.network.is_available():
            self.audio.speak("Çok oyunculu mod için websockets kütüphanesi gerekli. pip install websockets komutunu çalıştırın.")
    
    def handle_event(self, event) -> bool:
        # Erişilebilir metin girişi aktifse
        # Erişilebilir metin girişi aktifse
        if self._input_mode == "name":
            # Enter kontrolü (handle_event False döndürdüğü için dışarıda kontrol ediyoruz)
            if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                self.player_name = self.name_input.get_text()
                self._input_mode = None
                self.audio.speak(f"İsim değiştirildi: {self.player_name}", interrupt=True)
                self.audio.play_ui_sound('enter')
                return True
                
            if self.name_input.handle_event(event):
                return True
                
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self._input_mode = None
                self.name_input.unfocus()
                return True
            return True
        
        if self._input_mode == "room_code":
            if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                code = self.room_code_input.get_text()
                self._input_mode = None
                self._join_room(code)
                return True
                
            if self.room_code_input.handle_event(event):
                return True
                
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self._input_mode = None
                self.room_code_input.unfocus()
                return True
            return True
        
        if self._input_mode == "chat":
            if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                message = self.chat_input.get_text()
                if message and self.network:
                    self.network.send_chat(message)
                    self.audio.speak("Mesaj gönderildi.", interrupt=True)
                self._input_mode = None
                self.chat_input.clear()
                return True
                
            if self.chat_input.handle_event(event):
                return True
                
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self._input_mode = None
                self.chat_input.unfocus()
                return True
            return True
        
        # Normal menü işleme
        if self.state == "menu":
            if self.main_menu.handle_event(event):
                return True
        
        elif self.state == "connecting":
            # Bağlantı sırasında ESC ile iptal
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
                    self.audio.speak("Bağlantı iptal edildi.", interrupt=True)
                    if self.network:
                        self.network.disconnect()
                    self.state = "menu"
                    self._setup_main_menu()
                    return True
        
        elif self.state == "lobby":
            if self.action_menu.handle_event(event):
                return True
            
            # Period (.) tuşu - Sohbet aç
            if event.type == pygame.KEYDOWN and event.key == pygame.K_PERIOD:
                self._send_chat_prompt()
                return True
        
        elif self.state == "province_select":
            if self.province_menu.handle_event(event):
                return True
        
        if self.back_button.handle_event(event):
            return True
        
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self._go_back()
                return True
            
            if event.key == pygame.K_F1:
                self._announce_status()
                return True
        
        return False
    
    def _announce_status(self):
        """Durumu duyur"""
        if self.state == "menu":
            self.audio.speak("Çok oyunculu menüsü.", interrupt=True)
        elif self.state == "lobby":
            players = self.network.get_players() if self.network else []
            self.audio.speak(
                f"Lobide {len(players)} oyuncu var. "
                f"Oda kodu: {self.network.room_code if self.network else 'yok'}",
                interrupt=True
            )
    
    # ===== AKSİYONLAR =====
    
    def _create_room(self):
        """Oda oluştur (HTTP)"""
        if not self.network:
            self.audio.speak("Ağ bağlantısı yok.", interrupt=True)
            return
        
        self.state = "connecting"
        self.audio.speak(f"Sunucuya bağlanılıyor: {self.server_ip}:{self.server_port}", interrupt=True)
        
        # HTTP bağlantı testi
        if self.network.connect(self.server_ip, self.server_port):
            # Bağlantı başarılı - oda oluştur
            if self.network.create_room(self.player_name):
                self.audio.speak(f"Oda oluşturuldu! Kod: {self.network.room_code}", interrupt=True)
                self._set_state("lobby")
            else:
                self.audio.speak(f"Oda oluşturulamadı: {self.network.last_error}", interrupt=True)
                self.state = "menu"
                self._setup_main_menu()
        else:
            self.audio.speak(f"Sunucuya bağlanılamadı: {self.network.last_error}", interrupt=True)
            self.state = "menu"
            self._setup_main_menu()
    
    def _join_room_prompt(self):
        """Oda kodunu sor"""
        self._input_mode = "room_code"
        self.room_code_input.clear()
        self.room_code_input.focus()
    
    def _join_room(self, room_code: str):
        """Odaya katıl (HTTP)"""
        if not self.network:
            return
        
        self.state = "connecting"
        self.audio.speak(f"Sunucuya bağlanılıyor, oda kodu: {room_code}", interrupt=True)
        
        # HTTP bağlantı testi
        if self.network.connect(self.server_ip, self.server_port):
            # Bağlantı başarılı - odaya katıl
            if self.network.join_room(room_code, self.player_name):
                self.audio.speak(f"Odaya katıldınız! Kod: {room_code}", interrupt=True)
                self._set_state("lobby")
            else:
                self.audio.speak(f"Odaya katılınamadı: {self.network.last_error}", interrupt=True)
                self.state = "menu"
                self._setup_main_menu()
        else:
            self.audio.speak(f"Sunucuya bağlanılamadı: {self.network.last_error}", interrupt=True)
            self.state = "menu"
            self._setup_main_menu()
    
    def _change_name(self):
        """İsim değiştir"""
        self._input_mode = "name"
        self.name_input.set_text(self.player_name)
        self.name_input.focus()
    
    def _select_province_prompt(self):
        """Eyalet seçim moduna geç"""
        self._set_state("province_select")
        self._setup_province_menu()
    
    def _select_province(self, province: str):
        """Eyalet seç"""
        if self.network:
            self.network.select_province(province)
            self._set_state("lobby")
    
    def _set_ready(self, ready: bool):
        """Hazır durumunu ayarla"""
        if self.network:
            self.network.set_ready(ready)
    
    def _start_game(self):
        """Oyunu başlat"""
        if self.network and self.network.is_host:
            if self.network.start_game():
                self.audio.speak("Oyun başlıyor!", interrupt=True)
                self.screen_manager.change_screen(ScreenType.MULTIPLAYER_GAME)
            else:
                self.audio.speak(f"Oyun başlatılamadı: {self.network.last_error}", interrupt=True)
    
    def _send_chat_prompt(self):
        """Mesaj gönder"""
        self._input_mode = "chat"
        self.chat_input.clear()
        self.chat_input.focus()
    
    def _leave_room(self):
        """Odadan ayrıl"""
        if self.network:
            self.network.disconnect()
        self.state = "menu"
        self._setup_main_menu()
    
    def _set_state(self, state: str):
        """Durumu değiştir"""
        self.state = state
        if state == "lobby":
            self._setup_lobby_menu()
            self._update_players_panel()
    
    # ===== CALLBACK'LER =====
    
    def _on_room_created(self, data: dict):
        """Oda oluşturuldu"""
        self.audio.speak(f"Oda oluşturuldu! Kod: {data.get('room_code')}", interrupt=True)
        self._set_state("lobby")
    
    def _on_room_joined(self, data: dict):
        """Odaya katılındı"""
        self.audio.speak("Odaya katıldınız!", interrupt=True)
        self._set_state("lobby")
    
    def _on_player_joined(self, data: dict):
        """Yeni oyuncu katıldı"""
        player = data.get("player", {})
        self.audio.speak(f"{player.get('name')} odaya katıldı.", interrupt=True)
        self._update_players_panel()
        self._setup_lobby_menu()
    
    def _on_player_disconnected(self, data: dict):
        """Oyuncu ayrıldı"""
        player = data.get("player", {})
        self.audio.speak(f"{player.get('name')} ayrıldı.", interrupt=True)
        self._update_players_panel()
        self._setup_lobby_menu()
    
    def _on_province_selected(self, data: dict):
        """Eyalet seçildi"""
        # Kim hangi eyaleti seçti bildir
        player_id = data.get("player_id")
        province = data.get("province")
        if player_id and province:
            # Kendi seçimimiz değilse bildir
            if self.network and player_id != self.network.player_id:
                players = self.network.room_data.get("players", {}) if self.network.room_data else {}
                player_name = players.get(player_id, {}).get("name", "Bir oyuncu")
                self.audio.speak(f"{player_name} {province} eyaletini seçti.", interrupt=False)
        
        self._update_players_panel()
        self._setup_lobby_menu()
        self._setup_province_menu()
        
        # NOT: Burada sesli uyarı yok. Sunucudan "all_ready" gelince konuşacak.
    
    def _on_player_ready(self, data: dict):
        """Oyuncu hazır durumu değişti"""
        self._update_players_panel()
        self._setup_lobby_menu()  # Menüyü güncelle
    
    def _on_all_ready(self, data: dict):
        """Tüm oyuncular hazır (DÜZELTİLDİ)"""
        msg = data.get("message", "Tüm oyuncular hazır!")
        self.audio.speak(msg, interrupt=True)
        self._setup_lobby_menu()  # Başlat butonunu GÖSTER
    
    def _on_game_started(self, data: dict):
        """Oyun başladı"""
        self.audio.speak("Oyun başlıyor!", interrupt=True)
        # Çok oyunculu oyun ekranına geç
        self.screen_manager.change_screen(ScreenType.MULTIPLAYER_GAME)
    
    def _on_error(self, data: dict):
        """Hata"""
        msg = data.get("message", "Bilinmeyen hata")
        self.audio.speak(f"Hata: {msg}", interrupt=True)
        self.error_message = msg
    
    def _on_chat_message(self, data: dict):
        """Sohbet mesajı alındı"""
        player = data.get("from_player", {})
        message = data.get("message", "")
        player_name = player.get("name", "Anonim")
        
        # Mesajı sesli oku
        self.audio.speak(f"{player_name}: {message}", interrupt=True)
    
    def _go_back(self):
        """Geri dön"""
        if self.state == "province_select":
            self._set_state("lobby")
        elif self.state == "lobby":
            self._leave_room()
        elif self.state == "connecting":
            # Bağlantı iptal edildi
            if self.network:
                self.network.disconnect()
            self.audio.speak("Bağlantı iptal edildi.", interrupt=True)
            self.state = "menu"
            self._setup_main_menu()
        else:
            if self.network:
                self.network.disconnect()
            self.screen_manager.change_screen(ScreenType.MAIN_MENU)
    
    def update(self, dt: float):
        # Ağ mesajlarını işle
        if self.network:
            self.network.get_pending_messages()  # Callback'ler otomatik çağrılır
            
            # Bağlantı durumunu kontrol et (non-blocking)
            if self.state == "connecting":
                if self.network.connected:
                    # Bağlantı başarılı - bekleyen aksiyonu çalıştır
                    if hasattr(self, '_pending_action'):
                        if self._pending_action == "create_room":
                            self.audio.speak("Bağlantı başarılı! Oda oluşturuluyor...", interrupt=True)
                            self.network.create_room(self.player_name)
                        elif self._pending_action == "join_room":
                            self.audio.speak("Bağlantı başarılı! Odaya katılınıyor...", interrupt=True)
                            self.network.join_room(self._pending_room_code, self.player_name)
                        self._pending_action = None
                elif self.network.get_connection_error():
                    # Bağlantı başarısız
                    error = self.network.get_connection_error()
                    self.error_message = f"Bağlantı hatası: {error}"
                    self.audio.speak(self.error_message, interrupt=True)
                    self.state = "menu"
                    self._setup_main_menu()
            
            if self.state == "lobby":
                self._update_players_panel()
    
    def draw(self, surface: pygame.Surface):
        header_font = self.get_header_font()
        
        if self.state == "menu":
            title = header_font.render("🌐 ÇOK OYUNCULU", True, COLORS['gold'])
            surface.blit(title, (200, 100))
            
            # Mevcut ayarlar
            font = get_font(FONTS['body'])
            info = font.render(f"İsim: {self.player_name} | Sunucu: {self.server_ip}", True, COLORS['text'])
            surface.blit(info, (200, 150))
            
            self.main_menu.draw(surface)
            
        elif self.state == "connecting":
            title = header_font.render("Bağlanıyor...", True, COLORS['gold'])
            surface.blit(title, (300, 250))
            
        elif self.state == "lobby":
            title = header_font.render(f"🏰 LOBİ - {self.network.room_code if self.network else ''}", True, COLORS['gold'])
            surface.blit(title, (50, 40))
            
            self.players_panel.draw(surface)
            self.action_menu.draw(surface)
            
        elif self.state == "province_select":
            title = header_font.render("📍 EYALET SEÇ", True, COLORS['gold'])
            surface.blit(title, (500, 100))
            
            self.players_panel.draw(surface)
            self.province_menu.draw(surface)
        
        # Giriş modu - Erişilebilir metin kutuları
        if self._input_mode:
            # Arkaplan overlay
            overlay = pygame.Surface((500, 150), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 220))
            surface.blit(overlay, (150, 270))
            
            if self._input_mode == "name":
                self.name_input.draw(surface)
            elif self._input_mode == "room_code":
                self.room_code_input.draw(surface)
            elif self._input_mode == "chat":
                self.chat_input.draw(surface)
        
        # Hata mesajı
        if self.error_message:
            font = get_font(FONTS['body'])
            error = font.render(self.error_message, True, (255, 100, 100))
            surface.blit(error, (200, 550))
        
        self.back_button.draw(surface)