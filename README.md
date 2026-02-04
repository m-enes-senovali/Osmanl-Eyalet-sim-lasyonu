# Osmanlı Eyalet Yönetim Simülasyonu

**Versiyon:** Kapalı Beta 3.0  
**Geliştirici:** Muhammet Enes Şenovalı  
**Dönem:** 1520 - Kanuni Sultan Süleyman Dönemi

---

## Oyun Hakkında

Osmanlı Eyalet Yönetim Simülasyonu, 16. yüzyıl Osmanlı İmparatorluğu'nda bir eyalet valisi (Beylerbeyi) olarak görev yaptığınız kapsamlı strateji oyunudur. Ekonomi, askeri güçler, diplomasi, ticaret ve halk yönetimi sistemlerini dengeli şekilde yönetmeniz gerekmektedir.

### Erişilebilirlik (Görme Engelli Desteği)

Bu oyun **görme engelli oyuncular için tam erişilebilirlik** desteği sunmaktadır:
- NVDA/JAWS ekran okuyucu tam desteği
- Tüm menülerde sesli geri bildirim
- Klavye ile tam kontrol (fare gerekmez)
- Oyun durumu sesli duyuruları
- Hiyerarşik menü sistemi (kolay navigasyon)
- F1 ile her ekranda özet duyurusu

---

## Beta 3.0 Yenilikler

### Hiyerarşik Menü Sistemi
Tüm menüler artık alt menülerle organize:
- **Enter** ile alt menüye girin
- **Backspace/Escape** ile geri dönün
- **Yukarı/Aşağı ok** ile gezinin
- **F1** ile özet alın (tek kısayol!)

### Gelişmiş Diplomasi Sistemi
- **Prestij sistemi** (0-500 puan, 5 seviye)
- **Olay zincirleri** (evlilik, vassal müzakereleri birden fazla tur sürer)
- **AI kişilikleri** (Agresif, Tüccar, Onurlu, Korkak, Dindar)
- **Momentum sistemi** (ilişki değişimleri kademeli)

### Non-blocking Çok Oyunculu
- Sunucu bağlantısı artık oyunu dondurmaz
- Escape ile bağlantı iptal edilebilir

---

## Kontroller

### Temel Navigasyon (Tüm Ekranlarda)

| Tuş | İşlev |
|-----|-------|
| Yukarı/Aşağı Ok | Menüde gezin |
| Enter | Seç / Alt menüye gir |
| Backspace | Geri dön / Üst menüye çık |
| Escape | Geri dön / İptal |
| F1 | Özet duyurusu |

### Ana Menü

| Tuş | İşlev |
|-----|-------|
| N | Yeni Oyun |
| C | Devam Et (kayıtlı oyun) |
| O | Çok Oyunculu |
| A | Ayarlar |
| Q | Çıkış |

### Eyalet Görünümü (Ana Oyun Ekranı)

| Tuş | İşlev |
|-----|-------|
| Space (Boşluk) | Tur Bitir |
| F5 | Hızlı Kaydet |
| Escape | Ana Menüye Dön |
| E | Ekonomi Ekranı |
| M | Askeri Ekranı |
| I | İnşaat Ekranı |
| D | Diplomasi Ekranı |
| P | Nüfus Ekranı |
| O | İşçiler Ekranı |
| K | Savaş Ekranı |
| X | Ticaret Ekranı |
| N | Harita Ekranı |
| J | Mevsim Bilgisi |
| F1 | Eyalet Durumu Özeti |

---

## Oyun Ekranları

### Diplomasi Ekranı

Hiyerarşik menü yapısı:

```
DİPLOMASİ
├── Padişah İlişkileri
│   ├── Padişaha 500 Altın Gönder
│   ├── Padişaha 2000 Altın Gönder
│   └── [Varsa görev tamamlama seçenekleri]
│
├── Evlilik İttifakları (10000 Altın)
│   └── [Komşu listesi - ilişki puanlarıyla]
│
├── Haraç Talebi (500+ güç gerekli)
│   └── [Komşu listesi - kişilik bilgisiyle]
│
├── Vassallaştırma (1500+ güç gerekli)
│   └── [Komşu listesi]
│
├── Durum Özeti
│   ├── Prestij seviyesi
│   ├── Aktif olay zincirleri (detaylı)
│   ├── Mevcut vassallar
│   └── Evlilik ittifakları
│
├── Haritaya Git
└── Ana Ekrana Dön
```

