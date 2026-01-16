# Osmanlı Eyalet Yönetim Simülasyonu

**Versiyon:** Kapalı Beta 2.0  
**Geliştirici:** Muhammet Enes Şenovalı  
**Dönem:** 1520 - Kanuni Sultan Süleyman  

---

## 🎮 Oyun Hakkında

Osmanlı Eyalet Yönetim Simülasyonu, 16. yüzyıl Osmanlı İmparatorluğu'nda bir eyalet valisi (Beylerbeyi) olarak görev yaptığınız strateji oyunudur. Ekonomi, askeri, diplomasi ve halk yönetimi gibi pek çok sistemi yöneteceksiniz.

### ♿ Erişilebilirlik

Bu oyun **görme engelli oyuncular için tam erişilebilirlik** desteği sunmaktadır:
- NVDA ekran okuyucu tam desteği
- Tüm menülerde sesli geri bildirim
- Klavye kısayolları ile tam kontrol
- Oyun durumu sesli duyuruları
- Boş menü öğeleri ekran okuyucu tarafından atlanır

---

## 🆕 Beta 2.0 Yenilikler

### ⚔️ Sıralı Savaş Sistemi
- **Oyuncu turu**: Taktik seçin, sonuç görün
- **Düşman turu**: 1.5 saniye sonra düşman AI hamle yapar
- **Düşman AI**: Moraline göre agresif, dengeli veya savunmacı taktik seçer

### 🏛️ Bina İç Ekranları
- **Çiftlik**: İşçi atama/çekme (tarım görevi)
- **Maden**: İşçi atama/çekme (madencilik görevi)
- **Kervansaray**: Kervan gönderme (tüm ticaret yolları)
- **Kışla**: 10'lu gruplarla asker eğitimi
- **Topçu Ocağı**: Top üretimi (Darbzen, Balyemez, Kolunburna, Şahi)
- **Tersane**: Gemi inşası (Mavna, Kalyon, Firkateyn, Kadırga, Mahon)

### 📚 Tarihsel Danışmanlar
Eyalet valisi danışmanları gerçekçi:
- **Sancak Beyi**: Askeri tavsiyeler
- **Kadı**: Hukuki/diplomatik tavsiyeler
- **Defterdar**: Mali tavsiyeler
- **Subaşı**: Güvenlik tavsiyeleri

### 🎵 Müzik Sistemi
- `ambient.ogg` - Normal oyun müziği
- `battle.ogg` - Savaş müziği (otomatik geçiş)

### 💰 Ekonomi Dengesi
- Sultan haracı %5 → %2
- Vergi çarpanı 0.1 → 0.15
- Ticaret geliri 500 → 800
- Askeri bakım 1.5 → 1.0
- Kış yiyecek üretimi %50 → %75

---

## 🕹️ Kontroller

### Ana Menü
| Tuş | İşlev |
|-----|-------|
| N | Yeni Oyun |
| C | Devam Et |
| O | Çok Oyunculu |
| A | Ayarlar |
| Q | Çıkış |

### Oyun İçi (Ana Ekran)
| Tuş | İşlev |
|-----|-------|
| Space | Tur Bitir |
| F5 | Kaydet |
| ESC | Ana Menü |
| E | Ekonomi |
| M | Askeri |
| I | İnşaat |
| D | Diplomasi |
| P | Nüfus |
| O | İşçiler |
| K | Savaş |
| X | Ticaret |
| N | Harita |
| J | Mevsim Bilgisi |
| F1 | Durum Duyurusu |

### İnşaat Menüsü
| Tuş | İşlev |
|-----|-------|
| Tab | Seçili binanın yükseltme bilgisi |
| Enter | Binaya gir (mevcut) veya inşa et (yeni) |

### Bina İç Ekranı
| Tuş | İşlev |
|-----|-------|
| ↑/↓ | Eylem seç |
| Enter | Eylemi uygula |
| F1 | Bina bonuslarını oku |
| Backspace | Geri dön |

---

## 🏛️ Oyun Sistemleri

