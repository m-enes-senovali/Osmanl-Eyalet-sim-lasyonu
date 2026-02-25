# -*- coding: utf-8 -*-
"""
Osmanlı Eyalet Yönetim Simülasyonu - Ana Oyun Ekranı (Eyalet Görünümü)
"""

import pygame
from ui.screen_manager import BaseScreen, ScreenType
from ui.components import Button, Panel, ProgressBar, MenuList
from config import COLORS, FONTS, SCREEN_WIDTH, SCREEN_HEIGHT, KEYBINDS, get_font
from game.tutorial import get_tutorial


class ProvinceViewScreen(BaseScreen):
    """Ana oyun ekranı - Eyalet genel görünümü"""
    
    def __init__(self, screen_manager):
        super().__init__(screen_manager)
        
        # Paneller
        self._create_panels()
        
        # Yan menü
        self._create_side_menu()
        
        # Butonlar
        self._create_buttons()
        
        # Fontlar
        self._header_font = None
        self._info_font = None
        
        # Seçili panel index (klavye navigasyonu için)
        self.selected_panel_index = 0
        self.panels = ['resources', 'status', 'menu']
        
        # Erişilebilir istatistik gezinme modu
        self._stats_mode = False
        self._stats_items = []
        self._stats_index = 0
        
        # Çıkış onayı durumu
        self.exit_confirmation_pending = False
    
    def _create_panels(self):
        """Bilgi panellerini oluştur"""
        # Kaynak paneli (üst)
        self.resource_panel = Panel(20, 20, SCREEN_WIDTH - 40, 100, "Kaynaklar")
        
        # Durum paneli (sol)
        self.status_panel = Panel(20, 140, 350, 450, "Eyalet Durumu")
        
        # Özet paneli (sağ alt)
        self.summary_panel = Panel(390, 400, SCREEN_WIDTH - 410, 190)
    
    def _create_side_menu(self):
        """Yan menü oluştur"""
        self.side_menu = MenuList(
            x=390,
            y=150,
            width=300,
            item_height=50
        )
        
        self.side_menu.add_item("Ekonomi", lambda: self._open_screen(ScreenType.ECONOMY), "e")
        self.side_menu.add_item("Ordu", lambda: self._open_screen(ScreenType.MILITARY), "m")
        self.side_menu.add_item("İnşaat", lambda: self._open_screen(ScreenType.CONSTRUCTION), "c")
        self.side_menu.add_item("Diplomasi", lambda: self._open_screen(ScreenType.DIPLOMACY), "d")
        self.side_menu.add_item("Halk", lambda: self._open_screen(ScreenType.POPULATION), "p")
        self.side_menu.add_item("Loncalar", lambda: self._open_screen(ScreenType.GUILD), "l")
        self.side_menu.add_item("Casusluk", lambda: self._open_screen(ScreenType.ESPIONAGE), "s")
        self.side_menu.add_item("Din", lambda: self._open_screen(ScreenType.RELIGION), "")
        self.side_menu.add_item("Başarılar", lambda: self._open_screen(ScreenType.ACHIEVEMENT), "b")
        self.side_menu.add_item("Geçmiş", lambda: self._open_screen(ScreenType.HISTORY), "g")
        self.side_menu.add_item("Topçu", lambda: self._open_screen(ScreenType.ARTILLERY), "t")
        self.side_menu.add_item("Akın/Savaş", lambda: self._open_screen(ScreenType.WARFARE), "k")
        self.side_menu.add_item("Divan", lambda: self._open_screen(ScreenType.DIVAN), "v")
        
        # Donanma sadece kıyı eyaletlerinde (on_enter'da eklenir)
        self._side_menu_needs_coastal_update = True
    
    def _create_buttons(self):
        """Butonları oluştur"""
        # Tur bitir butonu
        self.next_turn_button = Button(
            x=SCREEN_WIDTH - 220,
            y=140,
            width=200,
            height=50,
            text="Tur Bitir",
            shortcut="space",
            callback=self._on_next_turn
        )
        
        # Kaydet butonu
        self.save_button = Button(
            x=SCREEN_WIDTH - 220,
            y=200,
            width=95,
            height=40,
            text="Kaydet",
            shortcut="f5",
            callback=self._on_save
        )
        
        # Ana menü butonu
        self.menu_button = Button(
            x=SCREEN_WIDTH - 115,
            y=200,
            width=95,
            height=40,
            text="Menü",
            shortcut="escape",
            callback=self._on_main_menu
        )
    
    def get_header_font(self):
        if self._header_font is None:
            self._header_font = get_font(FONTS['header'])
        return self._header_font
    
    def get_info_font(self):
        if self._info_font is None:
            self._info_font = get_font(FONTS['body'])
        return self._info_font
    
    def on_enter(self):
        """Ekrana girişte panelleri güncelle"""
        self._update_panels()
        self.audio.play_ambient('city')
        
        is_tutorial_active = False
        try:
            tutorial = get_tutorial()
            is_tutorial_active = tutorial.is_active
        except Exception:
            pass
        
        # Donanma sadece kıyı eyaletlerinde
        if self._side_menu_needs_coastal_update:
            gm = self.screen_manager.game_manager
            if gm and gm.province.is_coastal:
                # Ordu'dan sonra (index 2) Donanma ekle
                self.side_menu.items.insert(2, ("Donanma", lambda: self._open_screen(ScreenType.NAVAL), "n"))
            self._side_menu_needs_coastal_update = False
        
        # İlk giriş rehberi
        gm = self.screen_manager.game_manager
        if gm and gm.turn_count == 0:
            tutorial = get_tutorial()
            tutorial.welcome_message()
    
    def announce_screen(self):
        gm = self.screen_manager.game_manager
        if gm and gm.player:
            title = gm.player.get_full_title()
            self.audio.announce_screen_change(f"{gm.province.name} - {title}")
            self.audio.speak(f"Yıl {gm.current_year}, Altın: {gm.economy.resources.gold:,}", interrupt=False)
        else:
            self.audio.announce_screen_change("Eyalet Yönetimi")
            if gm:
                self.audio.speak(f"{gm.province.name}, Yıl {gm.current_year}", interrupt=False)
        self.audio.speak("H tuşuna basarak yardım alabilirsiniz.", interrupt=False)
    
    def _update_panels(self):
        """Panel içeriklerini güncelle"""
        gm = self.screen_manager.game_manager
        if not gm:
            return
        
        # Kaynak paneli
        self.resource_panel.clear()
        self.resource_panel.add_item("Altın", f"{gm.economy.resources.gold:,}")
        self.resource_panel.add_item("Zahire", f"{gm.economy.resources.food:,}")
        self.resource_panel.add_item("Kereste", f"{gm.economy.resources.wood:,}")
        self.resource_panel.add_item("Demir", f"{gm.economy.resources.iron:,}")
        self.resource_panel.add_item("Bakır", f"{gm.economy.resources.copper:,}")
        self.resource_panel.add_item("Barut", f"{gm.economy.resources.gunpowder:,}")
        
        # Durum paneli — önem sırasına göre (Tab ile ilk okunanlar üstte)
        self.status_panel.clear()
        self.status_panel.add_item("Yıl", str(gm.current_year))
        self.status_panel.add_item("Tur", str(gm.turn_count))
        self.status_panel.add_item("", "")  # boşluk
        self.status_panel.add_item("Padişah Sadakati", f"%{gm.diplomacy.sultan_loyalty}")
        self.status_panel.add_item("Halk Memnuniyeti", f"%{gm.population.happiness}")
        self.status_panel.add_item("Nüfus", f"{gm.population.population.total:,}")
        self.status_panel.add_item("Askeri Güç", f"{gm.military.get_total_power():,}")
        
        # Vergi tipi gösterimi
        tax_labels = {
            "salyanesiz": "Salyanesiz (Tımar)",
            "salyaneli": "Salyaneli (Nakit)",
            "karma": "Karma",
        }
        tax_type = getattr(gm.province, 'tax_type', 'salyanesiz')
        self.status_panel.add_item("Vergi Tipi", tax_labels.get(tax_type, tax_type))
        
        # Karakter bonusları gösterimi
        if gm.player:
            self.status_panel.add_item("", "")  # boşluk
            self.status_panel.add_item("Karakter", gm.player.get_full_title())
            
            if gm.player.gender.value == 'female':
                self.status_panel.add_item("Diplomasi", "+%20")
                self.status_panel.add_item("Ticaret", "+%15")
                self.status_panel.add_item("Vakıf", "+%30")
                # Aktif malus göster
                bey_malus = gm.player.get_malus('bey_loyalty')
                if bey_malus < 0:
                    remaining = max(0, 40 - gm.player.turns_as_governor)
                    self.status_panel.add_item("⚠ Bey Şüphesi", f"%{int(abs(bey_malus)*100)} ({remaining} tur)")
            else:
                self.status_panel.add_item("Akın Gücü", "+%20")
                self.status_panel.add_item("Yeniçeri", "+%15")
                self.status_panel.add_item("Kuşatma", "+%10")
        
        # İsyan uyarısı
        if gm.population.active_revolt:
            self.status_panel.add_item("⚠ DURUM", "İSYAN VAR!")
    
    def handle_event(self, event) -> bool:
        # İstatistik gezinme modu aktifse
        if self._stats_mode:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_DOWN:
                    self._stats_index = min(self._stats_index + 1, len(self._stats_items) - 1)
                    self.audio.speak(self._stats_items[self._stats_index], interrupt=True)
                    return True
                elif event.key == pygame.K_UP:
                    self._stats_index = max(self._stats_index - 1, 0)
                    self.audio.speak(self._stats_items[self._stats_index], interrupt=True)
                    return True
                elif event.key == pygame.K_HOME:
                    self._stats_index = 0
                    self.audio.speak(self._stats_items[0], interrupt=True)
                    return True
                elif event.key == pygame.K_END:
                    self._stats_index = len(self._stats_items) - 1
                    self.audio.speak(self._stats_items[self._stats_index], interrupt=True)
                    return True
                elif event.key in (pygame.K_ESCAPE, pygame.K_TAB):
                    self._close_stats_mode()
                    return True
                elif event.key == pygame.K_SPACE:
                    # Space tuşuyla tur bitirme stats modunda da çalışsın
                    self._close_stats_mode()
                    self._on_next_turn()
                    return True
            return True  # Stats modundayken diğer tuşları engelle
        
        # Çıkış onayı bekleniyorsa
        if self.exit_confirmation_pending:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_e:  # Evet - Kaydet ve çık
                    gm = self.screen_manager.game_manager
                    if gm and gm.save_slot:
                        gm.save_game(gm.save_slot)
                        self.audio.speak("Oyun kaydedildi. Ana menüye dönülüyor.", interrupt=True)
                    else:
                        gm.save_game(1)  # Varsayılan yuva 1
                        self.audio.speak("Yuva 1'e kaydedildi. Ana menüye dönülüyor.", interrupt=True)
                    self.exit_confirmation_pending = False
                    self.screen_manager.change_screen(ScreenType.MAIN_MENU)
                    return True
                elif event.key == pygame.K_h:  # Hayır - Kaydetmeden çık
                    self.audio.speak("Ana menüye dönülüyor.", interrupt=True)
                    self.exit_confirmation_pending = False
                    self.screen_manager.change_screen(ScreenType.MAIN_MENU)
                    return True
                elif event.key == pygame.K_ESCAPE or event.key == pygame.K_i:  # İptal
                    self.audio.speak("Çıkış iptal edildi.", interrupt=True)
                    self.exit_confirmation_pending = False
                    return True
            return True  # Diğer tuşları engelle
        
        # ESC - Çıkış onayı iste
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.exit_confirmation_pending = True
            self.audio.speak(
                "Oyundan çıkmak istiyor musunuz? "
                "E tuşuna basın kaydet ve çık, H tuşuna basın kaydetmeden çık, "
                "I veya Escape tuşuna basın iptal.",
                interrupt=True
            )
            return True
        
        # Yan menü
        if self.side_menu.handle_event(event):
            return True
        
        # Butonlar
        if self.next_turn_button.handle_event(event):
            return True
        if self.save_button.handle_event(event):
            return True
        if self.menu_button.handle_event(event):
            return True
        
        # Klavye kısayolları
        if event.type == pygame.KEYDOWN:
            gm = self.screen_manager.game_manager
            tutorial = get_tutorial()
            
            # H - Yardım (Kethüda)
            if event.key == pygame.K_h:
                tutorial.show_quick_help()
                return True
            
            # T - Durum ipucu (Kethüda tavsiyeleri)
            if event.key == pygame.K_t:
                if gm:
                    tutorial.get_contextual_tip(gm)
                return True
            
            # F1 - Tam durum özeti
            if event.key == pygame.K_F1:
                if gm:
                    gm.announce_full_status()
                return True
            
            # F2 - Ekonomi rehberi
            if event.key == pygame.K_F2:
                tutorial.economy_guide()
                return True
            
            # F3 - Askeri rehber
            if event.key == pygame.K_F3:
                tutorial.military_guide()
                return True
            
            # F4 - İnşaat rehberi
            if event.key == pygame.K_F4:
                tutorial.construction_guide()
                return True
            
            # R - Kaynakları oku (Altın, Zahire, Kereste, Demir)
            if event.key == pygame.K_r:
                self._announce_resources()
                return True
            
            # G - Sadece altın
            if event.key == pygame.K_g:
                if gm:
                    self.audio.speak(f"Altın: {gm.economy.resources.gold:,}", interrupt=True)
                return True
            
            # S - Durum özeti (Nüfus, Memnuniyet, Askeri Güç, Sadakat)
            if event.key == pygame.K_s:
                self._announce_status()
                return True
            
            # I - Gelir/Gider özeti
            if event.key == pygame.K_i:
                self._announce_income()
                return True
            
            # O - İşçi yönetimi ekranı
            if event.key == pygame.K_o:
                self.screen_manager.change_screen(ScreenType.WORKERS)
                return True
            
            # Y - Yıl ve tur bilgisi
            if event.key == pygame.K_y:
                if gm:
                    self.audio.speak(f"Yıl {gm.current_year}, {gm.current_month}. ay, {gm.turn_count}. tur", interrupt=True)
                return True
            
            # W - Uyarıları oku (isyan, düşük kaynak vb.)
            if event.key == pygame.K_w:
                self._announce_warnings()
                return True
            
            # K - Kılıç (Savaş) ekranı
            if event.key == pygame.K_k:
                self.screen_manager.change_screen(ScreenType.WARFARE)
                return True
            
            # X - Ticaret (eXchange) ekranı
            if event.key == pygame.K_x:
                self.screen_manager.change_screen(ScreenType.TRADE)
                return True
            
            # Page Up - Müzik sesini artır
            if event.key == pygame.K_PAGEUP:
                new_vol = min(1.0, self.audio.music_volume + 0.1)
                self.audio.set_music_volume(new_vol)
                self.audio.speak(f"Müzik sesi: yüzde {int(new_vol * 100)}", interrupt=True)
                return True
            
            # Page Down - Müzik sesini azalt
            if event.key == pygame.K_PAGEDOWN:
                new_vol = max(0.0, self.audio.music_volume - 0.1)
                self.audio.set_music_volume(new_vol)
                self.audio.speak(f"Müzik sesi: yüzde {int(new_vol * 100)}", interrupt=True)
                return True
            
            # Tab - Erişilebilir istatistik paneli aç/kapat
            if event.key == pygame.K_TAB:
                if self._stats_mode:
                    self._close_stats_mode()
                else:
                    self._open_stats_mode()
                return True
        
        return False
    
    def _announce_resources(self):
        """Tüm kaynakları oku"""
        gm = self.screen_manager.game_manager
        if not gm:
            return
        
        res = gm.economy.resources
        self.audio.speak("Kaynaklar:", interrupt=True)
        self.audio.speak(f"Altın: {res.gold:,}", interrupt=False)
        self.audio.speak(f"Zahire: {res.food:,}", interrupt=False)
        self.audio.speak(f"Kereste: {res.wood:,}", interrupt=False)
        self.audio.speak(f"Demir: {res.iron:,}", interrupt=False)
        self.audio.speak(f"Taş: {res.stone:,}", interrupt=False)
        self.audio.speak(f"Bakır: {res.copper:,}", interrupt=False)
        self.audio.speak(f"Barut: {res.gunpowder:,}", interrupt=False)
    
    def _announce_status(self):
        """Durum özetini oku"""
        gm = self.screen_manager.game_manager
        if not gm:
            return
        
        self.audio.speak("Eyalet Durumu:", interrupt=True)
        self.audio.speak(f"Nüfus: {gm.population.population.total:,}", interrupt=False)
        self.audio.speak(f"Halk Memnuniyeti: yüzde {gm.population.happiness}", interrupt=False)
        self.audio.speak(f"Askeri Güç: {gm.military.get_total_power():,}", interrupt=False)
        self.audio.speak(f"Padişah Sadakati: yüzde {gm.diplomacy.sultan_loyalty}", interrupt=False)
    
    # ===== ERİŞİLEBİLİR İSTATİSTİK GEZİNME PANELİ =====
    
    def _open_stats_mode(self):
        """İstatistik gezinme modunu aç — Tab ile aktifleştir"""
        self._stats_items = self._build_stats_items()
        if not self._stats_items:
            self.audio.speak("İstatistik bilgisi yok.", interrupt=True)
            return
        self._stats_mode = True
        self._stats_index = 0
        self.audio.speak(
            f"İstatistik Paneli. {len(self._stats_items)} madde. "
            f"Yukarı-Aşağı oklarla gezinin. Tab veya Escape ile kapatın.",
            interrupt=True
        )
        self.audio.speak(self._stats_items[0], interrupt=False)
    
    def _close_stats_mode(self):
        """İstatistik gezinme modundan çık"""
        self._stats_mode = False
        self._stats_items = []
        self._stats_index = 0
        self.audio.speak("İstatistik paneli kapatıldı.", interrupt=True)
    
    def _build_stats_items(self):
        """Tüm önemli istatistikleri liste olarak döndür"""
        gm = self.screen_manager.game_manager
        if not gm:
            return []
        
        items = []
        
        # --- Genel Bilgi ---
        items.append(f"Yıl: {gm.current_year}, {gm.current_month}. ay")
        items.append(f"Tur: {gm.turn_count}")
        items.append(f"Eyalet: {gm.province.name}")
        
        # --- Karakter ---
        if gm.player:
            items.append(f"Karakter: {gm.player.get_full_title()}")
        
        # --- Kaynaklar ---
        items.append(f"Altın: {gm.economy.resources.gold:,}")
        items.append(f"Zahire: {gm.economy.resources.food:,}")
        items.append(f"Kereste: {gm.economy.resources.wood:,}")
        items.append(f"Demir: {gm.economy.resources.iron:,}")
        items.append(f"Bakır: {gm.economy.resources.copper:,}")
        items.append(f"Barut: {gm.economy.resources.gunpowder:,}")
        
        # --- Gelir/Gider ---
        try:
            report = gm.economy.get_income_report()
            items.append(f"Gelir: {report.get('total_income', 0):,} altın")
            items.append(f"Gider: {report.get('total_expense', 0):,} altın")
            net = report.get('total_income', 0) - report.get('total_expense', 0)
            items.append(f"Net: {'+' if net >= 0 else ''}{net:,} altın")
        except Exception:
            pass
        
        # --- Sadakat ve Memnuniyet ---
        items.append(f"Padişah Sadakati: yüzde {gm.diplomacy.sultan_loyalty}")
        items.append(f"Halk Memnuniyeti: yüzde {gm.population.happiness}")
        
        # --- Nüfus ---
        items.append(f"Nüfus: {gm.population.population.total:,}")
        
        # --- Askeri Güç ---
        items.append(f"Askeri Güç: {gm.military.get_total_power():,}")
        try:
            items.append(f"Yeniçeri: {gm.military.janissary_count:,}")
            items.append(f"Sipahi: {gm.military.sipahi_count:,}")
            items.append(f"Azap: {gm.military.azap_count:,}")
        except Exception:
            pass
        
        # --- Donanma ---
        try:
            if gm.province.is_coastal and hasattr(gm, 'naval'):
                items.append(f"Donanma Gücü: {gm.naval.get_total_power():,}")
        except Exception:
            pass
        
        # --- Topçu ---
        try:
            if hasattr(gm, 'artillery'):
                items.append(f"Top Sayısı: {gm.artillery.get_total_cannons()}")
        except Exception:
            pass
        
        # --- Vergi ---
        tax_labels = {
            "salyanesiz": "Salyanesiz (Tımar)",
            "salyaneli": "Salyaneli (Nakit)",
            "karma": "Karma",
        }
        tax_type = getattr(gm.province, 'tax_type', 'salyanesiz')
        items.append(f"Vergi Tipi: {tax_labels.get(tax_type, tax_type)}")
        
        # --- İşçiler ---
        try:
            items.append(f"Toplam İşçi: {len(gm.workers.workers)}")
            idle = gm.workers.get_idle_count()
            if idle > 0:
                items.append(f"Boşta İşçi: {idle}")
        except Exception:
            pass
        
        # --- İsyan ---
        if gm.population.active_revolt:
            items.append("⚠ UYARI: İSYAN VAR!")
        
        return items
    
    def _announce_income(self):
        """Gelir/gider özetini oku"""
        gm = self.screen_manager.game_manager
        if not gm:
            return
        
        income = gm.economy.income.total
        expense = gm.economy.expense.total
        net = income - expense
        
        self.audio.speak("Ekonomi Özeti:", interrupt=True)
        self.audio.speak(f"Gelir: {income:,} altın", interrupt=False)
        self.audio.speak(f"Gider: {expense:,} altın", interrupt=False)
        if net >= 0:
            self.audio.speak(f"Net kazanç: {net:,} altın her tur", interrupt=False)
        else:
            self.audio.speak(f"Net kayıp: {abs(net):,} altın her tur", interrupt=False)
    
    def _announce_warnings(self):
        """Uyarıları oku"""
        gm = self.screen_manager.game_manager
        if not gm:
            return
        
        warnings = []
        
        # İsyan kontrolü
        if gm.population.active_revolt:
            warnings.append("Dikkat! Halk isyan halinde!")
        
        # Düşük kaynak
        if gm.economy.resources.gold < 100:
            warnings.append("Uyarı! Altın çok düşük!")
        if gm.economy.resources.food < 50:
            warnings.append("Uyarı! Zahire çok düşük!")
        
        # Düşük memnuniyet
        if gm.population.happiness < 30:
            warnings.append("Uyarı! Halk memnuniyeti kritik seviyede!")
        
        # Düşük sadakat
        if gm.diplomacy.sultan_loyalty < 30:
            warnings.append("Tehlike! Padişah sadakati çok düşük! İdam riski var!")
        
        # Olay var mı
        if gm.events.current_event:
            warnings.append(f"Bekleyen olay: {gm.events.current_event.title}. O tuşuna basın.")
        
        if warnings:
            self.audio.speak("Uyarılar:", interrupt=True)
            for w in warnings:
                self.audio.speak(w)
        else:
            self.audio.speak("Aktif uyarı yok.", interrupt=True)
    
    def update(self, dt: float):
        self._update_panels()
    
    def draw(self, surface: pygame.Surface):
        gm = self.screen_manager.game_manager
        if not gm:
            return
        
        # Kaynak paneli (yatay düzen)
        self._draw_resource_bar(surface, gm)
        
        # Durum paneli
        self.status_panel.draw(surface)
        
        # Yan menü
        self.side_menu.draw(surface)
        
        # Butonlar
        self.next_turn_button.draw(surface)
        self.save_button.draw(surface)
        self.menu_button.draw(surface)
        
        # Özet paneli
        self._draw_summary(surface, gm)
        
        # Olay varsa bildirim
        if gm.events.current_event:
            self._draw_event_notification(surface)
    
    def _draw_resource_bar(self, surface: pygame.Surface, gm):
        """Kaynak çubuğunu çiz"""
        # Panel arka planı
        pygame.draw.rect(surface, COLORS['panel_bg'], 
                        (20, 20, SCREEN_WIDTH - 40, 100), border_radius=10)
        pygame.draw.rect(surface, COLORS['panel_border'], 
                        (20, 20, SCREEN_WIDTH - 40, 100), width=2, border_radius=10)
        
        # Kaynaklar
        resources = [
            ("Altin", gm.economy.resources.gold, COLORS['gold']),
            ("Zahire", gm.economy.resources.food, COLORS['success']),
            ("Kereste", gm.economy.resources.wood, (139, 90, 43)),
            ("Demir", gm.economy.resources.iron, (150, 150, 160)),
            ("Tas", gm.economy.resources.stone, (180, 170, 150)),
            ("Bakir", gm.economy.resources.copper, (184, 115, 51)),
            ("Barut", gm.economy.resources.gunpowder, (80, 80, 80)),
        ]
        
        font = self.get_info_font()
        x_start = 50
        spacing = (SCREEN_WIDTH - 100) // len(resources)
        
        for i, (name, value, color) in enumerate(resources):
            x = x_start + i * spacing
            
            # İsim
            name_surface = font.render(name, True, COLORS['text'])
            surface.blit(name_surface, (x, 40))
            
            # Değer
            value_font = get_font(FONTS['subheader'])
            value_surface = value_font.render(f"{value:,}", True, color)
            surface.blit(value_surface, (x, 70))
    
    def _draw_summary(self, surface: pygame.Surface, gm):
        """Özet bölümünü çiz"""
        rect = pygame.Rect(390, 400, SCREEN_WIDTH - 410, 190)
        pygame.draw.rect(surface, COLORS['panel_bg'], rect, border_radius=10)
        pygame.draw.rect(surface, COLORS['panel_border'], rect, width=2, border_radius=10)
        
        font = self.get_info_font()
        
        # Başlık
        title_font = get_font(FONTS['subheader'])
        title = title_font.render(f"📍 {gm.province.name}", True, COLORS['gold'])
        surface.blit(title, (410, 420))
        
        # Gelir/Gider özeti
        net = gm.economy.income.total - gm.economy.expense.total
        net_color = COLORS['success'] if net >= 0 else COLORS['danger']
        net_text = f"+{net}" if net >= 0 else str(net)
        
        income_text = font.render(f"Gelir: {gm.economy.income.total}", True, COLORS['success'])
        expense_text = font.render(f"Gider: {gm.economy.expense.total}", True, COLORS['danger'])
        net_text_surface = font.render(f"Net: {net_text}/tur", True, net_color)
        
        surface.blit(income_text, (410, 460))
        surface.blit(expense_text, (410, 490))
        surface.blit(net_text_surface, (410, 520))
        
        # Sağ taraf - hızlı istatistikler
        stats = [
            f"Asker: {gm.military.get_total_soldiers():,}",
            f"Bina: {len(gm.construction.buildings)}",
            f"Görev: {len(gm.diplomacy.active_missions)}"
        ]
        
        for i, stat in enumerate(stats):
            stat_surface = font.render(stat, True, COLORS['text'])
            surface.blit(stat_surface, (rect.right - 150, 460 + i * 30))
    
    def _draw_event_notification(self, surface: pygame.Surface):
        """Olay bildirimi çiz"""
        gm = self.screen_manager.game_manager
        event = gm.events.current_event
        
        # Bildirim kutusu
        rect = pygame.Rect(SCREEN_WIDTH - 320, 260, 300, 120)
        pygame.draw.rect(surface, COLORS['warning'], rect, border_radius=8)
        pygame.draw.rect(surface, COLORS['gold'], rect, width=3, border_radius=8)
        
        font = get_font(FONTS['body'])
        
        # Başlık
        title = font.render("⚠ OLAY!", True, COLORS['text_dark'])
        surface.blit(title, (rect.x + 20, rect.y + 15))
        
        # Olay adı
        event_name = font.render(event.title, True, COLORS['text_dark'])
        surface.blit(event_name, (rect.x + 20, rect.y + 45))
        
        # Talimat
        small_font = get_font(FONTS['small'])
        instruction = small_font.render("O tuşuna basarak olayı görüntüle", True, COLORS['text_dark'])
        surface.blit(instruction, (rect.x + 20, rect.y + 85))
    
    def _open_screen(self, screen_type: ScreenType):
        """Alt ekran aç"""
        self.screen_manager.change_screen(screen_type)
    
    def _on_next_turn(self):
        """Tur bitir"""
        gm = self.screen_manager.game_manager
        if gm:
            # Önceki durumu kaydet
            prev_gold = gm.economy.resources.gold
            prev_food = gm.economy.resources.food
            prev_wood = gm.economy.resources.wood
            prev_iron = gm.economy.resources.iron
            prev_copper = gm.economy.resources.copper
            prev_gunpowder = gm.economy.resources.gunpowder
            
            result = gm.process_turn()
            
            # Tur duyurusu
            self.audio.speak(f"Tur {gm.turn_count} tamamlandı.", interrupt=True)
            
            # Kaynak değişimi
            gold_change = gm.economy.resources.gold - prev_gold
            food_change = gm.economy.resources.food - prev_food
            wood_change = gm.economy.resources.wood - prev_wood
            iron_change = gm.economy.resources.iron - prev_iron
            copper_change = gm.economy.resources.copper - prev_copper
            gunpowder_change = gm.economy.resources.gunpowder - prev_gunpowder
            
            self.audio.speak(f"Altın: {gm.economy.resources.gold:,} ({'+' if gold_change >= 0 else ''}{gold_change})", interrupt=False)
            self.audio.speak(f"Zahire: {gm.economy.resources.food:,} ({'+' if food_change >= 0 else ''}{food_change})", interrupt=False)
            self.audio.speak(f"Kereste: {gm.economy.resources.wood:,} ({'+' if wood_change >= 0 else ''}{wood_change})", interrupt=False)
            self.audio.speak(f"Demir: {gm.economy.resources.iron:,} ({'+' if iron_change >= 0 else ''}{iron_change})", interrupt=False)
            # Bakır ve barut sadece değişim varsa duyur (her tur değişmeyebilir)
            if copper_change != 0:
                self.audio.speak(f"Bakır: {gm.economy.resources.copper:,} ({'+' if copper_change >= 0 else ''}{copper_change})", interrupt=False)
            if gunpowder_change != 0:
                self.audio.speak(f"Barut: {gm.economy.resources.gunpowder:,} ({'+' if gunpowder_change >= 0 else ''}{gunpowder_change})", interrupt=False)
            
            # Alt sistem mesajlarını duyur (İnşaat, Casusluk vb.)
            if 'messages' in result and result['messages']:
                for msg in result['messages']:
                    self.audio.speak(msg, interrupt=False)
            
            # Olay varsa duyur
            if result.get('event', False):
                if gm.events.current_event:
                    self.audio.speak(f"Yeni olay: {gm.events.current_event.title}. O tuşuna basın.", interrupt=False)
            
            # Kritik uyarılar
            if gm.economy.resources.gold < 0:
                self.audio.speak("Dikkat! Hazine ekside!")
            if gm.population.active_revolt:
                self.audio.speak("Dikkat! İsyan devam ediyor!")
            if gm.diplomacy.sultan_loyalty < 30:
                self.audio.speak("Tehlike! Padişah sadakati çok düşük!")
            
            # Bekleyen akın raporu kontrolü
            pending_raid = gm.get_pending_raid_report()
            if pending_raid:
                # Raporu al ve ekranı aç
                raid_data = gm.consume_pending_raid_report()
                
                # RaidReportScreen'e veriyi gönder
                raid_screen = self.screen_manager.screens.get(ScreenType.RAID_REPORT)
                if raid_screen:
                    from ui.screens.raid_report_screen import RaidStory
                    story = RaidStory(
                        target_name=raid_data['target_name'],
                        raid_size=raid_data['raid_size'],
                        villages_raided=raid_data['villages_raided'],
                        encounter_type=raid_data['encounter_type'],
                        loot_gold=raid_data['loot_gold'],
                        loot_food=raid_data['loot_food'],
                        prisoners_taken=raid_data['prisoners_taken'],
                        enemy_killed=raid_data['enemy_killed'],
                        our_casualties=raid_data['our_casualties'],
                        victory=raid_data['victory'],
                        enemy_commander=raid_data['enemy_commander'],
                        special_event=raid_data.get('special_event'),
                        is_naval=raid_data.get('is_naval', False)
                    )
                    raid_screen.set_raid_story(story)
                    self.screen_manager.change_screen(ScreenType.RAID_REPORT)
                    return  # Oyun sonu kontrolüne geçme
            
            # Bekleyen kuşatma savaşı kontrolü
            pending_siege = gm.get_pending_siege_battle()
            if pending_siege:
                # Savaş verisini al ve BattleScreen'i aç
                siege_data = gm.consume_pending_siege_battle()
                
                battle_screen = self.screen_manager.screens.get(ScreenType.BATTLE)
                if battle_screen:
                    battle_screen.set_battle_data(siege_data)
                    self.screen_manager.change_screen(ScreenType.BATTLE)
                    return  # Oyun sonu kontrolüne geçme
                    
            # Düşman İstilası Kontrolü (Savunma Savaşı)
            if hasattr(gm, 'current_invasion') and gm.current_invasion:
                invader = gm.current_invasion['invader']
                self.audio.announce(f"DİKKAT! Sınırlar aşıldı! Eyaletimiz {invader} tarafından kuşatılıyor! Savunma hattına geçin!")
                self._open_screen(ScreenType.BATTLE)
                return
            
            if gm.game_over:
                self.screen_manager.change_screen(ScreenType.GAME_OVER)
    
    def _on_save(self):
        """Oyunu kaydet - yuva seçim ekranını aç"""
        # SaveLoadScreen'i save modunda aç
        save_screen = self.screen_manager.screens.get(ScreenType.SAVE_LOAD)
        if save_screen:
            save_screen.set_mode('save')
        self.screen_manager.change_screen(ScreenType.SAVE_LOAD)
    
    def _on_main_menu(self):
        """Ana menüye veya multiplayer ekranına dön"""
        if getattr(self.screen_manager, 'is_multiplayer_mode', False):
            self.screen_manager.change_screen(ScreenType.MULTIPLAYER_GAME)
        else:
            self.screen_manager.change_screen(ScreenType.MAIN_MENU)
