# -*- coding: utf-8 -*-
"""
Osmanlı Eyalet Yönetim Simülasyonu - Müzakere Ekranı
Diplomatik eylemler için pazarlık arayüzü
"""

import pygame
from ui.screen_manager import BaseScreen, ScreenType
from ui.components import Button, Panel, MenuList
from config import COLORS, FONTS, SCREEN_WIDTH, SCREEN_HEIGHT, get_font
from enum import Enum


class NegotiationType(Enum):
    """Müzakere türleri"""
    MARRIAGE = "marriage"
    TRIBUTE = "tribute"
    VASSAL = "vassal"
    TRADE = "trade"
    ALLIANCE = "alliance"


class NegotiationScreen(BaseScreen):
    """Diplomatik müzakere ekranı"""
    
    # Müzakere parametreleri (varsayılan değerler)
    NEGOTIATION_DEFAULTS = {
        NegotiationType.MARRIAGE: {
            'dowry': {'min': 5000, 'max': 50000, 'default': 10000, 'step': 1000, 'label': 'Çeyiz'},
            'yearly_gift': {'min': 0, 'max': 2000, 'default': 0, 'step': 100, 'label': 'Yıllık Hediye'},
            'trade_agreement': {'min': 0, 'max': 1, 'default': 0, 'step': 1, 'label': 'Ticaret Anlaşması'},
            'use_event_chain': {'min': 0, 'max': 1, 'default': 1, 'step': 1, 'label': 'Olay Zinciri (Detaylı)'},
        },
        NegotiationType.TRIBUTE: {
            'demand_amount': {'min': 500, 'max': 5000, 'default': 1000, 'step': 250, 'label': 'Talep Miktarı'},
            'threat_level': {'min': 1, 'max': 3, 'default': 1, 'step': 1, 'label': 'Tehdit Seviyesi'},
        },
        NegotiationType.VASSAL: {
            'autonomy': {'min': 0, 'max': 100, 'default': 50, 'step': 10, 'label': 'Özerklik (%)'},
            'tribute_rate': {'min': 50, 'max': 500, 'default': 200, 'step': 50, 'label': 'Yıllık Haraç'},
            'military_support': {'min': 0, 'max': 1, 'default': 1, 'step': 1, 'label': 'Askeri Destek'},
            'use_event_chain': {'min': 0, 'max': 1, 'default': 1, 'step': 1, 'label': 'Olay Zinciri (Detaylı)'},
        },
        NegotiationType.TRADE: {
            'trade_value': {'min': 100, 'max': 1000, 'default': 300, 'step': 50, 'label': 'Ticaret Değeri'},
            'duration': {'min': 4, 'max': 20, 'default': 12, 'step': 4, 'label': 'Süre (Tur)'},
        },
    }
    
    def __init__(self, screen_manager):
        super().__init__(screen_manager)
        
        # Müzakere durumu
        self.negotiation_type = None
        self.target = None
        self.offer_values = {}
        self.current_field_index = 0
        self.fields = []
        
        # Paneller
        self.offer_panel = Panel(50, 100, 500, 350, "Teklifiniz")
        self.demands_panel = Panel(600, 100, 500, 200, "Karşı Tarafın Beklentileri")
        self.result_panel = Panel(600, 320, 500, 130, "Tahmin")
        
        # Butonlar
        self.send_button = Button(
            x=200, y=SCREEN_HEIGHT - 80,
            width=200, height=50,
            text="Teklifi Gönder (Enter)",
            shortcut="return",
            callback=self._send_offer
        )
        
        self.cancel_button = Button(
            x=450, y=SCREEN_HEIGHT - 80,
            width=150, height=50,
            text="İptal (Esc)",
            shortcut="escape",
            callback=self._cancel
        )
        
        self._header_font = None
    
    def get_header_font(self):
        if self._header_font is None:
            self._header_font = get_font(FONTS['header'])
        return self._header_font
    
    def setup_negotiation(self, negotiation_type: NegotiationType, target: str):
        """Müzakere kur"""
        self.negotiation_type = negotiation_type
        self.target = target
        self.current_field_index = 0
        
        # Varsayılan değerleri yükle
        defaults = self.NEGOTIATION_DEFAULTS.get(negotiation_type, {})
        self.offer_values = {}
        self.fields = []
        
        for field_name, config in defaults.items():
            self.offer_values[field_name] = config['default']
            self.fields.append({
                'name': field_name,
                'label': config['label'],
                'min': config['min'],
                'max': config['max'],
                'step': config['step'],
                'is_boolean': config['max'] == 1 and config['min'] == 0
            })
    
    def on_enter(self):
        self._update_panels()
        self._announce_current_field()
    
    def announce_screen(self):
        type_names = {
            NegotiationType.MARRIAGE: "Evlilik Müzakeresi",
            NegotiationType.TRIBUTE: "Haraç Talebi",
            NegotiationType.VASSAL: "Vassallaştırma Müzakeresi",
            NegotiationType.TRADE: "Ticaret Anlaşması",
        }
        type_name = type_names.get(self.negotiation_type, "Müzakere")
        self.audio.announce_screen_change(f"{type_name} - {self.target}")
        self.audio.speak("Yukarı aşağı okla değer değiştirin. Tab ile sonraki alana geçin.", interrupt=False)
    
    def _update_panels(self):
        """Panelleri güncelle"""
        # Teklif paneli
        self.offer_panel.clear()
        for i, field in enumerate(self.fields):
            value = self.offer_values[field['name']]
            
            # Boolean değer için özel gösterim
            if field['is_boolean']:
                display_value = "Evet" if value else "Hayır"
            else:
                display_value = str(value)
            
            # Seçili alan işareti
            prefix = "> " if i == self.current_field_index else "  "
            self.offer_panel.add_item(f"{prefix}{field['label']}", display_value)
        
        # Karşı tarafın beklentileri
        self.demands_panel.clear()
        demands = self._get_target_demands()
        for demand, value in demands.items():
            self.demands_panel.add_item(demand, value)
        
        # Sonuç tahmini
        self.result_panel.clear()
        acceptance = self._calculate_acceptance_chance()
        self.result_panel.add_item("Kabul Şansı", f"%{acceptance}")
        
        # Renk kodu
        if acceptance >= 70:
            status = "Muhtemelen kabul edecek"
        elif acceptance >= 40:
            status = "Şüpheli, pazarlık gerekebilir"
        else:
            status = "Büyük ihtimalle reddedecek"
        self.result_panel.add_item("Değerlendirme", status)
    
    def _get_target_demands(self) -> dict:
        """Hedefin beklentilerini hesapla"""
        gm = self.screen_manager.game_manager
        if not gm or self.target not in gm.diplomacy.neighbors:
            return {}
        
        neighbor = gm.diplomacy.neighbors[self.target]
        relation = neighbor.value
        
        demands = {}
        
        # Kişilik bilgisi
        demands["Kişilik"] = neighbor.get_personality_description()
        demands[""] = ""  # Ayırıcı
        
        if self.negotiation_type == NegotiationType.MARRIAGE:
            # İlişki kötüyse daha yüksek çeyiz ister
            min_dowry = 8000 - (relation * 50)
            demands["Minimum Çeyiz"] = f"{max(5000, min_dowry)} altın"
            if relation < 20:
                demands["Ticaret Anlaşması"] = "İsteniyor"
            
            # Kişilik etkisi
            personality_mod = neighbor.get_personality_modifier('marriage')
            if personality_mod > 0:
                demands["Kişilik Etkisi"] = f"+{personality_mod}% (olumlu)"
            elif personality_mod < 0:
                demands["Kişilik Etkisi"] = f"{personality_mod}% (olumsuz)"
        
        elif self.negotiation_type == NegotiationType.TRIBUTE:
            # Güçlü komşu daha zor boyun eğer
            if relation > 30:
                demands["Uyarı"] = "İyi ilişkiler bozulabilir"
            demands["Minimum Güç"] = "500 askeri güç"
            
            # Kişilik etkisi
            personality_mod = neighbor.get_personality_modifier('tribute')
            if personality_mod > 0:
                demands["Kişilik Etkisi"] = f"+{personality_mod}% (boyun eğer)"
            elif personality_mod < 0:
                demands["Kişilik Etkisi"] = f"{personality_mod}% (direnç)"
        
        elif self.negotiation_type == NegotiationType.VASSAL:
            demands["Minimum Özerklik"] = "40%"
            if relation < 0:
                demands["Risk"] = "Düşmanlık çok yüksek"
            
            # Kişilik etkisi
            personality_mod = neighbor.get_personality_modifier('vassal')
            if personality_mod > 0:
                demands["Kişilik Etkisi"] = f"+{personality_mod}% (kabul eğilimi)"
            elif personality_mod < 0:
                demands["Kişilik Etkisi"] = f"{personality_mod}% (reddedecek)"
        
        return demands
    
    def _calculate_acceptance_chance(self) -> int:
        """Kabul şansını hesapla"""
        gm = self.screen_manager.game_manager
        if not gm or self.target not in gm.diplomacy.neighbors:
            return 0
        
        neighbor = gm.diplomacy.neighbors[self.target]
        relation = neighbor.value
        military_power = gm.military.get_total_power()
        
        base_chance = 30
        
        if self.negotiation_type == NegotiationType.MARRIAGE:
            dowry = self.offer_values.get('dowry', 10000)
            yearly = self.offer_values.get('yearly_gift', 0)
            trade = self.offer_values.get('trade_agreement', 0)
            
            # Çeyiz etkisi
            base_chance += (dowry - 5000) // 500
            base_chance += yearly // 50
            base_chance += trade * 15
            base_chance += relation // 2
            
            # Kişilik modifiyeri
            base_chance += neighbor.get_personality_modifier('marriage')
            
            # Kadın karakter evlilik bonusu (+%25)
            if gm.player:
                marriage_bonus = gm.player.get_bonus('marriage_alliance')
                base_chance += int(marriage_bonus * 100)
        
        elif self.negotiation_type == NegotiationType.TRIBUTE:
            demand = self.offer_values.get('demand_amount', 1000)
            threat = self.offer_values.get('threat_level', 1)
            
            # Güç etkisi
            base_chance += min(30, (military_power - 500) // 50)
            base_chance += threat * 10
            base_chance -= demand // 100
            base_chance -= relation // 3
            
            # Kişilik modifiyeri
            base_chance += neighbor.get_personality_modifier('tribute')
        
        elif self.negotiation_type == NegotiationType.VASSAL:
            autonomy = self.offer_values.get('autonomy', 50)
            tribute = self.offer_values.get('tribute_rate', 200)
            
            # Özerklik etkisi
            base_chance += autonomy // 5
            base_chance -= tribute // 50
            base_chance += min(30, (military_power - 1000) // 100)
            base_chance += relation // 4
            
            # Kişilik modifiyeri
            base_chance += neighbor.get_personality_modifier('vassal')
        
        return max(5, min(95, base_chance))
    
    def handle_event(self, event) -> bool:
        if self.send_button.handle_event(event):
            return True
        if self.cancel_button.handle_event(event):
            return True
        
        if event.type == pygame.KEYDOWN:
            # Escape - İptal
            if event.key == pygame.K_ESCAPE:
                self._cancel()
                return True
            
            # Enter - Gönder
            if event.key == pygame.K_RETURN:
                self._send_offer()
                return True
            
            # Tab veya Aşağı - Sonraki alan
            if event.key in (pygame.K_TAB, pygame.K_DOWN):
                self.current_field_index = (self.current_field_index + 1) % len(self.fields)
                self._announce_current_field()
                self._update_panels()
                return True
            
            # Shift+Tab veya Yukarı - Önceki alan
            if event.key == pygame.K_UP:
                self.current_field_index = (self.current_field_index - 1) % len(self.fields)
                self._announce_current_field()
                self._update_panels()
                return True
            
            # Sağ veya + - Değer artır
            if event.key in (pygame.K_RIGHT, pygame.K_PLUS, pygame.K_KP_PLUS):
                self._adjust_current_value(1)
                return True
            
            # Sol veya - - Değer azalt
            if event.key in (pygame.K_LEFT, pygame.K_MINUS, pygame.K_KP_MINUS):
                self._adjust_current_value(-1)
                return True
            
            # Space - Boolean değiştir
            if event.key == pygame.K_SPACE:
                field = self.fields[self.current_field_index]
                if field['is_boolean']:
                    self._adjust_current_value(1)
                return True
            
            # F1 - Teklif özeti
            if event.key == pygame.K_F1:
                self._announce_offer_summary()
                return True
        
        return False
    
    def _adjust_current_value(self, direction: int):
        """Mevcut değeri ayarla"""
        if not self.fields:
            return
        
        field = self.fields[self.current_field_index]
        name = field['name']
        current = self.offer_values[name]
        step = field['step']
        
        new_value = current + (step * direction)
        new_value = max(field['min'], min(field['max'], new_value))
        
        self.offer_values[name] = new_value
        
        # Değişikliği duyur
        if field['is_boolean']:
            display = "Evet" if new_value else "Hayır"
        else:
            display = str(new_value)
        
        self.audio.speak(f"{field['label']}: {display}", interrupt=True)
        
        # Kabul şansını da duyur
        acceptance = self._calculate_acceptance_chance()
        self.audio.speak(f"Kabul şansı: yüzde {acceptance}", interrupt=False)
        
        self._update_panels()
    
    def _announce_current_field(self):
        """Mevcut alanı duyur"""
        if not self.fields:
            return
        
        field = self.fields[self.current_field_index]
        value = self.offer_values[field['name']]
        
        if field['is_boolean']:
            display = "Evet" if value else "Hayır"
        else:
            display = str(value)
        
        self.audio.speak(
            f"{field['label']}: {display}. "
            f"Minimum {field['min']}, maksimum {field['max']}. "
            f"Sol sağ okla değiştirin.",
            interrupt=True
        )
    
    def _announce_offer_summary(self):
        """Teklif özetini duyur"""
        self.audio.speak(f"{self.target} için teklif özeti:", interrupt=True)
        
        for field in self.fields:
            value = self.offer_values[field['name']]
            if field['is_boolean']:
                display = "Evet" if value else "Hayır"
            else:
                display = str(value)
            self.audio.speak(f"{field['label']}: {display}", interrupt=False)
        
        acceptance = self._calculate_acceptance_chance()
        self.audio.speak(f"Toplam kabul şansı: yüzde {acceptance}", interrupt=False)
    
    def _send_offer(self):
        """Teklifi gönder"""
        gm = self.screen_manager.game_manager
        if not gm:
            return
        
        acceptance = self._calculate_acceptance_chance()
        
        # Prestij modifiyeri (yüksek prestij diplomatik başarıyı artırır)
        prestige_bonus = gm.diplomacy.get_prestige_modifier()
        acceptance = min(95, max(5, acceptance + prestige_bonus))
        
        # Olay zinciri modu mu?
        use_chain = self.offer_values.get('use_event_chain', 0)
        
        # Rastgele sonuç
        import random
        success = random.randint(1, 100) <= acceptance
        
        # ========================
        # EVLİLİK
        # ========================
        if self.negotiation_type == NegotiationType.MARRIAGE:
            dowry = self.offer_values.get('dowry', 10000)
            if not gm.economy.can_afford(gold=dowry):
                self.audio.speak(f"Yetersiz altın. {dowry} altın gerekli.", interrupt=True)
                return
            
            gm.economy.spend(gold=dowry)
            
            if use_chain:
                # Olay zinciri başlat
                gm.diplomacy.start_event_chain('marriage', self.target, {
                    'dowry': dowry,
                    'yearly_gift': self.offer_values.get('yearly_gift', 0),
                    'trade_agreement': self.offer_values.get('trade_agreement', 0)
                })
                self.audio.announce(f"{self.target}'e evlilik elcisi gonderildi! Cevap bekleniyor...")
                gm.diplomacy.add_prestige(10, f"{self.target}'e evlilik teklifi")
            else:
                # Anında sonuç
                if success:
                    gm.diplomacy.marriage_alliances.append({
                        'partner': self.target,
                        'turns_active': 0,
                        'relation_bonus': 20,
                        'yearly_gift': self.offer_values.get('yearly_gift', 0)
                    })
                    gm.diplomacy.neighbors[self.target].value += 30
                    gm.diplomacy.neighbors[self.target].update_type()
                    gm.diplomacy.add_prestige(50, f"{self.target} ile evlilik")
                    self.audio.announce(f"Tebrikler! {self.target} ile evlilik ittifakı kuruldu!")
                else:
                    gm.diplomacy.add_prestige(-10, "Evlilik teklifi reddedildi")
                    self.audio.announce(f"{self.target} teklifinizi reddetti.")
        
        # ========================
        # HARAÇ
        # ========================
        elif self.negotiation_type == NegotiationType.TRIBUTE:
            demand = self.offer_values.get('demand_amount', 1000)
            
            if success:
                gm.economy.resources.gold += demand
                gm.diplomacy.neighbors[self.target].value -= 20
                gm.diplomacy.neighbors[self.target].update_type()
                gm.diplomacy.add_prestige(30, f"{self.target}'den haraç alındı")
                # Momentum: Düşmanlık yavaşça artacak
                gm.diplomacy.add_relationship_momentum(self.target, -10, 5, "Haraç tepkisi")
                self.audio.announce(f"{self.target} {demand} altın haraç ödedi!")
            else:
                gm.diplomacy.neighbors[self.target].value -= 30
                gm.diplomacy.neighbors[self.target].update_type()
                gm.diplomacy.add_prestige(-15, "Haraç talebi reddedildi")
                self.audio.announce(f"{self.target} haracı reddetti ve düşmanlık arttı!")
        
        # ========================
        # VASSAL
        # ========================
        elif self.negotiation_type == NegotiationType.VASSAL:
            if use_chain:
                # Olay zinciri başlat
                gm.diplomacy.start_event_chain('vassal', self.target, {
                    'tribute': self.offer_values.get('tribute_rate', 200),
                    'autonomy': self.offer_values.get('autonomy', 50),
                    'military_power': gm.military.get_total_power()
                })
                self.audio.announce(f"{self.target}'e vassallasma ultimatomu gonderildi!")
                gm.diplomacy.add_prestige(20, f"{self.target}'e ultimatom")
            else:
                # Anında sonuç
                if success:
                    tribute = self.offer_values.get('tribute_rate', 200)
                    autonomy = self.offer_values.get('autonomy', 50)
                    gm.diplomacy.vassals.append({
                        'name': self.target,
                        'tribute': tribute,
                        'loyalty': 50 + autonomy // 5,
                        'autonomy': autonomy,
                        'military_support': self.offer_values.get('military_support', 1) * 100
                    })
                    gm.diplomacy.neighbors[self.target].value = 50
                    gm.diplomacy.neighbors[self.target].update_type()
                    gm.diplomacy.add_prestige(100, f"{self.target} vassallaştırıldı")
                    self.audio.announce(f"{self.target} artık vassalınız! Yıllık {tribute} altın haraç.")
                else:
                    gm.diplomacy.neighbors[self.target].value -= 40
                    gm.diplomacy.neighbors[self.target].update_type()
                    gm.diplomacy.add_prestige(-25, "Vassallaştırma başarısız")
                    self.audio.announce(f"{self.target} vassalığı reddetti ve düşman oldu!")
        
        # Diplomasi ekranına dön
        self.screen_manager.change_screen(ScreenType.DIPLOMACY)
    
    def _cancel(self):
        """Müzakereyi iptal et"""
        self.audio.speak("Müzakere iptal edildi.", interrupt=True)
        self.screen_manager.change_screen(ScreenType.DIPLOMACY)
    
    def update(self, dt: float):
        pass
    
    def draw(self, surface: pygame.Surface):
        # Başlık
        header_font = self.get_header_font()
        
        type_names = {
            NegotiationType.MARRIAGE: "Evlilik Müzakeresi",
            NegotiationType.TRIBUTE: "Haraç Talebi",
            NegotiationType.VASSAL: "Vassallaştırma",
            NegotiationType.TRADE: "Ticaret Anlaşması",
        }
        title_text = f"{type_names.get(self.negotiation_type, 'Müzakere')} - {self.target}"
        title = header_font.render(title_text, True, COLORS['gold'])
        surface.blit(title, (50, 30))
        
        # Alt başlık
        small_font = get_font(FONTS['small'])
        help_text = small_font.render(
            "Tab: Sonraki alan | Sol/Sağ: Değer değiştir | F1: Özet | Enter: Gönder | Esc: İptal",
            True, COLORS['text_dim']
        )
        surface.blit(help_text, (50, 65))
        
        # Paneller
        self.offer_panel.draw(surface)
        self.demands_panel.draw(surface)
        self.result_panel.draw(surface)
        
        # Kabul şansı göstergesi
        self._draw_acceptance_bar(surface)
        
        # Butonlar
        self.send_button.draw(surface)
        self.cancel_button.draw(surface)
    
    def _draw_acceptance_bar(self, surface: pygame.Surface):
        """Kabul şansı çubuğu"""
        acceptance = self._calculate_acceptance_chance()
        
        rect = pygame.Rect(600, 470, 500, 40)
        pygame.draw.rect(surface, COLORS['panel_bg'], rect, border_radius=10)
        pygame.draw.rect(surface, COLORS['panel_border'], rect, width=2, border_radius=10)
        
        # Progress bar
        bar_width = int((rect.width - 20) * (acceptance / 100))
        
        # Renk
        if acceptance >= 70:
            color = COLORS['success']
        elif acceptance >= 40:
            color = COLORS['warning']
        else:
            color = COLORS['danger']
        
        bar_rect = pygame.Rect(rect.x + 10, rect.y + 25, bar_width, 10)
        pygame.draw.rect(surface, color, bar_rect, border_radius=5)
        
        # Label
        font = get_font(FONTS['small'])
        label = font.render(f"Kabul Şansı: %{acceptance}", True, COLORS['text'])
        surface.blit(label, (rect.x + 10, rect.y + 5))
