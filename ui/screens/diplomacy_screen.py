# -*- coding: utf-8 -*-
"""
Osmanlı Eyalet Yönetim Simülasyonu - Diplomasi Ekranı
"""

import pygame
from ui.screen_manager import BaseScreen, ScreenType
from ui.components import Button, Panel, HierarchicalMenu
from config import COLORS, FONTS, SCREEN_WIDTH, SCREEN_HEIGHT


class DiplomacyScreen(BaseScreen):
    """Diplomasi yönetim ekranı"""
    
    def __init__(self, screen_manager):
        super().__init__(screen_manager)
        
        # Paneller
        self.sultan_panel = Panel(20, 80, 400, 250, "Padisah Iliskileri")
        self.neighbors_panel = Panel(440, 80, 400, 250, "Komsu Beylikler")
        self.missions_panel = Panel(860, 80, 380, 250, "Olaylar ve Gorevler")
        
        # Hiyerarşik menü (alt menüler destekli)
        self.action_menu = HierarchicalMenu(
            x=20,
            y=360,
            width=820,
            item_height=40
        )
        
        self.back_button = Button(
            x=20,
            y=SCREEN_HEIGHT - 70,
            width=150,
            height=50,
            text="Geri",
            shortcut="backspace",
            callback=self._go_back
        )
        
        self._header_font = None
    
    def get_header_font(self):
        if self._header_font is None:
            self._header_font = pygame.font.Font(None, FONTS['header'])
        return self._header_font
    
    def on_enter(self):
        self._update_panels()
        self._setup_action_menu()
    
    def announce_screen(self):
        self.audio.announce_screen_change("Diplomasi")
        gm = self.screen_manager.game_manager
        if gm:
            gm.diplomacy.announce_status()
    
    def _setup_action_menu(self):
        """Hiyerarsik eylem menusunu ayarla"""
        self.action_menu.clear()
        gm = self.screen_manager.game_manager
        if not gm:
            return
        
        dip = gm.diplomacy
        military_power = gm.military.get_total_power()
        
        # === 1. PADİŞAH İLİŞKİLERİ ===
        padisah_items = [
            {'text': 'Padişaha 500 Altın Gönder', 'callback': lambda: self._send_tribute(500)},
            {'text': 'Padişaha 2000 Altın Gönder', 'callback': lambda: self._send_tribute(2000)},
        ]
        
        # Padişah görevleri
        if dip.active_missions:
            padisah_items.append({'text': '', 'is_separator': True})
            for i, mission in enumerate(dip.active_missions):
                if mission['type'] == 'tribute':
                    gold_needed = mission['target']
                    if gm.economy.can_afford(gold=gold_needed):
                        padisah_items.append({
                            'text': f"Tamamla: {mission['title']} ({gold_needed} altin)",
                            'callback': lambda idx=i, g=gold_needed: self._complete_tribute_mission(idx, g)
                        })
                elif mission['type'] == 'military':
                    soldiers = mission['target']
                    padisah_items.append({
                        'text': f"Tamamla: {mission['title']} ({soldiers} asker)",
                        'callback': lambda idx=i: self._complete_military_mission(idx)
                    })
                elif mission['type'] == 'suppress':
                    padisah_items.append({
                        'text': f"Tamamla: {mission['title']}",
                        'callback': lambda idx=i: self._complete_suppress_mission(idx)
                    })
        
        self.action_menu.add_category("Padişah İlişkileri", padisah_items)
        
        # === 2. EVLİLİK İTTİFAKLARI ===
        evlilik_items = []
        for neighbor in dip.neighbors:
            is_married = any(m['partner'] == neighbor for m in dip.marriage_alliances)
            relation = dip.neighbors[neighbor]
            if not is_married:
                evlilik_items.append({
                    'text': f"{neighbor} (İlişki: {relation.value})",
                    'callback': lambda n=neighbor: self._propose_marriage(n)
                })
            else:
                evlilik_items.append({
                    'text': f"[Evli] {neighbor}",
                    'callback': None
                })
        
        self.action_menu.add_category("Evlilik İttifakları (10000 Altın)", evlilik_items)
        
        # === 3. HARAÇ TALEBİ ===
        harac_items = []
        if military_power >= 500:
            for neighbor in dip.neighbors:
                relation = dip.neighbors[neighbor]
                personality = relation.get_personality_description()
                harac_items.append({
                    'text': f"{neighbor} ({personality})",
                    'callback': lambda n=neighbor: self._demand_tribute(n)
                })
        else:
            harac_items.append({
                'text': f"500+ güç gerekli (Mevcut: {military_power})",
                'callback': None
            })
        
        self.action_menu.add_category(f"Haraç Talebi (Güç: {military_power})", harac_items)
        
        # === 4. VASSALLAŞTIRMA ===
        vassal_items = []
        if military_power >= 1500:
            for neighbor in dip.neighbors:
                is_vassal = any(v['name'] == neighbor for v in dip.vassals)
                if not is_vassal:
                    vassal_items.append({
                        'text': neighbor,
                        'callback': lambda n=neighbor: self._make_vassal(n)
                    })
                else:
                    vassal_items.append({
                        'text': f"[Vassal] {neighbor}",
                        'callback': None
                    })
        else:
            vassal_items.append({
                'text': f"1500+ güç gerekli (Mevcut: {military_power})",
                'callback': None
            })
        
        self.action_menu.add_category(f"Vassallaştırma (Güç: {military_power})", vassal_items)
        
        # === 5. DURUM ÖZETİ ===
        durum_items = [
            {'text': f"Prestij: {dip.prestige} ({dip.get_prestige_level()})", 'callback': None},
            {'text': '', 'is_separator': True},
        ]
        
        # Aktif olay zincirleri detayları
        if dip.event_chains:
            durum_items.append({'text': f"--- Aktif Olaylar ({len(dip.event_chains)}) ---", 'callback': None})
            
            stage_names = {
                'marriage': ['Cevap Bekleniyor', 'Çeyiz Pazarlığı', 'Düğün Hazırlığı'],
                'vassal': ['Ultimatom Gönderildi', 'Şartlar Görüşülüyor'],
                'peace': ['Barış Teklifi']
            }
            type_names = {'marriage': 'Evlilik', 'vassal': 'Vassallaştırma', 'peace': 'Barış'}
            
            for chain in dip.event_chains:
                chain_type = chain['type']
                target = chain['target']
                stage = chain['stage']
                turns = chain['turns_in_stage']
                
                stages = stage_names.get(chain_type, ['Devam Ediyor'])
                stage_name = stages[min(stage, len(stages)-1)]
                type_name = type_names.get(chain_type, chain_type)
                
                durum_items.append({
                    'text': f"{target}: {type_name} - {stage_name} ({turns} tur)",
                    'callback': None
                })
        else:
            durum_items.append({'text': "Aktif olay yok", 'callback': None})
        
        durum_items.append({'text': '', 'is_separator': True})
        
        # Vassallar detayları
        if dip.vassals:
            durum_items.append({'text': f"--- Vassallar ({len(dip.vassals)}) ---", 'callback': None})
            for vassal in dip.vassals:
                durum_items.append({
                    'text': f"{vassal['name']}: {vassal['tribute']} altın/tur, sadakat %{vassal['loyalty']}",
                    'callback': None
                })
        else:
            durum_items.append({'text': f"Vassal: Yok", 'callback': None})
        
        # Evlilik ittifakları detayları
        if dip.marriage_alliances:
            durum_items.append({'text': f"--- Evlilik İttifakları ({len(dip.marriage_alliances)}) ---", 'callback': None})
            for marriage in dip.marriage_alliances:
                durum_items.append({
                    'text': f"{marriage['partner']}: {marriage['turns_active']} tur aktif",
                    'callback': None
                })
        else:
            durum_items.append({'text': f"Evlilik İttifakı: Yok", 'callback': None})
        
        self.action_menu.add_category("Durum Özeti", durum_items)
        
        # === HARİTAYA GİT ===
        self.action_menu.add_action("Haritaya Git", self._go_to_map)
        
        # === GERİ BUTONU ===
        self.action_menu.add_back_button()
    
    def _update_panels(self):
        """Panelleri güncelle"""
        gm = self.screen_manager.game_manager
        if not gm:
            return
        
        dip = gm.diplomacy
        
        # Padişah paneli
        self.sultan_panel.clear()
        self.sultan_panel.add_item("Sadakat", f"%{dip.sultan_loyalty}")
        self.sultan_panel.add_item("Durum", dip.get_loyalty_description())
        self.sultan_panel.add_item("Lütuf", f"%{dip.sultan_favor}")
        self.sultan_panel.add_item("", "")
        self.sultan_panel.add_item("Prestij", f"{dip.prestige} ({dip.get_prestige_level()})")
        self.sultan_panel.add_item("", "")
        self.sultan_panel.add_item("Sadrazam İlişkisi", f"{dip.sadrazam_relation}")
        self.sultan_panel.add_item("Defterdar İlişkisi", f"{dip.defterdar_relation}")
        
        # Komşular paneli
        self.neighbors_panel.clear()
        for name, relation in dip.neighbors.items():
            type_name = dip.get_relation_type_name(relation.relation_type)
            personality_desc = relation.get_personality_description()
            self.neighbors_panel.add_item(f"{name} ({personality_desc})", f"{type_name} ({relation.value})")
        
        if dip.envoy_cooldown > 0:
            self.neighbors_panel.add_item("", "")
            self.neighbors_panel.add_item("Elçi Bekleme", f"{dip.envoy_cooldown} tur")
        
        # Görevler ve Olay Zincirleri paneli
        self.missions_panel.clear()
        
        # Aktif olay zincirleri
        if dip.event_chains:
            self.missions_panel.add_item("Aktif Olaylar:", "")
            for chain in dip.event_chains:
                stage_names = {
                    'marriage': ['Cevap Bekleniyor', 'Pazarlık', 'Düğün Hazırlığı'],
                    'vassal': ['Ultimatom', 'Şartlar Görüşülüyor'],
                    'peace': ['Barış Teklifi']
                }
                chain_stages = stage_names.get(chain['type'], ['Devam Ediyor'])
                stage_name = chain_stages[min(chain['stage'], len(chain_stages)-1)]
                self.missions_panel.add_item(
                    f"{chain['target']}: {chain['type'].title()}",
                    stage_name
                )
            self.missions_panel.add_item("", "")
        
        # Padişah görevleri
        if dip.active_missions:
            self.missions_panel.add_item("📋 Görevler:", "")
            for mission in dip.active_missions:
                self.missions_panel.add_item(
                    mission['title'],
                    f"{mission['turns_remaining']} tur"
                )
        
        if not dip.event_chains and not dip.active_missions:
            self.missions_panel.add_item("Aktif görev veya olay yok", "")
    
    def handle_event(self, event) -> bool:
        # HierarchicalMenu tüm navigasyonu işler
        result = self.action_menu.handle_event(event)
        
        # False dönerse ana ekrana dön
        if result is False:
            self._go_back()
            return True
        
        # True ise menü işledi
        if result is True:
            return True
        
        if event.type == pygame.KEYDOWN:
            # F1 - Özet (tek kısayol)
            if event.key == pygame.K_F1:
                gm = self.screen_manager.game_manager
                if gm:
                    gm.diplomacy.announce_status()
                return True
        
        return False
    
    def _announce_sultan_status(self):
        """Padişah durumunu duyur"""
        gm = self.screen_manager.game_manager
        if not gm:
            return
        dip = gm.diplomacy
        self.audio.speak(f"Padişah Sadakati: yüzde {dip.sultan_loyalty}", interrupt=True)
        self.audio.speak(f"Durum: {dip.get_loyalty_description()}", interrupt=False)
        self.audio.speak(f"Padişah Lütfu: yüzde {dip.sultan_favor}", interrupt=False)
    
    def _announce_neighbor_status(self):
        """Komşu durumlarını duyur"""
        gm = self.screen_manager.game_manager
        if not gm:
            return
        dip = gm.diplomacy
        self.audio.speak("Komşu Beylikler:", interrupt=True)
        for neighbor, relation in dip.neighbor_relations.items():
            status = "Dost" if relation >= 50 else "Nötr" if relation >= 0 else "Düşman"
            self.audio.speak(f"{neighbor}: {status}, ilişki yüzde {relation}", interrupt=False)
    
    def _announce_prestige(self):
        """Prestij durumunu duyur"""
        gm = self.screen_manager.game_manager
        if not gm:
            return
        dip = gm.diplomacy
        self.audio.speak(f"Prestij: {dip.prestige} puan", interrupt=True)
        self.audio.speak(f"Seviye: {dip.get_prestige_level()}", interrupt=False)
        bonus = dip.get_prestige_modifier()
        if bonus > 0:
            self.audio.speak(f"Diplomatik bonus: artı yüzde {bonus}", interrupt=False)
        elif bonus < 0:
            self.audio.speak(f"Diplomatik ceza: eksi yüzde {abs(bonus)}", interrupt=False)
        
        # Son prestij değişikliklerini de duyur
        if dip.prestige_history:
            last = dip.prestige_history[-1]
            if last['amount'] > 0:
                self.audio.speak(f"Son değişiklik: artı {last['amount']}, sebep: {last['reason']}", interrupt=False)
            else:
                self.audio.speak(f"Son değişiklik: eksi {abs(last['amount'])}, sebep: {last['reason']}", interrupt=False)
    
    def _announce_event_chains(self):
        """Olay zincirlerini duyur"""
        gm = self.screen_manager.game_manager
        if not gm:
            return
        dip = gm.diplomacy
        
        if not dip.event_chains:
            self.audio.speak("Aktif olay zinciri yok.", interrupt=True)
            return
        
        self.audio.speak(f"{len(dip.event_chains)} aktif olay zinciri:", interrupt=True)
        
        stage_names = {
            'marriage': ['Elçi gönderildi, cevap bekleniyor', 'Çeyiz pazarlığı yapılıyor', 'Düğün hazırlıkları devam ediyor'],
            'vassal': ['Ultimatom gönderildi, cevap bekleniyor', 'Şartlar görüşülüyor'],
            'peace': ['Barış teklifi gönderildi, cevap bekleniyor']
        }
        
        for chain in dip.event_chains:
            chain_type = chain['type']
            target = chain['target']
            stage = chain['stage']
            turns = chain['turns_in_stage']
            
            stages = stage_names.get(chain_type, ['Devam ediyor'])
            stage_name = stages[min(stage, len(stages)-1)]
            
            type_names = {'marriage': 'Evlilik', 'vassal': 'Vassallaştırma', 'peace': 'Barış'}
            type_name = type_names.get(chain_type, chain_type)
            
            self.audio.speak(
                f"{target} ile {type_name}: {stage_name}. Bu aşamada {turns} tur geçti.",
                interrupt=False
            )
    
    def _announce_missions(self):
        """Görevleri duyur"""
        gm = self.screen_manager.game_manager
        if not gm:
            return
        dip = gm.diplomacy
        
        if not dip.active_missions:
            self.audio.speak("Aktif padişah görevi yok.", interrupt=True)
            return
        
        self.audio.speak(f"{len(dip.active_missions)} aktif görev:", interrupt=True)
        
        for mission in dip.active_missions:
            self.audio.speak(
                f"{mission['title']}: {mission.get('description', '')}. Kalan süre: {mission['turns_remaining']} tur.",
                interrupt=False
            )
    
    def _announce_neighbors_detailed(self):
        """Komşuları detaylı kişilikleriyle duyur"""
        gm = self.screen_manager.game_manager
        if not gm:
            return
        dip = gm.diplomacy
        
        if not dip.neighbors:
            self.audio.speak("Komşu yok.", interrupt=True)
            return
        
        self.audio.speak(f"{len(dip.neighbors)} komşu beylik:", interrupt=True)
        
        for name, relation in dip.neighbors.items():
            type_name = dip.get_relation_type_name(relation.relation_type)
            personality_desc = relation.get_personality_description()
            
            self.audio.speak(
                f"{name}: {type_name}, ilişki {relation.value}. Kişiliği: {personality_desc}.",
                interrupt=False
            )
        
        # Vassalları da duyur
        if dip.vassals:
            self.audio.speak(f"Ayrıca {len(dip.vassals)} vassalınız var:", interrupt=False)
            for vassal in dip.vassals:
                self.audio.speak(
                    f"{vassal['name']}: yıllık {vassal['tribute']} altın haraç, sadakat yüzde {vassal['loyalty']}.",
                    interrupt=False
                )
        
        # Evlilik ittifaklarını duyur
        if dip.marriage_alliances:
            self.audio.speak(f"{len(dip.marriage_alliances)} evlilik ittifakınız var:", interrupt=False)
            for marriage in dip.marriage_alliances:
                self.audio.speak(
                    f"{marriage['partner']} ile evli, {marriage['turns_active']} tur aktif.",
                    interrupt=False
                )
    
    def _announce_next_panel(self):
        """Sıradaki paneli duyur"""
        if not hasattr(self, '_current_panel'):
            self._current_panel = 0
        
        panels = [self.sultan_panel, self.neighbors_panel, self.missions_panel]
        self._current_panel = (self._current_panel + 1) % len(panels)
        panels[self._current_panel].announce_content()
    
    def update(self, dt: float):
        self._update_panels()
        self.action_menu.update()  # İlk duyuruyu yapar
    
    def draw(self, surface: pygame.Surface):
        # Başlık
        header_font = self.get_header_font()
        title = header_font.render("DIPLOMASI", True, COLORS['gold'])
        surface.blit(title, (20, 20))
        
        # Paneller (üst kısım)
        self.sultan_panel.draw(surface)
        self.neighbors_panel.draw(surface)
        self.missions_panel.draw(surface)
        
        # Hiyerarşik menü (alt kısım)
        self.action_menu.draw(surface)
        
        # Sadakat göstergesi
        self._draw_loyalty_bar(surface)
        
        # Geri butonu
        self.back_button.draw(surface)
    
    def _draw_loyalty_bar(self, surface: pygame.Surface):
        """Sadakat göstergesini çiz"""
        gm = self.screen_manager.game_manager
        if not gm:
            return
        
        rect = pygame.Rect(860, 80, 380, 60)
        pygame.draw.rect(surface, COLORS['panel_bg'], rect, border_radius=10)
        pygame.draw.rect(surface, COLORS['panel_border'], rect, width=2, border_radius=10)
        
        # Progress bar
        loyalty = gm.diplomacy.sultan_loyalty
        bar_width = int((rect.width - 40) * (loyalty / 100))
        
        # Renk (düşükse kırmızı, yüksekse yeşil)
        if loyalty < 30:
            color = COLORS['danger']
        elif loyalty < 60:
            color = COLORS['warning']
        else:
            color = COLORS['success']
        
        bar_rect = pygame.Rect(rect.x + 20, rect.y + 30, bar_width, 15)
        pygame.draw.rect(surface, color, bar_rect, border_radius=5)
        
        # Label
        font = pygame.font.Font(None, FONTS['small'])
        label = font.render(f"Padişah Sadakati: %{loyalty}", True, COLORS['text'])
        surface.blit(label, (rect.x + 20, rect.y + 10))
    
    def _send_tribute(self, amount: int):
        """Haraç gönder"""
        gm = self.screen_manager.game_manager
        if gm:
            gm.diplomacy.send_tribute_to_sultan(amount, gm.economy)
            self._update_panels()
    
    def _send_envoy(self, target: str):
        """Elçi gönder"""
        gm = self.screen_manager.game_manager
        if gm:
            gm.diplomacy.send_envoy(target)
            self._update_panels()
            self._setup_action_menu()
    
    def _propose_marriage(self, target: str):
        """Evlilik teklifi - Müzakere ekranını aç"""
        from ui.screens.negotiation_screen import NegotiationType
        
        neg_screen = self.screen_manager.screens.get(ScreenType.NEGOTIATION)
        if neg_screen:
            neg_screen.setup_negotiation(NegotiationType.MARRIAGE, target)
            self.screen_manager.change_screen(ScreenType.NEGOTIATION)
    
    def _demand_tribute(self, target: str):
        """Haraç talep et - Müzakere ekranını aç"""
        from ui.screens.negotiation_screen import NegotiationType
        
        neg_screen = self.screen_manager.screens.get(ScreenType.NEGOTIATION)
        if neg_screen:
            neg_screen.setup_negotiation(NegotiationType.TRIBUTE, target)
            self.screen_manager.change_screen(ScreenType.NEGOTIATION)
    
    def _make_vassal(self, target: str):
        """Vassal yap - Müzakere ekranını aç"""
        from ui.screens.negotiation_screen import NegotiationType
        
        neg_screen = self.screen_manager.screens.get(ScreenType.NEGOTIATION)
        if neg_screen:
            neg_screen.setup_negotiation(NegotiationType.VASSAL, target)
            self.screen_manager.change_screen(ScreenType.NEGOTIATION)
    
    def _complete_tribute_mission(self, mission_index: int, gold_amount: int):
        """Haraç görevi tamamla"""
        gm = self.screen_manager.game_manager
        if not gm:
            return
        
        # Altını harca
        if not gm.economy.can_afford(gold=gold_amount):
            self.audio.speak(f"Yetersiz altın. {gold_amount} altın gerekli.", interrupt=True)
            return
        
        gm.economy.spend(gold=gold_amount)
        
        # Görevi tamamla
        if mission_index < len(gm.diplomacy.active_missions):
            mission = gm.diplomacy.active_missions[mission_index]
            gm.diplomacy.complete_mission(mission_index)
            gm.diplomacy.add_prestige(20, f"{mission['title']} görevi tamamlandı")
            
            self.audio.speak(
                f"Görev tamamlandı: {mission['title']}. {gold_amount} altın gönderildi. "
                f"Sadakat artı {mission['reward_loyalty']}.",
                interrupt=True
            )
        
        self._update_panels()
        self._setup_action_menu()
    
    def _complete_military_mission(self, mission_index: int):
        """Asker görevi tamamla"""
        gm = self.screen_manager.game_manager
        if not gm:
            return
        
        # Askeri gücü kontrol et
        if mission_index < len(gm.diplomacy.active_missions):
            mission = gm.diplomacy.active_missions[mission_index]
            soldiers_needed = mission['target']
            
            # Güç düşer (asker gönderildi)
            # Görevi tamamla
            gm.diplomacy.complete_mission(mission_index)
            gm.diplomacy.add_prestige(30, f"{mission['title']} görevi tamamlandı")
            
            self.audio.speak(
                f"Görev tamamlandı: {mission['title']}. {soldiers_needed} asker sefere gönderildi. "
                f"Sadakat artı {mission['reward_loyalty']}.",
                interrupt=True
            )
        
        self._update_panels()
        self._setup_action_menu()
    
    def _complete_suppress_mission(self, mission_index: int):
        """İsyan bastırma görevi tamamla"""
        gm = self.screen_manager.game_manager
        if not gm:
            return
        
        if mission_index < len(gm.diplomacy.active_missions):
            mission = gm.diplomacy.active_missions[mission_index]
            
            # Görevi tamamla
            gm.diplomacy.complete_mission(mission_index)
            gm.diplomacy.add_prestige(25, f"{mission['title']} görevi tamamlandı")
            
            self.audio.speak(
                f"Görev tamamlandı: {mission['title']}. İsyan başarıyla bastırıldı. "
                f"Sadakat artı {mission['reward_loyalty']}.",
                interrupt=True
            )
        
        self._update_panels()
        self._setup_action_menu()
    
    def _go_to_map(self):
        """Harita ekranına git"""
        self.screen_manager.change_screen(ScreenType.MAP)
    
    def _go_back(self):
        """Geri dön"""
        if getattr(self.screen_manager, 'is_multiplayer_mode', False):
            self.screen_manager.change_screen(ScreenType.MULTIPLAYER_GAME)
        else:
            self.screen_manager.change_screen(ScreenType.PROVINCE_VIEW)
