# -*- coding: utf-8 -*-
"""
Osmanlı Eyalet Yönetim Simülasyonu - Akın Rapor Ekranı
Akın sonuçlarını canlı hikaye anlatımıyla sunar.
"""

import pygame
import random
from dataclasses import dataclass
from typing import Dict, List, Optional
from ui.screen_manager import BaseScreen, ScreenType
from ui.components import Panel
from config import COLORS, FONTS, SCREEN_WIDTH, SCREEN_HEIGHT, get_font


@dataclass
class RaidStory:
    """Akın hikayesi verileri"""
    target_name: str                    # Hedef ismi
    raid_size: int                      # Akın birlik sayısı
    villages_raided: int                # Basılan köy sayısı (1-5)
    encounter_type: str                 # "patrol", "ambush", "surrender", "none"
    loot_gold: int                      # Yağmalanan altın
    loot_food: int                      # Yağmalanan yiyecek
    prisoners_taken: int                # Esir alınan
    enemy_killed: int                   # Öldürülen düşman
    our_casualties: int                 # Bizim kayıplarımız
    victory: bool                       # Zafer mi?
    enemy_commander: str                # Düşman komutan ismi
    special_event: Optional[str] = None # Özel olay


# Rastgele düşman komutan isimleri
ENEMY_COMMANDERS = [
    "Kont Dracula", "Voyvoda Mircea", "Ban Petrović", 
    "Despot Lazar", "Kral Mátyás", "Dük Ferdinand",
    "Kardinal Antonio", "Baron von Habsburg", "Prens Konstantin"
]

# Özel olaylar
SPECIAL_EVENTS = [
    "Akıncılar hazine dolu bir araba ele geçirdi!",
    "Düşman casusları pusuya düşürüldü!",
    "Yerel halk direniş göstermeden teslim oldu.",
    "Bir düşman subayı esir alındı!",
    "Akıncılar gizli bir silah deposu buldu!",
    None, None, None  # Çoğu zaman özel olay yok
]


