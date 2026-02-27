# Osmanlı Eyalet Yönetim Simülasyonu - Kapsamlı Oyun Rehberi

Sürüm: 1.0.0 (Genişletilmiş Sürüm)
Geliştirici: Muhammet Enes Şenovalı
Dil: Türkçe
Erişilebilirlik: Tam NVDA ve SAPI5 Ekran Okuyucu Desteği

---

## 1. Oyuna Giriş ve Temel Amaç

Osmanlı Eyalet Yönetim Simülasyonu, 1520 yılı Osmanlı İmparatorluğu (Kanuni Sultan Süleyman dönemi) atmosferinde geçen, derinlemesine strateji, ekonomi ve kriz yönetimi tabanlı bir ekran okuyucu uyumlu yönetim simülasyonudur. Oyuncu, bir Eyalet Beylerbeyi veya Sancakbeyi olarak atandığı bölgeyi yönetmekle ve şahsi karakterinin (örn. yaş, kültür, özellikler) getirdiği avantaj ve dezavantajlarla başa çıkmakla yükümlüdür.

Temel Amaçlarınız:
- Halkınızı zenginleştirmek, göç alıp nüfusu büyütmek ve refah içinde yaşatmak.
- Güçlü bir ordu (Yeniçeriler, Sipahiler, Donanma, Topçular) kurup eyaletinizi düşmanlardan ve eşkıyalardan korumak.
- Payitaht'a (İstanbul) olan mali ve askeri yükümlülüklerinizi yerine getirerek Padişah'ın güvenini (Sadakat ve Lütuf) kazanmak.
- Ekonomiyi, ticareti (Pazar, Kervanlar) ve üretimi (İşçiler, Loncalar) canlandırarak veziriazamlığa kadar yükselebilecek bir prestije ulaşmak.

Dikkat Edilmesi Gereken Riskler:
Halkı aç bırakırsanız (Zahire eksikliği) veya vergi adaletsizliği yaparsanız isyanlar baş gösterir. Padişahın sadakatini yönetemez ve sıfıra düşürürseniz "Fetva ve İdam" ile oyun anında sonlanır. Hazineyi eksi 5000 altın sınırına kadar batırırsanız iflas nedeniyle görevden el çektirilirsiniz. Savaş veya kuşatmalarda ordularınızı kaybederseniz eyaletinizi yağmalamaya açık hale getirirsiniz.

---

## 2. Temel Kontroller ve Ekran Okuyucu (Erişilebilirlik) Kısayolları

Bu oyun görme engelli oyuncular için NVDA / SAPI5 uyumlu olarak %100 tam erişilebilir tasarlanmıştır. Hiçbir grafiksel fare tıklamasına ihtiyaç duymadan, oyun açıldığı andan itibaren klavyeyle oynanabilirsiniz.

Ekran ve Navigasyon (Menü) Kısayolları:
- Yukarı ve Aşağı Yön Tuşları: Menüdeki eylemler ve seçenekler arasında gezinir. Oyun Sonu/Zafer ekranlarında veya durum raporlarında satırlar arası geçişleri sağlar.
- Enter: Seçili öğeyi onaylar, binanın içine girer veya eylemi gerçekleştirir.
- Tab: Ana ekrandayken sağ taraftaki "İstatistik ve Eyalet Özeti" bilgilerine geçiş yaparak satır satır okumanızı sağlar.
- Backspace (Geri): Bir önceki menüye döner.
- Escape (ESC): Çıkış onayını, "Kaydet ve Çık" veya "Ana Menüye Dön" ekranını tetikler. Çıkış yaparken E, H ve I tuşlarıyla kaydetme tercihini seçebilirsiniz.
- Space (Boşluk): Turu bitirir (Ayı atlatır), ekonomiyi hesaplar, tarihi olayların yaşanmasını sağlar.
- F5 ve F9: Oyunu hızlıca kaydetme (F5) ve yükleme (F9) işlevlerini yerine getirir.
- Page Up ve Page Down: Arka planda çalan müziğin ses seviyesini kademeli artırır veya azaltır.

