# -*- coding: utf-8 -*-
"""
Osmanlı Eyalet Yönetim Simülasyonu - Eyalet Seçim Ekranı
"""

import pygame
from ui.screen_manager import BaseScreen, ScreenType
from ui.components import Button, Panel, MenuList
from config import COLORS, FONTS, SCREEN_WIDTH, SCREEN_HEIGHT
from game.data.territories import TERRITORIES, TerritoryType, Region


def _get_difficulty(territory):
    """Bölge türüne göre zorluk belirle"""
    if territory.territory_type == TerritoryType.OSMANLI_SANCAK and territory.is_coastal:
        return "Kolay"
    elif territory.territory_type == TerritoryType.OSMANLI_EYALET:
        return "Orta"
    elif territory.territory_type == TerritoryType.VASAL:
        return "Zor"
    elif territory.territory_type == TerritoryType.KOMSU_DEVLET:
        return "Çok Zor"
    else:
        return "Orta"


def _get_region_name(region):
    """Bölge enum'unu Türkçe isme çevir"""
    names = {
        Region.ANADOLU: "Anadolu",
        Region.BALKANLAR: "Rumeli",
        Region.ORTADOGU: "Ortadoğu",
        Region.AFRIKA: "Afrika",
        Region.ADALAR: "Adalar",
        Region.KARADENIZ: "Karadeniz",
        Region.AVRUPA: "Avrupa",
        Region.IRAN: "İran"
    }
    return names.get(region, "Bilinmeyen")


def _get_description(territory):
    """Bölge açıklaması oluştur"""
    parts = []
    difficulty = _get_difficulty(territory)
    parts.append(difficulty)
    
    if territory.is_coastal:
        parts.append("Kıyı bölgesi")
    else:
        parts.append("İç bölge")
    
    if territory.special_resources:
        parts.append(f"Kaynaklar: {', '.join(territory.special_resources[:2])}")
    
    return ". ".join(parts)


# Tüm oynanabilir bölgeleri dinamik olarak oluştur
AVAILABLE_PROVINCES = []
for name, territory in TERRITORIES.items():
    # Sadece oynanabilir türler (komşu devletlerin bir kısmı hariç)
    if territory.territory_type in [TerritoryType.OSMANLI_EYALET, TerritoryType.OSMANLI_SANCAK, TerritoryType.VASAL]:
        AVAILABLE_PROVINCES.append({
            "name": territory.name,
            "capital": territory.capital,
            "region": _get_region_name(territory.region),
            "is_coastal": territory.is_coastal,
            "description": _get_description(territory),
            "difficulty": _get_difficulty(territory)
        })

# Zorluğa göre sırala (Kolay -> Orta -> Zor)
difficulty_order = {"Kolay": 0, "Orta": 1, "Zor": 2, "Çok Zor": 3}
AVAILABLE_PROVINCES.sort(key=lambda x: difficulty_order.get(x["difficulty"], 1))


