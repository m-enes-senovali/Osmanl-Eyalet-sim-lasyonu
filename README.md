# Osmanlı Eyalet Yönetim Simülasyonu - Kapsamlı Oyun Rehberi

![Osmanlı Tuğrası](assets/icon.png)

**Sürüm:** 1.0.0 (Genişletilmiş Sürüm)  
**Geliştirici:** Rodoslav Aleksandrov  
**Dil:** Türkçe  
**Erişilebilirlik:** Tam NVDA & SAPI5 Ekran Okuyucu Desteği

---

## 📜 1. Oyuna Giriş ve Amacınız

**Osmanlı Eyalet Yönetim Simülasyonu**, 1520 yılı Osmanlı İmparatorluğu (Kanuni Sultan Süleyman dönemi) atmosferinde geçen, derinlemesine bir strateji ve yönetim oyunudur. Bir Eyalet Beylerbeyi veya Sancakbeyi olarak atandığınız bölgeyi yönetmekle sorumlusunuz.

**Temel Amacınız:** 
Halkınızı zenginleştirmek, güçlü bir ordu kurup eyaletinizi düşmanlardan ve eşkıyalardan korumak, Payitaht'a (İstanbul) olan yükümlülüklerinizi yerine getirerek Padişah'ın güvenini kazanmak ve nihayetinde Veziriazamlığa kadar yükselebilmektir. Eğer halkı aç bırakırsanız **İsyan** çıkar, Padişahı küstürürseniz **Kelleniz gider.**

---

## 🎮 2. Temel Kontroller ve Erişilebilirlik (Görme Engelli Desteği)

Bu oyun tamamen menü tabanlıdır ve farenin yanı sıra **tamamen klavye** ile oynanabilir. Oyun açıldığı andan itibaren ekran okuyucunuz her menüyü ve uyarıyı size sesli olarak bildirecektir. Oynanış sırasında şu kısayollar hayat kurtarır:

### Ekran Kısayolları
*   **Yukarı / Aşağı Yön Tuşları:** Menüdeki seçenekler arasında gezinir.
*   **Enter:** Seçili öğeyi onaylar / İçine girer.
*   **Tab (Gezinme Tuşu):** Sağ taraftaki "İstatistik / Eyalet Özeti" bilgilerini satır satır okumanızı sağlar.
*   **Backspace (Geri Tuşu):** Bir önceki menüye döner.
*   **Escape (ESC):** Çıkış / Ana Menüye dönme ekranını açar.
*   **Space (Boşluk):** Turu Bitirir (Bir sonraki aya geçer) ve aylık raporu size okur.
*   **F5:** Oyunu hızlı kaydeder.
*   **F9:** En son kaydedilen oyunu hızlı bir şekilde yükler.
*   **Page Up / Page Down:** Arka planda çalan müziğin ses seviyesini artırır veya azaltır.

### Bilgi ve Durum Öğrenme Kısayolları (Eyalet Ekranındayken)
*   **H:** Yardımcı Kethüda'nız size o an basabileceğiniz tuşların listesini okur.
*   **F1:** Genel Eyalet Durumunu (Sadakat, Asker, Altın vb.) baştan sona özetler.
*   **R:** Deponuzdaki temel kaynakları (Altın, Zahire, Kereste, Demir, vs.) tek tek okur.
*   **S:** Halkın durumunu (Nüfus numarası, Memnuniyet, Padişah Sadakati) okur.
*   **I:** O turki **Gelir ve Gider** dökümünüzü okur (Vergiler, Maaşlar).
*   **Y:** Hangi Yıl, Ay ve Tur'da olduğunuzu söyler.
*   **W:** Eyalette akut bir kriz (İsyan, Açlık, Para bitmesi) varsa bunları acil uyarı olarak söyler.
*   **T:** Kethüda'nız o anki durumunuza göre size **tavsiye** verir (Örn: "Zahiremiz bitiyor beyim, hemen çiftlik yapın").
*   **O:** Tur sonunda gerçekleşen ve bekleyen bir tarihi Olay (Event) varsa onu ekrana getirir.