class RaidReportScreen(BaseScreen):
    """Akın raporu - canlı hikaye anlatımı ekranı"""
    
    # Olay zamanlaması (saniye cinsinden)
    EVENT_TIMELINE = [
        (0.0, "intro"),           # Giriş
        (2.5, "scout"),           # Keşif
        (5.0, "approach"),        # Yaklaşma
        (7.5, "raid_start"),      # Baskın başlangıcı
        (10.0, "loot"),           # Yağma
        (12.5, "encounter"),      # Karşılaşma
        (15.0, "retreat"),        # Geri çekilme
        (17.5, "result"),         # Sonuç
        (20.0, "close"),          # Kapanış
    ]
    
    def __init__(self, screen_manager):
        super().__init__(screen_manager)
        
        self.raid_story: Optional[RaidStory] = None
        self.elapsed_time = 0.0
        self.events_played = set()
        self.current_text = ""
        self.is_complete = False
        
        # Görsel elemanlar
        self.main_panel = Panel(50, 100, SCREEN_WIDTH - 100, 350, "Akın Raporu")
        self.result_panel = Panel(50, 470, SCREEN_WIDTH - 100, 120, "Sonuç")
        
        self._header_font = None
        self._text_font = None
    
    def get_header_font(self):
        if self._header_font is None:
            self._header_font = get_font(FONTS['header'])
        return self._header_font
    
    def get_text_font(self):
        if self._text_font is None:
            self._text_font = get_font(FONTS['body'])
        return self._text_font
    
    def set_raid_story(self, story: RaidStory):
        """Akın hikayesini ayarla"""
        self.raid_story = story
        self.elapsed_time = 0.0
        self.events_played = set()
        self.current_text = ""
        self.is_complete = False
    
    def generate_raid_story(self, target: str, raid_size: int, victory: bool, 
                           loot_gold: int, our_casualties: int) -> RaidStory:
        """Akın hikayesi oluştur"""
        villages = random.randint(1, 4) if victory else random.randint(0, 2)
        
        # Karşılaşma türü
        encounters = ["patrol", "ambush", "surrender", "none"]
        weights = [0.3, 0.2, 0.2, 0.3] if victory else [0.4, 0.3, 0.1, 0.2]
        encounter = random.choices(encounters, weights=weights)[0]
        
        # Yağma detayları
        loot_food = random.randint(100, 500) if victory else 0
        prisoners = random.randint(5, 30) if victory and encounter != "ambush" else 0
        enemy_killed = random.randint(20, 80) if victory else random.randint(5, 20)
        
        special = random.choice(SPECIAL_EVENTS) if victory and random.random() > 0.6 else None
        
        return RaidStory(
            target_name=target,
            raid_size=raid_size,
            villages_raided=villages,
            encounter_type=encounter,
            loot_gold=loot_gold,
            loot_food=loot_food,
            prisoners_taken=prisoners,
            enemy_killed=enemy_killed,
            our_casualties=our_casualties,
            victory=victory,
            enemy_commander=random.choice(ENEMY_COMMANDERS),
            special_event=special
        )
    
    def on_enter(self):
        """Ekrana girişte"""
        self.elapsed_time = 0.0
        self.events_played = set()
        self.is_complete = False
        
        # İlk duyuru
        if self.raid_story:
            self.audio.speak("Akın Raporu. Hikaye başlıyor...", interrupt=True)
    
    def announce_screen(self):
        self.audio.announce_screen_change("Akın Raporu")
    
    def _get_event_text(self, event_type: str) -> str:
        """Olay türüne göre metin döndür"""
        if not self.raid_story:
            return ""
        
        story = self.raid_story
        
        texts = {
            "intro": f"{story.raid_size} akıncı askeri {story.target_name} topraklarına doğru yola çıktı!",
            
            "scout": "Keşif birlikleri düşman köylerini tespit ediyor... İlerleyen atlılar ufukta toz kaldırıyor.",
            
            "approach": f"Süvari birlikleri {story.villages_raided} köye yaklaşıyor. Sessizce mevzi alınıyor...",
            
            "raid_start": f"BASKIN! Akıncılar köylere saldırıya geçti! Düşman {story.enemy_commander} komutasında savunma yapıyor.",
            
            "loot": self._get_loot_text(),
            
            "encounter": self._get_encounter_text(),
            
            "retreat": "Akıncı birlikleri ganimetlerle birlikte geri çekiliyor... Atlılar hızla uzaklaşıyor.",
            
            "result": self._get_result_text(),
            
            "close": "Akın raporu tamamlandı. Devam etmek için Enter tuşuna basın."
        }
        
        return texts.get(event_type, "")
    
    def _get_loot_text(self) -> str:
        """Yağma metnini oluştur"""
        if not self.raid_story:
            return ""
        
        story = self.raid_story
        
        if story.victory:
            parts = []
            if story.loot_gold > 0:
                parts.append(f"{story.loot_gold} altın")
            if story.loot_food > 0:
                parts.append(f"{story.loot_food} birim yiyecek")
            if story.prisoners_taken > 0:
                parts.append(f"{story.prisoners_taken} esir")
            
            loot_str = ", ".join(parts) if parts else "az miktarda ganimet"
            
            base = f"Yağma devam ediyor! Şu ana kadar toplanan: {loot_str}."
            
            if story.special_event:
                base += f" Özel haber: {story.special_event}"
            
            return base
        else:
            return "Yağma girişimi başarısız! Düşman savunması çok güçlü."
    
    def _get_encounter_text(self) -> str:
        """Karşılaşma metnini oluştur"""
        if not self.raid_story:
            return ""
        
        story = self.raid_story
        
        encounter_texts = {
            "patrol": f"Düşman devriye birliği ile karşılaşıldı! {story.enemy_killed} düşman askeri öldürüldü, {story.our_casualties} kayıp verdik.",
            "ambush": f"PUSU! Düşman bizi pusuya düşürdü! Ağır çatışma... {story.our_casualties} askerimiz şehit düştü.",
            "surrender": f"Köy halkı direniş göstermeden teslim oldu. Kan dökülmeden {story.prisoners_taken} esir alındı.",
            "none": "Düşman kuvvetleriyle herhangi bir karşılaşma olmadı. Akın sessizce tamamlandı."
        }
        
        return encounter_texts.get(story.encounter_type, "Çatışma yaşandı.")
    
    def _get_result_text(self) -> str:
        """Sonuç metnini oluştur"""
        if not self.raid_story:
            return ""
        
        story = self.raid_story
        
        if story.victory:
            return (f"ZAFER! Akın başarıyla tamamlandı. "
                   f"Toplam ganimet: {story.loot_gold} altın. "
                   f"Kayıplarımız: {story.our_casualties} asker. "
                   f"{story.enemy_killed} düşman öldürüldü.")
        else:
            return (f"YENİLGİ! Akın başarısızlıkla sonuçlandı. "
                   f"Kayıplarımız: {story.our_casualties} asker. "
                   f"Askerler geri çekildi.")
    
    def handle_event(self, event) -> bool:
        if event.type == pygame.KEYDOWN:
            # Enter veya Escape ile çık
            if event.key in (pygame.K_RETURN, pygame.K_ESCAPE, pygame.K_SPACE):
                self._close_screen()
                return True
            
            # S tuşu - hikayeyi atla
            if event.key == pygame.K_s:
                self.elapsed_time = 20.0
                self._play_event("result")
                self._play_event("close")
                return True
        
        return False
    
    def update(self, dt: float):
        """Ekranı güncelle"""
        if self.is_complete:
            return
        
        self.elapsed_time += dt
        
        # Zamanlanmış olayları kontrol et
        for event_time, event_type in self.EVENT_TIMELINE:
            if event_time <= self.elapsed_time and event_type not in self.events_played:
                self._play_event(event_type)
        
        # Otomatik kapanış kontrolü
        if self.elapsed_time >= 22.0:  # 2 saniye ekstra bekleme
            self._close_screen()
    
    def _play_event(self, event_type: str):
        """Olayı oynat"""
        if event_type in self.events_played:
            return
        
        self.events_played.add(event_type)
        
        if event_type == "close":
            self.is_complete = True
            return
        
        text = self._get_event_text(event_type)
        if text:
            self.current_text = text
            self.audio.speak(text, interrupt=True)
            
            # Paneli güncelle
            self.main_panel.clear()
            
            # Metnin ilk 50 karakterini başlık olarak kullan
            short_text = text[:60] + "..." if len(text) > 60 else text
            self.main_panel.add_item("", short_text)
    
    def _close_screen(self):
        """Ekranı kapat ve önceki ekrana dön"""
        self.is_complete = True
        self.screen_manager.change_screen(ScreenType.WARFARE)
    
    def draw(self, surface: pygame.Surface):
        # Arka plan
        surface.fill(COLORS['background'])
        
        # Başlık
        header_font = self.get_header_font()
        
        if self.raid_story:
            title_text = f"AKIN RAPORU: {self.raid_story.target_name}"
        else:
            title_text = "AKIN RAPORU"
        
        title = header_font.render(title_text, True, COLORS['gold'])
        surface.blit(title, (50, 30))
        
        # İlerleme çubuğu
        progress = min(1.0, self.elapsed_time / 20.0)
        bar_width = SCREEN_WIDTH - 100
        bar_x = 50
        bar_y = 70
        
        pygame.draw.rect(surface, COLORS['panel_border'], 
                        (bar_x, bar_y, bar_width, 10), 1)
        pygame.draw.rect(surface, COLORS['gold'],
                        (bar_x + 2, bar_y + 2, int((bar_width - 4) * progress), 6))
        
        # Ana panel - mevcut olay metni
        self.main_panel.draw(surface)
        
        # Mevcut metin (daha büyük göster)
        if self.current_text:
            text_font = self.get_text_font()
            
            # Metni satırlara böl
            words = self.current_text.split()
            lines = []
            current_line = ""
            max_width = SCREEN_WIDTH - 140
            
            for word in words:
                test_line = current_line + " " + word if current_line else word
                test_surface = text_font.render(test_line, True, COLORS['text'])
                
                if test_surface.get_width() <= max_width:
                    current_line = test_line
                else:
                    if current_line:
                        lines.append(current_line)
                    current_line = word
            
            if current_line:
                lines.append(current_line)
            
            # Satırları çiz
            y_offset = 150
            for line in lines[:6]:  # Maksimum 6 satır
                line_surface = text_font.render(line, True, COLORS['text'])
                surface.blit(line_surface, (70, y_offset))
                y_offset += 35
        
        # Sonuç paneli (sadece sonuç aşamasında)
        if "result" in self.events_played and self.raid_story:
            self.result_panel.clear()
            story = self.raid_story
            
            result_text = "ZAFER" if story.victory else "YENİLGİ"
            self.result_panel.add_item("Sonuç", result_text)
            self.result_panel.add_item("Ganimet", f"{story.loot_gold} altın")
            self.result_panel.add_item("Kayıp", f"{story.our_casualties} asker")
            
            self.result_panel.draw(surface)
        
        # Kontrol bilgisi
        small_font = get_font(FONTS['small'])
        controls = small_font.render("Enter: Kapat | S: Atla", True, COLORS['text_dark'])
        surface.blit(controls, (50, SCREEN_HEIGHT - 40))
