# -*- coding: utf-8 -*-
"""
Osmanlı Eyalet Yönetim Simülasyonu - Askeri Ekran
"""

import pygame
from ui.screen_manager import BaseScreen, ScreenType
from ui.components import Button, Panel, HierarchicalMenu
from game.systems.military import UnitType, UNIT_DEFINITIONS
from config import COLORS, FONTS, SCREEN_WIDTH, SCREEN_HEIGHT, get_font


class MilitaryScreen(BaseScreen):
    """Askeri yönetim ekranı"""
    
    def __init__(self, screen_manager):
        super().__init__(screen_manager)
        
        # Paneller (üst kısım)
        self.army_panel = Panel(20, 80, 400, 250, "Ordu Durumu")
        self.training_panel = Panel(440, 80, 400, 150, "Eğitim Kuyruğu")
        self.stats_panel = Panel(440, 250, 400, 80, "İstatistikler")
        
        # Hiyerarşik menü (alt kısım)
        self.action_menu = HierarchicalMenu(
            x=20,
            y=360,
            width=820,
            item_height=40
        )
        
        self._header_font = None
        self._font = None
        
    def get_header_font(self):
        if self._header_font is None:
            self._header_font = get_font(FONTS['header'])
        return self._header_font
        
    def get_font(self):
        if self._font is None:
            self._font = get_font(FONTS['body'])
        return self._font
    
    def _setup_action_menu(self):
        """Hiyerarşik askeri menüyü ayarla"""
        # Mevcut menü durumunu kaydet (başlıklar listesi)
        saved_stack_titles = [m['title'] for m in self.action_menu.menu_stack]
        saved_index = self.action_menu.selected_index
        
        self.action_menu.clear()
        gm = self.screen_manager.game_manager
        if not gm:
            return
        
        mil = gm.military
        eco = gm.economy
        
        # === 1. ASKER TOPLA (her birim tipi alt menü) ===
        for unit_type in UnitType:
            stats = UNIT_DEFINITIONS[unit_type]
            current_count = mil.units.get(unit_type, 0)
            
            # Bu birim için toplama seçenekleri
            unit_items = []
            
            # Mevcut sayı bilgisi
            unit_items.append({
                'text': f"Mevcut: {current_count} adet",
                'callback': None
            })
            unit_items.append({
                'text': f"Maliyet: {stats.cost_gold} altın/birim, {stats.train_time} tur eğitim",
                'callback': None
            })
            unit_items.append({'text': '', 'is_separator': True})
            
            # Eğitim seçenekleri
            for count in [10, 50, 100]:
                cost = stats.cost_gold * count
                can_afford = eco.can_afford(gold=cost)
                if can_afford:
                    unit_items.append({
                        'text': f"+{count} topla ({cost} altın)",
                        'callback': lambda ut=unit_type, c=count: self._recruit(ut, c)
                    })
                else:
                    unit_items.append({
                        'text': f"+{count} ({cost} altın) - Yetersiz",
                        'callback': None
                    })
            
            # Maksimum topla
            max_affordable = eco.resources.gold // stats.cost_gold if stats.cost_gold > 0 else 0
            if max_affordable >= 10:
                max_count = min(max_affordable, 200)
                unit_items.append({
                    'text': f"Maksimum: {max_count} topla ({stats.cost_gold * max_count} altın)",
                    'callback': lambda ut=unit_type, c=max_count: self._recruit(ut, c)
                })
            
            self.action_menu.add_category(f"{stats.name_tr} ({current_count})", unit_items)
        
        # === 2. EĞİTİM KUYRUĞU ===
        training_items = []
        if mil.training_queue:
            for item in mil.training_queue:
                stats = UNIT_DEFINITIONS[item.unit_type]
                training_items.append({
                    'text': f"{item.count}x {stats.name_tr}: {item.turns_remaining} tur kaldı",
                    'callback': None
                })
        else:
            training_items.append({'text': "Eğitimde birim yok", 'callback': None})
        
        training_items.append({'text': '', 'is_separator': True})
        training_items.append({
            'text': f"Toplam eğitimde: {sum(i.count for i in mil.training_queue)} asker",
            'callback': None
        })
        
        self.action_menu.add_category("Eğitim Kuyruğu", training_items)
        
        # === 3. ORDU DURUMU ===
        # Topçu sayısı
        total_cannons = 0
        if hasattr(gm, 'artillery'):
            total_cannons = len(gm.artillery.cannons)
            
        durum_items = [
            {'text': f"Toplam Asker: {mil.get_total_soldiers()}", 'callback': None},
            {'text': f"Toplam Top: {total_cannons}", 'callback': None},
            {'text': f"Toplam Askeri Güç: {mil.get_total_power()}", 'callback': None},
            {'text': f"Bakım Maliyeti: {mil.get_maintenance_cost()} altın/tur", 'callback': None},
            {'text': '', 'is_separator': True},
            {'text': f"Moral: %{mil.morale}", 'callback': None},
            {'text': f"Zaferler: {mil.total_victories}", 'callback': None},
            {'text': f"Kayıplar: {mil.total_losses}", 'callback': None},
        ]
        
        self.action_menu.add_category("Ordu Durumu", durum_items)
        
        # === 4. EŞKIYA BASTIR ===
        self.action_menu.add_action("Eşkıya Bastır", self._fight_bandits)
        
        commander_items = []
        
        trait_dict = {
            'SIEGE_MASTER': 'Kuşatma Ustası',
            'LOGISTICIAN': 'Lojistik Uzmanı',
            'AGGRESSOR': 'Serdengeçti',
            'TACTICIAN': 'Taktisyen',
            'DEFENDER': 'Savunma Ustası'
        }
        
        if mil.assigned_commander:
            trait_name = mil.assigned_commander.trait.name
            trait_tr = trait_dict.get(trait_name, trait_name)
            commander_items.append({
                'text': f"Aktif Paşa: {mil.assigned_commander.name} ({trait_tr})",
                'callback': None
            })
            commander_items.append({
                'text': "Paşayı Görevden Al",
                'callback': self._unassign_commander
            })
        else:
            commander_items.append({
                'text': "Atanmış Paşa Yok (Sefere lidersiz çıkılacak)",
                'callback': None
            })
        
        commander_items.append({'text': '', 'is_separator': True})
        
        for cmdr in mil.commanders:
            if cmdr != mil.assigned_commander:
                trait_name = cmdr.trait.name
                trait_tr = trait_dict.get(trait_name, trait_name)
                commander_items.append({
                    'text': f"Ata: {cmdr.name} (Yetenek: {trait_tr}, Seviye: {cmdr.level})",
                    'callback': lambda c=cmdr: self._assign_commander(c)
                })
        
        self.action_menu.add_category("Komutanlar (Paşalar)", commander_items)
        
        # === GERİ BUTONU ===
        self.action_menu.add_back_button()
        
        # Durumu geri yükle
        self._restore_menu_state(saved_stack_titles, saved_index)

    def _restore_menu_state(self, stack_titles, saved_index):
        """Menü durumunu başlık eşleşmesiyle geri yükle"""
        current_menu = self.action_menu.root_menu
        
        for title in stack_titles:
            # Bu başlıklı öğeyi bul
            found = False
            for item in current_menu:
                # İsim eşleşmesi (kısmi eşleşme çünkü sayılar değişebilir "Yeniçeri (100)" -> "Yeniçeri (110)")
                # Parantez öncesi kısmı kontrol et
                item_text = item.get('text', '').split('(')[0].strip()
                target_title = title.split('(')[0].strip()
                
                if item_text == target_title and item.get('submenu'):
                    self.action_menu.menu_stack.append({
                        'title': item['text'],
                        'items': item['submenu']
                    })
                    current_menu = item['submenu']
                    found = True
                    break
            
            if not found:
                break
        
        # İndeksi geri yükle (eğer geçerliyse)
        if saved_index < len(current_menu):
            self.action_menu.selected_index = saved_index
        else:
            self.action_menu.selected_index = 0

    def on_enter(self):
        self._update_panels()
        # İlk girişte temiz kurulum
        self.action_menu.clear()
        self._setup_action_menu()
        # Stack temizlendiği için restore çalışmayacak, bu doğru
        self.audio.play_game_sound('military', 'march')
    
    def announce_screen(self):
        self.audio.announce_screen_change("Askeri Yönetim")
        gm = self.screen_manager.game_manager
        if gm:
            gm.military.announce_army()
    
    def _update_panels(self):
        """Panelleri güncelle"""
        gm = self.screen_manager.game_manager
        if not gm:
            return
        
        mil = gm.military
        
        # Ordu paneli
        self.army_panel.clear()
        for unit_type, count in mil.units.items():
            stats = UNIT_DEFINITIONS[unit_type]
            self.army_panel.add_item(stats.name_tr, str(count))
        self.army_panel.add_item("", "")
        self.army_panel.add_item("Toplam Asker", str(mil.get_total_soldiers()))
        self.army_panel.add_item("Toplam Güç", str(mil.get_total_power()))
        self.army_panel.add_item("Bakım Maliyeti", f"{mil.get_maintenance_cost()}/tur")
        
        # Eğitim paneli
        self.training_panel.clear()
        if mil.training_queue:
            for item in mil.training_queue:
                stats = UNIT_DEFINITIONS[item.unit_type]
                self.training_panel.add_item(
                    f"{item.count}x {stats.name_tr}",
                    f"{item.turns_remaining} tur"
                )
        else:
            self.training_panel.add_item("Eğitim yok", "")
        
        # İstatistik paneli
        self.stats_panel.clear()
        self.stats_panel.add_item("Moral", f"%{mil.morale}")
        self.stats_panel.add_item("Zaferler", str(mil.total_victories))
        self.stats_panel.add_item("Kayıplar", str(mil.total_losses))
    
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
                    gm.military.announce_army()
                return True
        
        return False
    
    def _announce_unit_breakdown(self):
        """Detaylı birim dökümü"""
        gm = self.screen_manager.game_manager
        if not gm:
            return
        
        mil = gm.military
        
        # Kara kuvvetleri
        lines = []
        lines.append(f"Piyade: {mil.infantry} asker")
        lines.append(f"Süvari: {mil.cavalry} atlı")
        lines.append(f"Topçu mürettebatı: {mil.artillery_crew} kişi")
        lines.append(f"Akıncı: {mil.raiders} kişi")
        lines.append(f"Toplam kara gücü: {mil.get_total_soldiers()} asker, güç: {mil.get_total_power()}")
        
        # Toplar
        if hasattr(gm, 'artillery') and gm.artillery.cannons:
            counts = gm.artillery.get_cannon_counts()
            cannon_parts = []
            from game.systems.artillery import CannonType, CANNON_DEFINITIONS
            for ct in CannonType:
                if counts[ct] > 0:
                    cannon_parts.append(f"{counts[ct]} {CANNON_DEFINITIONS[ct].name}")
            if cannon_parts:
                lines.append(f"Toplar: {', '.join(cannon_parts)}")
                lines.append(f"Toplam top gücü: {gm.artillery.get_total_power()}")
        
        # Gemiler
        if hasattr(gm, 'naval') and gm.naval.ships:
            counts = gm.naval.get_ship_counts()
            ship_parts = []
            from game.systems.naval import ShipType, SHIP_DEFINITIONS
            for st in ShipType:
                if counts[st] > 0:
                    ship_parts.append(f"{counts[st]} {SHIP_DEFINITIONS[st].name}")
            if ship_parts:
                lines.append(f"Gemiler: {', '.join(ship_parts)}")
                lines.append(f"Filo savaş gücü: {gm.naval.get_fleet_power()}")
        
        full_text = ". ".join(lines)
        self.audio.speak(full_text, interrupt=True)
    
    def _announce_next_panel(self):
        """Sıradaki paneli duyur"""
        if not hasattr(self, '_current_panel'):
            self._current_panel = 0
        
        panels = [self.army_panel, self.training_panel, self.stats_panel]
        self._current_panel = (self._current_panel + 1) % len(panels)
        panels[self._current_panel].announce_content()
    
    def _announce_training_queue(self):
        """Eğitim kuyruğunu duyur"""
        gm = self.screen_manager.game_manager
        if not gm:
            return
        
        mil = gm.military
        
        if not mil.training_queue:
            self.audio.speak(
                "Eğitim kuyruğu boş. Asker topladığınızda burada görünecek.",
                interrupt=True
            )
            return
        
        total_units = sum(item.count for item in mil.training_queue)
        self.audio.speak(f"Eğitim kuyruğunda {total_units} asker:", interrupt=True)
        
        for item in mil.training_queue:
            stats = UNIT_DEFINITIONS[item.unit_type]
            if item.turns_remaining == 1:
                self.audio.speak(
                    f"{item.count} {stats.name_tr}: Bu tur sonunda hazır olacak!",
                    interrupt=False
                )
            else:
                self.audio.speak(
                    f"{item.count} {stats.name_tr}: {item.turns_remaining} tur sonra hazır.",
                    interrupt=False
                )
        
        self.audio.speak(
            "Tur geçirmek için ana ekranda Boşluk tuşuna basın.",
            interrupt=False
        )
    
    def update(self, dt: float):
        self._update_panels()
        self.action_menu.update()  # İlk duyuruyu yapar
    
    def draw(self, surface: pygame.Surface):
        # Başlık
        header_font = self.get_header_font()
        title = header_font.render("ASKERI YONETIM", True, COLORS['gold'])
        surface.blit(title, (20, 20))
        
        # Paneller (üst kısım)
        self.army_panel.draw(surface)
        self.training_panel.draw(surface)
        self.stats_panel.draw(surface)
        
        # Hiyerarşik menü (alt kısım)
        self.action_menu.draw(surface)
    
    def _draw_unit_info(self, surface: pygame.Surface):
        """Seçili birim bilgilerini göster"""
        gm = self.screen_manager.game_manager
        if not gm:
            return
        
        # Bilgi kutusu
        rect = pygame.Rect(700, 460, 540, 130)
        pygame.draw.rect(surface, COLORS['panel_bg'], rect, border_radius=10)
        pygame.draw.rect(surface, COLORS['panel_border'], rect, width=2, border_radius=10)
        
        # Hangi birim seçili?
        if not self.recruit_menu.items:
            return
        
        selected_idx = self.recruit_menu.selected_index
        
        # Menü yapısı: Her birim için 1 başlık + 4 seçenek (10, 50, 100, maksimum) = ~5 item
        # Hangi birim grubundayız hesapla
        items_per_unit = 5  # Başlık + 4 seçenek (maksimum varsa)
        unit_types = list(UnitType)
        
        # Güvenli index hesaplama
        unit_index = min(selected_idx // items_per_unit, len(unit_types) - 1)
        unit_type = unit_types[unit_index]
        stats = UNIT_DEFINITIONS[unit_type]
        current_count = gm.military.units.get(unit_type, 0)
        
        font = get_font(FONTS['body'])
        small_font = get_font(FONTS['small'])
        
        # Birim adı ve mevcut sayı
        name = font.render(f"{stats.name_tr} - Mevcut: {current_count}", True, COLORS['gold'])
        surface.blit(name, (rect.x + 20, rect.y + 15))
        
        # İstatistikler
        info_lines = [
            f"Saldırı: {stats.attack} | Savunma: {stats.defense} | Hız: {stats.speed}",
            f"Maliyet: {stats.cost_gold} Altın, {stats.cost_food} Zahire",
            f"Eğitim: {stats.train_time} tur | Bakım: {stats.maintenance}/tur"
        ]
        
        for i, line in enumerate(info_lines):
            text = small_font.render(line, True, COLORS['text'])
            surface.blit(text, (rect.x + 20, rect.y + 45 + i * 25))
    
    def _recruit(self, unit_type: UnitType, count: int):
        """Asker topla"""
        gm = self.screen_manager.game_manager
        if gm:
            gm.military.recruit(unit_type, count, gm.economy)
            self.audio.play_game_sound('military', 'recruit')
            self._update_panels()
            self._setup_action_menu()  # Menüyü güncelle
    
    def _fight_bandits(self):
        """Eşkıya bastır"""
        gm = self.screen_manager.game_manager
        if gm:
            result = gm.military.fight_bandits()
            
            if result['victory']:
                self.audio.announce(
                    f"Zafer! Eşkıyalar bastırıldı. "
                    f"Kayıplar: {sum(result['losses'].values())} asker"
                )
            else:
                self.audio.announce(
                    f"Mağlubiyet! Ordu geri çekildi. "
                    f"Kayıplar: {sum(result['losses'].values())} asker"
                )
            
            self._update_panels()
            
    def _assign_commander(self, commander):
        """Orduya komutan ata"""
        gm = self.screen_manager.game_manager
        if gm:
            gm.military.assigned_commander = commander
            commander.assigned = True
            
            # Sesli geri bildirim
            trait_tr = {
                'SIEGE_MASTER': 'Kuşatma Ustası',
                'LOGISTICIAN': 'Lojistik Uzmanı',
                'AGGRESSOR': 'Serdengeçti',
                'TACTICIAN': 'Taktisyen',
                'DEFENDER': 'Savunma Ustası'
            }.get(commander.trait.name, commander.trait.name)
            
            self.audio.announce(f"{commander.name}, ordu komutanı olarak atandı. Yeteneği: {trait_tr}")
            self._setup_action_menu()
            
    def _unassign_commander(self):
        """Mevcut komutanı görevden al"""
        gm = self.screen_manager.game_manager
        if gm and gm.military.assigned_commander:
            name = gm.military.assigned_commander.name
            gm.military.assigned_commander.assigned = False
            gm.military.assigned_commander = None
            self.audio.announce(f"{name} görevden alındı. Ordu şu an lidersiz.")
            self._setup_action_menu()
    
    def _go_back(self):
        """Geri dön"""
        if getattr(self.screen_manager, 'is_multiplayer_mode', False):
            self.screen_manager.change_screen(ScreenType.MULTIPLAYER_GAME)
        else:
            self.screen_manager.change_screen(ScreenType.PROVINCE_VIEW)
