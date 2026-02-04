# -*- coding: utf-8 -*-
"""
Osmanlı Eyalet Yönetim Simülasyonu - Çok Oyunculu Oyun Ekranı
Multiplayer oyun modu ana ekranı
"""

import pygame
from ui.screen_manager import BaseScreen, ScreenType
from ui.components import Button, Panel, MenuList
from ui.text_input import AccessibleTextInput
from config import COLORS, FONTS, SCREEN_WIDTH, SCREEN_HEIGHT


class MultiplayerGameScreen(BaseScreen):
    """Çok oyunculu oyun ekranı"""
    
    def __init__(self, screen_manager):
        super().__init__(screen_manager)
        
        # Network client
        self.network = None
        
        # Sohbet girişi
        self.chat_input = AccessibleTextInput(
            x=50, y=SCREEN_HEIGHT - 80, width=400, height=35,
            label="", placeholder="Mesaj yazın (. tuşu)", max_length=100
        )
        self.chat_mode = False
        
        # Oyuncu paneli
        self.players_panel = Panel(SCREEN_WIDTH - 300, 50, 280, 300, "Oyuncular")
        
        # Aksiyon menüsü
        self.action_menu = MenuList(
            x=50,
            y=150,
            width=300,
            item_height=45
        )
        
        # Diplomasi alt menüsü
        self.diplomacy_menu = MenuList(
            x=400,
            y=150,
            width=300,
            item_height=45
        )
        self.diplomacy_mode = False
        self.diplomacy_target = None
        
        # Teklif kuyruğu
        self.pending_proposals = []  # [{"type": "alliance"/"trade", "from_player": {...}, "from_player_id": "..."}]
        self.proposal_mode = False
        self.current_proposal = None
        
        # Fontlar
        self._header_font = None
        self._info_font = None
    
    def get_header_font(self):
        if self._header_font is None:
            self._header_font = pygame.font.Font(None, FONTS['header'])
        return self._header_font
    
    def get_info_font(self):
        if self._info_font is None:
            self._info_font = pygame.font.Font(None, FONTS['body'])
        return self._info_font
    
    def on_enter(self):
        # Lobi'den mevcut network client'ı al
        from network import get_network_client
        
        # Mevcut client'ı al (lobi'de oluşturulmuş olmalı)
        if hasattr(self.screen_manager, '_shared_network'):
            self.network = self.screen_manager._shared_network
        else:
            # Yeni client oluştur (fallback)
            self.network = get_network_client()
        
        # Oyuncunun eyaletini al ve GameManager oluştur
        # Bu tüm offline özellikleri (ekonomi, askeri, diplomasi vb.) aktif eder
        if self.network and self.network.room_data:
            my_player = self.network.get_my_player()
            if my_player and my_player.get('province'):
                from game.game_manager import GameManager
                
                # GameManager yoksa veya farklı eyalet ise yeniden oluştur
                province_name = my_player['province']
                gm = self.screen_manager.game_manager
                
                if not gm or getattr(gm, '_mp_province', None) != province_name:
                    gm = GameManager()
                    gm.new_game(province_name)
                    gm._mp_province = province_name  # Multiplayer eyalet takibi
                    self.screen_manager.game_manager = gm
                    print(f"[MP] GameManager oluşturuldu: {province_name}")
        
        self._setup_action_menu()
        self._update_players_panel()
        self._register_callbacks()
        
        # Oyun başladı bildirimi
        if self.network and self.network.is_my_turn():
            self.audio.speak("Oyun başladı! Sıra sizde.", interrupt=True)
        else:
            current = self._get_current_player_name()
            self.audio.speak(f"Oyun başladı! Sıra {current} oyuncusunda.", interrupt=True)
    
    def _register_callbacks(self):
        """Ağ callback'lerini kaydet"""
        if not self.network:
            return
        
        self.network.register_callback("turn_ended", self._on_turn_ended)
        self.network.register_callback("chat_message", self._on_chat_message)
        self.network.register_callback("player_disconnected", self._on_player_disconnected)
        self.network.register_callback("war_declared", self._on_war_declared)
        self.network.register_callback("alliance_proposal", self._on_alliance_proposal)
        self.network.register_callback("trade_proposal", self._on_trade_proposal)
        self.network.register_callback("alliance_formed", self._on_alliance_formed)
        self.network.register_callback("trade_agreement_formed", self._on_trade_formed)
        self.network.register_callback("all_ready", self._on_all_ready)
        self.network.register_callback("player_state_updated", self._on_player_state_updated)
        self.network.register_callback("battle_result", self._on_battle_result)
        self.network.register_callback("room_saved", self._on_room_saved)
        self.network.register_callback("player_reconnected", self._on_player_reconnected)
    
    def _setup_action_menu(self):
        """Aksiyon menüsünü ayarla"""
        self.action_menu.clear()
        
        # Bekleyen teklifler (her zaman göster)
        proposals = self.network.get_pending_proposals() if self.network else []
        if proposals:
            self.action_menu.add_item(f"Gelen Teklifler ({len(proposals)})", self._open_proposals)
        
        # Sıra bendeyse aksiyonlar
        if self.network and self.network.is_my_turn():
            self.action_menu.add_item("Eyalet Yönetimi", self._manage_province)
            self.action_menu.add_item("Ekonomi", self._open_economy)
            self.action_menu.add_item("Askeri", self._open_military)
            self.action_menu.add_item("İnşaat", self._open_construction)
            self.action_menu.add_item("Diplomasi (Oyuncular)", self._open_diplomacy)
            self.action_menu.add_item("Mesaj Gönder", self._open_chat)
            self.action_menu.add_item("Turu Bitir", self._end_turn)
            
            # Host ise kaydetme seçeneği
            if self.network.is_host:
                self.action_menu.add_item("Odayı Kaydet", self._save_room)
        else:
            self.action_menu.add_item("Mesaj Gönder", self._open_chat)
            self.action_menu.add_item("Durumu Görüntüle", self._view_status)
        
        # Oyundan ayrılma (her zaman)
        self.action_menu.add_item("Oyundan Ayrıl", self._leave_game)
    
    def _setup_diplomacy_menu(self):
        """Diplomasi menüsünü ayarla"""
        self.diplomacy_menu.clear()
        
        if not self.network:
            return
        
        # Diğer oyuncuları listele
        players = self.network.get_players()
        my_id = self.network.player_id
        
        for player in players:
            player_id = player.get("id")
            if player_id != my_id:
                name = player.get("name", "?")
                province = player.get("province", "?")
                
                # Durum kontrolü
                is_allied = self.network.is_allied_with(player_id)
                is_at_war = self.network.is_at_war_with(player_id)
                
                if is_allied:
                    status = "[Müttefik]"
                elif is_at_war:
                    status = "[Savaşta]"
                else:
                    status = ""
                
                self.diplomacy_menu.add_item(
                    f"{status} {name} ({province})".strip(),
                    lambda p=player: self._select_diplomacy_target(p)
                )
        
        self.diplomacy_menu.add_item("Geri", self._close_diplomacy)
    
    def _setup_diplomacy_actions(self):
        """Hedef seçildikten sonra diplomasi aksiyonları"""
        self.diplomacy_menu.clear()
        
        if not self.diplomacy_target:
            self._close_diplomacy()
            return
        
        name = self.diplomacy_target.get("name", "?")
        target_id = self.diplomacy_target.get("id")
        
        is_allied = self.network.is_allied_with(target_id)
        is_at_war = self.network.is_at_war_with(target_id)
        
        # Bilgi görüntüleme (her zaman)
        self.diplomacy_menu.add_item(f"Bilgi Görüntüle - {name}", self._view_target_info)
        
        if is_allied:
            self.diplomacy_menu.add_item(f"[Müttefik] {name}", None)
        elif is_at_war:
            self.diplomacy_menu.add_item(f"Saldır - {name}", self._attack)
            self.diplomacy_menu.add_item(f"Barış Teklif Et - {name}", self._propose_peace)
        else:
            self.diplomacy_menu.add_item(f"İttifak Teklif Et - {name}", self._propose_alliance)
            self.diplomacy_menu.add_item(f"Ticaret Teklif Et - {name}", self._propose_trade)
            self.diplomacy_menu.add_item(f"Savaş İlan Et - {name}", self._declare_war)
        
        self.diplomacy_menu.add_item("Geri", lambda: self._setup_diplomacy_menu())
    
    def _update_players_panel(self):
        """Oyuncu panelini güncelle"""
        self.players_panel.clear()
        
        if not self.network or not self.network.room_data:
            return
        
        room = self.network.room_data
        current_id = room.get("current_player_id")
        
        for pid, player in room.get("players", {}).items():
            if pid == current_id:
                status = "[SIRA]"  # Sıra ondaysa
            elif player.get("connected"):
                status = "[Bağlı]"
            else:
                status = "[Çevrimdışı]"
            
            name = player.get("name", "?")
            province = player.get("province", "?")
            
            self.players_panel.add_item(f"{status} {name}", province)
    
    def _get_current_player_name(self) -> str:
        """Sırası olan oyuncunun adını döndür"""
        if not self.network or not self.network.room_data:
            return "Bilinmeyen"
        
        room = self.network.room_data
        current_id = room.get("current_player_id")
        players = room.get("players", {})
        
        if current_id in players:
            return players[current_id].get("name", "Bilinmeyen")
        return "Bilinmeyen"
    
    def announce_screen(self):
        self.audio.announce_screen_change("Çok Oyunculu Oyun")
        
        if self.network and self.network.is_my_turn():
            self.audio.speak("Sıra sizde. Aksiyon seçin veya turu bitirin.")
        else:
            current = self._get_current_player_name()
            self.audio.speak(f"Sıra {current} oyuncusunda. Bekleyin.")
    
    def handle_event(self, event) -> bool:
        # Sohbet modu
        if self.chat_mode:
            if self.chat_input.handle_event(event):
                if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                    message = self.chat_input.get_text()
                    if message and self.network:
                        self.network.send_chat(message)
                        self.audio.speak("Mesaj gönderildi.", interrupt=True)
                    self.chat_mode = False
                    self.chat_input.clear()
                    self.chat_input.unfocus()
                return True
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.chat_mode = False
                self.chat_input.unfocus()
                return True
            return True
        
        # Diplomasi modu
        if self.diplomacy_mode:
            if self.diplomacy_menu.handle_event(event):
                return True
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self._close_diplomacy()
                return True
        
        # Teklif yanıtlama modu
        if self.proposal_mode:
            if self.diplomacy_menu.handle_event(event):
                return True
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self._close_proposal_menu()
                return True
            return True
        
        # Normal aksiyon menüsü
        if self.action_menu.handle_event(event):
            return True
        
        if event.type == pygame.KEYDOWN:
            # Y - Teklifleri yanıtla
            if event.key == pygame.K_y:
                if self.pending_proposals:
                    self._open_proposal_menu()
                else:
                    self.audio.speak("Bekleyen teklif yok.", interrupt=True)
                return True
            
            # Period (.) - Sohbet aç
            if event.key == pygame.K_PERIOD:
                self._open_chat()
                return True
            
            # Space - Turu bitir (sıra bendeyse)
            if event.key == pygame.K_SPACE:
                if self.network and self.network.is_my_turn():
                    self._end_turn()
                else:
                    self.audio.speak("Sıra sizde değil.", interrupt=True)
                return True
            
            # F1 - Yardım
            if event.key == pygame.K_F1:
                self._announce_help()
                return True
            
            # Escape - Ana menüye dön
            if event.key == pygame.K_ESCAPE:
                self._leave_game()
                return True
        
        return False
    
    def _announce_help(self):
        """Yardım metnini oku"""
        help_text = (
            "Çok oyunculu oyun. "
            "Sıranız geldığında aksiyon seçin. "
            "Diplomasi ile diğer oyunculara ittifak, ticaret teklif edebilir veya savaş ilan edebilirsiniz. "
            "Nokta tuşuyla mesaj gönderin. "
            "Space ile turu bitirin. "
            "Escape ile oyundan çıkın."
        )
        self.audio.speak(help_text, interrupt=True)
    
    # ===== AKSİYONLAR =====
    
    def _manage_province(self):
        """Eyalet yönetimi - ana eyalet görünümüne geç"""
        self.screen_manager.is_multiplayer_mode = True
        self.audio.speak("Eyalet yönetimi açılıyor.", interrupt=True)
        self.screen_manager.change_screen(ScreenType.PROVINCE_VIEW)
    
    def _open_economy(self):
        """Ekonomi ekranına git"""
        self.screen_manager.is_multiplayer_mode = True
        self.audio.speak("Ekonomi ekranı açılıyor.", interrupt=True)
        self.screen_manager.change_screen(ScreenType.ECONOMY)
    
    def _open_military(self):
        """Askeri ekrana git"""
        self.screen_manager.is_multiplayer_mode = True
        self.audio.speak("Askeri ekranı açılıyor.", interrupt=True)
        self.screen_manager.change_screen(ScreenType.MILITARY)
    
    def _open_construction(self):
        """Inşaat ekranına git"""
        self.screen_manager.is_multiplayer_mode = True
        self.audio.speak("İnşaat ekranı açılıyor.", interrupt=True)
        self.screen_manager.change_screen(ScreenType.CONSTRUCTION)
    
    def _open_diplomacy(self):
        """Diplomasi menüsünü aç"""
        self.diplomacy_mode = True
        self.diplomacy_target = None
        self._setup_diplomacy_menu()
        self.audio.speak("Diplomasi. Hedef oyuncu seçin.", interrupt=True)
    
    def _close_diplomacy(self):
        """Diplomasi menüsünü kapat"""
        self.diplomacy_mode = False
        self.diplomacy_target = None
        self._setup_action_menu()
    
    def _select_diplomacy_target(self, player: dict):
        """Diplomasi hedefi seç"""
        self.diplomacy_target = player
        self._setup_diplomacy_actions()
        self.audio.speak(f"{player.get('name')} seçildi. Aksiyon seçin.", interrupt=True)
    
    def _open_proposals(self):
        """Gelen teklifleri göster"""
        if not self.network:
            return
        
        proposals = self.network.get_pending_proposals()
        
        if not proposals:
            self.audio.speak("Bekleyen teklif yok.", interrupt=True)
            return
        
        self.diplomacy_mode = True
        self.diplomacy_menu.clear()
        
        for proposal in proposals:
            p_type = proposal.get('type', '?')
            from_player = proposal.get('from_player', {})
            from_name = from_player.get('name', '?')
            p_id = proposal.get('id')
            
            type_names = {
                'alliance': 'İttifak',
                'trade': 'Ticaret',
                'peace': 'Barış'
            }
            type_name = type_names.get(p_type, p_type)
            
            self.diplomacy_menu.add_item(
                f"{type_name} - {from_name}",
                lambda pid=p_id, ptype=type_name, pname=from_name: self._show_proposal_options(pid, ptype, pname)
            )
        
        self.diplomacy_menu.add_item("Geri", self._close_diplomacy)
        self.audio.speak(f"{len(proposals)} teklif var. Birini seçin.", interrupt=True)
    
    def _show_proposal_options(self, proposal_id, proposal_type, from_name):
        """Teklif seçeneklerini göster"""
        self.diplomacy_menu.clear()
        
        self.diplomacy_menu.add_item(
            f"Kabul Et - {proposal_type} ({from_name})",
            lambda: self._respond_proposal(proposal_id, True)
        )
        self.diplomacy_menu.add_item(
            f"Reddet - {proposal_type} ({from_name})",
            lambda: self._respond_proposal(proposal_id, False)
        )
        self.diplomacy_menu.add_item("Geri", self._open_proposals)
    
    def _respond_proposal(self, proposal_id, accept):
        """Teklifi yanıtla"""
        if self.network:
            if self.network.respond_proposal(proposal_id, accept):
                if accept:
                    self.audio.speak("Teklif kabul edildi!", interrupt=True)
                else:
                    self.audio.speak("Teklif reddedildi.", interrupt=True)
            else:
                self.audio.speak(f"Hata: {self.network.last_error}", interrupt=True)
        
        self._close_diplomacy()
        self._setup_action_menu()
    
    def _propose_alliance(self):
        """İttifak teklifi"""
        if self.network and self.diplomacy_target:
            self.network.propose_alliance(self.diplomacy_target.get("id"))
            self.audio.speak("İttifak teklifi gönderildi.", interrupt=True)
        self._close_diplomacy()
    
    def _propose_trade(self):
        """Ticaret teklifi"""
        if self.network and self.diplomacy_target:
            self.network.propose_trade(self.diplomacy_target.get("id"))
            self.audio.speak("Ticaret teklifi gönderildi.", interrupt=True)
        self._close_diplomacy()
    
    def _declare_war(self):
        """Savaş ilanı"""
        if self.network and self.diplomacy_target:
            self.network.declare_war(self.diplomacy_target.get("id"))
            self.audio.speak("Savaş ilan edildi!", interrupt=True)
        self._close_diplomacy()
    
    def _attack(self):
        """Savaş saldırısı"""
        if self.network and self.diplomacy_target:
            # Askeri gücü al
            gm = self.screen_manager.game_manager
            power = gm.military.get_total_power() if gm else 100
            
            result = self.network.attack(self.diplomacy_target.get("id"), power)
            
            if result:
                self.audio.speak(result.get('message', 'Saldiri tamamlandi.'), interrupt=True)
                
                # Kayıpları uygula
                if gm:
                    attacker_losses = result.get('attacker_losses', 0)
                    if attacker_losses > 0:
                        gm.military.apply_casualties(attacker_losses)
                        self.audio.speak(f"{attacker_losses} asker kaybettiniz.", interrupt=False)
                    
                    # Zafer ödülü (altın yağması)
                    gold_plunder = result.get('gold_plunder', 0)
                    if gold_plunder > 0:
                        gm.economy.resources.gold += gold_plunder
                        self.audio.speak(f"{gold_plunder} altin yagmalandi!", interrupt=False)
                        
                    # Zafer deneyimi
                    if result.get('result') in ['decisive_victory', 'victory']:
                        gm.military.total_victories += 1
                        gm.military.morale = min(100, gm.military.morale + 10)
            else:
                self.audio.speak(f"Saldiri basarisiz: {self.network.last_error}", interrupt=True)
        
        self._close_diplomacy()
    
    def _view_target_info(self):
        """Hedef oyuncu bilgisini görüntüle"""
        if not self.network or not self.diplomacy_target:
            return
        
        target_id = self.diplomacy_target.get("id")
        info = self.network.get_player_info(target_id)
        
        if info:
            player = info.get('player', {})
            state = info.get('state', {})
            
            name = player.get('name', '?')
            province = player.get('province', '?')
            gold = state.get('gold', '?')
            power = state.get('military_power', '?')
            population = state.get('population', '?')
            
            self.audio.speak(
                f"{name}. Eyalet: {province}. "
                f"Altın: {gold}. Askeri güç: {power}. Nüfus: {population}.",
                interrupt=True
            )
        else:
            self.audio.speak("Oyuncu bilgisi alınamadı.", interrupt=True)
    
    def _propose_peace(self):
        """Barış teklifi"""
        if self.network and self.diplomacy_target:
            # Barış teklifi gönder
            try:
                import requests
                r = requests.post(
                    f"{self.network.server_url}/room/{self.network.room_code}/diplomacy/propose",
                    json={
                        'from_player_id': self.network.player_id,
                        'to_player_id': self.diplomacy_target.get("id"),
                        'type': 'peace',
                        'terms': {}
                    },
                    timeout=5
                )
                if r.status_code == 200:
                    self.audio.speak("Barış teklifi gönderildi.", interrupt=True)
                else:
                    self.audio.speak("Barış teklifi gönderilemedi.", interrupt=True)
            except:
                self.audio.speak("Barış teklifi gönderilemedi.", interrupt=True)
        
        self._close_diplomacy()
    
    def _open_chat(self):
        """Sohbet modunu aç"""
        self.chat_mode = True
        self.chat_input.clear()
        self.chat_input.focus()
    
    def _view_status(self):
        """Durumu görüntüle"""
        if not self.network or not self.network.room_data:
            return
        
        room = self.network.room_data
        game_state = room.get("game_state", {})
        
        year = game_state.get("year", 1520)
        month = game_state.get("month", 1)
        day = game_state.get("day", 1)
        turn = room.get("current_turn", 0)
        
        player_count = len(room.get("players", {}))
        current = self._get_current_player_name()
        
        self.audio.speak(
            f"Tarih: {day}.{month}.{year}. Tur: {turn}. "
            f"{player_count} oyuncu aktif. Sıra: {current}.",
            interrupt=True
        )
    
    def _end_turn(self):
        """Turu bitir"""
        if not self.network:
            return
        
        if not self.network.is_my_turn():
            self.audio.speak("Sıra sizde değil.", interrupt=True)
            return
        
        # Yerel oyun durumunu güncelle (ekonomi, askeri, inşaat vb.)
        gm = self.screen_manager.game_manager
        if gm:
            gm.process_turn()
            
            # Durumu sunucuya senkronize et
            state = {
                'gold': gm.economy.resources.gold,
                'military_power': gm.military.get_total_power(),
                'population': gm.population.population.total,
                'happiness': gm.population.happiness,
                'buildings': [str(b) for b in gm.construction.buildings.keys()]
            }
            self.network.sync_state(state)
        
        # Ağ üzerinden sırayı devret
        self.network.end_turn()
        self.audio.speak("Tur bitti. Sıra sonraki oyuncuda.", interrupt=True)
        self._setup_action_menu()
    
    def _save_room(self):
        """Odayı kaydet (sadece host)"""
        if not self.network or not self.network.is_host:
            self.audio.speak("Sadece host odayı kaydedebilir.", interrupt=True)
            return
        
        self.network.save_room()
        self.audio.speak("Oda kaydediliyor...", interrupt=True)
    
    def _leave_game(self):
        """Oyundan ayrıl"""
        if self.network:
            self.network.disconnect()
        self.screen_manager.change_screen(ScreenType.MAIN_MENU)
    
    # ===== CALLBACK'LER =====
    
    def _on_turn_ended(self, data: dict):
        """Tur bitti"""
        previous_id = data.get("previous_player")
        current_id = data.get("current_player")
        
        self._update_players_panel()
        self._setup_action_menu()
        
        # Sıra bana mı geldi?
        if self.network and current_id == self.network.player_id:
            self.audio.speak("Sıra sizde! Aksiyon seçin veya turu bitirin.", interrupt=True)
        else:
            current = self._get_current_player_name()
            self.audio.speak(f"Sıra {current} oyuncusunda.", interrupt=True)
    
    def _on_chat_message(self, data: dict):
        """Sohbet mesajı alındı"""
        player = data.get("from_player", {})
        message = data.get("message", "")
        player_name = player.get("name", "Anonim")
        
        # Mesajı sesli oku
        self.audio.speak(f"{player_name}: {message}", interrupt=True)
    
    def _on_player_disconnected(self, data: dict):
        """Oyuncu ayrıldı"""
        player = data.get("player", {})
        self.audio.speak(f"{player.get('name')} oyundan ayrıldı.", interrupt=True)
        self._update_players_panel()
    
    def _on_war_declared(self, data: dict):
        """Savaş ilan edildi"""
        attacker = data.get("attacker", {})
        defender = data.get("defender", {})
        message = data.get("message", "")
        
        self.audio.speak(message, interrupt=True)
    
    def _on_battle_result(self, data: dict):
        """Savaş sonucu"""
        message = data.get("message", "Savaş bitti.")
        winner = data.get("winner", "")
        
        # Sonucu oku
        self.audio.speak(message, interrupt=True)
        
        # Oyuncu panelini güncelle
        self._update_players_panel()
    
    def _on_alliance_proposal(self, data: dict):
        """İttifak teklifi alındı"""
        player = data.get("from_player", {})
        message = data.get("message", "")
        from_player_id = data.get("from_player_id") or player.get("id")
        
        # Teklifi kuyruğa ekle
        self.pending_proposals.append({
            "type": "alliance",
            "from_player": player,
            "from_player_id": from_player_id,
            "message": message
        })
        
        self.audio.speak(f"{message} Yanıtlamak için Y tuşuna basın.", interrupt=True)
    
    def _on_trade_proposal(self, data: dict):
        """Ticaret teklifi alındı"""
        player = data.get("from_player", {})
        message = data.get("message", "")
        from_player_id = data.get("from_player_id") or player.get("id")
        
        # Teklifi kuyruğa ekle
        self.pending_proposals.append({
            "type": "trade",
            "from_player": player,
            "from_player_id": from_player_id,
            "message": message
        })
        
        self.audio.speak(f"{message} Yanıtlamak için Y tuşuna basın.", interrupt=True)
    
    def _on_alliance_formed(self, data: dict):
        """İttifak kuruldu"""
        message = data.get("message", "İttifak kuruldu!")
        self.audio.speak(message, interrupt=True)
    
    def _on_trade_formed(self, data: dict):
        """Ticaret anlaşması kuruldu"""
        message = data.get("message", "Ticaret anlaşması kuruldu!")
        self.audio.speak(message, interrupt=True)
    
    def _open_proposal_menu(self):
        """Bekleyen teklifleri göster"""
        if not self.pending_proposals:
            self.audio.speak("Bekleyen teklif yok.", interrupt=True)
            return
        
        self.current_proposal = self.pending_proposals[0]
        self.proposal_mode = True
        
        # Menüyü ayarla
        self.diplomacy_menu.clear()
        p_type = "İttifak" if self.current_proposal["type"] == "alliance" else "Ticaret"
        from_name = self.current_proposal["from_player"].get("name", "?")
        
        self.diplomacy_menu.add_item(f"{p_type} Kabul Et", self._accept_proposal)
        self.diplomacy_menu.add_item(f"{p_type} Reddet", self._reject_proposal)
        self.diplomacy_menu.add_item("Geri", self._close_proposal_menu)
        
        self.audio.speak(f"{from_name} {p_type.lower()} teklif ediyor. Kabul veya reddet.", interrupt=True)
    
    def _accept_proposal(self):
        """Teklifi kabul et"""
        if not self.current_proposal or not self.network:
            return
        
        from_id = self.current_proposal["from_player_id"]
        
        if self.current_proposal["type"] == "alliance":
            self.network.accept_alliance(from_id)
        else:
            self.network.accept_trade(from_id)
        
        # Kuyruktan çıkar
        if self.current_proposal in self.pending_proposals:
            self.pending_proposals.remove(self.current_proposal)
        
        self._close_proposal_menu()
        self.audio.speak("Teklif kabul edildi.", interrupt=True)
    
    def _reject_proposal(self):
        """Teklifi reddet"""
        if not self.current_proposal or not self.network:
            return
        
        from_id = self.current_proposal["from_player_id"]
        
        if self.current_proposal["type"] == "alliance":
            self.network.reject_alliance(from_id)
        else:
            self.network.reject_trade(from_id)
        
        # Kuyruktan çıkar
        if self.current_proposal in self.pending_proposals:
            self.pending_proposals.remove(self.current_proposal)
        
        self._close_proposal_menu()
        self.audio.speak("Teklif reddedildi.", interrupt=True)
    
    def _close_proposal_menu(self):
        """Teklif menüsünü kapat"""
        self.proposal_mode = False
        self.current_proposal = None
        self._setup_action_menu()
    
    def _on_all_ready(self, data: dict):
        """Tüm oyuncular hazır"""
        self.audio.speak(data.get("message", "Tüm oyuncular hazır."), interrupt=True)
    
    def _on_player_state_updated(self, data: dict):
        """Bir oyuncunun durumu güncellendi"""
        player = data.get("player", {})
        player_name = player.get("name", "?")
        game_state = player.get("game_state", {})
        
        # Oyuncu panelini güncelle
        self._update_players_panel()
        
        # Önemli değişiklikleri bildir (opsiyonel)
        # self.audio.speak(f"{player_name} durumu güncellendi.", interrupt=False)
    
    def _on_room_saved(self, data: dict):
        """Oda kaydedildi"""
        message = data.get("message", "Oda kaydedildi.")
        room_code = data.get("room_code", "")
        
        self.audio.speak(f"{message} Kod: {room_code}", interrupt=True)
    
    def _on_player_reconnected(self, data: dict):
        """Oyuncu yeniden bağlandı"""
        player = data.get("player", {})
        player_name = player.get("name", "?")
        
        self.audio.speak(f"{player_name} yeniden bağlandı!", interrupt=True)
        self._update_players_panel()
    
    def update(self, dt: float):
        # Ağ mesajlarını işle
        if self.network:
            self.network.get_pending_messages()
    
    def draw(self, surface: pygame.Surface):
        header_font = self.get_header_font()
        info_font = self.get_info_font()
        
        # Başlık
        title = header_font.render("ÇOK OYUNCULU OYUN", True, COLORS['gold'])
        surface.blit(title, (50, 20))
        
        # Sıra bilgisi
        if self.network and self.network.room_data:
            room = self.network.room_data
            game_state = room.get("game_state", {})
            
            # Tarih
            year = game_state.get("year", 1520)
            month = game_state.get("month", 1)
            day = game_state.get("day", 1)
            date_text = info_font.render(f"Tarih: {day}.{month}.{year}", True, COLORS['text'])
            surface.blit(date_text, (50, 70))
            
            # Tur
            turn = room.get("current_turn", 0)
            turn_text = info_font.render(f"Tur: {turn}", True, COLORS['text'])
            surface.blit(turn_text, (200, 70))
            
            # Sıra
            if self.network.is_my_turn():
                turn_info = info_font.render("SIRA SIZDE", True, COLORS['success'])
            else:
                current = self._get_current_player_name()
                turn_info = info_font.render(f"Sira: {current}", True, COLORS['warning'])
            surface.blit(turn_info, (50, 100))
        
        # Oyuncu paneli
        self.players_panel.draw(surface)
        
        # Aksiyon menüsü
        if self.diplomacy_mode:
            self.diplomacy_menu.draw(surface)
        else:
            self.action_menu.draw(surface)
        
        # Sohbet modu
        if self.chat_mode:
            overlay = pygame.Surface((500, 100), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 220))
            surface.blit(overlay, (30, SCREEN_HEIGHT - 120))
            self.chat_input.draw(surface)
        
        # Kısayollar
        shortcuts = info_font.render("SPACE: Tur Bitir | NOKTA: Mesaj | F1: Yardım | ESC: Çık", True, COLORS['text'])
        surface.blit(shortcuts, (50, SCREEN_HEIGHT - 30))
