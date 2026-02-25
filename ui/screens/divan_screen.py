# -*- coding: utf-8 -*-
"""
Osmanlı Eyalet Yönetim Simülasyonu - Eyalet Divanı Ekranı
NPC danışmanların raporlarını gösteren toplantı ekranı.
"""

import pygame
from ui.screen_manager import BaseScreen, ScreenType
from ui.components import Button, Panel, HierarchicalMenu
from ui.text_input import AccessibleTextInput
from config import COLORS, FONTS, SCREEN_WIDTH, SCREEN_HEIGHT, get_font
from game.systems.divan import (
    AdvisorRole, ReportSeverity, ROLE_DISPLAY_NAMES
)


class DivanScreen(BaseScreen):
    """Eyalet Divanı Toplantı Ekranı"""
    
    def __init__(self, screen_manager):
        super().__init__(screen_manager)
        
        # Paneller
        self.advisor_panel = Panel(20, 80, 380, 250, "Divan Üyeleri")
        self.summary_panel = Panel(420, 80, 400, 250, "Divan Özeti")
        
        # Hiyerarşik menü — raporlar
        self.report_menu = HierarchicalMenu(
            x=20,
            y=360,
            width=820,
            item_height=40
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
        
        # Danışman isim değiştirme modu
        self.renaming_advisor = None
        self.rename_input = AccessibleTextInput(
            x=20, y=SCREEN_HEIGHT - 120,
            width=400, height=40,
            placeholder="Yeni isim girin..."
        )
    
    def get_header_font(self):
        if self._header_font is None:
            self._header_font = get_font(FONTS['header'])
        return self._header_font
    
    def on_enter(self):
        gm = self.screen_manager.game_manager
        if gm and hasattr(gm, 'divan'):
            gm.divan.refresh_analysis(gm)
        self._update_panels()
        self._setup_report_menu()
    
    def announce_screen(self):
        self.audio.announce_screen_change("Eyalet Divanı")
        gm = self.screen_manager.game_manager
        if gm and hasattr(gm, 'divan'):
            gm.divan.announce_summary()
            unread = gm.divan.get_unread_count()
            if unread > 0:
                self.audio.speak(f"{unread} okunmamış rapor var.", interrupt=False)
    
    def _update_panels(self):
        """Panel içeriklerini güncelle"""
        gm = self.screen_manager.game_manager
        if not gm or not hasattr(gm, 'divan'):
            return
        
        divan = gm.divan
        
        # Danışman paneli — beceri ve sadakat bilgisiyle
        advisor_items = []
        for role, advisor in divan.advisors.items():
            display_name = ROLE_DISPLAY_NAMES[role]
            advisor_items.append((
                f"{display_name}: {advisor.name}",
                f"Beceri: {advisor.skill}/10, Sadakat: %{advisor.loyalty}"
            ))
        
        advisor_items.append(("", ""))
        advisor_items.append(("Son Analiz", f"Tur {divan.last_analysis_turn}" if divan.last_analysis_turn >= 0 else "Henüz yok"))
        
        self.advisor_panel.set_content(advisor_items)
        
        # Özet paneli
        summary_items = []
        counts = divan.get_report_count_by_severity()
        
        if counts['acil'] > 0:
            summary_items.append(("⚠ ACİL", f"{counts['acil']} rapor"))
        if counts['uyari'] > 0:
            summary_items.append(("⚡ UYARI", f"{counts['uyari']} rapor"))
        if counts['bilgi'] > 0:
            summary_items.append(("ℹ BİLGİ", f"{counts['bilgi']} rapor"))
        
        summary_items.append(("", ""))
        summary_items.append(("Toplam Rapor", str(counts['total'])))
        
        # Okunmamış
        unread = divan.get_unread_count()
        if unread > 0:
            summary_items.append(("📩 Okunmamış", f"{unread} rapor"))
        
        # Son 5 turdaki acil raporlar
        urgent = divan.get_urgent_reports()
        if urgent:
            summary_items.append(("", ""))
            summary_items.append(("Son Aciller", f"{len(urgent)} adet"))
        
        self.summary_panel.set_content(summary_items)
    
    def _setup_report_menu(self):
        """Rapor menüsünü danışmanlara göre ayarla"""
        self.report_menu.clear()
        gm = self.screen_manager.game_manager
        if not gm or not hasattr(gm, 'divan'):
            return
        
        divan = gm.divan
        
        # Her danışmanın raporlarını kategorize et
        for role in AdvisorRole:
            display_name = ROLE_DISPLAY_NAMES[role]
            advisor = divan.advisors[role]
            reports = divan.get_reports_by_role(role)
            
            report_items = []
            
            if not reports:
                report_items.append({
                    'text': 'Rapor yok — eyalette sorun görülmüyor.',
                    'callback': None,
                    'disabled': True
                })
            else:
                # En yeni raporları önce göster
                for report in reversed(reports):
                    severity_prefix = self._get_severity_prefix(report.severity)
                    read_marker = "" if report.read else "● "
                    report_items.append({
                        'text': f"{read_marker}{severity_prefix} {report.message}",
                        'callback': lambda r=report: self._read_report(r),
                    })
            
            # İsim değiştirme seçeneği her danışman için
            report_items.append({'text': '', 'is_separator': True})
            report_items.append({
                'text': f"✏ İsim Değiştir: {advisor.name}",
                'callback': lambda a=advisor: self._start_rename(a)
            })
            
            category_title = f"{display_name} — {advisor.name}"
            self.report_menu.add_category(category_title, report_items)
        
        # Tümünü Okundu İşaretle
        self.report_menu.add_action(
            "Tümünü Okundu İşaretle",
            self._mark_all_read
        )
    
    def _get_severity_prefix(self, severity: ReportSeverity) -> str:
        if severity == ReportSeverity.ACIL:
            return "[ACİL]"
        elif severity == ReportSeverity.UYARI:
            return "[UYARI]"
        else:
            return "[BİLGİ]"
    
    def _read_report(self, report):
        """Raporu sesli oku ve okundu olarak işaretle"""
        severity_text = {
            ReportSeverity.ACIL: "Acil rapor",
            ReportSeverity.UYARI: "Uyarı",
            ReportSeverity.BILGI: "Bilgi"
        }
        
        # Okundu olarak işaretle
        gm = self.screen_manager.game_manager
        if gm and hasattr(gm, 'divan'):
            gm.divan.mark_read(report)
        
        display_name = ROLE_DISPLAY_NAMES[report.role]
        header = f"{display_name} {report.advisor_name}, {severity_text[report.severity]}:"
        
        self.audio.speak(header, interrupt=True)
        self.audio.speak(report.message, interrupt=False)
        self.audio.speak(f"Öneri: {report.recommendation}", interrupt=False)
        
        # Paneli güncelle (okunmamış sayısı değişir)
        self._update_panels()
    
    def _mark_all_read(self):
        """Tüm raporları okundu olarak işaretle"""
        gm = self.screen_manager.game_manager
        if gm and hasattr(gm, 'divan'):
            gm.divan.mark_all_read()
            self.audio.speak("Tüm raporlar okundu olarak işaretlendi.", interrupt=True)
            self._update_panels()
            self._setup_report_menu()
    
    def _start_rename(self, advisor):
        """Danışman ismini değiştirme modunu başlat"""
        self.renaming_advisor = advisor
        self.rename_input.set_text(advisor.name)
        self.rename_input.focus()
        display_name = ROLE_DISPLAY_NAMES[advisor.role]
        self.audio.speak(
            f"{display_name} {advisor.name} için yeni isim girin. Enter ile onaylayın, Escape ile iptal edin.",
            interrupt=True
        )
    
    def _confirm_rename(self):
        """İsim değişikliğini onayla"""
        new_name = self.rename_input.get_text().strip()
        if not new_name:
            self.audio.speak("Lütfen bir isim girin.", interrupt=True)
            return
        
        display_name = ROLE_DISPLAY_NAMES[self.renaming_advisor.role]
        old_name = self.renaming_advisor.name
        self.renaming_advisor.name = new_name
        self.renaming_advisor = None
        self.rename_input.unfocus()
        
        self.audio.speak(f"{display_name} ismi değiştirildi: {old_name} → {new_name}", interrupt=True)
        self._setup_report_menu()
        self._update_panels()
    
    def _cancel_rename(self):
        """İsim değişikliğini iptal et"""
        self.renaming_advisor = None
        self.rename_input.unfocus()
        self.audio.speak("İsim değişikliği iptal edildi.", interrupt=True)
    
    def _go_back(self):
        self.screen_manager.change_screen(ScreenType.PROVINCE_VIEW)
    
    def handle_event(self, event):
        # İsim değiştirme modu aktifse
        if self.renaming_advisor:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    self._confirm_rename()
                    return True
                elif event.key == pygame.K_ESCAPE:
                    self._cancel_rename()
                    return True
            self.rename_input.handle_event(event)
            return True
        
        # Menü navigasyonu — tüm event tiplerini ilet (keyboard + mouse)
        result = self.report_menu.handle_event(event)
        if result is False:
            self._go_back()
            return True
        if result is True:
            return True
        
        # Ek kısayollar
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_BACKSPACE or event.key == pygame.K_ESCAPE:
                self._go_back()
                return True
            
            # F1 — Divan özeti tekrar duyur
            if event.key == pygame.K_F1:
                gm = self.screen_manager.game_manager
                if gm and hasattr(gm, 'divan'):
                    gm.divan.announce_summary()
                return True
        
        return False
    
    def update(self, dt: float):
        pass
    
    def draw(self, surface: pygame.Surface):
        # Başlık
        header_font = self.get_header_font()
        title = header_font.render("EYALET DİVANI", True, COLORS['gold'])
        surface.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 20))
        
        # Paneller
        self.advisor_panel.draw(surface)
        self.summary_panel.draw(surface)
        
        # Menü
        self.report_menu.draw(surface)
        
        # Geri butonu
        self.back_button.draw(surface)
        
        # Rename modu aktifse input göster
        if self.renaming_advisor:
            self.rename_input.draw(surface)
