# -*- coding: utf-8 -*-
"""
Osmanlı Eyalet Yönetim Simülasyonu - İnteraktif Savaş Ekranı
Kuşatma ve büyük savaşlarda taktiksel kararlar
"""

import pygame
import random
from ui.screen_manager import BaseScreen, ScreenType
from ui.components import Button, Panel, MenuList
from config import COLORS, FONTS, SCREEN_WIDTH, SCREEN_HEIGHT
from game.systems.warfare import BattleType, BattlePhase


class BattleScreen(BaseScreen):
    """İnteraktif savaş ekranı - kuşatmalar için"""
    
    def __init__(self, screen_manager):
        super().__init__(screen_manager)
        
        # Savaş durumu
        self.current_battle = None
        self.current_round = 1
        self.max_rounds = 5  # 5 tur taktik savaş
        self.player_morale = 100
        self.enemy_morale = 100
        self.player_casualties = 0
        self.enemy_casualties = 0
        
        # Tur sistemi - oyuncu ve düşman sırası
        self.is_player_turn = True
        self.enemy_action_pending = False
        self.enemy_turn_timer = 0
        
        # Danışman tavsiyeleri
        self.advisor_tip = ""
        self.last_action_result = ""
        
        # Taktik seçenekleri menüsü
        self.tactics_menu = MenuList(
            x=50,
            y=280,
            width=400,
            item_height=50
        )
        
        # Durum paneli
        self.status_panel = Panel(500, 80, 350, 200, "Savaş Durumu")
        
        # Geri butonu (sadece savaş bitince aktif)
        self.back_button = Button(
            x=SCREEN_WIDTH - 170,
            y=SCREEN_HEIGHT - 70,
            width=150,
            height=50,
            text="Bitir",
            shortcut="escape",
            callback=self._end_battle
        )
        
        self._header_font = None
        self.battle_ended = False
        self.victory = False
    
    def get_header_font(self):
        if self._header_font is None:
            self._header_font = pygame.font.Font(None, FONTS['header'])
        return self._header_font
    
    def set_battle_data(self, battle_data: dict):
        """Dışarıdan savaş verisi ayarla"""
        self.external_battle_data = battle_data
        # Veriyi kullanarak savaş durumunu başlat
        if battle_data:
            self.player_morale = battle_data.get('attacker_army', {}).get('morale', 100)
            self.enemy_morale = battle_data.get('defender_army', {}).get('morale', 80)
    
    def on_enter(self):
        """Savaş ekranına girildiğinde"""
        self._initialize_battle()
        self._setup_tactics_menu()
        self._update_status_panel()
        
        # Savaş müziğini başlat
        self.audio.play_music('battle')
    
    def _initialize_battle(self):
        """Aktif savaşı başlat"""
        gm = self.screen_manager.game_manager
        if not gm or not gm.warfare.active_battles:
            self.battle_ended = True
            return
        
        # İlk aktif kuşatmayı al
        for battle in gm.warfare.active_battles:
            if battle.battle_type == BattleType.SIEGE:
                self.current_battle = battle
                break
        
        if not self.current_battle:
            self.battle_ended = True
            return
        
        self.current_round = 1
        self.player_morale = self.current_battle.attacker_army.morale
        self.enemy_morale = self.current_battle.defender_army.morale
        self.player_casualties = 0
        self.enemy_casualties = 0
        self.battle_ended = False
        self.victory = False
    
    def _setup_tactics_menu(self):
        """Taktik seçeneklerini ayarla"""
        self.tactics_menu.clear()
        
        if self.battle_ended:
            self.tactics_menu.add_item(
                "Savaş Alanından Ayrıl",
                self._end_battle,
                "escape"
            )
            return
        
        # Taktik seçenekleri - her birinin avantaj/dezavantajı var
        tactics = [
            ("Merkez Hücumu", self._tactic_center_attack, 
             "Yüksek hasar, yüksek kayıp riski"),
            ("Kanat Manevrası", self._tactic_flank,
             "Orta hasar, düşük kayıp"),
            ("Savunmada Kal", self._tactic_defend,
             "Düşük hasar, moralı korur"),
            ("Topçu Bombardımanı", self._tactic_artillery,
             "Uzak mesafeden hasar, mühimmat harcır"),
            ("Aldatıcı Geri Çekilme", self._tactic_feint,
             "Düşmanı açığa çıkarır, riskli"),
            ("Teslim Çağrısı", self._tactic_demand_surrender,
             "Savaşsız zafer şansı, reddedilirse moral düşer"),
        ]
        
        for i, (name, callback, desc) in enumerate(tactics):
            self.tactics_menu.add_item(
                name,
                callback,
                str(i + 1)
            )
    
    def _update_status_panel(self):
        """Durum panelini güncelle"""
        self.status_panel.clear()
        
        if not self.current_battle:
            return
        
        self.status_panel.add_item("Hedef", self.current_battle.defender_name)
        self.status_panel.add_item("Tur", f"{self.current_round} / {self.max_rounds}")
        self.status_panel.add_item("", "")
        self.status_panel.add_item("Ordumuz Morali", f"%{self.player_morale}")
        self.status_panel.add_item("Kayıplarımız", str(self.player_casualties))
        self.status_panel.add_item("", "")
        self.status_panel.add_item("Düşman Morali", f"%{self.enemy_morale}")
        self.status_panel.add_item("Düşman Kayıpları", str(self.enemy_casualties))
    
    def announce_screen(self):
        self.audio.announce_screen_change("Savaş Meydanı")
        if self.current_battle:
            self.audio.speak(
                f"{self.current_battle.defender_name} kuşatması. "
                f"Tur {self.current_round}. "
                f"Moralimiz yüzde {self.player_morale}, düşman morali yüzde {self.enemy_morale}. "
                "Taktik seçin.",
                interrupt=False
            )
    
    def handle_event(self, event) -> bool:
        if self.tactics_menu.handle_event(event):
            return True
        
        if event.type == pygame.KEYDOWN:
            # F1 - Durumu oku
            if event.key == pygame.K_F1:
                self._announce_status()
                return True
            
            # D - Danışman tavsiyesi
            if event.key == pygame.K_d:
                self._get_advisor_tip()
                return True
            
            # R - Son sonucu tekrar oku
            if event.key == pygame.K_r:
                if self.last_action_result:
                    self.audio.speak(self.last_action_result, interrupt=True)
                return True
            
            # ESC - Savaş bittiyse çık
            if event.key == pygame.K_ESCAPE and self.battle_ended:
                self._end_battle()
                return True
        
        return False
    
    def _announce_status(self):
        """Savaş durumunu duyur"""
        if not self.current_battle:
            return
        
        self.audio.speak(
            f"Savaş durumu: Tur {self.current_round} / {self.max_rounds}. "
            f"Ordumuz: Moral yüzde {self.player_morale}, {self.player_casualties} kayıp. "
            f"Düşman: Moral yüzde {self.enemy_morale}, {self.enemy_casualties} kayıp.",
            interrupt=True
        )
    
    def _get_advisor_tip(self):
        """Danışmandan tavsiye al"""
        tips = []
        
        if self.player_morale < 50:
            tips.append("Sancak Beyi: Moralimiz düşük, savunmada kalmalıyız!")
        if self.enemy_morale < 40:
            tips.append("Kadı: Düşman çökmek üzere, teslim çağrısı yapabiliriz.")
        if self.player_casualties > self.enemy_casualties * 1.5:
            tips.append("Defterdar: Kayıplarımız ağır, dikkatli olmalıyız.")
        if self.enemy_morale > 70:
            tips.append("Subaşı: Düşman hala güçlü, topçu kullanımı etkili olabilir.")
        if self.current_round >= 4:
            tips.append("Sancak Beyi: Son turlara yaklaştık, kesin sonuç için saldırı şart.")
        
        if not tips:
            tips = ["Danışmanlar: Durumumuz dengeli, herhangi bir taktik uygundur."]
        
        self.advisor_tip = " ".join(tips)
        self.audio.speak(self.advisor_tip, interrupt=True)
    
    # ===== TAKTİK İŞLEMLERİ =====
    
    def _tactic_center_attack(self):
        """Merkez hücumu - yüksek risk, yüksek ödül"""
        player_damage = random.randint(15, 30)
        enemy_damage = random.randint(20, 40)
        
        self.player_casualties += random.randint(50, 150)
        self.enemy_casualties += random.randint(80, 200)
        self.player_morale -= player_damage
        self.enemy_morale -= enemy_damage
        
        self.last_action_result = (
            f"Merkez hücumu! Düşmana {enemy_damage} moral hasarı verdik. "
            f"Ancak biz de {player_damage} moral kaybettik."
        )
        self._process_round_end()
    
    def _tactic_flank(self):
        """Kanat manevrası - dengeli"""
        player_damage = random.randint(5, 15)
        enemy_damage = random.randint(15, 25)
        
        self.player_casualties += random.randint(20, 60)
        self.enemy_casualties += random.randint(50, 100)
        self.player_morale -= player_damage
        self.enemy_morale -= enemy_damage
        
        self.last_action_result = (
            f"Kanat manevrası başarılı! Düşmana {enemy_damage} moral hasarı verdik. "
            f"Kayıplarımız minimal, {player_damage} moral kaybı."
        )
        self._process_round_end()
    
    def _tactic_defend(self):
        """Savunmada kal - güvenli"""
        self.player_morale = min(100, self.player_morale + random.randint(5, 10))
        self.player_casualties += random.randint(10, 30)
        self.enemy_casualties += random.randint(20, 50)
        self.enemy_morale -= random.randint(5, 10)
        
        self.last_action_result = (
            "Savunma pozisyonu aldık. Moralimiz yükseldi. "
            "Düşman saldırıları etkisiz kaldı."
        )
        self._process_round_end()
    
    def _tactic_artillery(self):
        """Topçu bombardımanı - mühimmat harcar ama etkili"""
        gm = self.screen_manager.game_manager
        
        # Mühimmat kontrolü (demir kullan)
        if gm and gm.economy.resources.iron < 50:
            self.audio.speak("Yeterli mühimmat yok! En az 50 demir gerekli.", interrupt=True)
            return
        
        if gm:
            gm.economy.resources.iron -= 50
        
        enemy_damage = random.randint(25, 40)
        self.enemy_casualties += random.randint(100, 200)
        self.enemy_morale -= enemy_damage
        self.player_casualties += random.randint(5, 15)  # Minimal kayıp
        
        self.last_action_result = (
            f"Topçu bombardımanı! Güçlü etki. "
            f"Düşmana {enemy_damage} moral hasarı ve ağır kayıplar verdik."
        )
        self._process_round_end()
    
    def _tactic_feint(self):
        """Aldatıcı geri çekilme - riskli ama etkili olabilir"""
        success = random.random() > 0.4  # %60 başarı şansı
        
        if success:
            enemy_damage = random.randint(30, 50)
            self.enemy_morale -= enemy_damage
            self.enemy_casualties += random.randint(100, 180)
            self.player_casualties += random.randint(20, 40)
            self.last_action_result = (
                f"Aldatma taktiği başarılı! Düşman tuzağa düştü. "
                f"{enemy_damage} moral hasarı ve ağır kayıplar!"
            )
        else:
            player_damage = random.randint(20, 35)
            self.player_morale -= player_damage
            self.player_casualties += random.randint(60, 120)
            self.last_action_result = (
                f"Aldatma taktiği başarısız! Düşman taktiği gördü. "
                f"Karşı saldırıya uğradık, {player_damage} moral kaybı!"
            )
        
        self._process_round_end()
    
    def _tactic_demand_surrender(self):
        """Teslim çağrısı - savaşsız zafer şansı"""
        # Düşman morali düşükse kabul edebilir
        surrender_chance = (100 - self.enemy_morale) / 100
        
        if random.random() < surrender_chance:
            # Teslim!
            self.victory = True
            self.battle_ended = True
            self.last_action_result = (
                "ZAFER! Düşman teslim oldu! "
                "Kalesini kan dökmeden aldık. Büyük başarı!"
            )
        else:
            # Reddedildi
            self.player_morale -= random.randint(10, 20)
            self.last_action_result = (
                "Teslim çağrısı reddedildi! "
                "Düşman direnmeye kararlı. Moralimiz düştü."
            )
        
        self._process_round_end()
    
    def _process_round_end(self):
        """Oyuncu turunun sonunda düşman turunu başlat"""
        # Sonucu duyur
        self.audio.speak(self.last_action_result, interrupt=True)
        
        # Savaş sesleri çal
        self.audio.play_ui_sound('battle_hit')
        
        # Zafer kontrolü (oyuncu anında kazandı mı?)
        if self.enemy_morale <= 0:
            self.victory = True
            self.battle_ended = True
            self.audio.speak("ZAFER! Düşman tamamen çöktü! Kale ele geçirildi!", interrupt=False)
            self._update_status_panel()
            self._setup_tactics_menu()
            return
        
        # Düşman turunu başlat
        self.is_player_turn = False
        self.enemy_action_pending = True
        self.enemy_turn_timer = 0
        self.audio.speak("Düşman hamle yapıyor...", interrupt=False)
        
        # Panelleri güncelle
        self._update_status_panel()
    
    def _check_battle_end(self):
        """Düşman turundan sonra savaş kontrolü"""
        # Yenilgi kontrolü
        if self.player_morale <= 0:
            self.victory = False
            self.battle_ended = True
            self.audio.speak("YENİLGİ! Ordumuz dağıldı! Geri çekilmek zorundayız.", interrupt=False)
        elif self.current_round >= self.max_rounds:
            # Son tur - sonucu belirle
            if self.enemy_morale < self.player_morale:
                self.victory = True
                self.audio.speak("Savaş sona erdi. Düşman geri çekildi, ZAFER bizim!", interrupt=False)
            else:
                self.victory = False
                self.audio.speak("Savaş sona erdi. Kuşatma başarısız oldu.", interrupt=False)
            self.battle_ended = True
        else:
            self.current_round += 1
            self.audio.speak(f"Tur {self.current_round}. Hamlenizi seçin.", interrupt=False)
        
        # Panelleri güncelle
        self._update_status_panel()
        
        if self.battle_ended:
            self._setup_tactics_menu()  # "Ayrıl" seçeneğini göster
    
    def _end_battle(self):
        """Savaşı bitir ve sonuçları uygula"""
        gm = self.screen_manager.game_manager
        
        if gm and self.current_battle:
            # Savaşı listeden kaldır
            if self.current_battle in gm.warfare.active_battles:
                gm.warfare.active_battles.remove(self.current_battle)
            
            # Sonuçları uygula
            if self.victory:
                # Zafer ödülleri (artırılmış)
                loot = random.randint(5000, 15000)
                gm.economy.add_resources(gold=loot)
                gm.diplomacy.sultan_loyalty = min(100, gm.diplomacy.sultan_loyalty + 10)
                gm.military.experience = min(100, gm.military.experience + 15)
                self.audio.speak(f"Zafer! {loot} altın yağma ve padişah sadakati arttı!", interrupt=True)
            else:
                # Yenilgi cezaları (azaltılmış)
                gm.diplomacy.sultan_loyalty = max(0, gm.diplomacy.sultan_loyalty - 5)
                gm.military.morale = max(0, gm.military.morale - 10)
        
        # Normal müziğe dön
        self.audio.play_music('background')
        
        # Ana ekrana dön
        self.screen_manager.change_screen(ScreenType.PROVINCE_VIEW)
    
    def update(self, dt: float):
        """Düşman turunu işle"""
        if self.enemy_action_pending and not self.battle_ended:
            self.enemy_turn_timer += dt
            
            # 1.5 saniye bekle sonra düşman hamle yapar
            if self.enemy_turn_timer >= 1.5:
                self._execute_enemy_turn()
                self.enemy_turn_timer = 0
                self.enemy_action_pending = False
                self.is_player_turn = True
    
    def _execute_enemy_turn(self):
        """Düşman AI taktiği seç ve uygula"""
        # Düşman morali ve durumuna göre taktik seç
        if self.enemy_morale > 70:
            # Yüksek moral - agresif saldırı
            tactic = random.choice(['attack', 'attack', 'flank'])
        elif self.enemy_morale > 40:
            # Orta moral - dengeli
            tactic = random.choice(['flank', 'defend', 'attack'])
        elif self.enemy_morale > 20:
            # Düşük moral - savunmacı
            tactic = random.choice(['defend', 'defend', 'flank'])
        else:
            # Çok düşük moral - umutsuz saldırı veya savunma
            tactic = random.choice(['attack', 'defend'])
        
        # Taktiği uygula
        if tactic == 'attack':
            damage = random.randint(15, 30)
            self.player_morale -= damage
            self.player_casualties += random.randint(40, 100)
            enemy_loss = random.randint(30, 80)
            self.enemy_casualties += enemy_loss
            result = f"Düşman merkez hücumu yaptı! Bize {damage} moral hasarı verdi."
        
        elif tactic == 'flank':
            damage = random.randint(10, 20)
            self.player_morale -= damage
            self.player_casualties += random.randint(30, 70)
            enemy_loss = random.randint(20, 50)
            self.enemy_casualties += enemy_loss
            result = f"Düşman kanat manevrası denedi! Bize {damage} moral hasarı verdi."
        
        else:  # defend
            self.enemy_morale = min(100, self.enemy_morale + random.randint(3, 8))
            self.player_casualties += random.randint(10, 30)
            result = "Düşman savunmaya geçti ve pozisyonunu güçlendirdi."
        
        # Sonucu duyur
        self.audio.speak(f"Düşman turu: {result}", interrupt=True)
        
        # _process_round_end çağır
        self._check_battle_end()
    
    def draw(self, surface: pygame.Surface):
        # Başlık
        header_font = self.get_header_font()
        if self.current_battle:
            title = f"⚔️ {self.current_battle.defender_name} KUŞATMASI - TUR {self.current_round}"
        else:
            title = "⚔️ SAVAŞ"
        
        title_render = header_font.render(title, True, COLORS['gold'])
        surface.blit(title_render, (50, 30))
        
        # Durum paneli
        self.status_panel.draw(surface)
        
        # Danışman tavsiyesi
        if self.advisor_tip:
            font = pygame.font.Font(None, FONTS['body'])
            tip_render = font.render(self.advisor_tip[:80], True, COLORS['text'])
            surface.blit(tip_render, (50, 250))
        
        # Taktik menüsü başlığı
        font = pygame.font.Font(None, FONTS['subheader'])
        if self.battle_ended:
            menu_title = "Savaş Sona Erdi - " + ("ZAFER!" if self.victory else "YENİLGİ")
        else:
            menu_title = "Taktik Seçin (D: Danışman)"
        menu_render = font.render(menu_title, True, COLORS['gold'])
        surface.blit(menu_render, (50, 250))
        
        self.tactics_menu.draw(surface)
        
        # Son eylem sonucu
        if self.last_action_result:
            result_font = pygame.font.Font(None, FONTS['body'])
            result_render = result_font.render(
                self.last_action_result[:90] + "..." if len(self.last_action_result) > 90 else self.last_action_result,
                True, COLORS['text']
            )
            surface.blit(result_render, (50, SCREEN_HEIGHT - 100))