### Alt Menü Kısayolları
*   **E:** Ekonomi
*   **M:** Askeri Ordu
*   **C:** İnşaat
*   **D:** Diplomasi
*   **P:** Halk (Politikalar ve Göç)
*   **O:** İşçiler (Reaya / İşçi Atamaları)
*   **L:** Loncalar
*   **K:** Sefer / Savaş Ekranı
*   **X:** Ticaret / Pazar Ekranı
*   **S (Eğer Yan Menüdeyseniz):** Casusluk Ekranı
*   **G:** Geçmiş (Önceki turlarda yaşanan olayların kaydı)

---

## 💰 3. Ekonomi: Altın, Kaynaklar ve İşçiler

Oyunun can damarı ekonomidir. Kaynak üretmeden asker basamaz veya bina yapamazsınız.

*   **Altın:** Bina yapmak, asker maaşı ödemek ve diplomasi (haraç) için kullanılır. Başlıca **Vergi** toplayarak ve **Ticaret** yaparak kazanılır.
*   **Zahire (Yiyecek):** Halkınızın yemesi ve askerlerinizin karnının doyması için şarttır. Biterse **Açlık** başlar, nüfus düşer ve hastalık/isyan patlak verir.
*   **Kereste & Demir & Taş & Yelken Bezi vb.:** Bina inşası ve Asker üretimi (Örn: Donanma için halat, Topçu için demir) için kullanılır.

**İşçi Mantığı (O Tuşu):** Binaları inşa etmeniz tek başına yeterli değildir. Bir Çiftlik veya Maden kurduğunuzda, `İşçiler` ekranına gidip oraya halkınızdan "Çalışan" atamalısınız. Atanan her işçi günlük olarak kaynak üretir.

**Vergi ve Enflasyon:** Altını vergiyle toplarsınız. "Halk" ekranından Tımar veya Nakit sistemi seçebilirsiniz. Ancak kasanızda aşırı derecede altın birikirse paranız değer kaybeder **(Enflasyon)**. Enflasyonu düşürmek için harcamalar yapabilir veya binlerce altın ödeyerek **Sikke Tashihi** (Para Kararını Sabitleme) uygulayabilirsiniz. Acil paranız bittiğinde piyasadaki sikkenin ayarıyla oynayıp anında nakit alabilirsiniz (**Sikke Tağşişi**) ancak bu Enflasyonunuzu ve İsyan riskini kalıcı olarak artırır!

---

## 🏗️ 4. İnşaat Sistemi ve Eklentiler (C Tuşu)

İnşaat menüsü, eyaletinizi bir köyden devasa bir şehre dönüştürdüğünüz yerdir. Yapılabilecek binalar şunlardır:
*   **Üretim Binaları:** Çiftlik, Kereste Ocağı, Maden vs. (Kaynak üretmek için şarttır).
*   **Sosyal Binalar:** Cami, İmaret, Hamam (Halk memnuniyetini ve göç oranını artırır).
*   **Askeri Binalar:** Kışla, Talimgah, Kale (Daha nitelikli asker basmanızı sağlar).
*   **Adalet Binaları:** Mahkeme (Yolsuzlukları önler, adaleti sağlar).
*   **Diplomatik Binalar:** Elçilik (Ajan ve Casus gücünü artırır).

**EKLENTİ SİSTEMİ:** 
Bir bina (Örneğin: Cami) inşa ettiğinizde iş bitmez. İnşaat listesinde mevcut Camii'nizin üzerine gelip **Enter'a basarak içine girin.** Karşınıza çıkacak **"--- Eklentiler ---"** menüsünden o binayı yükseltebilirsiniz. Örneğin bir Camiye "Muvakkithane" ekleyebilir, bir Kaleye "Hendek" kazabilirsiniz. Her eklenti binaya benzersiz ekstra bonuslar verir.

---

## ⚔️ 5. Ordu ve Savaş (M ve K Tuşları)