Eyalet İçi Bilgi (Sözlü İstatistik) Kısayolları (Ana Ekrandayken):
- H: Yardımcı Kethüda'nızın anlık ekran kısayollarını hatırlattığı menü.
- F1: Genel Eyalet Durumunu (Sadakat, Asker sayısı, Altın vb.) baştan sona tek hamlede özetler.
- F2, F3, F4: Sırasıyla Ekonomi, Askeri ve İnşaat sistemi temel işleyiş kurallarını anlatan sözlü rehberlerdir.
- R: Deponuzdaki tam kaynak listesini (Altın, Zahire, Kereste, Demir, Bakır, Barut vb.) seri şekilde okur.
- G: Anlık olarak sadece Altın miktarınızı ve Hazine durumunuzu söyler.
- S: Halkın özet durumunu (Nüfus, Memnuniyet, Padişah Sadakati ve İşçi oranı) seslendirir.
- I: O anki "Bir Önceki Tur Hulasası" yani Gelir (Vergiler) ve Gider (Maaşlar) dökümünüzü okur.
- Y: Hangi Yıl, Ay ve Tur'da (Örn. Yıl 1521, 3. ay, 15. tur) olduğunuzu söyler.
- W: Acil Durum Uyarıları: Eyalette isyan, kriz veya eksik kaynak varsa Kethüda'nız uyarır.
- T: Kethüda'nın (Danışmanınızın) o anki stratejik gidişata göre verdiği durum tavsiyelerini dinlersiniz.
- O (İşçi Sistemi): O tuşu doğrudan "İşçi Yönetimi" ekranını açar ve çalışmayan nüfusu (Reaya) tarlalara ve madenlere atamanızı sağlar.
- K (Savaş / Sefer Ekranı): Kılıç ve Sefer ekranını açarak savaş raporlarını, asker atamalarını ve düşmana taarruzu yönetirsiniz.
- X (Ticaret Ekranı): Tüccar ve Pazar / Kervan menüsünü açarak kaynak değişimi yaparsınız.

---

## 3. Ekonomi, Kaynaklar ve Endüstri (İşçi Atamaları)

Ekonomi sistemi; üretilen malların ticareti, toplanan vergiler ve sistemli israflar arasında bir denge kurmanızı gerektirir. Geliri harcamalarına yetmeyen bir eyalet kısa sürede isyana ve iflasa sürüklenir.

Temel Kaynaklar:
- Altın: Binaları inşa etme, askerlere maaş ve ulufe dağıtma, komşulara haraç verme işlemlerinde kullanılır.
- Zahire (Yiyecek): Halkınızın ve özellikle kalabalık ordularınızın her ay düzenli tükettiği erzaktır. Yetersizliğinde "Açlık ve Kıtlık" çıkar, askerler firar eder. Üretmek için Çiftlik yapılmalı ve İşçi atanmalıdır.
- Kereste, Demir ve Taş: Sosyal bina, kale, gemi inşası veya silah donanımı üretimi için gereklidir.
- Bakır ve Barut: Topçu Ocağı'nda veya ağır bombardıman birimlerinin eğitiminde ve kuşatmalarda kullanılan mühimmattır.

İşçi Yönetimi:
Bir bina (Örneğin Kereste Ocağı veya Çiftlik) inşa etmek üretim için tek başına yeterli değildir. Yapı inşa edildikten sonra "O" tuşu ile "İşçiler" (Reaya Yönetimi) ekranına girilmeli, eyaletinizdeki boştaki halk ilgili binaya "Çalışan" olarak atanmalıdır. Yalnızca işçi atanan binalar size her ay düzenli kaynak sağlayacaktır.

Mali Politikalar ve Enflasyon:
Oyunda toplanan verginin tipini Sistemden "Tımar" (Üretimden) veya "Nakit" (Piyasadan) olarak belirleyebilirsiniz. Şehrinizde çok fazla nakit akışı veya işlenmemiş altın biriktiğinde Enflasyon tetiklenir ve gider fiyatları korkunç oranlarda artar.
Enflasyonu yenmek için büyük miktarda altını rüşvet veya devlet fonu olarak bağışlayabilir, veya binlerce hazine kaybedilerek "Sikke Tashihi" (Para Reformu) uygulayıp kurları sabitleyebilirsiniz.
Piyasa çökerşe "Sikke Tağşişi" uygulayap acil nakit elde edebilirsiniz ancak bu durum kalıcı bir enflasyon patlaması ve geri dönüşü zor bir halk öfkesine yol açacaktır.

---

## 4. İnşaat Sistemi ve Eklentiler (Modüler Mimari)

Eyaletinizi genişletmenin yegane yolu mimari yapıları doğru bir işleyiş sırasıyla inşa edip onları en üst seviyelere çıkartmaktır (Giriş: Side Menu -> İnşaat).

Bina Türleri ve Ağacı:
- Üretim: Çiftlik, Kereste Ocağı, Demir Madeni, Taş Ocağı (İlgili kaynakların çıkarılmasını sağlar).
- Eğitim ve Ordu: Kışla (Azaplar), Talimgah (Yeniçeriler), Kale (Savunma bonosu ve Sipahiler), Topçu Ocağı (Kuşatma gücü birimleri). Deniz eyaletiyseniz Tersane inşası donanmanın kapısını açar.
- Sosyal ve Kültürel: Cami, İmaret, Hamam, Medrese. Nüfus sayısını (göç çekerek) artırır, halkın öfkesini dindirir, kültür puanını yükseltir.
- Bürokratik: Mahkeme, Elçilik. Elçilik binaları Casus sistemi katsayılarını yükseltir; Mahkemeler ise yolsuzlukları azaltır.

