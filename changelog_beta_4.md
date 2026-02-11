# 📜 Osmanlı Eyalet Simülasyonu - Beta 4 sürüm Notları
**"Hanım Sultanlar ve Paşalar Sürümü"**

Bu güncelleme, oyuna derinlikli bir **Cinsiyet ve Karakter Sistemi** ekleyerek oynanış stratejilerini temelden çeşitlendiriyor. Artık sadece bir vali değil, yaşayan bir karakteri yönetiyorsunuz.

## ✨ Öne Çıkanlar
*   **Karakter Oluşturma:** Oyuna başlarken cinsiyet (Bey/Hatun) ve isim seçimi.
*   **Dinamik Oynanış:** Seçilen cinsiyete göre değişen bonuslar, olaylar ve mekanikler.
*   **Erişilebilirlik:** Tüm yeni ekranlar ekran okuyucu uyumlu.

## 🛠 Oynanış Mekanikleri (Gameplay)

### 👤 1. Karakter ve Unvan Sistemi
*   **Cinsiyet Seçimi:**
    *   **Erkek (Bey):** Askeri odaklı. Akınlarda ve orduda daha etkili.
    *   **Kadın (Hatun):** Diplomasi ve yönetim odaklı. Saray ilişkileri ve ticarette üstün.
*   **Dinamik Unvanlar:** Oyun artık size uygun şekilde hitap ediyor (Örn: *"Vali Paşa"* veya *"Vali Hatun"*).
*   **Kayıt Sistemi:** Karakter özellikleri artık save dosyasında saklanıyor.

### 💍 2. Diplomasi Güncellemeleri
*   **Evlilik İttifakları (Geliştirilmiş):**
    *   Kadın yöneticiler, evlilik ittifakı tekliflerinde **+%25 başarı bonusu** kazanıyor.
    *   Evlilik akrabalık bağları cinsiyete göre değişen metinlerle sunuluyor.

### 🕵️‍♀️ 3. Casusluk Sistemi (Yeni!)
*   **Yeni Casus Tipi: Cariye (Sadece Kadın Yönetici):**
    *   Saraylara sızabilen, yüksek gizlilik ve diplomasi yeteneğine sahip özel ajan.
*   **Yeni Operasyon: Harem İstihbaratı (Sadece Kadın Yönetici):**
    *   Padişahın sadakatini **+15** artıran ve istihbarat sağlayan güçlü bir operasyon.
*   **UI Filtreleme:** Bu seçenekler sadece kadın karakter ile oynarken menüde görünür.

### ⚔️ 4. Savaş ve Akın Sistemi
*   **Liderlik Mekaniği:**
    *   **Erkek Yöneticiler:** Akınlara "Bizzat" liderlik ederek **+%20** güç bonusu kazanır.
    *   **Kadın Yöneticiler:** Akınlara "Vekil" (Komutan) gönderir. Risk almazlar ancak kişisel liderlik bonusu almazlar.
*   **Arayüz:** Savaş ekranı, cinsiyetinize uygun seçenekleri (Bizzat/Vekil) dinamik olarak gösterir.

## 📜 İçerik ve Olaylar

### Yeni Rastgele Olaylar (Event System)
*   **Erkeklere Özel:**
    *   *Akın Daveti:* Komşu beylerden ortak akın teklifi.
    *   *Yeniçeri Ağası:* Ordu içi siyaset.
*   **Kadınlara Özel:**
    *   *Saraydan Mektup:* Valide Sultan ile yazışmalar.
    *   *Şüpheci Beyler:* Otoritenizi sorgulayan yerel beylerle başa çıkma.
    *   *Vakıf Açılışı:* Halk desteğini artıran sosyal projeler.

## 🔧 Teknik ve Arayüz Düzeltmeleri
*   **Bug Fix:** Karakter oluşturma ekranındaki renk hatası (`light_text` KeyError) giderildi.
*   **Bug Fix:** Metin giriş kutusunda (Input Box) "Enter" tuşu çakışması düzeltildi.
*   **İyileştirme:** `Province View` başlığında artık karakter unvanı da okunuyor.
*   **İyileştirme:** Ana menü "Yeni Oyun" butonu artık karakter oluşturma sihirbazına yönlendiriyor.

---
*İyi oyunlar dileriz! - Geliştirici Ekibi*