Eyaletinizin güvenliğini sağlamak için çeşitli birlikler eğitebilirsiniz (Askeri Menü - M):
*   **Azaplar / Yaya Askerler:** Gündelik ucuz piyadelerdir.
*   **Yeniçeriler:** Çok masraflı ama muazzam derecede güçlü elit birlikler.
*   **Tımarlı Sipahiler:** Bakım masrafı olmayan ancak üretmek için "Fethedilmiş Tımar Arazisi"ne ihtiyaç duyan süvariler.
*   **Topçular:** Kale kuşatmalarında şarttır (İnşaat'tan Topçu Ocağı gerektirir).
*   **Donanma:** Limanınız varsa Kadırga ve Kalyon üretebilirsiniz (Kıyı Eyaletlerinde geçerli).

**Savaşmak (K Tuşu):** Bir komşu devlete "Casusluk" ekranından saldırı planlayabilir veya çok oyunculu oyundaysanız direkt savaş açabilirsiniz. Savaşlarda Ordu Güçlerinin çarpışması haricinde kuşatmayı nasıl yöneteceğinizi (Açık Taarruz, Kuşatma, Menzilli Ateş vs) rakam tuşlarına (1, 2, 3) basarak seçmeniz istenir. Taktik doğrudan kayıpları etkiler!

---

## 🎭 6. Nüfus, Sosyoloji ve Olay Zincirleri

Oyun boyunca rastgele veya tarihe dayalı (1520 - 1566 dönemi) **Olaylar (Eventler)** karşınıza çıkar. Olay uyarısı aldığınızda "O" tuşuyla olaya bakıp bir ferman vermelisiniz (Örn: İsyan eden Celalilere af mı çıkacak yoksa ordu mu yollanacak?).

Bazı olaylar **[OLAY ZİNCİRİ]** şeklindedir. Bunlar basit bir pop-up değillerdir; "Veba Salgını", "Celali İsyanları" veya "Taht Kavgaları" gibi sizin kararınıza göre dallanıp budaklanan ve yıllarca (pasif olarak her turunuzda canınızı yakan) kalıcı krizlerdir. İsyan edeni hoşgörüyle mi yatıştıracaksınız yoksa demir yumrukla mı ezeceksiniz, seçim sizin.

**Göç Politikaları:** "Halk" menüsünden Eyaletinizin göç politikasını belirleyin (Örn: Herkes gelsin, Sadece Müslümanlar, Sınırları Kapat).
**Meslek Dönüştürme:** Altın ve kaynak harcayarak çiftçilerinizi Zanaatkar, Tüccar veya Ulemaya evirebilirsiniz. (Şehirleşme).

---

## 🕵️ 7. Casusluk (Espionage) ve Diplomasi

Kethüdanız vasıtasıyla diğer komşu krallıklara ajan gönderebilirsiniz (Çavuş, Gezgin Derviş, vs).
*   **Güvenli Görevler:** Keşif yapmak size diğer devletin zayıf alanlarını gösterir.
*   **Riskli Görevler:** İsyan çıkartmak veya Suikast düzenlemek relations'ı (ilişkiyi) darmadağın eder. Eğer yakalanırsanız Padişahın kulağına gider ve sadakatiniz tepetaklak olur.

Düşmanla ilişkinizi ölçün. Altın göndererek Padişahın Lütfunu alın (Diplomasi Menüsü - D). Unutmayın, Padişah Sadakati %30'ların altına düştüğü an fermanınız yazılır!

---

## 🌐 8. Çok Oyunculu (Multiplayer) Deneyim

Arkadaşlarınızla aynı anda rakip "Sancakbeyleri" olarak oynayabilirsiniz.
1. "Multiplayer" menüsünden bir arkadaşınız "Lobi Kur" der. Diğerleri Oda Kodunu girip bağlanır.
2. Tüm oyuncular aynı dönemi oynarlar. Padişahın sadakati hepiniz için ayrı ayrı işler.
3. Diğer oyuncularla "Diplomasi" menüsünden **Ticaret Antlaşması** veya **İttifak** kurabilirsiniz. Bunlar gerçek etkilerdir; Ticaret size her ay pasif olarak altın getirirken, müttefikiniz sizinle savaşa girebilir.
4. Diğer oyunculara (Kısa yol: . (Nokta) tuşu) mesaj gönderip sohbet edebilirsiniz.
5. Savaş ilan edebilirsiniz! Bir oyuncuya saldırdığınızda onun sahip olduğu askeri varlıkları ve depoladığı altınları yağmalarsınız, onun oyunundaki ordusunu fiilen eksiltmiş olursunuz.
6. Bağlantınız koparsa odaya aynı isimle geri bağlandığınızda oyununuz sıfırlanmaz, arkadaşlarınızın kaldığı Yıldan, askeri gücünüz restore edilerek geri dönersiniz (State Recovery).

---

### *İyi Şanslar Sancakbeyi! Tarih senin kararlarınla yazılacak.*
