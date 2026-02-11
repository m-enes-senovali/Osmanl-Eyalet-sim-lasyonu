# Osmanlı Eyalet Yönetim Simülasyonu

![Osmanlı Tuğrası](assets/icon.png)

**Sürüm:** 1.0.0  
**Geliştirici:** Rodoslav Aleksandrov  
**Dil:** Türkçe  
**Erişilebilirlik:** Tam NVDA Ekran Okuyucu Desteği

## 📜 Hakkında

**Osmanlı Eyalet Yönetim Simülasyonu**, 1520 yılı Osmanlı İmparatorluğu döneminde geçen, derinlemesine strateji ve yönetim oyunudur. Bir Sancak Beyi veya Beylerbeyi olarak atandığınız eyaleti yönetin, ekonomiyi kalkındırın, ordular kurun, diplomatik ilişkiler geliştirin ve Padişah'ın (Kanuni Sultan Süleyman) gözüne girerek yükselin.

Oyun, tarihi gerçekliğe sadık kalarak tasarlanmış olup, görme engelli oyuncular için **tam erişilebilirlik** sunmaktadır.

---

## 🌟 Öne Çıkan Özellikler

### 💰 Gelişmiş Ekonomi Sistemi
*   **Kaynak Yönetimi:** Altın, Zahire, Kereste, Demir, Taş, Halat, Katran ve Yelken Bezi üretimi.
*   **Dinamik Piyasa:** Arz-talep dengesine göre değişen fiyatlar (Enflasyon ve Deflasyon).
*   **Ticaret Yolları:** İpek Yolu, Akdeniz, Karadeniz ve Hint Okyanusu ticaret ağları.
*   **Vergi Sistemi:** Halkın memnuniyeti ile gelir arasında denge kurun.

### ⚔️ Detaylı Askeri Sistem (1520 Dönemi)
*   **Birim Çeşitliliği:**
    *   **Kapıkulu:** Yeniçeri, Kapıkulu Sipahisi, Topçu, Cebeci.
    *   **Eyâlet:** Tımarlı Sipahi, Akıncı, Azap.
    *   **Donanma:** Kadırga, Levent.
*   **Savaş Mekanikleri:** Meydan Savaşları, Kale Kuşatmaları, Deniz Savaşları.
*   **Taktiksel Derinlik:** Merkez hücumu, Kanat manevrası, Savunma hattı gibi taktikler.

### 📜 Diplomasi ve Siyaset
*   **İlişkiler:** Komşu devletler (Venedik, Safevi, Macaristan vb.) ve vasal devletler ile ilişkiler.
*   **Aksiyonlar:** Elçi gönderme, Ticaret anlaşması, Evlilik ittifakı, Haraç talep etme, Savaş ilanı, Vasallaştırma.
*   **Saray İlişkileri:** Padişah Sadakati ve Lütfu, Sadrazam ve Defterdar ile ilişkiler.
*   **Prestij Sistemi:** Şanlı zaferler ve büyük yapılarla prestij kazanın.

### 🏗️ İnşaat ve Şehirleşme
*   **5 Kategori, 20+ Bina Tipi:**
    *   **Dini:** Cami, Medrese, Tabhane.
    *   **Askeri:** Ocak, Kale, Topçu Ocağı, Gözetleme Kulesi.
    *   **Ekonomi:** Çarşı, Kervansaray, Han, Bedesten, Darphane.
    *   **Altyapı:** Çiftlik, Maden, Kereste Ocağı, Taş Ocağı, Tersane, Su Kemeri.
    *   **Sosyal:** Darüşşifa (Hastane), Hamam.
*   **Sinerji Sistemi:** Binalar birbirini etkiler (Örn: Cami + Medrese = Eğitim Bonusu).

### 🕵️ Casusluk ve İstihbarat
*   **Ajanlar:** Çavuş, Hafiye, Gezgin Derviş, Tebdil Gezen, Cariye.
*   **Operasyonlar:** Keşif, Sabotaj, Suikast, Fitne Çıkarma, Propaganda, Harem İstihbaratı.
*   **Karşı İstihbarat:** Düşman casuslarını yakalayın.

### 🕌 Din ve Kültür (Millet Sistemi)
*   **Milletler:** Müslüman, Rum Ortodoks, Ermeni, Yahudi, Süryani toplulukları.
*   **Ulema:** Şeyhülislam, Kadıasker, Kadı, Müderris atamaları.
*   **Vakıflar:** Cami, İmaret, Medrese vakıfları kurarak halka hizmet edin.
*   **Fetvalar:** Kritik kararlarda dini meşruiyet kazanın (Cihad, Vergi, vs.).

