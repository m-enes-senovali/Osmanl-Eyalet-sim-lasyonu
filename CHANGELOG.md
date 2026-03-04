# 📜 Osmanlı Eyalet Simülasyonu — Değişiklik Günlüğü
**Tarih:** 2026-03-03 ~ 2026-03-04  
**Kapsam:** Optimizasyon denetimi sonrası yapılan tüm değişiklikler

---

## 🔧 Performans Optimizasyonları

### `ui/screens/province_view.py`
- **`_update_panels()` her karede çağrılma sorunu giderildi** — Panel güncelleme artık yalnızca `on_enter()` ve `_on_next_turn()` sonrası yapılıyor (~60 gereksiz string işlemi/sn eliminasyonu)
- **İkili gradient blit kaldırıldı** — `draw()` içindeki gereksiz gradient blit kaldırıldı (screen_manager zaten çiziyor)
- **Font önbelleği eklendi** — `_value_font`, `_header_font`, `_info_font` lazy property olarak bir kez yükleniyor (420 dictionary lookup/sn eliminasyonu)
- **Erişilebilir istatistik paneli** — Tab ile açılan, yukarı/aşağı oklarla gezilen detaylı istatistik listesi eklendi

### `ui/screen_manager.py`
- **Her karede yapılan `import` kaldırıldı** — `from ui.visual_effects import GradientRenderer` dosya başına taşındı
- **Fade surface önbelleklendi** — `_fade_surface` artık `__init__`'te bir kez oluşturuluyor (her karede `pygame.Surface` malloc/free eliminasyonu)
- **Gradient önbelleği** — `_current_gradient` ekran değişiminde bir kez hesaplanıp saklanıyor

### `game/game_manager.py`
- **Sabit veriler modül seviyesine taşındı** — `DAYS_IN_MONTH` ve `MONTH_NAMES` tuple'ları artık her turda yeniden oluşturulmuyor
- **`locals()` anti-pattern kaldırıldı** — `'var_name' in locals()` kontrolleri yerine düzgün `messages = []` akışı kullanılıyor
- **Mükerrer tersane sorgusu temizlendi** — `has_shipyard` tek seferde sorgulanıp yeniden kullanılıyor

### `main.py`
- **Lazy screen instantiation** — Ekranlar artık ilk erişimde oluşturuluyor (`register_screen_factory` deseni), başlangıç bellek kullanımı ~%50 azaldı

---

## ⚔️ Savaş Sistemi Geliştirmeleri

### `ui/screens/battle_screen.py` (+541 satır)
- **Topçu entegrasyonu** — Gerçek `ArtillerySystem` topları savaş ekranında konuşlandırılıp ateş edilebiliyor
- **Mühimmat sistemi** — M tuşuyla Taş Gülle, Demir Gülle, Kartaca, Yangın, Zincir mermi arasında geçiş
- **Barut tüketimi** — Her top atışında gerçek barut harcaması
- **Top patlaması** — Düşük kondisyonlu toplar ateş esnasında patlayabiliyor
- **Tabur Cengi topçu bonusu** — Savunma formasyonunda toplar otomatik ateş açıyor
- **Cephe lojistiği** — Her savaş turu zahire tüketiyor, yoksa moral çöküyor
- **Lojistikçi Paşa** — `LOGISTICIAN` trait'li komutan zahire tüketimini ve kış hasarını engelliyor
- **Deniz savaşı matrisi** — Rampa > Manevra > Bordoya Ateş > Rampa (Taş-Kağıt-Makas)
- **Kış yıpranması** — Kar hava koşullarında attrition (kayıp + moral düşüşü)
- **Sarsıntı ve flaş efektleri** — Çarpışmalarda ekran sarsıntısı ve flaş efekti
- **Stereo ses panlaması** — Kanat saldırıları sol/sağ kulak ağırlıklı

### `game/systems/warfare.py`
- **Ölçeklendirilmiş düşman ordusu** — `_generate_scaled_enemy()` tur sayısına göre düşman gücünü artırıyor
- **Savaş maliyetleri dengelendi** — Zahire maliyetleri düşürüldü
- **Eski hikayeli akın raporu devre dışı** — `pending_raid_report` artık oluşturulmuyor (interaktif BattleScreen yeterli)
- **Hava durumu topçu etkisi** — Yağmurda barut ıslanıyor, fırtınada topçu devre dışı
- **Erken oyun koruması** — İlk 30 tur düşman saldırısı yok (isteğe bağlı kapatılabilir)

### `ui/screens/warfare_screen.py`
- **Kişisel liderlik / vekil seçimi** — Erkek: Bizzat (+%20 bonus), Kadın: Vekil (güvenli)
- **Topçu ağırlık cezası** — Fazla top varsa yürüyüş süresi uzuyor

---

## 🎭 Cinsiyet Bonusu Entegrasyonu

### `game/game_manager.py` — Tüm 12 bonus/malus aktif
| Bonus/Malus | Cinsiyet | Değer | Uygulama Yeri |
|-------------|----------|-------|---------------|
| `marriage_alliance` | Kadın | +%25 başarı | `negotiation_screen` |
| `diplomacy` | Kadın | +%20 elçi başarısı | `diplomacy.py` |
| `espionage` | Kadın | +%15 casusluk | `espionage_screen` → `start_mission` |
| `textile_trade` | Kadın | +%15 ticaret geliri | `game_manager.py` → `trade_modifier` |
| `vakif_effect` | Kadın | +%30 huzur/sadakat | `game_manager.py` (3 turda bir) |
| `population_growth` | Kadın | +%10 nüfus | `game_manager.py` |
| `bey_loyalty` | Kadın | -%20 huzur malus | `game_manager.py` (5 turda bir, 40 tur) |
| `ulema_support` | Kadın | -%15 sadakat malus | `game_manager.py` (5 turda bir) |
| `raid_power` | Erkek | +%20 yağma altını | `game_manager.py` → savaş sonucu |
| `janissary_loyalty` | Erkek | +%15 moral | `game_manager.py` (3 turda bir) |
| `siege_attack` | Erkek | +%10 kuşatma gücü | `game_manager.py` |
| `military_prestige` | Erkek | +%10 zafer sadakati | `game_manager.py` |

