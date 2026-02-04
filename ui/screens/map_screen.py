# -*- coding: utf-8 -*-
"""
Osmanlı Eyalet Yönetim Simülasyonu - Büyük Osmanlı Haritası
Yön tabanlı navigasyon ile tüm bölgeler (territories.py verisi)
"""

import pygame
from ui.screen_manager import BaseScreen, ScreenType
from ui.components import Button, Panel
from config import COLORS, FONTS, SCREEN_WIDTH, SCREEN_HEIGHT
from game.data.territories import (
    TERRITORIES, Territory, TerritoryType, Region,
    get_territory, get_neighbors_with_direction, get_all_neighbors
)


def _get_type_name(territory: Territory) -> str:
    """Bölge türü Türkçe adı"""
    type_names = {
        TerritoryType.OSMANLI_EYALET: "Osmanlı Eyaleti",
        TerritoryType.OSMANLI_SANCAK: "Osmanlı Sancağı",
        TerritoryType.VASAL: "Vasal Devlet",
        TerritoryType.KOMSU_DEVLET: "Komşu Devlet"
    }
    return type_names.get(territory.territory_type, "Bilinmeyen")


def _get_region_name(territory: Territory) -> str:
    """Bölge coğrafyası Türkçe adı"""
    region_names = {
        Region.ANADOLU: "Anadolu",
        Region.BALKANLAR: "Rumeli",
        Region.ORTADOGU: "Ortadoğu",
        Region.AFRIKA: "Afrika",
        Region.ADALAR: "Adalar",
        Region.KARADENIZ: "Karadeniz",
        Region.AVRUPA: "Avrupa",
        Region.IRAN: "İran"
    }
    return region_names.get(territory.region, "Bilinmeyen")


