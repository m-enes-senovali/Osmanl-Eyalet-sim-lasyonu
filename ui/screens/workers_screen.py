# -*- coding: utf-8 -*-
"""
Osmanlı Eyalet Yönetim Simülasyonu - İşçi Yönetim Ekranı
"""

import pygame
from ui.screen_manager import BaseScreen, ScreenType
from ui.components import Button, Panel, MenuList
from game.systems.workers import WorkerType, TaskType
from config import COLORS, FONTS, SCREEN_WIDTH, SCREEN_HEIGHT


class WorkersScreen(BaseScreen):
    """İşçi yönetim ekranı"""
    
    def __init__(self, screen_manager):
        super().__init__(screen_manager)
        
        # Paneller
        self.workers_panel = Panel(20, 80, 450, 350, "İşçiler")
        self.production_panel = Panel(490, 80, 380, 150, "Üretim Özeti")
        
        # İşçi listesi menüsü
        self.worker_menu = MenuList(
            x=20,
            y=200,
            width=450,
            item_height=40
        )
        
        # Görev atama menüsü (işçi seçilince görünür)
        self.task_menu = MenuList(
            x=490,
            y=260,
            width=380,
            item_height=40
        )
        
        # İşe alma menüsü
        self.hire_menu = MenuList(
            x=490,
            y=450,
            width=380,
            item_height=35
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
        self.menu_mode = "workers"  # "workers" veya "tasks"
    
    def get_header_font(self):
        if self._header_font is None:
            self._header_font = pygame.font.Font(None, FONTS['header'])
        return self._header_font
    
    def on_enter(self):
        self._update_panels()
        self._setup_worker_menu()
        self._setup_hire_menu()
    
    def announce_screen(self):
        self.audio.announce_screen_change("İşçi Yönetimi")
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
    
    def _setup_hire_menu(self):
        """İşe alma menüsünü oluştur"""
        self.hire_menu.clear()
        
        type_costs = {
            WorkerType.FARMER: ("Çiftçi", 100),
            WorkerType.LUMBERJACK: ("Oduncu", 120),
            WorkerType.MINER: ("Madenci", 150),
            WorkerType.CRAFTSMAN: ("Usta", 300),
            WorkerType.MERCHANT: ("Tüccar", 250),
            WorkerType.ENVOY: ("Elçi", 400),
        }
        
        for wtype, (name, cost) in type_costs.items():
            self.hire_menu.add_item(
                f"İşe Al: {name} ({cost} altın)",
                lambda wt=wtype: self._hire_worker(wt)
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
        self.task_menu.add_item("← Geri", self._close_task_menu)
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
        self.task_menu.add_item("🗑️ İşten Çıkar", self._fire_worker)
        
        self.audio.speak(f"{worker.name} seçildi. Görev atayın.", interrupt=True)
    
    def _close_task_menu(self):
        """Görev menüsünü kapat"""
        self.menu_mode = "workers"
        self.selected_worker = None
        self.audio.speak("İşçi listesine dönüldü.", interrupt=True)
    
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
        self.workers_panel.add_item("Toplam", f"{len(workers.workers)} / {workers.max_workers}")
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
        # Görev menüsü aktifse
        if self.menu_mode == "tasks":
            if self.task_menu.handle_event(event):
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
            # Backspace veya Escape - Geri dön
            if event.key in (pygame.K_BACKSPACE, pygame.K_ESCAPE):
                if self.menu_mode == "tasks":
                    self._close_task_menu()
                else:
                    self._go_back()
                return True
            
            # F1 - Özet
            if event.key == pygame.K_F1:
                gm = self.screen_manager.game_manager
                if gm:
                    gm.workers.announce_workers()
                return True
            
            # Tab - Menüler arası geçiş
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
    
    def _hire_worker(self, worker_type: WorkerType):
        """İşçi işe al"""
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
        # Başlık
        header_font = self.get_header_font()
        title = header_font.render("👷 İŞÇİ YÖNETİMİ", True, COLORS['gold'])
        surface.blit(title, (20, 20))
        
        # Paneller
        self.production_panel.draw(surface)
        
        small_font = pygame.font.Font(None, FONTS['subheader'])
        
        if self.menu_mode == "tasks":
            # Görev atama menüsü
            task_title = small_font.render("Görev Seç", True, COLORS['gold'])
            surface.blit(task_title, (490, 235))
            self.task_menu.draw(surface)
        else:
            # İşçi listesi menüsü
            worker_title = small_font.render("İşçiler (Seçmek için tıklayın)", True, COLORS['gold'])
            surface.blit(worker_title, (20, 175))
            self.worker_menu.draw(surface)
            
            # İşe alma menüsü
            hire_title = small_font.render("Yeni İşçi Al", True, COLORS['gold'])
            surface.blit(hire_title, (490, 425))
            self.hire_menu.draw(surface)
        
        # Geri butonu
        self.back_button.draw(surface)
    
    def _go_back(self):
        self.screen_manager.change_screen(ScreenType.PROVINCE_VIEW)