Eklenti Sistemi (Binanın İçine Girme):
Bir binayı seviye atlatmaktan fazlası oyunda mevcuttur. İnşaat listesinde olan bir binanızın (Örn: Cami veya Kale) üstüne gelip Eklenti menüsüne girdiğinizde (Enter), o yapıya özel alt mimariler ekleyebilirsiniz. Örneğin, Kaleye bir "Savunma Hendeği" veya askeri "Kışla Erzak Deposu", İmaret'e bir "Yolcu Bekleme Hanı" eklenebilir. Bu spesifik eklentiler eyalet istatistiklerine pasif matematiksel bonuslar sağlar.

---

## 5. Ordu Dağılımı, Denizcilik ve Taktik Savaş (Warfare) Menüsü

Oyun içi güvenlik altyapısı ve fetih haritaları savaş gücünüze (Military) endekslidir. Ancak yalnızca asker üretmek yeterli değildir; bunları savaş ekonomisiyle beslemek ve doğru yönetmek zorunludur.

Kara ve Deniz Birimleri:
- Azaplar (Yaya): Hızlı üretilen, barınma masrafı en düşük fakat meydan savaşlarında disiplinleri düşük kılıçlı, piyade birliklerdir.
- Yeniçeriler: Devşirme sistemine dayanan, son derece pahalı fakat savaş meydanlarında durdurulması en zor ateşli silahlara sahip profesyonel ordu.
- Tımarlı Sipahiler: Devletin askeri belkemiğidir. Nakit ulufe ödemesi gerektirmezler (Tımardan geçinirler). Güçlü süvarilerdir ancak üretilebilmesi için arka planda askeri binalar ve düzenli Tımar alanlarına ihtiyaç duyulur.
- Topçular (Artillery): Kuşatmaların vazgeçilmezidir. Ağır zayiat verdirir ama demir, barut ve maden sarfiyatı (Ateş Gücü Puanı) gerektirir.
- Kadırgalaşma (Donanma): Sadece limana sahip eyaletlerde (İzmir, İstanbul, Rodos vb.) gemi filoları kurup deniz akınları gerçekleştirilebilinmesine olanak sağlar.

Savaş Yönetimi (K Tuşu):
Oyunda komşu düşman uluslara veya isyancılara karşı "Sefer ve Savaş" ekranı üzerinden doğrudan etkileşime geçersiniz.
Düşman ordusuyla eşleştiğinizde sizden salt asker sayısı değil bir "Savaş Taktiği" (1, 2 veya 3 rakamlarıyla) istenecektir. Açık Meydan Taarruzu, Geri Çekilerek Menzi̇lli̇ Ateş, Bozkır/Hilal Taktiği, Pusular vb. Doğru iklim, düşman yapısı ve asimetrik üstünlük için seçeceğiniz Taktik, savaşın gidişatını doğrudan değiştirir. Mükemmel bir taktik kararıyla üç katı büyüklükteki orduları mağlup edebilir; ganimet, sadakat ve eyalet prestiji kazanabilirsiniz.

---

## 6. Sosyoloji, Din, Nüfus Politikaları ve Karar Olayları (Event) Sistemi

Bir devlet sadece askerle yönetilmez, masada alınan kararlar şehirdeki insanların kaderini etkiler.

Olaylara Müdahale (Event Sistemi):
Her ay turu geçtiğinde Padişahtan, yerel halktan veya diğer krallıklardan rastgele olaylar (Fermanlar) ekranınıza gelebilir. Bu durumlarda ekranda beliren Seçenek 1 veya Seçenek 2'yi seçmelisiniz. (Örn: "Bir tüccar devleti dolandırdı, mallarına mı el konulsun yoksa hapse mi atılsın?").
Verdiğiniz kararlar tek seferlik etkiler yaratabileceği gibi bazı kararlar "Olay Zincirleri" başlatır. Veba salgını varken karantina tavsiyesini reddetmeniz, aylar sonra Eyaleti ölüm tarlasına çevirecek kalıcı cezalar doğurabilir. Celali (Eşkıya) isyanlarında taviz vermeniz veya kılıç doğratmanız aylar süren asayiş krizlerine evrilebilir.

