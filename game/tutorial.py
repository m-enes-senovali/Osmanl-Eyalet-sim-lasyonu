# -*- coding: utf-8 -*-
"""
Osmanlı Eyalet Yönetim Simülasyonu - Rehber Sistemi
Hikayeci bir Kethüda (vezir yardımcısı) karakteri ile öğretici.
"""

from audio.audio_manager import get_audio_manager


class Tutorial:
    """Oyun rehber sistemi - Kethüda (danışman) anlatımıyla"""
    
    def __init__(self):
        self.audio = get_audio_manager()
        self.current_step = 0
        self.completed_tutorials = set()
        self.enabled = True
        
        # Kethüda karakteri
        self.narrator = "Kethüda"
    
    def speak(self, text: str, interrupt: bool = True):
        """Kethüda olarak konuş"""
        self.audio.speak(text, interrupt=interrupt)
    
    # === AÇILIŞ REHBERİ ===
    
    def welcome_message(self):
        """İlk açılış hoş geldin mesajı"""
        if 'welcome' in self.completed_tutorials:
            return
        
        self.speak("Hoş geldiniz, Beyim! Ben Kethüdanız.", True)
        self.speak("Size bu eyaletin yönetiminde rehberlik edeceğim.", False)
        self.speak("Dinlemeye hazır olduğunuzda, H tuşuna basarak yardım alabilirsiniz.", False)
        self.speak("Şimdi size kısaca durumu özetleyeyim.", False)
        
        self.completed_tutorials.add('welcome')
    
    def first_turn_guide(self):
        """İlk tur rehberi"""
        if 'first_turn' in self.completed_tutorials:
            return
        
        self.speak("Beyim, ilk turunuza başlıyorsunuz.", True)
        self.speak("Her tur, ekonominiz, ordunuz ve halkınız güncellenir.", False)
        self.speak("Hedefimiz: Hazineyi dolu tutmak, halkı memnun etmek ve Padişahımızın güvenini kazanmak.", False)
        self.speak("İlk olarak R tuşuna basarak kaynaklarınızı kontrol edin.", False)
        
        self.completed_tutorials.add('first_turn')
    
    # === DURUM REHBERLERİ ===
    
    def economy_guide(self):
        """Ekonomi rehberi"""
        self.speak("Ekonomi Rehberi:", True)
        self.speak("Geliriniz vergilerden ve ticaretten gelir.", False)
        self.speak("Giderleriniz asker bakımı ve bina bakımıdır.", False)
        self.speak("Tavsiyem: Vergiyi yüzde 15-20'de tutun. Yüksek vergi halkı kızdırır!", False)
        self.speak("Çarşı ve Kervansaray inşa ederek ticaret gelirini artırabilirsiniz.", False)
    
    def military_guide(self):
        """Askeri rehber"""
        self.speak("Askeri Rehber:", True)
        self.speak("Sipahi süvariler güçlüdür ama pahalıdır.", False)
        self.speak("Azaplar ucuz ve hızlı eğitilir, başlangıç için idealdir.", False)
        self.speak("Yeniçeriler elit askerlerdir, çok etkilidir ama masraflıdır.", False)
        self.speak("Tavsiyem: Başlangıçta 50 Azap toplayın. Güvenlik için yeterlidir.", False)
    
    def construction_guide(self):
        """İnşaat rehberi"""
        self.speak("İnşaat Rehberi:", True)
        self.speak("Önce Çiftlik inşa edin. Yiyecek üretimi kritiktir!", False)
        self.speak("Sonra Çarşı yaparak ticaret gelirinizi artırın.", False)
        self.speak("Cami halkın mutluluğunu artırır.", False)
        self.speak("Kışla asker eğitimini hızlandırır.", False)
        self.speak("Tavsiyem: Çiftlik, Çarşı, Cami sıralamasıyla başlayın.", False)
    
    def diplomacy_guide(self):
        """Diplomasi rehberi"""
        self.speak("Diplomasi Rehberi:", True)
        self.speak("Padişah sadakati yüzde 30'un altına düşerse idam edilirsiniz!", False)
        self.speak("Her birkaç turda Padişaha haraç gönderin.", False)
        self.speak("Komşu beyliklerle iyi ilişkiler ticaret bonusu sağlar.", False)
        self.speak("Tavsiyem: Sadakat yüzde 50'nin altına düşmeden 500 altın gönderin.", False)
    
    def population_guide(self):
        """Halk rehberi"""
        self.speak("Halk Rehberi:", True)
        self.speak("Memnuniyet yüzde 20'nin altına düşerse isyan çıkar!", False)
        self.speak("İsyanı bastırmak için güçlü bir ordu gerekir.", False)
        self.speak("Cami ve Hamam inşa ederek mutluluğu artırın.", False)
        self.speak("Tavsiyem: Vergiyi düşük tutun ve yiyecek stoğunu koruyun.", False)
    
    # === UYARI REHBERLERİ ===
    
    def low_gold_warning(self, gold: int):
        """Düşük altın uyarısı"""
        self.speak(f"Beyim, hazinemiz tehlikede! Sadece {gold} altınımız kaldı.", True)
        self.speak("Vergiyi artırabilirsiniz ama dikkatli olun, halk kızar.", False)
        self.speak("Ya da asker sayısını azaltarak bakım masraflarını düşürün.", False)
    
    def low_loyalty_warning(self, loyalty: int):
        """Düşük sadakat uyarısı"""
        self.speak(f"Acil durum! Padişah sadakati yüzde {loyalty}!", True)
        self.speak("Derhal Padişaha haraç gönderin, yoksa kelleniz gider!", False)
        self.speak("D tuşuna basarak Diplomasi ekranına gidin.", False)
    
    def revolt_warning(self):
        """İsyan uyarısı"""
        self.speak("Felaket! Halk isyan halinde!", True)
        self.speak("Ordunuzu güçlendirin ve isyanı bastırın.", False)
        self.speak("Vergiyi derhal düşürün ve Cami inşa edin.", False)
    
    def low_food_warning(self, food: int):
        """Düşük yiyecek uyarısı"""
        self.speak(f"Uyarı! Zahire stoğu sadece {food}.", True)
        self.speak("Halk aç kalırsa memnuniyet düşer ve isyan çıkar.", False)
        self.speak("Çiftlik inşa edin veya yiyecek satın alın.", False)
    
    # === İPUCU SİSTEMİ ===
    
    def get_contextual_tip(self, game_manager):
        """Oyun durumuna göre ipucu ver"""
        gm = game_manager
        
        # Öncelik sırasına göre kontrol
        
        # 1. Kritik: Sadakat
        if gm.diplomacy.sultan_loyalty < 30:
            self.low_loyalty_warning(gm.diplomacy.sultan_loyalty)
            return
        
        # 2. Kritik: İsyan
        if gm.population.active_revolt:
            self.revolt_warning()
            return
        
        # 3. Kritik: Altın
        if gm.economy.resources.gold < 50:
            self.low_gold_warning(gm.economy.resources.gold)
            return
        
        # 4. Uyarı: Yiyecek
        if gm.economy.resources.food < 30:
            self.low_food_warning(gm.economy.resources.food)
            return
        
        # 5. Uyarı: Memnuniyet
        if gm.population.happiness < 40:
            self.speak("Tavsiye: Halk memnuniyeti düşük. Vergiyi azaltmayı deneyin.", True)
            return
        
        # 6. Genel ipucu
        tips = [
            "Her şey yolunda görünüyor Beyim. Turları geçirerek ilerlemeye devam edin.",
            "Düzenli olarak Padişaha haraç göndermeyi unutmayın.",
            "Çiftlik ve Çarşı, ekonominin temelini oluşturur.",
            "Orta seviye bir ordu, eşkıyalara karşı koruma sağlar.",
        ]
        
        import random
        self.speak(random.choice(tips), True)
    
    # === KISA KOMUT ===
    
    def show_quick_help(self):
        """Hızlı yardım menüsü"""
        self.speak("Klavye Kısayolları:", True)
        self.speak("R: Kaynaklar, S: Durum, I: Gelir, W: Uyarılar", False)
        self.speak("E: Ekonomi, M: Askeri, C: İnşaat, D: Diplomasi, P: Halk", False)
        self.speak("Space: Tur bitir, F5: Kaydet, H: Bu yardım", False)
        self.speak("Tab: Paneller arası, Backspace: Geri", False)


# Singleton
_tutorial = None

def get_tutorial() -> Tutorial:
    global _tutorial
    if _tutorial is None:
        _tutorial = Tutorial()
    return _tutorial
