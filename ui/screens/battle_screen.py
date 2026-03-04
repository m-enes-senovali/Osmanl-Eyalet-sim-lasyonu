# -*- coding: utf-8 -*-
"""
Osmanlı Eyalet Yönetim Simülasyonu - İnteraktif Savaş Ekranı
Kuşatma ve büyük savaşlarda taktiksel kararlar + Özel Yetenekler
"""

import pygame
import random
from ui.screen_manager import BaseScreen, ScreenType
from ui.components import Button, Panel, MenuList
from ui.visual_effects import GradientRenderer, ScreenShake, FlashEffect
from config import COLORS, FONTS, SCREEN_WIDTH, SCREEN_HEIGHT, get_font
from game.systems.warfare import (
    BattleType, BattlePhase, SiegePhase, TerrainType, WeatherType,
    SPECIAL_ABILITIES, SpecialAbilityType, TERRAIN_MODIFIERS, WEATHER_MODIFIERS
)
from game.systems.military import CommanderTrait
from audio.music_manager import get_music_manager, MusicContext


class BattleScreen(BaseScreen):
    """İnteraktif savaş ekranı - kuşatma, akın ve deniz akını için"""
    
    def __init__(self, screen_manager):
        super().__init__(screen_manager)
        
        # Savaş durumu
        self.current_battle = None
        self.battle_mode = 'siege'  # 'siege', 'raid', 'naval'
        self.current_round = 1
        self.max_rounds = 5  # Kuşatma: 5, Akın/Deniz: 3
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
        
        # Savaşa konuşlandırılmış toplar (moda göre filtrelenir)
        self.deployed_cannons = []
        self._artillery_result = None
        
        # Görsel efektler
        self._gradient = GradientRenderer.get_gradient('battle')
        self._shake = ScreenShake()
        self._flash = FlashEffect()
    
    def get_header_font(self):
        if self._header_font is None:
            self._header_font = get_font(FONTS['header'])
        return self._header_font
    
    def set_battle_data(self, battle_data: dict):
        """Dışarıdan savaş verisi ayarla"""
        self.external_battle_data = battle_data
        # Modu belirle
        if battle_data:
            self.battle_mode = battle_data.get('battle_type', 'siege')
            self.player_morale = battle_data.get('attacker_army', {}).get('morale', 100)
            self.enemy_morale = battle_data.get('defender_army', {}).get('morale', 80)
    
    def on_enter(self):
        """Savaş ekranına girildiğinde"""
        self._initialize_battle()
        self._setup_tactics_menu()
        self._update_status_panel()
        # Savaş müziğini hemen başlat
        try:
            get_music_manager().play_context(MusicContext.BATTLE, force=True)
        except Exception:
            pass
    
    def _initialize_battle(self):
        """Aktif savaşı başlat"""
        gm = self.screen_manager.game_manager
        
        self.is_defending = False
        if gm and hasattr(gm, 'current_invasion') and gm.current_invasion:
            self.is_defending = True
            
        if not self.is_defending and (not gm or not gm.warfare.active_battles):
            self.battle_ended = True
            return
            
        self.current_battle = None
        
        if not self.is_defending:
            # Battle moduna göre doğru savaşı bul
            target_types = {
                'siege': BattleType.SIEGE,
                'raid': BattleType.RAID,
                'naval': BattleType.NAVAL_RAID,
            }
            target_type = target_types.get(self.battle_mode, BattleType.SIEGE)
            
            for battle in gm.warfare.active_battles:
                if battle.battle_type == target_type and getattr(battle, 'combat_ready', False):
                    self.current_battle = battle
                    break
            
            if not self.current_battle:
                self.battle_ended = True
                return
            
            self.player_morale = self.current_battle.attacker_army.morale
            self.enemy_morale = self.current_battle.defender_army.morale
        else:
            # İstila için değerleri kur
            self.player_morale = 100
            self.enemy_morale = 100
            if gm:
                self.player_morale += gm.construction.get_defense_bonus() * 10
            
        self.current_round = 1
        self.player_casualties = 0
        self.enemy_casualties = 0
        self.battle_ended = False
        self.victory = False
        self.combat_log = []
        self.player_tactic = None
        
        # Moda göre tur sayısı
        if self.battle_mode in ('raid', 'naval'):
            self.max_rounds = 3
        else:
            self.max_rounds = 5
            
        # Düşman Komutan Profili Atama (Doktrin)
        doctrines = ['SERDENGECTI', 'MUHENDIS', 'AKINCI_BEYI', 'DENGE']
        self.enemy_doctrine = random.choice(doctrines)
        
        # Topları moda göre filtrele
        self.deployed_cannons = []
        gm_art = self.screen_manager.game_manager
        if gm_art and hasattr(gm_art, 'artillery') and gm_art.artillery.cannons:
            if self.battle_mode == 'raid':
                # Akında top yok — hafif akıncı birliği
                self.deployed_cannons = []
            elif self.battle_mode == 'naval':
                # Denizde sadece deniz topları (is_naval=True)
                from game.systems.artillery import CANNON_DEFINITIONS
                self.deployed_cannons = [
                    c for c in gm_art.artillery.cannons
                    if CANNON_DEFINITIONS[c.cannon_type].is_naval and c.condition > 0
                ]
            else:
                # Kuşatma/kara: tüm kara topları (is_naval=False)
                from game.systems.artillery import CANNON_DEFINITIONS
                self.deployed_cannons = [
                    c for c in gm_art.artillery.cannons
                    if not CANNON_DEFINITIONS[c.cannon_type].is_naval and c.condition > 0
                ]
    
    def _setup_tactics_menu(self):
        """Taktik seçeneklerini ayarla - moda göre farklı"""
        self.tactics_menu.clear()
        
        if self.battle_ended:
            self.tactics_menu.add_item(
                "Escape: Ayrıl",
                self._end_battle,
                "escape"
            )
            return
        
        # Savunma modu
        if getattr(self, 'is_defending', False):
            # Savunma her modda aynı
            pass  # Alttaki ortak taktikler eklenir
        
        # DENİZ AKINI MODU — Gemi taktikleri
        if self.battle_mode == 'naval':
            self.tactics_menu.add_item(
                "1. Rampa: Gemiye borda atıp göğüs göğüse savaş. [Manevra yapana karşı üstün, kaçana karşı zayıf.]",
                lambda: self._naval_tactic('boarding'),
                "1"
            )
            self.tactics_menu.add_item(
                "2. Bordoya Ateş: Top atışıyla düşman gemisini batmaya zorla. [Kaçana karşı üstün, rampa yapana karşı zayıf.]",
                lambda: self._naval_tactic('broadside'),
                "2"
            )
            self.tactics_menu.add_item(
                "3. Manevra: Gemi konumunu değiştir, avantajlı açı yakala. [Rampaya karşı üstün, top atışına karşı zayıf.]",
                lambda: self._naval_tactic('maneuver'),
                "3"
            )
            self.tactics_menu.add_item(
                "4. Teslim Çağrısı - Savaşsız zafer şansı.",
                self._tactic_demand_surrender,
                "4"
            )
        else:
            # === KARA SALDIRI TAKTİKLERİ (Akın + Kuşatma ortak) ===
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
            # Topçu butonu — sadece konuşlandırılmış top varsa (akında gizli)
            if self.battle_mode != 'raid' and self.deployed_cannons:
                barut_cost = sum(c.get_definition().gunpowder_per_shot for c in self.deployed_cannons)
                ammo_name = self.deployed_cannons[0].get_ammo_multipliers().get('name', 'Bilinmeyen') if self.deployed_cannons else ''
                art_label = (
                    f"4. Topçu Ateşi ({len(self.deployed_cannons)} top, {barut_cost} barut, "
                    f"Mühimmat: {ammo_name}): [M tuşu: Mühimmat değiştir]"
                )
                self.tactics_menu.add_item(
                    art_label,
                    self._tactic_artillery,
                    "4"
                )
                self.tactics_menu.add_item(
                    "5. Sahte Ricat (Turan): Şansa dayalı büyük kumar. [Başarılı olursa orduyu yok eder, başarısızlık felakettir.]",
                    self._tactic_feint,
                    "5"
                )
            elif self.battle_mode != 'raid':
                # Top yok ama akın da değil — bilgi göster
                self.tactics_menu.add_item(
                    "4. Topçu Ateşi: Uygun top yok!",
                    None,
                    ""
                )
                self.tactics_menu.add_item(
                    "5. Sahte Ricat (Turan): Şansa dayalı büyük kumar.",
                    self._tactic_feint,
                    "5"
                )
            else:
                # Akın modunda topçu yok, sahte ricatı 4. sıraya al
                self.tactics_menu.add_item(
                    "4. Sahte Ricat (Turan): Şansa dayalı büyük kumar. [Başarılı olursa orduyu yok eder, başarısızlık felakettir.]",
                    self._tactic_feint,
                    "4"
                )
            teslim_no = "5" if self.battle_mode == 'raid' else "6"
            self.tactics_menu.add_item(
                f"{teslim_no}. Teslim Çağrısı - Savaşsız zafer şansı.",
                self._tactic_demand_surrender,
                teslim_no
            )
        # Savaş devam ederken kaçış tuşu (Sadece Saldıran Bizsek)
        if not self.is_defending and not getattr(self, 'battle_ended', False):
             self.tactics_menu.add_item(
                "[GERİ ÇEKİL] Savaş Alanından Ayrıl (Escape)",
                self._end_battle,
                "escape"
            )
        
        # === KUŞATMA DURUMU (Sadece siege modunda) ===
        if self.battle_mode == 'siege' and self.current_battle and hasattr(self.current_battle, 'siege_state') and self.current_battle.siege_state:
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
            
            # Abluka fazında özel buton
            if siege.phase == SiegePhase.BLOCKADE:
                self.tactics_menu.add_item(
                    "Abluka Uygula — Erzak kesmeye devam et",
                    self._tactic_blockade,
                    "b"
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
        
        # === ÖZEL YETENEKLER (Kara modlarında) ===
        abilities_available = False
        
        if self.battle_mode != 'naval':
            if self._can_use_ability(SpecialAbilityType.JANISSARY_VOLLEY):
                abilities_available = True
                self.tactics_menu.add_item(
                    "Y: Yeniçeri Ateşi",
                    lambda: self._use_special_ability(SpecialAbilityType.JANISSARY_VOLLEY),
                    "y"
                )
            
            if self._can_use_ability(SpecialAbilityType.AKINCI_RAID):
                abilities_available = True
                self.tactics_menu.add_item(
                    "A: Akıncı Baskını",
                    lambda: self._use_special_ability(SpecialAbilityType.AKINCI_RAID),
                    "a"
                )
            
            if self._can_use_ability(SpecialAbilityType.CANNON_BARRAGE):
                abilities_available = True
                self.tactics_menu.add_item(
                    "B: Top Bombardımanı",
                    lambda: self._use_special_ability(SpecialAbilityType.CANNON_BARRAGE),
                    "b"
                )
            
            if self._can_use_ability(SpecialAbilityType.CAVALRY_CHARGE):
                abilities_available = True
                self.tactics_menu.add_item(
                    "S: Süvari Şarjı",
                    lambda: self._use_special_ability(SpecialAbilityType.CAVALRY_CHARGE),
                    "s"
                )
            
        # Savaş ve Teslimiyet (Savunan ise ekleme)
        if getattr(self, 'is_defending', False):
             self.tactics_menu.add_item(
                "0. Şehrin Anahtarlarını Ver ve Teslim Ol (Oyunu Kaybetme Riski)",
                self._tactic_surrender,
                "0"
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
        mode_names = {'siege': 'Kuşatma', 'raid': 'Akın', 'naval': 'Deniz Akını'}
        mode_name = mode_names.get(self.battle_mode, 'Savaş')
        self.audio.announce_screen_change(f"{mode_name} Meydanı")
        
        # Savaş bittiyse sadece sonucu söyle
        if self.battle_ended:
            if self.victory:
                self.audio.speak("Zafer! Savaş sona erdi. Escape tuşuyla çıkın.", interrupt=False)
            else:
                self.audio.speak("Yenilgi. Savaş sona erdi. Escape tuşuyla çıkın.", interrupt=False)
            return
        
        if self.current_battle or getattr(self, 'is_defending', False):
            target_name = self.current_battle.defender_name if self.current_battle else getattr(self.screen_manager.game_manager, 'current_invasion', {}).get('invader', 'Düşman')
            
            if self.is_defending:
                context_str = f"Şehrimiz {target_name} tarafından kuşatılıyor."
            else:
                context_str = f"{target_name} {mode_name.lower()}ı."
            
            self.audio.speak(
                f"{context_str} "
                f"Tur {self.current_round}, toplam {self.max_rounds} tur. "
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
            
            # M - Mühimmat değiştir
            if event.key == pygame.K_m and not self.battle_ended:
                self._cycle_ammo()
                return True
            
            # ESC - Savaş bittiyse çık
            if event.key == pygame.K_ESCAPE and self.battle_ended:
                self._end_battle()
                return True
        
        return False
    
    def _announce_status(self):
        """Savaş durumunu duyur"""
        if not self.current_battle and not getattr(self, 'is_defending', False):
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
        """Topçu taktiği — konuşlandırılmış top yoksa engelle"""
        if not self.deployed_cannons:
            self.audio.speak("Bu savaşta kullanılabilir top yok!", interrupt=True)
            return
        
        gm = self.screen_manager.game_manager
        if not gm:
            return
        
        # Barut kontrolü
        gunpowder_needed = sum(c.get_definition().gunpowder_per_shot for c in self.deployed_cannons)
        if gm.economy.resources.gunpowder < gunpowder_needed:
            self.audio.speak(
                f"Yetersiz barut! {gunpowder_needed} barut gerekli, "
                f"{gm.economy.resources.gunpowder} mevcut.",
                interrupt=True
            )
            return
        
        self._fire_artillery_and_resolve()
    
    def _fire_artillery_and_resolve(self):
        """Konuşlandırılmış topları ateşle, kaynakları harca"""
        gm = self.screen_manager.game_manager
        if not gm or not self.deployed_cannons:
            return
        
        combat_type = 'siege' if self.battle_mode == 'siege' else 'field'
        
        # Sadece konuşlandırılmış topları ateşle
        result = gm.artillery.fire_subset(self.deployed_cannons, combat_type)
        
        # Barut tüketimi
        if result['gunpowder_used'] > 0:
            gm.economy.resources.gunpowder = max(0, 
                gm.economy.resources.gunpowder - result['gunpowder_used'])
        
        # Demir tüketimi (mühimmat bazlı)
        iron_used = sum(c.get_ammo_multipliers().get('iron_cost', 0) 
                       for c in self.deployed_cannons if c.condition > 0)
        if iron_used > 0:
            gm.economy.resources.iron = max(0, gm.economy.resources.iron - iron_used)
        
        # Patlayan topları deployed listesinden de kaldır
        if result['bursts'] > 0:
            burst_msg = f"DİKKAT: {', '.join(result['burst_names'])} patladı!"
            self.audio.speak(burst_msg, interrupt=True)
            self.deployed_cannons = [c for c in self.deployed_cannons if c.condition > 0]
        
        self._artillery_result = result
        self.player_tactic = 'artillery'
        self._process_round_end()
    
    def _cycle_ammo(self):
        """M tuşu: Konuşlandırılmış topların mühimmatını döngüsel değiştir"""
        if not self.deployed_cannons:
            self.audio.speak("Aktif top yok.", interrupt=True)
            return
        
        from game.systems.artillery import AmmoType, AMMO_MULTIPLIERS
        ammo_order = [AmmoType.STONE_BALL, AmmoType.IRON_BALL, AmmoType.GRAPESHOT,
                     AmmoType.INCENDIARY, AmmoType.CHAIN_SHOT]
        
        # Mevcut mühimmatı al
        current_ammo = self.deployed_cannons[0].get_ammo_type()
        try:
            idx = ammo_order.index(current_ammo)
            next_ammo = ammo_order[(idx + 1) % len(ammo_order)]
        except ValueError:
            next_ammo = AmmoType.STONE_BALL
        
        # Tüm konuşlandırılmış toplara uygula
        for cannon in self.deployed_cannons:
            cannon.selected_ammo = next_ammo.value
        
        # Mühimmat bilgisini duyur
        ammo_info = AMMO_MULTIPLIERS[next_ammo]
        self.audio.speak(
            f"Mühimmat değiştirildi: {ammo_info['name']}. {ammo_info['description']}",
            interrupt=True
        )
        
        # Taktik menüsünü yeniden oluştur (yeni mühimmat bilgisi için)
        self._setup_tactics_menu()
    
    def _tactic_feint(self):
        self.player_tactic = 'feint'
        self._process_round_end()
    
    def _tactic_blockade(self):
        """Abluka taktiği — kuşatmada erzak kesme"""
        self.player_tactic = 'blockade'
        self.audio.speak("Abluka devam ediyor. Düşmanın erzakı kesiliyor.", interrupt=True)
        self._process_round_end()
    
    def _tactic_demand_surrender(self):
        self.player_tactic = 'surrender'
        self._process_round_end()
    
    def _naval_tactic(self, tactic: str):
        """Deniz taktiği seç — kara taktiklerine eşleştir"""
        # Deniz taktikleri kara matrisine eşlenir:
        # boarding (rampa) = center (göğüs göğüse)
        # broadside (top ateşi) = artillery
        # maneuver (manevra) = flank (kanat)
        naval_to_land = {
            'boarding': 'center',
            'broadside': 'artillery',
            'maneuver': 'flank',
        }
        self.player_tactic = naval_to_land.get(tactic, 'center')
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
    
    def _tactic_surrender(self):
        """Şehri AI'a teslim et (Sadece Savunmadayken)"""
        if getattr(self, 'is_defending', False):
            self.victory = False
            self.battle_ended = True
            
            # Ağır cezalar
            self.audio.speak("Kalenin anahtarlarını düşmana teslim ettik. Büyük bir hezimet!", interrupt=True)
            self.combat_log.append(f"Tur {self.current_round}: Şartlı teslimiyet kabul edildi, şehir yağmalandı.")
            self._end_battle()
            
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
        
        if gm and (self.current_battle or getattr(self, 'is_defending', False)):
            # Savaşı listeden kaldır
            if self.current_battle in gm.warfare.active_battles:
                gm.warfare.active_battles.remove(self.current_battle)
            
            # Savaş tarihçesine ekle
            if self.current_battle:
                gm.warfare.war_history.append({
                    'target': self.current_battle.defender_name,
                    'type': self.current_battle.battle_type.value,
                    'victory': self.victory,
                    'terrain': self.current_battle.terrain.value,
                    'weather': self.current_battle.weather.value
                })
            
            # Kriz müziğini kapat
            get_music_manager().set_crisis(False)
            
            # Asker kayıplarını MilitarySystem'e uygula
            if self.player_casualties > 0:
                gm.military.apply_casualties(self.player_casualties)
            
            # Savunma Savaşıysa Farklı Sonuçlar Uygula
            if getattr(self, 'is_defending', False):
                if self.victory:
                    get_music_manager().play_context(MusicContext.VICTORY, force=True)
                    gm.diplomacy.sultan_loyalty = min(100, gm.diplomacy.sultan_loyalty + 20)
                    gm.military.experience = min(100, gm.military.experience + 20)
                    self.audio.speak(f"ZAFER! Kuşatmayı yardık ve düşmanı topraklarımızdan attık! Padişah bizden razı olsun.", interrupt=True)
                else:
                    loot_lost = int(gm.economy.resources.gold * 0.4)
                    gm.economy.spend(gold=loot_lost)
                    gm.diplomacy.sultan_loyalty = max(0, gm.diplomacy.sultan_loyalty - 30)
                    gm.military.morale = max(0, gm.military.morale - 30)
                    gm.population.unrest = min(100, gm.population.unrest + 25)
                    self.audio.speak(f"HEZİMET! Eyaletimiz düştü, hazinemizden {loot_lost} altın yağmalandı ve halk isyanın eşiğinde!", interrupt=True)
                gm.current_invasion = None
            
            # Akın veya Deniz Akını Sonu
            elif self.battle_mode in ('raid', 'naval'):
                is_naval = self.battle_mode == 'naval'
                target_name = self.current_battle.defender_name if self.current_battle else 'Bilinmeyen'
                
                # Yağma hesapla
                loot_gold = 0
                loot_food = 0
                if self.victory:
                    loot_gold = random.randint(500, 2000)
                    loot_food = random.randint(100, 500)
                    if is_naval:
                        loot_gold = int(loot_gold * 1.5)
                    gm.economy.add_resources(gold=loot_gold, food=loot_food)
                    gm.military.experience = min(100, gm.military.experience + 5)
                    get_music_manager().play_context(MusicContext.VICTORY, force=True)
                    self.audio.speak(f"ZAFER! {loot_gold} altın ve {loot_food} zahire yağma ettik!", interrupt=True)
                else:
                    gm.military.morale = max(0, gm.military.morale - 10)
                    gm.military.experience = min(100, gm.military.experience + 2)
                    self.audio.speak("Akın başarısız oldu. Geri çekiliyoruz.", interrupt=True)
                
                # Deniz akınında gemi hasarı
                if is_naval and hasattr(gm, 'naval'):
                    damage_roll = random.randint(10, 30)
                    if not self.victory:
                        damage_roll = int(damage_roll * 1.5)
                    warships = [s for s in gm.naval.ships if s.get_definition().is_warship]
                    for ship in warships:
                        dmg = int(damage_roll * random.uniform(0.5, 1.5))
                        ship.health -= dmg
                        if ship.health <= 0:
                            gm.naval.ships.remove(ship)
                            gm.naval.ships_lost += 1
                
                # Akın raporu artık oluşturulmaz — interaktif savaş ekranı yeterli
                # (Eski hikayeli akın raporu devre dışı bırakıldı)
            
            else:
                # Normal Kuşatma Sonu (Saldıran Biziz)
                if self.victory:
                    get_music_manager().play_context(MusicContext.VICTORY, force=True)
                    loot = random.randint(5000, 15000)
                    gm.economy.add_resources(gold=loot)
                    gm.diplomacy.sultan_loyalty = min(100, gm.diplomacy.sultan_loyalty + 10)
                    gm.military.experience = min(100, gm.military.experience + 15)
                    self.audio.speak(f"Zafer! {loot} altın yağma ve padişah sadakati arttı!", interrupt=True)
                else:
                    gm.diplomacy.sultan_loyalty = max(0, gm.diplomacy.sultan_loyalty - 5)
                    gm.military.morale = max(0, gm.military.morale - 10)
        
        # Ana ekrana dön
        self.screen_manager.change_screen(ScreenType.PROVINCE_VIEW)
    

    def update(self, dt: float):
        """Düşman turunu işle"""
        # Efektleri güncelle
        self._shake.update(dt)
        self._flash.update(dt)
        
        if self.enemy_action_pending and not self.battle_ended:
            self.enemy_turn_timer += dt
            
            # 1.5 saniye bekle sonra savaş hesaplansın
            if self.enemy_turn_timer >= 1.5:
                # Düşman taktiğini seç
                enemy_tactic = self._get_enemy_tactic_by_doctrine()
                # Savaştır
                self._resolve_tactics(self.player_tactic, enemy_tactic)
                
                # Sarsıntı + flaş efekti
                self._shake.trigger(intensity=6.0, duration=0.3)
                self._flash.trigger(color=(255, 220, 150), duration=0.1)
                
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
        
        # Taktik isimleri — moda göre farklı
        if self.battle_mode == 'naval':
            tactic_names = {
                'center': 'Rampa (Borda)',
                'flank': 'Manevra',
                'defend': 'Savunma Düzeni',
                'artillery': 'Bordoya Ateş',
                'feint': 'Sahte Ricat'
            }
        else:
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
        
        # === DENIZ SAVAŞI MATRİSİ ===
        if self.battle_mode == 'naval':
            # Rampa (center) > Manevra (flank): gemiye atlayınca manevra işe yaramaz
            if pt == 'center' and et == 'flank':
                p_dmg_mult = 1.5; e_dmg_mult = 0.5
                matchup_desc += "Gemiye borda atıp düşman mürettebatını kılıçtan geçirdik! Manevraları boşa çıktı. "
            elif et == 'center' and pt == 'flank':
                e_dmg_mult = 1.5; p_dmg_mult = 0.5
                matchup_desc += "Düşman gemimize borda attı! Manevra yapamadan yakalandık. "
            # Bordoya Ateş (artillery) > Rampa (center): top ateşi yaklaşanı vurur  
            elif pt == 'artillery' and et == 'center':
                p_dmg_mult = 1.5; e_dmg_mult = 0.5
                matchup_desc += "Bordoya ateş açtık! Yaklaşmaya çalışan düşman gemisini delik deşik ettik. "
            elif et == 'artillery' and pt == 'center':
                e_dmg_mult = 1.5; p_dmg_mult = 0.5
                matchup_desc += "Borda ateşe yaklaşırken düşman toplarına yakalandık! "
            # Manevra (flank) > Bordoya Ateş (artillery): hızlı gemi top menzilinden kaçar
            elif pt == 'flank' and et == 'artillery':
                p_dmg_mult = 1.5; e_dmg_mult = 0.5
                matchup_desc += "Rüzgârı arkamıza alıp düşman top menzilinden sıyrıldık ve karşı ateşe geçtik! "
            elif et == 'flank' and pt == 'artillery':
                e_dmg_mult = 1.5; p_dmg_mult = 0.5
                matchup_desc += "Düşman gemileri çevik manevrayla toplarımızın menzilinden kaçtı! "
            # Aynı taktik = berabere
            elif pt == et:
                matchup_desc += "İki filo da aynı stratejiyi uyguladı, dengeli bir çatışma yaşandı. "
            else:
                matchup_desc += "Deniz savaşı devam ediyor. "
        
        # === KARA SAVAŞI MATRİSİ ===
        elif pt == 'center' and et == 'defend':
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
        
        # === GENİŞLETİLMİŞ MATRİS: Topçu ve Sahte Ricat ===
        # Topçu, savunmayı ezer (sabit mevzide toplar etkili)
        elif pt == 'artillery' and et == 'defend':
            p_dmg_mult = 1.5; e_dmg_mult = 0.5
            matchup_desc += "Top atışlarımız düşmanın sabit savunma mevzilerini yerle bir etti! "
        elif et == 'artillery' and pt == 'defend':
            e_dmg_mult = 1.5; p_dmg_mult = 0.5
            matchup_desc += "Düşman topları savunma mevzilerimizi paramparça etti! "
        # Kanat, topçuyu ezer (süvariler top mevzilerine dalar)
        elif pt == 'flank' and et == 'artillery':
            p_dmg_mult = 1.5; e_dmg_mult = 0.5
            matchup_desc += "Süvarilerimiz düşman top mevzilerine saldırdı ve topçuları dağıttı! "
        elif et == 'flank' and pt == 'artillery':
            e_dmg_mult = 1.5; p_dmg_mult = 0.5
            matchup_desc += "Düşman süvarileri topçu mevzilerimize saldırdı! "
        # Sahte Ricat, kanat man. ezer (kanat takip ederken tuzak)
        elif pt == 'feint' and et == 'flank':
            p_dmg_mult = 1.8; e_dmg_mult = 0.4
            matchup_desc += "Turan Taktiği! Sahte geri çekilme düşman süvarilerini pusuya düşürdü! "
        elif et == 'feint' and pt == 'flank':
            e_dmg_mult = 1.8; p_dmg_mult = 0.4
            matchup_desc += "Düşman sahte geri çekildi, süvarilerimiz tuzaktaki pusucuların eline düştü! "
        # Savunma, Sahte Ricatı ezer (disiplinli hat tuzakları bozar)
        elif pt == 'defend' and et == 'feint':
            p_dmg_mult = 1.4; e_dmg_mult = 0.6
            matchup_desc += "Disiplinli savunma hattımız düşmanın Turan taktiğine kanmadı! "
        elif et == 'defend' and pt == 'feint':
            e_dmg_mult = 1.4; p_dmg_mult = 0.6
            matchup_desc += "Sahte geri çekilmemiz işe yaramadı, düşman yerinden kıpırdamadı! "
            
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
                    
        # === TABUR CENGİ TOPÇU BONUSU ===
        # Savunma formasyonunda toplar zincirle birbirine bağlanıp
        # savunma hattının arkasına yerleştirilir. Saldıran düşmana ağır hasar.
        if pt == 'defend' and gm and hasattr(gm, 'artillery'):
            artillery = gm.artillery
            if len(artillery.cannons) > 0:
                crew_eff = artillery.get_crew_effectiveness(gm.military)
                # Sahra gücü bazlı bonus (mühimmat çarpanı dahil)
                tabur_artillery_power = int(artillery.get_total_power('field') * crew_eff * 0.5)
                tabur_morale_dmg = int(artillery.get_morale_damage() * crew_eff * 0.3)
                
                if tabur_artillery_power > 0:
                    # Düşmana ek hasar
                    self.enemy_casualties += tabur_artillery_power
                    self.enemy_morale -= tabur_morale_dmg
                    
                    # Barut tüketimi (tek salvo)
                    barut_cost = artillery.get_gunpowder_consumption()
                    if gm.economy.resources.gunpowder >= barut_cost:
                        gm.economy.resources.gunpowder -= barut_cost
                        matchup_desc += (
                            f"TABUR CENGİ: Savunma hattımızdaki {len(artillery.cannons)} top "
                            f"zincirleme ateş açtı! {tabur_artillery_power} hasar, "
                            f"{tabur_morale_dmg} moral kaybı. ({barut_cost} barut harcandı) "
                        )
                    else:
                        # Barut yoksa bonus yarıya düşer
                        self.enemy_casualties += tabur_artillery_power // 2
                        matchup_desc += (
                            "TABUR CENGİ: Toplar ateş açmak istedi ama barut yetersiz! "
                            "Yarım güçle ateş edildi. "
                        )
                    
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
        
        # Topçu — gerçek toplarla entegre
        if pt == 'artillery':
            gm = self.screen_manager.game_manager
            art_result = getattr(self, '_artillery_result', None)
            if art_result and art_result['total_damage'] > 0:
                # Gerçek top hasarını çarpanlara yansıt
                power_bonus = art_result['total_damage'] / 100  # %1 bonus per power point
                morale_bonus = art_result['morale_damage']
                p_dmg_mult = 1.0 + min(1.0, power_bonus)  # Max 2x çarpan
                e_dmg_mult = max(0.3, 1.0 - power_bonus * 0.5)  # Bize gelen hasar azalır
                # Ek moral hasarı — toplardan gelen
                self.enemy_morale -= min(20, morale_bonus)
                
                cannon_count = len(gm.artillery.cannons) if gm else 0
                matchup_desc += f"{cannon_count} topumuz ateş açtı! "
                if art_result['bursts'] > 0:
                    matchup_desc += f"({art_result['bursts']} top patladı!) "
                matchup_desc += f"Barut: {art_result['gunpowder_used']} harcandı. "
            else:
                # Top yoksa veya sonuç yoksa zayıf etki
                p_dmg_mult = 1.1; e_dmg_mult = 0.9
                matchup_desc += "Topçu ateşi zayıf kaldı. "
            self._artillery_result = None  # Temizle
        
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
                matchup_desc += "Tüm toplar ateş açıp surları sarstı! "
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
        # Gradient arka plan
        surface.blit(self._gradient, (0, 0))
        
        # Sarsıntı offset
        shake_x = self._shake.offset_x
        shake_y = self._shake.offset_y
        if shake_x != 0 or shake_y != 0:
            # Offset'li bir subsurface oluşturmak yerine, çizim koordinatlarına offset ekliyoruz
            pass  # Aşağıdaki çizimler normal devam eder, flaş efekti üstüne eklenir
        
        # Başlık
        header_font = self.get_header_font()
        
        title = "SAVAS"
        if getattr(self, 'is_defending', False):
            gm = self.screen_manager.game_manager
            invader = gm.current_invasion['invader'] if gm and hasattr(gm, 'current_invasion') and gm.current_invasion else "Düşman"
            title = f"!!! {invader} ŞEHRİMİZİ KUŞATIYOR !!! TUR {self.current_round}"
        elif self.current_battle:
            mode_titles = {'siege': 'KUSATMASI', 'raid': 'AKINI', 'naval': 'DENIZ AKINI'}
            mode_title = mode_titles.get(self.battle_mode, 'SAVASI')
            title = f"{self.current_battle.defender_name} {mode_title} - TUR {self.current_round}"
        
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
        
        # Flaş efekti (üst katman)
        self._flash.draw(surface)
