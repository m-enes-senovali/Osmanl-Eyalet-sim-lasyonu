# -*- coding: utf-8 -*-
"""
Osmanlı Eyalet Yönetim Simülasyonu - Büyük Osmanlı Haritası
Grid tabanlı navigasyon ile tüm eyaletler
"""

import pygame
from ui.screen_manager import BaseScreen, ScreenType
from ui.components import Button, Panel
from config import COLORS, FONTS, SCREEN_WIDTH, SCREEN_HEIGHT


# Osmanlı İmparatorluğu haritası (1520 dönemi - Kanuni başlangıcı)
# NOT: Rodos 1522'de, Kıbrıs 1571'de, Girit 1669'da, Bağdat 1534'te fethedildi
# Grid: 7 sütun x 5 satır
OTTOMAN_MAP = {
    # Satır 0 (Kuzey) - Balkanlar ve Karadeniz
    (0, 0): {"name": "Bosna Eyaleti", "type": "eyalet", "is_coastal": True, "connections": [(1, 0), (0, 1)]},
    (1, 0): {"name": "Belgrad Sancağı", "type": "sancak", "is_coastal": False, "connections": [(0, 0), (2, 0), (1, 1)]},
    (2, 0): {"name": "Rumeli Eyaleti", "type": "eyalet", "is_coastal": True, "connections": [(1, 0), (3, 0), (2, 1)]},
    (3, 0): {"name": "Silistre Eyaleti", "type": "eyalet", "is_coastal": True, "connections": [(2, 0), (4, 0), (3, 1)]},
    (4, 0): {"name": "Kefe Eyaleti", "type": "eyalet", "is_coastal": True, "connections": [(3, 0), (5, 0), (4, 1)]},
    (5, 0): {"name": "Kırım Hanlığı", "type": "vasal", "is_coastal": True, "connections": [(4, 0), (5, 1)]},
    
    # Satır 1 - Yunanistan ve Anadolu kuzeyi
    (0, 1): {"name": "Arnavutluk Sancağı", "type": "sancak", "is_coastal": True, "connections": [(0, 0), (1, 1), (0, 2)]},
    (1, 1): {"name": "Selanik Sancağı", "type": "sancak", "is_coastal": True, "connections": [(0, 1), (2, 1), (1, 0), (1, 2)]},
    (2, 1): {"name": "Konstantiniye (Başkent)", "type": "başkent", "is_coastal": True, "connections": [(1, 1), (3, 1), (2, 0), (2, 2)]},
    (3, 1): {"name": "Kastamonu Sancağı", "type": "sancak", "is_coastal": True, "connections": [(2, 1), (4, 1), (3, 0), (3, 2)]},
    (4, 1): {"name": "Trabzon Eyaleti", "type": "eyalet", "is_coastal": True, "connections": [(3, 1), (5, 1), (4, 0), (4, 2)]},
    (5, 1): {"name": "Safevi Sınırı", "type": "düşman", "is_coastal": False, "connections": [(4, 1), (5, 0), (5, 2)]},
    
    # Satır 2 - Ege ve İç Anadolu
    (0, 2): {"name": "Mora Sancağı", "type": "sancak", "is_coastal": True, "connections": [(0, 1), (1, 2)]},
    (1, 2): {"name": "Aydın Sancağı (İzmir)", "type": "sancak", "is_coastal": True, "connections": [(0, 2), (2, 2), (1, 1), (1, 3)]},
    (2, 2): {"name": "Anadolu Eyaleti", "type": "eyalet", "is_coastal": False, "connections": [(1, 2), (3, 2), (2, 1), (2, 3)]},
    (3, 2): {"name": "Karaman Eyaleti", "type": "eyalet", "is_coastal": False, "connections": [(2, 2), (4, 2), (3, 1), (3, 3)]},
    (4, 2): {"name": "Dulkadir Beyliği", "type": "vasal", "is_coastal": False, "connections": [(3, 2), (5, 2), (4, 1), (4, 3)]},
    (5, 2): {"name": "Diyarbakır Eyaleti", "type": "eyalet", "is_coastal": False, "connections": [(4, 2), (5, 1), (5, 3)]},
    
    # Satır 3 - Akdeniz ve Güney Anadolu
    (0, 3): {"name": "Girit (Venedik)", "type": "düşman", "is_coastal": True, "connections": [(1, 3)]},
    (1, 3): {"name": "Rodos (Şövalyeler)", "type": "düşman", "is_coastal": True, "connections": [(0, 3), (2, 3), (1, 2)]},
    (2, 3): {"name": "Teke Sancağı (Antalya)", "type": "sancak", "is_coastal": True, "connections": [(1, 3), (3, 3), (2, 2)]},
    (3, 3): {"name": "Adana Sancağı", "type": "sancak", "is_coastal": True, "connections": [(2, 3), (4, 3), (3, 2)]},
    (4, 3): {"name": "Halep Eyaleti", "type": "eyalet", "is_coastal": False, "connections": [(3, 3), (5, 3), (4, 2), (4, 4)]},
    (5, 3): {"name": "Musul Eyaleti", "type": "eyalet", "is_coastal": False, "connections": [(4, 3), (5, 2), (5, 4)]},
    
    # Satır 4 (Güney) - Arap toprakları
    (2, 4): {"name": "Kıbrıs (Venedik)", "type": "düşman", "is_coastal": True, "connections": [(3, 4)]},
    (3, 4): {"name": "Şam Eyaleti", "type": "eyalet", "is_coastal": True, "connections": [(2, 4), (4, 4), (3, 3)]},
    (4, 4): {"name": "Kudüs Sancağı", "type": "sancak", "is_coastal": True, "connections": [(3, 4), (5, 4), (4, 3)]},
    (5, 4): {"name": "Bağdat (Safevi)", "type": "düşman", "is_coastal": False, "connections": [(4, 4), (5, 3)]},
}


