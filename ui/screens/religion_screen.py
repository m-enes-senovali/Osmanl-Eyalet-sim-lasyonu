# -*- coding: utf-8 -*-
"""
Osmanlı Eyalet Yönetim Simülasyonu - Din ve Kültür Ekranı
"""

import pygame
from ui.screen_manager import BaseScreen, ScreenType
from ui.components import Button, Panel, HierarchicalMenu
from config import COLORS, FONTS, SCREEN_WIDTH, SCREEN_HEIGHT, get_font
from game.systems.religion import (
    Millet, UlemaRank, VakifType,
    MILLET_DEFINITIONS, ULEMA_DEFINITIONS, VAKIF_DEFINITIONS
)


class ReligionScreen(BaseScreen):
    """Din ve Kültür yönetim ekranı"""
    
    def __init__(self, screen_manager):
        super().__init__(screen_manager)
        
        # Paneller
        self.millet_panel = Panel(20, 80, 400, 250, "Millet Durumu")
        self.ulema_panel = Panel(440, 80, 400, 250, "Ulema")
        self.vakif_panel = Panel(860, 80, 380, 250, "Vakıflar")
        
        # Hiyerarşik menü
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
            self._header_font = get_font(FONTS['header'])
        return self._header_font
    
    def on_enter(self):
        self._update_panels()
        self._setup_action_menu()
        self.audio.play_game_sound('religion', 'prayer')
    
    def announce_screen(self):
        self.audio.announce_screen_change("Din ve Kültür")
        gm = self.screen_manager.game_manager
        if gm:
            gm.religion.announce_status()
    
    def _update_panels(self):
        """Panel içeriklerini güncelle"""
        gm = self.screen_manager.game_manager
        if not gm:
            return
        
        rel = gm.religion
        
        # Millet paneli - (label, value) format
        millet_items = []
        for millet, state in rel.millet_states.items():
            stats = MILLET_DEFINITIONS[millet]
            loyalty = state['loyalty']
            millet_items.append((stats.name_tr, f"%{loyalty} sadakat"))
        
        millet_items.append(("Dindarlık", f"%{rel.piety}"))
        millet_items.append(("Meşruiyet", f"%{rel.legitimacy}"))
        millet_items.append(("Hoşgörü", f"%{rel.tolerance}"))
        
        if rel.kizilbas_threat > 30:
            millet_items.append(("Kızılbaş Tehdidi", f"%{rel.kizilbas_threat}"))
        
        self.millet_panel.set_content(millet_items)
        
        # Ulema paneli
        ulema_items = []
        for ulema in rel.ulema:
            stats = ULEMA_DEFINITIONS[ulema.rank]
            ulema_items.append((ulema.name, stats.name_tr))
        
        if not ulema_items:
            ulema_items.append(("Durum", "Henüz ulema atanmadı"))
        
        ulema_items.append(("Eğitim Seviyesi", f"%{rel.education_level}"))
        
        self.ulema_panel.set_content(ulema_items)
        
        # Vakıf paneli
        vakif_items = []
        for vakif in rel.vakifs:
            vakif_items.append((vakif.name, f"%{vakif.condition} durum"))
        
        if not vakif_items:
            vakif_items.append(("Durum", "Henüz vakıf yok"))
        
        vakif_items.append(("Toplam", f"{len(rel.vakifs)} vakıf"))
        
        self.vakif_panel.set_content(vakif_items)
    
    def _setup_action_menu(self):
        """Eylem menüsünü ayarla"""
        self.action_menu.clear()
        gm = self.screen_manager.game_manager
        if not gm:
            return
        
        rel = gm.religion
        
        # === 1. ULEMA ATAMA ===
        ulema_items = []
        for rank in UlemaRank:
            # Şeyhülislam yalnızca Padişah tarafından atanır, listede gösterme
            if rank == UlemaRank.SEYHULISLAM:
                continue
            stats = ULEMA_DEFINITIONS[rank]
            current = len([u for u in rel.ulema if u.rank == rank])
            if current < stats.max_count:
                cost = stats.salary * 4
                ulema_items.append({
                    'text': f'{stats.name_tr} Ata ({cost} altın, maks {stats.max_count})',
                    'callback': lambda r=rank: self._appoint_ulema(r)
                })
        
        if ulema_items:
            self.action_menu.add_category("Ulema Ata", ulema_items)
        
        # === 2. VAKIF İNŞA ===
        vakif_items = []
        population = gm.population.population.total
        for vakif_type in VakifType:
            stats = VAKIF_DEFINITIONS[vakif_type]
            if population >= stats.required_population:
                vakif_items.append({
                    'text': f'{stats.name_tr} ({stats.build_cost} altın)',
                    'callback': lambda vt=vakif_type: self._build_vakif(vt)
                })
            else:
                vakif_items.append({
                    'text': f'{stats.name_tr} (min {stats.required_population} nüfus)',
                    'callback': None,
                    'disabled': True
                })
        
        self.action_menu.add_category("Vakıf İnşa Et", vakif_items)
        
        # === 3. FETVA ===
        if rel.has_seyhulislam:
            # Fetva kısıtlamaları (1 turda 1 fetva)
            is_disabled = getattr(rel, 'fetva_issued_this_turn', False)
            
            fetva_items = [
                {'text': 'Cihad Fetvası (Askeri Moral +20)' if not is_disabled else '[Kullanıldı] Cihad Fetvası', 
                 'callback': lambda: self._issue_fetva('cihad') if not is_disabled else None, 
                 'disabled': is_disabled},
                {'text': 'Ticaret Fetvası (500 Altın Destek)' if not is_disabled else '[Kullanıldı] Ticaret', 
                 'callback': lambda: self._issue_fetva('ticaret') if not is_disabled else None,
                 'disabled': is_disabled},
                {'text': 'Vergi Fetvası (+400 Altın, -5 Halk Huzuru)' if not is_disabled else '[Kullanıldı] Vergi', 
                 'callback': lambda: self._issue_fetva('vergi') if not is_disabled else None,
                 'disabled': is_disabled},
            ]
            
            if rel.kizilbas_threat > 20 and not rel.kizilbas_suppressed:
                fetva_items.append({
                    'text': 'Kızılbaş Karşıtı Fetva (Tehdit -20)' if not is_disabled else '[Kullanıldı] Kızılbaş Fetvası',
                    'callback': lambda: self._issue_fetva('kizilbas') if not is_disabled else None,
                    'disabled': is_disabled
                })
            
            cat_title = "Fetva Ver (50 altın)" if not is_disabled else "Fetva Ver (Beklemede)"
            self.action_menu.add_category(cat_title, fetva_items)
        
        # === 4. HOŞGÖRÜ POLİTİKASI ===
        tolerance_items = [
            {'text': 'Hoşgörüyü Artır (+10, millet sadakati artar)', 'callback': self._increase_tolerance},
            {'text': 'Hoşgörüyü Azalt (-10, Müslüman sadakati artar)', 'callback': self._decrease_tolerance},
        ]
        self.action_menu.add_category("Hoşgörü Politikası", tolerance_items)
    
    def _appoint_ulema(self, rank: UlemaRank):
        """Ulema ata"""
        gm = self.screen_manager.game_manager
        if gm:
            gm.religion.appoint_ulema(rank, gm.economy)
            self._update_panels()
            self._setup_action_menu()
    
    def _build_vakif(self, vakif_type: VakifType):
        """Vakıf inşa et"""
        gm = self.screen_manager.game_manager
        if gm:
            population = gm.population.population.total
            gm.religion.build_vakif(vakif_type, gm.economy, population)
            self._update_panels()
            self._setup_action_menu()
    
    def _issue_fetva(self, topic: str):
        """Fetva ver"""
        gm = self.screen_manager.game_manager
        if gm:
            result = gm.religion.issue_fetva(topic, gm.economy)
            if result.get('success'):
                effects = result.get('effects', {})
                if 'military_morale' in effects and hasattr(gm, 'military'):
                    gm.military.morale = min(100, gm.military.morale + effects['military_morale'])
                    
                if topic == 'ticaret' and hasattr(gm, 'economy'):
                    gm.economy.add_resources(gold=500)
                    
                if topic == 'vergi' and hasattr(gm, 'economy'):
                    gm.economy.add_resources(gold=400)
                    if hasattr(gm, 'population'):
                        gm.population.unrest = min(100, gm.population.unrest + 5)
                        
            self._update_panels()
            self._setup_action_menu()
    
    def _increase_tolerance(self):
        """Hoşgörüyü artır"""
        gm = self.screen_manager.game_manager
        if gm:
            if gm.religion.tolerance >= 100:
                self.audio.announce_action_result("Hoşgörü", False, "Hoşgörü zaten maksimum seviyede")
                return
                
            gm.religion.tolerance = min(100, gm.religion.tolerance + 10)
            
            # Gayrimüslim sadakati anında artar, Müslüman sadakati bir miktar düşer
            for millet, state in gm.religion.millet_states.items():
                if millet != Millet.MUSLIM:
                    state['loyalty'] = min(100, state['loyalty'] + 3)
            
            gm.religion.millet_states[Millet.MUSLIM]['loyalty'] = max(0, gm.religion.millet_states[Millet.MUSLIM]['loyalty'] - 2)
            
            self.audio.announce_action_result("Hoşgörü", True, "Artırıldı. Azınlık sadakati yükseldi")
            self._update_panels()
    
    def _decrease_tolerance(self):
        """Hoşgörüyü azalt"""
        gm = self.screen_manager.game_manager
        if gm:
            if gm.religion.tolerance <= 0:
                self.audio.announce_action_result("Hoşgörü", False, "Hoşgörü zaten minimum seviyede")
                return
                
            gm.religion.tolerance = max(0, gm.religion.tolerance - 10)
            # Müslüman sadakati artar
            gm.religion.millet_states[Millet.MUSLIM]['loyalty'] = min(
                100, gm.religion.millet_states[Millet.MUSLIM]['loyalty'] + 5)
            self.audio.announce_action_result("Hoşgörü", True, "-10 (Müslüman sadakati +5)")
            self._update_panels()
    
    def _go_back(self):
        self.screen_manager.change_screen(ScreenType.PROVINCE_VIEW)
    
    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_BACKSPACE or event.key == pygame.K_ESCAPE:
                self._go_back()
                return True
            
            # Menü navigasyonu
            result = self.action_menu.handle_event(event)
            if result is not None:
                return result
        
        return False
    
    def update(self, dt: float):
        pass
    
    def draw(self, surface: pygame.Surface):
        # Başlık
        header_font = self.get_header_font()
        title = header_font.render("Din ve Kültür", True, COLORS['text'])
        surface.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 20))
        
        # Paneller
        self.millet_panel.draw(surface)
        self.ulema_panel.draw(surface)
        self.vakif_panel.draw(surface)
        
        # Menü
        self.action_menu.draw(surface)
        
        # Geri butonu
        self.back_button.draw(surface)
