# -*- coding: utf-8 -*-
"""
Osmanlı Eyalet Yönetim Simülasyonu - İnteraktif Savaş Ekranı
Kuşatma ve büyük savaşlarda taktiksel kararlar + Özel Yetenekler
"""

import pygame
import random
from ui.screen_manager import BaseScreen, ScreenType
from ui.components import Button, Panel, MenuList
from config import COLORS, FONTS, SCREEN_WIDTH, SCREEN_HEIGHT, get_font
from game.systems.warfare import (
    BattleType, BattlePhase, SiegePhase, TerrainType, WeatherType,
    SPECIAL_ABILITIES, SpecialAbilityType, TERRAIN_MODIFIERS, WEATHER_MODIFIERS
)
from game.systems.military import CommanderTrait
from audio.music_manager import get_music_manager, MusicContext


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
        self.combat_log = []
        
        # Düşman komutan profili (Doktrin)
        self.enemy_doctrine = "DENGE"
        self.player_tactic = None
        
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
            self._header_font = get_font(FONTS['header'])
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
        self.combat_log = []
        self.player_tactic = None
        
        # Düşman Komutan Profili Atama (Doktrin)
        doctrines = ['SERDENGECTI', 'MUHENDIS', 'AKINCI_BEYI', 'DENGE']
        self.enemy_doctrine = random.choice(doctrines)
    
    def _setup_tactics_menu(self):
        """Taktik seçeneklerini ayarla - organize menü"""
        self.tactics_menu.clear()
        
        if self.battle_ended:
            self.tactics_menu.add_item(
                "Savaş Alanından Ayrıl (Escape)",
                self._end_battle,
                "escape"
            )
            return
        
        # === KUŞATMA DURUMU ===
        if self.current_battle and hasattr(self.current_battle, 'siege_state') and self.current_battle.siege_state:
            siege = self.current_battle.siege_state
            wall_status = f"Sur: %{siege.wall_integrity}" if siege.wall_integrity < 100 else ""
            
            self.tactics_menu.add_item(
                f"[{siege.get_phase_name().upper()}] {wall_status}",
                None,
                ""
            )
            
            # Aşama ilerletme
            can_advance, reason = siege.can_advance_phase()
            if can_advance:
                self.tactics_menu.add_item(
                    "➤ Sonraki Aşamaya Geç (P)",
                    self._advance_siege_phase,
                    "p"
                )
        
        # === SALDIRI TAKTİKLERİ ===
        # Taktik Önizlemeleri (Forecasting)
        
        self.tactics_menu.add_item(
            "1. Merkez Hücumu: Yüksek hasar, risk. [Savunan düşmana karşı ağır üstünlük sağlar, kanat saldırısına karşı zayıftır.]",
            self._tactic_center_attack,
            "1"
        )
        self.tactics_menu.add_item(
            "2. Kanat Manevrası: Çevik ve dengeli. [Merkez hücumunu ezer geçer, sağlam savunmaya karşı çöker.]",
            self._tactic_flank,
            "2"
        )
        self.tactics_menu.add_item(
            "3. Savunma (Tabur Cengi): Güvenli mevzi. [Kanat süvarilerini parçalar, topçu ve ağır merkez hücumuna karşı kırılgandır.]",
            self._tactic_defend,
            "3"
        )
        self.tactics_menu.add_item(
            "4. Topçu Bombardımanı: Güvenli hasar. [Surları döver ve moral bozar, demir harcar.]",
            self._tactic_artillery,
            "4"
        )
        self.tactics_menu.add_item(
            "5. Sahte Ricat (Turan): Şansa dayalı büyük kumar. [Başarılı olursa orduyu yok eder, başarısızlık felakettir.]",
            self._tactic_feint,
            "5"
        )
        self.tactics_menu.add_item(
            "6. Teslim Çağrısı - Savaşsız zafer şansı.",
            self._tactic_demand_surrender,
            "6"
        )
        
        # Arazi/Hava Uyarıları (Forecasting)
        if self.current_battle:
            terrain_name = {
                TerrainType.PLAINS: "Ova", TerrainType.FOREST: "Orman",
                TerrainType.MOUNTAIN: "Dağ", TerrainType.RIVER: "Nehir",
                TerrainType.FORTRESS: "Kale", TerrainType.DESERT: "Çöl",
                TerrainType.SWAMP: "Bataklık"
            }.get(self.current_battle.terrain, "Bilinmeyen")
            
            weather_name = {
                WeatherType.CLEAR: "Açık", WeatherType.RAIN: "Yağmur",
                WeatherType.SNOW: "Kar", WeatherType.FOG: "Sis",
                WeatherType.STORM: "Fırtına"
            }.get(self.current_battle.weather, "Bilinmeyen")
            
            self.tactics_menu.add_item(
                f"[BİLGİ] Arazi: {terrain_name} | Hava: {weather_name}",
                None,
                ""
            )
            
            cmdr = self.current_battle.attacker_army.commander
            if cmdr:
                trait_names = {
                    'SIEGE_MASTER': "Kuşatmacı",
                    'LOGISTICIAN': "Lojistik Uzmanı",
                    'AGGRESSOR': "Serdengeçti (Agresif)",
                    'TACTICIAN': "Taktisyen",
                    'DEFENDER': "Savunmacı"
                }
                # Handle both Enum and string gracefully
                t_key = cmdr.trait.name if hasattr(cmdr.trait, 'name') else str(cmdr.trait)
                t_name = trait_names.get(t_key, t_key)
                self.tactics_menu.add_item(
                    f"[KOMUTAN] Paşa {cmdr.name} - Yatkınlık: {t_name}",
                    None,
                    ""
                )
        
        # === ÖZEL YETENEKLER ===
        abilities_available = False
        
        if self._can_use_ability(SpecialAbilityType.JANISSARY_VOLLEY):
            abilities_available = True
            self.tactics_menu.add_item(
                "Y: Yeniceri Atesi",
                lambda: self._use_special_ability(SpecialAbilityType.JANISSARY_VOLLEY),
                "y"
            )
        
        if self._can_use_ability(SpecialAbilityType.AKINCI_RAID):
            abilities_available = True
            self.tactics_menu.add_item(
                "A: 🐎 Akıncı Baskını",
                lambda: self._use_special_ability(SpecialAbilityType.AKINCI_RAID),
                "a"
            )
        
        if self._can_use_ability(SpecialAbilityType.CANNON_BARRAGE):
            abilities_available = True
            self.tactics_menu.add_item(
                "B: 💣 Top Bombardımanı",
                lambda: self._use_special_ability(SpecialAbilityType.CANNON_BARRAGE),
                "b"
            )
        
        if self._can_use_ability(SpecialAbilityType.CAVALRY_CHARGE):
            abilities_available = True
            self.tactics_menu.add_item(
                "S: Suvari Sarji",
                lambda: self._use_special_ability(SpecialAbilityType.CAVALRY_CHARGE),
                "s"
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
        
        # Savaş bittiyse sadece sonucu söyle
        if self.battle_ended:
            if self.victory:
                self.audio.speak("Zafer! Savaş sona erdi. Escape tuşuyla çıkın.", interrupt=False)
            else:
                self.audio.speak("Yenilgi. Savaş sona erdi. Escape tuşuyla çıkın.", interrupt=False)
            return
        
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
                
            # F2 - Savaş Kaydı (Combat Log)
            if event.key == pygame.K_F2:
                self._read_combat_log()
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
    
    def _read_combat_log(self):
        """Son turun detaylı özetini oku (F2)"""
        if not self.combat_log:
            self.audio.speak("Henüz savaş raporu yok.", interrupt=True)
            return
        
        last_log = self.combat_log[-1]
        self.audio.speak(last_log, interrupt=True)
    
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
        self.player_tactic = 'center'
        self._process_round_end()
    
    def _tactic_flank(self):
        self.player_tactic = 'flank'
        self._process_round_end()
    
    def _tactic_defend(self):
        self.player_tactic = 'defend'
        self._process_round_end()
    
    def _tactic_artillery(self):
        gm = self.screen_manager.game_manager
        if gm and gm.economy.resources.iron < 50:
            self.audio.speak("Yeterli mühimmat yok! En az 50 demir gerekli.", interrupt=True)
            return
        self.player_tactic = 'artillery'
        self._process_round_end()
    
    def _tactic_feint(self):
        self.player_tactic = 'feint'
        self._process_round_end()
    
    def _tactic_demand_surrender(self):
        self.player_tactic = 'surrender'
        self._process_round_end()
    
    def _can_use_ability(self, ability_type: SpecialAbilityType) -> bool:
        """Özel yetenek kullanılabilir mi?"""
        gm = self.screen_manager.game_manager
        if not gm:
            return False
        
        # Basit kontroller
        if ability_type == SpecialAbilityType.JANISSARY_VOLLEY:
            return gm.military.infantry >= 50
        elif ability_type == SpecialAbilityType.AKINCI_RAID:
            return gm.military.cavalry >= 30
        elif ability_type == SpecialAbilityType.CANNON_BARRAGE:
            return gm.military.artillery_crew >= 10 and gm.economy.resources.iron >= 100
        elif ability_type == SpecialAbilityType.CAVALRY_CHARGE:
            return gm.military.cavalry >= 50
        
        return False
    
    def _use_special_ability(self, ability_type: SpecialAbilityType):
        """Özel yetenek kullan - Sadece seçimi hazırla"""
        ability = SPECIAL_ABILITIES.get(ability_type)
        if not ability:
            return
        
        self.audio.speak(f"{ability.name_tr} için hazırlık yapılıyor...", interrupt=True)
        self.player_tactic = f"special_{ability_type.name}"
        self._process_round_end()
    
    def _advance_siege_phase(self):
        """Kuşatma aşamasını ilerlet"""
        if not self.current_battle or not self.current_battle.siege_state:
            return
        
        siege = self.current_battle.siege_state
        can_advance, reason = siege.can_advance_phase()
        
        if not can_advance:
            self.audio.speak(f"Aşama ilerletilemez: {reason}", interrupt=True)
            return
        
        # Aşama ilerlet
        if siege.phase == SiegePhase.BLOCKADE:
            siege.phase = SiegePhase.BOMBARDMENT
            self.audio.speak(
                "BOMBARDIMAN AŞAMASINA GEÇİLDİ! Artık toplarla surları dövebilirsiniz.",
                interrupt=True
            )
        elif siege.phase == SiegePhase.BOMBARDMENT:
            siege.phase = SiegePhase.ASSAULT
            self.audio.speak(
                "GENEL HÜCUM AŞAMASINA GEÇİLDİ! Son saldırı başlasın!",
                interrupt=True
            )
            # Hücum aşamasında maksimum 3 tur
            self.max_rounds = self.current_round + 3
        
        self._setup_tactics_menu()
        self._update_status_panel()
    
    def _process_round_end(self):
        """Oyuncu taktiğini seçtikten sonra düşman turunu başlat"""
        self.audio.play_game_sound('military', 'march')
        self.audio.speak("Düşman hamle yapıyor...", interrupt=False)
        
        self.is_player_turn = False
        self.enemy_action_pending = True
        self.enemy_turn_timer = 0
        
        # Panelleri güncelle
        self._update_status_panel()
    
    def _check_battle_end(self):
        """Düşman turundan sonra savaş kontrolü"""
        # Yenilgi kontrolü
        if self.player_morale <= 0:
            self.victory = False
            self.battle_ended = True
            self.audio.play_game_sound('military', 'defeat')
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
        
        # Dinamik Müzik - Kriz kontrolü
        if not self.battle_ended:
            if self.player_morale <= 30 or self.enemy_morale <= 30:
                get_music_manager().set_crisis(True)
            else:
                get_music_manager().set_crisis(False)
        
        if self.battle_ended:
            self._setup_tactics_menu()  # "Ayrıl" seçeneğini göster
    
    def _end_battle(self):
        """Savaşı bitir ve sonuçları uygula"""
        gm = self.screen_manager.game_manager
        
        if gm and self.current_battle:
            # Savaşı listeden kaldır
            if self.current_battle in gm.warfare.active_battles:
                gm.warfare.active_battles.remove(self.current_battle)
            
            # Kriz müziğini kapat
            get_music_manager().set_crisis(False)
            
            # Sonuçları uygula
            if self.victory:
                # Zafer ödülleri
                get_music_manager().play_context(MusicContext.VICTORY, force=True)
                loot = random.randint(5000, 15000)
                gm.economy.add_resources(gold=loot)
                gm.diplomacy.sultan_loyalty = min(100, gm.diplomacy.sultan_loyalty + 10)
                gm.military.experience = min(100, gm.military.experience + 15)
                self.audio.speak(f"Zafer! {loot} altın yağma ve padişah sadakati arttı!", interrupt=True)
            else:
                # Yenilgi cezaları (azaltılmış)
                gm.diplomacy.sultan_loyalty = max(0, gm.diplomacy.sultan_loyalty - 5)
                gm.military.morale = max(0, gm.military.morale - 10)
        
        # Ana ekrana dön
        self.screen_manager.change_screen(ScreenType.PROVINCE_VIEW)
    
    def update(self, dt: float):
        """Düşman turunu işle"""
        if self.enemy_action_pending and not self.battle_ended:
            self.enemy_turn_timer += dt
            
            # 1.5 saniye bekle sonra savaş hesaplansın
            if self.enemy_turn_timer >= 1.5:
                # Düşman taktiğini seç
                enemy_tactic = self._get_enemy_tactic_by_doctrine()
                # Savaştır
                self._resolve_tactics(self.player_tactic, enemy_tactic)
                
                self.enemy_turn_timer = 0
                self.enemy_action_pending = False
                self.is_player_turn = True
                self._check_battle_end()
            
            # Dinamik Müzik - Kriz kontrolü
            if not self.battle_ended:
                if self.player_morale <= 30 or self.enemy_morale <= 30:
                    get_music_manager().set_crisis(True)
                else:
                    get_music_manager().set_crisis(False)
    
    def _get_enemy_tactic_by_doctrine(self) -> str:
        """Düşmanın belirlediği doktrine göre hamle seçimi"""
        choices = []
        if self.enemy_doctrine == 'SERDENGECTI': # Agresif
            choices = ['center', 'center', 'center', 'flank', 'flank', 'defend']
        elif self.enemy_doctrine == 'MUHENDIS': # Savunması Topçu
            choices = ['defend', 'defend', 'defend', 'artillery', 'center']
        elif self.enemy_doctrine == 'AKINCI_BEYI': # Manevrası
            choices = ['flank', 'flank', 'feint', 'center', 'defend']
        else: # DENGE
            choices = ['center', 'flank', 'defend', 'artillery', 'feint']
            
        # Eğer morali çok düşükse savunma eğilimi artsın
        if self.enemy_morale < 30:
            choices.extend(['defend', 'defend', 'surrender'])
            
        return random.choice(choices)

    def _resolve_tactics(self, pt: str, et: str):
        """Seçilen iki taktiği çaprazlaştırarak Taş-Kağıt-Makas matrisi uygula"""
        
        if pt == 'surrender':
            surrender_chance = (100 - self.enemy_morale) / 100
            if random.random() < surrender_chance or et == 'surrender':
                self.victory = True
                self.battle_ended = True
                self.last_action_result = "ZAFER! Düşman teslim oldu!"
                self.combat_log.append(f"Tur {self.current_round}: Düşman teslimiyet çağrımızı kabul etti. Savaş sona erdi.")
                return
            else:
                self.player_morale -= random.randint(10, 20)
                self.last_action_result = "Teslim çağrısı reddedildi! Düşman savaşa devam ediyor."
                self.combat_log.append(f"Tur {self.current_round}: Teslim çağrısı yaptık ancak düşman reddetti. Moralimiz bozuldu.")
                return

        # Savaş Çarpanları
        p_dmg_mult = 1.0 # Player damage multiplier
        e_dmg_mult = 1.0 # Enemy damage multiplier
        
        # Taş-Kağıt-Makas: Merkez(Taş) > Savunma(Makas) > Kanat(Kağıt) > Merkez(Taş)
        # Merkez Hücumu, Tabur Cengini ezer
        # Tabur Cengi (Savunma), Süvari Kanat Şarjını ezer
        # Süvari Kanat Şarjı, Merkez Hücumu ezer
        
        tactic_names = {
            'center': 'Merkez Hücumu',
            'flank': 'Kanat Manevrası',
            'defend': 'Savunma (Tabur Cengi)',
            'artillery': 'Topçu Ateşi',
            'feint': 'Sahte Ricat'
        }
        
        is_special = pt.startswith("special_")
        ability = None
        ability_type = None
        if is_special:
            ability_name = pt.replace("special_", "")
            try:
                ability_type = SpecialAbilityType[ability_name]
                ability = SPECIAL_ABILITIES.get(ability_type)
            except KeyError:
                pass
                
        player_tactic_name = ability.name_tr if ability else tactic_names.get(pt, pt)
        matchup_desc = f"Biz {player_tactic_name} yaptık, düşman ise {tactic_names.get(et, et)} ile karşılık verdi. "
        
        # Cephe Lojistiği (Her tur zahire tüketimi)
        gm = self.screen_manager.game_manager
        if gm:
            supply_cost = 10
            # Lojistikçi Paşa varsa tüketim yarıya düşsün veya sıfırlansın
            if self.current_battle and self.current_battle.attacker_army.commander:
                if self.current_battle.attacker_army.commander.trait == CommanderTrait.LOGISTICIAN:
                    supply_cost = 0
            
            if gm.economy.resources.food >= supply_cost:
                gm.economy.resources.food -= supply_cost
            else:
                self.player_morale -= 15
                matchup_desc += "(AÇLIK: Erzak tükendiği için ordunun morali hızla çöküyor!) "
        
        if pt == 'center' and et == 'defend':
            p_dmg_mult = 1.5; e_dmg_mult = 0.5
            matchup_desc += "Ağır taarruzumuz düşman savunma hattını (Tabur Cengini) yarmayı başardı! "
        elif pt == 'defend' and et == 'flank':
            p_dmg_mult = 1.5; e_dmg_mult = 0.5
            matchup_desc += "Düşman kanat manevrası yaparken savunma hatlarımızdaki top ateşine tutuldu! "
        elif pt == 'flank' and et == 'center':
            p_dmg_mult = 1.5; e_dmg_mult = 0.5
            matchup_desc += "Düşman merkezden hantalca gelirken biz süvarilerle onları kuşattık! "
        # Düşman üstünse
        elif et == 'center' and pt == 'defend':
            e_dmg_mult = 1.5; p_dmg_mult = 0.5
            matchup_desc += "Düşmanın ağır merkez hücumu savunma hatlarımızı kırdı geçti. "
        elif et == 'defend' and pt == 'flank':
            e_dmg_mult = 1.5; p_dmg_mult = 0.5
            matchup_desc += "Kanatlardan sarkıp saldırmak istedik ama düşman topçu tabyalarına (Tabur Cengi) tosladık. "
        elif et == 'flank' and pt == 'center':
            e_dmg_mult = 1.5; p_dmg_mult = 0.5
            matchup_desc += "Merkezden ilerlerken düşman süvarisi kanatlarımızı sardı. "
            
        # Arazi ve Hava Etkileri
        if self.current_battle:
            terrain = self.current_battle.terrain
            weather = self.current_battle.weather
            
            if terrain in [TerrainType.MOUNTAIN, TerrainType.FOREST, TerrainType.SWAMP]:
                if pt == 'flank':
                    p_dmg_mult -= 0.4
                    matchup_desc += "(Engebeli/Ağaçlık arazi süvarilerimizi yavaşlattı) "
                if et == 'flank':
                    e_dmg_mult -= 0.4
            
            if terrain == TerrainType.PLAINS:
                if pt == 'flank':
                    p_dmg_mult += 0.2
                if et == 'flank':
                    e_dmg_mult += 0.2
                    
            if weather in [WeatherType.RAIN, WeatherType.STORM]:
                if pt == 'artillery':
                    p_dmg_mult -= 0.3
                    matchup_desc += "(Yağışlı hava top atışlarını zayıflattı) "
                if et == 'artillery':
                    e_dmg_mult -= 0.3
                    
            if weather == WeatherType.SNOW:
                # Kış şartları yıpranma (attrition) yapar
                attrition_morale = 5
                attrition_cas = random.randint(30, 80)
                
                # Paşa Lojistikçi ise kış hasarını engeller
                cmdr = self.current_battle.attacker_army.commander
                if cmdr and cmdr.trait == CommanderTrait.LOGISTICIAN:
                    attrition_morale = 0
                    attrition_cas = 0
                    matchup_desc += f" (Paşa {cmdr.name}'nin dâhiyane lojistik ağı sayesinde kışın dondurucu soğuğundan etkilenmedik!) "
                else:
                    self.player_morale -= attrition_morale
                    self.player_casualties += attrition_cas
                    matchup_desc += f"(Kış aylarında çetin savaş {attrition_cas} şehit ve {attrition_morale} moral kaybına yol açtı!) "
                    
        # Komutan Yetenekleri (Paşalar)
        if self.current_battle and self.current_battle.attacker_army.commander:
            cmdr = self.current_battle.attacker_army.commander
            if cmdr.trait == CommanderTrait.AGGRESSOR and pt == 'center':
                p_dmg_mult += 0.4
                e_dmg_mult += 0.3  # Kendi kayıplarımız da artar
                matchup_desc += f"[Paşa {cmdr.name}] Serdengeçti hücumuyla safları yardık ama çok kayıp verdik! "
            elif cmdr.trait == CommanderTrait.DEFENDER and pt == 'defend':
                e_dmg_mult -= 0.4  # Bize gelen hasar azalır
                matchup_desc += f"[Paşa {cmdr.name}] Savunmacı doktriniyle kayıpları asgariye indirdik. "
            elif cmdr.trait == CommanderTrait.TACTICIAN:
                p_dmg_mult += 0.15 # Genel taktik bonusu
            elif cmdr.trait == CommanderTrait.SIEGE_MASTER and pt == 'artillery':
                p_dmg_mult += 0.4
                matchup_desc += f"[Paşa {cmdr.name}] Kuşatmacı topyekün bombardımanı etkili oldu. "
        
        # Topçu 
        if pt == 'artillery':
            gm = self.screen_manager.game_manager
            if gm: gm.economy.resources.iron -= 50
            p_dmg_mult = 1.2; e_dmg_mult = 0.8
        
        # Çözümleme ve Ses Efekti (Stereo Panning)
        base_e_dmg = random.randint(15, 30)
        
        # Pan ayarları: -1.0 Sol Kulak, 1.0 Sağ Kulak
        # Oyuncu flank (kanat): Sol ağırlıklı (-0.6)
        # Düşman flank: Sağ ağırlıklı (0.6)
        # Merkez/Topçu: Tam ortadan (0.0)
        
        player_pan = -0.6 if pt == 'flank' else 0.0
        enemy_pan = 0.6 if et == 'flank' else 0.0
        
        # Eğer özel yetenekse pan ona göre yapılsın
        if is_special and ability:
            gm = self.screen_manager.game_manager
            
            # Ses
            ability_sounds = {
                SpecialAbilityType.JANISSARY_VOLLEY: ('military', 'arrow'),
                SpecialAbilityType.AKINCI_RAID: ('military', 'charge'),
                SpecialAbilityType.CANNON_BARRAGE: ('military', 'cannon'),
                SpecialAbilityType.CAVALRY_CHARGE: ('military', 'charge'),
            }
            sound = ability_sounds.get(ability_type)
            if sound:
                self.audio.play_game_sound_panned(sound[0], sound[1], pan=player_pan)
            
            # Kaynak tüketimi
            if ability_type == SpecialAbilityType.CANNON_BARRAGE and gm:
                gm.economy.resources.iron -= 100
                
            if self.current_battle:
                self.current_battle.abilities_used.append(ability.name_tr)
                
            # Yetenek hasarı
            final_p_dmg = ability.morale_damage + random.randint(-5, 5)
            e_cas = int(ability.damage_multiplier * random.randint(60, 120))
            
            if ability_type == SpecialAbilityType.JANISSARY_VOLLEY:
                matchup_desc += "Yoğun tüfek volisi düşmanı taradı! "
            elif ability_type == SpecialAbilityType.AKINCI_RAID:
                matchup_desc += "Hafif süvariler düşman gerisine sızıp panik yarattı! "
            elif ability_type == SpecialAbilityType.CANNON_BARRAGE:
                matchup_desc += "Tüm toplar ateş açıp suru sarstı! "
                if self.current_battle and self.current_battle.siege_state:
                    self.current_battle.siege_state.wall_integrity -= random.randint(10, 25)
            elif ability_type == SpecialAbilityType.CAVALRY_CHARGE:
                matchup_desc += "Ağır süvariler düşman hattına dalıp kırdı! "
                
            final_e_dmg = int(base_e_dmg * e_dmg_mult)
            p_cas = int(random.randint(40, 100) * e_dmg_mult)
            
        else:
            # Standart taktik hasarı
            base_p_dmg = random.randint(15, 30)
            final_p_dmg = int(base_p_dmg * p_dmg_mult)
            final_e_dmg = int(base_e_dmg * e_dmg_mult)
            
            p_cas = int(random.randint(40, 100) * e_dmg_mult)
            e_cas = int(random.randint(40, 100) * p_dmg_mult)
            
            if pt == 'artillery':
                self.audio.play_game_sound_panned('military', 'cannon', pan=player_pan)
            else:
                self.audio.play_game_sound_panned('military', 'sword_clash', pan=player_pan)
                
            # Düşmanın karşı saldırı sesi (Gecikmeli veya beraber)
            if et == 'artillery':
                self.audio.play_game_sound_panned('military', 'cannon', pan=enemy_pan)
            else:
                self.audio.play_game_sound_panned('military', 'sword_clash', pan=enemy_pan)
        
        # Sonuçları matrise dök
        self.enemy_morale -= final_p_dmg
        self.player_morale -= final_e_dmg
        
        self.player_casualties += p_cas
        self.enemy_casualties += e_cas
        
        # Sonuç metni
        log_entry = f"Tur {self.current_round} Raporu: {matchup_desc} Düşmana {final_p_dmg} moral hasarı, {e_cas} zayiat verdik; {final_e_dmg} moral hasarı ve {p_cas} şehit verdik."
        self.combat_log.append(log_entry)
        self.last_action_result = f"{matchup_desc} Sonuç: Bize {final_e_dmg} moral hasarı, düşmana {final_p_dmg} moral hasarı."
        self.audio.speak(self.last_action_result, interrupt=True)
    
    def draw(self, surface: pygame.Surface):
        # Başlık
        header_font = self.get_header_font()
        if self.current_battle:
            title = f"{self.current_battle.defender_name} KUSATMASI - TUR {self.current_round}"
        else:
            title = "SAVAS"
        
        title_render = header_font.render(title, True, COLORS['gold'])
        surface.blit(title_render, (50, 30))
        
        # Durum paneli
        self.status_panel.draw(surface)
        
        # Danışman tavsiyesi
        if self.advisor_tip:
            font = get_font(FONTS['body'])
            tip_render = font.render(self.advisor_tip[:80], True, COLORS['text'])
            surface.blit(tip_render, (50, 250))
        
        # Taktik menüsü başlığı
        font = get_font(FONTS['subheader'])
        if self.battle_ended:
            menu_title = "Savaş Sona Erdi - " + ("ZAFER!" if self.victory else "YENİLGİ")
        else:
            menu_title = "Taktik Seçin (D: Danışman)"
        menu_render = font.render(menu_title, True, COLORS['gold'])
        surface.blit(menu_render, (50, 250))
        
        self.tactics_menu.draw(surface)
        
        # Son eylem sonucu
        if self.last_action_result:
            result_font = get_font(FONTS['body'])
            result_render = result_font.render(
                self.last_action_result[:90] + "..." if len(self.last_action_result) > 90 else self.last_action_result,
                True, COLORS['text']
            )
            surface.blit(result_render, (50, SCREEN_HEIGHT - 100))