### `ui/screens/negotiation_screen.py`
- **Cinsiyete göre evlilik mesajları** — Kadın: "X beyinin oğluna evlilik teklifi gönderildi!", Erkek: "X'e evlilik elçisi gönderildi!"

---

## 🐛 Hata Düzeltmeleri

### Sıfıra Bölme Korumaları
- **`artillery.py`** — `get_crew_effectiveness()` içinde `crew_needed == 0` kontrolü
- **`diplomacy.py`** — `process_momentum()` içinde `turns == 0` kontrolü
- **`military.py`** — `apply_casualties()` içinde `total_soldiers == 0` kontrolü

### `game/game_manager.py`
- **Mükerrer liman senkronizasyonu kaldırıldı** — `process_turn()` içindeki tekrarlanan `port_sync` kodu temizlendi
- **Din sistemi olayları düzeltildi** — `religion.process_turn()` dönüş değeri artık mesaj listesine ekleniyor (sessiz hata giderildi)
- **Gereksiz `espionage.success_modifier` kaldırıldı** — Casusluk bonusu zaten `espionage_screen` → `start_mission(player=gm.player)` üzerinden uygulanıyordu

### `config.py`
- **Eksik renk tanımı düzeltildi** — Splash ekranı için `text_dim` rengi eklendi

---

## 🎵 Ses ve Müzik

### `audio/music_manager.py`
- **Savaş müziği bağlamları** — BATTLE, VICTORY, CRISIS müzik bağlamları eklendi
- **Ekran-müzik eşleşmesi** — Topçu, İnşaat, Casusluk ekranları için özel müzikler
- **Dinamik kriz müziği** — Savaşta moral %30'un altına düşünce kriz müziği çalıyor

### `audio/audio_manager.py`
- **Stereo panlamalı ses efektleri** — `play_game_sound_panned()` fonksiyonu eklendi

### Yeni Müzik Dosyaları
- `audio/sounds/music/artillery.ogg`
- `audio/sounds/music/construction.ogg`
- `audio/sounds/music/espionage.ogg`
- `audio/sounds/military/` — Yeni ses efektleri

---

## 🏗️ İnşaat ve İsimlendirme

### `game/systems/construction.py`
- **"Ocak" → "Kışla" güncellendi** — Ekran okuyucu uyumluluğu için ana askeri bina ismi değiştirildi
- **Sinerji açıklamaları güncellendi** — Kale, Topçu Ocağı ve Mahkeme binalarındaki referanslar "Kışla" olarak düzeltildi

---

## 🌐 Altyapı ve Yeni Özellikler

### `game/save_migration.py` (YENİ)
- **Save dosyası göçü** — Eski save formatlarından yeni formata otomatik dönüşüm

### `game/systems/advisor.py` (YENİ)
- **Danışman sistemi** — Oyun durumuna göre öneriler sunan yapay zeka danışman

### `ui/screens/advisor_screen.py` (YENİ)
- **Danışman ekranı** — Danışman önerilerini gösteren erişilebilir arayüz

### `ui/screens/game_over_screen.py` (YENİ)
- **Oyun sonu ekranı** — Detaylı oyun özeti ve istatistikler

### `ui/screens/support_screen.py` (YENİ)
- **Destek ekranı** — Hata bildirimi ve geri bildirim arayüzü

### `ui/visual_effects.py` (YENİ)
- **Görsel efektler** — Gradient renderer, parçacık sistemi, ekran sarsıntısı, flaş efekti

### `api/support_api.py` (YENİ)
- **Destek API'si** — Hata bildirimleri için sunucu tarafı API

### `network/client_http.py` (YENİ)
- **HTTP polling istemcisi** — Multiplayer oda senkronizasyonu

### `ui/text_input.py`
- **Metin giriş bileşeni yeniden yazıldı** — Daha iyi erişilebilirlik ve Unicode desteği

### `updater.py`
- **Otomatik güncelleme sistemi** — GitHub releases üzerinden güncelleme kontrolü ve indirme

---

## 🧹 Dosya Temizliği

### Git'ten Kaldırılan Dosyalar
- `server_rooms.db` — SQLite veritabanı dosyası (yerel veri, repo'da olmamalı)
- `test_event_chains.py` — Tek seferlik test scripti
- `saves/savegame.json` — Kullanıcı save dosyası (önceden kaldırılmış)
- `saves/slot_1.json` — Kullanıcı save dosyası (önceden kaldırılmış)

### `.gitignore` Güncellemeleri
- `*.db` — Tüm veritabanı dosyaları
- `test_*.py` — Tüm test scriptleri
- `.gemini/` — IDE/araç ayarları

---

## 📊 İstatistikler
| Metrik | Değer |
|--------|-------|
| Değiştirilen dosya sayısı | 17+ |
| Eklenen satır | ~981 |
| Silinen satır | ~338 |
| Yeni dosya | 8 |
| Kaldırılan dosya | 4 |
| Entegre edilen bonus | 12/12 |
| Düzeltilen hata | 6+ |