**Olay Zincirleri:** Evlilik ve vassal müzakereleri birden fazla tur sürebilir. Durum Özeti'nden ilerlemeyi takip edin.

### Askeri Ekranı

Hiyerarşik menü yapısı:

```
ASKERİ YÖNETİM
├── Sipahi (mevcut sayı)
│   ├── Mevcut: X adet
│   ├── Maliyet: 100 altın/birim, 2 tur eğitim
│   ├── +10 topla
│   ├── +50 topla
│   ├── +100 topla
│   └── Maksimum topla
│
├── Yeniçeri (mevcut sayı)
├── Azap (mevcut sayı)
├── Topçu (mevcut sayı)
├── Akıncı (mevcut sayı)
│
├── Eğitim Kuyruğu
│   └── [Eğitimdeki birimler ve kalan turlar]
│
├── Ordu Durumu
│   ├── Toplam asker
│   ├── Toplam güç
│   ├── Bakım maliyeti
│   ├── Moral
│   └── Zafer/Kayıp istatistikleri
│
├── Eşkıya Bastır
└── Ana Ekrana Dön
```

**Eğitim Süresi:**
| Birim | Eğitim Süresi | Maliyet |
|-------|---------------|---------|
| Akıncı | 1 tur | 50 altın |
| Azap | 1 tur | 30 altın |
| Sipahi | 2 tur | 100 altın |
| Yeniçeri | 2 tur | 80 altın |
| Topçu | 3 tur | 150 altın |

### İnşaat Ekranı

| Tuş | İşlev |
|-----|-------|
| Yukarı/Aşağı | Bina seç |
| Enter | Binaya gir (mevcut) veya inşa et (yeni) |
| Tab | Seçili binanın yükseltme bilgisi |
| Backspace | Geri dön |

### Bina İç Ekranı

| Tuş | İşlev |
|-----|-------|
| Yukarı/Aşağı | Eylem seç |
| Enter | Eylemi uygula |
| F1 | Bina bonuslarını oku |
| Backspace | Geri dön |

**Bina İçi Eylemler:**
- **Çiftlik/Maden:** İşçi atama ve çekme
- **Kervansaray:** Kervan gönderme (tüm ticaret yolları)
- **Kışla:** Asker eğitimi
- **Topçu Ocağı:** Top üretimi
- **Tersane:** Gemi inşası

---

## Oyun Sistemleri

### Ekonomi

**Kaynaklar:**
- Altın - Ana para birimi
- Zahire (Yiyecek) - Nüfus için gerekli
- Kereste - İnşaat için gerekli
- Demir - Askeri üretim için gerekli

**Gelir Kaynakları:**
- Vergi (nüfusa göre)
- Ticaret (kervansaray ve ticaret yolları)
- Maden/Çiftlik üretimi

**Giderler:**
- Askeri bakım (asker sayısına göre)
- Bina bakımı
- Padişah haracı (%2)

### Mevsim Sistemi

Oyun 4 mevsim döngüsünde ilerler:

| Mevsim | Yiyecek Üretimi | Ticaret |
|--------|-----------------|---------|
| Kış | %75 | %70 |
| İlkbahar | %120 | Normal |
| Yaz | Normal | %120 |
| Sonbahar | %150 | Normal |

Mevsim bilgisi için ana ekranda **J** tuşuna basın.

### Diplomasi

**Prestij Seviyeleri:**
| Puan | Seviye | Diplomatik Bonus |
|------|--------|------------------|
| 0-99 | Yeni Vali | %0 |
| 100-249 | Saygın Bey | %10 |
| 250-399 | Güçlü Paşa | %20 |
| 400-499 | Efsanevi Vezir | %30 |
| 500 | Sultan'ın Sağ Kolu | %40 |

**Komşu Kişilikleri:**
- **Agresif:** Askeri tehditler, haraç kabul etmez
- **Tüccar:** Ticaret tekliflerine açık
- **Onurlu:** Sözünde durur, ihanet etmez
- **Korkak:** Güçlü olana boyun eğer
- **Dindar:** Dini bağlar önemli

### Savaş

**Savaş Türleri:**
- Akın - Hızlı yağma
- Kuşatma - Kale fethi
- Savunma - Eyalet koruması
- Sefer - Büyük askeri harekât

**Taktikler:**
- Merkez Hücumu
- Kanat Manevrası
- Savunma
- Topçu Bombardımanı
- Aldatma Taktiği
- Teslim Çağrısı

---

## Çok Oyunculu Mod

### Bağlantı