class ProvinceSelectScreen(BaseScreen):
    """Eyalet seçim ekranı - Yeni oyun başlarken"""
    
    def __init__(self, screen_manager):
        super().__init__(screen_manager)
        
        # Eyalet menüsü
        self.province_menu = MenuList(
            x=(SCREEN_WIDTH - 600) // 2,
            y=180,
            width=600,
            item_height=70
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
        
        self._title_font = None
        self._setup_menu()
    
    def get_title_font(self):
        if self._title_font is None:
            self._title_font = pygame.font.Font(None, FONTS['header'])
        return self._title_font
    
    def _setup_menu(self):
        """Eyalet menüsünü oluştur"""
        self.province_menu.clear()
        
        for i, province in enumerate(AVAILABLE_PROVINCES):
            coastal_text = "[Kiyi]" if province["is_coastal"] else "[Ic]"
            text = f"{province['name']} ({province['difficulty']}) - {coastal_text}"
            self.province_menu.add_item(
                text,
                lambda p=province: self._select_province(p),
                str(i + 1)
            )
    
    def on_enter(self):
        self._setup_menu()
    
    def announce_screen(self):
        self.audio.announce_screen_change("Eyalet Seçimi")
        self.audio.speak(
            "Yönetmek istediğiniz eyaleti seçin. "
            "Kıyı eyaletlerinde tersane inşa edebilirsiniz.",
            interrupt=False
        )
    
    def handle_event(self, event) -> bool:
        if self.province_menu.handle_event(event):
            return True
        
        if self.back_button.handle_event(event):
            return True
        
        if event.type == pygame.KEYDOWN:
            # Backspace veya Escape - Geri
            if event.key in (pygame.K_BACKSPACE, pygame.K_ESCAPE):
                self._go_back()
                return True
            
            # F1 - Yardım
            if event.key == pygame.K_F1:
                self._announce_selected_province()
                return True
            
            # 1-6 Direkt seçim
            for i in range(6):
                if event.key == getattr(pygame, f'K_{i+1}'):
                    if i < len(AVAILABLE_PROVINCES):
                        self._select_province(AVAILABLE_PROVINCES[i])
                    return True
        
        return False
    
    def _announce_selected_province(self):
        """Seçili eyalet bilgisini duyur"""
        idx = self.province_menu.selected_index
        if 0 <= idx < len(AVAILABLE_PROVINCES):
            p = AVAILABLE_PROVINCES[idx]
            coastal = "Kıyı şehri, tersane inşa edilebilir" if p["is_coastal"] else "İç bölge, tersane inşa edilemez"
            self.audio.speak(
                f"{p['name']}. Başkent: {p['capital']}. "
                f"Bölge: {p['region']}. {p['description']}. {coastal}.",
                interrupt=True
            )
    
    def _select_province(self, province: dict):
        """Eyalet seç ve oyunu başlat"""
        gm = self.screen_manager.game_manager
        if gm:
            # Eyalet bilgilerini ayarla
            gm.province.name = province["name"]
            gm.province.capital = province["capital"]
            gm.province.region = province["region"]
            gm.province.is_coastal = province["is_coastal"]
            
            # Oyunu başlat
            gm.new_game()
            
            # Eyalete özel komşuları güncelle
            gm.diplomacy.update_neighbors(province["name"])
            
            # Kıyı bilgisi duyur
            coastal_msg = "Tersane inşa edebilirsiniz." if province["is_coastal"] else "İç bölgedesiniz, tersane inşa edilemez."
            self.audio.speak(
                f"{province['name']} seçildi. {coastal_msg}",
                interrupt=True
            )
            
            self.screen_manager.change_screen(ScreenType.PROVINCE_VIEW)
    
    def update(self, dt: float):
        pass
    
    def draw(self, surface: pygame.Surface):
        # Başlık
        title_font = self.get_title_font()
        title = title_font.render("EYALET SECIMI", True, COLORS['gold'])
        title_rect = title.get_rect(centerx=SCREEN_WIDTH // 2, top=40)
        surface.blit(title, title_rect)
        
        # Alt başlık
        subtitle_font = pygame.font.Font(None, FONTS['body'])
        subtitle = subtitle_font.render(
            "Yonetmek istediginiz eyaleti secin. [Kiyi] = Tersane, [Ic] = Ic bolge",
            True, COLORS['text']
        )
        subtitle_rect = subtitle.get_rect(centerx=SCREEN_WIDTH // 2, top=100)
        surface.blit(subtitle, subtitle_rect)
        
        # Eyalet menüsü
        self.province_menu.draw(surface)
        
        # Seçili eyalet detayı
        self._draw_province_detail(surface)
        
        # Geri butonu
        self.back_button.draw(surface)
    
    def _draw_province_detail(self, surface: pygame.Surface):
        """Seçili eyalet detaylarını göster"""
        idx = self.province_menu.selected_index
        if 0 <= idx < len(AVAILABLE_PROVINCES):
            p = AVAILABLE_PROVINCES[idx]
            
            detail_rect = pygame.Rect(
                (SCREEN_WIDTH - 600) // 2,
                SCREEN_HEIGHT - 180,
                600,
                100
            )
            pygame.draw.rect(surface, COLORS['panel_bg'], detail_rect, border_radius=10)
            pygame.draw.rect(surface, COLORS['panel_border'], detail_rect, width=2, border_radius=10)
            
            font = pygame.font.Font(None, FONTS['body'])
            
            # Başkent
            capital_text = font.render(f"Başkent: {p['capital']}", True, COLORS['gold'])
            surface.blit(capital_text, (detail_rect.x + 20, detail_rect.y + 15))
            
            # Bölge
            region_text = font.render(f"Bölge: {p['region']}", True, COLORS['text'])
            surface.blit(region_text, (detail_rect.x + 20, detail_rect.y + 40))
            
            # Açıklama
            desc_text = font.render(p['description'], True, COLORS['text'])
            surface.blit(desc_text, (detail_rect.x + 20, detail_rect.y + 65))
    
    def _go_back(self):
        self.screen_manager.change_screen(ScreenType.MAIN_MENU)
