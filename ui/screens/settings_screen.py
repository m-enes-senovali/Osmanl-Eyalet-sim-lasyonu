# -*- coding: utf-8 -*-
"""
Osmanlı Eyalet Yönetim Simülasyonu - Ayarlar Ekranı
"""

import pygame
from ui.screen_manager import BaseScreen, ScreenType
from ui.components import Button, Panel, MenuList
from game.game_settings import get_settings, get_text, t
from config import COLORS, FONTS, SCREEN_WIDTH, SCREEN_HEIGHT, VERSION, get_font
from updater import get_updater
from audio.music_manager import get_music_manager


class SettingsScreen(BaseScreen):
    """Ayarlar ekranı"""
    
    def __init__(self, screen_manager):
        super().__init__(screen_manager)
        
        self.settings = get_settings()
        self.updater = get_updater()
        self.music_manager = get_music_manager()
        
        # Paneller
        self.sound_panel = Panel(20, 80, 400, 200, t('sound_settings'))
        self.auto_save_panel = Panel(20, 300, 400, 150, t('auto_save'))
        self.language_panel = Panel(440, 80, 350, 150, t('language'))
        self.update_panel = Panel(440, 250, 350, 200, "Güncelleme")
        
        # Ayarlar menüsü
        self.settings_menu = MenuList(
            x=20,
            y=160,
            width=400,
            item_height=45
        )
        
        self.back_button = Button(
            x=20,
            y=SCREEN_HEIGHT - 70,
            width=150,
            height=50,
            text=t('back'),
            shortcut="backspace",
            callback=self._go_back
        )
        
        self._header_font = None
        self.current_setting = None
        
        # Güncelleme durumu
        self.update_status = None
        self.update_checking = False
        self.update_downloading = False
        self.changelog_visible = False
    
    def get_header_font(self):
        if self._header_font is None:
            self._header_font = get_font(FONTS['header'])
        return self._header_font
    
    def on_enter(self):
        self.settings = get_settings()
        self._setup_settings_menu()
        self._update_panels()
    
    def announce_screen(self):
        lang = self.settings.get('language')
        if lang == 'en':
            self.audio.announce_screen_change("Settings")
        else:
            self.audio.announce_screen_change("Ayarlar")
    
    def _setup_settings_menu(self):
        """Ayarlar menüsünü oluştur"""
        self.settings_menu.clear()
        
        # Ses Ayarları
        music_vol = self.settings.get('music_volume')
        sfx_vol = self.settings.get('sfx_volume')
        music_on = self.settings.get('music_enabled')
        sfx_on = self.settings.get('sfx_enabled')
        
        music_status = t('enabled') if music_on else t('disabled')
        sfx_status = t('enabled') if sfx_on else t('disabled')
        
        self.settings_menu.add_item(
            f"{t('music_volume')}: {music_vol}%",
            lambda: self._change_volume('music_volume'),
            ""
        )
        self.settings_menu.add_item(
            f"{t('music_enabled')}: {music_status}",
            lambda: self._toggle_setting('music_enabled'),
            ""
        )
        self.settings_menu.add_item(
            f"{t('sfx_volume')}: {sfx_vol}%",
            lambda: self._change_volume('sfx_volume'),
            ""
        )
        self.settings_menu.add_item(
            f"{t('sfx_enabled')}: {sfx_status}",
            lambda: self._toggle_setting('sfx_enabled'),
            ""
        )
        
        self.settings_menu.add_item("", None, "")  # Ayırıcı
        
        # Otomatik Kayıt
        auto_save = self.settings.get('auto_save_enabled')
        auto_interval = self.settings.get('auto_save_interval')
        auto_status = t('enabled') if auto_save else t('disabled')
        
        self.settings_menu.add_item(
            f"{t('auto_save')}: {auto_status}",
            lambda: self._toggle_setting('auto_save_enabled'),
            ""
        )
        if auto_save:
            self.settings_menu.add_item(
                f"{t('auto_save_interval')}: {auto_interval}",
                lambda: self._change_interval(),
                ""
            )
        
        self.settings_menu.add_item("", None, "")  # Ayırıcı
        
        # Dil Seçimi
        current_lang = self.settings.get('language')
        lang_display = t('turkish') if current_lang == 'tr' else t('english')
        
        self.settings_menu.add_item(
            f"{t('language')}: {lang_display}",
            self._toggle_language,
            ""
        )
        
        self.settings_menu.add_item("", None, "")  # Ayırıcı
        
        # Güncelleme Seçenekleri
        if self.update_checking:
            self.settings_menu.add_item("Kontrol ediliyor...", None, "")
        elif self.update_downloading:
            progress = self.updater.download_progress
            self.settings_menu.add_item(f"İndiriliyor... %{progress}", None, "")
        elif self.update_status and self.update_status.get('available'):
            latest = self.update_status.get('latest', '?')
            self.settings_menu.add_item(
                f"Yeni Sürüm: {latest} (Güncelle)",
                self._download_update,
                "u"
            )
            self.settings_menu.add_item(
                "Değişiklikleri Oku",
                self._show_changelog,
                "c"
            )
        else:
            current = VERSION
            self.settings_menu.add_item(
                f"Sürüm: {current} - Güncelleme Kontrol Et",
                self._check_updates,
                "u"
            )
    
    def _update_panels(self):
        """Panelleri güncelle"""
        # Ses paneli
        self.sound_panel.clear()
        self.sound_panel.add_item(t('music_volume'), f"{self.settings.get('music_volume')}%")
        self.sound_panel.add_item(t('sfx_volume'), f"{self.settings.get('sfx_volume')}%")
        
        music_status = t('enabled') if self.settings.get('music_enabled') else t('disabled')
        sfx_status = t('enabled') if self.settings.get('sfx_enabled') else t('disabled')
        self.sound_panel.add_item(t('music_enabled'), music_status)
        self.sound_panel.add_item(t('sfx_enabled'), sfx_status)
        
        # Otomatik kayıt paneli
        self.auto_save_panel.clear()
        auto_status = t('enabled') if self.settings.get('auto_save_enabled') else t('disabled')
        self.auto_save_panel.add_item(t('auto_save'), auto_status)
        if self.settings.get('auto_save_enabled'):
            interval = self.settings.get('auto_save_interval')
            self.auto_save_panel.add_item(t('auto_save_interval'), str(interval))
        
        # Dil paneli
        self.language_panel.clear()
        current_lang = self.settings.get('language')
        lang_display = t('turkish') if current_lang == 'tr' else t('english')
        self.language_panel.add_item(t('language'), lang_display)
    
    def _change_volume(self, volume_key: str):
        """Ses seviyesini değiştir (10'ar artır/azalt, 0-100 arası döngüsel)"""
        current = self.settings.get(volume_key)
        new_value = (current + 10) % 110  # 0, 10, 20, ... 100, 0
        if new_value > 100:
            new_value = 0
        self.settings.set(volume_key, new_value)
        
        # Sadece ilgili ses kanalını güncelle (müziği etkilemeden)
        if volume_key == 'music_volume':
            music_enabled = self.settings.get('music_enabled')
            if music_enabled and hasattr(pygame.mixer, 'music'):
                pygame.mixer.music.set_volume(new_value / 100.0)
            self.audio.music_volume = new_value / 100.0
        elif volume_key == 'sfx_volume':
            sfx_enabled = self.settings.get('sfx_enabled')
            self.audio.sfx_volume = (new_value / 100.0) if sfx_enabled else 0
        
        name = t('music_volume') if 'music' in volume_key else t('sfx_volume')
        self.audio.speak(f"{name}: {new_value} yüzde", interrupt=True)
        
        saved_index = self.settings_menu.selected_index
        self._setup_settings_menu()
        self.settings_menu.selected_index = min(saved_index, len(self.settings_menu.items) - 1)
        self._update_panels()
    
    def _toggle_setting(self, setting_key: str):
        """Boolean ayarı değiştir"""
        current = self.settings.get(setting_key)
        self.settings.set(setting_key, not current)
        
        # Sadece ses ayarları için ses sistemine uygula
        if setting_key in ('music_enabled', 'sfx_enabled'):
            self._apply_volume_to_audio()
        
        status = t('enabled') if not current else t('disabled')
        self.audio.speak(f"{status}", interrupt=True)
        
        saved_index = self.settings_menu.selected_index
        self._setup_settings_menu()
        self.settings_menu.selected_index = min(saved_index, len(self.settings_menu.items) - 1)
        self._update_panels()
    
    def _change_interval(self):
        """Otomatik kayıt aralığını değiştir"""
        intervals = [3, 5, 10, 15, 20]
        current = self.settings.get('auto_save_interval')
        
        try:
            idx = intervals.index(current)
            new_interval = intervals[(idx + 1) % len(intervals)]
        except ValueError:
            new_interval = intervals[0]
        
        self.settings.set('auto_save_interval', new_interval)
        self.audio.speak(f"Her {new_interval} turda kaydet", interrupt=True)
        
        saved_index = self.settings_menu.selected_index
        self._setup_settings_menu()
        self.settings_menu.selected_index = min(saved_index, len(self.settings_menu.items) - 1)
        self._update_panels()
    
    def _toggle_language(self):
        """Dil değiştir"""
        current = self.settings.get('language')
        new_lang = 'en' if current == 'tr' else 'tr'
        self.settings.set('language', new_lang)
        
        if new_lang == 'en':
            self.audio.speak("Language changed to English", interrupt=True)
        else:
            self.audio.speak("Dil Türkçe olarak değiştirildi", interrupt=True)
        
        # Menüyü ve panelleri güncelle (yeni dilde)
        saved_index = self.settings_menu.selected_index
        self._setup_settings_menu()
        self.settings_menu.selected_index = min(saved_index, len(self.settings_menu.items) - 1)
        self._update_panels()
    
    def _check_updates(self):
        """Güncelleme kontrolü başlat"""
        self.update_checking = True
        self.audio.speak("Güncelleme kontrol ediliyor...", interrupt=True)
        self._setup_settings_menu()
        
        # Arka planda kontrol
        self.updater.check_async(self._on_update_check_complete)
    
    def _on_update_check_complete(self, result):
        """Güncelleme kontrolü tamamlandı"""
        self.update_checking = False
        self.update_status = result
        
        # Sonucu duyur
        self.updater.announce_status(result)
        
        # UI güncelle
        self._setup_settings_menu()
        self._update_panels()
    
    def _download_update(self):
        """Güncellemeyi indir"""
        self.update_downloading = True
        self.audio.speak("Güncelleme indiriliyor...", interrupt=True)
        self._setup_settings_menu()
        
        # Arka planda indir
        self.updater.download_async(self._on_download_progress)
    
    def _on_download_progress(self, progress, status):
        """İndirme ilerleme güncellemesi"""
        if progress < 0:
            # Hata
            self.update_downloading = False
            self.audio.speak(f"İndirme hatası: {status}", interrupt=True)
        elif progress >= 100:
            self.update_downloading = False
            self.audio.speak("Güncelleme tamamlandı!", interrupt=True)
        else:
            self.updater.download_progress = progress
        
        self._setup_settings_menu()
    
    def _show_changelog(self):
        """Değişiklikleri göster"""
        if self.update_status and self.update_status.get('changelog'):
            changelog = self.update_status['changelog']
            # İlk 500 karakter yeterli
            short_log = changelog[:500] + "..." if len(changelog) > 500 else changelog
            self.audio.speak(f"Değişiklikler: {short_log}", interrupt=True)
        else:
            self.audio.speak("Değişiklik notu bulunamadı.", interrupt=True)
    
    def _apply_volume_to_audio(self):
        """Ses ayarlarını audio manager'a uygula"""
        music_vol = self.settings.get('music_volume') / 100.0
        sfx_vol = self.settings.get('sfx_volume') / 100.0
        music_enabled = self.settings.get('music_enabled')
        sfx_enabled = self.settings.get('sfx_enabled')
        
        # Müzik
        if music_enabled:
            self.audio.music_volume = music_vol
            if hasattr(pygame.mixer, 'music'):
                pygame.mixer.music.set_volume(music_vol)
        else:
            if hasattr(pygame.mixer, 'music'):
                pygame.mixer.music.set_volume(0)
        
        # Efektler
        self.audio.sfx_volume = sfx_vol if sfx_enabled else 0
    
    def handle_event(self, event) -> bool:
        if self.settings_menu.handle_event(event):
            return True
        
        if self.back_button.handle_event(event):
            return True
        
        if event.type == pygame.KEYDOWN:
            # Backspace veya Escape - Geri
            if event.key in (pygame.K_BACKSPACE, pygame.K_ESCAPE):
                self._go_back()
                return True
            
            # F1 - Ayarları oku
            if event.key == pygame.K_F1:
                self._announce_settings()
                return True
            
            # Sol/Sağ ok - Değer değiştir
            if event.key == pygame.K_LEFT:
                self._adjust_selected(-10)
                return True
            if event.key == pygame.K_RIGHT:
                self._adjust_selected(10)
                return True
        
        return False
    
    def _adjust_selected(self, delta: int):
        """Seçili ayarı sol/sağ okla ayarla"""
        selected_idx = self.settings_menu.selected_index
        
        # Ses seviyeleri
        if selected_idx == 0:  # Müzik seviyesi
            self._adjust_volume('music_volume', delta)
        elif selected_idx == 2:  # Efekt seviyesi
            self._adjust_volume('sfx_volume', delta)
    
    def _adjust_volume(self, key: str, delta: int):
        """Ses seviyesini sol/sağ okla ayarla"""
        current = self.settings.get(key)
        new_value = max(0, min(100, current + delta))
        self.settings.set(key, new_value)
        
        # Sadece ilgili ses kanalını güncelle (müziği etkilemeden)
        if key == 'music_volume':
            music_enabled = self.settings.get('music_enabled')
            if music_enabled and hasattr(pygame.mixer, 'music'):
                pygame.mixer.music.set_volume(new_value / 100.0)
            self.audio.music_volume = new_value / 100.0
            self.music_manager.set_volume(new_value / 100.0)
        elif key == 'sfx_volume':
            sfx_enabled = self.settings.get('sfx_enabled')
            self.audio.sfx_volume = (new_value / 100.0) if sfx_enabled else 0
        
        name = t('music_volume') if 'music' in key else t('sfx_volume')
        self.audio.speak(f"{new_value}", interrupt=True)
        
        saved_index = self.settings_menu.selected_index
        self._setup_settings_menu()
        self.settings_menu.selected_index = min(saved_index, len(self.settings_menu.items) - 1)
        self._update_panels()
    
    def _announce_settings(self):
        """Tüm ayarları oku"""
        lang = self.settings.get('language')
        
        music = self.settings.get('music_volume')
        sfx = self.settings.get('sfx_volume')
        auto_save = "açık" if self.settings.get('auto_save_enabled') else "kapalı"
        interval = self.settings.get('auto_save_interval')
        
        if lang == 'en':
            auto_save = "on" if self.settings.get('auto_save_enabled') else "off"
            message = f"Music: {music}%, Effects: {sfx}%, Auto save: {auto_save}, every {interval} turns"
        else:
            message = f"Müzik: yüzde {music}, Efektler: yüzde {sfx}, Otomatik kayıt: {auto_save}, her {interval} turda"
        
        self.audio.speak(message, interrupt=True)
    
    def update(self, dt: float):
        pass
    
    def draw(self, surface: pygame.Surface):
        surface.fill(COLORS['background'])
        
        # Başlık
        font = self.get_header_font()
        title = font.render(t('settings_title'), True, COLORS['gold'])
        surface.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 20))
        
        # Paneller
        self.sound_panel.draw(surface)
        self.auto_save_panel.draw(surface)
        self.language_panel.draw(surface)
        
        # Menü
        self.settings_menu.draw(surface)
        
        # Geri butonu
        self.back_button.draw(surface)
        
        # Yardım metni
        small_font = get_font(FONTS['small'])
        help_text = "Sol/Sağ ok: Değer değiştir | Enter: Seçenekleri değiştir | F1: Oku"
        help_surface = small_font.render(help_text, True, COLORS['text'])
        surface.blit(help_surface, (20, SCREEN_HEIGHT - 100))
    
    def _go_back(self):
        self.screen_manager.change_screen(ScreenType.MAIN_MENU)
