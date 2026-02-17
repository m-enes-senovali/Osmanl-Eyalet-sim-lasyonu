# -*- coding: utf-8 -*-
"""
Osmanlı Eyalet Yönetim Simülasyonu - Lonca Yönetim Ekranı
Esnaf loncalarını görüntüleme, narh denetimi ve zanaat yönetimi
"""

import pygame
from ui.screen_manager import BaseScreen, ScreenType
from ui.components import Button, Panel, MenuList
from config import COLORS, FONTS, SCREEN_WIDTH, SCREEN_HEIGHT, get_font
from game.systems.guilds import GuildSystem, GuildType, GuildRank, GUILD_HIERARCHY


class GuildScreen(BaseScreen):
    """Lonca yönetim ekranı"""
    
    def __init__(self, screen_manager):
        super().__init__(screen_manager)
        
        # Paneller
        self.info_panel = Panel(20, 80, 400, 300, "Lonca Bilgisi")
        self.stats_panel = Panel(20, 400, 400, 200, "Üretim İstatistikleri")
        
        # Lonca menüsü
        self.guild_menu = MenuList(
            x=440,
            y=80,
            width=400,
            item_height=50
        )
        
        # Alt eylem menüsü
        self.action_menu = MenuList(
            x=440,
            y=400,
            width=400,
            item_height=45
        )
        
        # Geri butonu
        self.back_button = Button(
            SCREEN_WIDTH - 200, SCREEN_HEIGHT - 60,
            180, 45, "Geri", callback=self._go_back
        )
        
        # Font
        self._header_font = None
        
        # Durum
        self.selected_guild_key = None
        self.viewing_actions = False
    
    def get_header_font(self):
        if self._header_font is None:
            self._header_font = get_font(FONTS['header'])
        return self._header_font
    
    def on_enter(self):
        self._setup_guild_menu()
        self._setup_action_menu()
        self._update_panels()
    
    def announce_screen(self):
        gm = self.screen_manager.game_manager
        guild_system = self._get_guild_system()
        count = len(guild_system.guilds) if guild_system else 0
        self.audio.announce_screen_change(f"Lonca Yönetimi - {count} lonca aktif")
        self.audio.speak("Yukarı/aşağı ok ile lonca seçin. Tab ile eylem menüsüne geçin.", interrupt=False)
    
    def _get_guild_system(self) -> GuildSystem:
        """Oyun yöneticisinden lonca sistemini al, yoksa oluştur"""
        gm = self.screen_manager.game_manager
        if not gm:
            return None
        if not hasattr(gm, 'guild_system'):
            gm.guild_system = GuildSystem()
        return gm.guild_system
    
    def _setup_guild_menu(self):
        """Lonca listesini oluştur"""
        self.guild_menu.clear()
        guild_system = self._get_guild_system()
        if not guild_system:
            return
        
        if not guild_system.guilds:
            self.guild_menu.add_item("Henüz aktif lonca yok", None)
            self.guild_menu.add_item("", None)
            self.guild_menu.add_item("YENİ LONCA KUR ▼", lambda: self._show_create_menu())
            return
        
        for key, guild in guild_system.guilds.items():
            self.guild_menu.add_item(
                f"{guild.name_tr} ({guild.city}) - {guild.total_members} üye",
                lambda k=key: self._select_guild(k)
            )
        
        self.guild_menu.add_item("", None)
        self.guild_menu.add_item("YENİ LONCA KUR", lambda: self._show_create_menu())
    
    def _setup_action_menu(self):
        """Eylem menüsünü ayarla"""
        self.action_menu.clear()
        guild_system = self._get_guild_system()
        if not guild_system:
            return
        
        if self.selected_guild_key and self.selected_guild_key in guild_system.guilds:
            guild = guild_system.guilds[self.selected_guild_key]
            self.action_menu.add_item(
                f"Narh Denetimi: {guild.name_tr}",
                lambda: self._inspect_narh()
            )
            self.action_menu.add_item(
                f"Üretim Detayı: {guild.name_tr}",
                lambda: self._announce_production()
            )
        
        self.action_menu.add_item("Çeyreklik Rapor", lambda: self._quarterly_report())
        self.action_menu.add_item("Askeri Lojistik", lambda: self._military_support())
    
    def _select_guild(self, guild_key: str):
        """Lonca seç ve bilgilerini oku"""
        self.selected_guild_key = guild_key
        guild_system = self._get_guild_system()
        if not guild_system:
            return
        
        guild = guild_system.guilds.get(guild_key)
        if not guild:
            return
        
        self.audio.speak(
            f"{guild.name_tr} loncası, {guild.city}. "
            f"Toplam {guild.total_members} üye: "
            f"{guild.usta_count} usta, {guild.kalfa_count} kalfa, {guild.cirak_count} çırak. "
            f"Moral: yüzde {guild.guild_morale}. "
            f"Narh uyumu: yüzde {guild.narh_compliance}.",
            interrupt=True
        )
        
        self._update_panels()
        self._setup_action_menu()
    
    def _show_create_menu(self):
        """Yeni lonca kurma menüsünü göster"""
        self.guild_menu.clear()
        self.guild_menu.add_item("<- Geri", lambda: self._setup_guild_menu())
        self.guild_menu.add_item("", None)
        
        for guild_type in GuildType:
            name = guild_type.value.title()
            self.guild_menu.add_item(
                f"Kur: {name}",
                lambda gt=guild_type: self._create_guild(gt)
            )
    
    def _create_guild(self, guild_type: GuildType):
        """Yeni lonca kur"""
        gm = self.screen_manager.game_manager
        guild_system = self._get_guild_system()
        if not guild_system or not gm:
            return
        
        city = gm.province.name if hasattr(gm, 'province') else "İstanbul"
        guild = guild_system.create_guild(guild_type, city)
        self.audio.speak(
            f"{guild.name_tr} loncası {city} şehrinde kuruldu! "
            f"Şeyh: {guild.seyh_name}, Kethüda: {guild.kethuda_name}.",
            interrupt=True
        )
        self._setup_guild_menu()
        self._update_panels()
    
    def _inspect_narh(self):
        """Muhtesip narh denetimi"""
        guild_system = self._get_guild_system()
        if not guild_system or not self.selected_guild_key:
            return
        
        result = guild_system.inspect_narh(self.selected_guild_key)
        
        if result.get("violation_found"):
            severity = result.get("severity", "minor")
            penalties = result.get("penalties", {})
            fine = penalties.get("gold_fine", 0)
            self.audio.speak(
                f"Narh ihlali tespit edildi! Seviye: {severity}. "
                f"Para cezası: {fine} akçe. Moral düştü.",
                interrupt=True
            )
        else:
            self.audio.speak(
                f"{result.get('guild', '')} loncası narh kurallarına uyuyor. "
                f"Moral ve kalite arttı.",
                interrupt=True
            )
        self._update_panels()
    
    def _announce_production(self):
        """Üretim detayını oku"""
        guild_system = self._get_guild_system()
        if not guild_system or not self.selected_guild_key:
            return
        
        guild = guild_system.guilds.get(self.selected_guild_key)
        if not guild:
            return
        
        self.audio.speak(
            f"{guild.name_tr}: Günlük üretim {guild.daily_production:.1f} birim. "
            f"Üretim seviyesi: yüzde {guild.production_level}. "
            f"Kalite seviyesi: yüzde {guild.quality_level}. "
            f"Çeyreklik vergi katkısı: {guild.tax_contribution:.0f} akçe.",
            interrupt=True
        )
    
    def _quarterly_report(self):
        """Çeyreklik rapor"""
        guild_system = self._get_guild_system()
        if not guild_system:
            return
        
        result = guild_system.process_quarterly()
        self.audio.speak(
            f"Çeyreklik lonca raporu: "
            f"{result['guild_count']} aktif lonca. "
            f"Toplam vergi: {result['total_tax']:.0f} akçe. "
            f"Toplam üretim: {result['total_production']:.0f} birim.",
            interrupt=True
        )
        
        for event in result.get("events", []):
            self.audio.speak(event.get("message", ""), interrupt=False)
    
    def _military_support(self):
        """Askeri lojistik desteği"""
        guild_system = self._get_guild_system()
        if not guild_system:
            return
        
        support = guild_system.get_military_support()
        parts = []
        if support["leather"] > 0:
            parts.append(f"Deri teçhizat: {support['leather']:.1f}")
        if support["saddles"] > 0:
            parts.append(f"Eyer/koşum: {support['saddles']:.1f}")
        if support["weapons"] > 0:
            parts.append(f"Silah üretimi: {support['weapons']:.1f}")
        if support["construction"] > 0:
            parts.append(f"İnşaat desteği: {support['construction']:.1f}")
        
        if parts:
            self.audio.speak(f"Askeri lojistik: {', '.join(parts)}", interrupt=True)
        else:
            self.audio.speak("Askeri sektör loncası henüz kurulmamış.", interrupt=True)
    
    def _update_panels(self):
        """Panel bilgilerini güncelle"""
        guild_system = self._get_guild_system()
        
        self.info_panel.clear()
        self.stats_panel.clear()
        
        if not guild_system or not guild_system.guilds:
            self.info_panel.add_item("Durum", "Lonca yok")
            self.info_panel.add_item("İpucu", "Menüden lonca kurun")
            return
        
        if self.selected_guild_key and self.selected_guild_key in guild_system.guilds:
            guild = guild_system.guilds[self.selected_guild_key]
            self.info_panel.add_item("Lonca", guild.name_tr)
            self.info_panel.add_item("Şehir", guild.city)
            self.info_panel.add_item("Usta", str(guild.usta_count))
            self.info_panel.add_item("Kalfa", str(guild.kalfa_count))
            self.info_panel.add_item("Çırak", str(guild.cirak_count))
            self.info_panel.add_item("", "")
            self.info_panel.add_item("Moral", f"%{guild.guild_morale}")
            self.info_panel.add_item("Narh Uyumu", f"%{guild.narh_compliance}")
            
            self.stats_panel.add_item("Üretim", f"%{guild.production_level}")
            self.stats_panel.add_item("Kalite", f"%{guild.quality_level}")
            self.stats_panel.add_item("Günlük", f"{guild.daily_production:.1f}")
            self.stats_panel.add_item("Vergi/Çeyrek", f"{guild.tax_contribution:.0f}")
        else:
            self.info_panel.add_item("Toplam Lonca", str(len(guild_system.guilds)))
            self.info_panel.add_item("Muhtesip", "Aktif" if guild_system.muhtesip_active else "Pasif")
    
    def handle_event(self, event) -> bool:
        if self.back_button.handle_event(event):
            return True
        
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE or event.key == pygame.K_BACKSPACE:
                self._go_back()
                return True
            
            # Tab — menüler arası geçiş
            if event.key == pygame.K_TAB:
                self.viewing_actions = not self.viewing_actions
                if self.viewing_actions:
                    self.audio.speak("Eylem Menüsü", interrupt=True)
                else:
                    self.audio.speak("Lonca Listesi", interrupt=True)
                return True
            
            # F1 — özet oku
            if event.key == pygame.K_F1:
                guild_system = self._get_guild_system()
                if guild_system:
                    self.audio.speak(
                        f"Lonca sistemi: {len(guild_system.guilds)} aktif lonca. "
                        f"Narh katılığı: yüzde {guild_system.narh_strictness}.",
                        interrupt=True
                    )
                return True
        
        if self.viewing_actions:
            return self.action_menu.handle_event(event)
        else:
            return self.guild_menu.handle_event(event)
    
    def update(self, dt: float):
        pass
    
    def draw(self, surface: pygame.Surface):
        # Başlık
        header_font = self.get_header_font()
        title = header_font.render("Lonca Yönetimi", True, COLORS['gold'])
        title_rect = title.get_rect(centerx=SCREEN_WIDTH // 2, top=20)
        surface.blit(title, title_rect)
        
        # Paneller
        self.info_panel.draw(surface)
        self.stats_panel.draw(surface)
        
        # Menüler
        if self.viewing_actions:
            self.action_menu.draw(surface)
        else:
            self.guild_menu.draw(surface)
        
        # Geri butonu
        self.back_button.draw(surface)
        
        # Hiyerarşi bilgisi (sağ alt)
        small_font = get_font(FONTS['small'])
        hierarchy_text = "Şeyh → Kethüda → Yiğitbaşı → Ehli Hibre → Usta → Kalfa → Çırak"
        info = small_font.render(hierarchy_text, True, COLORS['text_dim'])
        info_rect = info.get_rect(centerx=SCREEN_WIDTH // 2, bottom=SCREEN_HEIGHT - 10)
        surface.blit(info, info_rect)
    
    def _go_back(self):
        self.screen_manager.change_screen(ScreenType.PROVINCE_VIEW)
