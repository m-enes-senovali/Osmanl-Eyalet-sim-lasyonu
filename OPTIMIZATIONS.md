# Osmanlı Eyalet Simülasyonu — Optimizasyon Denetimi

**Tarih:** 2026-03-03  
**Denetçi:** Antigravity AI  
**Kapsam:** Tüm kod tabanı (oyun döngüsü, render, ağ, ses, kaydetme/yükleme, sunucu)

---

## 1. Optimizasyon Özeti

### Mevcut Sağlık Durumu
Kod tabanı işlevsel olarak kararlı ancak **render döngüsünde** (60 FPS'te her kare) ciddi verimsizlikler, `process_turn` içinde tekrarlanan hesaplamalar ve bellek israfı tespit edildi. Oyuncuya görünür performans etkisi düşük güçlü sistemlerde hissedilebilir.

### En Yüksek Etkiye Sahip İlk 3 İyileştirme
1. **`province_view.py` → `_update_panels()` her karede çağrılıyor** — saniyede 60 kez tüm panel metinleri yeniden oluşturuluyor, gereksiz string birleştirme + nesne tahsisi.
2. **`screen_manager.py` → `draw()` her karede import yapıyor** — `from ui.visual_effects import GradientRenderer` satırı her `draw()` çağrısında Python import makinesini tetikliyor.
3. **`game_manager.py` → `process_turn()` içinde sabit veriler her turda yeniden oluşturuluyor** — `days_in_month`, `month_names`, `locals()` kontrolleri, mükerrer tersane sorguları.

### Değişiklik Yapılmazsa En Büyük Risk
Düşük donanımlı bilgisayarlarda FPS düşüşü ve ses takılmaları. Özellikle `_update_panels()` + parçacık sistemi + gradient blit'in aynı karede çalışması, CPU bütçesini her karede gereksiz yere tüketir.

---

## 2. Önceliklendirilmiş Bulgular

### BULGU-01: `_update_panels()` Her Karede Çağrılıyor
| Alan | Detay |
|------|-------|
| **Kategori** | Render / CPU |
| **Kritiklik** | 🔴 YÜKSEK |
| **Dosya** | `ui/screens/province_view.py:610-611` |
| **Kanıt** | `update(dt)` metodu her karede `self._update_panels()` çağırıyor. Bu metot `Panel.clear()` + 15+ `add_item()` + string formatting yapıyor — saniyede 60 kez. |
| **Neden Verimsiz** | Panel verileri sadece tur sonunda değişiyor (`process_turn` çağrıldığında). Karelerin %99.9'unda aynı veriler tekrar hesaplanıyor. |
| **Önerilen Düzeltme** | `_update_panels()`'i `on_enter()` ve `_on_next_turn()` sonrasında çağır; `update(dt)` içinden kaldır. İsteğe bağlı olarak bir `_dirty` flag'i kullanılabilir. |
| **Risk** | Düşük — panel verisi zaten sadece tur bitince değişiyor. |
| **Beklenen Etki** | ~60 gereksiz string işlemi/sn eliminasyonu. FPS stability artışı. |
| **Güvenlik** | Kaldırılabilir — doğruluk etkilenmez. |

---

### BULGU-02: `screen_manager.draw()` İçinde Her Karede `import` 
| Alan | Detay |
|------|-------|
| **Kategori** | Render / Import Overhead |
| **Kritiklik** | 🟡 ORTA |
| **Dosya** | `ui/screen_manager.py:272` |
| **Kanıt** | `from ui.visual_effects import GradientRenderer` satırı `draw()` içinde — her karede çalışıyor. |
| **Neden Verimsiz** | Python `import` ifadesi modül önbelleğinden alsa bile `sys.modules` dictionary lookup + frame overhead yaratır. 60 FPS'te gereksiz. |
| **Önerilen Düzeltme** | Import'u dosyanın en üstüne taşı veya `__init__` içinde bir kez yap. |
| **Risk** | Sıfır. |
| **Beklenen Etki** | Kare başına ~2-5μs tasarruf (mikro, ama ücretsiz). |

---

### BULGU-03: Fade Surface Her Karede Yeniden Oluşturuluyor
| Alan | Detay |
|------|-------|
| **Kategori** | Bellek / Render |
| **Kritiklik** | 🟡 ORTA |
| **Dosya** | `ui/screen_manager.py:284-287` |
| **Kanıt** | `fade_surface = pygame.Surface(surface.get_size())` her fade karesinde yeni bir Surface nesnesi oluşturuyor. |
| **Neden Verimsiz** | SDL Surface tahsisi pahalıdır. Fade ~0.2 saniye sürse bile ~12 Surface malloc/free döngüsü yapar. |
| **Önerilen Düzeltme** | `__init__`'te bir kez `self._fade_surface = pygame.Surface(...)` oluştur, `draw()`'da her karede sadece `set_alpha()` + `blit()` çağır. |
| **Risk** | Sıfır. |
| **Beklenen Etki** | Düşük (0.2s boyunca ~12 allocation eliminasyonu), ama bedava. |

---

### BULGU-04: `process_turn()` İçinde Sabit Listeler Her Turda Yeniden Oluşturuluyor
| Alan | Detay |
|------|-------|
| **Kategori** | CPU / Bellek |
| **Kritiklik** | 🟡 ORTA |
| **Dosya** | `game/game_manager.py:217, 223-224` |
| **Kanıt** | `days_in_month = [31, 28, 31, ...]` ve `month_names = ["", "Ocak", ...]` listeleri her tur çağrısında yeniden oluşturuluyor. |
| **Neden Verimsiz** | Bu sabit veriler değişmez. Sınıf veya modül düzeyinde tanımlanmalı. |
| **Önerilen Düzeltme** | Modül seviyesinde `DAYS_IN_MONTH = (31, 28, ...)` ve `MONTH_NAMES = (...)` tuple'ları tanımla. |
| **Risk** | Sıfır. |
| **Beklenen Etki** | Düşük ama ücretsiz — her turda 2 liste tahsisi eliminasyonu. |

---

### BULGU-05: `process_turn()` Sonunda `'var_name' in locals()` Anti-Pattern
| Alan | Detay |
|------|-------|
| **Kategori** | Kod Kalitesi / Güvenilirlik |
| **Kritiklik** | 🟡 ORTA |
| **Dosya** | `game/game_manager.py:610-617` |
| **Kanıt** | `if 'construction_messages' in locals():` kontrolü — değişken her zaman tanımlı olduğu halde gereksiz güvenlik kontrolü. |
| **Neden Verimsiz** | `locals()` çağrısı geçici bir dictionary oluşturur. Ayrıca bu pattern, kodun kendi akışına güvenmediğini gösterir ve bakım riskidir. |
| **Önerilen Düzeltme** | Fonksiyon başında `messages = []` tanımla, her alt sistem sonucu ürettiğinde doğrudan `.extend()` yap. Sonunda `locals()` kontrolüne gerek kalmaz. |
| **Risk** | Sıfır. |
| **Beklenen Etki** | Düşük performans, yüksek okunabilirlik artışı. |

---

### BULGU-06: `process_turn()` İçinde Mükerrer Tersane (Shipyard) Sorgusu 
| Alan | Detay |
|------|-------|
| **Kategori** | Tekrarlanan Hesaplama |
| **Kritiklik** | 🟢 DÜŞÜK |
| **Dosya** | `game/game_manager.py:415-421` ve `517-521` |
| **Kanıt** | `has_shipyard = self.construction.has_building(BuildingType.SHIPYARD)` + seviye sorgusu iki kez yapılıyor: satır 415'te ve 517'de. |
| **Neden Verimsiz** | Aynı dictionary lookup + attribute erişimi gereksiz yere tekrarlanıyor. |
| **Önerilen Düzeltme** | İlk sorguda değişkeni kaydet, ikincisinde yeniden kullan. |
| **Risk** | Sıfır. |
| **Beklenen Etki** | Minimal. Temiz kod amacıyla. |

---

### BULGU-07: `process_turn()` Sonunda `divan.analyze_turn()` Sadece `len()` İçin Çağrılıyor
| Alan | Detay |
|------|-------|
| **Kategori** | CPU |
| **Kritiklik** | 🟡 ORTA |
| **Dosya** | `game/game_manager.py:627` |
| **Kanıt** | `'divan_reports': len(self.divan.analyze_turn(self))` — Divan analizi muhtemelen tüm istatistikleri hesaplıyor, ama sadece öğe sayısı kullanılıyor. |
| **Neden Verimsiz** | Eğer `analyze_turn` ağır bir hesaplama yapıyorsa (tüm ekonomi+askeri+diplomatik analiz), sadece `len()` almak israftır. |
| **Önerilen Düzeltme** | `analyze_turn` çağrısını kaldır veya sonucunu önbelleğe al. Alternatif: daha hafif bir `get_report_count()` metodu ekle. |
| **Risk** | Düşük. `analyze_turn` içeriğine bağlı. |
| **Beklenen Etki** | Muhtemelen orta — `divan.py` 28KB, analiz hesaplaması ağır olabilir. |

---

### BULGU-08: Başarı Sistemi Her Turda Dinamik Import Yapıyor
| Alan | Detay |
|------|-------|
| **Kategori** | Import / CPU |
| **Kritiklik** | 🟢 DÜŞÜK |
| **Dosya** | `game/game_manager.py:593` |
| **Kanıt** | `from game.systems.achievements import get_achievement_system` — `process_turn()` içinde her turda çağrılıyor. |
| **Neden Verimsiz** | Her ne kadar Python modül önbelleği sayesinde hızlı olsa da, bu import `try/except` bloğu ile sarmalandığı için exception handling overhead'i de ekliyor. |
| **Önerilen Düzeltme** | `__init__`'te bir kez import et, `self.achievements = get_achievement_system()` olarak sakla. |
| **Risk** | Sıfır — modül zaten yüklü. |
| **Beklenen Etki** | Düşük. |

---

### BULGU-09: `_draw_resource_bar()` Her Karede `get_font()` Çağırıyor
| Alan | Detay |
|------|-------|
| **Kategori** | Render |
| **Kritiklik** | 🟡 ORTA |
| **Dosya** | `ui/screens/province_view.py:688` |
| **Kanıt** | `value_font = get_font(FONTS['subheader'])` her `draw()` çağrısında (60 FPS) çağrılıyor. `get_font()` önbellekli olmasına rağmen dictionary lookup + `if` kontrolü * 7 kaynak = 420 lookup/sn. |
| **Neden Verimsiz** | Font nesnesi asla değişmiyor. Bir kez `__init__` veya lazy property olarak alınmalı. |
| **Önerilen Düzeltme** | `self._value_font` olarak bir kez kaydet. |
| **Risk** | Sıfır. |
| **Beklenen Etki** | Küçük ama ücretsiz (420 dict lookup/sn eliminasyonu). |

---

### BULGU-10: `province_view.py` — `_draw_resource_bar` ve `_draw_summary` Her Karede Yeni Liste/String Oluşturuyor
| Alan | Detay |
|------|-------|
| **Kategori** | Bellek / GC Baskısı |
| **Kritiklik** | 🟢 DÜŞÜK |
| **Dosya** | `ui/screens/province_view.py:666-690, 692-727` |
| **Kanıt** | `resources = [("Altın", ...), ...]` listesi ve `stats = [...]` listesi her karede oluşturuluyor. |
| **Neden Verimsiz** | Kullanılıp hemen çöpe giden 60 * (7+3) = 600 tuple/sn GC baskısı yaratır. Düşük etkili ama önlenebilir. |
| **Önerilen Düzeltme** | Panel verisi gibi, sadece veri değiştiğinde yeniden oluştur (dirty flag). Veya `__init__`'te statik yapıyı oluşturup sadece değerleri güncelle. |
| **Risk** | Düşük. |
| **Beklenen Etki** | Düşük — GC baskısı azalması. |

---

### BULGU-11: 36 Ekran Başlangıçta Eşzamanlı Olarak Oluşturuluyor (Eager Instantiation)
| Alan | Detay |
|------|-------|
| **Kategori** | Başlangıç Süresi / Bellek |
| **Kritiklik** | 🟡 ORTA |
| **Dosya** | `main.py:84-306` |
| **Kanıt** | `_register_screens()` metodu tüm 36 ekranı `__init__`'te oluşturuyor. Her ekran `Panel`, `Button`, `MenuList`, `ParticleSystem` gibi bileşenleri yaratıyor. |
| **Neden Verimsiz** | Oyuncu ana menüdeyken 34 ekranın nesneleri bellekte gereksiz yere duruyor. Ayrıca başlangıç süresi uzuyor. |
| **Önerilen Düzeltme** | Lazy instantiation: `register_screen` yerine `register_screen_factory(ScreenType.X, lambda sm: XScreen(sm))` şeklinde bir fabrika kullan. Ekran ilk açıldığında oluşturulsun. |
| **Risk** | Orta — ilk ekran geçişinde kısa bir gecikme olabilir. |
| **Beklenen Etki** | ~%50 başlangıç bellek tasarrufu, ~%30 daha hızlı başlangıç. |

---

### BULGU-12: `screen_manager.draw()` Her Karede Gradient Alıyor
| Alan | Detay |
|------|-------|
| **Kategori** | Render |
| **Kritiklik** | 🟢 DÜŞÜK |
| **Dosya** | `ui/screen_manager.py:272-277` |
| **Kanıt** | `GradientRenderer.get_gradient(theme)` önbellekli (hash tabanlı). Ama dictionary lookup + string comparison her karede gereksiz. |
| **Neden Verimsiz** | Gradient yalnızca ekran değiştiğinde değişir. |
| **Önerilen Düzeltme** | `_execute_screen_change` içinde gradient'ı bir kez al ve `self._current_gradient` olarak sakla. `draw()`'da doğrudan `self._current_gradient` kullan. |
| **Risk** | Sıfır. |
| **Beklenen Etki** | Düşük. |

---

### BULGU-13: `province_view.py` İkili Gradient Blit
| Alan | Detay |
|------|-------|
| **Kategori** | Render — Çift Blit |
| **Kritiklik** | 🟡 ORTA |
| **Dosya** | `ui/screen_manager.py:277` + `ui/screens/province_view.py:631` |
| **Kanıt** | `screen_manager.draw()` zaten gradient'ı surface'e blit ediyor (satır 277), ardından `province_view.draw()` aynı gradient'ı tekrar blit ediyor (satır 631). Her karede aynı ekran boyutunda piksel kopyası 2 kez yapılıyor. |
| **Neden Verimsiz** | 1280×720 = ~920K piksel × 2 = gereksiz ~1.8M piksel yazımı/kare. |
| **Önerilen Düzeltme** | `province_view.draw()` içindeki gradient blit'i kaldır — zaten `screen_manager` çiziyor. Veya `screen_manager`'daki gradient çizimini kaldırıp ekranların kendi gradient'larını çizmesine izin ver. |
| **Risk** | Düşük — tek bir politikaya karar verilmeli. |
| **Beklenen Etki** | Kare başına ~1ms tasarruf (SDL blit maliyeti). |

---

### BULGU-14: HTTP Polling Client'ta `old_room != self.room_data` Deep Comparison
| Alan | Detay |
|------|-------|
| **Kategori** | Ağ / CPU |
| **Kritiklik** | 🟢 DÜŞÜK |
| **Dosya** | `network/client_http.py:123` |
| **Kanıt** | `if old_room != self.room_data:` — iki iç içe dictionary'nin (oyuncu listesi, sohbet mesajları, diplomasi verileri vb.) deep comparison'ı her 2 saniyede yapılıyor. |
| **Neden Verimsiz** | Oda verisi büyüdükçe karşılaştırma maliyeti artar. |
| **Önerilen Düzeltme** | Sunucu tarafına bir `version` veya `last_modified` sayacı ekle. İstemci sadece bu sayacı karşılaştırsın. |
| **Risk** | Sunucu değişikliği gerektirir. |
| **Beklenen Etki** | Düşük (şimdilik oda verisi küçük). Ölçeklenebilirlik için önemli. |

---

### BULGU-15: `process_turn()` İçinde `try/except` ile Bina Erişimi
| Alan | Detay |
|------|-------|
| **Kategori** | Hata Yönetimi / Performans |
| **Kritiklik** | 🟢 DÜŞÜK |
| **Dosya** | `game/game_manager.py:313-328` |
| **Kanıt** | Barut ve bakır üretimi `try: ... except Exception: pass` bloklarıyla sarmalanmış. Normal akışta exception fırlatılmıyor, ama `try` bloğu overhead ekliyor. |
| **Neden Verimsiz** | `except Exception: pass` kötü bir anti-pattern: hataları sessizce yutabilir. |
| **Önerilen Düzeltme** | `if self.construction.has_building(BuildingType.ARTILLERY_FOUNDRY):` şeklinde açık kontrol yap. `try/except` kaldır. |
| **Risk** | Sıfır — aynı sorgular zaten başka yerlerde yapılıyor. |
| **Beklenen Etki** | Düşük performans iyileştirmesi, yüksek kod kalitesi artışı. |

---

### BULGU-16: `construction.py` 98KB / 2285 Satır — Tanrı Dosyası (God File)
| Alan | Detay |
|------|-------|
| **Kategori** | Sürdürülebilirlik |
| **Kritiklik** | 🟡 ORTA |
| **Dosya** | `game/systems/construction.py` |
| **Kanıt** | ~1700 satır bina tanımı (veri) + ~600 satır iş mantığı tek dosyada. |
| **Neden Verimsiz** | Her import'ta tüm bina verisi bellekte parse ediliyor. Bakım zorluğu: yeni bina eklemek için 2285 satırlık dosyada gezinme. |
| **Önerilen Düzeltme** | Bina verilerini `building_data.py` veya `buildings.json` dosyasına ayır. `construction.py` sadece iş mantığını barındırsın. |
| **Risk** | Orta — refactoring gerektirir. |
| **Beklenen Etki** | Bakım kolaylığı. Performans etkisi minimal. |

---

### BULGU-17: `events.py` 80KB — Benzer Yapı
| Alan | Detay |
|------|-------|
| **Kategori** | Sürdürülebilirlik |
| **Kritiklik** | 🟡 ORTA |
| **Dosya** | `game/systems/events.py` |
| **Kanıt** | ~1580 satır olay tanımı (veri) + ~460 satır iş mantığı. |
| **Önerilen Düzeltme** | Olay verilerini `event_data.py` veya JSON/YAML'a ayır. |

---

## 3. Hızlı Kazanımlar (Düşük Efor, Yüksek Etki)

| # | Değişiklik | Efor | Etki |
|---|-----------|------|------|
| 1 | `province_view.update()` içinden `_update_panels()` çağrısını kaldır, sadece `_on_next_turn()` ve `on_enter()` içinde çağır | 2 dk | 🔴 Yüksek |
| 2 | `screen_manager.draw()` içindeki `from ui.visual_effects import` satırını dosya başına taşı | 1 dk | 🟡 Orta |
| 3 | `province_view.draw()` içindeki ikili gradient blit'i kaldır | 1 dk | 🟡 Orta |
| 4 | `screen_manager` için `_fade_surface`'i `__init__`'te bir kez oluştur | 2 dk | 🟢 Düşük |
| 5 | `process_turn()` içindeki `days_in_month`, `month_names` listelerini modül sabiti yap | 2 dk | 🟢 Düşük |
| 6 | `process_turn()` sonundaki `locals()` kontrollerini kaldır, `messages = []` ile başlat | 3 dk | 🟢 Düşük |

---

## 4. Derin Optimizasyonlar (Mimari Seviye)

### 4.1 Lazy Screen Instantiation
36 ekranı başlangıçta oluşturmak yerine, bir screen factory registry kullanarak sadece ilk erişimde oluştur. Bu, başlangıç süresini ve bellekteki nesne sayısını önemli ölçüde azaltır.

### 4.2 Dirty Flag Tabanlı Render Pipeline
`province_view` ve diğer ekranlar için bir "dirty flag" mekanizması kur:
- Oyun durumu değiştiğinde (tur sonu, olay vb.) `dirty = True` ayarla
- `update()` sadece `dirty` ise panel/string güncelle
- `draw()` sadece değişen bölgeleri yeniden çizsin (kısmi render)

### 4.3 `construction.py` ve `events.py` Veri Ayırma
Bina ve olay tanımlarını ayrı veri dosyalarına (JSON veya Python dict modülleri) taşıyarak iş mantığını veriden ayır. Bu, bakım kolaylığı + gelecekte modding desteği sağlar.

### 4.4 Server-Side Versioning (Multiplayer)
HTTP polling istemcisine sunucu tarafında `room_version` sayacı ekle. İstemci sadece versiyon numarasını karşılaştırarak değişiklik olup olmadığını anlasın — deep dict comparison eliminate edilsin.

### 4.5 `process_turn()` Pipeline Refactoring
420 satırlık monolitik metodu daha küçük, test edilebilir adımlara böl:
```python
def process_turn(self):
    self._advance_calendar()
    self._process_economy()
    self._process_population()
    self._process_military()
    self._process_diplomacy()
    self._process_events()
    self._check_end_conditions()
    return self._build_turn_report()
```

---

## 5. Doğrulama Planı

### Otomatik Testler
```bash
# Tur performasını ölç
python -c "
import time
from game.game_manager import GameManager
gm = GameManager()
gm.new_game()
start = time.perf_counter()
for _ in range(365): gm.process_turn()
print(f'365 tur: {time.perf_counter()-start:.3f}s')
"
```

### Profilleme Stratejisi
```bash
# cProfile ile hot-path tespiti
python -m cProfile -s cumulative main.py 2>&1 | head -50
```

### Öncesi/Sonrası Metrikleri
| Metrik | Ölçüm Yöntemi |
|--------|---------------|
| FPS stabilitesi | `pygame.time.Clock.get_fps()` değerini 1 dk boyunca logla |
| Başlangıç süresi | `time.perf_counter()` ile `Game.__init__` süresini ölç |
| Bellek kullanımı | `tracemalloc` ile peak bellek tüketimini karşılaştır |
| `process_turn` süresi | 365 tur için toplam süre (öncesi vs sonrası) |

### Manuel Doğrulama
- Oyunu 10 tur oyna, panel verilerinin doğru güncellendiğini kontrol et
- Ekranlar arası geçişte fade efektinin düzgün çalıştığını doğrula
- Kaydet/yükle döngüsünün veri bütünlüğünü korduğunu test et

---

## 6. Optimize Edilmiş Kod Örnekleri

> ⚠️ **NOT:** Kullanıcı talimatı gereği dosyalarda değişiklik YAPILMADI. Aşağıdakiler uygulama referansıdır.

### 6.1 `province_view.py` — `_update_panels()` Düzeltmesi

```diff
 def update(self, dt: float):
-    self._update_panels()
     self._particles.update(dt)
     # Mevsimi güncelle ...
```

```diff
 def _on_next_turn(self):
     gm = self.screen_manager.game_manager
     if gm:
         # ... process_turn ...
+        self._update_panels()  # Sadece tur sonunda güncelle
```

### 6.2 `screen_manager.py` — Import ve Fade Surface Düzeltmesi

```diff
 # Dosya başı
 import pygame
 from enum import Enum
 from typing import Optional
 from audio.audio_manager import get_audio_manager
 from audio.music_manager import get_music_manager
 from config import COLORS
+from ui.visual_effects import GradientRenderer
```

```diff
 def __init__(self, game_manager=None):
     # ...
+    self._fade_surface = pygame.Surface((1280, 720))
+    self._fade_surface.fill((0, 0, 0))
+    self._current_gradient = None
```

```diff
 def draw(self, surface):
-    from ui.visual_effects import GradientRenderer
-    theme = 'default'
-    if self.current_screen_type:
-        theme = self.SCREEN_GRADIENT_MAP.get(self.current_screen_type.value, 'default')
-    gradient = GradientRenderer.get_gradient(theme)
-    surface.blit(gradient, (0, 0))
+    if self._current_gradient:
+        surface.blit(self._current_gradient, (0, 0))
     if self.current_screen:
         self.current_screen.draw(surface)
     if self.fade_state is not None and self.fade_alpha > 0:
-        fade_surface = pygame.Surface(surface.get_size())
-        fade_surface.fill((0, 0, 0))
-        fade_surface.set_alpha(int(self.fade_alpha))
-        surface.blit(fade_surface, (0, 0))
+        self._fade_surface.set_alpha(int(self.fade_alpha))
+        surface.blit(self._fade_surface, (0, 0))
```

### 6.3 `game_manager.py` — Sabit Veriler

```diff
+# Modül seviyesi sabitler
+DAYS_IN_MONTH = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)
+MONTH_NAMES = ("", "Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran",
+               "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık")

 def process_turn(self):
     self.turn_count += 1
     self.current_day += 1
-    days_in_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
-    if self.current_day > days_in_month[self.current_month - 1]:
+    if self.current_day > DAYS_IN_MONTH[self.current_month - 1]:
         self.current_day = 1
         self.current_month += 1
-        month_names = ["", "Ocak", ...]
         if self.current_month <= 12:
-            self.audio.announce(f"{month_names[self.current_month]} ayı başladı")
+            self.audio.announce(f"{MONTH_NAMES[self.current_month]} ayı başladı")
```