### Ekonomi
- **Kaynaklar:** Altın, Zahire, Kereste, Demir
- **Gelir:** Vergi, Ticaret, Kervan
- **Gider:** Askeri bakım, Bina bakımı, Padişah haracı (%2)

### Askeri
- **Birimler:** Sipahi, Yeniçeri, Azap, Topçu, Akıncı
- **Eğitim:** Kışla iç ekranından 10'lu gruplarla
- **Savaş:** Akın, Kuşatma, Savunma, Sefer
- **Taktikler:** Merkez Hücumu, Kanat Manevrası, Savunma, Topçu Bombardımanı, Aldatma Taktiği, Teslim Çağrısı

### İnşaat
- **Binalar:** Cami, Medrese, Kışla, Pazar, Kervansaray, Hastane, Hamam, Kale, Çiftlik, Maden, Kereste Ocağı, Taş Ocağı, Ambar, Han, Tersane, Topçu Ocağı
- **Tersane:** Sadece kıyı şehirlerinde
- **Topçu Ocağı:** Top üretimi için gerekli

### Ticaret
- **Kara Yolları:** İpek Yolu, Baharat Yolu, Balkan Yolu
- **Deniz Yolları:** Akdeniz, Karadeniz (Tersane gerektirir)
- **Kervan:** Kervansaray iç ekranından gönderim

### Mevsimler
| Mevsim | Yiyecek | Ticaret |
|--------|---------|---------|
| Kış | %75 | %70 |
| İlkbahar | %120 | Normal |
| Yaz | Normal | %120 |
| Sonbahar | %150 | Normal |

---

## 🌐 Çok Oyunculu Mod

### Özellikler
- 2-6 oyuncu desteği
- Oda oluşturma ve katılma
- Sıra tabanlı tur sistemi
- Diplomasi (ittifak, ticaret, savaş)
- Sohbet sistemi
- Bağlantı kopması/yeniden bağlanma
- Oda kaydetme/yükleme

### Sunucu Başlatma
```bash
python server.py --port 8765
```

---

## 🗺️ Seçilebilir Eyaletler

| Eyalet | Başkent | Kıyı | Zorluk |
|--------|---------|------|--------|
| Aydın Sancağı | İzmir | ⚓ Evet | Kolay |
| Selanik Sancağı | Selanik | ⚓ Evet | Kolay |
| Trabzon Eyaleti | Trabzon | ⚓ Evet | Orta |
| Rum Eyaleti | Sivas | 🏔️ Hayır | Orta |
| Karaman Eyaleti | Konya | 🏔️ Hayır | Zor |
| Halep Eyaleti | Halep | 🏔️ Hayır | Zor |

---

## 🛠️ Kurulum

### EXE (Önerilen)
`OsmanliEyaletSimulasyonu.exe` dosyasını çalıştırın. **Ek kurulum gerekmez.**

### Kaynak Koddan
```bash
pip install pygame accessible_output2 websockets
python main.py
```

### Gereksinimler (Kaynak Kod İçin)
- Python 3.10+
- pygame
- accessible_output2 (ekran okuyucu)
- websockets (çok oyunculu için)

---

## 📝 Sürüm Notları

### Kapalı Beta 2.0
- ⚔️ Sıralı savaş sistemi (düşman AI turu)
- 🏛️ Bina iç ekranları (işçi yönetimi, kervan, üretim)
- 📚 Tarihsel danışman isimleri
- 🎵 Dinamik müzik sistemi (battle/ambient)
- 💰 Ekonomi dengesi iyileştirmeleri
- 🌐 Çok oyunculu mod (6 oyuncu)
- ♿ Geliştirilmiş erişilebilirlik

### Kapalı Beta 1.0
- 6 seçilebilir eyalet
- 16 farklı bina türü
- 5 askeri birim + toplar + gemiler
- Mevsim sistemi
- Savaş ve ticaret sistemleri
- Tam erişilebilirlik desteği

---

## 📧 İletişim
**E-posta:** Mesenovali@gmail.com  
**Geliştirici:** Muhammet Enes Şenovalı  

---

*İyi oyunlar!*