Halk, Din ve Kültür (Din ve Divan Ekranları):
- Nüfus Göçü Politikası: "Halk" menüsünden sınırlarınızın kapalılık durumunu tayin edin (Açık Kapı, Tam Sıkı Denetim, Sadece Seçilmişler).
- Din Menüsü (Vakıf ve Millet): Şehrinizde farklı inançtan insanlar (Millet Sistemi) yaşar. Kadılar ve Ulema meclisi atayarak hoşgörü puanınızı ayarlayın, isyan etkililik katsayısını bastırın.
- Meslek Entegrasyonu: Ekonominiz geliştikçe fazla nüfuslu olan çiftçi ve tarım sınıflarını okutarak, eğiterek "Zanaatkarlar", "Tüccarlar" veya "Bürokrasi Sınıfı" kimliğine geçiş yaptırıp vergi modelinizi tarımdan kentsel zenginliğe aktarın.

---

## 7. Casusluk Merkezleri, İstihbarat ve Diplomasi Divanı

"Diplomasi" ekranı ve buna bağlı Casusluk sekmesi, dış ilişkilerinizin yönetildiği ve en kirli siyasi operasyonların çevrildiği yerdir.

Casusluk Sistemi ve Operasyonlar:
Elçilik veya istihbarat binalarından gelen puanlarla komşu devletlere aktif istihbarat memurları yollanabilir.
- Temel Görevler (Düşük Risk): Gönderilen elçiler "Keşif ve Gözlem" yaparak düşmanın anlık altın depolamasını, ordu sayısını veya olası saldırı hedeflerini açık ederler.
- Riskli (Sabotaj) Görevler: İleri seviye ajanlar "Düşman Şehrinde Ayaklanma Çıkarma", "Suikast Girişimi" veya "Mühimmat Sabotajı" gibi tehlikeli görevlere atanabilir. İşlem başarılı olursa savaşsız eyalet çökertilir. Ancak elçiniz deşifre olup yakalanırsa düşman devlet Padişaha siyasi protesto çeker, Sadakatiniz devasa oranda düşer ve savaş başlatılır.

Diplomatik İlişkiler:
Rakip krallıklara veya multiplayer modundaki diğer gerçek oyunculara Altın yollayarak İttifak Antlaşmaları yapabilir, askeri saldırışmazlık paktları imzalayabilirsiniz. "Saray Divanı" menüsü üzerinden doğrudan Padişaha veya Paşalara ulufe nitelikli hediyeler (Rüşvet, Liyakat Ödülleri) göndererek "Sultan Lütfunu" yüksek derecede manipüle edebilir; idamınızı geciktirebilirsiniz.

---

## 8. Gerçek Zamanlı Çok Oyunculu (Multiplayer) Deneyim

Bu simülasyon, yerel ağ veya internet üzerinden arkadaşlarınızla birlikte kıran kırana Eyalet yarışları yapmanıza olanak tanıyan senkronize bir Çok Oyunculu mod içerir.

Multiplayer Kurulumu ve Oynanışı:
1. "Multiplayer" ana menüsünden Host ("Lobi Kur") işlemi yapılarak kod yaratılır.
2. Diğer Eyalet Beyleri isimlerini girip IP koduyla lobiye dahil olduklarında oyun başlatılır ve tur atlama mekaniği iki oyuncu içinde "Eşzamanlı" olarak sayılır.
3. Kendi aranızdaki diplomasiler artık yalandan ibaret değildir; doğrudan "Ticaret Antlaşması" yaparak birbirinize Altın, Zahir veya Asker pompalayabilirsiniz. İttifak kurduğunuz oyuncunun Eyaletindeki refah size çarpan olarak geri döner.
4. Çatışma: Eğer çıkarlarınız çakışırsa savaş açabilirsiniz. Kazanan oyuncu diğer Eyalet Beyinin ordularını fiziki olarak katledebilir, hazinesindeki parayı "Yağma" edip kendi eyaletine geçirebilir.
5. İletişim: "." (Nokta) kısayoluyla canlı sohbet penceresini (Chat) açıp "Ordumu toparlamam gerek, hammadde atar mısın?" yazarak anında rol yapma ve konuşma deneyimi sağlayabilirsiniz.
6. Ağ Kopması ve Oturumsal Kurtarma: Oyun çöker, arkadaşınız dondurucu bir hata alırsa problem yoktur. Tekrar Lobiye "Aynı Karakter İsmiyle" girildiğinde sunucu, kopan oyuncunun Yıl bilgisini, var olan Askerini ve Altınını veri tabanından geri alarak oyuna fiilen geri döndürür. Hiçbir ilerleme zayi olmaz.

---

Adalet Terazisini Bozmayan, Eyaletini Demirden Bir Kılıçla Koruyan ve Padişahı Şanlı Seferlere Çıkartan Bir Sancakbeyi Olmanız Ümidiyle... 

İyi Şanslar Beylerbeyi! Hüküm Artık Sizin Elinizde!
