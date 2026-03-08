# AGENT KODLAMA REHBERİ (AGENTS.md)

Bu dosya, Osmanlı Eyalet Simülasyonu kod tabanında çalışan yapay zeka ajanları için kesin görev ve mimari kısıtlamalarını içerir. Linter/formatter kuralları kasıtlı olarak hariç tutulmuştur.

## 1. Erişilebilirlik ve Girdi (Kritik İş Etiketi)
Oyun görme engelli oyuncular için tasarlanmıştır. Görsel arayüz (UI) ikincildir.
- **Klavye Önceliği:** Tüm ekranlar SADECE klavye ile (Yön tuşları, Enter, Esc, Tab, kısayol harfleri) tam oynanabilir olmalıdır. Yeni bir buton/ekran eklendiğinde kısayol tuşu atanması zorunludur.
- **Sesli Geri Bildirim (Audio Manager):** Ekranda değişen her veri (tur geçişi, savaş sonucu, hata mesajı) `self.audio.speak()` veya `self.audio.announce()` ile duyurulmalıdır. Sessiz UI değişiklikleri **kesinlikle yasaktır**.
- **Panel Okuma:** Tab tuşu gibi erişilebilir istatistik özetleri, bilgileri ekranda göstermenin ötesinde *okunabilir* formatta sunmalıdır.

## 2. Render ve Performans Döngüsü (60 FPS Kısıtlamaları)
Pygame döngüsü saniyede 60 kez çalışır. Aşağıdaki işlemler `update(dt)` veya `draw(surface)` içinde **kesinlikle yasaktır**:
- `pygame.Surface` tahsisi (malloc işlemi yaratır, `__init__`'te oluşturup tekrar kullanın).
- `get_font()` çağrıları veya font render işlemleri önbelleksiz yapılmamalıdır (`__init__`'te hazırlayın).
- Veri listesi oluşturma, format string (`f"{var}"`) veya string birleştirme işlemleri. Bunları sadece veri değiştiğinde (örn. `_on_next_turn` veya `on_enter` tetikleyicilerinde) güncelleyin.
- Metot içi `import` kullanımı modül önbelleğine rağmen cycle yakar, dosya başına taşıyın.

## 3. Ekran (Screen) Mimarisi 
- **Lazy Instantiation:** `main.py` içinde ekranlar doğrudan (eager) oluşturulamaz. Bellek şişmesini önlemek için `register_screen_factory(ScreenType.X, lambda sm: XScreen(sm))` modelini kullanın.
- **Ekran Yönlendirmesi:** Ekranlar arası geçiş doğrudan nesne üzerinden değil, `self.screen_manager.change_screen(ScreenType.X)` kullanılarak Enum üzerinden yapılmalıdır.
- **UI Elementleri (Bileşenler):** Standart `UI/components.py` sınıflarını (`Button`, `Panel`, `MenuList`) kullanın. Kendi özel draw/event handler rutinlerinizi sadece bu bileşenler yetersiz kaldığında yazın.

## 4. Oyun Döngüsü ve State Yönetimi (Game Manager)
- **Anti-Pattern Yasakları:** `process_turn()` veya diğer logic bloklarında `if 'var' in locals():` gibi yansıma (reflection) kontrolleri kullanmak yasaktır. Değişkenleri açıkça `[]` veya `None` olarak ilklendirin.
- **Sessiz Hatalar:** `try ... except Exception: pass` kalıbı ile logic yönetmek (özellikle bool kontrolleri için) yasaktır. Binanın/objenin varlığını `has_building()` gibi metotlarla açıkça kontrol edin.
- **Sabitler:** Aylar, isimler, matrisler gibi değişmeyen listeleri/sözlükleri fonksiyon içinde tanımlamayın; modül seviyesinde büyük harfle (örn. `MONTH_NAMES`) tanımlayın.

## 5. Değişiklik Güvenliği
- Oyun **Save/Load** mantığına bağımlıdır. Modele/Sınıfa yeni bir özellik (attribute) eklediğinizde, `game/save_migration.py` dosyasında geriye dönük uyumluluk dönüşümünü mutlaka sağlayın. Yeni özellik eski save dosyalarında `AttributeError` fırlatmamalıdır (`getattr(obj, 'new_prop', default_val)` kullanın).
- `construction.py` ve `events.py` devasa veri tanımları taşır (Tanrı dosyaları). Bu dosyalarda değişiklik yaparken mevcut `dataclass` yapılarına (örn. `BuildingStats`, `BuildingModuleStats`) birebir uyun; eksik veya fazla argüman çökme yaratır.

## 6. Savaş ve Olay Senkronizasyonu
- Çift Tetikleyici Uyarısı: Otomatik savaş `_resolve_battle` ile interaktif ekran `battle_screen` aynı sonucu (örn. `pending_raid_report`) iki kez tetiklememelidir. Sisteme eklenen yeni bir post-battle ekranının hem otomatik hem de manuel modda çatışmadığından emin olun.