class MapScreen(BaseScreen):
    """Büyük Osmanlı haritası - Grid tabanlı navigasyon"""
    
    def __init__(self, screen_manager):
        super().__init__(screen_manager)
        
        # Oyuncunun eyaleti (başlangıç: Anadolu)
        self.player_position = (2, 2)  # Anadolu Eyaleti
        self.current_position = self.player_position  # Gezilen konum
        
        self.info_panel = Panel(20, 350, 400, 150, "Bölge Bilgisi")
        
        self.back_button = Button(
            x=20,
            y=SCREEN_HEIGHT - 70,
            width=150,
            height=50,
            text="Geri (Backspace)",
            shortcut="backspace",
            callback=self._go_back
        )
        
        self._header_font = None
        self._map_font = None
    
    def get_header_font(self):
        if self._header_font is None:
            self._header_font = pygame.font.Font(None, FONTS['header'])
        return self._header_font
    
    def get_map_font(self):
        if self._map_font is None:
            self._map_font = pygame.font.Font(None, 20)
        return self._map_font
    
    def on_enter(self):
        # Oyuncunun eyaletini game_manager'dan al
        gm = self.screen_manager.game_manager
        if gm:
            # Eyalet ismine göre konum bul
            for pos, data in OTTOMAN_MAP.items():
                if gm.province.name in data['name']:
                    self.player_position = pos
                    break
        self.current_position = self.player_position
    
    def announce_screen(self):
        self.audio.announce_screen_change("Osmanlı Haritası")
        self.audio.speak("Ok tuşlarıyla haritada gezinin.", interrupt=False)
        self._announce_current_position()
    
    def _announce_current_position(self):
        """Mevcut konumu duyur"""
        data = OTTOMAN_MAP.get(self.current_position)
        if not data:
            return
        
        # Oyuncunun kendi eyaleti mi?
        is_home = self.current_position == self.player_position
        
        self.audio.speak(f"{data['name']}", interrupt=True)
        
        type_names = {
            "eyalet": "Eyalet",
            "sancak": "Sancak", 
            "başkent": "Payitaht (Başkent)",
            "vasal": "Vasal Devlet",
            "beylik": "Beylik",
            "sınır": "Sınır Bölgesi",
            "ada": "Ada"
        }
        self.audio.speak(f"Tür: {type_names.get(data['type'], data['type'])}", interrupt=False)
        
        if is_home:
            self.audio.speak("Burası sizin eyaletiniz.", interrupt=False)
        
        # Bağlantıları duyur
        connections = data.get('connections', [])
        if connections:
            neighbor_names = []
            for conn in connections:
                n = OTTOMAN_MAP.get(conn)
                if n:
                    neighbor_names.append(n['name'].split()[0])  # İlk kelime
            if neighbor_names:
                self.audio.speak(f"Komşular: {', '.join(neighbor_names[:4])}", interrupt=False)
    
    def _update_info_panel(self):
        """Bilgi panelini güncelle"""
        self.info_panel.clear()
        data = OTTOMAN_MAP.get(self.current_position)
        if not data:
            return
        
        self.info_panel.title = data['name']
        
        type_names = {
            "eyalet": "Eyalet",
            "sancak": "Sancak",
            "başkent": "Payitaht",
            "vasal": "Vasal",
            "beylik": "Beylik",
            "sınır": "Sınır",
            "ada": "Ada"
        }
        self.info_panel.add_item("Tür", type_names.get(data['type'], data['type']))
        self.info_panel.add_item("Konum", f"({self.current_position[0]}, {self.current_position[1]})")
        
        is_home = self.current_position == self.player_position
        if is_home:
            self.info_panel.add_item("Durum", "SİZİN EYALETİNİZ")
        else:
            # Diplomasi durumu
            gm = self.screen_manager.game_manager
            if gm and data['name'] in gm.diplomacy.neighbors:
                relation = gm.diplomacy.neighbors[data['name']]
                rel = relation.value  # Relation objesi
                status = "Dost" if rel >= 50 else "Nötr" if rel >= 0 else "Düşman"
                self.info_panel.add_item("İlişki", f"{status} (%{rel})")
    
    def handle_event(self, event) -> bool:
        try:
            if self.back_button.handle_event(event):
                return True
            
            if event.type == pygame.KEYDOWN:
                # Backspace / Escape - Geri
                if event.key in (pygame.K_BACKSPACE, pygame.K_ESCAPE):
                    self._go_back()
                    return True
                
                # Yukarı ok - Kuzeye git
                if event.key == pygame.K_UP:
                    self._move(0, -1)
                    return True
                
                # Aşağı ok - Güneye git
                if event.key == pygame.K_DOWN:
                    self._move(0, 1)
                    return True
                
                # Sol ok - Batıya git
                if event.key == pygame.K_LEFT:
                    self._move(-1, 0)
                    return True
                
                # Sağ ok - Doğuya git
                if event.key == pygame.K_RIGHT:
                    self._move(1, 0)
                    return True
                
                # Home - Kendi eyaletine dön
                if event.key == pygame.K_HOME:
                    self.current_position = self.player_position
                    self._announce_current_position()
                    return True
                
                # H - Elçi gönder
                if event.key == pygame.K_h and self.current_position != self.player_position:
                    self._send_envoy()
                    return True
                
                # F1 - Yardım
                if event.key == pygame.K_F1:
                    self.audio.speak("Harita Kontrolleri:", interrupt=True)
                    self.audio.speak("Ok tuşları: Haritada gezin", interrupt=False)
                    self.audio.speak("Home: Kendi eyaletinize dönün", interrupt=False)
                    self.audio.speak("H: Elçi gönder", interrupt=False)
                    self.audio.speak("Backspace: Geri dön", interrupt=False)
                    return True
            
            return False
        except Exception as e:
            import traceback
            print(f"HARITA HATASI: {e}")
            traceback.print_exc()
            return False
    
    def _move(self, dx: int, dy: int):
        """Haritada hareket et"""
        try:
            new_x = self.current_position[0] + dx
            new_y = self.current_position[1] + dy
            new_pos = (new_x, new_y)
            
            # Hedef konum var mı?
            if new_pos in OTTOMAN_MAP:
                self.current_position = new_pos
                try:
                    self.audio.play_ui_sound('click')
                except:
                    pass  # Ses dosyası yoksa hata verme
                self._announce_current_position()
            else:
                # Yön ismi
                dir_name = ""
                if dy < 0:
                    dir_name = "kuzeyde"
                elif dy > 0:
                    dir_name = "güneyde"
                elif dx < 0:
                    dir_name = "batıda"
                elif dx > 0:
                    dir_name = "doğuda"
                self.audio.speak(f"Bu yönde ({dir_name}) bölge yok.", interrupt=True)
        except Exception as e:
            print(f"Harita hatası: {e}")
    
    def _send_envoy(self):
        """Bulunulan konuma elçi gönder"""
        gm = self.screen_manager.game_manager
        data = OTTOMAN_MAP.get(self.current_position)
        
        if not gm or not data:
            return
        
        if gm.diplomacy.send_envoy(data['name']):
            self.audio.speak(f"{data['name']}'e elçi gönderildi.", interrupt=True)
        else:
            self.audio.speak("Elçi gönderilemedi.", interrupt=True)
    
    def update(self, dt: float):
        self._update_info_panel()
    
    def draw(self, surface: pygame.Surface):
        # Başlık
        header_font = self.get_header_font()
        title = header_font.render("🗺️ OSMANLI İMPARATORLUĞU HARİTASI", True, COLORS['gold'])
        surface.blit(title, (20, 20))
        
        # Harita çiz
        self._draw_map(surface)
        
        # Bilgi paneli
        self.info_panel.draw(surface)
        
        # Kontroller
        self._draw_controls(surface)
        
        # Geri butonu
        self.back_button.draw(surface)
    
    def _draw_map(self, surface: pygame.Surface):
        """Haritayı çiz"""
        font = self.get_map_font()
        
        # Grid boyutları
        cell_width = 120
        cell_height = 50
        start_x = 50
        start_y = 60
        
        for pos, data in OTTOMAN_MAP.items():
            x = start_x + pos[0] * cell_width
            y = start_y + pos[1] * cell_height
            
            # Renk belirle
            if pos == self.current_position:
                color = COLORS['gold']
                border = 3
            elif pos == self.player_position:
                color = COLORS['success']
                border = 2
            else:
                type_colors = {
                    "eyalet": COLORS['text'],
                    "sancak": (150, 150, 150),
                    "başkent": (255, 215, 0),
                    "vasal": (100, 150, 200),
                    "beylik": (200, 150, 100),
                    "sınır": (150, 100, 100),
                    "ada": (100, 150, 150)
                }
                color = type_colors.get(data['type'], COLORS['text'])
                border = 1
            
            # Kutu çiz
            rect = pygame.Rect(x, y, cell_width - 5, cell_height - 5)
            pygame.draw.rect(surface, color, rect, border)
            
            # İsim yaz (kısaltılmış)
            name = data['name'][:12]
            text = font.render(name, True, color)
            text_rect = text.get_rect(center=rect.center)
            surface.blit(text, text_rect)
    
    def _draw_controls(self, surface: pygame.Surface):
        """Kontrol ipuçlarını çiz"""
        font = pygame.font.Font(None, FONTS['small'])
        
        hints = [
            "←↑↓→ Gezin | Home: Eve Dön | H: Elçi Gönder | F1: Yardım"
        ]
        
        for i, hint in enumerate(hints):
            text = font.render(hint, True, COLORS['text'])
            surface.blit(text, (450, 480 + i * 20))
    
    def _go_back(self):
        self.screen_manager.change_screen(ScreenType.DIPLOMACY)