1. Ana Menü → Çok Oyunculu (O)
2. "Oda Oluştur" veya "Odaya Katıl"
3. Bağlantı sırasında **Escape ile iptal edebilirsiniz**
4. Oda kodu ile arkadaşlarınızı davet edin

### Özellikler

- 2-6 oyuncu desteği
- Sıra tabanlı tur sistemi
- Diplomasi (ittifak, ticaret, savaş)
- Sohbet sistemi
- Bağlantı kopması/yeniden bağlanma
- Oda kaydetme/yükleme

### Sunucu Başlatma (Kendi Sunucunuz İçin)
```bash
python server.py --port 8765
```

---

## Seçilebilir Eyaletler

| Eyalet | Başkent | Kıyı | Zorluk |
|--------|---------|------|--------|
| Aydın Sancağı | İzmir | Evet | Kolay |
| Selanik Sancağı | Selanik | Evet | Kolay |
| Trabzon Eyaleti | Trabzon | Evet | Orta |
| Rum Eyaleti | Sivas | Hayır | Orta |
| Karaman Eyaleti | Konya | Hayır | Zor |
| Halep Eyaleti | Halep | Hayır | Zor |

**Kıyı Eyaletleri:** Tersane inşa edebilir, deniz ticareti yapabilir.

---

## Binalar

| Bina | İşlev |
|------|-------|
| Cami | Halk mutluluğu |
| Medrese | Eğitim, teknoloji |
| Kışla | Asker eğitimi |
| Pazar | Ticaret geliri |
| Kervansaray | Kervan gönderme, ticaret |
| Hastane | Nüfus sağlığı |
| Hamam | Halk temizliği, mutluluk |
| Kale | Savunma gücü |
| Çiftlik | Yiyecek üretimi |
| Maden | Demir üretimi |
| Kereste Ocağı | Kereste üretimi |
| Taş Ocağı | Taş üretimi |
| Ambar | Kaynak depolama |
| Han | Yolcu konaklama, gelir |
| Tersane | Gemi inşası (kıyı gerekir) |
| Topçu Ocağı | Top üretimi |

---

## Kurulum

### EXE Dosyası (Önerilen)

`OsmanliEyaletSimulasyonu.exe` dosyasını çalıştırın. Ek kurulum gerekmez.

### Kaynak Koddan Çalıştırma

```bash
pip install pygame accessible_output2 websockets
python main.py
```

### Gereksinimler (Kaynak Kod)
- Python 3.10+
- pygame
- accessible_output2 (ekran okuyucu desteği)
- websockets (çok oyunculu mod için)

---

## Sürüm Notları

### Kapalı Beta 3.0
- Hiyerarşik menü sistemi (Enter/Backspace navigasyon)
- Gelişmiş diplomasi (prestij, olay zincirleri, momentum)
- AI komşu kişilikleri
- Non-blocking çok oyunculu bağlantı
- Tutarlı klavye navigasyonu
- Ses efektleri iyileştirmeleri
- Türkçe karakter düzeltmeleri

### Kapalı Beta 2.0
- Sıralı savaş sistemi (düşman AI turu)
- Bina iç ekranları (işçi yönetimi, kervan, üretim)
- Tarihsel danışman isimleri
- Dinamik müzik sistemi
- Ekonomi dengesi iyileştirmeleri
- Çok oyunculu mod (6 oyuncu)

### Kapalı Beta 1.0
- 6 seçilebilir eyalet
- 16 farklı bina türü
- 5 askeri birim + toplar + gemiler
- Mevsim sistemi
- Savaş ve ticaret sistemleri
- Tam erişilebilirlik desteği

---

## İpuçları

1. **Tur geçirmek için Boşluk tuşuna basın** - Asker eğitimi ve inşaatlar tur geçtikçe tamamlanır.

2. **F1 tuşu her ekranda çalışır** - Mevcut durumun özetini dinleyin.

3. **Prestij kazanın** - Diplomatik başarılar prestij kazandırır, bu da gelecek müzakerelerde avantaj sağlar.

4. **Mevsimi takip edin** - Kış aylarında yiyecek üretimi düşer, hazırlıklı olun.

5. **Güç = Diplomasi** - Askeri gücünüz diplomaside etkilidir. 500+ güç haraç talebi, 1500+ güç vassallaştırma için gereklidir.

---

## İletişim

**E-posta:** Mesenovali@gmail.com  
**Geliştirici:** Muhammet Enes Şenovalı

---

*İyi oyunlar! Osmanlı'nın şanını yüceltin!*
