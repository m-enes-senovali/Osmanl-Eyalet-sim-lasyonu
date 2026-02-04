# -*- coding: utf-8 -*-
"""
Osmanlı Eyalet Yönetim Simülasyonu - Casusluk Ekranı
"""

import pygame
from ui.screen_manager import BaseScreen, ScreenType
from ui.components import Button, Panel, HierarchicalMenu
from config import COLORS, FONTS, SCREEN_WIDTH, SCREEN_HEIGHT
from game.systems.espionage import SpyType, OperationType, SPY_DEFINITIONS, OPERATION_DEFINITIONS


class EspionageScreen(BaseScreen):
    """Casusluk yönetim ekranı"""
    
    def __init__(self, screen_manager):
        super().__init__(screen_manager)
        
        # Paneller
        self.spy_panel = Panel(20, 80, 400, 250, "Casuslarınız")
        self.mission_panel = Panel(440, 80, 400, 250, "Aktif Görevler")
        self.intel_panel = Panel(860, 80, 380, 250, "İstihbarat")
        
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
            self._header_font = pygame.font.Font(None, FONTS['header'])
        return self._header_font
    
    def on_enter(self):
        self._update_panels()
        self._setup_action_menu()
    
    def announce_screen(self):
        self.audio.announce_screen_change("Casusluk")
        gm = self.screen_manager.game_manager
        if gm:
            gm.espionage.announce_status()
    
    def _update_panels(self):
        """Panel içeriklerini güncelle"""
        gm = self.screen_manager.game_manager
        if not gm:
            return
        
        esp = gm.espionage
        
        # Casus paneli - (label, value) format
        spy_items = []
        for spy in esp.spies:
            if spy.status != "dead":
                stats = SPY_DEFINITIONS[spy.spy_type]
                status_tr = {
                    'idle': 'Müsait',
                    'on_mission': 'Görevde',
                    'captured': 'Yakalandı'
                }.get(spy.status, spy.status)
                spy_items.append((f"{spy.name} ({stats.name_tr})", status_tr))
        
        if not spy_items:
            spy_items.append(("Durum", "Henüz casusunuz yok"))
        
        self.spy_panel.set_content(spy_items)
        
        # Görev paneli
        mission_items = []
        for mission in esp.active_missions:
            op_stats = OPERATION_DEFINITIONS[mission.operation]
            target_name = esp.targets.get(mission.target, {}).get('name', mission.target)
            mission_items.append((f"{op_stats.name_tr}", f"{target_name} ({mission.turns_remaining} tur)"))
        
        if not mission_items:
            mission_items.append(("Durum", "Aktif görev yok"))
        
        self.mission_panel.set_content(mission_items)
        
        # İstihbarat paneli
        intel_items = [
            ("Güvenlik", f"%{esp.security_level}"),
            ("Başarılı görev", str(esp.successful_missions)),
            ("Başarısız", str(esp.failed_missions)),
            ("Kaybedilen", str(esp.spies_lost)),
        ]
        self.intel_panel.set_content(intel_items)
    
    def _setup_action_menu(self):
        """Eylem menüsünü ayarla"""
        self.action_menu.clear()
        gm = self.screen_manager.game_manager
        if not gm:
            return
        
        esp = gm.espionage
        
        # Kadın karakter kontrolü
        is_female = gm.player and gm.player.gender.value == 'female'
        
        # === 1. CASUS TOPLAMA ===
        recruit_items = []
        for spy_type in SpyType:
            # Cariye sadece kadın karakter için
            if spy_type == SpyType.CARIYE and not is_female:
                continue
            
            stats = SPY_DEFINITIONS[spy_type]
            recruit_items.append({
                'text': f'{stats.name_tr} Topla ({stats.cost_gold} altın)',
                'callback': lambda st=spy_type: self._recruit_spy(st)
            })
        
        self.action_menu.add_category("Casus Topla", recruit_items)
        
        # === 2. GÖREV BAŞLAT ===
        available_spies = esp.get_available_spies()
        if available_spies:
            mission_items = []
            for spy in available_spies:
                spy_stats = SPY_DEFINITIONS[spy.spy_type]
                
                # Her casus için hedef seçimi alt menüsü
                target_items = []
                for target_id, target_info in esp.targets.items():
                    op_items = []
                    for op in OperationType:
                        # Harem İstihbaratı sadece kadın karakter için
                        if op == OperationType.HAREM_ISTIHBARATI and not is_female:
                            continue
                        
                        op_stats = OPERATION_DEFINITIONS[op]
                        if spy.skill >= op_stats.required_skill:
                            op_items.append({
                                'text': f'{op_stats.name_tr} ({op_stats.base_cost} altın)',
                                'callback': lambda s=spy.spy_id, o=op, t=target_id: self._start_mission(s, o, t)
                            })
                    
                    if op_items:
                        target_items.append({
                            'text': target_info['name'],
                            'children': op_items
                        })
                
                if target_items:
                    mission_items.append({
                        'text': f'{spy.name} ({spy_stats.name_tr})',
                        'children': target_items
                    })
            
            if mission_items:
                self.action_menu.add_category("Görev Başlat", mission_items)
        
        # === 3. KARŞI İSTİHBARAT ===
        counter_items = [
            {'text': 'Güvenliği Artır (100 altın)', 'callback': self._increase_security}
        ]
        self.action_menu.add_category("Karşı İstihbarat", counter_items)
    
    def _recruit_spy(self, spy_type: SpyType):
        """Casus topla"""
        gm = self.screen_manager.game_manager
        if gm:
            gm.espionage.recruit_spy(spy_type, gm.economy)
            self._update_panels()
            self._setup_action_menu()
    
    def _start_mission(self, spy_id: str, operation: OperationType, target: str):
        """Görev başlat"""
        gm = self.screen_manager.game_manager
        if gm:
            gm.espionage.start_mission(spy_id, operation, target, gm.economy)
            self._update_panels()
            self._setup_action_menu()
    
    def _increase_security(self):
        """Güvenliği artır"""
        gm = self.screen_manager.game_manager
        if gm and gm.economy.can_afford(gold=100):
            gm.economy.spend(gold=100)
            gm.espionage.security_level = min(100, gm.espionage.security_level + 10)
            self.audio.announce_action_result("Güvenlik", True, "+10")
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
        title = header_font.render("Casusluk", True, COLORS['text'])
        surface.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 20))
        
        # Paneller
        self.spy_panel.draw(surface)
        self.mission_panel.draw(surface)
        self.intel_panel.draw(surface)
        
        # Menü
        self.action_menu.draw(surface)
        
        # Geri butonu
        self.back_button.draw(surface)
