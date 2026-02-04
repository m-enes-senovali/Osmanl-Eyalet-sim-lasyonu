# -*- coding: utf-8 -*-
"""
OsmanlÄ± Eyalet YÃ¶netim SimÃ¼lasyonu - Ä°ÅŸÃ§i YÃ¶netim EkranÄ±
"""

import pygame
from ui.screen_manager import BaseScreen, ScreenType
from ui.components import Button, Panel, MenuList
from ui.text_input import AccessibleTextInput
from game.systems.workers import WorkerType, TaskType
from config import COLORS, FONTS, SCREEN_WIDTH, SCREEN_HEIGHT


class WorkersScreen(BaseScreen):
    """Ä°ÅŸÃ§i yÃ¶netim ekranÄ±"""
    
    def __init__(self, screen_manager):
        super().__init__(screen_manager)
        
        # Paneller
        self.workers_panel = Panel(20, 80, 450, 350, "Ä°ÅŸÃ§iler")
        self.production_panel = Panel(490, 80, 380, 150, "Ãœretim Ã–zeti")
        
        # Ä°ÅŸÃ§i listesi menÃ¼sÃ¼
        self.worker_menu = MenuList(
            x=20,
            y=200,
            width=450,
            item_height=40
        )
        
        # GÃ¶rev atama menÃ¼sÃ¼ (iÅŸÃ§i seÃ§ilince gÃ¶rÃ¼nÃ¼r)
        self.task_menu = MenuList(
            x=490,
            y=260,
            width=380,
            item_height=40
        )
        
        # İşe alma menüsü
        self.hire_menu = MenuList(
            x=490,
            y=250,
            width=380,
            item_height=50
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
        self.selected_worker = None
        self.menu_mode = "workers"  # "workers", "tasks", veya "rename"
        
        # İsim değiştirme için AccessibleTextInput
        self.rename_input = AccessibleTextInput(
            x=490,
            y=260,
            width=380,
            height=40,
            label="Yeni İsim",
            placeholder="İşçi adını yazın",
            max_length=30
        )
        self.rename_input_mode = False
    
    def get_header_font(self):
        if self._header_font is None:
            self._header_font = pygame.font.Font(None, FONTS['header'])
        return self._header_font
    
    def on_enter(self):
        self._update_panels()
        self._setup_worker_menu()
        self._setup_hire_menu()
    
    def announce_screen(self):
        self.audio.announce_screen_change("Ä°ÅŸÃ§i YÃ¶netimi")
        gm = self.screen_manager.game_manager
        if gm:
            gm.workers.announce_workers()
    
    def _setup_worker_menu(self):
        """İşçi listesi menüsünü oluştur"""
        self.worker_menu.clear()
        gm = self.screen_manager.game_manager
        if not gm:
            return
        
        type_names = {
            WorkerType.FARMER: "Çiftçi",
            WorkerType.MINER: "Madenci",
            WorkerType.LUMBERJACK: "Oduncu",
            WorkerType.CRAFTSMAN: "Usta",
            WorkerType.MERCHANT: "Tüccar",
            WorkerType.ENVOY: "Elçi"
        }
        
        task_names = {
            TaskType.FARMING: "Tarım",
            TaskType.MINING: "Madencilik",
            TaskType.LOGGING: "Kereste",
            TaskType.CONSTRUCTION: "İnşaat",
            TaskType.TRADING: "Ticaret",
            TaskType.DIPLOMACY: "Diplomasi",
            TaskType.IDLE: "Boşta"
        }
        
        for i, worker in enumerate(gm.workers.workers):
            type_name = type_names.get(worker.worker_type, "İşçi")
            task_name = task_names.get(worker.current_task, "?")
            self.worker_menu.add_item(
                f"{worker.name} - {type_name} ({task_name})",
                lambda idx=i: self._open_task_menu(idx)
            )
        
        # Ayırıcı ve işe alım butonu
        self.worker_menu.add_item("", None)  # Boş satır
        self.worker_menu.add_item(
            "YENİ İŞÇİ İSTİHDAM ET",
            self._open_interview_screen
        )
    
    def _setup_hire_menu(self):
        """İşe alma menüsünü oluştur"""
        self.hire_menu.clear()
        
        # İnteraktif görüşme sistemi
        self.hire_menu.add_item(
            "YENİ İŞÇİ İSTİHDAM ET",
            self._open_interview_screen
        )
    
    def _open_task_menu(self, worker_index: int):
        """Seçili işçi için görev menüsünü aç"""
        gm = self.screen_manager.game_manager
        if not gm or worker_index >= len(gm.workers.workers):
            return
        
        self.selected_worker = worker_index
        self.menu_mode = "tasks"
        worker = gm.workers.workers[worker_index]
        
        self.task_menu.clear()
        self.task_menu.add_item("<- Geri", self._close_task_menu)
        self.task_menu.add_item("", None)  # Boşluk
        
        # Görev seçenekleri
        tasks = [
            (TaskType.FARMING, "Tarım Yap"),
            (TaskType.MINING, "Madencilik Yap"),
            (TaskType.LOGGING, "Kereste Kes"),
            (TaskType.CONSTRUCTION, "İnşaatta Çalış"),
            (TaskType.TRADING, "Ticaret Yap"),
            (TaskType.DIPLOMACY, "Diplomasi Yap"),
        ]
        
        for task, name in tasks:
            self.task_menu.add_item(
                name,
                lambda t=task: self._assign_task(t)
            )
        
        self.task_menu.add_item("", None)  # Boşluk
        self.task_menu.add_item("İsim Değiştir (R)", lambda: self._start_rename())
        self.task_menu.add_item("İşten Çıkar", self._fire_worker)
        
        self.audio.speak(f"{worker.name} seçildi. Görev atayın veya R ile ismini değiştirin.", interrupt=True)
    
    def _close_task_menu(self):
        """Görev menüsünü kapat"""
        self.menu_mode = "workers"
        self.selected_worker = None
        self.audio.speak("İşçi listesine dönüldü.", interrupt=True)
    
    def _start_rename(self):
        """İsim değiştirme modunu başlat"""
        gm = self.screen_manager.game_manager
        if not gm or self.selected_worker is None:
            return
        
        worker = gm.workers.workers[self.selected_worker]
        self.rename_input_mode = True
        self.rename_input.text = worker.name  # Mevcut ismi yükle
        self.rename_input.cursor_pos = len(worker.name)
        self.rename_input.focus()
    
    def _finish_rename(self):
        """İsim değiştirmeyi tamamla"""
        gm = self.screen_manager.game_manager
        if not gm or self.selected_worker is None:
            self.rename_input_mode = False
            self.rename_input.unfocus()
            return
        
        new_name = self.rename_input.text.strip()
        if not new_name:
            self.audio.speak("İsim boş olamaz.", interrupt=True)
            return
        
        old_name = gm.workers.workers[self.selected_worker].name
        gm.workers.workers[self.selected_worker].name = new_name
        
        self.rename_input_mode = False
        self.rename_input.unfocus()
        self.rename_input.text = ""
        
        self.audio.speak(f"{old_name} artık {new_name} olarak adlandırılıyor.", interrupt=True)
        self._update_panels()
        self._setup_worker_menu()
        self._close_task_menu()
    
    def _assign_task(self, task: TaskType):
        """Seçili işçiye görev ata"""
        gm = self.screen_manager.game_manager
        if not gm or self.selected_worker is None:
            return
        
        task_names = {
            TaskType.FARMING: "Tarım",
            TaskType.MINING: "Madencilik",
            TaskType.LOGGING: "Kereste",
            TaskType.CONSTRUCTION: "İnşaat",
            TaskType.TRADING: "Ticaret",
            TaskType.DIPLOMACY: "Diplomasi",
        }
        
        success = gm.workers.assign_task(self.selected_worker, task)
        worker = gm.workers.workers[self.selected_worker]
        
        if success:
            self.audio.speak(f"{worker.name} artık {task_names.get(task, 'yeni görevde')}.", interrupt=True)
            self._update_panels()
            self._setup_worker_menu()
            self._close_task_menu()
        else:
            self.audio.speak("Bu görev bu işçi için uygun değil.", interrupt=True)
    
    def _fire_worker(self):
        """Seçili işçiyi işten çıkar"""
        gm = self.screen_manager.game_manager
        if not gm or self.selected_worker is None:
            return
        
        worker = gm.workers.workers[self.selected_worker]
        name = worker.name
        gm.workers.fire_worker(self.selected_worker)
        self.audio.speak(f"{name} işten çıkarıldı.", interrupt=True)
        self._update_panels()
        self._setup_worker_menu()
        self._close_task_menu()
    
    def _update_panels(self):
        """Panelleri güncelle"""
        gm = self.screen_manager.game_manager
        if not gm:
            return
        
        workers = gm.workers
        
        # İşçiler paneli
        self.workers_panel.clear()
        self.workers_panel.add_item("Toplam İşçi", str(len(workers.workers)))
        self.workers_panel.add_item("", "")
        
        type_names = {
            WorkerType.FARMER: "Çiftçi",
            WorkerType.MINER: "Madenci",
            WorkerType.LUMBERJACK: "Oduncu",
            WorkerType.CRAFTSMAN: "Usta",
            WorkerType.MERCHANT: "Tüccar",
            WorkerType.ENVOY: "Elçi"
        }
        
        task_names = {
            TaskType.FARMING: "Tarım",
            TaskType.MINING: "Madencilik",
            TaskType.LOGGING: "Kereste",
            TaskType.CONSTRUCTION: "İnşaat",
            TaskType.TRADING: "Ticaret",
            TaskType.DIPLOMACY: "Diplomasi",
            TaskType.IDLE: "Boşta"
        }
        
        for i, worker in enumerate(workers.workers):
            type_name = type_names.get(worker.worker_type, "İşçi")
            task_name = task_names.get(worker.current_task, "?")
            self.workers_panel.add_item(
                f"{i+1}. {worker.name}",
                f"{type_name} Lv{worker.skill_level}, {task_name}"
            )
        
        # Üretim paneli
        self.production_panel.clear()
        result = workers.process_turn()
        prod = result['production']
        self.production_panel.add_item("Yiyecek/tur", f"+{prod['food']}")
        self.production_panel.add_item("Kereste/tur", f"+{prod['wood']}")
        self.production_panel.add_item("Demir/tur", f"+{prod['iron']}")
    
    def handle_event(self, event) -> bool:
        # İsim değiştirme modu - AccessibleTextInput kullan
        if self.rename_input_mode:
            if self.rename_input.handle_event(event):
                # Enter pressed - confirm rename
                if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                    self._finish_rename()
                return True
            # Escape pressed - cancel rename
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.rename_input_mode = False
                self.rename_input.unfocus()
                self.rename_input.text = ""
                self.audio.speak("İsim değiştirme iptal edildi.", interrupt=True)
                return True
            return True
        
        # Görev menüsü aktifse
        if self.menu_mode == "tasks":
            if self.task_menu.handle_event(event):
                return True
            
            # R - İsim değiştir
            if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                self._start_rename()
                return True
            
            # ESC - Görev menüsünden çık
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self._close_task_menu()
                return True
        else:
            # İşçi menüsü
            if self.worker_menu.handle_event(event):
                return True
            
            # İşe alma menüsü
            if self.hire_menu.handle_event(event):
                return True
        
        if self.back_button.handle_event(event):
            return True
        
        if event.type == pygame.KEYDOWN:
            # Backspace veya Escape - Geri dÃ¶n
            if event.key in (pygame.K_BACKSPACE, pygame.K_ESCAPE):
                if self.menu_mode == "tasks":
                    self._close_task_menu()
                else:
                    self._go_back()
                return True
            
            # F1 - Ã–zet
            if event.key == pygame.K_F1:
                gm = self.screen_manager.game_manager
                if gm:
                    gm.workers.announce_workers()
                return True
            
            # Tab - MenÃ¼ler arasÄ± geÃ§iÅŸ
            if event.key == pygame.K_TAB:
                self._announce_next_panel()
                return True
        
        return False
    
    def _assign_task_to_selected(self, task: TaskType):
        """Seçili işçiye görev ata"""
        gm = self.screen_manager.game_manager
        if not gm or self.selected_worker is None:
            self.audio.speak("Önce bir işçi seçin. 1-9 tuşlarını kullanın.", interrupt=True)
            return
        
        task_names = {
            TaskType.FARMING: "Tarım",
            TaskType.MINING: "Madencilik",
            TaskType.LOGGING: "Kereste",
            TaskType.CONSTRUCTION: "İnşaat",
            TaskType.TRADING: "Ticaret",
            TaskType.DIPLOMACY: "Diplomasi",
        }
        
        success = gm.workers.assign_task(self.selected_worker, task)
        if success:
            worker = gm.workers.workers[self.selected_worker]
            self.audio.speak(f"{worker.name} artık {task_names.get(task, 'yeni görevde')} yapıyor.", interrupt=True)
            self._update_panels()
        else:
            self.audio.speak("Bu görev bu işçi için uygun değil.", interrupt=True)
    
    def _fire_selected_worker(self):
        """Seçili işçiyi işten çıkar"""
        gm = self.screen_manager.game_manager
        if not gm or self.selected_worker is None:
            return
        
        worker = gm.workers.workers[self.selected_worker]
        name = worker.name
        gm.workers.fire_worker(self.selected_worker)
        self.audio.speak(f"{name} işten çıkarıldı.", interrupt=True)
        self.selected_worker = None
        self._update_panels()
        self._setup_action_menu()
    
    def _select_worker(self, index: int):
        """İşçi seç ve bilgisini oku"""
        gm = self.screen_manager.game_manager
        if not gm or index >= len(gm.workers.workers):
            self.audio.speak("Bu numarada işçi yok.", interrupt=True)
            return
        
        worker = gm.workers.workers[index]
        self.selected_worker = index
        
        type_names = {
            WorkerType.FARMER: "Çiftçi",
            WorkerType.MINER: "Madenci",
            WorkerType.LUMBERJACK: "Oduncu",
            WorkerType.CRAFTSMAN: "Usta",
            WorkerType.MERCHANT: "Tüccar",
            WorkerType.ENVOY: "Elçi"
        }
        
        self.audio.speak(f"{worker.name}, {type_names.get(worker.worker_type, 'İşçi')}", interrupt=True)
        self.audio.speak(f"Beceri Seviyesi: {worker.skill_level}", interrupt=False)
        self.audio.speak(f"Verimlilik: yüzde {int(worker.efficiency * 100)}", interrupt=False)
        self.audio.speak(f"Görevde: {worker.turns_on_task} tur", interrupt=False)
    
    def _open_interview_screen(self):
        """Görüşme ekranını aç"""
        self.screen_manager.change_screen(ScreenType.WORKER_INTERVIEW)
    
    def _hire_worker(self, worker_type: WorkerType):
        """İşçi işe al (eski yöntem - artık kullanılmıyor)"""
        gm = self.screen_manager.game_manager
        if not gm:
            return
        
        cost = gm.workers.get_hire_cost(worker_type)
        
        if gm.economy.resources.gold < cost:
            self.audio.speak(f"Yeterli altın yok. {cost} altın gerekli.", interrupt=True)
            return
        
        gm.economy.resources.gold -= cost
        worker = gm.workers.hire_worker(worker_type)
        
        if worker:
            self.audio.play_ui_sound('click')
            self.audio.speak(f"{worker.name} işe alındı.", interrupt=True)
            self._update_panels()
            self._setup_worker_menu()
    
    def _announce_next_panel(self):
        """Sıradaki paneli duyur"""
        if not hasattr(self, '_current_panel'):
            self._current_panel = 0
        
        panels = [self.workers_panel, self.production_panel]
        self._current_panel = (self._current_panel + 1) % len(panels)
        panels[self._current_panel].announce_content()
    
    def update(self, dt: float):
        self._update_panels()
    
    def draw(self, surface: pygame.Surface):
        # BaÅŸlÄ±k
        header_font = self.get_header_font()
        title = header_font.render("İŞÇİ YÖNETİMİ", True, COLORS['gold'])
        surface.blit(title, (20, 20))
        
        # Paneller
        self.production_panel.draw(surface)
        
        small_font = pygame.font.Font(None, FONTS['subheader'])
        
        if self.menu_mode == "tasks":
            # GÃ¶rev atama menÃ¼sÃ¼
            task_title = small_font.render("Görev Seç", True, COLORS['gold'])
            surface.blit(task_title, (490, 235))
            self.task_menu.draw(surface)
        else:
            # Ä°ÅŸÃ§i listesi menÃ¼sÃ¼
            worker_title = small_font.render("İşçiler (Seçmek için tıklayın)", True, COLORS['gold'])
            surface.blit(worker_title, (20, 175))
            self.worker_menu.draw(surface)
            
            # İşe alma menüsü
            hire_title = small_font.render("İŞE ALIM", True, COLORS['gold'])
            surface.blit(hire_title, (490, 225))
            self.hire_menu.draw(surface)
        
        # Geri butonu
        self.back_button.draw(surface)
    
    def _go_back(self):
        self.screen_manager.change_screen(ScreenType.PROVINCE_VIEW)