### 🌐 Çok Oyunculu Mod (Multiplayer)
*   **Gerçek Zamanlı:** Arkadaşlarınızla aynı anda oynayın.
*   **Diplomasi:** Oyuncular arası ittifak, ticaret ve savaş.
*   **WebSocket Sunucusu:** Hızlı ve güvenilir bağlantı.

---

## 🚀 Kurulum ve Çalıştırma

### Gereksinimler
*   Python 3.8 veya üzeri
*   `pygame` kütüphanesi
*   `websockets` kütüphanesi (Multiplayer için)

### Kurulum Adımları
1.  Bu projeyi bilgisayarınıza indirin veya klonlayın.
2.  Gerekli kütüphaneleri yükleyin:
    ```bash
    pip install -r requirements.txt
    ```
    *(Eğer `requirements.txt` yoksa: `pip install pygame websockets`)*

### Oyunu Başlatma
Oyunu başlatmak için ana dizindeki `main.py` dosyasını çalıştırın:
```bash
python main.py
```

### Çok Oyunculu Sunucu Kurulumu
Arkadaşlarınızla oynamak için bir kişinin sunucu olması gerekir:
```bash
python server.py --port 8765
```

---

## 🎮 Kontroller (Klavye Kısayolları)

Oyun, klavye ile tam kontrol edilebilir şekilde tasarlanmıştır.

| Tuş | İşlev |
| :--- | :--- |
| **Yön Tuşları** | Menülerde gezinme / Harita hareketi |
| **Enter** | Seçim yapma / Onaylama |
| **ESC** | Geri gelme / Ana Menü |
| **Boşluk (Space)** | Turu Bitir (Sıradaki aya geç) |
| **E** | Ekonomi Ekranı |
| **M** | Askeri Ekran |
| **C** | İnşaat Ekranı |
| **D** | Diplomasi Ekranı |
| **P** | Nüfus ve Eyalet Ekranı |
| **F5** | Oyunu Hızlı Kaydet |
| **F9** | Oyunu Hızlı Yükle |
| **J** | Mevsim ve Tarih Bilgisi (Sesli) |
| **Page Up** | Müzik Sesi Artır |
| **Page Down** | Müzik Sesi Azalt |
| **O** | Olay Bildirimi (Varsa) |

---

## 📚 Oynanış Rehberi

### 1. Ekonomi Yönetimi
İlk hedefiniz ekonomiyi dengelemektir.
*   **Vergiler:** Halkı çok sıkmadan vergileri ayarlayın (%15-20 idealdir).
*   **Üretim:** Çiftlik (Zahire), Maden (Demir/Altın) ve Kereste Ocağı inşa edin.
*   **Ticaret:** Pazar ve Kervansaray inşa ederek ticaret gelirini artırın. İpek Yolu gibi ticaret yollarını açın.

### 2. Ordu Kurma
Güvenlik için ordu şarttır.
*   **Ocak:** Yeniçeri ve Sipahi yetiştirmek için Ocak inşa edin.
*   **Tımar:** Tımarlı Sipahiler ücretsizdir ancak tımar arazisi (Fethedilen toprak) gerektirir.
*   **Bakım:** Askerlerin tur başına altın ve zahire tükettiğini unutmayın.

### 3. Diplomasi
Komşularınızla iyi geçinin veya onları ezin.
*   **Elçi:** İlişkileri düzeltmek için elçi gönderin.
*   **Evlilik:** Güçlü bir müttefik için evlilik ittifakı kurun.
*   **Casusluk:** Savaşa girmeden önce düşmanı zayıflatmak için casus gönderin.
*   **Padişah:** İstanbul'dan gelen emirlere uyun, sadakatiniz düşerse kelleniz gidebilir!

### 4. Din ve Halk
Huzuru sağlamak önemlidir.
*   **Hoşgörü:** Farklı milletlere (Müslüman, Rum, Ermeni vb.) hoşgörü gösterin, her birinin farklı bonusları vardır.
*   **Vakıf:** İmaret ve Şifahane gibi vakıflar kurarak halkın duasını alın.

---

## 🛠️ Geliştirici Notları

Bu proje, Osmanlı tarihine duyulan ilgi ve strateji oyunlarına olan tutkuyla geliştirilmiştir. Özellikle görme engelli oyuncuların da strateji oyunlarından tam keyif alabilmesi için NVDA ekran okuyucu entegrasyonuna büyük önem verilmiştir.

**Katkıda Bulunanlar:**
*   **Kodlama & Tasarım:** Rodoslav Aleksandrov
*   **Tarih Danışmanlığı:** (1520-1566 Dönemi Kaynakları)

---

*Osmanlı Eyalet Yönetim Simülasyonu © 2026*