class MapScreen(BaseScreen):
    """Büyük Osmanlı haritası - Yön tabanlı komşu navigasyonu"""
    
    def __init__(self, screen_manager):
        super().__init__(screen_manager)
        
        # Mevcut konumdaki bölge ismi
        self.current_territory_name = "Rum Eyaleti"  # Varsayılan
        self.player_territory_name = "Rum Eyaleti"   # Oyuncunun eyaleti
        
        self.info_panel = Panel(20, 350, 400, 180, "Bölge Bilgisi")
        
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
        if gm and gm.province:
            self.player_territory_name = gm.province.name
        
        # Başlangıç konumu oyuncunun eyaleti
        self.current_territory_name = self.player_territory_name
    
    def announce_screen(self):
        self.audio.announce_screen_change("Osmanlı Haritası")
        self.audio.speak("Ok tuşlarıyla haritada gezinin. Yukarı: Kuzey, Aşağı: Güney, Sol: Batı, Sağ: Doğu", interrupt=False)
        self._announce_current_position()
    
    def _announce_current_position(self):
        """Mevcut konumu duyur"""
        territory = get_territory(self.current_territory_name)
        if not territory:
            self.audio.speak(f"{self.current_territory_name} - bilinmeyen bölge", interrupt=True)
            return
        
        # Oyuncunun kendi eyaleti mi?
        is_home = self.current_territory_name == self.player_territory_name
        
        self.audio.speak(f"{territory.name}", interrupt=True)
        self.audio.speak(f"Tür: {_get_type_name(territory)}", interrupt=False)
        self.audio.speak(f"Bölge: {_get_region_name(territory)}", interrupt=False)
        
        if territory.is_coastal:
            self.audio.speak("Kıyı bölgesi", interrupt=False)
        
        if is_home:
            self.audio.speak("Burası sizin eyaletiniz!", interrupt=False)
        
        # Yönlere göre komşuları duyur
        neighbors = get_neighbors_with_direction(territory)
        directions = []
        if neighbors["kuzey"]:
            directions.append(f"Kuzey: {neighbors['kuzey'][0]}")
        if neighbors["güney"]:
            directions.append(f"Güney: {neighbors['güney'][0]}")
        if neighbors["doğu"]:
            directions.append(f"Doğu: {neighbors['doğu'][0]}")
        if neighbors["batı"]:
            directions.append(f"Batı: {neighbors['batı'][0]}")
        
        if directions:
            self.audio.speak(f"Komşular: {', '.join(directions[:4])}", interrupt=False)
    
    def _update_info_panel(self):
        """Bilgi panelini güncelle"""
        self.info_panel.clear()
        territory = get_territory(self.current_territory_name)
        if not territory:
            return
        
        self.info_panel.title = territory.name
        
        self.info_panel.add_item("Tür", _get_type_name(territory))
        self.info_panel.add_item("Bölge", _get_region_name(territory))
        self.info_panel.add_item("Başkent", territory.capital)
        
        if territory.is_coastal:
            self.info_panel.add_item("Kıyı", "Evet")
        
        is_home = self.current_territory_name == self.player_territory_name
        if is_home:
            self.info_panel.add_item("Durum", "SİZİN EYALETİNİZ")
        else:
            # Diplomasi durumu
            gm = self.screen_manager.game_manager
            if gm and territory.name in gm.diplomacy.neighbors:
                relation = gm.diplomacy.neighbors[territory.name]
                rel = relation.value
                status = "Dost" if rel >= 50 else "Nötr" if rel >= 0 else "Düşman"
                self.info_panel.add_item("İlişki", f"{status} ({rel})")
        
        # Kaynaklar
        if territory.special_resources:
            self.info_panel.add_item("Kaynaklar", ", ".join(territory.special_resources[:3]))
    
    def handle_event(self, event) -> bool:
        try:
            if self.back_button.handle_event(event):
                return True
        except Exception:
            pass
        
        if event.type == pygame.KEYDOWN:
            # Yön tuşları ile navigasyon
            if event.key == pygame.K_UP:
                self._move_direction("kuzey")
                return True
            elif event.key == pygame.K_DOWN:
                self._move_direction("güney")
                return True
            elif event.key == pygame.K_LEFT:
                self._move_direction("batı")
                return True
            elif event.key == pygame.K_RIGHT:
                self._move_direction("doğu")
                return True
            
            # Home - Kendi eyaletine dön
            elif event.key == pygame.K_HOME:
                self.current_territory_name = self.player_territory_name
                self._announce_current_position()
                self._update_info_panel()
                return True
            
            # E tuşu - Elçi gönder
            elif event.key == pygame.K_e:
                self._send_envoy()
                return True
            
            # Backspace - Geri
            elif event.key == pygame.K_BACKSPACE:
                self._go_back()
                return True
        
        return False
    
    def _move_direction(self, direction: str):
        """Belirtilen yöne hareket et"""
        territory = get_territory(self.current_territory_name)
        if not territory:
            return
        
        neighbors = get_neighbors_with_direction(territory)
        direction_neighbors = neighbors.get(direction, [])
        
        if direction_neighbors:
            # İlk komşuya git
            next_territory = direction_neighbors[0]
            if next_territory in TERRITORIES:
                self.current_territory_name = next_territory
                self._announce_current_position()
                self._update_info_panel()
            else:
                self.audio.speak(f"{next_territory} - bu bölgeye gidilemiyor", interrupt=True)
        else:
            direction_names = {"kuzey": "kuzeyde", "güney": "güneyde", "doğu": "doğuda", "batı": "batıda"}
            self.audio.speak(f"Bu yönde ({direction_names.get(direction, direction)}) komşu yok", interrupt=True)
    
    def _send_envoy(self):
        """Bulunulan konuma elçi gönder"""
        if self.current_territory_name == self.player_territory_name:
            self.audio.speak("Kendi eyaletinize elçi gönderemezsiniz.", interrupt=True)
            return
        
        gm = self.screen_manager.game_manager
        if gm:
            if gm.diplomacy.envoy_cooldown > 0:
                self.audio.speak(f"Elçi göndermek için {gm.diplomacy.envoy_cooldown} tur beklemelisiniz.", interrupt=True)
                return
            
            if self.current_territory_name in gm.diplomacy.neighbors:
                gm.diplomacy.send_envoy(self.current_territory_name)
                self.audio.speak(f"{self.current_territory_name} bölgesine elçi gönderildi!", interrupt=True)
            else:
                self.audio.speak("Bu bölgeye elçi gönderilemez.", interrupt=True)
    
    def update(self, dt: float):
        pass
    
    def draw(self, surface: pygame.Surface):
        surface.fill(COLORS['background'])
        
        # Başlık
        header_text = self.get_header_font().render(
            f"Osmanlı Haritası - {self.current_territory_name}",
            True, COLORS['text']
        )
        surface.blit(header_text, (20, 20))
        
        # Mini harita çizimi (basit metin tabanlı)
        self._draw_map(surface)
        
        # Bilgi paneli
        self.info_panel.draw(surface)
        self._update_info_panel()
        
        # Geri butonu
        self.back_button.draw(surface)
        
        # Kontrol ipuçları
        self._draw_controls(surface)
    
    def _draw_map(self, surface: pygame.Surface):
        """Haritayı çiz - mevcut bölge ve yönler"""
        territory = get_territory(self.current_territory_name)
        if not territory:
            return
        
        # Merkez bölge
        center_x = SCREEN_WIDTH // 2
        center_y = 200
        
        # Mevcut bölge kutusu
        pygame.draw.rect(surface, COLORS['primary'], (center_x - 80, center_y - 25, 160, 50))
        pygame.draw.rect(surface, COLORS['text'], (center_x - 80, center_y - 25, 160, 50), 2)
        
        font = self.get_map_font()
        text = font.render(territory.name[:20], True, COLORS['text'])
        text_rect = text.get_rect(center=(center_x, center_y))
        surface.blit(text, text_rect)
        
        # Yön göstergeleri
        neighbors = get_neighbors_with_direction(territory)
        
        # Kuzey
        if neighbors["kuzey"]:
            name = neighbors["kuzey"][0][:15]
            text = font.render(f"↑ {name}", True, COLORS['success'])
            surface.blit(text, (center_x - 60, center_y - 70))
        
        # Güney
        if neighbors["güney"]:
            name = neighbors["güney"][0][:15]
            text = font.render(f"↓ {name}", True, COLORS['success'])
            surface.blit(text, (center_x - 60, center_y + 45))
        
        # Batı
        if neighbors["batı"]:
            name = neighbors["batı"][0][:15]
            text = font.render(f"← {name}", True, COLORS['success'])
            surface.blit(text, (center_x - 200, center_y - 10))
        
        # Doğu
        if neighbors["doğu"]:
            name = neighbors["doğu"][0][:15]
            text = font.render(f"→ {name}", True, COLORS['success'])
            surface.blit(text, (center_x + 100, center_y - 10))
    
    def _draw_controls(self, surface: pygame.Surface):
        """Kontrol ipuçlarını çiz"""
        font = self.get_map_font()
        controls = [
            "↑↓←→: Haritada gezin",
            "Home: Kendi eyaletinize dönün",
            "E: Elçi gönder",
            "Backspace: Geri"
        ]
        
        y = SCREEN_HEIGHT - 130
        for ctrl in controls:
            text = font.render(ctrl, True, COLORS['text'])
            surface.blit(text, (450, y))
            y += 25
    
    def _go_back(self):
        self.screen_manager.change_screen(ScreenType.DIPLOMACY)
